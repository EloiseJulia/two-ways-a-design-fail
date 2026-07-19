# AUDIT — amzbook 2nd-domain arms (D5.26): cross-domain generalization

Independent HOSTILE + methodology audit. You did NOT run these. Reproduce from raw `responses`; do not
trust summaries. Report per-check + `VERDICT: PASS`/`FAIL`. Do NOT merge/edit/push. Read-only, no live calls.

## Repo / env
`C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail` (Windows PowerShell).
- `$env:PYTHONPATH=(Resolve-Path .\src).Path`; `$env:GH_TOKEN=$null` before `gh`.
- 4 results: `results/{axis2_powered_crossvendor,axis2_powered_capladder,confirmatory_axis1_crossvendor,confirmatory_axis1_capladder}_amzbook.json`.
- Prereg DECISIONS **D5.26** (amzbook, matched protocol to beer D5.18/D5.23; domain=amzbook; item seeds
  axis-1=42/axis-2=2024; per-model NO pooling; report regardless). Compare to beer D5.20/D5.24.

## Manager re-derivation to reproduce (don't trust it)
- AXIS-2 over-reliance on dark (displayed=1-ground_truth, n=120/model):
  cross-vendor: gpt-5.5 0.150, claude-sonnet-4.5 0.442, gemini-2.5-pro 0.492.
  capladder: gpt-4o-mini 0.475, gpt-4.1 **0.658 (p=0.0003)**, gpt-4o 0.475, gpt-5.5 0.150.
  persona p5 = 1.0 for non-frontier models; gpt-5.5 lower (~0.40).
- AXIS-1 conflict over-dispersion / mean disagreement:
  cross-vendor: claude 0.025/0.036, gemini 0.328/0.080, gpt-5.5 0.000/0.015.
  capladder: gpt-4o-mini 0.343/0.124, gpt-4.1 0.577/0.192, gpt-4o 0.440/0.108, gpt-5.5 0.000/0.015.
  correspondence rho ~0 (n=5, degenerate; amzbook human anchor near-constant).

## Checks (be adversarial)
1. **AXIS-2 from raw responses (both arms):** filter dark ("Wrong-AI-GT (dark)"); recompute displayed wrong
   advice as `1 - trace['ground_truth']` (E4 trap — do NOT trust stored ai_advice for scoring); score
   over-reliance per model + binomial vs 0.5. Reproduce the numbers; confirm stored-vs-recomputed advice
   mismatch = 0; confirm ONLY gpt-4.1 is significantly above chance and gpt-5.5 significantly below.
2. **AXIS-1 from the results (both arms):** reproduce per-model conflict over-dispersion + mean disagreement.
   Confirm gpt-5.5 near-homogeneous (~0.015 disagreement, 0.000 od) on BOTH arms; non-frontier elevated.
3. **Parser-clean:** decisions/confidences diverse (not a fabricated (0,0.5) pile); raw re-parse to stored.
4. **Prereg D5.26 conformance:** domain=amzbook in all 4 configs; amzbook items (seed 42 → the 20 amzbook IDs
   `12,13,14,15,16,17,18,20,21,22,25,26,27,3,33,34,4,44,45,8`); matched seeds; correct model sets; per-model
   no pooling; axis-1 uses `results/e1_multicond_amzbook.json` (amzbook-only anchor).
5. **No leakage:** human reliance only in item selection, never in panel prompts (scan amzbook prompts).
6. **Generalization claim (CRITICAL, honest):** verify the data support "the beer capability-dependence
   pattern GENERALIZES to amzbook" — (a) gpt-4.1 sole significant over-relier on BOTH domains, (b) gpt-5.5
   resists on both, (c) axis-1 frontier heterogeneity collapse on both, (d) persona p5 robust. FLAG any
   overclaim, and note honest domain DIFFERENCES (e.g. absolute over-reliance lower on amzbook; claude axis-1
   more homogeneous on amzbook than beer). Guard against overstating "generalizes" beyond what holds.

## Deliverable
Per-check CORRECT/INCOMPLETE/WRONG with command evidence, then `VERDICT: PASS`/`FAIL`.
