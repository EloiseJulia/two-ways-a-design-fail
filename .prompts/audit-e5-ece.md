# audit-e5-ece — INDEPENDENT audit (PR #16)

Fresh independent auditor. REPORT ONLY; no fix/commit/merge. Offline `pytest -m "not live"` only.
Evidence = file:line + reproduced values. End with **VERDICT: PASS** or **VERDICT: FAIL**.

## What this PR does
Adds `src/twdf/analysis/reliability.py` — SPEC §5 E5 / §6.3–6.4 reliability layer: ECE/MCE +
reliability bins, generalization gradient (failure-region map by feature-distance/difficulty/persona),
reliable radius, measured abstention rate (via Module D `triage`). Branch `feature/e5-ece` (draft PR
#16), merged up to date with main.

## Checks (PASS/FAIL + evidence)
1. **ECE correctness:** perfectly-calibrated synthetic → ECE ≈ 0; the hand miscalibrated example
   (always predict 0.9, 50% accurate) → **ECE ≈ 0.4**; MCE ≥ ECE. Reproduce the arithmetic.
2. **Generalization gradient:** synthetic where error GROWS with feature-distance → per-bin ECE (or
   error) is monotone increasing across distance bins; a failure region at high distance is flagged.
   Confirm it can bin by feature_distance, difficulty, AND persona.
3. **Reliable radius:** returns a finite radius that excludes the high-distance failure region; a
   fully-calibrated set → radius = max distance. Deterministic + documented.
4. **Measured abstention rate:** runs Module D `triage` over a design sample; ABSTAIN/HUMAN_STUDY/
   RELEASE fractions sum to 1.0; abstain fraction > 0 when some designs are OOD. Reuses
   `twdf.calibration.thresholds.triage` (not reinvented).
5. **Reuse:** feature-distance uses PR #13 `feature_distance`; triage uses PR #14 — no reinvention.
   Does NOT freeze τ.
6. **Determinism + hygiene:** same inputs → identical `to_dict()`; hashlib only / no builtin `hash(`;
   no network.
7. **Tests meaningful:** `pytest -m "not live" tests/test_e5_ece.py -q` pass count; the ECE,
   gradient, radius, and abstention tests are substantive.
8. **Merge safety:** `git diff --name-status main...feature/e5-ece` is additive; **deletes NOTHING**
   (esp. NOT the PR #12 confirmatory, PR #13 features, PR #14 calibration, or PR #15 E3 LOIO files —
   verify all present).
9. **Records:** `docs/DECISIONS.md` D5.9 + `INTERFACES.md` §8.

Final line: **VERDICT: PASS** or **VERDICT: FAIL**.
