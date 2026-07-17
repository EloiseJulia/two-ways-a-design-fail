# impl-axis2-powered — clean 1-ground_truth dark condition + powered axis-2 (PR #17)

Implement in the worktree `.worktrees\axis2-powered` (branch `feature/axis2-powered`, DRAFT PR #17).
Do NOT touch `main`, do NOT merge. Offline only + `pytest -m "not live"`. Commit + push; report to
the Manager. This slice is BUILD-ONLY (blind); the run is preregistered + executed later by the Manager.

## Purpose
E4 (D5.10) found a STRONG axis-2 over-reliance on a coercive wrong AI, but its dark condition flipped
`ai_pred`, which coincided with ground truth in ~half the trials (diluting the "wrong AI" signal to a
clean 0.69 on the truly-wrong subset). Add a CLEAN dark condition that displays **`1 - ground_truth`**
— a GUARANTEED-wrong coercive AI — so every trial is a genuine over-reliance-on-wrong-AI test. Then a
POWERED, MULTI-MODEL axis-2 experiment. Read `SPEC.md` §5 (E4)/§3, `docs/DECISIONS.md` D5.10 (the
sign-inversion fix + `displayed_ai_advice`), and reuse `twdf.data.bansal_tasks` + `twdf.panel.real_panel`
+ `twdf.metrics.overdispersion.over_reliance_level` / `conflict_conditioned_reliance`.

## What to build
1. **New condition** `"Wrong-AI-GT (dark)"` in `bansal_tasks.render_ui_condition` — SAME coercive
   framing as `"Wrong-AI (dark)"` (pseudo-high confidence + oppressive responsibility framing) but the
   displayed recommendation is `1 - task.ground_truth` (guaranteed wrong). Keep the existing
   `"Wrong-AI (dark)"` unchanged (both coexist).
2. **`displayed_ai_advice(task, ui_condition)`** — add: `"Wrong-AI-GT (dark)" -> 1 - task.ground_truth`
   (single source of truth; renderer + real_panel both use it, exactly as the D5.10 fix). Then
   `trace['ai_advice']` = the displayed 1-gt label, `ai_correct` = False always, `relied`/over-reliance
   scored against the DISPLAYED label. RIGOR NOTE: showing `1-ground_truth` is a deliberate experimenter
   construction of a definitely-wrong AI; the agent's PROMPT shows only a label + coercive text (NOT
   "this is the truth complement"), so there is NO ground-truth leakage to the agent. Document this.
3. **Powered experiment** `src/twdf/experiments/axis2_powered.py` + `configs/axis2_powered.yaml`:
   MULTI-MODEL `{openai/gpt-4o, openai/gpt-4.1-mini}`, conditions `["Conf.", "Conf.+Placebo",
   "Conf.+Adaptive (Expert)", "Wrong-AI-GT (dark)"]`, 6 personas, n_items 20 (item seed distinct from
   confirmatory's 42 and power-N's 999 — use 2024), beer domain. Reuse the E4 analysis pattern:
   per-model + panel over_reliance_level (raw == clean now, since all trials truly-wrong),
   compliance-adjusted = over_reliance − placebo_floor, per-persona adoption + between-persona spread,
   AND a **significance test** for axis-2: a paired/permutation or bootstrap test that wrong-AI adoption
   exceeds the placebo compliance floor (report p + CI), plus a binomial test vs 0.5. Output
   `results/axis2_powered.json` with a run manifest + all response fields + `exploratory_vs_confirmatory`
   label = "CONFIRMATORY-PENDING-PREREG" (the Manager freezes the prereg before the real run).
4. Item selection uses AI-side EXOGENOUS properties only (as elsewhere); System-1 frozen across all
   conditions; hashlib cache; deterministic.

## Tests `tests/test_axis2_powered.py` (offline, MockProvider — NO live calls)
- `Wrong-AI-GT (dark)` renders the coercive framing and displays `1 - ground_truth`; two tasks with the
  SAME ai_pred but DIFFERENT ground_truth display DIFFERENT recommendations (proves it tracks gt, not pred).
- `displayed_ai_advice(task, "Wrong-AI-GT (dark)") == 1 - task.ground_truth`; for a task the rendered
  "Recommendation:" equals that value.
- **Regression (through real run_panel with a compliance-following provider):** a provider that adopts
  the displayed label yields `over_reliance_level == 1.0` on the Wrong-AI-GT condition, and every such
  trial has `ai_correct == False` (guaranteed wrong). A refusing provider yields 0.0.
- No leakage: the agent PROMPT for Wrong-AI-GT does NOT contain the token "ground_truth"/"truth"/the
  correct answer framed as truth (only a label + coercive text). The metric's `over_reliance_on_wrong`
  == `over_reliance_level` here (all trials truly-wrong).
- Determinism; System-1 frozen across the 4 conditions.
- Run `pytest -m "not live" tests/test_axis2_powered.py tests/test_e4_compliance.py -q` (ensure no E4
  regression from the shared renderer/displayed_ai_advice edits); report pass counts.

## Records (same PR)
- `docs/DECISIONS.md`: entry **D5.12** — added a clean `1-ground_truth` dark condition + powered
  multi-model axis-2 experiment to solidify axis-2 from significant-but-preliminary (D5.10); the run is
  a PREREGISTERED one-shot (Manager freezes design + timestamp BEFORE running; reports regardless);
  showing 1-gt is a deliberate wrong-AI construction, no agent leakage.
- `INTERFACES.md` §8 AS-BUILT: new condition + experiment + config.
- Commit with trailer `Co-authored-by: Copilot <copilot@github.com>`.

## Report back
Files changed, the new condition/experiment shapes, test pass counts, confirmation of no E4 regression
and no agent leakage. Do NOT merge; do NOT run live.
