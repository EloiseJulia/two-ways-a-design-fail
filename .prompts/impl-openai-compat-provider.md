# IMPL — OpenAI-compatible proxy provider (ghc-api) + cross-vendor configs

You are an IMPLEMENT subagent (fresh, non-interactive). Build the slice below in a
git WORKTREE, open a DRAFT PR, and STOP. **Do NOT merge. Do NOT run live LLM calls
against the proxy** (the Manager runs live after an independent audit). Return a
concise report of what you built + how you tested it offline.

## Repo / env
`C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail` (Windows PowerShell).
- `twdf` NOT pip-installed: `$env:PYTHONPATH=(Resolve-Path .\src).Path` to run python.
- `$env:GH_TOKEN=$null` before any `gh`.
- Full test suite hangs on network downloads — run only the offline test files you add/touch.
- Branch from latest main in a NEW worktree, e.g.:
  `git worktree add .worktrees/openai-compat -b feat/openai-compat-provider origin/main`

## Why (context)
PI opened `ghc-api` = a local **GitHub Copilot API Proxy**: OpenAI-compatible,
base URL `http://127.0.0.1:8787/v1`, **NO auth token** (started with `--no-enable-auth`),
effectively unlimited quota, cross-vendor. We will use it for a cross-vendor
robustness arm (gpt-5.5 + claude + gemini). Endpoint verified working:
- POST `http://127.0.0.1:8787/v1/chat/completions`, OpenAI schema, `model` in body.
- `gpt-4o` / `gpt-4.1` / `claude-sonnet-4.5`: standard `max_tokens` works.
- `gpt-5.5`, `gpt-5.6-*`, `gemini-2.5-pro`: **reasoning models** — require
  `max_completion_tokens` (NOT `max_tokens`) AND a LARGE budget, else the hidden
  reasoning consumes the budget and `content` is EMPTY / truncated (finish=length).

## What to build

### 1. `src/twdf/panel/openai_compat_provider.py` — `OpenAICompatibleProvider`
A DROP-IN `ModelProvider` (same protocol as `src/twdf/panel/azure_provider.py`:
attributes/methods `name`, `generate(prompt,*,seed,max_tokens,temperature)`,
`generate_messages(messages,*,seed,max_tokens,temperature)`, `get_stats()`).
Mirror `azure_provider.py` closely (it is the template) but:
- **base_url** from arg/env `COPILOT_PROXY_ENDPOINT` (default `http://127.0.0.1:8787/v1`);
  request URL = `{base_url}/chat/completions`.
- **Auth OPTIONAL**: if env `COPILOT_PROXY_KEY` is set, send `Authorization: Bearer <key>`;
  otherwise send NO auth header (proxy needs none). NEVER log/print the key.
- **`model` in body** (OpenAI style).
- **token_param** ("max_tokens" | "max_completion_tokens") and **omit_temperature**
  (bool) constructor args, same semantics as azure_provider (and same cache-key
  handling: only include them in the hashlib key when non-default, so existing
  caches are not invalidated).
- **Reasoning-model budget:** add a constructor arg `min_completion_tokens: int = 0`.
  When `token_param == "max_completion_tokens"`, the effective token budget sent =
  `max(max_tokens, min_completion_tokens)`. This lets configs guarantee e.g. 4096
  tokens so panel JSON (real_panel asks for 500-600) isn't starved by hidden reasoning.
  (Keep the cache key based on the ORIGINAL max_tokens arg to stay comparable across
  providers — document this choice in a comment.)
- **Empty-content guard:** after a 200, if `choices[0].message.content` is empty/whitespace,
  treat as a retryable failure (retry up to max_retries, then raise a clear RuntimeError
  naming the model + finish_reason). This prevents silently caching empty panel answers.
- Same hashlib (sha256) deterministic cache in `data/cache/panel/`, same 429/5xx retry
  logic. Cache key MUST include `self.name` (model) to avoid cross-model collisions.

### 2. `src/twdf/experiments/provider_factory.py` — add a branch
Add provider types `{"openai_compatible", "copilot_proxy", "proxy", "ghc"}` →
build `OpenAICompatibleProvider`, passing through `base_url`/`token_param`/
`omit_temperature`/`min_completion_tokens` from the config `provider:` block.
Do NOT change the existing `github` (default) or `azure` branches' behavior.

### 3. Configs (mirror existing, point at proxy)
Copy the structure of `configs/confirmatory_axis1_azure_gpt5.yaml` and
`configs/axis2_powered_azure_gpt5.yaml` into NEW files, one MODELS set = the
cross-vendor trio, provider block targeting the proxy. Use the SAME item seed as the
primary configs (matched items). Suggest ONE config per axis with all three models,
OR three per axis — your call, but keep item seeds matched and outputs distinct
(e.g. `results/confirmatory_axis1_crossvendor.json`, `results/axis2_powered_crossvendor.json`).
Models + per-model token handling:
- `gpt-5.5`  → token_param: max_completion_tokens, omit_temperature: true, min_completion_tokens: 4096
- `claude-sonnet-4.5` → token_param: max_tokens (standard), temperature kept
- `gemini-2.5-pro` → token_param: max_completion_tokens, min_completion_tokens: 4096
  (Per-model overrides: if the config schema only supports one provider block for all
  models, instead make the token_param/min_completion_tokens settable PER MODEL — check
  how `models:` + `provider:` interact in provider_factory/model_names_from_config and
  pick the cleanest approach that lets each model use the right token param. Document it.)

### 4. Offline tests (`tests/test_openai_compat_provider.py`)
Use `monkeypatch`/mock of `requests.post` (do NOT hit the network). Cover:
- URL/base_url construction (default + env override); model in body.
- No auth header when key absent; Bearer header when `COPILOT_PROXY_KEY` set.
- token_param routing: max_tokens vs max_completion_tokens field in payload.
- min_completion_tokens raises the sent budget but NOT the cache key.
- omit_temperature drops temperature from payload.
- Empty-content 200 → retried then raises (not cached).
- Deterministic cache hit on second identical call (no 2nd HTTP call).
- provider_factory builds OpenAICompatibleProvider for the new type strings.
Run: `$env:PYTHONPATH=(Resolve-Path .\src).Path; python -m pytest tests\test_openai_compat_provider.py -q`

## Rigor / hygiene
- Additive only; do NOT alter github/azure provider behavior or any frozen config.
- Before opening the PR: `git merge origin/main --no-edit` into your branch and verify
  `git diff --diff-filter=D --name-only origin/main..HEAD` is EMPTY (no deletions —
  this repo has a stale-branch deletion trap).
- Do NOT commit scratch/logs. Commit trailer: `Co-authored-by: Copilot <copilot@github.com>`.
- Open a DRAFT PR with a body listing files + offline test results. Then STOP and report
  the PR number + branch + a summary. Do not merge.
