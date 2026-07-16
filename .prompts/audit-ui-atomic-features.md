# audit-ui-atomic-features — INDEPENDENT audit (PR #13)

Fresh independent auditor. REPORT ONLY; no fix/commit/merge. Offline `pytest -m "not live"` only.
Evidence = file:line + reproduced values. End with **VERDICT: PASS** or **VERDICT: FAIL**.

## What this PR does
Adds `src/twdf/features/ui_features.py` — the §4.3 atomic UI feature space (`UIFeatureVector`,
`extract_ui_features`, `FEATURE_NAMES`, `feature_vector_to_array`, `feature_distance`) for the 7
rendered conditions. This is the space where τ is LATER learned (Module D); this PR must NOT learn or
freeze τ. Branch `feature/ui-atomic-features` (draft PR #13), merged up to date with main.

## Checks (PASS/FAIL + evidence)
1. **All 7 conditions → correct, distinct vectors** (render real cached beer stimulus
   `data/raw/task-sentiment-beer.json`): `Conf.`→no explanation; `Conf.+Single`→lime, predicted-class
   spans only, both_classes=False; `Conf.+Double`→both classes True; `Conf.+Adaptive`→Single-or-Double
   by conf vs 0.892; `Conf.+Adaptive (Expert)`→source=expert; `Conf.+Placebo`→has_explanation=True,
   source=placebo, faithfulness=0, n_highlight_spans=0; `Wrong-AI (dark)`→authority_cue=True,
   wrong_ai=True. Reproduce a dump.
2. **NO leakage:** two tasks identical except `ground_truth` → IDENTICAL vectors
   (`feature_vector_to_array` equal). No feature reads `ground_truth`. Reproduce.
3. **`feature_distance`:** 0 for identical, >0 for different, symmetric; a defensible sanity relation
   holds (e.g. placebo↔expert closer than Conf.↔expert on explanation presence). Deterministic.
4. **Determinism + hygiene:** same inputs → identical `to_dict()`; hashlib only / no builtin `hash(`;
   pure (no time/random/network).
5. **Does NOT freeze/learn τ**; does not modify the renderer or other existing modules.
6. **Faithful to the renderer:** feature derivation matches `render_ui_condition` semantics after D5.1
   (e.g. adaptive threshold beer 0.892; predicted class = `class{ai_pred}`).
7. **Tests meaningful:** `pytest -m "not live" tests/test_ui_features.py -q` pass count; tests aren't
   tautological.
8. **Merge safety:** `git diff --name-status main...feature/ui-atomic-features` is additive (new
   module + __init__ + test) + doc edits; deletes NOTHING (esp. NOT the PR #12 confirmatory files).
9. **Records:** `docs/DECISIONS.md` D5.6 + `INTERFACES.md` §8 present and correct.

Final line: **VERDICT: PASS** or **VERDICT: FAIL**.
