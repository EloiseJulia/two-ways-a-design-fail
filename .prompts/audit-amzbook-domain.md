# AUDIT — PR #23 amzbook domain generalization (feat/amzbook-domain)

Independent HOSTILE + methodology audit. You did NOT write this. Try to break it, ESPECIALLY the
backward-compatibility (must not perturb the FROZEN beer arms D5.11/D5.18/D5.23). Report per-check +
`VERDICT: PASS`/`FAIL`. Do NOT merge/edit/push. Offline only — no live LLM/proxy calls.

## Repo / env
`C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail` (Windows PowerShell).
- `$env:PYTHONPATH=(Resolve-Path .\src).Path`; `$env:GH_TOKEN=$null` before `gh`. Full suite hangs on
  network — run only the named test files.
- Diff: `git fetch origin; git diff origin/main...origin/feat/amzbook-domain`.
- Purpose: add amzbook as a 2nd domain (generalize beer-hardcoded item selection to a `domain` param) to
  test cross-domain generalization of the capability-dependence (D5.22/D5.24) + persona-robustness findings.

## Checks (be adversarial)
1. **BACKWARD COMPAT (CRITICAL):** with default/absent domain (`domain="beer"`), `select_hard_items(seed=42)`
   MUST return the SAME 20 beer IDs `['10','11','13','14','17','18','21','25','28','29','33','35','38','4','40','44','45','48','49','6']`
   as origin/main. Prove by running BOTH origin/main and the branch. Confirm no existing beer config, frozen
   result, or beer-path code path changed behavior. `compute_human_reliance_variance` default must still be beer.
2. **amzbook wiring:** `load_domain_tasks('amzbook')` returns amzbook stimuli (auto-download ok);
   `select_hard_items(domain='amzbook', seed=42)` returns 20 amzbook IDs, deterministic across 2 calls;
   `build_tasks` in BOTH `confirmatory_axis1.py` and `axis2_powered.py` honors `domain: amzbook`.
3. **amzbook human anchor:** `results/e1_multicond_amzbook.json` is amzbook-ONLY (task_domains==['amzbook']);
   the e1_multicond `--domain` filter restricts to `extra.task==amzbook`; the all-domain
   `results/e1_multicond.json` is UNCHANGED. Sanity-check the per-condition human over-dispersion values.
4. **configs (4):** `*_amzbook.yaml` for cross-vendor + capladder × axis-1 + axis-2 carry `domain: amzbook`,
   matched item seeds (axis-1=42, axis-2=2024), the correct model sets (frontier trio / gpt-4o-mini→gpt-4.1
   →gpt-4o→gpt-5.5), provider `type: ghc`, throttling (inter_call_sleep 2.0, max_retries 8, call_budget 5000,
   gpt-5.5/gemini min_completion_tokens 4096), axis-1 anchor `results/e1_multicond_amzbook.json`, distinct
   `*_amzbook.json` outputs that do NOT overwrite any beer output. Personas + UI conditions identical to beer.
5. **Additive / no regression:** `git diff --diff-filter=D` empty; no frozen beer config/result/provider
   behavior changed. Run `tests\test_amzbook_domain.py` + a couple of beer-path suites
   (`tests\test_e4_compliance.py tests\test_panel_real.py`) — all pass.
6. **No live calls / methodology:** confirm the impl made no live panel/proxy calls; amzbook is a faithful
   replication of the beer protocol (same personas/conditions/estimators, only domain+items differ); no
   human-outcome leakage introduced (human reliance still only in item selection).

## Deliverable
Per-check CORRECT/INCOMPLETE/WRONG with command evidence (run origin/main vs branch for the beer
backward-compat check), then `VERDICT: PASS`/`FAIL`.
