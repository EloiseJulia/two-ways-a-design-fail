# impl-azure-provider — AzureFoundryProvider (CODE + OFFLINE TESTS ONLY)

You are an implementation subagent in worktree `.worktrees/azure-provider` (branch
`feature/azure-provider`, draft PR #9). **Build CODE + OFFLINE TESTS ONLY — do NOT call
any real Azure or GitHub API** (Azure creds are not provisioned yet; tests use a mock).
You do NOT audit/merge. Report FACTS; do NOT claim "done/all green".

## 0. FIRST: read the source of truth
Read: `INTERFACES.md` (§3 `ModelProvider` protocol + `AgentResponse` + `run_panel`),
`SPEC.md` (§4.2 multi-family panel; DECIDED: Azure fallback), `PROGRESS.md` (Known pitfalls),
`docs/plans/2026-07-15-quota-strategy.md` (Lever C — Azure removes the daily cap),
and — CRITICAL — the EXISTING provider you are mirroring:
`src/twdf/panel/provider.py` (`GitHubModelsProvider`: `model_name` param, hashlib response
cache in `data/cache/panel/`, `generate(prompt,...)` + `generate_messages(messages,...)`,
`_call_api` with retry/backoff, `get_stats()`, 429/5xx handling). Also skim
`src/twdf/panel/real_panel.py` to confirm how `provider.generate_messages(...)` /
`provider.name` are used, and `tests/test_panel_real.py` for the mock-provider + cache
determinism test patterns.

## 1. GOAL
Add `AzureFoundryProvider` implementing the SAME `ModelProvider` protocol as
`GitHubModelsProvider`, so it is a DROP-IN replacement usable by `run_panel` for the
confirmatory axis-1 run WITHOUT the per-model daily cap. It must reuse the SAME hashlib
response cache mechanism so runs are deterministic + resumable and cross-provider cache keys
don't collide.

## 2. Requirements — `src/twdf/panel/azure_provider.py`
- Class `AzureFoundryProvider` with:
  - `name: str` = the model/deployment id (so `AgentResponse.model` + cache key carry it).
  - `generate(self, prompt, *, seed, max_tokens, temperature) -> str` and
    `generate_messages(self, messages, *, seed, max_tokens, temperature) -> str` — SAME
    signatures as `GitHubModelsProvider` (real_panel.py calls `generate_messages`).
  - `get_stats()` returning at least `{api_calls, cache_hits, total_requests}`.
- **Credentials from ENV (never hard-code/print/commit):**
  - `AZURE_OPENAI_ENDPOINT` (e.g. `https://<resource>.openai.azure.com` or a Foundry endpoint),
  - `AZURE_OPENAI_KEY`,
  - `AZURE_OPENAI_API_VERSION` (default a recent stable value, e.g. `2024-10-21`),
  - deployment name: constructor arg `deployment` (falls back to `model_name`); optionally an
    env `AZURE_OPENAI_DEPLOYMENT`.
  - If required env vars are missing, raise a CLEAR error at construction (do NOT invent a
    fallback). NEVER log the key.
- **Two auth/endpoint styles — support BOTH, selected by a constructor arg
  `api_style: str = "azure_openai"`:**
  1. `"azure_openai"` (Azure OpenAI Service): POST
     `{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={version}`,
     header `api-key: {key}`, body OpenAI-compatible (`messages`, `temperature`, `max_tokens`,
     `seed`) — note: NO `model` field in body for this style (deployment is in the URL).
  2. `"foundry"` (Azure AI Foundry models-as-a-service / OpenAI-compatible): POST
     `{endpoint}/chat/completions` (or `{endpoint}/openai/v1/chat/completions` — make the path
     configurable), header `Authorization: Bearer {key}`, body includes `model` = deployment.
  Document both; default `azure_openai`. Parse `choices[0].message.content`.
- **Reuse the cache:** import/share the SAME cache-key + read/write logic as
  `GitHubModelsProvider` (best: refactor the cache into a small shared helper/mixin that BOTH
  providers use, WITHOUT changing GitHubModelsProvider's public behavior or breaking its
  tests; if a clean refactor is risky, replicate the exact hashlib.sha256 keying —
  key over (name/deployment, normalized messages, temperature, max_tokens, seed) — in the same
  `data/cache/panel/` dir). Cache hit ⇒ 0 API calls, identical content. Builtin `hash()` BANNED.
- **Retries:** retry on 429/5xx with backoff (transient throttling can still occur on Azure),
  but NO per-model daily-cap special-case (Azure has no such cap). Keep an optional
  `inter_call_sleep` (default small, e.g. 0.2s) and `max_retries`.
- Do NOT modify `GitHubModelsProvider`'s behavior or break `tests/test_panel_real.py` /
  `tests/test_panel_redesign.py`. If you refactor shared cache code, run those tests.

## 3. Tests — `tests/test_azure_provider.py` (OFFLINE, mock; your validation gate)
Use `unittest.mock` / monkeypatch to fake the HTTP layer (`requests.post`) — NO network.
- Constructor raises a clear error when required env vars are missing.
- `azure_openai` style: builds the correct URL
  (`.../openai/deployments/{deployment}/chat/completions?api-version=...`) + `api-key` header;
  body has NO `model` field; parses content from a mocked `choices[0].message.content`.
- `foundry` style: posts to `{endpoint}/chat/completions` with `Authorization: Bearer` +
  `model` in body; parses content.
- **Cache determinism:** with the HTTP layer mocked, a second identical call is served from the
  hashlib cache with the mock NOT called again (assert call count) and identical content;
  cross-process determinism via subprocess if feasible (reuse existing pattern).
- Key never appears in any request log/repr/cache file (assert).
- Interchangeability: `AzureFoundryProvider` satisfies the `ModelProvider` protocol used by
  `run_panel` (a tiny `run_panel` smoke test with the mocked Azure provider produces
  well-formed `AgentResponse`s, System-1 frozen across a 2-condition pair).
- Mark any real-network test `@pytest.mark.live` and skip by default.
- `pytest -m "not live"` GREEN (report counts); do NOT weaken tests; grep `\bhash\(` = 0.

## 4. Docs
- Update `INTERFACES.md` §8 AS-BUILT (AzureFoundryProvider added; env vars; both api styles).
- Update `PROGRESS.md` (a "Doing / Azure provider code-complete, awaiting PI-provisioned creds"
  entry) noting the exact env vars the PI must set:
  `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, `AZURE_OPENAI_API_VERSION`, and deployment
  name(s); and that the confirmatory run switches the experiment's provider to this class.
- Add a short `docs/plans/azure-setup.md`: the exact steps/vars the PI needs to provision
  (endpoint, key, api-version, deployment names for the frozen confirmatory model set), and
  how to point an experiment at Azure.

## 5. Guardrails (§4.5)
Creds only from env, never printed/committed; `.gitignore` covers `data/cache/` + `data/raw/`
(already) — verify; `hashlib` only; do NOT break existing provider tests; do NOT call real APIs;
do NOT change `GitHubModelsProvider` public behavior. Do NOT commit any scratch.

## 6. Deliverables + wrap-up
Code (`azure_provider.py` + any shared cache helper), `tests/test_azure_provider.py` (offline,
green), `INTERFACES.md` + `PROGRESS.md` + `docs/plans/azure-setup.md` updates. Commit (trailer
`Co-authored-by: Copilot <copilot@github.com>`) + push to `feature/azure-provider`. Return a
FACTUAL report: the class API, the two api styles + exact URLs/headers, how the cache is
shared/replicated, the env vars the PI must set, `pytest -m "not live"` counts, and confirmation
you called NO real API. Manager audits + merges; real Azure run happens once the PI provisions creds.
