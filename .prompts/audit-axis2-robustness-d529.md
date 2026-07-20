# AUDIT — axis-2 robustness analyses (D5.29), read-only, hostile

You are an INDEPENDENT auditor (fresh eyes), read-only. Reproduce, from RAW responses, the numbers
emitted by `scripts/analysis/axis2_robustness.py` (output `results/axis2_robustness.json`). Do NOT trust
the script; recompute independently in your own throwaway code and compare.

## Setup
- Repo: `C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail`; `$env:PYTHONPATH=(Resolve-Path .\src).Path`.
- Inputs (axis-2, each has top-level `responses` list; each row: model, persona_id, ui_condition,
  task_id, final_decision, trace.{ai_advice, ground_truth}):
  - results/axis2_powered_capladder.json (beer; gpt-4o-mini/gpt-4.1/gpt-4o/gpt-5.5)
  - results/axis2_powered_crossvendor.json (beer; gpt-5.5/claude-sonnet-4.5/gemini-2.5-pro)
  - results/axis2_powered_capladder_amzbook.json (amzbook; ladder)
  - results/axis2_powered_crossvendor_amzbook.json (amzbook; cross-vendor)
- Dark condition = `Wrong-AI-GT (dark)`. adopt = (int(final_decision) == 1 - int(trace.ground_truth)).
- **gpt-5.5 is shared between capladder & crossvendor files and must be de-duplicated** (the script keeps
  the capladder copy). VERIFY the two gpt-5.5 dark sets are byte-identical in final_decision; if they are,
  de-dup is safe; if not, FLAG it.
- 12 cells = 2 domains x 6 models {gpt-4o-mini, gpt-4.1, gpt-4o, gpt-5.5, claude-sonnet-4.5, gemini-2.5-pro}.
  Each cell dark n=120 (6 personas x 20 items). Sign firewall: in the dark arm ai_advice must equal 1-gt.

## Claims to reproduce (recompute yourself; report PASS/FAIL with YOUR numbers)

### Analysis 1 — persona-p5 robustness
- p5 (`p5-novice-trusting`) is the STRICT top-adoption persona in **12/12** cells. (Recompute each cell's
  6 persona adoption rates; confirm p5 is uniquely max in every cell.)
- Per-cell Fisher exact (p5 adopt/n vs pooled other-5 adopt/n, one-sided greater) then BH across 12:
  ALL 12 significant (largest BH p ~= 0.0023). Confirm every cell < 0.05 after BH.
- GEE logistic adopt~is_p5 clustered by cell: odds ratio ~15.0 (CI ~5.8-38.8), p~2e-8. (You may reproduce
  with statsmodels GEE, or sanity-check the pooled OR by hand from the 2x2 p5-vs-others counts and confirm
  it is large and highly significant.)
- p5-minus-others per-cell gap: mean ~0.526, min ~0.300; Wilcoxon signed-rank one-sided p~2.4e-4.

### Analysis 2 — ordering agreement vs rate idiosyncrasy
- Aggregate wrong-AI rate spread: beer range ~0.30 (0.30-0.60), amzbook range ~0.508 (0.15-0.658).
- Persona-ORDERING pairwise Spearman: beer within-domain mean ~0.813; beer independent-vendor
  (gpt-5.5/claude/gemini) mean ~0.872 (min ~0.824); amzbook within ~0.581, indep-vendor ~0.499.
- Cross-domain ordering by model: most 0.79-0.99 EXCEPT gpt-5.5 ~0.281. Confirm the gpt-5.5 outlier.

### Analysis 3 — stats hygiene
- Per-cell Wilson 95% CI + binomtest vs 0.5, BH across 12: confirm ONLY these survive BH<0.05:
  amzbook gpt-4.1 (0.658, BH~0.0027), amzbook gpt-5.5 (0.150, BH~2.4e-14), beer gpt-5.5 (0.300, BH~8.3e-5).
  In particular CONFIRM **beer gpt-4.1 (0.600) does NOT survive BH (p~0.106)** — this is the key honesty
  correction; verify it.
- Between-model Fisher (two-sided): gpt-4.1 vs gpt-4o sig both domains (~0.014 beer, ~0.006 amzbook);
  gpt-5.5 vs gpt-4.1 highly sig both (4.8e-6 / 4.9e-16); vendors vs gpt-5.5 sig.

## Hostile checks
- Sign firewall holds (dark ai_advice==1-gt at 100%; non-dark not).
- De-dup correctness (no double-counting gpt-5.5 → would inflate n to 240 and bias pooled stats).
- No parser sentinels / no leakage (spot check).
- Any mismatch vs the script's numbers → FAIL that claim with your independently computed value.

## Deliverable
Per-analysis PASS/FAIL with YOUR recomputed numbers, the gpt-5.5 de-dup identity check, the beer-gpt-4.1
BH-nonsignificance confirmation, and any red flags. Overall PASS only if everything reproduces within
rounding.
