# audit-confirmatory-axis1-pipeline — INDEPENDENT hostile + §4.5 audit (PR #12)

Fresh independent auditor. You did NOT write this. REPORT ONLY; do not fix/commit/merge. Offline
`pytest -m "not live"` only (quota scarce; do NOT run live). Evidence = file:line + reproduced
numbers. End with **VERDICT: PASS** or **VERDICT: FAIL**.

## What this PR does
Implements, BLIND (before any confirmatory panel data), the pre-registered confirmatory axis-1
(H1a) analysis: `src/twdf/analysis/confirmatory_axis1.py` (pure analysis) + a thin runner
`src/twdf/experiments/confirmatory_axis1.py` + `configs/confirmatory_axis1.yaml`. Branch
`feature/confirmatory-axis1-pipeline` (draft PR #12), merged up to date with main. Source of truth:
`docs/plans/preregistration-axis1.md` §§1–8, `SPEC.md` §3 H1a / §8 stats / §2 D5.4.

## Checks (each PASS/FAIL + file:line + reproduced number)
1. **Conflict-conditioned DV:** reliance measured on System-1 ≠ AI trials (not raw agreement).
   Verify the conflict/reliance predicates and that unconditional is only supplementary.
2. **Axis-1 DV is beta-binomial OVER-DISPERSION** (excess over binomial p(1−p)), NEVER raw variance.
   Confirm it reuses `overdispersion.betabinom_overdispersion*` correctly.
3. **Primary estimator = within-task difficulty-controlled counterfactual difference** (difficulty
   cancels within pair); reuses `within_task_diff`. Secondary = cross-condition Spearman via the
   PR #11 `panel_human_condition_correspondence` (n<3 guard + ceiling flag intact).
4. **Baselines genuine + must be BEATEN with a CI:** random, mean-predictor (ρ≈0 by construction),
   prompt-only, single-model, rational-Bayes null. Confirm "beaten" means the confirmatory signal
   exceeds the baseline with a bootstrap CI that excludes it — not a hand-wave. Check the
   rational-Bayes null is a defensible appropriate-reliance anchor, not a strawman.
5. **BH correction** at α=0.05 across the reported hypotheses; adjusted p ≥ raw p; monotone.
6. **PER-MODEL reporting, NO pooling** across gpt-4o vs gpt-4.1-mini (model-mix confound). Cross-model
   agreement is a summary only.
7. **Bootstrap resamples the right UNITS** (personas × seeds × models), not rows i.i.d.; permutation
   test is a valid label shuffle. Verify seeds → determinism.
8. **Reports REGARDLESS of outcome:** a null panel yields a fully-populated result (CI includes 0,
   mean-predictor not beaten) — not an exception. Reproduce with the null-synthetic test.
9. **No leakage / researcher-DoF:** no ground-truth/human-outcome enters any agent prompt or serves
   as a predictor; item selection uses AI-side exogenous props only; τ stays UNFROZEN (no
   thresholding here). hashlib only; no builtin `hash(`.
10. **Reuse, not reimplementation:** the statistics come from the existing `overdispersion` helpers
    and the PR #11 module; flag any silent reimplementation that diverges from them.
11. **Tests meaningful:** run `pytest -m "not live" tests/test_confirmatory_axis1.py -q` (report
    count). Confirm the known-signal test builds REAL between-user over-dispersion + a monotone
    panel↔human rank and requires beating ALL baselines; the null test builds no structure. Not
    tautological. Also confirm no existing test regressed (the diff adds files only — verify).
12. **Records/merge safety:** `docs/DECISIONS.md` D5.5 says it implements the pre-registered analysis
    BLIND, does NOT change H1a/prereg, τ unfrozen; `INTERFACES.md` §8 updated;
    `git diff --name-status main...feature/confirmatory-axis1-pipeline` deletes nothing.

Final line: **VERDICT: PASS** or **VERDICT: FAIL**.
