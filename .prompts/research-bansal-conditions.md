# research-bansal-conditions — verify Bansal CHI'21 explanation-condition semantics

Doc-only research. NO code changes. Goal: determine, with EXACT citations, what each Bansal
explanation UI condition means, so our panel can render them FAITHFULLY for the confirmatory
axis-1 run. Report findings + quotes + source locations only.

## Why this matters
Our 5-condition panel renderer (`src/twdf/data/bansal_tasks.py:render_ui_condition`) currently
interprets `Conf.+Single` / `Conf.+Double` / `Conf.+Adaptive` as showing the first 1 / first 2 /
all-or-top-3 highlighted TOKENS (in document order) from the LIME `system` HTML. We SUSPECT this
is a semantic misinterpretation: in Bansal CHI'21 these conditions likely refer to top-1 / top-2 /
confidence-adaptive LABEL explanations, not a count of highlighted tokens. The confirmatory
cross-condition Spearman rank (H1a secondary) depends on rendering these faithfully, so we must
verify before changing renderers.

## Authoritative sources
- Paper: Bansal, Wu, Zhou, Fok, Nushi, Kamar, Ribeiro, Weld. "Does the Whole Exceed Its Parts?
  The Effect of AI Explanations on Complementary Team Performance." CHI '21.
  arXiv: https://arxiv.org/pdf/2006.14779.pdf (also https://arxiv.org/abs/2006.14779).
- Data repo: https://github.com/uw-hai/Complementary-Performance
  - `README.md` (data formats: `system` = LIME highlights, `<span class=class0|class1>` = neg/pos
    class; `expert` = expert-annotated highlights, same span format).
  - `experiment-data/decision-result-filter.csv` condition column values (VERIFIED by Manager):
    `Conf.`, `Conf.+Single`, `Conf.+Double`, `Conf.+Adaptive`, `Conf.+Adaptive (Expert)`, `Human`.
  - `task-examples/task-sentiment-beer.json` (fields: testid, X, Y, pred, conf, expert, system).

## Questions to answer (each with an EXACT quote + section/figure/page)
1. **Exact definition of each condition** as used in the paper's study:
   - `Conf.` (confidence only) — what exactly is shown?
   - `Conf.+Single` — is it the explanation of the TOP-1 (predicted) label only?
   - `Conf.+Double` — is it explanations of the TOP-2 labels (for binary Beer/AmzBook = both
     classes)? Confirm what "top-2" means for a binary task.
   - `Conf.+Adaptive` — the EXACT rule that decides whether Single or Double is shown. Is it a
     confidence THRESHOLD? What threshold / policy (quote it)? Does "adaptive" pick top-1 when
     confident and top-2 when uncertain, or the reverse?
   - `Conf.+Adaptive (Expert)` — same adaptive policy but using EXPERT explanations (the `expert`
     field) instead of LIME (`system`)? Confirm.
2. **Highlight→class mapping:** confirm `class1` = positive-class evidence, `class0` = negative-class
   evidence, and that "the explanation for label L" = the spans whose class corresponds to L. State
   how a "top-1 explanation" selects spans (all spans of the predicted class? a ranked subset?).
   Is there ANY notion of highlight ranking/weight/intensity, or are highlights unweighted binary
   spans? (Manager already checked the beer JSON: spans carry ONLY class0/class1, no weights —
   confirm the paper does not imply a hidden ranking.)
3. **What the human actually saw per condition** (any figure showing the UI — cite figure number).
   Note whether confidence is shown numerically or as a bar, and whether the predicted label is shown.
4. **Adaptive threshold source:** if the paper cites a specific confidence cutoff for adaptive
   (e.g., a learned or fixed threshold), quote it and the value. If none is given precisely, say so
   explicitly (we then document our choice as a researcher DoF).
5. **LSAT differences** (brief): LSAT stimuli use choices/explanations, not class0/class1 spans —
   note how conditions map there, but our confirmatory is beer-domain primary, so keep this short.

## Deliverable
A concise findings report:
- A table: condition → faithful rendering rule → exact supporting quote (section/fig/page).
- A clear statement of whether our current token-count interpretation is WRONG, and the corrected
  rule for each condition.
- The adaptive policy + threshold (or an explicit "not specified in the paper" with the closest
  guidance).
- Any residual ambiguity we must resolve as a documented researcher DoF.
Cite everything (URL + section/figure/page or repo file:line). Do NOT edit any repo file.
