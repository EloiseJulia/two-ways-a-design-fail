# impl-confirmatory-axis1-pipeline — pre-specified H1a analysis (PR #12, BLIND)

Implement in the worktree `.worktrees\confirmatory-axis1-pipeline` (branch
`feature/confirmatory-axis1-pipeline`, DRAFT PR #12). Do NOT touch `main`, do NOT merge, do NOT run
live/networked tests (quota is scarce; both GitHub models are daily-capped). Offline work +
`pytest -m "not live"` only. Commit + push to the branch; report to the Manager.

## Purpose (rigor: build BLIND, before any confirmatory panel data)
Implement the FULL pre-registered confirmatory axis-1 (H1a) analysis as a pure, testable pipeline.
Building the analysis code before the panel data exists is the point (preregistration discipline —
it cannot bias the result). Source of truth: `docs/plans/preregistration-axis1.md` (§§1–8) and
`SPEC.md` (§2 positioning D5.4, §3 H1a, §6 triage, §8 stats). Do NOT change the prereg or H1a.

## Design: separate ANALYSIS (pure, tested) from the RUN (panel calls, NOT executed here)
1. **Pure analysis module** `src/twdf/analysis/confirmatory_axis1.py` — input = panel responses
   (a list of per-cell records: persona_id, model, task_id, ui_condition, seed, system1_decision,
   final_decision, ai_advice, relied, plus task difficulty/AI-correctness metadata) + the fixed
   human target path. Output = a `ConfirmatoryAxis1Result` dataclass (JSON-serializable `to_dict`).
   THIS is what your offline tests exercise on SYNTHETIC panel data with KNOWN structure.
2. **Thin runner** `src/twdf/experiments/confirmatory_axis1.py` + `configs/confirmatory_axis1.yaml`
   — reuse the EXISTING multi-provider panel loop (see `src/twdf/experiments/axis1_pilot.py` and
   `src/twdf/panel/real_panel.py`) to produce responses, then call the analysis module. The runner's
   API-calling path must be OFFLINE-TESTABLE with a mock provider (no real network in tests). DO NOT
   run it live. Config model set = `{openai/gpt-4o, openai/gpt-4.1-mini}` (the amended stable set,
   prereg §2 amendment), day-batched; faithful renderer is automatic (already on main).

## Analysis requirements (REUSE existing helpers in `src/twdf/metrics/overdispersion.py`)
Reuse, do NOT reimplement: `conflict_conditioned_reliance`, `betabinom_overdispersion` /
`betabinom_overdispersion_within_domain`, `baseline_mean_predictor`, `within_task_diff`,
`paired_permutation_test`, `bootstrap_ci`, `condition_correlation`. Reuse
`twdf.analysis.panel_human_correspondence.panel_human_condition_correspondence` (merged in PR #11)
for the cross-condition Spearman vs the human target.

Compute, per prereg:
1. **Primary DV:** conflict-conditioned reliance (System-1 ≠ AI trials). Report unconditional too.
2. **Axis-1 target:** between-user beta-binomial OVER-DISPERSION on the conflict DV (excess over
   binomial p(1−p) — NEVER raw variance).
3. **Panel disagreement per condition:** variance of per-(persona×model) conflict-conditioned
   reliance, per condition (align with `axis1_pilot`'s definition).
4. **Primary estimator:** difficulty-controlled **within-task counterfactual difference** (within
   pair; difficulty cancels) via `within_task_diff`. **Secondary:** cross-condition Spearman (panel
   disagreement vs HUMAN over-dispersion) via the PR #11 module (n<3 guard + ceiling flag included).
5. **Baselines that must be BEATEN (prereg §5):** `random`, `mean-predictor` (already exists;
   outputs p(1−p), ρ=0 by construction), `prompt-only` (single prompt, no persona panel),
   `single-model` (one model, no cross-model panel), plus a **rational-Bayesian null** (the
   appropriate-reliance anchor). Implement the missing baselines as clearly-documented functions;
   the confirmatory signal must exceed all of them with a bootstrap CI that EXCLUDES the baseline.
6. **Statistics (prereg §6/§8):** bootstrap over (personas × seeds × models) for CIs; permutation
   test for the disagreement→over-dispersion relationship; **Benjamini–Hochberg** correction across
   the reported hypotheses at **α = 0.05**; report effect sizes + CIs.
7. **PER-MODEL reporting (model-mix confound):** compute + report axis-1 results per model; DO NOT
   pool over incomparable models (gpt-4o vs gpt-4.1-mini). Provide a cross-model agreement summary
   but keep primary numbers per-model.
8. **τ stays UNFROZEN:** this run TESTS H1a; it does NOT set τ_disp/τ_level. No thresholding here.
9. **No leakage:** item selection / analysis uses AI-side EXOGENOUS properties only (AI-wrong /
   low-conf / human-reliance-variance for LOCATING items); human outcomes NEVER enter agent prompts
   or serve as a predictor. Deterministic (fixed seeds); hashlib only; no builtin `hash()`.
10. **Reporting commitment:** the result object reports the outcome REGARDLESS of direction (a null
    or wrong-signed result is a valid, fully-populated result, not an error).

## Result schema (`ConfirmatoryAxis1Result.to_dict`)
Include: per-model {conflict-conditioned over-dispersion + CI, within-task estimator + CI +
permutation p, cross-condition correspondence (from PR #11), baseline comparisons (each baseline
value + whether beaten + CI), BH-adjusted p-values}, the aligned per-condition table, a
cross-model-agreement summary, n (personas/items/models/conditions/seeds), and an
`exploratory_vs_confirmatory: "CONFIRMATORY"` label. JSON-serializable.

## Tests (offline) `tests/test_confirmatory_axis1.py`
- **Known-signal synthetic panel:** construct panel responses where conflict-conditioned reliance
  over-dispersion is engineered to be REAL and panel disagreement rank-tracks a known target →
  assert over-dispersion CI excludes 0, within-task estimator is positive, correspondence ρ>0
  significant, and the signal BEATS every baseline (random/mean-predictor/prompt-only/single-model/
  rational-Bayes).
- **Null synthetic panel:** no real over-dispersion / no disagreement structure → assert the result
  is a clean NULL (CI includes 0; does not beat mean-predictor) and is still fully populated
  (reporting-regardless).
- **Mean-predictor sanity:** mean-predictor baseline ρ ≈ 0 by construction.
- **Per-model separation:** two models with different signals are reported separately, not pooled.
- **BH correction** applied across the hypothesis set (check adjusted p ≥ raw p).
- **Determinism:** same inputs+seed → identical `to_dict()`.
- **Mock-provider runner smoke test:** the runner produces responses via a MockProvider and feeds
  the analysis end-to-end offline (System-1 frozen across conditions; no network).
- Run `pytest -m "not live"` for the new tests + the reused-metric tests; report pass count; fix any
  regression your changes cause.

## Records (same PR)
- `docs/DECISIONS.md`: entry after D5.4 (e.g. **D5.5**) — pre-specified confirmatory analysis
  pipeline implemented BLIND; reuses PR #11 correspondence + existing metrics; adds the 4 baselines +
  rational-Bayes null + BH + per-model reporting; does NOT change H1a/prereg; τ stays unfrozen.
- `INTERFACES.md` §8 AS-BUILT: new analysis module + runner + config + result schema + reused fns.
- Commit with trailer `Co-authored-by: Copilot <copilot@github.com>`.

## Report back
Files changed, the analysis/result shape, which baselines you added vs reused, the full
`pytest -m "not live"` pass count, and any ambiguity resolved. Do NOT merge.
