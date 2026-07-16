# impl-ui-atomic-features — §4.3 UIFeatureVector (PR #13)

Implement in the worktree `.worktrees\ui-atomic-features` (branch `feature/ui-atomic-features`,
DRAFT PR #13). Do NOT touch `main`, do NOT merge. Offline only + `pytest -m "not live"`. Commit +
push to the branch; report to the Manager.

## Purpose (SPEC §4.3 + §6)
Decompose each UI condition into an ATOMIC cognitive-interaction FEATURE VECTOR, so that the dual
thresholds τ_disp/τ_level are LATER learned in a low-dimensional, interpretable FEATURE SPACE (Module
D) and OOD distance is computed in feature space, not on the whole-UI surface. **This PR does NOT
freeze or learn τ** — it only builds the feature representation + a feature-space distance. Read
`SPEC.md` §4 (Atomic feature representation), §5 (E5 uses feature-distance), §6 (dual-threshold
protocol), and `src/twdf/data/bansal_tasks.py::render_ui_condition` (the 7 conditions + faithful
semantics after D5.1).

## What to build
`src/twdf/features/ui_features.py` (new `features/` package) with:
1. `@dataclass(frozen=True) UIFeatureVector` — atomic, interpretable, DETERMINISTIC features derived
   from `(task, ui_condition)` via the renderer output + condition semantics. Suggested fields (use
   judgment; keep each atomic + documented):
   - `has_explanation: bool`
   - `explanation_source: str`  # "none" | "lime" | "expert" | "placebo"
   - `explanation_faithfulness: float`  # 1.0 real (lime/expert), 0.0 placebo, and none→0.0 (+ a
     separate `has_explanation` so none vs placebo are distinguishable)
   - `n_highlight_spans: int`  # info density (count of rendered highlight spans; 0 for none/placebo)
   - `info_density: float`  # n_highlight_spans normalized by task length (salience proxy)
   - `shows_predicted_class_only: bool`  # Single or high-conf Adaptive
   - `shows_both_classes: bool`          # Double or low-conf Adaptive
   - `is_adaptive: bool`
   - `confidence_shown: bool`, `confidence_value: float`  # note Wrong-AI shows a pseudo value
   - `authority_cue: bool`  # dark/coercive framing present (Wrong-AI condition)
   - `wrong_ai: bool`       # AI advice deliberately flipped (dark)
   - `explanation_char_len: int`
   Derive these by RENDERING the condition (call `render_ui_condition`) and/or from the condition
   name + task fields — do NOT hard-code per-condition vectors; compute them. NO ground-truth/Y in
   any feature (no leakage). Handle all 7 conditions: `Conf.`, `Conf.+Single`, `Conf.+Double`,
   `Conf.+Adaptive`, `Conf.+Adaptive (Expert)`, `Conf.+Placebo`, `Wrong-AI (dark)`.
2. `extract_ui_features(task: TaskStimulus, ui_condition: str) -> UIFeatureVector`.
3. `feature_vector_to_array(v) -> np.ndarray` + an ordered `FEATURE_NAMES` (stable order) so the
   space is usable for calibration/OOD distance later.
4. `feature_distance(a: UIFeatureVector, b: UIFeatureVector, *, weights=None) -> float` — a
   documented distance (e.g. standardized/weighted Euclidean over the numeric encoding) usable as
   the OOD distance in SPEC §5/§6. Keep it simple + deterministic.
5. `to_dict()` on the dataclass (JSON-serializable).

## Constraints
- Deterministic + pure; hashlib only if hashing; no builtin `hash(`. No network (may render real
  cached beer stimuli offline from `data/raw/task-sentiment-beer.json` if helpful, else synthetic
  TaskStimulus fixtures).
- NO leakage: features must be computable from what the USER/agent SEES (pred, conf, explanation,
  framing) — never from `ground_truth`. `wrong_ai` is a DESIGN property (the condition flips advice),
  not the truth label, so it's allowed as a design feature.
- Do NOT learn/freeze τ; do NOT modify the renderer or other existing modules.

## Tests `tests/test_ui_features.py`
- Each of the 7 conditions maps to a DISTINCT, correct vector: `Conf.`→no explanation; Single→
  predicted-class-only, n_highlight_spans>0; Double→both classes; Adaptive→is_adaptive with
  Single-or-Double behavior by confidence threshold (beer 0.892); Expert→explanation_source="expert";
  Placebo→has_explanation=True, explanation_source="placebo", faithfulness=0.0, n_highlight_spans=0;
  Wrong-AI→authority_cue=True, wrong_ai=True.
- No `ground_truth` influence: two tasks identical except `ground_truth` produce identical vectors.
- `feature_distance` is 0 for identical, >0 for different, symmetric; placebo is closer to Expert
  than `Conf.` is to Expert on the explanation-presence axis (or a similar sanity relation you can
  justify).
- Determinism: same inputs → identical `to_dict()`.
- Run `pytest -m "not live" tests/test_ui_features.py -q`; report pass count.

## Records (same PR)
- `docs/DECISIONS.md`: entry **D5.6** (note D5.5 is on the confirmatory branch, not yet on main —
  use D5.6 and mention the ordering) — built the §4.3 atomic feature space for later Module D τ
  calibration; does NOT freeze τ; enables feature-space OOD distance (SPEC §5/§6).
- `INTERFACES.md` §8 AS-BUILT: new `twdf.features.ui_features` module + signatures + FEATURE_NAMES.
- Commit with trailer `Co-authored-by: Copilot <copilot@github.com>`.

## Report back
Files changed, the final feature list, test pass count, any ambiguity resolved. Do NOT merge.
