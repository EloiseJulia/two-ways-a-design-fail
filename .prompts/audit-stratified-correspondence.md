# audit-stratified-correspondence — INDEPENDENT audit (PR #18, EXPLORATORY)

Fresh independent auditor. REPORT ONLY; no fix/commit/merge. Offline `pytest -m "not live"` only.
Evidence = file:line + reproduced values. End with **VERDICT: PASS** or **VERDICT: FAIL**.

## What this PR does
Adds `src/twdf/analysis/stratified_correspondence.py`: (1) `stratified_correspondence(...)` — a
higher-power EXPLORATORY panel↔human correspondence over (condition × difficulty-stratum) cells (~15
points vs the frozen 5-condition version), and (2) `confirmatory_robustness(...)` — a per-model
robustness/leave-one-condition-out readout over the confirmatory result JSON. Branch
`feature/stratified-correspondence` (PR #18), merged up to date with main. Does NOT change the FROZEN
confirmatory prereg (D5.11) — it is labeled EXPLORATORY.

## Checks (PASS/FAIL + evidence)
1. **NO LEAKAGE (critical):** strata are formed from an AI-side EXOGENOUS property (default `ai_conf`);
   forbidden stratifiers (`ground_truth`/`y`/`relied`/`choice`/human reliance) are REJECTED. Reproduce
   the rejection. Confirm no human outcome / ground_truth is used to bin items OR as a predictor.
2. **Power gain:** on synthetic data with a known per-(condition×stratum) signal, the correspondence
   yields **n_points > 5** (≈15) and Spearman ≈ 1 with permutation p<0.05; a null → n.s. Reproduce.
3. **Correct human over-dispersion per cell:** each cell's human between-user over-dispersion is the
   beta-binomial estimator (conflict-conditioned), reusing `twdf.metrics.overdispersion` (not raw
   variance); panel disagreement = variance of per-(persona×model) conflict-conditioned reliance.
   Ceiling/low-variance cells flagged + small cells excluded (n<3 guard on the correlation).
4. **Real-data path:** `load_real_bansal_human_raw` reads the committed `data/raw/decision-result-
   filter.csv` (beer + 5 AI conditions), and a real-data test produces the cells/points (report the
   n_points achieved). Human raw is injectable via `human_raw_loader` for tests.
5. **Robustness readout:** `confirmatory_robustness` over a synthetic ConfirmatoryAxis1Result dict
   reports per-model stability + a leave-one-condition-out Spearman sensitivity (each condition's
   influence) + a task-selection note. Pure function (no re-run).
6. **Determinism + hygiene:** same inputs+seed → identical `to_dict()`; hashlib only / no builtin
   `hash(`; deterministic bootstrap/permutation seeds.
7. **Exploratory labeling / prereg untouched:** the result is labeled exploratory; the FROZEN 5-
   condition confirmatory prereg (D5.11) and its analysis (PR #12) are NOT modified.
8. **Tests meaningful:** `pytest -m "not live" tests/test_stratified_correspondence.py -q` pass count;
   tests aren't tautological (esp. the no-leakage + power-gain tests).
9. **Merge safety:** `git diff --name-status main...feature/stratified-correspondence` additive; deletes
   NOTHING (esp. not PR #7/#11–#17 files).
10. **Records:** `docs/DECISIONS.md` D5.14 (exploratory, doesn't change prereg) + `INTERFACES.md` §8.

Final line: **VERDICT: PASS** or **VERDICT: FAIL**.
