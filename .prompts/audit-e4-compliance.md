# audit-e4-compliance — INDEPENDENT hostile + §4.5 audit (PR #7)

You are a FRESH, independent auditor. You did NOT write this code. Try to break the
E4 axis-2 sensor + placebo baseline. REPORT ONLY; do NOT fix or merge. Verify from the
POPULATED CACHE / results JSON (0 API calls) and `pytest -m "not live"` ONLY — do NOT
run live tests (scarce daily quota). Evidence = file:line + reproduced numbers.

## Context
Branch `feature/e4-compliance` (draft PR #7) adds E4: a PLACEBO-explanation condition to
isolate the compliance floor + a formalized axis-2 systematic-over-reliance sensor, on the
PR#4 panel. Read: `SPEC.md` (§2 C1 PRIMARY; §5 E4; §3 H3), `INTERFACES.md` (§3/§4/§8),
`PROGRESS.md` (E4 entry + PR#4 wrong-AI 0.325 + p5 backfire + Known pitfalls),
`.prompts/impl-e4-compliance.md`. Diff: `git --no-pager diff main...feature/e4-compliance`.
Key files: `src/twdf/data/bansal_tasks.py` (placebo render), `src/twdf/experiments/
e4_compliance.py`, `configs/e4_compliance.yaml`, `src/twdf/metrics/overdispersion.py`
(compliance-floor + axis-2 helpers), `tests/test_e4_compliance.py`, and (if present)
`results/e4_compliance.json` (Manager-generated).

## Checks (PASS/FAIL + evidence)
1. **Placebo is genuinely content-free + no leakage:** the `"Conf.+Placebo"` renderer emits a
   present, format/length-matched explanation with NO task-specific decision-relevant content;
   it is IDENTICAL (or non-diagnostic) across different tasks and does NOT leak `Y`/label/
   decision cues. Inspect the placebo text + a rendered example. If it encodes task-specific
   info, FAIL.
2. **System-1 frozen across ALL 4 conditions** (control/faithful/placebo/dark) for fixed
   (persona,task,seed). Verify in code AND, if results exist, in the responses (0 violations).
3. **Compliance-floor metric (H3):** correctly computes conflict-conditioned reliance for
   control/placebo/faithful and the contrasts placebo−control and faithful−placebo with a
   WITHIN-pair permutation test + bootstrap CI. Re-derive from the results JSON (if present)
   and/or verify on the synthetic test fixtures. Confirm the H3 ordering claim
   (control < placebo < faithful) is only ASSERTED where the data supports it (honest if not).
4. **Axis-2 sensor:** `over_reliance_level` on wrong-AI = adoption of the WRONG label; the
   NEW compliance-adjusted value = over_reliance − placebo floor is computed correctly.
   Wrong-AI condition genuinely shows the wrong label. Per-persona breakdown present.
5. **Two axes SEPARATE**; conflict-conditioned DV; NO degenerate n<3 correlation; NO threshold
   freezing (τ stays unfrozen).
6. **Serialization:** all AgentResponse fields present in results (persona_id, model, task_id,
   ui_condition, seed, system1_decision, final_decision, relied, confidence, trace,
   trust_state) — no PR#3-style regression.
7. **Determinism & hygiene:** cross-process determinism test skip-safe (skips on cold cache /
   quota, not hard-fail); builtin `hash()` banned (grep); `pytest -m "not live"` GREEN (report
   counts; tests not weakened, STRONG synthetic thresholds); token not committed;
   `data/cache/` + `data/raw/` gitignored.
8. **Anti-gaming:** the synthetic metric tests use strong known-pattern thresholds and were not
   weakened to pass.

## Output
Markdown report: overall verdict (PASS / FAIL / CONDITIONAL PASS); per-check PASS/FAIL +
evidence + any reproduced numbers; explicit note on whether the placebo is truly content-free
and whether any H3/axis-2 claims are honestly stated vs the data; prioritized BLOCKER list.
Do NOT modify code or merge. Print the report in your final message.
