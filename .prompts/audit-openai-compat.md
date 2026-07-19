# AUDIT — PR #21 OpenAI-compatible proxy provider (feat/openai-compat-provider)

Independent, HOSTILE + methodology audit. You did NOT write this. Try to BREAK it.
Report findings + a single `VERDICT: PASS`/`VERDICT: FAIL` line. Do NOT merge/edit/push.
Do NOT run live proxy calls (no network to the proxy needed; use offline/mock only).

## Repo / env
`C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail` (Windows PowerShell).
- `$env:PYTHONPATH=(Resolve-Path .\src).Path` to run python; `$env:GH_TOKEN=$null` before `gh`.
- Full test suite hangs on network downloads — run ONLY the provider test file(s).
- Review diff: `git fetch origin; git diff origin/main...origin/feat/openai-compat-provider`.
- Key files: `src/twdf/panel/openai_compat_provider.py`,
  `src/twdf/experiments/provider_factory.py`,
  `configs/confirmatory_axis1_crossvendor.yaml`, `configs/axis2_powered_crossvendor.yaml`,
  `tests/test_openai_compat_provider.py`.

## Context (what it must do)
A DROP-IN `ModelProvider` for a local OpenAI-compatible proxy (ghc-api,
`http://127.0.0.1:8787/v1`, no token). Supports reasoning models (gpt-5.x,
gemini-2.5-pro) that need `max_completion_tokens` + a large budget or they return
EMPTY content. Backs the FROZEN cross-vendor robustness arm (DECISIONS D5.18:
gpt-5.5 + claude-sonnet-4.5 + gemini-2.5-pro; per-model, no pooling; matched items seed=42).

## Adversarial checks
1. **Token routing:** confirm `token_param=max_tokens` puts `max_tokens` in the payload and
   `max_completion_tokens` puts THAT field (and not both). Confirm `min_completion_tokens`
   raises the SENT budget (`max(max_tokens, min_completion_tokens)`) but the **cache key uses
   the ORIGINAL max_tokens** (so entries stay comparable across providers). Prove by test/inspection.
2. **Empty-content guard:** a 200 with empty/whitespace/None content must RETRY then RAISE — and
   must NEVER be written to cache. Confirm no cache file is created on the empty path. Also confirm
   list-style content (`content: [{type,text}]`) is joined correctly.
3. **Optional auth:** NO Authorization header when `COPILOT_PROXY_KEY` unset; Bearer header when set.
   Confirm the key is never logged/printed. base_url resolves arg > `COPILOT_PROXY_ENDPOINT` > default.
4. **Cache determinism + NO collision:** hashlib (not builtin hash); cache key includes model name so
   `gpt-5.5` / `claude-sonnet-4.5` / `gemini-2.5-pro` cannot collide with each other OR with the
   PRIMARY GitHub-Models `gpt-4o`/`gpt-4.1-mini` entries in the SHARED `data/cache/panel/`. This is
   critical: the cross-vendor arm shares the primary cache dir — prove no cross-provider/cross-model
   key collision (same messages+params but different model must yield different keys).
5. **provider_factory:** the new types `{openai_compatible, copilot_proxy, proxy, ghc}` build the new
   provider; **per-model `provider:` overrides merge OVER the top-level block** (so gpt-5.5 gets
   max_completion_tokens while claude keeps max_tokens under one `type: ghc`). CRITICAL REGRESSION:
   confirm the `github` (default, absent type) and `azure` branches are UNCHANGED in behavior.
6. **Additive only:** confirm NO frozen config (confirmatory_axis1.yaml, axis2_powered*, azure_gpt5)
   or provider (provider.py, azure_provider.py) changed behavior. `git diff --diff-filter=D` empty.
7. **Configs match the prereg (D5.18):** item seed=42 (matched to primary), same 6 personas + same 5
   UI conditions (axis-1) / same dark condition (axis-2), models exactly the frozen trio, per-model
   token params sane (gpt-5.5/gemini → max_completion_tokens+min 4096; claude → max_tokens), outputs
   distinct (`*_crossvendor.json`), and they do NOT overwrite any primary output file.

## Run the tests
`$env:PYTHONPATH=(Resolve-Path .\src).Path; python -m pytest tests\test_openai_compat_provider.py -q`
Report pass counts. Add your own adversarial test if you doubt a claim (in a scratch file you delete).

## §4.5 methodology
Does anything here retroactively alter a frozen primary (D5.11/D5.13) or contaminate its cache? Is the
shared-cache design safe? Is the arm faithfully mirroring the primary protocol per D5.18? Flag any way a
proxy result could be silently conflated with the primary GitHub-Models result.

## Deliverable
Per-check CORRECT/INCOMPLETE/WRONG with evidence (commands+outputs), then `VERDICT: PASS`/`FAIL` with
blocking reasons. No merge, no edits to the branch.
