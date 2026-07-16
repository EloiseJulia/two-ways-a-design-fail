# impl-e5-ece — ECE / reliable-radius / abstention rate (PR #16)

Implement in the worktree `.worktrees\e5-ece` (branch `feature/e5-ece`, DRAFT PR #16). Do NOT touch
`main`, do NOT merge. Offline only + `pytest -m "not live"`. Commit + push; report to the Manager.

## Purpose (SPEC §5 E5 + §6.3–6.4)
Build the E5 reliability/abstention layer: quantify how trustworthy the panel's predictions are and
WHERE they fail, to support the abstention rule. Reuse `twdf.features.ui_features.feature_distance`
(PR #13) and `twdf.calibration.thresholds` (PR #14, Module D triage/abstention). Read `SPEC.md` §5
(E5 row: ECE + generalization gradient by persona/difficulty/feature-distance/reversal → failure-region
map, reliable radius, measured abstention rate) and §6.3–6.4.

## What to build — `src/twdf/analysis/reliability.py` (pure core) + optional thin runner
`src/twdf/experiments/e5_ece.py`
1. `expected_calibration_error(pred_probs, outcomes, *, n_bins=10) -> ECEResult` — standard ECE
   (weighted mean |confidence − accuracy| over equal-width bins) + per-bin reliability table
   (bin range, count, mean confidence, empirical accuracy). Also expose `max_calibration_error` (MCE).
2. `generalization_gradient(records, *, by: str) -> GradientResult` — bin an error metric (e.g.
   ECE or |pred−actual|) by a covariate: `feature_distance` to a calibration reference,
   task `difficulty`, or `persona` — returns the error profile across bins (the FAILURE-REGION MAP).
   For feature-distance, reuse `feature_distance`.
3. `reliable_radius(records, *, ece_bound, distance_key="feature_distance") -> float` — the largest
   feature-distance within which ECE stays ≤ `ece_bound` (the applicability radius; beyond it →
   abstain). Documented, deterministic.
4. `measured_abstention_rate(designs, threshold_model, *, signals) -> AbstentionReport` — run Module
   D `triage` over a sample of designs (each with its UIFeatureVector + axis1/axis2 signals) and report
   the fraction ABSTAIN / HUMAN_STUDY / RELEASE (SPEC §6.4 "measured abstention rate"). Reuse
   `twdf.calibration.thresholds.triage`.
5. Dataclasses (`ECEResult`, `GradientResult`, `AbstentionReport`) with JSON `to_dict`.

## Constraints
- Deterministic, pure; hashlib only if hashing; no builtin `hash(`; no network.
- Reuse `feature_distance` (PR #13) + `triage`/`ThresholdModel` (PR #14) — do NOT reinvent.
- This PR does NOT freeze τ and does not require a frozen model (accept a ThresholdModel argument;
  tests may construct one via `fit_thresholds` on synthetic calibration).

## Tests `tests/test_e5_ece.py`
- **ECE correctness:** perfectly-calibrated synthetic probs → ECE ≈ 0; a deliberately miscalibrated
  set (e.g. always predict 0.9 but 50% accurate) → ECE ≈ 0.4 (check the arithmetic on a hand
  example). MCE ≥ ECE.
- **Generalization gradient:** synthetic where error GROWS with feature-distance → the gradient is
  monotone increasing across distance bins (failure region at high distance).
- **Reliable radius:** with the above, `reliable_radius(ece_bound=...)` returns a finite radius that
  excludes the high-distance failure region; a fully-calibrated set → radius = max distance.
- **Abstention rate:** over a design sample where some designs are OOD, `measured_abstention_rate`
  returns abstain fraction > 0 and the three fractions sum to 1.0.
- **Determinism:** same inputs → identical `to_dict()`.
- Run `pytest -m "not live" tests/test_e5_ece.py -q`; report pass count.

## Records (same PR)
- `docs/DECISIONS.md`: entry **D5.9** (note D5.8 is on the E3 branch; use D5.9) — E5 reliability layer
  (ECE + failure-region gradient + reliable radius + measured abstention rate) built on PR #13
  feature-distance + PR #14 triage; supports the §6.3 abstention rule; does not change the prereg.
- `INTERFACES.md` §8 AS-BUILT: the new `twdf.analysis.reliability` module + signatures + result shapes.
- Commit with trailer `Co-authored-by: Copilot <copilot@github.com>`.

## Report back
Files changed, the metric/result shapes, the ECE hand-example value, test pass count, any ambiguity
resolved. Do NOT merge.
