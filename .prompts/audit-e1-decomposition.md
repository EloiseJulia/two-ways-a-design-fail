You are an INDEPENDENT reviewer performing the HOSTILE PRE-MERGE audit of draft
PR #2 (branch feature/e1-multicond, 12 commits) of the top-venue HCI METHODS
project "two-ways-a-design-fail". A single silent statistical error voids the
paper. You did NOT write this code; NO prior context. Treat all descriptions,
commit messages, prior-agent "24/24 pass / strong thresholds / honest" claims, and
every number as UNTRUSTED. Re-derive from source + real re-runs. Assume defects
exist. READ-ONLY: report only; do NOT fix/commit/merge/push. Clean up scratch.

## WHERE
Worktree (read-only): C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail\.worktrees\e1-multicond
Confirm `pwd` + branch first. Throwaway venv OK; do NOT modify tracked files or the
main checkout. Read SPEC.md, INTERFACES.md, PROGRESS.md,
docs/research/2026-07-14-overdispersion-decomposition.md.

## WHAT PR #2 CONTAINS
(a) multi-condition E1 over all 6 Bansal UI conditions; (b) a robustness analysis
of over-dispersion vs task selection; (c) THE KEY NEW PART: a variance
decomposition answering "is between-user reliance a STABLE USER trait or USER x
TASK interaction?" via SPLIT-HALF RELIABILITY (primary) + a GLMM (corroboration).
Headline claim: Human (no-AI) reliance is substantially a stable user trait
(stable_user_share=0.74 [0.69,0.79]); under AI assistance it becomes
task-dependent (share ~0.32-0.41; Expert ~0). Framing implication: axis-1's "who
the user is" becomes "user x task" in AI conditions.

## PHASE 1 — DECOMPOSITION METHODOLOGY (most important; probe each yourself)
1. **Split-half correctness** (`src/twdf/metrics/variance_decomposition.py`):
   verify it splits each user's TASKS (not trials/rows arbitrarily) into disjoint
   halves, computes per-user reliance RATE per half, correlates ACROSS users;
   verify the Spearman-Brown formula and ICC(2,1) are implemented correctly
   (check against a hand/scipy computation on a small fixture); verify the
   min_tasks threshold and bootstrap CI (resampled over USERS) are sound. Confirm
   the derivation of stable_user_share from reliability is defensible and
   documented.
2. **Validation-generator HONESTY (critical anti-gaming check):** read the
   synthetic data generators used by the tests. Confirm the "pure stable-user"
   generator truly has NO user x task interaction (each user a fixed p across
   tasks) and the "pure user x task" generator truly has NO stable user main
   effect. A generator secretly matched to the estimator would make the STRONG
   thresholds meaningless. THEN write your OWN INDEPENDENT generators (different
   code) for the two extremes and confirm split-half gives high (>=0.7) vs low
   (<=0.2) reliability respectively. If your independent test disagrees with the
   repo's, that is a BLOCKER.
3. **Strong thresholds real:** confirm the test assertions are pure-stable
   reliability>=0.7 & share>=0.8, pure-interaction <=0.2 — and that they are NOT
   trivially passable / were NOT weakened. Confirm they actually run (not skipped).
4. **GLMM honesty:** the GLMM is bounded (maxiter=10) and reported as
   "did not converge". Verify: (a) no fabricated GLMM numbers are used anywhere in
   results/claims; (b) the docs/research write-up frames this HONESTLY as "not
   obtained within our compute budget", NOT as "GLMM is fundamentally unable"
   (maxiter=10 is a deliberately low cap — flag any overclaim); (c) the headline
   rests on split-half alone, which is legitimate. Judge whether capping at 10 and
   calling it "did not converge" is honest or misleading in the write-up.
5. **Conclusion not overstated:** does the 0.74 vs 0.32-0.41 gap actually support
   "stable trait (no-AI) -> task-dependent (AI)"? Check the CIs overlap/separation.
   Confirm the single-dataset caveat + replication-needed are stated. Confirm no
   premature tau_disp/tau_level freezing.

## PHASE 2 — logic + identity + leakage
Diff review (`git --no-pager diff main...feature/e1-multicond`): identity keys
(dataset/domain/task/condition/user/seed), silent row drops, any builtin `hash(`
or unordered iteration feeding numbers, hidden global normalization/leakage.

## PHASE 3 — ARTIFACT + regression + determinism
Throwaway venv `pip install -e .`. Run FULL `pytest` (expect ~24; attribute any
failure by reproducing on a clean `main` worktree). Run
`python -m twdf.experiments.e1_decomposition --config configs/e1_decomposition.yaml`
in >=2 SEPARATE processes — confirm split-half numbers byte-identical (determinism;
no hash bug). Also confirm e1_vslice, e1_multicond, e1_robustness still run
(regression). Confirm results/e1_decomposition.json matches a fresh run (no
hallucinated numbers).

## PHASE 4 — diff hygiene
No debug/scratch residue, no accidental deletions, data/raw not committed, no
stray venv/*.txt/verified.json.

## OUTPUT
Ranked findings (BLOCKER/MAJOR/MINOR/UNVERIFIED) with file:line + proof (your probe
code + output) + minimal fix, then explicit VERDICT: PASS or FAIL. This is the
merge gate for a methods paper — "it runs" != "correct". The single most important
questions: is the split-half decomposition CORRECT and HONESTLY VALIDATED (not
gamed), and is the GLMM non-convergence framed honestly? Return to Manager; do NOT
merge.
