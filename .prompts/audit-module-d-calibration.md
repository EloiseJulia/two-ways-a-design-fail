# audit-module-d-calibration — INDEPENDENT audit (PR #14)

Fresh independent auditor. REPORT ONLY; no fix/commit/merge. Offline `pytest -m "not live"` only.
Evidence = file:line + reproduced values. End with **VERDICT: PASS** or **VERDICT: FAIL**.

## What this PR does
Adds `src/twdf/calibration/thresholds.py` — SPEC §6 dual-threshold (τ_disp/τ_level) calibration +
triage + abstention in the PR #13 feature space. **τ values must stay UNFROZEN in this PR** (a freshly
fitted model has `timestamp=None`; freezing is a later deliberate step). Branch
`feature/module-d-calibration` (draft PR #14), merged up to date with main.

## Checks (PASS/FAIL + evidence)
1. **High-recall fit (SPEC §6.2):** `fit_thresholds(..., target_recall=0.9)` achieves ≥0.9 recall on
   `is_dangerous` on a synthetic calibration set where dangerous designs have high axis-1 (or axis-2)
   signal; reports precision-at-recall. Reproduce.
2. **Triage decisions:** in-distribution high-signal design → `HUMAN_STUDY`; in-distribution low-signal
   → `RELEASE`; **OOD design (large `feature_distance` / novel feature dim) → `ABSTAIN`** regardless of
   signal. Reproduce all three.
3. **τ stays UNFROZEN:** freshly fitted `ThresholdModel.timestamp is None`; `freeze_thresholds` sets a
   timestamp on a copy; **no frozen-τ artifact is written to `results/`** at import/fit time. Verify by
   code inspection + that fitting writes no file.
4. **Either-axis-over-threshold logic** is correct (τ_disp on axis-1, τ_level on axis-2; either triggers
   HUMAN_STUDY). Abstain OVERRIDES release/human-study when OOD/novel/reversal.
5. **Reuse:** OOD distance uses `twdf.features.ui_features.feature_distance` / `feature_vector_to_array`,
   not a reinvented metric. No leakage (calibration must not peek at a held-out/eval design).
6. **Determinism + hygiene:** same calibration+seed → identical `to_dict()`; hashlib only / no builtin
   `hash(`; pure/no network.
7. **Tests meaningful:** `pytest -m "not live" tests/test_module_d_calibration.py -q` pass count; the
   high-recall, OOD-abstain, and τ-unfrozen tests are substantive (not tautological).
8. **Merge safety:** `git diff --name-status main...feature/module-d-calibration` is additive (new
   module + __init__ + test) + doc edits; **deletes NOTHING** (esp. not PR #12/#13 files).
9. **Records:** `docs/DECISIONS.md` D5.7 (τ machinery built, VALUES unfrozen) + `INTERFACES.md` §8.

Final line: **VERDICT: PASS** or **VERDICT: FAIL**.
