# impl-module-d-calibration — SPEC §6 dual-threshold calibration + triage (PR #14)

Implement in the worktree `.worktrees\module-d-calibration` (branch `feature/module-d-calibration`,
DRAFT PR #14). Do NOT touch `main`, do NOT merge. Offline only + `pytest -m "not live"`. Commit +
push to the branch; report to the Manager.

## Purpose (SPEC §6 — pre-registered dual-threshold triage protocol)
Build the calibration + triage MACHINERY that turns per-design signals into a screening decision,
in the PR #13 atomic FEATURE SPACE. **CRITICAL RIGOR GUARD: this PR builds the machinery and a
freeze MECHANISM, but must NOT actually learn/commit frozen τ values** (τ_disp/τ_level stay UNFROZEN
— the real freeze needs the calibration data incl. E4 axis-2, and must be a deliberate timestamped
step later). Read `SPEC.md` §5 (E5), §6 (the 5-point protocol), `docs/plans/preregistration-axis1.md`
§7 (τ procedure; VALUES stay unfrozen), and reuse `twdf.features.ui_features`
(`UIFeatureVector`, `feature_vector_to_array`, `feature_distance`, `FEATURE_NAMES`).

## What to build — `src/twdf/calibration/thresholds.py`
1. `@dataclass(frozen=True) ThresholdModel` — holds τ_disp, τ_level, the calibration feature-space
   reference (for OOD distance), an OOD radius, and metadata (target_recall, fit timestamp=None until
   frozen). JSON `to_dict`.
2. `fit_thresholds(calibration: list[CalibrationExample], *, target_recall: float = 0.9,
   seed: int = 42) -> ThresholdModel` — each `CalibrationExample` = (UIFeatureVector, observed
   axis1_overdispersion: float, observed axis2_over_reliance: float, is_dangerous: bool). Learn
   τ_disp on axis-1 and τ_level on axis-2 to achieve **high RECALL** on `is_dangerous` (SPEC §6.2:
   a miss = releasing a dangerous design ≫ worse than a false alarm). Pick thresholds by scanning
   candidate cutoffs and choosing the one meeting `target_recall` with best precision; report
   precision-at-recall. Also compute the calibration reference set + a default OOD radius (e.g. a
   high percentile of within-calibration nearest-neighbor `feature_distance`). Deterministic.
   **Returns an UNFROZEN model (timestamp=None).**
3. `triage(features: UIFeatureVector, axis1_signal: float, axis2_signal: float, model:
   ThresholdModel) -> TriageDecision` — returns one of `RELEASE` / `HUMAN_STUDY` / `ABSTAIN`:
   - Either axis over its threshold ⇒ `HUMAN_STUDY` (high-recall screen).
   - Both low ⇒ `RELEASE`.
   - **Abstain overrides** (SPEC §6.3): if the design is OOD (nearest-neighbor `feature_distance` to
     the calibration reference > OOD radius) OR a feature dim is novel/uncalibrated OR (optional
     hook) a supplied ECE / human-agent reversal flag is set ⇒ `ABSTAIN` + recommend a human study.
   `TriageDecision` dataclass carries the decision + the reason + the triggering axis/flag.
4. `freeze_thresholds(model: ThresholdModel, *, timestamp: str) -> ThresholdModel` — returns a copy
   with the UTC `timestamp` set (the discipline mechanism). Provide a helper to serialize a frozen
   model to JSON. **Do NOT call this on real data in this PR** (only exercised in tests with synthetic
   data). Add a clear docstring: freezing on real data is a later, deliberate, logged step.
5. `precision_at_recall(...)` helper (or inline) for the report.

## Constraints
- Deterministic, pure; hashlib only if hashing; no builtin `hash(`. No network.
- Feature-space operations reuse `feature_distance` / `feature_vector_to_array` — do NOT reinvent.
- NO leakage: calibration uses observed axis-1/axis-2 risk + a danger label; it must not peek at any
  held-out/eval design. τ VALUES are not committed/frozen here.

## Tests `tests/test_module_d_calibration.py`
- **Recovers a separating threshold:** synthetic calibration where dangerous designs have high
  axis-1 (or axis-2) signal → `fit_thresholds` achieves the `target_recall` on `is_dangerous`; report
  precision-at-recall > chance.
- **High-recall property:** at target_recall=0.9, the fitted model's recall on the calibration danger
  labels ≥ 0.9 (misses minimized).
- **triage decisions:** a clearly-dangerous design (high axis signal, in-distribution) → HUMAN_STUDY;
  a clearly-safe in-distribution design → RELEASE; an OOD design (large feature_distance) → ABSTAIN
  regardless of signal.
- **τ stays unfrozen:** a freshly fitted model has `timestamp is None`; `freeze_thresholds` sets it;
  assert no frozen τ JSON artifact is written to `results/` by the module at import/fit time.
- **Determinism:** same calibration + seed → identical `to_dict()`.
- Run `pytest -m "not live" tests/test_module_d_calibration.py -q`; report pass count.

## Records (same PR)
- `docs/DECISIONS.md`: entry **D5.7** (note D5.5/D5.6 are on other feature branches / already on main;
  use D5.7) — Module D calibration/triage machinery built; τ VALUES remain UNFROZEN (freeze is a later
  timestamped step needing E4 axis-2 data); high-recall screening + abstention per SPEC §6.
- `INTERFACES.md` §8 AS-BUILT: `twdf.calibration.thresholds` module + signatures + the "calibration —
  NOT YET IMPLEMENTED" line updated to reflect fit_thresholds/triage now exist (τ still unfrozen).
- Commit with trailer `Co-authored-by: Copilot <copilot@github.com>`.

## Report back
Files changed, the model/decision shapes, the recall/precision behavior in tests, test pass count,
and any ambiguity resolved. Confirm τ is NOT frozen. Do NOT merge.
