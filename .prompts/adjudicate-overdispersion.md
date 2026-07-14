You are an INDEPENDENT statistical adjudicator. Tightly scoped, READ-ONLY: do NOT
modify tracked files, commit, or merge. Clean up any scratch files/venv you make.
Work fast; this is a single focused question.

## CONTEXT
Project "two-ways-a-design-fail", worktree (read-only):
C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail\.worktrees\e1-multicond
Confirm pwd first. The metric `betabinom_overdispersion` (in
src/twdf/metrics/overdispersion.py) estimates between-user reliance
over-dispersion (rho) on real Bansal CHI'21 data, separating it from binomial
sampling noise. A robustness table (results/e1_multicond_robustness.json) shows
Human over-dispersion rho by task-selection scheme:
  all            (~40 trials/user): rho ~ 0.0666
  first_10_shared(~8 trials/user):  rho ~ 0.0369
  min_per_domain (~4 trials/user):  rho ~ 1e-6 (estimator floor)
Under low trials/user, MOST conditions pin to the ~1e-6 floor.

## THE DISPUTE TO SETTLE
Hypothesis P (power): rho rises with trials/user because the beta-binomial
estimator lacks POWER to detect over-dispersion at few trials/user; the signal is
REAL and best estimated with full data.
Hypothesis A (artifact): the over-dispersion is a task-selection ARTIFACT / not a
real signal.

## DO EXACTLY THIS (make a throwaway venv, `pip install -e .`)
1. **Real-data CIs**: For the `Human` condition, compute rho WITH a bootstrap 95%
   CI (resample users, >=2000 reps, seeded) under BOTH `all` and `first_10_shared`
   task selection (reuse the repo's loader + bootstrap_ci; do NOT reimplement the
   estimator). Report whether each CI excludes 0. (Use the repo's existing data
   loader / experiment code to get per-user (n_relied, n_trials) for Human under
   each scheme.)
2. **Known-signal simulation** (the decisive test): simulate users from a
   beta-binomial with a KNOWN, fixed positive over-dispersion (pick a rho close to
   the observed ~0.05-0.07, with realistic mean reliance ~0.69). Draw ~283 users.
   Then estimate rho with the repo's `betabinom_overdispersion` at trials/user =
   4, 8, 20, 40 (subsample/redraw accordingly). Repeat over several seeds and
   report the mean recovered rho at each trials/user level. QUESTION: does the
   estimator, given a KNOWN nonzero signal, ALSO produce ~floor at 4/user and rise
   toward the true value by 40/user? If YES, the observed real-data monotone rise
   is explained by estimation power (supports P), NOT artifact.
3. Optionally: do a null simulation (KNOWN rho = 0, i.e. all users share one p) at
   40 trials/user and confirm the estimator returns ~floor (guards against the
   estimator inventing over-dispersion from high trials alone).

## OUTPUT (concise)
- The two real-data CIs (all, first_10) for Human, and whether they exclude 0.
- The simulation table: recovered rho vs trials/user for the known-positive signal
  (and the null check).
- A crisp VERDICT: does the evidence support Hypothesis P (power-limited, real
  signal) or Hypothesis A (artifact)? State plainly which, and how the paper's
  PROGRESS/SPEC should frame the "fragility": as an estimation-power/minimum-
  trials-per-user requirement, or as a genuine artifact/limitation.
Return the report to the Manager. Do NOT commit or merge.
