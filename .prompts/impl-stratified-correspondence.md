# impl-stratified-correspondence — higher-power correspondence + robustness (PR #18)

Implement in the worktree `.worktrees\stratified-correspondence` (branch
`feature/stratified-correspondence`, DRAFT PR #18). Do NOT touch `main`, do NOT merge. Offline only +
`pytest -m "not live"`. Commit + push; report to the Manager. EXPLORATORY (labeled) — the FROZEN
confirmatory prereg (D5.11) is the 5-condition version; this ADDS exploratory higher-power views and
does NOT change the prereg.

## Purpose (answers reviewer attacks A3 "only n=5 conditions" and A4 "fragile signal")
1. **Difficulty-stratified correspondence:** the frozen cross-condition Spearman has only n=5 points.
   Stratifying each condition by item DIFFICULTY (e.g. `ai_conf` terciles) yields up to condition×strata
   points (≈15), materially more power to test the core claim "panel disagreement tracks human
   over-dispersion." Read `docs/paper/reviewer-rebuttals.md` (A3/A4) + `SPEC.md` §5.
2. **Confirmatory robustness readout:** per-model stability, bootstrap, and leave-one-condition-out
   sensitivity over the confirmatory result — the honest robustness a methods paper needs (A4).

## What to build — `src/twdf/analysis/stratified_correspondence.py`
1. `stratified_correspondence(panel_responses, *, human_raw_loader, stratify_by="ai_conf",
   n_strata=3, seed=42, n_boot=10000, n_perm=10000) -> StratifiedCorrespondenceResult`:
   - Bin items into `n_strata` difficulty strata by `stratify_by` (default the AI-side EXOGENOUS
     `ai_conf`; low conf = harder — do NOT use human outcomes to stratify, no leakage). Strata edges by
     quantile over the items actually used.
   - For each (condition × stratum) cell with enough data: compute HUMAN between-user reliance
     **over-dispersion** (beta-binomial, conflict-conditioned) from the RAW human trials in that cell,
     and PANEL disagreement (variance of per-(persona×model) conflict-conditioned reliance) from the
     panel responses in that cell. REUSE `twdf.metrics.overdispersion` + the PR #11 machinery.
   - Spearman correspondence over ALL (condition×stratum) points (reuse `condition_correlation`; keep
     its n<3 degenerate guard + a ceiling/low-variance flag per cell, mirroring PR #11). Permutation p +
     bootstrap CI. Report the cell table + n_points.
   - Guard cells with too few users/items (uninterpretable → excluded, flagged).
2. `confirmatory_robustness(confirmatory_result: dict) -> RobustnessResult`: takes
   `results/confirmatory_axis1.json` (the `ConfirmatoryAxis1Result.to_dict()` schema from PR #12) and
   reports: per-model within-task estimate + CI stability, over-dispersion CI, a leave-one-condition-out
   recomputation of the 5-condition Spearman (how much each condition drives it), and a task-selection
   sensitivity note. Pure function over the JSON (no re-run).
3. Dataclasses with JSON `to_dict`. Deterministic; hashlib only; no builtin `hash(`; NO leakage
   (stratify by AI-side exogenous props only; human outcomes never used to bin or predict).

## Human raw data
Use the existing Bansal loader path used by the decomposition/e1 code to get RAW per-trial human
reliance (the same source behind `results/e1_multicond.json`). If a clean loader exists
(`twdf.data` / the decomposition module), reuse it; else load the committed CSV
`data/raw/decision-result-filter.csv` (already present) filtered to beer + the 5 AI conditions. Pass it
via `human_raw_loader` so tests can inject synthetic data.

## Tests `tests/test_stratified_correspondence.py` (offline)
- **Known signal:** synthetic panel + human where, per (condition×stratum), panel disagreement rank-
  tracks human over-dispersion → Spearman ≈ 1, permutation p<0.05, and n_points > 5 (proves the power
  gain vs the 5-condition version).
- **Null:** no structure → n.s.
- **Stratification correctness:** items split into the right terciles by `ai_conf`; a cell with too few
  users is flagged/excluded; no `ground_truth`/human-outcome used to stratify (assert).
- **Robustness readout:** on a synthetic confirmatory-result dict, leave-one-condition-out changes the
  Spearman as expected; per-model fields present.
- **Determinism.** Run `pytest -m "not live" tests/test_stratified_correspondence.py -q`; report count.
- Load the REAL `data/raw/decision-result-filter.csv` in at least one test to confirm the human loader +
  stratification work on the actual data (offline; the CSV is committed/available).

## Records
- `docs/DECISIONS.md`: entry **D5.14** — added EXPLORATORY difficulty-stratified correspondence
  (condition×strata → more power; answers A3) + confirmatory robustness readout (A4); does NOT change
  the frozen prereg (D5.11), clearly labeled exploratory. `INTERFACES.md` §8 update. Commit trailer
  `Co-authored-by: Copilot <copilot@github.com>`.

## Report back
Files changed, the result shapes, test pass count, n_points achieved on the real-data test, and
confirmation of no leakage (AI-side stratifier only). Do NOT merge.
