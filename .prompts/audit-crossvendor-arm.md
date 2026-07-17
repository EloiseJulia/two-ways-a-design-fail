# AUDIT — cross-vendor arm results (D5.18): axis-2 + axis-1 on gpt-5.5 / claude / gemini

Independent HOSTILE + methodology audit. You did NOT run these. Verify the numbers and the
honest interpretation. Report per-check evidence + `VERDICT: PASS`/`FAIL`. Do NOT merge/edit/push.

## Repo / env
`C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail` (Windows PowerShell).
- `$env:PYTHONPATH=(Resolve-Path .\src).Path`; `$env:GH_TOKEN=$null` before `gh`.
- Result files (already on main / working tree):
  `results/axis2_powered_crossvendor.json`, `results/confirmatory_axis1_crossvendor.json`.
- Human anchor: `results/e1_multicond.json`. Prereg: DECISIONS **D5.18** (frozen model set
  gpt-5.5 + claude-sonnet-4.5 + gemini-2.5-pro; per-model NO pooling; matched item seeds
  axis-1=42, axis-2=2024; axis-2 primary; report regardless). Parser fix = D5.19.

## Context (Manager's re-derivation — reproduce independently, don't trust it)
- AXIS-2 (dark = "Wrong-AI-GT (dark)", displayed advice = 1-ground_truth, n=120/model):
  gpt-5.5 over-reliance 0.300 (binomial vs 0.5 p=1.0, BELOW chance), claude 0.492 (p=0.61),
  gemini 0.525 (p=0.32). vs primary gpt-4.1-mini 0.69 (p=0.0098). Conclusion: 0/3 replicate.
  Persona p5 (trusting-novice) stays high: claude 0.95 / gemini 1.00 / gpt-5.5 0.60.
- AXIS-1 cross-condition correspondence (panel over-dispersion vs human over-dispersion, n=5
  conditions): claude rho -0.20, gemini -0.31, gpt-5.5 +0.10 — all non-significant.

## Checks (be adversarial)
1. **Axis-2 recomputation (from raw `responses`):** filter dark condition; INDEPENDENTLY recompute
   displayed wrong advice as `1 - trace['ground_truth']` (do NOT trust a stored ai_advice field —
   this is the E4 sign-inversion trap, D5.10); score `over = (final_decision == displayed_wrong)`;
   per model compute rate + binomial vs 0.5. Must reproduce 0.300 / 0.492 / 0.525. Confirm
   `trace['ai_advice']` EQUALS `1-ground_truth` on ALL dark trials (stored-vs-recomputed mismatch = 0).
2. **Axis-1 recomputation:** per model, recompute the Spearman between panel disagreement/over-dispersion
   and human per-condition over-dispersion across the 5 conditions from the aligned table; must reproduce
   -0.20 / -0.31 / +0.10. Note whether any p<0.05 (should be none; n=5 has ~no power).
3. **Parser-fix cleanliness:** the OLD parser fabricated (0,0.5). Confirm these runs are post-fix: scan
   the `responses` — decisions/confidences should be DIVERSE (not a suspicious pile of exactly
   decision=0/confidence=0.5). Spot-check a few raw traces parse to the stored decision.
4. **Prereg conformance (D5.18):** exactly the frozen trio; per-model reported (no cross-model POOLING
   presented as the primary — a pooled 'panel' block may exist but must be labelled descriptive only);
   matched item seeds (axis-1=42, axis-2=2024); 6 personas; axis-2 dark = Wrong-AI-GT (dark).
5. **No leakage:** human reliance used only for item SELECTION, never in panel prompts/predictors
   (disclosed). Confirm nothing in the panel prompt embeds human outcomes.
6. **Honest interpretation:** verify the data support "axis-2 does NOT replicate on frontier / gpt-5.5
   resists / persona p5 robust" and "axis-1 null-weak across vendors". Flag ANY spin or overclaim, and
   flag if you think the numbers actually support a DIFFERENT conclusion.
7. **Frontier-ceiling evidence:** check per-model conflict-trial fractions / panel disagreement — is
   gpt-5.5 near-homogeneous (low disagreement) consistent with the preregistered ceiling risk? Report
   the conflict counts so the null isn't mistaken for a bug.

## Deliverable
Per-check CORRECT/INCOMPLETE/WRONG with command evidence, then `VERDICT: PASS`/`FAIL`.
