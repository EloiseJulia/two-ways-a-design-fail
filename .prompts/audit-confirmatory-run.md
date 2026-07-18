# AUDIT — FROZEN confirmatory axis-1 (D5.11) result

Independent HOSTILE + methodology audit. You did NOT run this. Reproduce from raw `responses`; do not
trust summaries. Report per-check + `VERDICT: PASS`/`FAIL`. Do NOT merge/edit/push. Read-only.

## Repo / env
`C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail` (Windows PowerShell).
- `$env:PYTHONPATH=(Resolve-Path .\src).Path`; `$env:GH_TOKEN=$null` before `gh`. No live LLM calls.
- Result: `results/confirmatory_axis1.json`. Human anchor `results/e1_multicond.json`.
- FROZEN prereg DECISIONS **D5.11** (timestamp 2026-07-17T01:37:00Z): N=20 items, 2 models
  (openai/gpt-4o + openai/gpt-4.1-mini, GitHub Models), 6 personas, 5 UI conditions, item seed=42,
  per-model NO pooling, report REGARDLESS. Parser fix = D5.19 (this run is post-fix).

## Manager re-derivation to reproduce (don't trust it)
- gpt-4.1-mini: conflict over-dispersion 0.086, mean panel disagreement 0.028, cross-condition
  correspondence rho -0.205 (p=0.77, n=5), BH within-task adj p=0.248 — NULL.
- gpt-4o: conflict over-dispersion 0.364, mean disagreement 0.125, correspondence rho +0.410 (p=0.50,
  n=5), BH within-task adj p=0.498 — NULL.
- Overall: H1a panel↔human over-dispersion correspondence NON-SIGNIFICANT on both models.

## Checks (be adversarial)
1. **Completeness:** confirm the run is COMPLETE = 2 models × 6 personas × 20 items × 5 conditions =
   1200 responses; no missing cells; item seed=42 selected the frozen item set.
2. **Per-model reproduction:** recompute per-model conflict-conditioned over-dispersion (beta-binomial
   excess), mean panel disagreement, and the n=5 cross-condition Spearman (panel vs human per-condition
   over-dispersion from e1_multicond.json). Reproduce 0.086/0.028/-0.205 and 0.364/0.125/+0.410. Confirm
   NEITHER correspondence nor within-task permutation is significant after BH (report the p's).
3. **Parser-clean:** decisions/confidences diverse (not a fabricated (0,0.5) pile); raw traces re-parse
   to stored decisions (this run spans the D5.19 fix).
4. **No pooling / no leakage:** per-model reported (any pooled block descriptive-only); human reliance
   only in item SELECTION, never in panel prompts.
5. **Prereg conformance:** matches FROZEN D5.11 (N, models, conditions, seed, analysis plan); NOTHING
   changed post-freeze. Confirm the analysis reports REGARDLESS (a null is the honest outcome, not a bug).
6. **Baselines / honest framing:** verify over-dispersion beats the mean-predictor baseline where claimed
   (with CI), and that the NULL correspondence is not spun as positive. Flag any overclaim OR any hidden
   bug that would make a real effect look null (recall the E4 sign-inversion class).

## Deliverable
Per-check CORRECT/INCOMPLETE/WRONG with command evidence, then `VERDICT: PASS`/`FAIL`.
