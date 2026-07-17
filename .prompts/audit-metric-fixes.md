# AUDIT — PR #20 "three latent metric bugs" (fix/metric-boundary-bugs)

You are an INDEPENDENT, HOSTILE audit subagent (fresh session). You did NOT write
this code. Your job: try to BREAK the fix and its claims. Report findings only —
**do NOT merge, do NOT push, do NOT edit code.** Return a clear verdict: PASS or FAIL.

## Context
Repo: `C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail` (Windows PowerShell).
- `twdf` is NOT pip-installed: set `$env:PYTHONPATH=(Resolve-Path .\src).Path` before running python.
- Set `$env:GH_TOKEN=$null` before any `gh` command.
- The FULL test suite hangs on network downloads (test_bansal_discriminator / decomposition).
  Run offline-safe test files individually; do NOT run the whole suite.

PR #20 fixes three bugs found by a prior bug-hunt. Review the diff:
`git fetch origin; git diff origin/main...origin/fix/metric-boundary-bugs`
Key files: `src/twdf/metrics/overdispersion.py`, `src/twdf/features/ui_features.py`,
`tests/test_metric_boundary_fixes.py`, `docs/DECISIONS.md` (D5.16),
`docs/paper/reviewer-rebuttals.md` (A10/A11).

## What to verify (be adversarial on EACH)

### Fix 1 — betabinom boundary guard (overdispersion.py::betabinom_overdispersion)
Claim: users all pinned at the reliance boundary (mean_p in {0,1}) previously returned
rho ~ 0.999 (WRONG; truth is rho=0, no between-user variance); a `binomial_variance<=0`
guard now returns rho=0.
- Reproduce: does all-(0,10) and all-(10,10) now give rho=0? Did it give ~0.999 before the fix
  (check out origin/main and run)?
- CRITICAL: does the guard SUPPRESS genuine over-dispersion? Confirm half-(0,10)/half-(10,10)
  (genuine MAXIMAL dispersion, mean_p=0.5, binomial_var>0) STILL returns high rho. If the guard
  fires there, it's a FAIL.
- Any other inputs where the guard wrongly zeroes a real signal? mean_p just inside boundary?

### Fix 2 — Wrong-AI-GT ui feature (ui_features.py)
Claim: `wrong_ai` and `_has_authority_cue` now include `"Wrong-AI-GT (dark)"` (preregistered D5.13).
- Confirm both flags are True for `Wrong-AI-GT (dark)` AND still True for `Wrong-AI (dark)`.
- Confirm NON-dark conditions (Conf.+Single, etc.) are NOT flagged wrong_ai.
- Is `Wrong-AI-GT (dark)` the exact canonical string used elsewhere (grep the codebase /
  configs / prereg)? A near-miss string would silently miss.

### Fix 3 — degenerate/constant guard (overdispersion.py::condition_correlation)
Claim: an EARLY guard returns null stats before permutation/bootstrap for n<3 or constant input,
preventing an `np.percentile([])` crash / meaningless stats.
- Reproduce the OLD crash/NaN on origin/main (n=1, n=2, constant array) if possible.
- Confirm the fixed version returns `degenerate=True` and does NOT crash for n<3 and constant inputs.
- CRITICAL REGRESSION: confirm a VALID case (n>=3, non-constant) is UNCHANGED — same spearman_rho /
  degenerate=False as origin/main. The early guard must not alter valid results.

### Claim — "no already-merged result changes"
Independently verify: grep `results/*.json` for any `rho` near 0.99; check whether any merged
result was computed via `condition_correlation` on degenerate input or via Wrong-AI-GT ui-features.
If ANY merged number would change, that's a methodology finding (report it).

### §4.5 methodology audit
- Does this fix retroactively alter any PREREGISTERED / FROZEN result (D5.11 confirmatory axis-1,
  D5.13 axis-2)? If those runs haven't executed yet, the fix is pre-data (OK); confirm that.
- Is the DECISIONS.md D5.16 entry HONEST and complete (does it overstate/understate)?
- Is the new A11 limitation (item-selection circularity) fairly characterized as a disclosed
  design risk, not a hidden bug?

## Run the tests yourself
`$env:PYTHONPATH=(Resolve-Path .\src).Path; python -m pytest tests\test_metric_boundary_fixes.py tests\test_metrics.py tests\test_ui_features.py -q`
Report pass/fail counts. Try to add your own adversarial cases if you doubt a claim.

## Deliverable
A concise report: for each fix — CORRECT / INCOMPLETE / WRONG, with evidence (commands + outputs).
Then a single overall verdict line: `VERDICT: PASS` or `VERDICT: FAIL` with the blocking reasons.
Do NOT merge or modify anything.
