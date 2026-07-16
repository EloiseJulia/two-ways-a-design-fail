# audit-azure-provider — INDEPENDENT audit (PR #9)

You are a FRESH, independent auditor. You did NOT write this code. Verify the
`AzureFoundryProvider` slice. REPORT ONLY; do NOT fix or merge. NO real API calls
(Azure not provisioned; tests are mocked). Run `pytest -m "not live"` only. Evidence =
file:line + reproduced results.

## Context
Branch `feature/azure-provider` (draft PR #9) adds `AzureFoundryProvider` — an
OpenAI-compatible, drop-in `ModelProvider` against Azure OpenAI / Azure AI Foundry, to
run the confirmatory axis-1 panel WITHOUT the GitHub Models daily cap. Read:
`INTERFACES.md` (§3 `ModelProvider` protocol + §8 AS-BUILT), `src/twdf/panel/provider.py`
(the `GitHubModelsProvider` it mirrors), `src/twdf/panel/azure_provider.py` (new),
`tests/test_azure_provider.py`, `docs/plans/azure-setup.md`, `PROGRESS.md`. Diff:
`git --no-pager diff main...feature/azure-provider`.

## Checks (PASS/FAIL + evidence)
1. **Protocol drop-in:** `AzureFoundryProvider` exposes `name`, `generate(prompt,*,seed,
   max_tokens,temperature)`, `generate_messages(messages,*,...)`, `get_stats()` with the
   SAME signatures `run_panel`/`real_panel.py` use (real_panel calls `generate_messages`).
   A `run_panel` smoke test with a MOCKED Azure provider yields well-formed AgentResponses,
   System-1 frozen across the UI pair.
2. **Two api styles correct:**
   - `azure_openai`: URL `{endpoint}/openai/deployments/{deployment}/chat/completions?api-version=...`,
     header `api-key`, body has NO `model` field.
   - `foundry`: URL `{endpoint}/chat/completions` (configurable path), header
     `Authorization: Bearer`, body includes `model`. Both parse `choices[0].message.content`.
   Verify via the mocked-request assertions in the tests + reading the code.
3. **Secrets:** endpoint/key ONLY from env (`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`,
   `AZURE_OPENAI_API_VERSION`); missing → clear error at construction. Key NEVER logged,
   put in repr/str, or written to cache files (there is a test — verify it actually asserts
   the key is absent). Grep the diff for any hard-coded key-like string.
4. **Cache correctness + no collision:** reuses the SAME hashlib.sha256 keying + `data/cache/
   panel/` dir; the key INCLUDES the model/deployment name so Azure vs GitHub `gpt-4o` don't
   collide. Cache hit ⇒ 0 API calls + identical content (verify the mock is NOT re-called).
   Cross-process determinism test present + real (subprocess), or documented if not feasible.
   Builtin `hash()` banned (grep `\bhash\(` excl hashlib/comments = 0).
5. **No regression to GitHubModelsProvider:** if the cache logic was refactored into a shared
   helper/mixin, confirm `GitHubModelsProvider` public behavior is unchanged and
   `tests/test_panel_real.py` + `tests/test_panel_redesign.py` still pass (run
   `pytest -m "not live"` on them; report). If replicated instead of shared, note the
   duplication but it's acceptable.
6. **Retry logic:** 429/5xx retry with backoff; NO per-model daily-cap special-case (correct —
   Azure has none). Reasonable max_retries + pacing.
7. **Tests not weakened / anti-gaming:** the mock assertions actually check URL/headers/body
   shape (not trivially true); the key-absence + cache-determinism tests are real. `pytest -m
   "not live"` GREEN; report counts. Live tests marked + skipped by default.
8. **Hygiene:** `data/cache/` + `data/raw/` gitignored; no scratch committed; no secrets;
   `docs/plans/azure-setup.md` lists the exact env vars + provisioning steps accurately.

## Output
Markdown report: overall verdict (PASS / FAIL / CONDITIONAL PASS); per-check PASS/FAIL +
evidence (file:line, reproduced pytest counts); any BLOCKERS. Do NOT modify code or merge.
Print the report in your final message.
