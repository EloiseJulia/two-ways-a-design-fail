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

## Doing
- STEP 0: surfacing the THREE GATES to the PI (blocking all data-pipeline work).

## Todo (blocked on gates / PI go)
- [ ] Gate 1 DATA: confirm Bansal CHI'21 + Lu&Yin CHI'21 raw per-trial data
      obtainable (downloadable CSV/logs). Until cleared: NO data pipeline.
- [ ] Gate 2 BATCH API: confirm a programmable endpoint callable in a Python
      for-loop 10k+ times. Until cleared: NO panel inference loop.
- [ ] Gate 3 PI: PI owns scientific correctness (acknowledge).
- [ ] (allowed pre-gate) research subagent: dataset availability + batch-API
      options + license — must NEVER fabricate links.
- [ ] S0 code scaffold: package `twdf`, config, logging, run_manifest.
- [ ] Thin vertical slice v0 (Module A schema on fake data → B → axis-1
      over-dispersion metric → one correlation number).
- [ ] Modules A / B / C / D / E per §2.1 dependency map.

## Module status (§2.1)
| Module | Status | Blocked on |
|---|---|---|
| S0 architecture | docs skeleton done; code pending | — |
| A data & features | not started | Gate 1 |
| B panel engine | not started | Gate 2 |
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
