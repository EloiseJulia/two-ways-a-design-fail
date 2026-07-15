# audit-luyin-decomp — INDEPENDENT hostile + §4.5 methodology audit (PR #5)

You are a FRESH, independent auditor. You did NOT write this code. This touches the
paper's CO-ANCHOR (C0), so be maximally hostile on methodology — a silent stats error
here invalidates a headline contribution. REPORT ONLY; do NOT fix or merge. Zero API
calls are needed (pure real-data compute — you may rerun freely). Evidence = file:line
+ reproduced numbers.

## Context
Branch `feature/luyin-decomp` (draft PR #5) replicates the C0 split-half decomposition
on Lu&Yin CHI'21. Read first: `SPEC.md` (§2 C0 — note it is HELD pending a discriminator),
`PROGRESS.md` (Lu&Yin entry + PR#2 Bansal decomposition + Known pitfalls),
`docs/research/2026-07-14-overdispersion-decomposition.md` (Bansal method being replicated),
`docs/research/2026-07-15-luyin-decomposition-replication.md` (the new report),
`.prompts/impl-luyin-decomp.md` (the spec). Then the diff:
`git --no-pager diff main...feature/luyin-decomp`. Key files: `src/twdf/data/luyin.py`,
`src/twdf/experiments/luyin_decomposition.py`, `configs/luyin_decomposition.yaml`,
`src/twdf/metrics/variance_decomposition.py` (REUSED `split_half_reliability`),
`tests/test_luyin.py`, `results/luyin_decomposition.json`.

## Checks (each: PASS/FAIL + evidence + reproduction)
### A. Method correctness (the core — this is C0)
1. **Split-half, NOT ANOVA-on-cells.** Confirm the decomposition uses the existing
   `split_half_reliability` (Spearman-Brown) on per-user reliance across tasks — the
   well-identified method. If ANY cell-based variance partition on single-obs cells is
   used, FAIL (that trap got the first Bansal attempt rejected).
2. **Reliance definition** = `finalPrediction == prediction` (adopted AI), applied
   correctly in the loader; conflict-conditioned = among `selfPrediction != prediction`,
   did `finalPrediction == prediction`. Verify in code + spot-check rows from the CSV.
3. **Loader → canonical schema:** dtypes coerced explicitly (boolean-strings → bool),
   user_id/task_id/ai_advice/ai_correct/relied mapped right, no silent NaN/miscoercion.
   Re-derive structure: 301 users, tasks/user (30), reliance rate, AI accuracy — match JSON.
4. **Re-derive the headline numbers** from `results/luyin_decomposition.json` by rerunning
   the experiment (`python -m twdf.experiments.luyin_decomposition --config
   configs/luyin_decomposition.yaml`): unconditional stable_user_share = 0.801
   [0.771,0.834]; conflict-conditioned = 0.792 [0.761,0.824]. Must match.

### B. COMPARABILITY to Bansal (critical — the whole point is a cross-dataset comparison)
5. Confirm the Lu&Yin run uses the SAME `split_half_reliability` params as the Bansal
   decomposition (seed=43, n_splits=100, min_tasks threshold). Report any difference.
6. **Assess whether the Bansal-vs-Lu&Yin comparison is apples-to-apples.** Flag confounds
   that could inflate/deflate Lu&Yin's share relative to Bansal INDEPENDENT of any real
   effect: tasks/user count & min_tasks threshold, reliance base-rate & between-user
   variance, AI-accuracy regime, single-domain vs multi-domain, within-subject-sequential
   vs between-subjects. You do NOT need to resolve these — but VERIFY the report + SPEC do
   NOT overclaim a cause (they should say C0 is HELD and a discriminator is pending). If the
   docs assert "design-dependent C0" as established, FAIL for overclaiming.
7. Confirm the report honestly states Lu&Yin has NO no-AI arm and therefore cannot test
   C0's within-dataset contrast (0.74→0.32).

### C. Determinism & hygiene
8. Cross-process determinism: run the decomposition in TWO separate processes; assert
   byte-identical results excluding the manifest timestamp. Builtin `hash()` banned
   (grep `\bhash\(` excl hashlib/comments = 0).
9. `pytest -q` green; report counts. Tests NOT weakened (strong thresholds retained).
10. `data/raw/` gitignored; no scratch committed; no secrets (though this slice uses no token).

## Output
Markdown report: overall verdict (PASS / FAIL / CONDITIONAL PASS); a table of the 10 checks
with PASS/FAIL + evidence + reproduced numbers; an explicit statement on whether the docs
overclaim causation (they must present C0 as HELD, boundary observation, discriminator
pending); and a prioritized BLOCKER list. Do NOT modify code or merge. Print the report in
your final message.
