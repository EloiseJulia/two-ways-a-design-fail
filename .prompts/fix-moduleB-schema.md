# fix-moduleB-schema — resolve audit BLOCKER-1 (response serialization)

You are a focused fix subagent on branch `feature/moduleB-panel` in worktree
`.worktrees/moduleB-panel`. The independent audit returned CONDITIONAL PASS with
exactly ONE blocker. Fix ONLY that. Do NOT change the science, metrics, pacing, or
interfaces. Do NOT merge.

## BLOCKER-1 (INTERFACES.md §3 compliance)
The serialized responses in `results/e1_panel_v1.json` omit `model`, `trace`, and
`trust_state`. Per INTERFACES §3, `AgentResponse` has: persona_id, model, task_id,
ui_condition, seed, system1_decision, final_decision, relied, confidence, trace,
trust_state. The experiment's response serialization
(`src/twdf/experiments/e1_panel_v1.py`, around the response→dict block ~L335) must
emit ALL fields:
- `model` (provider.name),
- `trace` (the full dict already on the AgentResponse — keep it; do not truncate),
- `trust_state` (serialize as `null` in static mode).

## Steps
1. Update the serialization so every AgentResponse field is written. Prefer
   `dataclasses.asdict(resp)` or explicit inclusion of the 3 missing fields; keep
   existing field names/values unchanged.
2. Regenerate the results JSON (cache holds all 300 responses → **0 API calls**):
   `python -m twdf.experiments.e1_panel_v1 --config configs/e1_panel_v1.yaml`
   (GH_MODELS_TOKEN is in your env; provider init needs it but no calls are made —
   confirm `total_api_calls: 0`, `cache_hits: 300` in the new manifest).
3. Confirm the new `results/e1_panel_v1.json` responses now contain `model`,
   `trace`, `trust_state`. The scientific numbers (panel_disagreement, elasticity
   mean_diff=0.0/p=1.0, system1_accuracy=0.8) MUST be UNCHANGED — if any changed,
   STOP and report (that would indicate the regen altered results).
4. `pytest -q` — must stay green; report counts.
5. Grep `\bhash\(` (excluding hashlib/comments) = zero; confirm token not committed.
6. Commit (trailer `Co-authored-by: Copilot <copilot@github.com>`) and push to
   `feature/moduleB-panel`. Do NOT commit any scratch files (e.g. *.log, *_output.txt,
   audit reports) — only the code + regenerated results.

## Report
State: what you changed (file:line), confirmation the 3 fields are now present, the
unchanged scientific numbers, pytest counts, and the new manifest api_calls/cache_hits.
Do NOT claim "done/all green" — report facts; the Manager verifies determinism +
clean worktree before merge.
