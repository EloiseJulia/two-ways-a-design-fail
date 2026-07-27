# E6-stripped — human-validation task (LOCAL PROTOTYPE)

**Status: PILOT-READY prototype (flow/feel + real stimuli).** No server yet. Uses 18 **real** held-out
Bansal beer items (conflict-eligible / ambiguous), multilingual UI (en/zh/ja/de), Latin-square-ish item
rotation, and a **cue-only** dark condition (matched to the synthetic panel).
See the design `../docs/plans/e6-stripped-axis2-design.md` and the **preregistration**
`../docs/plans/2026-07-28-e6-stripped-prereg.md` (target **N≈60**; H1 safe, H2 needs ~60 + purposive
recruiting for trusting-novice spread).

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

- **Faithful / Placebo**: AI shows the model's *real* prediction (`ai_pred`) at its real confidence
  (neutral vs bare "AI-present" framing) — sometimes right, sometimes wrong, as in deployment.
- **Dark**: AI shows a *guaranteed-wrong* label (1−ground_truth) at 92% confidence with coercive authority
  language — **cue-only, matched to the synthetic dark arm** (no fabricated rationale: a probe showed a
  rationale *reduces* synthetic adoption, D5.72). `adopt_wrong_ai=1` when the final decision matches the
  wrong AI advice (the axis-2 human DV).

## Current state & what to finalize before a REAL run
- **Items:** 18 real held-out beer items are embedded (`ITEMS_POOL`), rotated 6-per-interface. **Constraint:**
  the Bansal beer set has only 50 tasks, so the prereg's ~15-per-interface (45 distinct) needs most of the
  set or a second domain — decide before freezing. Items must stay held out from the panel's selection.
- **Trusting-novice index:** the 5 `TN_INDEX` items are a working scale; freeze the final wording/scoring
  with the advisor + IRB.
- **Pre-log predictions:** generate + commit the 4 ladder models' per-interface / per-index predictions
  BEFORE any human data (prereg §6).
- **IRB** (deception + debrief) + a real consent/ethics/withdrawal screen.
- **Hosting + backend:** data currently downloads / sits in localStorage (fine for a labmate pilot where
  each person sends you their JSON); add a small POST endpoint before scaling.
- **Pilot first on non-precious people** (labmates), then spend the one-shot advisor sample once (N≈60).

## Data schema (per trial row, CSV)
`pid, lang, block, condition, item_id, ground_truth, ai_advice, ai_dark, dark_rationale, s1_decision,
s1_conf, s1_rt_ms, final_decision, final_conf, s2_rt_ms, adopt_wrong_ai, switched_from_s1`
