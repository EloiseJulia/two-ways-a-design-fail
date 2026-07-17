# AUDIT — PR #22 P0 robust panel decision parser (fix/panel-decision-parser)

Independent HOSTILE + methodology audit. You did NOT write this. Try to break it and
its claims. Report per-check evidence + a single `VERDICT: PASS`/`FAIL`. Do NOT merge/edit/push.

## Repo / env
`C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail` (Windows PowerShell).
- `$env:PYTHONPATH=(Resolve-Path .\src).Path` to run python; `$env:GH_TOKEN=$null` before `gh`.
- Full test suite hangs on network downloads — run only the named test files.
- Diff: `git fetch origin; git diff origin/main...origin/fix/panel-decision-parser`.
- Files: `src/twdf/panel/real_panel.py` (parser), `tests/test_panel_parser_robust.py`.

## The bug being fixed
`_parse_decision_response` / `_parse_decision_with_confidence` used strict `json.loads`
on a non-brace-balanced regex; on `JSONDecodeError` (literal control chars / bare newlines
in `reasoning`, ```json fences, nested braces) they jumped to `except` and returned a
SILENT default `decision=0 (conf=0.5)` — WITHOUT trying the regex fallback. This
systematically biased axis-1 over-dispersion & axis-2 over_reliance for verbose models.

## Claims to verify (be adversarial)
1. **Recovery:** the fixed parser recovers the TRUE decision from: (a) bare-newline control
   chars in a string value, (b) ```json fences, (c) nested braces in reasoning, (d) prose
   prefix then JSON, (e) malformed JSON but explicit `decision: N` (regex fallback). Prove by
   running the tests AND your own adversarial strings.
2. **Never fabricates:** on a response with NO extractable 0/1 decision, the parser RAISES
   `PanelParseError` — it does NOT return `(0, 0.5)` or `(0, ...)`. Grep the diff to confirm no
   `return 0, 0.5` / `return 0,` default path remains. An invalid decision value (e.g. 7) must
   also raise, not clamp to 0.
3. **Real-data measurement (independent):** scan `data/cache/panel/*.json` (raw responses).
   Reproduce the BEFORE failure counts with the OLD logic (expect ~claude 25/1140, gemini 1/490,
   gpt-4o 0/403, gpt-4.1-mini 0/786, gpt-5.5 0/1140) and confirm the FIXED parser raises on
   **0 / 3959**. This is the load-bearing "self-heal" evidence — verify it yourself, do not trust
   the PR. NOTE: the cache lives in the MAIN repo dir (gitignored), so run this from the main
   working tree with `PYTHONPATH` pointed at the FIXED branch's `src` (checkout the branch or use
   the worktree path).
4. **Merged results clean:** confirm primary `openai/gpt-4o` + `openai/gpt-4.1-mini` had 0
   old-parser failures → merged E4 / e1_multicond / confirmatory numbers are unaffected.
5. **Self-heal validity (§4.5):** confirm the provider cache stores the RAW model response (not
   the parsed default), so re-running re-parses correctly — i.e. no cache wipe is required for the
   26 recoverable cases. Confirm there is NO code path that caches a fabricated decision.
6. **Raise safety:** review `run_panel` / `_system1_no_ai` / `_system2_with_ai`. Does an
   uncaught `PanelParseError` risk a resume-crash-LOOP (same cached bad response re-raises every
   resume)? Assess whether this is acceptable given 0/3959 current failures, and whether the fix
   should instead record-missing/exclude. State your judgment (this is a design call, not
   necessarily a blocker) — but FLAG if you think raise is wrong.
7. **Additive / no regression:** existing panel tests still pass
   (`tests\test_panel_real.py tests\test_panel_redesign.py tests\test_e4_compliance.py`
   `tests\test_panel_parser_robust.py`). `git diff --diff-filter=D` empty.

## Deliverable
Per-check CORRECT/INCOMPLETE/WRONG with command evidence, then `VERDICT: PASS`/`FAIL`.
