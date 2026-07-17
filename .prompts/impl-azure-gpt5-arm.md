# impl-azure-gpt5-arm — wire AzureFoundryProvider into the runners + gpt-5.x configs (PR #19)

Implement in the worktree `.worktrees\azure-gpt5-arm` (branch `feature/azure-gpt5-arm`, DRAFT PR #19).
Do NOT touch `main`, do NOT merge. Offline only + `pytest -m "not live"` (NO live/networked calls — the
PI has not set Azure creds yet). Commit + push; report to the Manager.

## Purpose (D5.15 cross-generation robustness arm)
The PI's Azure has the gpt-5.x family (not gpt-4o/gpt-4.1-mini). We keep the PRIMARY confirmatory
axis-1 (D5.11) + powered axis-2 (D5.13) on the free GitHub {gpt-4o, gpt-4.1-mini}, and run the SAME
design on Azure **gpt-5.2 + gpt-5.4** as a SECONDARY robustness arm. This slice makes that arm a
one-command run once creds are set: wire `AzureFoundryProvider` (PR #9,
`src/twdf/panel/azure_provider.py`) into the two runners + add Azure gpt-5.x configs. Read
`docs/DECISIONS.md` D5.15, `docs/plans/azure-setup.md`, `src/twdf/panel/azure_provider.py`,
`src/twdf/experiments/confirmatory_axis1.py` + `src/twdf/experiments/axis2_powered.py` (their
`build_provider`), and `configs/confirmatory_axis1.yaml` / `configs/axis2_powered.yaml`.

## Requirements
1. **Config-selected provider (backward compatible):** extend the provider-building in BOTH runners so a
   config can select the provider. Default/absent = the existing `GitHubModelsProvider` (free path
   UNCHANGED — the primary runs must still work exactly as now). If the config sets e.g.
   `provider: { type: "azure", api_style: "azure_openai" }` (or `"foundry"`), build an
   `AzureFoundryProvider(deployment=<model_name>, api_style=..., call_budget=..., inter_call_sleep=...,
   cache_dir=...)` for each entry in `models` (the `models` entries are the Azure DEPLOYMENT names, e.g.
   `gpt-5.2`, `gpt-5.4`). Reuse the existing `collect_panel_responses`/`run_panel` flow unchanged.
   Prefer a shared helper so both runners behave identically; keep the change minimal + surgical.
2. **Azure configs (distinct outputs, same items):**
   - `configs/confirmatory_axis1_azure_gpt5.yaml`: copy of `confirmatory_axis1.yaml` but
     `models: ["gpt-5.2", "gpt-5.4"]`, `provider.type: "azure"` (+ `api_style`), item seed 42 UNCHANGED
     (SAME items as the primary, so cross-generation is on matched items), and
     `output_file: "results/confirmatory_axis1_gpt5.json"` (MUST NOT clobber the primary
     `results/confirmatory_axis1.json`).
   - `configs/axis2_powered_azure_gpt5.yaml`: same idea from `axis2_powered.yaml`; models gpt-5.2/gpt-5.4;
     item seed 2024 UNCHANGED; `output_file: "results/axis2_powered_gpt5.json"`.
   - Add a clear header comment: SECONDARY robustness arm (D5.15), gpt-5.3-codex excluded (code model),
     gpt-5.4-pro excluded unless PI opts in.
3. **gpt-5.x API adaptation hooks (best-effort, offline):** gpt-5.x models on Azure may reject
   `temperature` and/or require `max_completion_tokens` instead of `max_tokens`, and may ignore `seed`.
   If `AzureFoundryProvider` hard-codes `max_tokens`/`temperature` in the request body, add a
   CONFIG/CONSTRUCTOR-GATED option (e.g. `token_param="max_completion_tokens"`,
   `omit_temperature=True`) so the gpt-5.x configs can set it — WITHOUT changing default behavior for the
   existing Azure OpenAI path. Do NOT guess the exact gpt-5.x contract; just make it configurable + note
   in a comment that the Manager will confirm/adjust via the live cred-check. If the provider already
   supports overriding these, just expose them in config.
4. Deterministic; hashlib only; no builtin `hash(`. NO live calls anywhere in tests.

## Tests `tests/test_azure_gpt5_wiring.py` (offline, mocks only)
- **Runner builds AzureFoundryProvider from an azure config** (monkeypatch env `AZURE_OPENAI_*` +
  monkeypatch the provider's HTTP call to a mock) → `collect_panel_responses`/the runner produces
  responses via the Azure provider WITHOUT real network; the provider's `name`/deployment reflects
  `gpt-5.2`/`gpt-5.4`.
- **Backward compat:** a GitHub config still builds `GitHubModelsProvider` (default path unchanged).
- **Config parsing:** the two Azure configs load; models are gpt-5.2/gpt-5.4; output files are the
  `_gpt5` variants (NOT the primary files); item seeds match the primary (42 / 2024).
- **Token-param/temperature option** (if added) is threaded from config to the provider request body
  (assert on the mocked request payload).
- Run `pytest -m "not live" tests/test_azure_gpt5_wiring.py tests/test_azure_provider.py -q` (no
  regression to the existing 22 Azure offline tests); report counts.

## Records
- `docs/DECISIONS.md`: append a short note under D5.15 (or a D5.16) that the wiring + configs are built
  and offline-tested; the live run awaits the PI's Azure creds + a cred/connectivity check. `INTERFACES.md`
  §8 update (runners now accept an Azure provider via config). Commit trailer
  `Co-authored-by: Copilot <copilot@github.com>`.

## Report back
Files changed, how the provider is config-selected, the two configs' models/outputs/seeds, any gpt-5.x
adaptation hooks added, test pass counts, and confirmation the free GitHub path is unchanged. Do NOT
merge; do NOT run live.
