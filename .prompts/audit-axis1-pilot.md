# audit-axis1-pilot — INDEPENDENT hostile + §4.5 audit (PR #8, EXPLORATORY infra)

You are a FRESH, independent auditor. You did NOT write this code. Try to break the
axis-1 multi-family EXPLORATORY pilot. REPORT ONLY; do NOT fix, commit, or merge.
Verify from CODE + `pytest -m "not live"` ONLY — do NOT run live tests (scarce daily
quota; both gpt-4o and gpt-4.1-mini are daily-capped today). Evidence = file:line +
reproduced numbers/commands. End with an explicit **PASS** or **FAIL** verdict.

## Framing (READ FIRST — what this PR is and is NOT)
This PR merges the pilot as **EXPLORATORY INFRASTRUCTURE ONLY** + a documented
provider-stability limitation. Its real run did NOT yield a usable power/effect
estimate (gpt-4.1-mini capped; Llama-3.3-70B / Phi-4 unstable on GitHub Models:
timeouts / 500s / unparseable→0), so there is NO `results/axis1_pilot.json` and NO
axis-1 effect claim. You are auditing: (a) is the code correct, leakage-free, and
honestly labeled exploratory; (b) are the guardrails intact; (c) is nothing
confirmatory being smuggled in. Do NOT fail the PR for "no power estimate" — that is
the declared, honest outcome (see prereg §8 PENDING). DO fail it if any confirmatory
claim, leakage, non-determinism, or mislabeled result is present.

## Context to read
- `SPEC.md` (§2 C1 PRIMARY / C0 demoted; §3 H1a; §4.2 cross-family), `INTERFACES.md`
  (§3 provider, §8 AS-BUILT), `PROGRESS.md` (PR #8 Doing entry + Known pitfalls),
  `docs/plans/preregistration-axis1.md` (§2 amendment, §8 N PENDING, exclusion rule),
  `docs/DECISIONS.md` (D4.6 pilot failure, D4.7 amendment), `.prompts/impl-axis1-pilot.md`.
- Branch: `feature/axis1-pilot` (already merged up to date with `main`). Diff:
  `git --no-pager diff main...feature/axis1-pilot`.
- Key files: `src/twdf/data/bansal_tasks.py` (5-condition `render_ui_condition` +
  `_extract_lime_highlights`), `src/twdf/experiments/axis1_pilot.py` (multi-provider
  loop + skip-on-cap + readout), `configs/axis1_pilot.yaml`, `tests/test_axis1_pilot.py`.

## Checks (each: PASS/FAIL + file:line evidence)
1. **No label/ground-truth leakage:** none of the 5 renderers or the LIME highlight
   extractor put `ground_truth`/`Y` or any correct-answer cue into the agent prompt.
   Only `ai_pred`, `ai_conf`, LIME highlights, and task text may appear. Inspect a
   rendered example per condition.
2. **5 conditions produce DISTINCT content** and map to the exact Bansal strings
   (`Conf.`, `Conf.+Single`, `Conf.+Double`, `Conf.+Adaptive`, `Conf.+Adaptive (Expert)`).
   Single=top-1, Double=top-2, Adaptive≠Double. Confirm the heuristic nature of
   Single/Double/Adaptive is HONESTLY flagged as EXPLORATORY (docstring + PROGRESS).
3. **System-1 frozen across all 5 conditions AND across all models** for a fixed
   (persona, task, seed). Verify in code and in the test that asserts this.
4. **Conflict-conditioned DV** (reliance measured on System-1 ≠ AI trials), NOT raw
   agreement. Over-dispersion via beta-binomial (excess over p(1−p)), never raw variance.
5. **Degenerate-correlation guard:** cross-condition Spearman over n<3 is guarded/flagged
   (±1 by necessity). Confirm the n<3 guard + the test.
6. **Determinism / hygiene:** hashlib only (`grep \bhash\( src/` → 0 in the new code);
   cross-process determinism test present and skip-safe on cold cache/quota.
7. **skip-on-cap resilience:** the multi-provider loop skips a model on daily-cap/instability
   without corrupting other models' results or fabricating a 0-default that could be
   mistaken for a real reliance value in any SAVED artifact.
8. **No confirmatory smuggling / no researcher-DoF violation:** outputs are labeled
   EXPLORATORY / NON-CONFIRMATORY; nothing tunes conditions, τ, N, or model set on a peeked
   effect; τ stays UNFROZEN; the pilot does not write into the confirmatory prereg except
   the declared power-N channel (which is PENDING/unmet — that's fine).
9. **Offline tests:** run `pytest -m "not live" tests/test_axis1_pilot.py -q` and report
   pass count. Spot-check that at least the correlation-on-synthetic-known-pattern test
   actually exercises a KNOWN signal (not a tautology).
10. **Merge safety:** confirm `git diff main...feature/axis1-pilot` deletes NO existing
    files (azure_provider.py, DECISIONS.md, handoff docs, prereg) — the branch was stale and
    has been merged with main; verify it is now purely additive + the INTERFACES §8 update.

## Output
For each check: PASS/FAIL, evidence (file:line, reproduced number/command). List any BLOCKER
(leakage, non-determinism, confirmatory claim, deleted file) vs NON-BLOCKING nit. Final line:
**VERDICT: PASS** or **VERDICT: FAIL**. Do NOT modify anything.
