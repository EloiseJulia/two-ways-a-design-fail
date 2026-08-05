# Human study — runnable jsPsych experiment

Single public-link, bilingual (English/中文) implementation of the axis-2 human validation. Review text
stays English; participants choose UI language on the first screen.

## Local run

```powershell
cd study\experiment
python -m http.server 8765 --bind 127.0.0.1
```

- Normal local run: `http://127.0.0.1:8765/index.html?domain=beer`
- Team inspection: `...?domain=beer&debug=1&rotation=0`
- `debug=1` reveals condition labels, groups the inspectable order, and retains CSV download. Never field it.

## Production Prolific links

Use two quota-balanced Prolific studies/links to net approximately 40/domain:

```text
.../index.html?domain=beer&PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}&completion=https%3A%2F%2Fapp.prolific.com%2Fsubmissions%2Fcomplete%3Fcc%3DXXXX

.../index.html?domain=amzbook&PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}&completion=https%3A%2F%2Fapp.prolific.com%2Fsubmissions%2Fcomplete%3Fcc%3DXXXX
```

Participant ID deterministically assigns Latin rotation 0/1/2. The 12 main item-condition mappings are
Latin-balanced; display order is randomized. Three non-overlapping `dark+directive` trials follow as a
fixed exploratory escalation block.

## Design

- Main block: 4 neutral / 4 placebo / 4 static dark; all show guaranteed-wrong advice at fixed 92%.
- Escalation: 3 trailing dark+agreement-contingent-directive trials, excluded from H1/H2.
- Single-page two-stage trial: active initial P/N + 1–5 stars → AI reveal → symmetric prefill of initial
  answer + active confidence rerating → final submit.
- Main DV: `flipped_to_wrong` among `initial_correct=1` main trials.
- No attention/comprehension gate or RT exclusion, per owner decision; RT is passively recorded.

## Data capture

`index.html` includes:

- Prolific parameter capture;
- DataPipe→OSF save;
- completion redirect;
- post-debrief withdrawal;
- debug-only local CSV.

**Before fielding, replace:**

```js
const DATAPIPE_ID = 'REPLACE_WITH_DATAPIPE_ID';
```

Also replace researcher/ethics placeholders in consent/debrief and `XXXX` in the Prolific completion URL.
Run at least three end-to-end dummy submissions and verify complete CSVs in OSF, withdrawal handling, and
completion redirects.

## Files

- `index.html` — experiment, i18n, Prolific/DataPipe hooks.
- `stimuli.js` — browser bundle (`window.STIMULI`).
- `build_stimuli_js.py` — rebuild after `../export_stimuli.py`.

## Remaining launch requirements

- [ ] DataPipe experiment ID + verified OSF writes.
- [ ] Prolific completion code and two domain quotas.
- [ ] Researcher/ethics details and approval.
- [ ] Content-warning scan.
- [ ] Internal end-to-end timing/coding dry run.
- [ ] OSF preregistration frozen before recruitment.
