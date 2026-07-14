You are the IMPLEMENTATION subagent for slice "e1-multicond" of the top-venue HCI
METHODS project "two-ways-a-design-fail". Rigor > speed. "It runs" != "it is
correct" — your work will face an independent hostile + methodology audit.

## READ FIRST (in the worktree, read-only)
SPEC.md (§0 axis-1, §5 E1, §8 statistics), INTERFACES.md (the contract — implement
strictly to it; extend, don't fork the schema), PROGRESS.md (v0 is merged; read
the merge log). The existing v0 code is on `main` and already in your worktree:
`src/twdf/{data,metrics,panel,experiments}`, `tests/`, `configs/vslice_v0.yaml`,
`results/e1_vslice_v0.json`.

## WHERE
Worktree: C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail\.worktrees\e1-multicond
Branch feature/e1-multicond (draft PR #2). Confirm `pwd` + branch first. Work ONLY
here; DO NOT touch the main checkout. Commit trailer EVERY commit:
`Co-authored-by: Copilot <copilot@github.com>`. Push to the draft PR; do NOT mark
ready; NEVER merge.

## CONTEXT — the real Bansal data (already verified)
6 UI conditions exist in the `condition` column: `Human`, `Conf.`, `Conf.+Single`,
`Conf.+Double`, `Conf.+Adaptive`, `Conf.+Adaptive (Expert)`. 3 task domains in the
`task` column: `beer`, `amzbook`, `lsat` (different difficulty). v0 only used 2
conditions, giving a DEGENERATE (n=2) correlation. This slice broadens axis-1 to
ALL 6 conditions so the correlation is non-degenerate, with proper small-n stats.

## GOAL
Compute, per UI condition, the real human between-user reliance OVER-DISPERSION
(axis-1, beta-binomial), difficulty-controlled across task domains; get the
synthetic-panel disagreement per condition; and correlate disagreement vs human
over-dispersion across the >=5 conditions with APPROPRIATE small-n statistics
(Spearman rank + permutation test + bootstrap CI) — NOT a bare Pearson point.

## SCOPE — build exactly this
1. **Config:** add `configs/e1_multicond.yaml` selecting ALL 6 conditions (or a
   configurable list, defaulting to all 6) and a set of shared tasks per domain.
   Keep `configs/vslice_v0.yaml` working (backward compatible).
2. **Data (Module A):** generalize the selector in `src/twdf/data/bansal.py` (and/
   or the experiment) from a single UI *pair* to an arbitrary LIST of conditions.
   Keep the canonical schema (INTERFACES §1). Preserve determinism (sorted
   iteration; no builtin `hash()`; the v0 fix used hashlib — keep that).
3. **Metrics (Module C) — RIGOR:**
   - Per-condition human over-dispersion via the EXISTING
     `betabinom_overdispersion` (do not reimplement; reuse). Each user's
     (n_relied, n_trials) computed per condition.
   - **DIFFICULTY CONTROL across task domains:** beer/amzbook/lsat differ in
     difficulty. Do NOT pool raw across domains in a way that lets difficulty
     drive the signal. Compute over-dispersion controlling for task domain (e.g.
     within-domain then aggregate, or domain as a covariate/stratum) and DOCUMENT
     the exact method in the docstring. The auditor will check difficulty is not
     confounding the cross-condition comparison.
   - **Correlation across conditions:** implement `condition_correlation(...)` that
     takes the per-condition (disagreement, over-dispersion) pairs and returns:
     Spearman rho (rank-based, robust for small n and monotonic-not-linear
     expectation), a PERMUTATION-test p-value (shuffle condition labels, >=10000
     perms, seeded), and a bootstrap CI over (users/seeds). Keep the v0
     `degenerate` guard: if n_conditions < 3, flag degenerate and do not present
     it as a result.
4. **Experiment (Module E):** `src/twdf/experiments/e1_multicond.py` (+ `python -m
   twdf.experiments.e1_multicond --config configs/e1_multicond.yaml`) runs the
   whole chain over all 6 conditions and writes
   `results/e1_multicond.json`: per-condition mean reliance, n_users, over-
   dispersion rho + CI, synthetic panel disagreement, and the cross-condition
   Spearman rho + permutation p + bootstrap CI, plus a run_manifest (config hash,
   seeds, timestamp). Raw output to file; never restate numbers from memory.
5. **Tests:** unit tests for the multi-condition selector (correct row counts per
   condition), the difficulty-control aggregation (a synthetic case where pooling
   would be confounded by difficulty but the controlled estimator is not), and
   `condition_correlation` (a monotonic synthetic relation yields Spearman≈1 with
   small permutation p; a random relation yields non-significant p). Keep all
   existing v0 tests passing. Ensure cross-PROCESS determinism (no builtin hash).

## HONESTY GUARDRAILS (auditor WILL check)
- The synthetic panel disagreement is still a STUB. Therefore the
  disagreement-vs-over-dispersion correlation is a MECHANISM/plumbing check of
  the statistics, NOT scientific evidence, until the real panel (Module B)
  replaces the stub. State this explicitly in the JSON `note` and in PROGRESS.md.
  Do NOT tune the stub's per-condition disagreement to manufacture a nice
  correlation — derive it from documented, fixed condition properties/seed; if
  you make it correlate by construction, DISCLOSE that it is circular-by-design.
- The per-condition HUMAN over-dispersion numbers ARE a genuine finding — report
  them plainly with CIs.
- No leakage / no global normalization fit across conditions that peeks; no
  premature threshold freezing (tau_disp/tau_level remain the PI's to freeze).
- Identity keys include every output-affecting dimension
  (dataset/task/condition/user/seed).

## SELF-CHECK
`pip install -e .`; `pytest` ALL pass; `python -m twdf.experiments.e1_multicond
--config configs/e1_multicond.yaml` runs end-to-end twice with IDENTICAL numbers;
diff only intended files; data/raw not committed; update PROGRESS.md (Doing/Done +
module status). Remove any scratch files.

## DELIVERY
Commit in logical steps; push to feature/e1-multicond (draft, never merge).
Return to Manager: what you built, the difficulty-control method you chose and
why, the per-condition human over-dispersion table (quote results file), the
cross-condition Spearman rho + permutation p + CI, full pytest summary, and the
honest caveat about the stub. List anything the auditor should scrutinize.
