# impl-renderer-fidelity — correct Bansal condition renderers (PR #10)

You implement in the worktree `.worktrees/renderer-fidelity` (branch
`feature/renderer-fidelity`, DRAFT PR #10). Do NOT touch `main`, do NOT merge, do NOT run
live/networked tests (both GitHub models are daily-capped). Offline work + `pytest -m
"not live"` only. Commit to the branch and push; report findings to the Manager.

## Problem
`src/twdf/data/bansal_tasks.py::render_ui_condition` currently interprets `Conf.+Single` /
`Conf.+Double` / `Conf.+Adaptive` as showing the first 1 / first 2 / all-or-top-3 highlighted
TOKENS in document order, with an adaptive threshold of `conf > 0.8`. This is SEMANTICALLY
WRONG vs Bansal CHI'21 (arXiv:2006.14779). The conditions refer to which LABELS' evidence is
shown, adaptively gated by confidence — NOT a token count. This renderer feeds the CONFIRMATORY
axis-1 cross-condition Spearman rank (H1a secondary), so it must be faithful and is fixed BEFORE
the confirmatory run (prereg §3).

## Verified ground truth (from the paper + Manager's data inspection — treat as authoritative)
Highlight→class mapping: `class1` = POSITIVE-class evidence, `class0` = NEGATIVE-class evidence
(confirmed from data, README wording is imprecise). `pred` ∈ {0,1} is the predicted label; the
"predicted class" spans are `class{pred}`.

Two DISTINCT HTML span formats (both must be parsed):
- `system` field (LIME): UNQUOTED — `<span class=class0>word</span>` (token-level; many spans/class).
- `expert` field: SINGLE-QUOTED — `<span class='class0'>phrase</span>` (one short PHRASE span
  per class, embedded in the full review text). May not always contain both classes.

Adaptive threshold = the classifier's dataset MEDIAN confidence (paper §4.2, verbatim):
Beer = **0.892**, AmzBook = **0.889** (Manager verified Beer median conf = 0.892 exactly on the
50-item stimulus set). Not learned; fixed. Use these fixed values (do NOT recompute from a subset).

Faithful rendering rules:
| Condition | Rule |
|---|---|
| `Conf.` | pred + confidence only. NO highlights. (unchanged) |
| `Conf.+Single` | pred + conf + ALL `system` spans of the PREDICTED class (`class{pred}`) only. Counter-argument (other class) suppressed. |
| `Conf.+Double` | pred + conf + ALL `system` spans of BOTH classes (class0 AND class1). |
| `Conf.+Adaptive` | if `conf >= threshold(domain)` → Single (predicted-class spans); else → Double (both). |
| `Conf.+Adaptive (Expert)` | SAME threshold rule, but on `expert` phrase-spans: if `conf >= threshold` → the predicted-class expert phrase only; else → both expert phrases. |

For adaptive direction: HIGH confidence → Single (predicted class only); LOW confidence → Double
(also show the counter-argument). This matches the paper ("explains predicted class when confident,
alternative otherwise").

## Implementation requirements
1. Add a domain→threshold constant, e.g. `ADAPTIVE_CONF_THRESHOLD = {"beer": 0.892, "amzbook":
   0.889}`. `render_ui_condition` needs the task's `domain` (already on `TaskStimulus.domain`) to
   pick the threshold. If a domain is missing from the map, raise a clear error (do NOT silently
   default) — this is confirmatory-critical.
2. Rewrite `_extract_lime_highlights` (or add a helper) so selection is by CLASS, not by
   document-order token count: given a target set of classes ({class{pred}} for Single; {class0,
   class1} for Double), extract ALL matching spans, preserving document order, rendered as readable
   text with a per-class direction label (as today: class1="supporting positive", class0=
   "supporting negative"). Remove the `n_highlights` / `adaptive`/top-3 heuristics entirely.
3. Add an expert-span extractor that parses the SINGLE-QUOTED `<span class='class[01]'>phrase
   </span>` format from the `expert` field and returns the phrase(s) for the requested class(es).
   Note the loader currently stores `expert_explanation` as cleaned `**bold**` text — you likely
   need access to the RAW expert HTML to know the class of each phrase. If `TaskStimulus` does not
   retain the raw expert HTML with class tags, ADD a field (e.g. `expert_highlights_html`) to
   preserve it (mirroring `system_highlights`), populate it in the loader, and keep
   `expert_explanation` for backward compatibility. Do NOT break existing callers.
4. NO leakage: never put `ground_truth`/`Y` into any rendered output. Only `ai_pred`, `ai_conf`,
   class-filtered highlight spans, and task text may appear. (System-1 prompt is unchanged.)
5. Keep the exact Bansal condition strings. Keep `Conf.` unchanged. Keep any placebo/wrong-AI
   branches that already exist (E4 uses them) working — do not remove them.
6. DETERMINISM: hashlib only; no builtin `hash()`. Rendering must be pure/deterministic.

## Tests (offline, update `tests/test_axis1_pilot.py` and add cases)
- Single shows ONLY predicted-class spans (assert an other-class token is ABSENT; a predicted-class
  token is PRESENT). Flip `pred` and assert the selected class flips.
- Double shows BOTH classes (assert one token of each class present).
- Adaptive: construct/select a high-conf item (conf ≥ 0.892 beer) → identical to Single; a low-conf
  item (conf < 0.892) → identical to Double. Use REAL beer stimuli if available offline (cached
  `data/raw/task-sentiment-beer.json`), else synthetic TaskStimulus fixtures.
- Adaptive (Expert): high-conf → predicted-class expert phrase only; low-conf → both expert phrases;
  parses the single-quoted format.
- Threshold values asserted (beer 0.892, amzbook 0.889); missing-domain raises.
- Determinism/no-leakage tests still pass. Run `pytest -m "not live"` for the whole suite and
  report the pass count; fix any regressions your change causes in other tests.

## Records (same PR)
Append a `docs/DECISIONS.md` entry (next id after D4.8, e.g. **D5.1**): what changed (renderer
token-count → faithful label-explanation semantics + median-conf adaptive threshold), WHY (research
`research-bansal-conditions` with paper quotes; the token-count reading was a misinterpretation),
and the paper implication (confirmatory cross-condition rank now faithful; NOTE that this changes
the rendered prompt for `Conf.+Adaptive (Expert)`, so E4's 193-call cache is INVALIDATED and E4
must re-run fresh on the corrected renderer, and PR#4's exploratory numbers used the old renderer).
Also update `INTERFACES.md` §8 AS-BUILT renderer description and the PR #8 renderer docstrings that
describe the old heuristic. Commit with trailer `Co-authored-by: Copilot <copilot@github.com>`.

## Report back
Summarize: files changed, the new rules as implemented, test pass count, any ambiguity you had to
resolve, and explicitly confirm the E4-cache-invalidation note is logged. Do NOT merge.
