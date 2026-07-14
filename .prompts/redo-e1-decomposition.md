You are the IMPLEMENTATION subagent REDOING slice "e1-decomposition" of the HCI
METHODS project "two-ways-a-design-fail". A prior attempt chose a WRONG primary
method and WEAKENED its validation tests to fit it. You will do it correctly.
Rigor > speed; your work faces an independent hostile + methodology audit.

## WHERE
Worktree: C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail\.worktrees\e1-multicond
Confirm `pwd` + branch (feature/e1-multicond) first. Work ONLY here; not main.
Commit trailer EVERY commit: `Co-authored-by: Copilot <copilot@github.com>`. Push
to draft PR #2; do NOT mark ready; NEVER merge.

## CRITICAL STRUCTURAL FACTS (verified by the Manager on the real Bansal data)
- 99.7% of (condition, user, task) cells have EXACTLY ONE observation. Therefore
  USER x TASK interaction is CONFOUNDED with Bernoulli sampling noise AT THE CELL
  LEVEL. An ANOVA-style variance partition on single-observation cells CANNOT
  separate user x task interaction from noise. The prior attempt used exactly this
  ANOVA approach and then RELAXED its tests (e.g. pure-stable-user gave only
  share>0.4 instead of ~1.0). That is unacceptable. Do NOT repeat it.
- Each user sees 20-50 DISTINCT tasks (median 50). Therefore SPLIT-HALF
  RELIABILITY is well-powered and is the CORRECT PRIMARY method here.

## THE QUESTION
Of the between-user variation in reliance, how much is a STABLE USER trait
(consistent across tasks) vs USER x TASK (a user's reliance depends on the task)?
This decides whether axis-1's "safety depends on WHO the user is" should be "who
the user is" vs "user x task".

## SCOPE — build this (you MAY reuse/repair the uncommitted files already in the
## worktree: src/twdf/metrics/variance_decomposition.py,
## src/twdf/experiments/e1_decomposition.py, configs/e1_decomposition.yaml,
## tests/test_variance_decomposition.py — but you MUST fix the method + tests below)

1. **PRIMARY — split-half reliability** (well-identified on this data):
   `split_half_reliability(trials, condition, *, n_splits, seed, min_tasks=8)`:
   for each of `n_splits` seeded random splits, split each user's TASKS into two
   disjoint halves A/B; compute each user's reliance RATE on A and on B; correlate
   across users. Report ICC(2,1) AND Spearman, mean +/- sd over splits, plus a
   Spearman-Brown-corrected full-length reliability. Include only users with
   >= min_tasks tasks (document threshold). Interpretation: high reliability =>
   reliance is a STABLE USER TRAIT; low => TASK-DEPENDENT. Derive
   `stable_user_share` from the reliability (document the mapping) with a bootstrap
   CI over users. This is the headline number.

2. **CORROBORATION — GLMM** (optional, report ONLY if it converges & validates):
   `variance_components_glmm(trials, condition, *, seed)` using statsmodels
   `BinomialBayesMixedGLM` with crossed random intercepts for user and task and a
   user x task term, WITHIN domain (domain is between-subjects: each user & task in
   ONE domain). NOTE: unlike Gaussian ANOVA, the Bernoulli likelihood DOES identify
   the interaction variance via partial pooling, so a correct GLMM can separate
   interaction from noise. Report posterior mean+SD of sigma2_user,
   sigma2_task, sigma2_user_task and stable share. If it does NOT converge or fails
   validation, SAY SO HONESTLY and rely on split-half — do NOT fabricate numbers,
   do NOT keep the discredited ANOVA-on-cells method as if it were valid. If you
   keep any descriptive ANOVA number, label it prominently "NOT identified on
   single-observation cells; descriptive only".

3. **Experiment/report** `e1_decomposition.py` (+ config): run on the `all`
   task-selection for ALL 6 conditions; write `results/e1_decomposition.json` with
   split-half reliability (primary) + GLMM (if valid) + run_manifest. Focus
   reporting on Human; report all 6.

4. **VALIDATION TESTS — STRONG, DO NOT WEAKEN.** The METHOD must meet these; if a
   method can't, it is not reported as primary. Generate synthetic trial data with
   the SAME structure (each user ~40 tasks, one obs per cell, between-subjects
   domain):
   - **pure stable-user** (fixed per-user reliance p across tasks, NO interaction):
     split-half reliability HIGH (ICC and Spearman-Brown reliability >= 0.7) and
     stable_user_share >= 0.8.
   - **pure user x task** (each user's per-task p is independent, NO stable main
     effect): split-half reliability LOW (<= 0.2) and stable_user_share <= 0.2.
   - **null** (all users same p): reliability ~ 0.
   - If you include the GLMM, it must recover stable_share ~1 / ~0 on the first two
     respectively, else mark it non-validated and exclude from headline claims.
   Do NOT relax these thresholds to fit a weak estimator. Keep ALL existing repo
   tests passing.

5. **docs/research/2026-07-14-overdispersion-decomposition.md**: explain the
   single-observation-per-cell identifiability issue, why split-half is the primary
   method, the split-half results per condition (with CI), the GLMM corroboration
   (or its non-convergence), and the HONEST conclusion on whether Bansal reliance
   over-dispersion is a stable user trait or user x task — and what that means for
   framing axis-1 ("who the user is" vs "user x task"). No overclaiming.

## GUARDRAILS
Deterministic under fixed seed; reruns identical across processes (no builtin
hash()). No leakage; identity keys include dataset/domain/task/condition/user/seed.
No premature threshold freezing. All reported numbers from the actual re-run file,
never restated from memory.

## SELF-CHECK
`pip install -e .`; `pytest` ALL pass with the STRONG thresholds; `python -m
twdf.experiments.e1_decomposition --config configs/e1_decomposition.yaml` runs
end-to-end TWICE with identical numbers; e1_vslice + e1_multicond + e1_robustness
still run. `git status` clean (no venv/*.txt/report scratch outside docs/;
data/raw not committed). Update PROGRESS.md.

## DELIVERY
Commit in logical steps; push to feature/e1-multicond (draft, never merge). Return
to Manager: the split-half reliability table per condition (quote results file),
the derived stable_user_share + CI for Human, the GLMM result or honest
non-convergence, your one-paragraph HONEST conclusion (stable trait vs user x
task), full pytest summary (showing the STRONG thresholds), and what the auditor
should scrutinize.
