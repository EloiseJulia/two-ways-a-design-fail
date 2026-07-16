# impl-e3-loio — leave-one-item-out generalization harness (PR #15)

Implement in the worktree `.worktrees\e3-loio` (branch `feature/e3-loio`, DRAFT PR #15). Do NOT touch
`main`, do NOT merge. Offline only + `pytest -m "not live"`. Commit + push; report to the Manager.

## Purpose (SPEC §5 E3)
Build a LEAKAGE-SAFE leave-one-item-out (LOIO) cross-validation harness that tests axis-1
GENERALIZATION: fit any normalization / threshold / model parameters on the TRAIN split ONLY, then
predict the held-out item's axis-1 signal DIRECTION + RANKING, and score against the actual.
Pass criteria (SPEC §5 E3 row): **direction hit rate > random (0.5)** and **Spearman ρ > 0
(significant)** between predicted and actual item ranking. Read `SPEC.md` §5 (E3 row), §9 Known
pitfalls (LOIO leakage), and reuse existing metrics in `twdf.metrics.overdispersion` and (optionally)
`twdf.features.ui_features` for feature-based prediction.

## What to build — `src/twdf/experiments/e3_loio.py` (+ a small `src/twdf/analysis/loio.py` if a pure
core helps testing)
1. A pure core, e.g. `loio_generalization(items: list[LOIOItem], predict_fn, *, seed: int = 42,
   n_perm: int = 10000) -> LOIOResult` where each `LOIOItem` carries the observed axis-1 target and
   whatever features/train-usable signal it has. For each held-out item i: call `predict_fn(train=all
   items except i)` to fit, then predict item i; collect predicted vs actual.
2. **LEAKAGE FIREWALL (critical):** the harness MUST pass the fit function ONLY the train items; the
   held-out item's target is NEVER visible to fitting. Make this structurally enforced (predict_fn
   receives train items only; the test item's target is withheld) and add a test that fails if the
   test item leaks into fit.
3. Metrics on the collected (predicted, actual) pairs: **direction hit rate** (fraction where sign of
   predicted change matches actual, vs a 0.5 baseline — report a binomial p-value), **Spearman ρ** of
   predicted vs actual ranking with a **permutation p-value** (reuse scipy + a permutation like the
   existing metrics). `LOIOResult` dataclass with hit_rate, hit_p, spearman_rho, spearman_p, n,
   per-item table; JSON `to_dict`. Guard n<3 (degenerate) like the other modules.
4. A thin runner `main()` (config-driven) is optional; the PURE core + tests are the deliverable.
   If you add a runner, its data path must be offline/synthetic in tests (no live calls).

## Constraints
- Deterministic, pure; hashlib only if hashing; no builtin `hash(`. No network in tests.
- Leakage-safe by construction (see #2). No τ freezing here.

## Tests `tests/test_e3_loio.py`
- **Known-generalization signal:** synthetic items whose axis-1 target is a monotone function of a
  train-derivable feature → LOIO direction hit rate > 0.5 (p<0.05) and Spearman ρ > 0 (p<0.05).
- **Null:** items with no learnable structure (random target) → hit rate ≈ 0.5, ρ not significant.
- **LEAKAGE test:** assert the held-out item's target is not accessible to `predict_fn` (e.g. the
  fit receives train-only; a predict_fn that tries to read the test target cannot, or a spy confirms
  the test item is absent from the train set passed in). This is the key rigor test.
- **Degenerate guard:** n<3 → degenerate flagged, no meaningful correlation.
- **Determinism:** same inputs+seed → identical `to_dict()`.
- Run `pytest -m "not live" tests/test_e3_loio.py -q`; report pass count.

## Records (same PR)
- `docs/DECISIONS.md`: entry **D5.8** (note D5.5/D5.6/D5.7 are on other branches / main; use D5.8) —
  E3 LOIO generalization harness built, leakage-safe (fit on train split only); implements SPEC §5 E3
  pass criteria (direction hit > random; Spearman ρ > 0). Does not change the prereg.
- `INTERFACES.md` §8 AS-BUILT: the E3 LOIO module + signatures + `LOIOResult`.
- Commit with trailer `Co-authored-by: Copilot <copilot@github.com>`.

## Report back
Files changed, the harness/result shape, how leakage is structurally prevented, test pass count, and
any ambiguity resolved. Do NOT merge.
