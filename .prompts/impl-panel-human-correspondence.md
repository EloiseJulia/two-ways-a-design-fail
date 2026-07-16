# impl-panel-human-correspondence — pre-specified H1a secondary readout (PR #11)

You implement in the worktree `.worktrees\panel-human-correspondence` (branch
`feature/panel-human-correspondence`, DRAFT PR #11). Do NOT touch `main`, do NOT merge, do NOT run
live/networked tests. Offline work + `pytest -m "not live"` only. Commit to the branch and push;
report to the Manager.

## Purpose (rigor: build BLIND, before the confirmatory panel run)
Implement the PRE-REGISTERED cross-condition correspondence readout for H1a (prereg §1 secondary /
§4): does the agent-panel's **disagreement per Bansal UI condition** rank-correlate with the REAL
**human reliance over-dispersion per condition**? Writing this analysis BEFORE the panel data exists
is deliberate preregistration discipline — you have the fixed human target now; the panel side is
plugged in later. Do NOT tune anything to a panel effect (none exists yet).

## Fixed human target (already computed on real Bansal data — DO NOT recompute)
`results/e1_multicond.json` → `results.human_overdispersion` maps each condition to a dict with
`rho` (beta-binomial over-dispersion), `rho_ci_lower/upper`, `mean_p`, `empirical_var`,
`binomial_var`, `excess_var`, `n_users`, `n_trials`. The 5 AI conditions (exclude `"Human"`, the
no-AI baseline) and their human `rho` are:
`Conf.`=0.0206, `Conf.+Single`=0.0109, `Conf.+Double`=0.0263, `Conf.+Adaptive`=0.0139,
`Conf.+Adaptive (Expert)`=0.0000 (near-ceiling: excess_var≈0, mean_p high, n_users=195).
Load these from the JSON at runtime (do not hard-code the numbers in the module; hard-coding only
allowed in tests as expected values).

## What to build
`src/twdf/analysis/panel_human_correspondence.py` (new module; create `analysis/` package if
needed) exposing a clear function, e.g.:
```
def panel_human_condition_correspondence(
    panel_disagreement_by_condition: dict[str, float],   # condition -> panel disagreement
    human_overdispersion_path: str | Path = "results/e1_multicond.json",
    *, seed: int = 42, n_boot: int = 10000, n_perm: int = 10000,
) -> CorrespondenceResult
```
Behavior:
1. Load human `rho` per condition from the JSON; align on the conditions PRESENT IN BOTH the panel
   dict and the human target, EXCLUDING `"Human"`. Preserve a canonical condition order.
2. Compute the **Spearman** rank correlation between panel disagreement and human over-dispersion
   across the shared conditions. REUSE `twdf.metrics.overdispersion.condition_correlation` (it has
   the built-in n<3 DEGENERATE guard — if <3 shared conditions, return degenerate=True and DO NOT
   report a meaningful correlation). Also report Pearson as secondary.
3. **Permutation test**: shuffle the human-target labels vs panel values (n_perm) to get a p-value
   for the observed Spearman. **Bootstrap CI**: resample the paired (condition) points with
   replacement (n_boot) for a CI on the correlation. Use the provided seeds for determinism.
4. **Ceiling/low-variance flag**: for each condition, flag it as ceiling/uninterpretable when the
   human `excess_var` is ≈0 (e.g. `excess_var < 1e-4`) or `mean_p` is near 0/1 (e.g. |mean_p-0.5|
   very large AND empirical_var tiny). Return BOTH the full-5-condition result AND a
   "ceiling-excluded" sensitivity result (correlation over the non-ceiling conditions), clearly
   labeled. (This mirrors the discriminator ceiling-artifact lesson: near-ceiling over-dispersion
   ≈0 is mechanically uninterpretable — see docs/DECISIONS D3.2 / PROGRESS Known pitfalls.)
5. Return a dataclass `CorrespondenceResult` with: shared conditions (ordered), aligned
   (panel_disagreement, human_rho) pairs, spearman_rho, spearman_p (permutation), bootstrap_ci,
   pearson_r, n_conditions, degenerate (bool), ceiling_flags (per condition), and the
   ceiling-excluded sensitivity sub-result. Make it JSON-serializable (a `to_dict`).
6. NO leakage / no researcher-DoF violation: this reads the FIXED human target and a panel input;
   it must not read or depend on any human outcome inside the panel, and must not tune thresholds.
   hashlib only if you hash anything; deterministic.

## Tests (offline) `tests/test_panel_human_correspondence.py`
- **Known positive signal:** synthetic panel disagreement chosen to rank IDENTICALLY to the real
  human targets → assert spearman_rho ≈ 1, permutation p < 0.05, bootstrap CI excludes 0.
- **Known negative/anti signal:** panel disagreement ranked OPPOSITE → assert spearman_rho ≈ −1.
- **Null:** random/shuffled panel disagreement (fixed seed) → assert p not significant (≈ chance);
  do this over several seeds or assert the permutation p distribution is reasonable.
- **Degenerate guard:** <3 shared conditions → degenerate=True, no meaningful correlation reported.
- **Ceiling flag:** `Conf.+Adaptive (Expert)` is flagged ceiling (loads real JSON); the
  ceiling-excluded sensitivity result drops it and recomputes over the remaining 4.
- **Determinism:** same inputs+seed → identical outputs (bootstrap/permutation reproducible).
- Load the REAL `results/e1_multicond.json` in at least one test to confirm the loader + alignment
  work on the actual artifact (it is committed, offline).
- Run `pytest -m "not live" tests/test_panel_human_correspondence.py -q` and report pass count.

## Records (same PR)
- `docs/DECISIONS.md`: add an entry (next id after D5.2, e.g. **D5.3**) — what: pre-specified the
  panel↔human cross-condition correspondence readout BLIND before the confirmatory run; why:
  operationalizes H1a secondary (prereg §1/§4) and the panel-validity claim, with a ceiling-artifact
  guard; implication: the confirmatory just plugs panel disagreement in. NOTE it does NOT change
  H1a or the prereg — it implements an already-specified analysis.
- `INTERFACES.md` §8 AS-BUILT: add the new module + function signature + `CorrespondenceResult`.
- Commit with trailer `Co-authored-by: Copilot <copilot@github.com>`.

## Report back
Files changed, the function/dataclass shape, test pass count, how the ceiling flag behaves on the
real JSON, and any ambiguity resolved. Do NOT merge.
