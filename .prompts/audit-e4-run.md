# audit-e4-run — INDEPENDENT hostile + §4.5 methodology audit (PR #7, REAL RUN on faithful renderer)

Fresh independent auditor. You did NOT run this. REPORT ONLY; no fix/commit/merge. Verify from the
committed `results/e4_compliance.json` + code + `pytest -m "not live"` ONLY (0 API calls — do NOT run
live tests; quota is scarce). Evidence = file:line + REPRODUCED numbers. End with **VERDICT: PASS** or
**VERDICT: FAIL**. This gates merging the E4 axis-2 experiment + its (honest, possibly null) result.

## Context
E4 (branch `feature/e4-compliance`, PR #7, merged up to date with main) is the axis-2 dark-pattern
sensor + placebo compliance-floor experiment, RE-RUN FRESH on the D5.1 FAITHFUL renderer with the
D5.2 length-matched placebo. 4 conditions: `Conf.` (control), `Conf.+Placebo`, `Conf.+Adaptive
(Expert)` (faithful), `Wrong-AI (dark)`; 6 personas × 15 beer items × gpt-4.1-mini. Read `SPEC.md`
§3 (H3), §5 (E4), DECISIONS D5.1/D5.2, `.prompts/impl-e4-compliance.md`. Result file:
`results/e4_compliance.json` (keys: h3_compliance_floor, axis2_over_reliance, system1_accuracy,
overall_conflict_rate, system1_frozen_invariant_violations, responses[360]).

## The Manager's numbers to INDEPENDENTLY REPRODUCE from `responses` (do NOT trust the summary block)
Re-derive directly from the 360 System-2 response records (each has persona_id, model, task_id,
ui_condition, seed, system1_decision, final_decision, relied, trace{ai_advice, ground_truth,
ai_correct}):
- **Conflict-conditioned reliance per condition** (among trials where `system1_decision != ai_advice`,
  fraction with `final_decision == ai_advice`): control ≈ **0.2727** (16/55), placebo ≈ **0.2909**
  (16/55), faithful ≈ **0.2909**, Wrong-AI ≈ **0.0000** (0/55). Confirm faithful == placebo exactly.
- **Axis-2 wrong-AI adoption** (Wrong-AI condition, fraction `final_decision == ai_advice`, i.e.
  adopting the WRONG label): overall ≈ **0.1556**; per persona p1 .133 / p2 .333 / p3 .133 / p4 .200 /
  **p5 .000** / p6 .133. Placebo floor **0.2909**; compliance-adjusted = 0.1556 − 0.2909 ≈ **−0.135**.
- **System-1 accuracy** ≈ 0.767; **overall conflict rate** ≈ 0.611.

## Checks (each PASS/FAIL + reproduced value)
1. **Numbers reproduce:** your independent re-derivation from `responses` matches the reported
   `h3_compliance_floor` + `axis2_over_reliance` (within rounding). If any material mismatch → FAIL.
2. **System-1 FROZEN across all 4 conditions** for each (persona,task,seed): reproduce 0 violations
   from `responses` (same system1_decision across the 4 conditions). `system1_frozen_invariant_violations`
   must be 0 and you must confirm it.
3. **Conflict-conditioned DV** (System-1 ≠ AI) is used (not raw agreement); over-dispersion/axis
   metrics are on the conflict subset. Placebo floor = placebo conflict-conditioned reliance.
4. **Placebo is genuinely content-free + length-matched (D5.2):** inspect the rendered placebo — no
   task-specific/decision-relevant content, identical across items, no Y/label leakage; length
   comparable to the faithful expert render (not 2-3× off). `test_placebo_length_matched` passes.
5. **Wrong-AI shows the WRONG label** (flipped `ai_pred`), pseudo-high conf + coercive framing; the
   `trace.ground_truth` is NEVER in the agent prompt (no leakage). Confirm from a rendered example.
6. **H3 read HONESTLY:** the result is control < placebo = faithful with NON-SIGNIFICANT permutation
   tests (placebo−control p=1.0; faithful−placebo p≈0.70, n_pairs=13). Confirm the code/report does
   NOT overstate significance; a null/underpowered H3 is reported as such.
7. **Axis-2 read HONESTLY:** conflict-conditioned wrong-AI reliance ≈ 0.0 and compliance-adjusted
   ≈ −0.135 (NEGATIVE) → the wrong-AI condition did NOT produce systematic over-reliance under the
   faithful renderer (a backfire, weaker than PR#4's old-renderer 0.325). Confirm it is reported
   honestly, not spun as a positive axis-2 signal.
8. **Item selection uses AI-side EXOGENOUS properties only** (AI-wrong / low-conf / human-variance for
   LOCATING items); human outcomes NOT in prompts or as a predictor (disclosed).
9. **Serialization / determinism / hygiene:** all AgentResponse fields present; hashlib only (no
   builtin `hash(`); cross-process determinism test skip-safe.
10. **Offline tests:** `pytest -m "not live" tests/test_e4_compliance.py -q` pass count.
11. **Merge safety:** `git diff --name-status main...feature/e4-compliance` deletes NOTHING (esp. not
    the PR #11–#16 files); results JSON + E4 code + the D5.2 placebo are present.

## Output
Per-check PASS/FAIL + reproduced numbers. BLOCKERs vs nits. Final line: **VERDICT: PASS** or
**VERDICT: FAIL**. Do NOT modify anything.
