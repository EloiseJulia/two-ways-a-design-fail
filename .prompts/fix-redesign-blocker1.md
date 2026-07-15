# fix-redesign-blocker1 — test hygiene + p5 disclosure (PR #4)

You are a focused fix subagent in worktree `.worktrees/panel-redesign` (branch
`feature/panel-redesign`, draft PR #4). The independent audit returned FAIL with ONE
blocker (test hygiene); all science/security/interface checks PASSED and the Manager
independently confirmed cross-process determinism from the warm cache. Fix ONLY the
blocker + add one honest disclosure. Do NOT change the science/metrics/interfaces.
Do NOT merge. Do NOT burn API quota (gpt-4o-mini is daily-exhausted).

## BLOCKER-1 — cross-process determinism tests must SKIP (not FAIL) when cache is cold
Problem: `tests/test_panel_real.py::test_cache_determinism_cross_process` (and any
analogous cross-process determinism test in `tests/test_panel_redesign.py`) spawns a
subprocess that runs an experiment and compares outputs. It ASSUMES the response cache
is fully populated so the rerun makes 0 API calls. In an environment where the cache is
cold (e.g. a different model, or CI without cache) and the daily quota is exhausted, the
subprocess makes a live call → provider raises the 120s-cooldown RuntimeError → the test
hard-FAILS on an environmental condition. That is not a determinism failure.

Fix: make these cross-process determinism tests **skip gracefully** instead of failing:
- Before the byte-comparison, run the experiment once (in-process or first subprocess)
  and check the run_manifest `total_api_calls`. If it is > 0 (cache NOT warm) OR the run
  raises/exits-nonzero due to a rate-limit/quota RuntimeError, call
  `pytest.skip("cross-process determinism requires a warm response cache / API quota")`.
- Only when the run is fully cached (`total_api_calls == 0`) proceed to assert the two
  separate-process outputs are byte-identical EXCLUDING the run_manifest timestamp/
  wall_time. Keep the STRONG byte-identical assertion for the warm-cache path.
- Apply the same skip-guard to BOTH determinism tests (v1 in test_panel_real.py and the
  redesign one in test_panel_redesign.py) so neither can hard-fail on environment.
This keeps determinism verified when the cache is warm (the intended regression case) and
skips cleanly otherwise. Do NOT simply delete the test or weaken the byte-identical check.

After the fix, `pytest -m "not live"` must be GREEN (determinism tests either PASS on a
warm cache or SKIP cleanly — never FAIL). Report the pass/skip counts. Do NOT run live
tests. If running the redesign experiment during the test, it must report
`total_api_calls: 0` (warm cache); if not, the test should SKIP.

## Disclosure — p5 dark-pattern-backfire finding (audit-confirmed, genuine)
Add an honest note to the E2 entry in `PROGRESS.md`: persona **p5-novice-trusting**
adopted **0% of WRONG AI advice** in the Wrong-AI (dark) condition, vs 55.6% reliance in
the control condition. The independent audit verified this is GENUINE behavior (not a
parsing/label bug): p5 actively changes AWAY from the AI under the oppressive framing.
Possible interpretations (state all, commit to none): (a) tension in the "novice-trusting"
persona label, (b) the coercive dark-pattern BACKFIRES and triggers skepticism in some
agents, (c) gpt-4.1-mini safety training resisting coercion. Flag as a follow-up to
investigate — it is scientifically relevant to axis-2 (dark-pattern sensor) design.

## Steps
1. Implement the skip-guard fix in both determinism tests.
2. `pytest -m "not live"` → GREEN (report pass/skip/fail counts; fail must be 0).
   Grep `\bhash\(` (excl hashlib/comments) = 0. Confirm token not committed.
3. Add the p5 disclosure to PROGRESS.md E2 entry.
4. Do NOT commit scratch (*.log, *_output.txt, audit reports, data/cache, data/raw).
   Commit (trailer `Co-authored-by: Copilot <copilot@github.com>`) + push to
   `feature/panel-redesign`.

## Report (FACTS)
The exact pytest counts (passed/skipped/failed) under `-m "not live"`; how you made the
determinism tests skip-safe (file:line); confirmation the byte-identical assertion is
preserved for the warm-cache path; and that the p5 note was added. Manager re-verifies
+ merges.
