You are an INDEPENDENT reviewer doing a FOCUSED HOSTILE RE-AUDIT of draft PR #2
(branch feature/e1-multicond) of the HCI METHODS project "two-ways-a-design-fail".
A prior audit FAILED it with 2 blockers (B1: over-dispersion fragile to task
selection; B2: "stratified pooling" misnomer). A fix subagent claims both fixed +
added a robustness analysis. Trust NOTHING it claims — re-verify from source +
real re-runs. You are also asked to adjudicate a STATISTICAL INTERPRETATION
DISPUTE (below). READ-ONLY: report only; do NOT fix/commit/merge/push; clean up
scratch files.

## WHERE
Worktree (read-only): C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail\.worktrees\e1-multicond
Confirm `pwd` + branch first. Throwaway venv OK; do NOT modify tracked files or
the main checkout.

## PART A — verify the fixes
- **B2 fix**: confirm the function was renamed to accurately reflect
  within-domain per-user aggregation (not "stratified pooling"), docstring matches
  the code, all call sites updated, and the between-subjects-on-domain fact is
  stated. Re-confirm (from raw data) that every user appears in exactly one domain.
- **B1 fix**: confirm `task_selection` is now an explicit, documented config knob
  (default `all` = maximum data), not a magic number; and that a robustness
  analysis (`results/e1_multicond_robustness.json` + summary) exists and reports
  over-dispersion under >=3 schemes HONESTLY.
- **Minors**: stray results file removed; permutation docstring matches code; the
  determinism test now spawns a SUBPROCESS (or varies PYTHONHASHSEED) so it would
  actually catch cross-process nondeterminism — verify it genuinely would (try
  making the stub non-deterministic in a scratch copy and confirm the test would
  fail; or reason precisely about why it catches it).
- **No regression**: `betabinom_overdispersion` math unchanged; `e1_vslice` still
  works; full `pytest` passes on a fresh `pip install -e .`.
- **Determinism**: run `e1_multicond` (default config) in >=2 SEPARATE processes;
  confirm byte-identical numbers.

## PART B — ADJUDICATE THE INTERPRETATION DISPUTE (important, methodological)
The robustness table reports Human over-dispersion rho by task-selection scheme:
  all (50 tasks, ~11200 trials, ~40 trials/user):     rho ~ 0.0666
  first_10_shared (10 tasks, ~2340 trials, ~8/user):  rho ~ 0.0369
  min_per_domain (5 tasks, ~1220 trials, ~4/user):    rho ~ 0.0000
The fix subagent concluded the signal is a "FRAGILE task-selection ARTIFACT" and
suggested pivoting away from axis-1.
The Manager's competing hypothesis: rho increases MONOTONICALLY with
trials-per-user, which is the classic signature of a POWER-LIMITED beta-binomial
estimator (you cannot detect between-user over-dispersion with only ~4 trials per
user), NOT evidence the signal is fake — and with full data the signal is LARGEST.
Independently determine which reading the DATA supports:
1. Compute, for EACH scheme, the exact trials-per-user distribution (min/median/
   max) and the over-dispersion rho WITH its confidence interval (does the CI at
   the `all` scheme, ~40 trials/user, EXCLUDE 0? that would support a real,
   power-limited signal; a CI hugging 0 everywhere would support the artifact
   read).
2. Optionally run a small simulation: generate synthetic data with a KNOWN
   positive over-dispersion, subsample to ~4, ~8, ~40 trials/user, and check
   whether the estimator's recovered rho behaves like the observed table (rises
   with trials/user). If the known-signal simulation reproduces the monotone rise,
   that strongly supports the POWER interpretation over the ARTIFACT interpretation.
3. Give an explicit, evidence-backed VERDICT on the dispute: is the observed
   pattern better explained by (i) low estimation power at few trials/user, or
   (ii) a genuine task-selection artifact / non-existent signal? Note what the PI
   should conclude and whether the code's documentation currently frames it fairly
   (the fix subagent's "fragile artifact / pivot away" framing may be WRONG or
   overstated — say so if the evidence contradicts it).

## OUTPUT
Ranked findings (BLOCKER/MAJOR/MINOR/UNVERIFIED) with proof, a clear PASS/FAIL
verdict on the fixes, AND a separate, evidence-backed adjudication of the
power-vs-artifact interpretation with your recommendation for how PROGRESS/SPEC
should frame it. Return to the Manager; do NOT merge.
