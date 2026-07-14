# PROGRESS.md — Done / Doing / Todo · Known Pitfalls · Preregistration Freeze Log

> Every session updates this before finishing. Manager records each merge here
> (PR / diff summary / audit verdict) for later spot-checks.

## Preregistration freeze log (CRITICAL — never back-fill)
| Item | Value | Frozen-at (UTC) | Set by | Notes |
|---|---|---|---|---|
| τ_disp (axis 1 disagreement threshold) | NOT YET FROZEN | — | — | freeze in feature space BEFORE seeing E1 results |
| τ_level (axis 2 over-reliance threshold) | NOT YET FROZEN | — | — | same |
| BH alpha | 0.05 (proposed) | — | — | ratify before multiple comparisons |

Any post-hoc tuning of a frozen threshold = research misconduct. Log the reason
and timestamp for every change.

## Done
- 2026-07-14: Manager session started. Read v2.4 proposal, AI 分工计划, workflow
  template, manager-prompt. Verified env (copilot/gh authed EloiseJulia/git/
  python3.12; uv absent). Created SPEC.md / INTERFACES.md / PROGRESS.md skeletons.

## Gate status (STEP 0)
- **Gate 1 DATA: CLEARED (independently verified 2026-07-14).** Both raw
  per-trial datasets downloadable & academic-use licensed:
  - Bansal CHI'21: `uw-hai/Complementary-Performance` →
    `experiment-data/decision-result-filter.csv` (HTTP 200, 66,042 rows; cols
    assignmentId/questionId/condition/choice/y/pred/conf). Has UI conditions.
  - Lu&Yin CHI'21: `ZhuoranLu/Trustworthy-ML` →
    `data/expOneFinalPredictionsValid1125.csv` (HTTP 200, 9,031 rows; cols
    workerId/taskId/prediction/finalPrediction/mlCorrect/switch).
  - Manager verified URLs return 200 + real CSV headers (not subagent-claimed).
  - Detail: `docs/research/2026-07-14-dataset-availability.md`.
- **Gate 2 BATCH API: CLEARED for v0.** GitHub Models API via fine-grained PAT
  (good for thin-slice v0). For full-scale E1: verify GitHub Models rate limits
  for tier; Azure AI Foundry = high-throughput fallback. Copilot sub is
  interactive-only, not a batch endpoint.
- **Gate 3 PI: pending explicit acknowledgement.**

## Doing
- STEP 0 nearly done (Gate 3 ack). Proposing dependency map + v0 plan for PI go.

## Todo (post-gate)
- [ ] S0 code scaffold: package `twdf`, config, logging, run_manifest.
- [ ] Thin vertical slice v0 (Module A schema on fake data → B → axis-1
      over-dispersion metric → one correlation number).
- [ ] Modules A / B / C / D / E per §2.1 dependency map.

## Module status (§2.1)
| Module | Status | Blocked on |
|---|---|---|
| S0 architecture | docs skeleton done; code pending | — |
| A data & features | not started | Gate 1 CLEARED — ready |
| B panel engine | not started | Gate 2 CLEARED (v0: GitHub Models API) |
| C metrics & stats | not started (can start on fake data) | A schema |
| D calibration & protocol | not started | B + C |
| E experiments & report | not started | A+B+C+D |

## Known pitfalls (from §6 / §4.5 methodology checklist)
- Train/test LEAKAGE in LOIO (E3): normalization params fit on full data.
- Contamination isolation: run on perturbed data; report cutoff vs release date.
- beta-binomial over-dispersion MUST be separated from binomial noise (not raw var).
- mean-predictor baseline must be genuine (p(1−p)) and actually beaten.
- Difficulty control: E1 main estimator = within-task diff, NOT pooled correlation.
- Two axes must be computed & thresholded SEPARATELY; dark condition must trigger axis 2.
- researcher DoF: freeze τ_disp/τ_level before results (see freeze log above).
- Benjamini–Hochberg correction actually applied when scanning interventions.
- AI hallucinated numbers: trust only re-run raw output.

## Merge log
_(none yet)_
