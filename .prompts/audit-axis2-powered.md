# audit-axis2-powered — INDEPENDENT audit (PR #17, build-only)

Fresh independent auditor. REPORT ONLY; no fix/commit/merge. Offline `pytest -m "not live"` only (do
NOT run live). Evidence = file:line + reproduced values. End with **VERDICT: PASS** or **VERDICT: FAIL**.

## What this PR does
Adds a CLEAN axis-2 dark condition `"Wrong-AI-GT (dark)"` that displays `1 - ground_truth` (a
GUARANTEED-wrong coercive AI, vs E4's `"Wrong-AI (dark)"` which flips ai_pred and coincided with truth
in ~half the trials), wired through `displayed_ai_advice` (single source of truth used by renderer +
real_panel, per the D5.10 fix), plus a powered multi-model axis-2 experiment
(`experiments/axis2_powered.py` + `configs/axis2_powered.yaml`). BUILD-ONLY (blind); the run is
preregistered + executed later. Branch `feature/axis2-powered` (PR #17), merged up to date with main.

## Checks (PASS/FAIL + evidence)
1. **Wrong-AI-GT displays `1 - ground_truth`:** `displayed_ai_advice(task, "Wrong-AI-GT (dark)") ==
   1 - task.ground_truth`; the renderer's "Recommendation:" equals that. Reproduce: two tasks with the
   SAME ai_pred but DIFFERENT ground_truth display DIFFERENT recommendations (proves it tracks gt, not
   pred), and the shown label != ground_truth in BOTH (guaranteed wrong).
2. **E4's `"Wrong-AI (dark)"` UNCHANGED** (still flips ai_pred) — E4 continuity preserved.
3. **No agent leakage:** the Wrong-AI-GT PROMPT contains only a label + coercive framing — NOT the words
   "ground_truth"/"truth" nor any statement that the label is the truth-complement. (Using 1-gt to
   CONSTRUCT the stimulus is a legitimate experimenter action; the agent must not be able to infer it.)
   Confirm no other renderer/selection path leaks ground_truth into a prompt.
4. **Scoring correct (via real run_panel + MockProvider):** a compliance-following provider →
   `over_reliance_level == 1.0` on Wrong-AI-GT and every such trial `ai_correct == False`; a refusing
   provider → 0.0. `over_reliance_on_wrong == over_reliance_level` (all trials truly-wrong).
   `trace['ai_advice']` == the displayed 1-gt label. Reproduce.
5. **Powered experiment + significance:** config is multi-model {gpt-4o, gpt-4.1-mini}, 4 conditions
   (control/placebo/faithful/Wrong-AI-GT), 6 personas, 20 items, item seed 2024 (distinct from
   confirmatory 42 / power-N 999). The analysis reports per-model + panel over_reliance, compliance-
   adjusted (− placebo floor), per-persona, AND a significance test (permutation/bootstrap vs placebo
   floor + binomial vs 0.5). Output labeled so it is NOT mistaken for a frozen confirmatory result.
6. **System-1 frozen across conditions; determinism; hashlib only / no builtin `hash(`.**
7. **No E4 regression:** `pytest -m "not live" tests/test_axis2_powered.py tests/test_e4_compliance.py -q`
   pass count (expect 16). Confirm the shared `bansal_tasks`/`real_panel`/metric edits don't break E4.
8. **Merge safety:** `git diff --name-status main...feature/axis2-powered` deletes NOTHING (esp. not
   PR #7/#11–#16 files); additive + the shared renderer/real_panel edits for the new condition only.
9. **Records:** `docs/DECISIONS.md` D5.12 + `INTERFACES.md` §8.

Final line: **VERDICT: PASS** or **VERDICT: FAIL**.
