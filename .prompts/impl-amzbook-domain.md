# IMPL — generalize the panel pipeline to a `domain` parameter + amzbook 2nd-domain configs

You are an IMPLEMENT subagent (fresh, non-interactive). Build the slice in a git WORKTREE, open a
DRAFT PR, and STOP. **Do NOT merge. Do NOT make live LLM/panel calls** (the Manager runs panels on the
proxy after an independent audit). Offline/MockProvider tests only. Return a concise report.

## Repo / env
`C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail` (Windows PowerShell).
- `twdf` NOT pip-installed: `$env:PYTHONPATH=(Resolve-Path .\src).Path` to run python.
- `$env:GH_TOKEN=$null` before any `gh`.
- Full test suite hangs on network downloads — run ONLY the offline test files you add/touch.
- Branch from latest main in a NEW worktree:
  `git worktree add .worktrees/amzbook -b feat/amzbook-domain origin/main`

## WHY (context)
The paper PIVOTED (DECISIONS D5.22/D5.24) to "LLM-panel screening signals are model-capability-dependent
+ persona-robust susceptibility". Reviewer attack #1 is still "single domain (beer)". We are adding a
2nd domain, **amzbook** (Amazon book-review sentiment, binary), to test whether the capability-dependence
and persona-robustness findings GENERALIZE across domains. The panel already ran on beer for the
cross-vendor arm (D5.18) and the capability ladder (D5.23); we now replicate on amzbook.

## The problem to fix
The item-selection layer is HARDCODED to beer:
- `src/twdf/data/item_selector.py`: `compute_human_reliance_variance` filters `df['extra'].apply(... == 'beer')`
  (`df_beer`), and `select_hard_items` calls `load_beer_tasks(...)` ("load all beer tasks").
- `src/twdf/data/bansal_tasks.py`: `load_beer_tasks` (beer-specific), but a `TASK_URLS`/domain map and
  `ADAPTIVE_CONF_THRESHOLD` (beer 0.892, amzbook 0.889) already exist + auto-download works.
The runners `src/twdf/experiments/confirmatory_axis1.py` (`build_tasks`) and
`src/twdf/experiments/axis2_powered.py` build tasks via `item_selector` with NO domain param.

## What to build

### 1. Generalize the loaders/selectors to a `domain` parameter (BACKWARD-COMPATIBLE)
- `bansal_tasks.py`: add `load_domain_tasks(domain: str, n_tasks=..., ...)` that loads/downloads the
  correct `task-sentiment-<domain>.json` (beer/amzbook/lsat) via the existing URL map, using the
  per-domain `adaptive_conf_threshold(domain)`. Keep `load_beer_tasks` working (delegate to
  `load_domain_tasks('beer', ...)`).
- `item_selector.py`: add a `domain: str = "beer"` param to `compute_human_reliance_variance` and
  `select_hard_items` (and `ItemSelectionCriteria` if needed). Replace the hardcoded `== 'beer'` filter
  and `load_beer_tasks` call with the `domain`-parameterized versions. **Default `domain="beer"` so all
  existing beer configs/results are byte-identical (verify: beer selection with seed=42 still returns the
  SAME 20 task IDs `['10','11','13','14','17','18','21','25','28','29','33','35','38','4','40','44','45','48','49','6']`).**
- Thread `domain` from config → `build_tasks` in BOTH runners: read `config.get("domain", config.get("item_selection",{}).get("domain","beer"))` and pass to `select_hard_items`. Do NOT change behavior when `domain` absent (beer).

### 2. amzbook human over-dispersion anchor (for the axis-1 correspondence)
The current `results/e1_multicond.json` pools all 3 domains. Generate a **domain-matched amzbook anchor**:
add an optional `--domain` filter to `src/twdf/experiments/e1_multicond.py` (default = current all-domain
behavior for backward compat) that restricts the human decisions to `extra.task == <domain>` before
computing per-condition human over-dispersion. Produce `results/e1_multicond_amzbook.json`. (This is the
amzbook analogue of the beer anchor; the axis-1 amzbook configs will point at it. Correspondence is n=5 /
low-power — that is expected and fine; the panel-side over-dispersion/disagreement is the primary readout.)
Also (optional, nice) `results/e1_multicond_beer.json` for a clean beer-matched anchor, but do NOT change
the existing all-domain `results/e1_multicond.json`.

### 3. amzbook configs (mirror the beer arms; matched structure)
Create FOUR configs by copying the beer equivalents and changing ONLY domain + item source + output +
(axis-1) the human anchor path:
- `configs/axis2_powered_crossvendor_amzbook.yaml`  (models = frontier trio gpt-5.5/claude-sonnet-4.5/gemini-2.5-pro)
- `configs/axis2_powered_capladder_amzbook.yaml`     (models = gpt-4o-mini/gpt-4.1/gpt-4o/gpt-5.5)
- `configs/confirmatory_axis1_crossvendor_amzbook.yaml`
- `configs/confirmatory_axis1_capladder_amzbook.yaml`
Each: add `domain: amzbook` (threaded to item selection), keep matched item seeds (axis-1=42, axis-2=2024),
same 6 personas + same UI conditions, provider `type: ghc` (proxy) with the SAME per-model token overrides
and throttling as the beer capladder/crossvendor (inter_call_sleep 2.0, max_retries 8, call_budget 5000,
min_completion_tokens 4096 for gpt-5.5/gemini). axis-1 configs set
`human_overdispersion_path: results/e1_multicond_amzbook.json`. Distinct outputs
`results/*_amzbook.json`. Do NOT overwrite any beer output.

### 4. Offline tests (`tests/test_amzbook_domain.py`, MockProvider / no network beyond the one-time task download)
- `load_domain_tasks('amzbook')` returns amzbook stimuli (domain=='amzbook', non-empty, has ai_pred/conf).
- `select_hard_items(domain='amzbook', seed=42)` returns 20 amzbook items, deterministic across 2 calls.
- **Backward-compat: `select_hard_items(domain='beer', seed=42)` (and the default) returns the SAME 20 beer
  IDs as before** (guard against regressions to the frozen beer arm).
- `build_tasks` in both runners honors `domain: amzbook`.
- e1_multicond `--domain amzbook` filter yields amzbook-only anchor (task_domains == ['amzbook']).
Run: `$env:PYTHONPATH=(Resolve-Path .\src).Path; python -m pytest tests\test_amzbook_domain.py -q`
Also re-run the existing beer-path tests you might affect (e.g. `tests\test_e4_compliance.py`,
`tests\test_panel_real.py`) to prove no regression.

## Rigor / hygiene
- Additive + backward-compatible: existing beer configs/results/tests MUST be unaffected (default domain=beer).
- Before opening the PR: `git merge origin/main --no-edit` into your branch; verify
  `git diff --diff-filter=D --name-only origin/main..HEAD` is EMPTY (stale-branch deletion trap).
- Do NOT commit scratch/logs. Do NOT run live panels (no proxy calls). Commit trailer:
  `Co-authored-by: Copilot <copilot@github.com>`.
- Open a DRAFT PR listing files + offline test results, then STOP and report the PR number + branch +
  a summary (esp. confirm the beer backward-compat test passes and amzbook selection returns 20 items).
