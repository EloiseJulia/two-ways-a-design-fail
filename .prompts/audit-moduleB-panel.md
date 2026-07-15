# audit-moduleB-panel — INDEPENDENT hostile + §4.5 methodology audit

You are a FRESH, independent audit subagent. You did NOT write this code. Your job
is to try to BREAK it — find methodology errors, determinism failures, leakage,
mislabeled science, and security issues. You **report only**; you do NOT fix or
merge. Be hostile and specific. "It runs" is NOT a pass — a methods paper dies on a
silent statistical or design error.

## Context
Branch `feature/moduleB-panel` (draft PR #3) implements Module B: a real LLM panel
via GitHub Models replacing the synthetic stub. Read first: `SPEC.md`,
`INTERFACES.md` (§3 Panel, §8 AS-BUILT), `PROGRESS.md` (Known pitfalls +
Preregistration), `.prompts/impl-moduleB-panel.md` (the spec the impl was given),
then the new/changed code:
`src/twdf/panel/provider.py`, `src/twdf/panel/real_panel.py`,
`src/twdf/data/bansal_tasks.py`, `src/twdf/experiments/e1_panel_v1.py`,
`configs/e1_panel_v1.yaml`, `tests/test_panel_real.py`, `results/e1_panel_v1.json`,
`.gitignore`, and PROGRESS/INTERFACES diffs. Use `git --no-pager diff main...feature/moduleB-panel`.

## Checks (each: PASS/FAIL + file:line evidence + how to reproduce)

### A. Security / secrets
1. `GH_MODELS_TOKEN` value NEVER hard-coded, printed, logged, or committed. Grep the
   diff + `results/*.json` + any cache for token-like strings. Cache dir + `data/`
   are gitignored and NOT staged.

### B. Determinism (the project's #1 recurring bug)
2. Builtin `hash()` is BANNED. Grep `\bhash\(` (excluding `hashlib`/comments) across
   changed files — must be zero.
3. **Cross-process** determinism: actually RUN the offline cache-determinism test in
   TWO separate processes and confirm byte-identical outputs. A single-process
   double-call does NOT count. If the test only double-calls in one process, FAIL it.
4. The response cache key includes model, messages, temperature, max_tokens, seed
   (via hashlib). A cache hit returns identical content with zero API calls.

### C. Scientific correctness (the core)
5. **Counterfactual pairing invariant:** for fixed (persona, task, seed), the
   `system1_decision` is IDENTICAL across the control and treatment UI arms, and only
   the UI rendering differs. Verify in code AND by inspecting produced responses.
   If System-1 is recomputed per-arm (or leaks the UI), FAIL.
6. **No n=2 degenerate correlation:** confirm NO cross-condition disagreement↔
   over-dispersion correlation is computed/reported anywhere in this slice (it must be
   deferred). If present, FAIL (this exact bug was fought in PR #1).
7. **Reliance definition** is documented and consistent with Bansal adoption
   (final decision == AI advice). Check it isn't trivially always-true/always-false.
8. **Condition→content mapping faithful:** control `Conf.` = pred+conf, no
   explanation; treatment `Conf.+Adaptive (Expert)` = pred+conf + `expert`-highlight
   explanation. Exact Bansal strings. No mislabeled conditions.
9. **Elasticity statistics:** the paired permutation test shuffles labels WITHIN each
   persona×task pair (not across), ≥10k shuffles, seeded/hashlib; bootstrap CI over
   the right unit. Re-derive the reported effect/p/CI from `results/e1_panel_v1.json`
   by rerunning; numbers must match the JSON (trust only re-run output, not prose).
10. **testid↔questionId join** is real: independently confirm beer `testid`s overlap
    Bansal beer-domain `questionId`s (report the count). If fabricated/empty, FAIL.
11. **Task diversity:** the ~20 sampled tasks span AI-correct AND AI-incorrect items
    and a range of `conf` (few-task/low-diversity attenuates the signal per the
    user×task decomposition). Selection is deterministic.

### D. Interface & hygiene
12. `run_panel` / `Persona` / `AgentResponse` match INTERFACES §3 exactly; field
    names unchanged (other modules import them); `trust_state` still optional.
13. `pytest -q` passes offline (live-API test skipped without token). Report counts.
14. `run_manifest` present in results (config hash, seeds, model, timestamp, api
    calls, cache hits, wall time). Reproducible.
15. Anti-gaming: tests were NOT weakened to pass; synthetic-data assertions use STRONG
    thresholds. If tests look watered-down, FAIL and say which.

## Output
A markdown report: overall verdict (**PASS** / **FAIL** / **CONDITIONAL PASS**), a
table of the 15 checks with PASS/FAIL + evidence (file:line, reproduced numbers), and
a prioritized list of any BLOCKERS the impl must fix before merge. Do NOT modify code.
Do NOT merge. Save your report and also print it in your final message.
