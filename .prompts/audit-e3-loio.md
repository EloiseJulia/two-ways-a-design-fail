# audit-e3-loio — INDEPENDENT audit (PR #15)

Fresh independent auditor. REPORT ONLY; no fix/commit/merge. Offline `pytest -m "not live"` only.
Evidence = file:line + reproduced values. End with **VERDICT: PASS** or **VERDICT: FAIL**.

## What this PR does
Adds a leakage-safe leave-one-item-out (LOIO) generalization harness (`src/twdf/analysis/loio.py` +
`src/twdf/experiments/e3_loio.py`) for SPEC §5 E3: fit on the TRAIN split only, predict held-out item
axis-1 direction + ranking, score direction-hit (>0.5) + Spearman ρ (>0). Branch `feature/e3-loio`
(draft PR #15), merged up to date with main.

## Checks (PASS/FAIL + evidence)
1. **LEAKAGE FIREWALL (the key check):** `predict_fn` receives train items (with targets) EXCLUDING
   the held-out item + a TARGET-FREE `LOIOHeldoutItem` (no `target` attribute). Verify structurally in
   `loio_generalization` (train excludes i; heldout is `heldout_view()`), and reproduce that a
   `predict_fn` trying to read `heldout.target` raises AttributeError. Confirm the held-out target is
   NEVER passed to fitting.
2. **Known-generalization signal:** synthetic items whose target is monotone in a train-derivable
   feature → direction hit rate > 0.5 (binomial p<0.05) AND Spearman ρ > 0 (permutation p<0.05).
3. **Null:** random/unstructured targets → ρ not significantly positive.
4. **Degenerate guard:** n<3 → degenerate flagged, no meaningful correlation reported.
5. **Determinism + hygiene:** same items+seed → identical `to_dict()`; hashlib only / no builtin
   `hash(`; permutation uses a seeded RNG. No network.
6. **Metrics correct:** direction = sign match; hit_p is a binomial test vs 0.5; spearman_p is a valid
   permutation p. Spot-check the arithmetic.
7. **Tests meaningful:** `pytest -m "not live" tests/test_e3_loio.py -q` pass count; tests aren't
   tautological (esp. the leakage test actually proves absence of the target).
8. **Merge safety:** `git diff --name-status main...feature/e3-loio` additive; deletes NOTHING (esp.
   not PR #12/#13/#14 files).
9. **Records:** `docs/DECISIONS.md` D5.8 + `INTERFACES.md` §8.

Final line: **VERDICT: PASS** or **VERDICT: FAIL**.
