# audit-panel-redesign — INDEPENDENT hostile + §4.5 methodology audit (PR #4)

You are a FRESH, independent auditor. You did NOT write this code. Try to BREAK it:
methodology errors, leakage, determinism failures, mislabeled science, security. You
REPORT ONLY; do NOT fix or merge. "It runs" is NOT a pass. Be hostile and specific
(file:line + reproduced numbers).

## CRITICAL RESOURCE CONSTRAINT — do NOT burn API quota
GitHub Models enforces a PER-MODEL DAILY quota (~500/day). `gpt-4o-mini` is EXHAUSTED
today; `gpt-4.1-mini` was heavily used by this run. **Verify everything from the
POPULATED CACHE (0 API calls) and by re-deriving numbers from the results JSON.** Run
`pytest -m "not live"` ONLY — do NOT run live tests (they will 429 and waste quota).
If a cached rerun reports `total_api_calls > 0`, note it but do NOT loop.

## Context
Branch `feature/panel-redesign` (draft PR #4) redesigns the panel DV after PR #3's
compliance-collapse null. Read first: `SPEC.md` (§2 C0/C1, panel-status note),
`INTERFACES.md` (§3, §4, §8), `PROGRESS.md` (Known pitfalls, Preregistration, the PR#3
diagnosis + the new E2 entry), `.prompts/impl-panel-redesign.md` (the design spec).
Then the diff: `git --no-pager diff main...feature/panel-redesign`. Key files:
`src/twdf/metrics/overdispersion.py` (new `conflict_conditioned_reliance`,
`over_reliance_level`), `src/twdf/data/item_selector.py`, `src/twdf/panel/real_panel.py`
(strong personas + 3-cond), `src/twdf/data/bansal_tasks.py` (Wrong-AI render),
`src/twdf/panel/provider.py` (new `model_name` param + 120s cooldown cap),
`src/twdf/experiments/e2_panel_redesign.py`, `configs/e2_panel_redesign.yaml`,
`tests/test_panel_redesign.py`, `results/e2_panel_redesign.json`.

## Checks (each: PASS/FAIL + evidence + reproduction)
### A. Security
1. `GH_MODELS_TOKEN` never hard-coded/printed/logged/committed (grep diff, results, cache).

### B. Determinism & hygiene
2. Builtin `hash()` banned — grep `\bhash\(` (excl hashlib/comments) = 0 in changed files.
3. Cross-process cache determinism: run the offline determinism test in TWO separate
   processes; assert byte-identical results EXCLUDING run_manifest timestamp/wall_time;
   confirm cached rerun `total_api_calls == 0`. A single-process double-call does NOT count.
4. `pytest -m "not live"` green; report counts. Are the 2 live tests properly MARKED and
   SKIPPED by default (not failing when a token happens to exist)? If live tests FAIL under
   plain `pytest` due to 429, flag as a test-hygiene BLOCKER (they must skip, not fail).

### C. Scientific correctness (the core)
5. **Conflict-conditioned reliance** (new PRIMARY axis-1 DV): verify the definition =
   fraction of trials with System-1 ≠ AI advice on which the agent SWITCHED to AI
   (final == ai_advice | system1 != ai_advice). Re-derive control=0.327 / treatment=0.481
   and the per-persona spread (0.111–0.556) from `results/e2_panel_redesign.json`; must match.
6. **System-1 frozen invariant across ALL 3 conditions** (control/treatment/Wrong-AI):
   for fixed (persona,task,seed) system1_decision identical. Verify in code AND from the
   responses (0 violations). If System-1 leaks the UI or is recomputed per condition, FAIL.
7. **Wrong-AI (dark) condition** genuinely shows the WRONG label (1 - ai_pred, or flipped),
   NOT the correct one; `over_reliance_level` = adoption of that wrong label. Re-derive
   0.325 and per-persona (incl. p5=0.000). INVESTIGATE the p5=0.000 anomaly: is it a
   parsing/label artifact or genuine refusal? Report your finding.
8. **Elasticity stats:** paired permutation shuffles WITHIN persona×task pairs; re-derive
   mean_diff=+0.194, p=0.174, n_pairs=11. Confirm it is honestly reported as UNDERPOWERED /
   not significant (not spun as positive evidence).
9. **No leakage:** human reliance is used ONLY to SELECT items; it MUST NOT appear in any
   agent prompt or as a predictor. Inspect the System-1/System-2 prompt construction and
   item_selector. Item-selection use must be disclosed. If human outcomes reach the agent, FAIL.
10. **Item selector:** deterministic (sorted+seed) and the selected items genuinely satisfy
    the data-driven criteria (AI-wrong / low-conf / high-human-variance). Re-run the selector;
    confirm the same 20 task IDs.
11. **No degenerate correlation** (n=2/n<3) computed anywhere.
12. **Two axes SEPARATE:** axis-1 (conflict-conditioned reliance / disagreement) and axis-2
    (over_reliance_level on wrong AI) computed independently.

### D. Interface & anti-gaming
13. Serialized responses in `results/e2_panel_redesign.json` include ALL AgentResponse
    fields (persona_id, model, task_id, ui_condition, seed, system1_decision,
    final_decision, relied, confidence, trace, trust_state) — PR #3 had a BLOCKER here; check
    it did not regress.
14. `run_manifest` complete (config hash, seeds, model=openai/gpt-4.1-mini, timestamp,
    api_calls, cache_hits, wall_time, est_cost).
15. Anti-gaming: tests use STRONG thresholds and were NOT weakened to pass. Provider
    `model_name` param + 120s cooldown cap behave as documented (daily-cap → fail fast).

## Output
Markdown report: overall verdict (PASS / FAIL / CONDITIONAL PASS), a 15-row table with
PASS/FAIL + evidence (file:line, reproduced numbers), the p5 anomaly finding, and a
prioritized BLOCKER list. Do NOT modify code. Do NOT merge. Print the report in your final message.
