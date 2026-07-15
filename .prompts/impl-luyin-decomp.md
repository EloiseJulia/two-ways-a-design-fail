# impl-luyin-decomp — C0 decomposition replication on Lu&Yin (zero API)

You are an implementation subagent in worktree `.worktrees/luyin-decomp` (branch
`feature/luyin-decomp`, draft PR #5). Pure real-data analysis — NO API calls, NO
GH_MODELS_TOKEN needed. You do NOT audit/merge your own work. Report FACTS; do NOT
claim "done/all green". This touches the paper's CROWN JEWEL (co-anchor C0), so
methodology rigor is paramount — a silent stats error invalidates the contribution.

## 0. FIRST: read the source of truth
Read: `SPEC.md` (§2 **C0** co-anchor + H1a refinement), `PROGRESS.md` (the PR#2
decomposition finding + Known pitfalls + Preregistration), `INTERFACES.md` (§1 canonical
schema, §4 metrics, §8 AS-BUILT), `docs/research/2026-07-14-overdispersion-decomposition.md`
(the Bansal decomposition write-up you are replicating), and the EXISTING, well-tested
code you MUST reuse: `src/twdf/metrics/variance_decomposition.py`
(`split_half_reliability` = PRIMARY, ICC(2,1)+Spearman-Brown → `stable_user_share`+CI;
`variance_components_glmm` = optional), `src/twdf/data/bansal.py` (loader pattern),
`src/twdf/experiments/e1_decomposition.py` (the Bansal decomposition experiment to mirror),
`configs/e1_decomposition.yaml`, `tests/test_variance_decomposition.py`.

## 1. GOAL — answer the generalization attack
The C0 finding rests on ONE dataset (Bansal): no-AI reliance ≈ stable user trait
(stable_user_share ≈ 0.74), AI-assisted reliance ≈ user×task (≈ 0.32–0.41). REPLICATE the
AI-assisted decomposition on a SECOND dataset (Lu&Yin CHI'21) using the SAME primary method
(split-half). Report whether the "AI-assisted reliance is predominantly user×task (low
stable-user share)" pattern GENERALIZES, PARTIALLY replicates, or DIVERGES. A divergence is
still a valid, informative result — report it honestly, do NOT tune to force a match.

## 2. Data (Manager-verified — do NOT re-derive URLs)
- URL (download-if-missing to `data/raw/`, gitignored, mirror bansal.py):
  `https://raw.githubusercontent.com/ZhuoranLu/Trustworthy-ML/main/data/expOneFinalPredictionsValid1125.csv`
  (HTTP 200; 9030 data rows; **301 workers × exactly 30 tasks each** — well-powered for
  split-half, like Bansal's 20–50/user).
- Columns: `workerId`, `taskId`, `globalId`, `selfPrediction` (pre-AI human decision),
  `finalPrediction` (post-AI human decision), `prediction` (AI advice shown), `mlCorrect`
  (AI correct), `selfCorrect`, `finalCorrect`, `switch` (human changed self→final),
  `agreement`/`finalAgreement`/`idpAgreement`, `decision`. Values look boolean/int-coded —
  inspect dtypes and coerce explicitly (mixed-type guard, like Bansal).
- Implement `src/twdf/data/luyin.py`: `load_luyin(...) -> pd.DataFrame` in the CANONICAL
  per-trial schema (INTERFACES §1): map selfPrediction→`human_initial`,
  finalPrediction→`human_final`, prediction→`ai_advice`, mlCorrect→`ai_correct`,
  workerId→`user_id`, taskId→`task_id`, dataset='luyin21'; **relied = (finalPrediction ==
  prediction)** (adopted AI — same operationalization as Bansal). Include `switch`,
  `selfCorrect`, `finalCorrect` in `extra`. **VERIFY + REPORT** the loaded structure
  (n_users, n_tasks, tasks/user distribution, reliance rate, AI accuracy) and confirm no
  parsing surprises. Check for any CONDITION column (e.g. idpAgreement / decision) that
  would define subgroups; if a meaningful condition split exists, decompose per-condition,
  else decompose overall + report you did so.

## 3. Decomposition (reuse the PRIMARY method — do NOT invent a new one)
- Use `split_half_reliability` from `variance_decomposition.py` on per-user reliance across
  the 30 tasks (random task halves → correlate per-user reliance rates → Spearman-Brown).
  Use the SAME params as the Bansal run for comparability: **n_splits=100, seed=43**, and
  the SAME bootstrap-CI approach. Report `stable_user_share` + 95% CI.
- **Primary DV = unconditional reliance** (finalPrediction==prediction), to match Bansal's
  AI-assisted conditions (compare to 0.32–0.41).
- **Robustness DV = conflict-conditioned reliance**: among trials where selfPrediction ≠
  prediction (genuine conflict), did finalPrediction == prediction (switched to AI)? Report
  its stable_user_share too (this mirrors the PR#4 panel DV; note n_conflict/user — if too
  few per user for split-half, flag as underpowered rather than reporting a noisy number).
- Optional corroboration: `variance_components_glmm` (report honestly if non-convergent, as
  the Bansal run did). Split-half is the headline.
- **IDENTIFIABILITY GUARD (the trap that got the first Bansal attempt rejected):** do NOT
  use ANOVA-on-single-observation-cells. Split-half is valid here BECAUSE each user has 30
  tasks. If you compute anything cell-based, verify cells have >1 obs first; they won't, so
  don't.

## 4. Experiment + config + docs
- `configs/luyin_decomposition.yaml`; `src/twdf/experiments/luyin_decomposition.py`
  (CLI `python -m twdf.experiments.luyin_decomposition --config configs/luyin_decomposition.yaml`)
  → `results/luyin_decomposition.json` with full `run_manifest` (config hash, seeds,
  timestamp, dataset, n_users, n_tasks). No API calls; manifest need not have model/cost.
- Write `docs/research/2026-07-15-luyin-decomposition-replication.md`: the replication
  result, side-by-side vs Bansal (a small table), and a clear verdict — does the user×task
  pattern generalize? Include the identifiability argument + honest caveats (single new
  dataset, within-subject sequential design differs from Bansal's between-subject conditions,
  no true no-AI CONDITION so the 0.74 stable-trait arm may not be directly replicable — be
  explicit about what IS and ISN'T comparable).

## 5. Tests (`tests/test_luyin.py` + extend decomposition tests as needed)
- Loader: canonical schema columns present, dtypes correct, relied defined right, structure
  matches (301 users × 30 tasks). Determinism of the load.
- Decomposition determinism: split_half_reliability with seed=43 is reproducible
  (cross-process subprocess pattern, like `tests/test_variance_decomposition.py`).
- Do NOT weaken any existing test. `pytest -q` green overall; report counts.

## 6. Methodology guardrails (§4.5)
Split-half (not ANOVA-on-cells); same seed/params as Bansal for comparability; explicit
dtype coercion; relied defined consistently; honest reporting of replicate/partial/diverge;
no post-hoc tuning; determinism (fixed seeds; cross-process test); `data/raw/` gitignored;
`hashlib` only (grep `\bhash\(`); no leakage. This is C0 — the auditor will be hostile.

## 7. Deliverables + wrap-up
Code (luyin.py loader, luyin_decomposition experiment + config, tests), run it, commit
`results/luyin_decomposition.json` + the research doc; `pytest -q` green; update `PROGRESS.md`
(Done entry with the REAL stable_user_share numbers + verdict) and `INTERFACES.md` §8
AS-BUILT (Lu&Yin loader now exists). Commit (trailer `Co-authored-by: Copilot
<copilot@github.com>`) + push to `feature/luyin-decomp`. Do NOT commit scratch. Return a
FACTUAL report: Lu&Yin structure, stable_user_share (primary + conflict-conditioned) + CI,
the side-by-side vs Bansal, and your honest verdict on whether C0 generalizes. Independent
audit + Manager verification follow.
