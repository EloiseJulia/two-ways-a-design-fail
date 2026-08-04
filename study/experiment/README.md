# Human study — runnable experiment (jsPsych)

Single-page bilingual (EN/中文) implementation of the axis-2 coercion validation. The review text stays
English; all UI/instructions/AI-framing/directive/debrief are localized.

## Run locally
```powershell
# from study/experiment/
python -m http.server 8765 --bind 127.0.0.1
# then open http://127.0.0.1:8765/index.html
```
(Opening `index.html` via file:// also works; a server avoids any browser quirks.)

## Files
- `index.html` — the whole experiment (timeline, i18n strings, styling).
- `stimuli.js` — generated data (`window.STIMULI`); rebuild with `python build_stimuli_js.py`
  after re-running `../export_stimuli.py`. Bump the `?v=N` on the `<script src="stimuli.js">` tag if a
  browser caches an old copy.
- `build_stimuli_js.py` — bundles `../stimuli/stimuli_{beer,amzbook}.json` into `stimuli.js`.

## Design (as fielded)
- Between-subjects **domain** (beer / amzbook), randomized per session.
- Within-subject **framing**: 12 items, 4 each of **neutral / placebo / dark**, order **shuffled**, no
  condition labels shown. AI advice is guaranteed-wrong on every trial; only framing varies.
- Single-page two-stage per item: initial judgment + confidence → submit reveals the AI panel → (dark only)
  an agreement-contingent directive pops up → keep/revise → final submit.
- Records per trial: `initial, conf_initial, rt_initial, final, conf_final, rt_final, adopted_wrong,
  changed, conf_change, directive_shown, directive_type`.

## `?debug=1` (team inspection only — NOT for participants)
Adds a `[condition]` label to each trial and fixes a dark-first order so the dark directive is visible
immediately. **Never field with this flag**: it reveals the manipulation and removes randomization.

## Before fielding (TODO — not yet implemented)
- [ ] **Automatic data capture.** Currently data is only saved via the debrief "Download" button. Wire
      jsPsych DataPipe → OSF (or a backend) so every submission is stored server-side.
- [ ] **Prolific integration.** Capture `PROLIFIC_PID` / `STUDY_ID` / `SESSION_ID` from the URL; redirect to
      the Prolific completion URL at the end.
- [ ] **Domain balancing.** Replace per-session random domain with a balanced assignment (~40 beer / 40 amzbook).
- [ ] **Approvals.** IRB approval + OSF preregistration timestamped before recruitment (see
      `../PREREGISTRATION.md`).
- [ ] **Verify label semantics** (POSITIVE=1 / NEGATIVE=0) against the Bansal CHI'21 codebook.
- [ ] **Pilot n≈12** to confirm ≤10 min and the manipulation-check gate (neutral adoption ≥ 0.15).
