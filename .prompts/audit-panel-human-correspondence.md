# audit-panel-human-correspondence — INDEPENDENT audit (PR #11)

Fresh independent auditor. You did NOT write this. REPORT ONLY; do not fix/commit/merge. Offline
`pytest -m "not live"` only. Evidence = file:line + reproduced numbers. End with **VERDICT: PASS**
or **VERDICT: FAIL**.

## What this PR does
Adds `src/twdf/analysis/panel_human_correspondence.py` — the PRE-REGISTERED H1a secondary readout
(prereg §1/§4): cross-condition Spearman of panel disagreement per Bansal condition vs REAL human
reliance over-dispersion per condition (fixed target loaded from `results/e1_multicond.json`). Built
BLIND before the confirmatory panel run. Branch `feature/panel-human-correspondence` (draft PR #11).

## Checks (each PASS/FAIL + evidence)
1. **Fixed human target loaded, not recomputed:** reads `results.human_overdispersion[cond].rho`
   from the committed JSON; the `"Human"` (no-AI) baseline is EXCLUDED from the correlation.
2. **Alignment:** correlates only conditions present in BOTH the panel input and the human target,
   in a canonical order; extra/unknown conditions handled sanely.
3. **Correct statistics:** Spearman via `overdispersion.condition_correlation` (which carries the
   n<3 DEGENERATE guard); permutation p-value + bootstrap CI over the condition points; Pearson as
   secondary. Reproduce: feed panel = the human rhos (perfect rank match) → spearman ≈ 1.0 and
   permutation p < 0.05; a genuine rank-REVERSAL → spearman ≈ −1.0 (construct a true reversal:
   assign panel values whose ranks are the exact reverse of the human ranks). Confirm n=2 → degenerate
   (spearman None), no meaningless correlation reported.
4. **Ceiling/low-variance flag:** `Conf.+Adaptive (Expert)` (human excess_var ≈ 0) is flagged; a
   ceiling-EXCLUDED sensitivity result is returned recomputing over the remaining non-ceiling
   conditions. Verify on the REAL JSON. Confirm the flag does not silently drop conditions from the
   PRIMARY result (only from the sensitivity sub-result).
5. **No leakage / no researcher-DoF violation:** module reads only the fixed human target + a panel
   disagreement mapping; it does NOT read human outcomes into any panel/agent input and tunes no
   thresholds. Deterministic (fixed seeds); hashlib only if hashing.
6. **Tests meaningful:** `pytest -m "not live" tests/test_panel_human_correspondence.py -q` pass
   count; confirm the known-positive/known-negative/null/degenerate/ceiling/determinism tests are
   real (not tautological) and at least one loads the REAL e1_multicond.json.
7. **Records:** `docs/DECISIONS.md` entry (labelled D5.3) states this implements an
   already-specified prereg analysis (does NOT change H1a/prereg). `INTERFACES.md` §8 updated.
   NOTE: D5.2 is added on the E4 branch (not on main yet); flag that DECISIONS.md will need a
   trivial ordering merge when both land (NOT a blocker here).
8. **Merge safety:** `git diff --name-status main...feature/panel-human-correspondence` — additive
   (new module + __init__ + test) + doc edits; deletes nothing.

Final line: **VERDICT: PASS** or **VERDICT: FAIL**.
