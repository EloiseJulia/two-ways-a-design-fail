You are the IMPLEMENTATION subagent for slice "e1-decomposition" of the top-venue
HCI METHODS project "two-ways-a-design-fail". Rigor > speed; "it runs" != "it is
correct". Your work faces an independent hostile + methodology audit. You build on
the existing PR #2 branch feature/e1-multicond (held pending this analysis).

## WHERE
Worktree: C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail\.worktrees\e1-multicond
Confirm `pwd` + branch (feature/e1-multicond) first. Work ONLY here; not the main
checkout. Commit trailer EVERY commit: `Co-authored-by: Copilot <copilot@github.com>`.
Push to the draft PR #2; do NOT mark ready; NEVER merge.

## READ FIRST (in the worktree)
SPEC.md (§0 axis-1, §5 E1), INTERFACES.md, PROGRESS.md, and the existing code:
`src/twdf/{data,metrics,panel,experiments}`, `src/twdf/experiments/e1_robustness.py`
(currently UNTRACKED), `results/e1_multicond_robustness.json` (UNTRACKED),
`src/twdf/metrics/overdispersion.py` (contains verified `betabinom_overdispersion`
and `betabinom_overdispersion_within_domain`).

## BACKGROUND — the scientific question this slice must answer
Prior analysis established (evidence, do not re-litigate):
- Human reliance between-user OVER-DISPERSION on Bansal is REAL: full-data
  rho=0.067, bootstrap 95% CI [0.052, 0.081]; at 10 tasks rho=0.037, CI
  [0.009, 0.069] — both exclude 0.
- A known-signal simulation showed the beta-binomial estimator is UNBIASED even at
  4 trials/user; yet REAL data collapses to ~0 at few tasks. This implies the
  over-dispersion is NOT purely a stable per-user trait but is (partly)
  TASK-DEPENDENT (user x task interaction). This slice MEASURES that decomposition.

**Central question:** Of the between-user variation in reliance, how much is a
STABLE USER main effect (a user reliance propensity consistent across tasks) vs a
USER x TASK interaction (a user's reliance depends on the task)? This determines
whether axis-1's "safety depends on WHO the user is" should be "who the user is"
vs "user x task".

## SCOPE — build exactly this
0. **Commit the orphaned robustness deliverable FIRST** (the fix subagent created
   but never committed it): `git add src/twdf/experiments/e1_robustness.py
   results/e1_multicond_robustness.json` as one commit completing BLOCKER-1.
1. **Dependency:** add `statsmodels` to `pyproject.toml` deps (needed for the GLMM).
   Keep the package `pip install -e .`-able.
2. **`src/twdf/metrics/variance_decomposition.py`** with:
   - `variance_components(trials, condition, *, seed) -> dict`: fit a crossed
     random-effects LOGISTIC mixed model to trial-level `relied` with random
     intercepts for USER and TASK and a USER x TASK interaction component. Recommended
     tool: statsmodels `BinomialBayesMixedGLM` (variational Bayes, supports crossed
     random effects on Windows/pure-Python). Return posterior mean + SD for
     sigma2_user, sigma2_task, sigma2_user_task, and a derived
     `stable_user_share = sigma2_user / (sigma2_user + sigma2_user_task)`.
     IMPORTANT STRUCTURE: domain is BETWEEN-SUBJECTS (each user in ONE domain; each
     task belongs to ONE domain). So user x task is crossed only WITHIN domain.
     Handle this correctly (fit within-domain then combine, or include domain as a
     blocking fixed effect). Document the model + assumptions in the docstring.
   - `split_half_reliability(trials, condition, *, n_splits, seed) -> dict`: a
     robust, model-free corroboration. For each of `n_splits` random splits, split
     each user's TASKS into halves A/B, compute per-user reliance rate in each half,
     and correlate across users (Spearman + ICC(2,1)). High correlation => stable
     user trait; low => task-dependent. Report mean +/- sd across splits. Seeded,
     deterministic. (Only include users with >=4 tasks so halves are meaningful;
     document the threshold.)
3. **`src/twdf/experiments/e1_decomposition.py`** (+ config `configs/e1_decomposition.yaml`
   + `python -m twdf.experiments.e1_decomposition --config ...`): run both analyses
   on the `all` task-selection for ALL 6 conditions (focus reporting on Human but
   report all), write `results/e1_decomposition.json` with variance components +
   split-half reliability + a run_manifest. Raw output to file.
4. **Tests (VALIDATION is the point — mirror how the estimator was validated):**
   - Synthetic data with a KNOWN STABLE-USER-ONLY signal (each user a fixed p across
     tasks, no interaction) => `stable_user_share` ~ 1 and split-half correlation
     HIGH.
   - Synthetic data with a KNOWN USER x TASK-ONLY signal (each user's per-task p is
     independent noise, no stable main effect) => `stable_user_share` ~ 0 and
     split-half correlation LOW.
   - A null (all users same p) => components near 0.
   Keep ALL existing tests passing. Ensure cross-process determinism (no builtin
   `hash()`; seed everything; the repo already uses hashlib + subprocess det. test).
5. **`docs/research/2026-07-14-overdispersion-decomposition.md`**: summarize (a) the
   prior adjudication finding (real signal; estimator unbiased at 4 trials/user;
   real collapse at few tasks), and (b) THIS slice's decomposition result — the
   stable-user vs user x task shares (with uncertainty) and split-half reliability,
   per condition. State the HONEST conclusion for how SPEC/PROGRESS should frame
   axis-1 (stable trait vs user x task), whatever the numbers say. Do NOT overclaim.

## METHODOLOGY GUARDRAILS (auditor WILL check)
- Correct crossed structure with domain between-subjects (user & task nested in
  domain; user x task within domain). No pseudoreplication; each trial once.
- The decomposition METHOD must be validated on known-signal synthetic data (tests
  above) — a decomposition you can't validate is worthless for a methods paper.
- Report UNCERTAINTY on variance components (posterior SD / bootstrap), not point
  estimates alone. GLMM variance components near a boundary (0) need honest CIs.
- Deterministic under fixed seed; reruns identical across processes.
- No leakage; no premature threshold freezing (tau_disp/tau_level stay unfrozen).
- Identity keys include dataset/domain/task/condition/user/seed.
- No hallucinated numbers: all reported numbers from the actual re-run output file.

## SELF-CHECK
`pip install -e .`; `pytest` ALL pass (incl. the new decomposition validation
tests); `python -m twdf.experiments.e1_decomposition --config configs/e1_decomposition.yaml`
runs end-to-end TWICE with identical numbers; regression: e1_vslice + e1_multicond
still run. `git status` clean of scratch (no venvs, no *.txt, no report md outside
docs/); data/raw not committed; update PROGRESS.md (Doing/Done + module status).

## DELIVERY
Commit in logical steps; push to feature/e1-multicond (draft, never merge). Return
to Manager: the variance-component table (sigma2_user, sigma2_user_task,
stable_user_share +/- uncertainty) and split-half reliability PER condition (quote
results file); your honest one-paragraph conclusion on whether Bansal reliance
over-dispersion is dominated by stable user traits or user x task interaction;
full pytest summary; and anything the auditor should scrutinize (esp. GLMM
convergence + the domain-nesting handling).
