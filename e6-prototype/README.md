# E6-stripped — human-validation task (LOCAL PROTOTYPE)

**Status: prototype for flow/feel only.** No server, no real data, placeholder stimuli.
See the frozen design in `../docs/plans/e6-stripped-axis2-design.md`.

## Run it
Just **double-click `index.html`** (opens in your browser, works offline). Or, for a clean URL:

```powershell
cd e6-prototype
python -m http.server 8000
# then open http://localhost:8000
```

## What it does
Consent → instructions → 3 interface blocks (**Faithful / Placebo / Dark**, order randomized per
participant) → per trial: Step-1 no-AI judgment + confidence, then Step-2 AI advice + framing + final
judgment + confidence (reaction times logged) → trusting-novice questionnaire + background → debrief →
**Download JSON / CSV** (also auto-saved to the browser's localStorage).

- **Faithful / Placebo**: AI shows the *correct* label (neutral vs bare "AI-present" framing).
- **Dark**: AI shows a *guaranteed-wrong* label at 92% confidence with coercive authority language —
  byte-identical in spirit to the synthetic dark arm. `adopt_wrong_ai=1` when the final decision matches
  the wrong AI advice (the axis-2 human DV).

## Before any REAL run (must replace the placeholders)
1. Freeze the domain + the **~15 held-out Bansal items per interface** (leakage firewall — items must NOT
   overlap the panel's item selection). Edit `ITEMS` and `CONFIG.itemsPerBlock`.
2. Freeze the **trusting-novice index** wording/scoring. Edit `TN_INDEX`.
3. Pre-generate + **log the 4 ladder models' per-interface / per-persona predictions BEFORE** collecting
   any human data (pre-registered predictions).
4. **IRB approval** (deception + debrief) and a real consent/ethics/withdrawal screen.
5. Decide hosting + a data backend (right now data only downloads / sits in localStorage — fine for a
   pilot where each volunteer sends you their JSON, but a small POST endpoint is better at scale).

## Data schema (per trial row, CSV)
`pid, block, condition, item_id, ground_truth, ai_advice, ai_dark, s1_decision, s1_conf, s1_rt_ms,
final_decision, final_conf, s2_rt_ms, adopt_wrong_ai, switched_from_s1`
