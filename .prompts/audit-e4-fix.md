# audit-e4-fix — INDEPENDENT re-audit of the axis-2 sign-inversion FIX (PR #7)

Fresh independent auditor. REPORT ONLY; no fix/commit/merge. Offline `pytest -m "not live"` + read
the committed `results/e4_compliance.json` ONLY (0 API calls; do NOT run live tests). Evidence =
file:line + REPRODUCED numbers. End with **VERDICT: PASS** or **VERDICT: FAIL**. This re-audits the
fix for the axis-2 sign-inversion bug a prior audit correctly caught (VERDICT FAIL).

## The bug that was fixed
`Wrong-AI (dark)` DISPLAYS `1 - ai_pred`, but `real_panel.py` stored `trace['ai_advice'] = ai_pred`
(unflipped) and scored `over_reliance_level` / `relied` against it → the axis-2 adoption score was the
COMPLEMENT of the truth (reported 0.156 instead of 0.844). Fix: `bansal_tasks.displayed_ai_advice()`
is now the single source of truth (Wrong-AI → 1-ai_pred, else ai_pred), used by the renderer AND
`real_panel` for `relied`, `trace['ai_advice']`, `ai_correct`. Also added `over_reliance_on_wrong`
(adoption restricted to genuinely-wrong-advice trials, `displayed != ground_truth`) so the clean
axis-2 number is reported instead of the raw (label-coincidence-inflated) one. Branch
`feature/e4-compliance` (PR #7), merged up to date with main.

## Checks (each PASS/FAIL + reproduced value)
1. **Scoring now uses the DISPLAYED label:** `real_panel.py` sets `trace['ai_advice'] =
   displayed_ai_advice(task, ui_condition)` and `_compute_reliance(ai_advice=that)`. Confirm in code.
   Reproduce from `results/e4_compliance.json` responses that for EVERY Wrong-AI record
   `trace['ai_advice'] == 1 - ai_pred` (recover ai_pred from the prompt's flipped value or from a
   control-condition record of the same task) and equals the "Recommendation:" shown in the prompt.
2. **Regression test genuinely catches the bug:** `test_wrongai_advice_scored_against_displayed_label`
   drives the REAL `run_panel` with a compliance-following provider and asserts
   `over_reliance_level == 1.0` (the pre-fix code would yield 0.0) + `trace['ai_advice'] == 1-ai_pred`.
   Confirm it is not tautological (it goes through run_panel, not hand-set traces).
3. **Corrected numbers reproduce from `responses`** (score `final == displayed`):
   raw over_reliance_level ≈ **0.844** (76/90); per-persona p1 .867/p2 .667/p3 .867/p4 .800/**p5 1.000**/
   p6 .867. And the CLEAN signal restricted to `displayed != ground_truth` (n≈42): **≈ 0.690 (29/42)**,
   binomial vs 0.5 p ≈ **0.0098**. Confirm `axis2_over_reliance.over_reliance_on_wrong` and
   `n_truly_wrong` in the JSON match your re-derivation.
4. **H3 UNAFFECTED** (only Wrong-AI had the flip): control 0.2727 < placebo 0.2909 = faithful 0.2909;
   placebo−control p=1.0, faithful−placebo p≈0.70. Reproduce and confirm reported honestly as null.
5. **Honest interpretation:** DECISIONS D5.10 reports the reversal (backfire → strong over-reliance),
   uses the CLEAN 0.690 as the axis-2 signal (not the inflated 0.844), and states the caveats
   (underpowered; flip-vs-1−gt design; PR#4 superseded). No overclaim.
6. **No leakage / determinism / hygiene:** ground_truth never enters an agent prompt; hashlib only;
   determinism test skip-safe; System-1 frozen invariant still 0 violations.
7. **Offline tests:** `pytest -m "not live" tests/test_e4_compliance.py -q` pass count (incl. the new
   regression test). Also confirm no other test regressed from the metric/real_panel change
   (`tests/test_panel_real.py`, `tests/test_panel_redesign.py`).
8. **Merge safety:** `git diff --name-status main...feature/e4-compliance` deletes NOTHING (esp. not
   PR #11–#16 files); the shared `real_panel.py`/`overdispersion.py`/`bansal_tasks.py` edits are the
   fix only.

Final line: **VERDICT: PASS** or **VERDICT: FAIL**.
