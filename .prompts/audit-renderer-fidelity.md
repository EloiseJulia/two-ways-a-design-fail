# audit-renderer-fidelity — INDEPENDENT hostile + §4.5 audit (PR #10)

You are a FRESH, independent auditor. You did NOT write this code. Try to break the Bansal
condition-renderer fidelity fix. REPORT ONLY; do NOT fix, commit, or merge. Verify from CODE +
offline `pytest -m "not live"` ONLY — do NOT run live/networked tests (both GitHub models are
daily-capped). Evidence = file:line + reproduced numbers/commands. End with **VERDICT: PASS** or
**VERDICT: FAIL**.

## What this PR does
Corrects `src/twdf/data/bansal_tasks.py::render_ui_condition` from a token-COUNT heuristic
(`Single`=first 1 span, `Double`=first 2 spans, `Adaptive`=`conf>0.8`) to FAITHFUL Bansal CHI'21
label-explanation semantics. Authoritative source: arXiv:2006.14779, distilled in
`.prompts/research-bansal-conditions.md` (verbatim paper quotes). Branch `feature/renderer-fidelity`
(draft PR #10), already merged up-to-date with `main`.

## Ground truth to check against (from the paper + Manager's data inspection)
- `class1` = POSITIVE-class evidence; `class0` = NEGATIVE-class evidence. `class{ai_pred}` = the
  predicted-class explanation.
- `Conf.` = pred + conf, NO highlights. `Conf.+Single` = ALL predicted-class (`class{pred}`) LIME
  spans only. `Conf.+Double` = ALL class0 + class1 LIME spans. `Conf.+Adaptive` = if
  `conf >= threshold(domain)` → Single else Double. `Conf.+Adaptive (Expert)` = same threshold on
  the EXPERT phrase-spans.
- Adaptive threshold = fixed dataset median confidence: **beer = 0.892, amzbook = 0.889** (paper
  §4.2; Manager verified beer median conf = 0.892 exactly on the 50-item stimulus set).
- TWO span formats: `system` (LIME) is UNQUOTED `<span class=class0>token</span>`; `expert` is
  SINGLE-QUOTED `<span class='class0'>phrase</span>`. Both must parse.

## Checks (each PASS/FAIL + file:line evidence)
1. **Single = predicted class only:** for `pred=0`, Single shows negative evidence and OMITS
   positive; for `pred=1`, the reverse. Verify in code AND by rendering a REAL beer item (cached
   `data/raw/task-sentiment-beer.json`). Confirm no other-class span leaks in.
2. **Double = both classes.** Verify.
3. **Adaptive threshold correct + direction correct:** uses beer 0.892 / amzbook 0.889; high conf →
   Single, low conf → Double. Missing/unknown domain RAISES (no silent default). Test it.
4. **Adaptive (Expert):** same threshold, parses the SINGLE-QUOTED expert spans (not the cleaned
   `**bold**` text); high conf → predicted-class expert phrase only, low conf → both. Verify the
   raw expert HTML is preserved on `TaskStimulus` (new field) and populated by the loader.
5. **class mapping:** class1=positive, class0=negative in the rendered direction labels. Confirm.
6. **No ground-truth/Y leakage:** no renderer path emits `ground_truth`/`Y`/the correct label.
   The `Wrong-AI (dark)` path shows a FLIPPED pred, not the truth. System-1 prompt unchanged.
7. **Determinism/hygiene:** hashlib only (`Select-String '(?<![\w.])hash\('` on the changed src →
   0 real builtin hash); rendering pure/deterministic.
8. **No regression / backward compat:** the change does not break existing callers
   (`real_panel.py`, `test_panel_real.py`, `test_panel_redesign.py`, `test_axis1_pilot.py`). Run
   `pytest -m "not live" tests/test_axis1_pilot.py tests/test_azure_provider.py
   tests/test_panel_real.py tests/test_panel_redesign.py -q` (the renderer's blast radius) and
   report the pass count. (NOTE: the FULL suite hangs ONLY on network downloads in
   test_bansal_discriminator/decomposition, which do NOT import the renderer — do not treat that
   environmental hang as a failure; if you can, run those with data pre-cached, else skip them.)
9. **Records:** `docs/DECISIONS.md` has a new entry (D5.1) that (a) states the semantics change and
   the fixed thresholds, and (b) explicitly logs that this INVALIDATES E4's 193-call cache
   (Conf.+Adaptive (Expert) prompt changed) so E4 must re-run fresh, and that PR#4 numbers used the
   OLD renderer. `INTERFACES.md` §8 AS-BUILT updated. Confirm.
10. **Merge safety:** `git diff --name-status main...feature/renderer-fidelity` deletes NO existing
    file; purely modifications (bansal_tasks.py, real_panel.py, tests, INTERFACES.md, DECISIONS.md).

## Output
Per-check PASS/FAIL with evidence; BLOCKERs vs nits; reproduce at least the Single/Double/Adaptive
real-data render and the missing-domain raise. Final line: **VERDICT: PASS** or **VERDICT: FAIL**.
Do NOT modify anything.
