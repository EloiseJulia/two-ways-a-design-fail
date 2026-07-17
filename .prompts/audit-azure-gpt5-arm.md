# audit-azure-gpt5-arm — INDEPENDENT audit (PR #19, build-only wiring)

Fresh independent auditor. REPORT ONLY; no fix/commit/merge. Offline `pytest -m "not live"` ONLY (do
NOT run live — Azure creds are not set). Evidence = file:line + reproduced values. End with
**VERDICT: PASS** or **VERDICT: FAIL**.

## What this PR does
Wires `AzureFoundryProvider` (PR #9) into the confirmatory_axis1 + axis2_powered runners via a
config-selected provider factory, and adds Azure gpt-5.x configs for the D5.15 cross-generation
robustness arm. BUILD-ONLY; the live run awaits the PI's Azure creds. Branch `feature/azure-gpt5-arm`
(PR #19), merged up to date with main.

## Checks (PASS/FAIL + evidence)
1. **BACKWARD COMPATIBILITY (critical):** with NO `provider.type` (or `type: github`), the factory
   returns `GitHubModelsProvider` — the PRIMARY free-path confirmatory + axis-2 runs are UNCHANGED.
   Verify in `provider_factory.build_provider_from_config` (default "github") and that the existing
   `tests/test_confirmatory_axis1.py` + `tests/test_axis2_powered.py` still pass unchanged.
2. **Azure selection:** `provider.type: azure` (+ `api_style`) → `AzureFoundryProvider(deployment=<model
   name>)` per `models` entry (gpt-5.2/gpt-5.4). Reproduce via a monkeypatched env + mocked HTTP that the
   runner builds the Azure provider and produces responses with NO real network.
3. **Configs correct + non-clobbering:** `configs/confirmatory_axis1_azure_gpt5.yaml` (models gpt-5.2/
   gpt-5.4, seed 42, output `results/confirmatory_axis1_gpt5.json`) and `configs/axis2_powered_azure_gpt5.yaml`
   (gpt-5.2/gpt-5.4, seed 2024, output `results/axis2_powered_gpt5.json`). Outputs are the `_gpt5`
   variants (NEVER the primary `results/confirmatory_axis1.json` / `results/axis2_powered.json`); item
   seeds MATCH the primary (42 / 2024) so the arm uses matched items. gpt-5.3-codex / gpt-5.4-pro excluded.
4. **gpt-5.x adaptation hooks are CONFIG-GATED + non-default:** `token_param`
   (e.g. `max_completion_tokens`) and `omit_temperature` are threaded from config into the request body
   ONLY when set; the DEFAULT Azure-OpenAI path (existing 22 tests) is unchanged. Verify on a mocked
   request payload that setting them changes the body, and that absent → default (`max_tokens` +
   temperature present).
5. **No live calls anywhere in tests; determinism; hashlib only / no builtin `hash(`.**
6. **Tests:** `pytest -m "not live" tests/test_azure_gpt5_wiring.py tests/test_azure_provider.py
   tests/test_confirmatory_axis1.py tests/test_axis2_powered.py -q` pass count (expect ~41); confirm no
   regression to the existing 22 Azure offline tests or the primary-runner tests.
7. **Merge safety:** `git diff --name-status main...feature/azure-gpt5-arm` deletes NOTHING (esp. not
   any PR #7/#11–#18 files); additive + the surgical runner/provider edits.
8. **Records:** `docs/DECISIONS.md` note (D5.15/D5.16) + `INTERFACES.md` §8.

Final line: **VERDICT: PASS** or **VERDICT: FAIL**.
