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
- 2026-07-14: **VSLICE-V0 IMPLEMENTATION (feature/vslice-v0 branch)**
  - S0 scaffold: Package `twdf` v0.1.0, pyproject.toml, src/ structure, configs/, tests/
  - Module A (data): Bansal CHI'21 loader with canonical schema mapping. UI pair selected:
    **Human vs Conf.+Adaptive** (rationale: no-AI baseline vs core intervention).
  - Module C (metrics): **Rigorous beta-binomial over-dispersion estimator** (MLE fit,
    separates true heterogeneity from binomial noise), mean-predictor baseline (rho=0
    by construction), within-task diff, bootstrap CI. **CRITICAL TESTS PASS**:
    pure binomial->~0 rho, high/low split->positive rho, beats baseline.
  - Module B (stub): Synthetic panel stub (deterministic seeded generator, NOT real LLM).
  - Module E (experiment): E1 v0 runner end-to-end. **REAL RUN COMPLETED**:
    * Human condition: rho=0.0369 [95% CI: 0.0087, 0.0681], n=283 users, 2340 trials
    * Conf.+Adaptive: rho≈0.0000 (essentially no over-dispersion), n=292 users, 2415 trials
    * Panel disagreement (synthetic): Human=0.008, Conf.+Adaptive=0.163
    * **Correlation (panel disagreement vs human over-dispersion): r = -1.0000**
      (note: unexpected negative - Conf.+Adaptive shows convergent high reliance with
      zero over-dispersion in real data, flagging axis-2 systematic behavior, not axis-1)
    * Mean-predictor baseline: Human condition BEATS baseline (0.0369 > 0.0000).
  - Tests: 6/6 metrics tests PASS (incl. 3 critical beta-binomial tests), pytest clean.
  - Results: `results/e1_vslice_v0.json` with run_manifest (config hash, seeds, timestamp).
  - Deliverable: Installable package (`pip install -e .`), runnable CLI, tests pass,
    end-to-end chain proven. Ready for hostile methodology audit.
  - **⚠️ CRITICAL DISCLOSURE (post-audit)**: The correlation r=-1.0000 is computed over 
    only 2 UI conditions (n=2 data points: Human, Conf.+Adaptive). This is a DEGENERATE 
    correlation - any 2 non-identical points give r=±1.0 by mathematical necessity. This 
    number has NO STATISTICAL MEANING and is NOT evidence of any relationship. It is 
    included ONLY as a v0 plumbing check that the chain executes. Real evaluation 
    requires n≥3 (ideally n≥5) UI conditions. The code now explicitly flags this and 
    includes the warning in the output JSON.
  - **TODO (post-v0)**: Replace print() statements with proper logging (logging.info/debug)
    for cleaner production console output.

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
- **Gate 3 PI: CLEARED (2026-07-14).** PI owns final scientific correctness; no
  result merges on "it runs" alone; independent hostile + §4.5 methodology audit
  is the merge gate; τ_disp/τ_level frozen with timestamp before any results.

## Doing
- (empty - v0 slice complete)

## Todo (post-gate)
- [x] S0 code scaffold: package `twdf`, config, logging, run_manifest.
- [x] Thin vertical slice v0 (Module A schema on real data → B stub → axis-1
      over-dispersion metric → one correlation number). **COMPLETE: r=-1.0 obtained.**
- [ ] Real panel engine (Module B) — replace stub with LLM-based personas + counterfactual pairing.
- [ ] Modules D (calibration/threshold freezing) + full E1/E2/E3/E4/E5/E6 experiments.

## Module status (§2.1)
| Module | Status | Blocked on |
|---|---|---|
| S0 architecture | ✅ DONE (v0.1.0, pyproject.toml, src/ structure) | — |
| A data & features | ✅ DONE (Bansal loader, canonical schema, Human vs Conf.+Adaptive) | — |
| B panel engine | ⚠️ STUB ONLY (synthetic generator; real LLM panel deferred) | Gate 2 (scaled for E1 full) |
| C metrics & stats | ✅ DONE (beta-binomial over-dispersion, baselines, tests PASS) | — |
| D calibration & protocol | 🔲 NOT STARTED (threshold freezing deferred post-v0) | C+B |
| E experiments & report | ✅ DONE (E1 v0 end-to-end, correlation number obtained) | A+B+C |

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
- **2026-07-14 — PR #1 `vslice-v0` SQUASH-MERGED to main (commit e5a257b).**
  - Flow: impl-vslice-v0 → audit-vslice-v0 (FAIL: B1 degenerate n=2 corr, B2
    non-reproducible panel values, B3 test import) → fix-vslice-v0 → reaudit-
    vslice-v0 (**PASS**). Merge executed by Manager per policy.
  - B2 root cause: Python builtin `hash()` non-deterministic across processes →
    replaced with `hashlib.md5`; task iteration sorted. Re-audit independently
    confirmed byte-identical output across 3 separate-process runs.
  - Reproduced committed numbers: panel disagreement Human=0.008,
    Conf.+Adaptive=0.037; Human over-dispersion ρ=0.03691 [CI 0.0087, 0.0681]
    beats mean-predictor (ρ=0); Conf.+Adaptive ρ≈0 (axis-2 pattern). Correlation
    flagged `degenerate:true` (n=2, plumbing-only, NOT evidence).
  - Core beta-binomial estimator independently re-verified correct (pure
    binomial→~0, over-dispersed→>0, beats baseline).
  - **Post-merge TODO (re-audit MINOR-1):** `test_panel_stub_determinism` runs
    the stub twice in ONE process, so it would NOT by itself catch cross-process
    hash-seed nondeterminism. Enhance it to spawn a subprocess (or document the
    limitation). Cross-process reproducibility currently proven only by manual
    3-run audit, not by an automated regression test.
