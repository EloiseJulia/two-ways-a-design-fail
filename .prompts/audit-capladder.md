# AUDIT — capability-ladder results (D5.23): axis-2 + axis-1 on gpt-4o-mini/gpt-4.1/gpt-4o/gpt-5.5 (proxy)

Independent HOSTILE + methodology audit. You did NOT run these. Reproduce numbers from raw `responses`;
do not trust summaries. Report per-check + `VERDICT: PASS`/`FAIL`. Do NOT merge/edit/push. Read-only.

## Repo / env
`C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail` (Windows PowerShell).
- `$env:PYTHONPATH=(Resolve-Path .\src).Path`; `$env:GH_TOKEN=$null` before `gh`. No live LLM calls.
- Results: `results/axis2_powered_capladder.json`, `results/confirmatory_axis1_capladder.json`.
- Human anchor `results/e1_multicond.json`. Prereg DECISIONS **D5.23** (same-provider OpenAI ladder on
  the ghc-api proxy: gpt-4o-mini→gpt-4.1→gpt-4o→gpt-5.5; matched item seeds axis-1=42/axis-2=2024;
  per-model NO pooling; same protocol as D5.18; gpt-5.5 reuses cross-vendor cache). Parser fix = D5.19.

## Manager re-derivation to reproduce (don't trust it)
- AXIS-2 over-reliance on dark ("Wrong-AI-GT (dark)", displayed=1-ground_truth, n=120/model):
  gpt-4o-mini 0.500 (p=0.54), gpt-4.1 0.600 (p=0.018), gpt-4o 0.433 (p=0.94), gpt-5.5 0.300 (p=1.0).
  Persona p5 (novice-trusting) = 1.00/1.00/1.00/0.60.
- AXIS-1: conflict-conditioned over-dispersion 0.32/0.47/0.47/0.021; mean panel disagreement
  0.110/0.157/0.096/0.012; cross-condition correspondence rho +0.41/+0.80/-0.21/+0.10 (n=5).

## Checks (be adversarial)
1. **Axis-2 from raw responses:** filter dark; recompute displayed wrong advice as `1-trace['ground_truth']`
   (E4 trap — do NOT trust stored ai_advice for scoring); score over-reliance per model + binomial vs 0.5.
   Reproduce 0.500/0.600/0.433/0.300 and confirm stored-vs-recomputed advice mismatch = 0. Confirm ONLY
   gpt-4.1 is significantly above chance and gpt-5.5 significantly below.
2. **Axis-1 from the result:** reproduce per-model conflict over-dispersion + mean panel disagreement +
   correspondence rho (n=5). Confirm the frontier gpt-5.5 near-homogeneous (disagreement ~0.012) vs the
   others 0.10-0.16. Note none of the n=5 correspondences are significant.
3. **Parser-clean:** decisions/confidences diverse (not a fabricated (0,0.5) pile); raw traces re-parse to
   stored decisions.
4. **Prereg D5.23 conformance:** exactly the 4 ladder models, all via proxy (provider type ghc), matched
   seeds (42/2024), 6 personas, axis-2 dark = Wrong-AI-GT (dark), per-model reported (pooled labelled
   descriptive). Confirm gpt-5.5 rows are byte-identical to the cross-vendor gpt-5.5 (shared cache, same
   key) — a good consistency check.
5. **No leakage:** human reliance only in item SELECTION, never in panel prompts.
6. **Honest interpretation — CRITICAL:** the Manager's reading is that this is NOT a clean monotone
   capability curve: axis-2 over-reliance is MODEL-IDIOSYNCRATIC (only gpt-4.1 over-relies; smallest
   gpt-4o-mini is at chance) with reliable FRONTIER RESISTANCE (gpt-5.5), while axis-1
   heterogeneity/over-dispersion CLEANLY collapses at the frontier, and persona-p5 susceptibility is the
   robust invariant. VERIFY the data support this nuanced reading and FLAG if you think the numbers
   support a cleaner monotone (or a weaker) claim than stated. Guard against over-claiming a clean curve.

## Deliverable
Per-check CORRECT/INCOMPLETE/WRONG with command evidence, then `VERDICT: PASS`/`FAIL`.
