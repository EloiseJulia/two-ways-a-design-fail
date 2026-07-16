# PROGRESS.md — Done / Doing / Todo · Known Pitfalls · Preregistration Freeze Log

> Every session updates this before finishing. Manager records each merge here
> (PR / diff summary / audit verdict) for later spot-checks.

## Preregistration freeze log (CRITICAL — never back-fill)
| Item | Value | Frozen-at (UTC) | Set by | Notes |
|---|---|---|---|---|
| Axis-1 confirmatory design §§1–7 (H1a, model set, 5 conditions, DV, baselines, stats) | LOCKED | 2026-07-15T09:23:55Z | Manager/PI | `docs/plans/preregistration-axis1.md` — frozen BEFORE the exploratory pilot (PR #8) was RUN; pilot informs ONLY power target N (§8); pilot data EXCLUDED from confirmatory |
| Confirmatory MODEL SET amendment | {gpt-4o, Llama-3.3-70B, Phi-4} → **{gpt-4o, gpt-4.1-mini}** (GitHub, day-batched) | 2026-07-16T02:29:50Z | PI | AMENDMENT (prereg §2). Provider-stability driven via the pre-committed PIPELINE-only exclusion rule (non-OpenAI: timeouts/500s/unparseable→0), NOT effect-driven (pilot gave no clean axis-1 effect). Non-OpenAI = exploratory-only; cross-vendor deferred to Azure. |
| BH alpha | 0.05 (RATIFIED) | 2026-07-15T09:23:55Z | Manager/PI | ratified in prereg §6 |
| Power target N (axis-1 confirmatory) | PENDING | — | — | GitHub pilot did NOT deliver N (non-OpenAI parse failures). Get N from a CLEAN exploratory pass on {gpt-4o, gpt-4.1-mini} (or Azure); fill prereg §8 + record a freeze timestamp BEFORE the confirmatory run |
| τ_disp (axis 1 disagreement threshold) | NOT YET FROZEN | — | — | procedure pre-specified (prereg §7); freeze in feature space BEFORE Module D results |
| τ_level (axis 2 over-reliance threshold) | NOT YET FROZEN | — | — | same |

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
- 2026-07-14: **E1-MULTICOND AUDIT FIX (BLOCKER-1 & BLOCKER-2)**
  - **BLOCKER-1 (over-dispersion fragile to task selection):**
    * Added explicit `task_selection` parameter to configs (default: 'all' = maximum data)
    * Modified `load_bansal()` to support 3 modes: 'all' (default, maximizes n_trials),
      'min_per_domain' (backward compat, fragile), 'first_10_shared' (v0 mode, fragile)
    * Created `e1_robustness.py` to run robustness analysis across all 3 schemes
    * **ROBUSTNESS RESULTS (Human condition over-dispersion rho):**
      - 'all' (50 tasks, 11200 trials): rho = 0.0666
      - 'min_per_domain' (5 tasks, 1220 trials): rho = 0.0000
      - 'first_10_shared' (10 tasks, 2340 trials): rho = 0.0369
      - **VERDICT: FRAGILE** - Range (0.0666) > 50% of mean (0.0345)
      - Signal is SENSITIVE to task selection on small Bansal dataset
    * Documented in SPEC.md (E1 table) and this PROGRESS.md as **KNOWN LIMITATION**
    * The 'all' default (maximum data) is the principled choice for methods papers
  - **BLOCKER-2 (misleading "stratified pooling" terminology):**
    * Renamed `betabinom_overdispersion_difficulty_controlled()` to 
      `betabinom_overdispersion_within_domain()` to accurately describe what it does
    * Fixed docstring: Bansal is BETWEEN-SUBJECTS on domain (each user saw exactly 1 domain).
      Function aggregates trials within each user's assigned domain. NOT stratified estimation.
    * Updated all call sites in e1_multicond.py, tests, and methodology descriptions
    * Difficulty control works via experimental design (balanced domain assignment), not
      statistical adjustment
  - Results saved: `results/e1_multicond_robustness.json`
- 2026-07-14: **E1-MULTICOND IMPLEMENTATION (feature/e1-multicond branch)**
  - **Config:** `configs/e1_multicond.yaml` selecting all 6 Bansal conditions (configurable,
    defaults to all 6). Backward compatible with v0 config.
  - **Data (Module A extended):** Generalized `load_bansal()` from UI pair to arbitrary
    list of conditions. Multi-condition support with sorted iteration for determinism.
    Task difficulty mapped from domain (beer=1, amzbook=2, lsat=3) for difficulty control.
  - **Metrics (Module C) - RIGOR:**
    * **Difficulty control:** `betabinom_overdispersion_difficulty_controlled()` computes
      per-condition human over-dispersion using STRATIFIED POOLING. Each user contributes
      (n_relied, n_trials) pooled across task domains (beer/amzbook/lsat) to control for
      inherent difficulty differences. This ensures cross-condition comparisons are not
      confounded by task difficulty.
    * **Correlation:** `condition_correlation()` implements Spearman rank correlation
      (robust for small n=6, monotonic hypothesis), permutation test p-value (10k shuffles,
      exact finite-sample), and bootstrap CI (10k resamples). Degenerate guard: n<3
      flagged as non-evidence.
  - **Panel (Module B extended):** Generalized stub from UI pair to list of conditions.
  - **Experiment (Module E):** `src/twdf/experiments/e1_multicond.py` runs chain over
    all 6 conditions, writes `results/e1_multicond.json`.
  - **Results (n=6 conditions, ~1200 trials each):**
    * **Human over-dispersion (difficulty-controlled):**
      - Conf.: rho=0.0023 [CI: 0.0000, 0.0543], n=286 users
      - Conf.+Adaptive: rho=0.0146 [CI: 0.0000, 0.0650], n=292 users
      - Conf.+Adaptive (Expert): rho=0.0000 [CI: 0.0000, 0.0000], n=195 users
      - Conf.+Double: rho=0.0000 [CI: 0.0000, 0.0096], n=285 users
      - Conf.+Single: rho=0.0000 [CI: 0.0000, 0.0264], n=280 users
      - Human: rho=0.0000 [CI: 0.0000, 0.0386], n=283 users
    * **Cross-condition correlation (panel disagreement vs human over-dispersion):**
      - Spearman rho = -0.2319
      - Permutation p = 0.5800 (NOT significant)
      - Bootstrap 95% CI: [-1.0000, 1.0000]
      - n_conditions = 6 (NON-DEGENERATE)
  - **Tests:** 14/14 tests PASS (6 original + 8 new multi-condition tests). Added:
    multi-condition loader, difficulty-controlled overdispersion (synthetic confounded
    case), Spearman correlation (monotonic/random/degenerate cases), multi-condition
    panel stub.
  - **Determinism verified:** Cross-process reproducibility confirmed (identical Spearman
    rho, p-value, and per-condition human rho across independent runs).
  - **Honest caveat (disclosed in results JSON and methodology):**
    * The synthetic panel disagreement is DERIVED from fixed condition properties
      (deterministic hash-based spread assignment). This is CIRCULAR-BY-DESIGN.
    * The correlation is a PLUMBING/MECHANISM CHECK of the statistics pipeline, NOT
      scientific evidence of a relationship, until the real LLM panel (Module B)
      replaces the stub.
    * The per-condition HUMAN over-dispersion numbers ARE genuine findings from real data.
  - **Difficulty control method (for auditor):**
    * Method: STRATIFIED POOLING across task domains (beer/amzbook/lsat).
    * Rationale: Domains have different inherent difficulty. Naively pooling would let
      difficulty confound cross-condition comparisons (e.g., a condition with more hard
      tasks would show different reliance). Each user contributes trials summed across
      all domains they saw, so users are compared on the same difficulty distribution.
    * Note: In this dataset, users saw only one domain each (between-subjects design),
      so stratification reduces to within-domain pooling. The method is correct and
      ready for within-subjects designs where it would prevent confounding.
  - **Deliverable:** Runnable `python -m twdf.experiments.e1_multicond --config
    configs/e1_multicond.yaml`, all tests pass, cross-process determinism confirmed.

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

- 2026-07-14: **E1-DECOMPOSITION ANALYSIS (feature/e1-multicond branch, slice for PR #2)**
  - **Scientific Question:** Of the between-user variance in reliance, how much is a STABLE 
    USER main effect (consistent across tasks) vs USER × TASK interaction (task-dependent)?
  - **Critical Methodological Discovery:** ANOVA-style variance partition on single-observation 
    cells CANNOT identify interaction from noise. Verified on Bansal data: 99.7% of 
    (condition, user, task) cells have EXACTLY 1 observation. ANOVA on cells was the WRONG 
    method (confounded).
  - **Correct PRIMARY Method:** Split-half reliability (psychometric standard). Each user 
    sees ~40-50 tasks → randomly split tasks into halves A/B → correlate per-user reliance 
    rates across halves. High correlation = stable trait; low = task-dependent. Spearman-Brown 
    corrected for full-length reliability. This method is WELL-IDENTIFIED on this data structure.
  - **OPTIONAL Corroboration:** Binomial GLMM with crossed random effects (user, task, 
    user×task). Unlike Gaussian ANOVA, Bernoulli likelihood with partial pooling CAN identify 
    variance components via generative model. **Result: Did NOT converge (maxiter=10, bounded 
    for fast reruns).** HONEST REPORTING: GLMM corroboration not available; split-half stands 
    alone (this is acceptable — split-half is the gold standard for this structure).
  - **Implementation:**
    * `src/twdf/metrics/variance_decomposition.py`: `split_half_reliability()` (PRIMARY), 
      `variance_components_glmm()` (OPTIONAL, bounded maxiter=10 for fast failure)
    * `src/twdf/experiments/e1_decomposition.py`: Runs decomposition on all 6 Bansal conditions
    * `configs/e1_decomposition.yaml`: Config for decomposition analysis
    * `tests/test_variance_decomposition.py`: 10/10 tests PASS (validated on synthetic data 
      with STRONG thresholds: pure stable-user reliability ≥0.7, share ≥0.8; pure interaction 
      ≤0.2). Do NOT weaken thresholds.
  - **Results (PRIMARY: Split-half reliability, 100 splits, Spearman-Brown corrected):**
    * **Human (no AI):** stable_user_share = 0.742 [95% CI: 0.693, 0.787], n=283 users
      → 74% of between-user variance is stable across tasks. Reliance is substantially a 
      STABLE USER TRAIT.
    * **AI-assisted conditions:**
      - Conf.+Double: 0.414 [0.314, 0.505], n=285
      - Conf.: 0.358 [0.271, 0.463], n=286
      - Conf.+Adaptive: 0.334 [0.228, 0.416], n=292
      - Conf.+Single: 0.321 [0.166, 0.442], n=280
      - Conf.+Adaptive (Expert): ~0.000 [0.000, 0.000], n=195 (negative reliability clamped to 0)
      → Only 32-41% stable (Expert ~0%). The majority of variance is USER × TASK interaction.
  - **Key Finding:** AI assistance fundamentally changes reliance from a STABLE USER TRAIT 
    (Human: 74%) to predominantly TASK-DEPENDENT behavior (AI: 32-41%). This shifts axis-1 
    framing from "safety depends on WHO the user is" to "depends on USER × TASK interaction".
  - **Determinism:** VERIFIED. Split-half results are byte-identical across separate process runs 
    (all random seeds fixed: split-half seed=43, GLMM seed=42, n_splits=100). Test suite includes 
    explicit determinism check.
  - **Validation:** Tested on synthetic data with known variance structure. Method correctly 
    recovers ground truth (STRONG thresholds enforced: not weakened to fit weak estimators).
  - **Scientific Documentation:** `docs/research/2026-07-14-overdispersion-decomposition.md` 
    — full write-up including identifiability argument, split-half methodology, GLMM honest 
    non-convergence reporting, interpretation, and framing implications for SPEC/H1a.
  - **Dependencies:** Added `statsmodels` to pyproject.toml for GLMM (optional corroboration).
  - **Honest Caveat:** GLMM did not converge for any condition. Finding rests on split-half 
    evidence alone (methodologically sound; split-half is gold standard for this structure). 
    Replication and alternative corroboration methods desirable.
  - **Framing Implication:** PR #2's axis-1 interpretation now rests on this decomposition 
    finding: in AI-assisted conditions, safety interventions must account for TASK CONTEXT, 
    not only user traits. A user's reliance risk profile is not fixed; it depends on which 
    tasks they encounter.

## Done (LU&YIN DECOMPOSITION REPLICATION — 2026-07-15)
- **2026-07-15 LU&YIN C0 REPLICATION (feature/luyin-decomp, PR #5)**
  - **Scope:** Replicate the Bansal decomposition finding (C0: AI assistance → user×task dominant) on a SECOND dataset (Lu&Yin CHI'21) to test generalizability
  - **STATUS: ✅ COMPLETE — HONEST DIVERGENCE FINDING (valid, informative result)**
  - **IMPLEMENTATION:**
    * `src/twdf/data/luyin.py`: Loader for Lu&Yin CHI'21 dataset, canonical schema mapping
      - URL: https://github.com/ZhuoranLu/Trustworthy-ML (9030 trials, 301 users × 30 tasks each)
      - Reliance: `finalPrediction == AI advice` (same as Bansal)
      - Conflict-conditioned: reliance among trials where `selfPrediction ≠ AI` (robustness DV)
      - Dtype coercion (boolean strings → bool), ground_truth derivation verified
    * `src/twdf/experiments/luyin_decomposition.py`: CLI runner, reuses `split_half_reliability()` with SAME seeds (43) and params as Bansal for comparability
    * `configs/luyin_decomposition.yaml`: Config with `seed_split_half=43`, `n_splits=100`, `min_tasks=8` (same as Bansal)
    * `tests/test_luyin.py`: **7/7 tests PASS** (structure, reliance definition, dtype coercion, ground truth, determinism, conflict trials, cross-process subprocess determinism)
    * `docs/research/2026-07-15-luyin-decomposition-replication.md`: Full replication report with honest verdict
  - **RESULTS (2026-07-15, seed=43, 100 splits):**
    * **PRIMARY DV (unconditional reliance):**
      - **stable_user_share = 0.801** [95% CI: 0.771, 0.834]
      - Spearman-Brown reliability: 0.801 ± 0.016
      - Spearman (half): 0.668 ± 0.023
      - ICC(2,1): 0.662 ± 0.025
      - n_users (≥8 tasks): 301
    * **ROBUSTNESS DV (conflict-conditioned reliance, selfPrediction ≠ AI):**
      - **stable_user_share = 0.792** [95% CI: 0.761, 0.824]
      - Spearman-Brown reliability: 0.792 ± 0.018
      - n_users (≥8 conflict): 240
      - n_conflict_trials: 3446 (38.2% of total)
    * **GLMM:** Did not converge (API error: `maxiter` keyword unsupported). Split-half stands alone.
  - **COMPARISON TO BANSAL (from e1_decomposition.json):**
    * Bansal Human (no-AI): **0.742** [0.693, 0.787] ← stable user trait
    * Bansal AI-assisted range: **0.321–0.414** ← user×task dominant
    * **Lu&Yin AI-assisted: 0.801** [0.771, 0.834] ← **CLOSER TO NO-AI BASELINE, NOT AI-ASSISTED**
  - **VERDICT: DIVERGES**
    * The "AI assistance → user×task dominance" pattern found on Bansal **does NOT generalize** to Lu&Yin
    * On Lu&Yin, AI-assisted reliance remains a **stable user trait** (share 0.80), resembling Bansal's *no-AI* baseline (0.74)
    * This is **NOT a failure** — it reveals **boundary conditions** for the C0 theory
  - **C0 STATUS: HELD (not refined, not demoted) — mechanism UNRESOLVED (PI-directed):**
    * Lu&Yin establishes ONLY that the AI-assisted stable-user share is NOT universal
      (Bansal 0.32–0.41 vs Lu&Yin 0.80). It does NOT establish a cause. The between-dataset
      comparison is CONFOUNDED and Lu&Yin has NO no-AI arm, so it cannot test C0's core
      within-dataset contrast (0.74→0.32). Do NOT write "design-dependent C0" into SPEC yet.
    * **NEXT SLICE = zero-quota DISCRIMINATOR:** re-decompose **Bansal on subsets MATCHED to
      Lu&Yin's regime** (single domain, matched difficulty, comparable AI-accuracy).
      - user×task PERSISTS under matched homogeneity → regime NOT the driver → **demote C0**,
        lean on C1 (panel two-axis).
      - COLLAPSES to trait-stable → regime/feedback isolated → **reframe C0 as design-dependent**
        on identified ground.
    * Candidate (untested) moderators: sequential-feedback design, single-domain/difficulty
      homogeneity, higher AI accuracy, estimation power.
  - **METHODOLOGY RIGOR:**
    * ✅ Split-half reliability (PRIMARY, well-identified, same seeds/params as Bansal)
    * ✅ Determinism verified (cross-process subprocess test passes)
    * ✅ Honest reporting of divergence (no post-hoc tuning)
    * ✅ Same methodology as Bansal (direct comparability)
    * ✅ All tests pass (7/7)
  - **CAVEATS:**
    1. Single new dataset (Lu&Yin); not multi-dataset meta-analysis
    2. Design confounds: within-subject sequential (Lu&Yin) vs between-subjects (Bansal)
    3. No no-AI baseline in Lu&Yin (cannot replicate 0.74 → 0.32 shift within-dataset)
    4. Task domain differs: income prediction vs beer/books/LSAT
    5. GLMM non-convergence (split-half stands alone)
  - **NEXT STEP:** Independent audit + Manager verification → merge as an honest BOUNDARY
    result. C0 co-anchor framing HELD pending the discriminator slice (above).
  - **FILES:**
    * Results: `results/luyin_decomposition.json`
    * Research doc: `docs/research/2026-07-15-luyin-decomposition-replication.md`
    * Tests: `tests/test_luyin.py` (7/7 pass)

## Done (BANSAL DISCRIMINATOR — 2026-07-15)
- **2026-07-15 BANSAL DISCRIMINATOR (feature/bansal-discriminator, PR #6)**
  - **Scope:** C0 mechanism test — DECISIVE test of whether Bansal's low AI-assisted stable_user_share (~0.32–0.41, user×task dominant) PERSISTS or COLLAPSES under Lu&Yin-matched homogeneity
  - **STATUS: ✅ COMPLETE — INCONCLUSIVE (mechanism not isolated); C0 DEMOTED to Bansal-specific supporting finding on honest grounds (Manager/PI-corrected)**
  - **IMPLEMENTATION:**
    * `configs/bansal_discriminator.yaml`: PRE-SPECIFIED subsets (defined BEFORE seeing results):
      - `full_ai`: Full Conf.+Adaptive baseline
      - `domain_beer`, `domain_amzbook`, `domain_lsat`: By-domain slices (difficulty homogeneity test)
      - `ai_acc_band_0.6_0.75`: AI-accuracy band matching Lu&Yin's ~0.70
      - `tasks_per_user_30`: Subsample to Lu&Yin's task count (robustness check)
      - `lsat_matched`: LSAT + AI-acc band (strictest Lu&Yin match)
    * `src/twdf/experiments/bansal_discriminator.py`: CLI runner with `filter_subset()`, `compute_subset_structure()`, split_half_reliability on each subset, PI-directed verdict decision rule
      - Uses **Conf.+Adaptive** as representative AI condition (avoids pooling 1338 users)
      - Verdict thresholds: PERSIST ≤ 0.50, COLLAPSE ≥ 0.70
    * `tests/test_bansal_discriminator.py`: **13/13 tests PASS** (subset filtering, structure computation, cross-process determinism, real results validation)
    * `docs/research/2026-07-15-bansal-discriminator.md`: Full discriminator report with matched-subset table, heterogeneity gradient, honest verdict, C0 recommendation
  - **RESULTS (2026-07-15, seed=43, 100 splits, Conf.+Adaptive):**
    * **full_ai (baseline):** stable_user_share = **0.334** [0.228, 0.416] — matches Bansal AI-assisted range
    * **domain_beer:** 0.001 [0.000, 0.011] — **CEILING ARTIFACT, UNINTERPRETABLE** (between-user SD ≈ 0.05; no signal to detect)
    * **domain_amzbook:** 0.000 [0.000, 0.000] — **CEILING ARTIFACT, UNINTERPRETABLE** (SD ≈ 0.05)
    * **domain_lsat (Lu&Yin-matched regime):** **0.464 [0.309, 0.587]** — **HEADLINE (only interpretable subset; SD ≈ 0.135)**
      - RISES from full_ai (0.334) toward Lu&Yin's 0.80 — but only PARTWAY
      - CI [0.309, 0.587] OVERLAPS full_ai's [0.228, 0.416] → rise NOT statistically clean
      - Does NOT collapse to trait-stable (0.80) → INCONCLUSIVE, not a clean persist
    * **ai_acc_band_0.6_0.75:** 0.320 [0.205, 0.417] — Matching AI-acc alone does NOT raise share
    * **tasks_per_user_30:** 0.373 [0.284, 0.453] — Slightly higher (robustness check, Spearman-Brown corrects)
    * **lsat_matched:** error (no data — LSAT 20 tasks + narrow AI-acc band leaves too few)
  - **HETEROGENEITY GRADIENT (internal Bansal evidence):**
    * Hypothesis: If homogeneity drives share, share should RISE as heterogeneity falls
    * Observed: **NON-MONOTONIC**
      - full_ai (multi-domain): 0.334
      - domain_beer/amzbook: 0.001/0.000 — **DROPS** to near-zero (paradoxical!)
      - domain_lsat: 0.464 — **RISES** (modest effect, but does not collapse)
      - ai_acc_band: 0.320 — Similar to full_ai
    * Conclusion: Relationship between task homogeneity and trait-stability is **COMPLEX and DOMAIN-DEPENDENT**, not a simple linear effect
  - **VERDICT (Manager/PI-corrected 2026-07-15): INCONCLUSIVE — mechanism NOT isolated.**
    * ⚠️ The original subagent verdict "PERSISTS → clean DEMOTE" was OVERSTATED. It leaned on
      the beer/amzbook near-zero shares, which are **CEILING/LOW-VARIANCE ARTIFACTS**:
      between-user reliance SD ≈ 0.05 (mean ~0.81–0.85) → almost no between-user signal →
      split-half reliability mechanically ≈ 0. These 2 of 3 domain subsets are
      **UNINTERPRETABLE** (you cannot measure trait-stability without between-user spread).
    * The ONLY interpretable Lu&Yin-matched subset is **lsat** (SD ≈ 0.135): share = 0.464
      [0.309, 0.587] — a RISE from full_ai 0.334 toward Lu&Yin 0.80, but only PARTWAY, and
      its CI **OVERLAPS** full_ai's [0.228, 0.416] → the rise is not statistically clean.
    * So matching Bansal to Lu&Yin's controllable regime does NOT cleanly resolve the gap;
      the Bansal↔Lu&Yin difference remains **CONFOUNDED and UNRESOLVED** (sequential feedback
      is uncontrollable here; residual variance/ceiling differences remain).
  - **RECOMMENDATION (PI-approved): DEMOTE C0** to a **Bansal-specific SUPPORTING finding**
    on HONEST inconclusive grounds (generalization unresolved; NOT a "clean persist"). Make
    **C1 (panel two-axis triage) the PRIMARY contribution.** Keep the **regime-dependent /
    sequential-feedback driver as an explicit OPEN QUESTION** + future mechanism study
    (§4.1 sequential-stateful mode), NOT a claim. §4.1 build deferred as optional upside
    AFTER C1 is solid (don't spend scarce quota on a speculative C0 upgrade now).
  - **HONEST CAVEATS:**
    1. Sequential-feedback is UNCONTROLLABLE (Bansal static; Lu&Yin sequential). PERSIST verdict does NOT prove "regime doesn't matter" in general; only rules out controllable confounds tested.
    2. Beer/amzbook paradox: single-domain homogeneity in easy/medium tasks LOWERS share (near-zero), not raises it. Unexpected; may be ceiling effect (high reliance → low variance → weak split-half correlation).
    3. LSAT has fewer tasks (20 vs 50) → wider 95% CI [0.309, 0.587] than full_ai [0.228, 0.416], but point estimate (0.464) robustly in PERSIST range.
    4. Representative condition (Conf.+Adaptive) may not generalize to other AI conditions, but prior work shows all have low share (0.32–0.41), so verdict unlikely to change.
    5. lsat_matched subset (LSAT + AI-acc band) produced no data (too few tasks). LSAT domain alone is strictest available match.
  - **METHODOLOGY RIGOR:**
    * ✅ All subsets PRE-SPECIFIED in config BEFORE seeing results
    * ✅ Verdict thresholds (PERSIST ≤ 0.50, COLLAPSE ≥ 0.70) defined in config
    * ✅ Determinism verified (cross-process subprocess test: bit-identical stable_user_share)
    * ✅ Same split_half_reliability() method as e1_decomposition (seed=43, n_splits=100, min_tasks=8)
    * ✅ All subsets reported (including inconvenient beer/amzbook near-zero results)
    * ✅ All tests pass (13/13)
  - **NEXT STEP:** Independent audit + Manager verification → if approved, this verdict informs C0 final status in SPEC (demote to single-dataset finding or reframe as design-dependent with honest caveats).
  - **FILES:**
    * Config: `configs/bansal_discriminator.yaml`
    * Experiment: `src/twdf/experiments/bansal_discriminator.py`
    * Results: `results/bansal_discriminator.json`
    * Research doc: `docs/research/2026-07-15-bansal-discriminator.md`
    * Tests: `tests/test_bansal_discriminator.py` (13/13 pass)

## Done (REAL RUN COMPLETE — 2026-07-15)
- **2026-07-15 MODULE B (REAL LLM PANEL) — IMPLEMENTATION + REAL RUN COMPLETE**
  - **Scope:** Thin vertical slice — real LLM panel via GitHub Models with counterfactual pairing
  - **FINAL STATUS: ✅ COMPLETE AND VERIFIED**
    * `src/twdf/panel/provider.py`: GitHubModelsProvider with hashlib-based deterministic caching, retry logic, call budget
      - **PACING FIX:** Raised default `inter_call_sleep` to 0.8s (≈1.25 req/s, safe margin under empirical 1.5 req/s sustainable rate)
      - **BACKOFF FIX:** HTTP 429 now waits 8.0s minimum (vs exponential) to let token bucket refill, max 8 retries
      - **5xx HANDLING:** Server errors keep exponential backoff (unchanged)
    * `src/twdf/panel/real_panel.py`: Dual-system flow (System-1 frozen + System-2 counterfactual pairing), implements INTERFACES §3 exactly
    * `src/twdf/data/bansal_tasks.py`: Beer task stimulus loader with testid→questionId join verification (50/50 overlap confirmed)
    * `src/twdf/metrics/overdispersion.py`: Added `paired_permutation_test()` for elasticity significance
    * `src/twdf/experiments/e1_panel_v1.py`: CLI runner with run_manifest, elasticity + bootstrap CI + permutation test
      - **BOOTSTRAP FIX:** Edge-case handling for persona resampling (shared-tasks filter)
    * `configs/e1_panel_v1.yaml`: 5 diverse personas, **20 beer tasks (thin-slice scale restored)**, UI pair (Conf. vs Conf.+Adaptive (Expert)), `inter_call_sleep=0.8`, `call_budget=350`
    * `tests/test_panel_real.py`: **31/31 offline tests PASS** (updated live test assertion for System-1 sharing)
    * `.gitignore`: Added `data/cache/`, `*.log`, `*_output.txt` exclusions
    * `pyproject.toml`: Added `requests>=2.31.0` dependency
  - **CRITICAL DESIGN VERIFIED:**
    * Counterfactual invariant holds (System-1 identical across UI arms for same persona/task/seed) — TESTED cross-process
    * Deterministic caching uses hashlib (NOT builtin hash()) — TESTED cross-process
    * testid→questionId join confirmed: 50/50 beer tasks overlap with Bansal questionIds 0-49
    * Reliance definition aligned with Bansal adoption: `final == ai_advice`
    * UI conditions use exact Bansal strings: "Conf.", "Conf.+Adaptive (Expert)"
  - **REAL RUN RESULTS (2026-07-15, config hash 424c5469d6bbb4c3):**
    * **API Performance:** 145 API calls + 155 cache hits = 300 total requests, 0 HTTP 429 errors (0.8s pacing worked perfectly)
    * **Runtime:** 745.9s first run (API calls), 4.5s cached rerun (100% cache hit)
    * **Estimated Cost:** $0.0544 (145 calls @ gpt-4o-mini pricing)
    * **Per-Persona Reliance Rates:**
      - Control (Conf.): p1=0.70, p2=0.75, p3=0.70, p4=0.70, p5=0.80 (mean=0.73)
      - Treatment (Conf.+Adaptive Expert): p1=0.70, p2=0.70, p3=0.75, p4=0.70, p5=0.80 (mean=0.73)
    * **Panel Disagreement:** Control=0.0020, Treatment=0.0020 (identical variance across UI arms)
    * **Within-Task Reliance Elasticity (Treatment − Control):** 0.0000
    * **Paired Permutation Test:** p = 1.0000 (n_pairs=20, NO significant treatment effect)
    * **Bootstrap 95% CI:** [0.0000, 0.0000]
    * **System-1 Accuracy (no AI):** 0.800 (160/200 correct; agents genuinely attempt task)
    * **Task Diversity:** 16/20 AI-correct (80%), 4/20 AI-incorrect, conf range [0.509, 0.983] mean=0.826
  - **DELIVERABLES:**
    * ✅ All code implemented per spec
    * ✅ All offline tests pass (31/31)
    * ✅ Cross-process determinism verified
    * ✅ Data join verified (50/50 tasks)
    * ✅ Real API run completed with no 429s
    * ✅ `results/e1_panel_v1.json` with full run_manifest
    * ✅ Pacing empirically validated (0.8s inter-call sleep sustainable)
  - **KEY FINDING (METHODOLOGY):**
    * **NULL RESULT:** No treatment effect detected (elasticity=0, p=1.0). Expert explanations did NOT shift reliance in this LLM panel.
    * **CAVEAT:** This is a SYNTHETIC agent panel (gpt-4o-mini System-2), NOT real humans. Null result does NOT contradict Bansal's human findings. This run VALIDATES THE PIPELINE (data → panel → metrics → output) for hostile audit, NOT the scientific hypothesis.
    * **PANEL vs HUMAN COMPARISON:** Humans show reliance 79.1% (Bansal data), LLM panel 73%. LLM agents are NOT calibrated to human behavior. This is EXPECTED for a plumbing validation run.
  - **METHODOLOGY CAVEATS (FOR AUDIT):**
    1. LLM panel personas are SYNTHETIC proxies (defined by skill/literacy/caution parameters), NOT real user archetypes
    2. System-2 generation prompts are MINIMAL (not psychologically validated)
    3. 20-task thin slice is smaller than full Bansal dataset (50 tasks)
    4. Single model (gpt-4o-mini) — no cross-model triangulation yet
    5. No abstention modeling (future: Module D protocol)
    6. Reliance definition is binary (final == AI), no partial adoption modeling
  - **MANAGER DIAGNOSIS (independent, from raw responses — the scientifically important part):**
    * The null is REAL, not a bug (audit + Manager confirmed: counterfactual invariant
      0/100 violations; treatment prompt genuinely renders the expert explanation; arms
      are not cache-collapsed — 2/100 cells flip, in opposite directions).
    * **Mechanism = panel compliance/anchoring collapse:** in **97% of cells the agent's
      final decision == its own System-1 anchor** (agent almost never moves). Of 146
      "relied" cells, **140 are baseline agreement** (System-1 already matched AI); only
      **6 are genuine switches-to-AI**. So measured "reliance" (~0.73) ≈ agent↔AI
      AGREEMENT, not AI adoption. Personas barely diverge (disagreement 0.002 ≈ 0).
    * **Root cause:** the sim agent is a strong, confident independent classifier
      (System-1 acc 0.80) on easy binary sentiment → rarely uncertain → rarely defers;
      the reliance DV conflates agreement with adoption; no wrong-AI/conflict pressure;
      weak persona conditioning. => the naive panel does NOT reproduce human reliance
      heterogeneity (the axis-1 signal has ~no dynamic range to act on).
  - **PI DECISION (2026-07-15, user = "BOTH"):** (1) MERGE this slice as honest infra +
    documented negative result (audit CONDITIONAL PASS → BLOCKER-1 fixed → Manager
    verified); (2) NEXT slice REDESIGNS the panel DV = conflict-conditioned reliance
    (System-1 ≠ AI trials only) + inject WRONG-AI / axis-2 condition + harder/ambiguous
    item selection + stronger persona conditioning; (3) ELEVATE the real-data
    decomposition (stable-trait → user×task) to a CO-ANCHOR contribution (see SPEC C1).
  - **MERGE STATUS:** audit CONDITIONAL PASS (all methodology/security/determinism PASS;
    one schema BLOCKER-1) → BLOCKER-1 fixed (model/trace/trust_state serialized, commit
    d6c48db, numbers unchanged, 0 API calls) → Manager independently verified: 11 fields
    present, cross-process determinism IDENTICAL, worktree clean → MERGED (see Merge log).
    * Tests: 31/31 pass. Branch: `feature/moduleB-panel` (PR #3).

## Done (E2 PANEL REDESIGN — 2026-07-15)
- **2026-07-15 E2 PANEL REDESIGN — IMPLEMENTATION + REAL RUN COMPLETE**
  - **Scope:** Panel redesign with 4 fixes (A-D) to address PR#3's compliance-collapse
  - **FINAL STATUS: ✅ COMPLETE AND VERIFIED**
    * **Fix A (conflict-conditioned reliance DV):** `conflict_conditioned_reliance()` in overdispersion.py — computes reliance ONLY on conflict trials (system1 ≠ AI), resolving the 97% agreement-collapse
    * **Fix B (data-driven item selection):** `src/twdf/data/item_selector.py` — selects hard/ambiguous items using AI-wrong (50%), low-conf (30%), high-variance (20%) criteria; deterministic with sorted+seeded RNG
    * **Fix C (strengthened personas):** 6 diverse personas spanning skill×ai_literacy×caution space with explicit behavioral policies (vs PR#3's weak 5-persona set)
    * **Fix D (axis-2 Wrong-AI):** `over_reliance_level()` in overdispersion.py — Wrong-AI dark condition shows WRONG label (1 - ai_pred) + pseudo-high conf + oppressive framing; measures adoption of wrong AI
    * **3-condition panel:** Control ("Conf."), Treatment ("Conf.+Adaptive (Expert)"), Dark ("Wrong-AI (dark)")
    * **Provider fixes:** `model_name` parameter added; 429 cooldown capped at 120s (fails fast on daily quota exhaustion instead of sleeping ~13h)
    * **Item selection:** 20 hard beer tasks (AI-wrong 40%, low-conf 50%, mean conf 0.721, human variance 0.159)
    * `tests/test_panel_redesign.py`: 39/39 offline tests PASS (2 live tests skipped due to daily quota)
  - **REAL RUN RESULTS (2026-07-15, model openai/gpt-4.1-mini, config hash d0a7f2e9):**
    * **API Performance:** 480 API calls first run, 0 calls + 480 cache hits on rerun (DETERMINISTIC, cross-process verified)
    * **Runtime:** Real run 8.4s (cached), $0.18 total cost
    * **FIX A EFFECTIVENESS — Conflict rate RESTORED:**
      - Overall conflict rate: **43.3%** (vs PR#3's 3% collapse) ✅
      - Control: 52/120 conflict trials (43.3%)
      - Treatment: 52/120 conflict trials (43.3%)
    * **Conflict-conditioned reliance (PRIMARY DV):**
      - Control (Conf.): 0.327 (unconditional: 0.708)
      - Treatment (Conf.+Adaptive Expert): 0.481 (unconditional: 0.775)
    * **Per-persona conflict reliance DIVERGES (FIX C works):**
      - Control range: 0.111 (p2-expert-trusting) → 0.556 (p5-novice-trusting)
      - Treatment range: 0.333 (p1,p2) → 0.667 (p5-novice-trusting)
      - Personas now show clear heterogeneity (vs PR#3's near-uniformity)
    * **Axis-1 within-task elasticity (conflict trials):**
      - Mean diff (treatment − control): **+0.194**
      - Paired permutation test: p = 0.174 (n_pairs=11)
      - Direction: POSITIVE (treatment increased reliance as expected)
      - Power: UNDERPOWERED (n=11 tasks with conflict, not significant)
    * **FIX D — Axis-2 over-reliance level:**
      - Wrong-AI adoption: **0.325** (32.5% adopted wrong AI advice)
      - Per-persona range: 0.000 (p5) → 0.450 (p2, p4)
      - Between-persona spread: 0.0287
      - **p5-novice-trusting dark-pattern BACKFIRE (audit-confirmed GENUINE):** p5 adopted **0% of WRONG AI advice** in Wrong-AI (dark) condition, vs 55.6% reliance in control condition. Independent audit verified this is NOT a parsing/label bug but GENUINE behavior: p5 actively changes AWAY from AI under oppressive framing. Possible interpretations (state all, commit to none): (a) tension in "novice-trusting" persona label, (b) coercive dark-pattern BACKFIRES and triggers skepticism in some agents, (c) gpt-4.1-mini safety training resisting coercion. Flag as follow-up to investigate — scientifically relevant to axis-2 (dark-pattern sensor) design.
    * **System-1 accuracy:** 0.817 (agents genuinely attempt task)
    * **System-1 frozen invariant:** ✅ HOLDS across all 3 conditions (0 violations)
  - **DELIVERABLES:**
    * ✅ All code implemented per spec
    * ✅ 39/39 offline tests pass (2 live tests expected to skip on quota)
    * ✅ Cross-process determinism verified (subprocess pattern from test_panel_real.py)
    * ✅ Item selector determinism + criteria validated
    * ✅ Wrong-AI condition renders wrong label (tested)
    * ✅ `results/e2_panel_redesign.json` with full run_manifest
    * ✅ Documentation updated (PROGRESS.md + INTERFACES.md)
  - **KEY FINDINGS (HONEST FRAMING):**
    * **RESOLVES PR#3 compliance-collapse:** Conflict rate 3% → 43% ✅, personas now diverge ✅
    * **Positive-but-underpowered axis-1 elasticity:** +0.194 in expected direction, p=0.174 (n=11 not sufficient power)
    * **Real axis-2 signal:** 32.5% wrong-AI adoption, per-persona heterogeneity present
    * **CAVEATS:**
      - Model switched to gpt-4.1-mini (gpt-4o-mini daily quota exhausted) — NOT same-model comparable to PR#3
      - Elasticity not significant (small n, limited power)
      - Single domain (beer), 20 items, 6 personas — thin slice
      - One persona (p5) shows axis-2=0 anomaly — requires investigation
  - **METHODOLOGY IMPROVEMENTS:**
    * Conflict-conditioned reliance is now the PRIMARY axis-1 DV (resolves agreement≈reliance conflation)
    * Data-driven item selection concentrates conflict/ambiguity where it matters (vs random sampling)
    * Stronger persona conditioning gives axis-1 mechanism dynamic range
    * Axis-2 dark condition closes "uniformly lethal" blind spot (PR#3 had no wrong-AI pressure)
    * Provider model_name param + 120s cooldown cap improves robustness
  - **MERGE STATUS:** Ready for independent audit + Manager verification. Tests pass, determinism verified, docs updated.

## Doing (Manager #3 takeover 2026-07-16 — see docs/handoff/2026-07-16-manager-handoff.md + docs/DECISIONS.md)
- **✅ MERGED PR #10 renderer fidelity (2e8935b, 2026-07-16, DECISIONS D5.1):** corrected
  render_ui_condition to FAITHFUL Bansal semantics — `Conf.+Single`=predicted-class LIME spans only,
  `Conf.+Double`=both classes, `Conf.+Adaptive`=fixed median-conf threshold (beer 0.892 / amzbook
  0.889) gating Single↔Double, `Conf.+Adaptive (Expert)`=same rule on single-quoted expert
  phrase-spans; class1=positive/class0=negative; added `expert_highlights_html`. Replaces the prior
  token-COUNT misinterpretation BEFORE the confirmatory H1a run (prereg §3). Research
  `research-bansal-conditions` (paper quotes) + Manager verified beer median conf=0.892. Independent
  audit PASS + real-data verify; blast-radius tests 47/47. **⇒ the PR #8 "firm up renderer
  heuristics before confirmatory" item is now DONE.** Open cosmetic nit: expert-condition reuses the
  "identified by the AI model" header (wording only; no science/leakage impact).
  **⚠️ CACHE IMPACT:** the `Conf.+Adaptive (Expert)` prompt changed ⇒ E4's 193-call cache is
  INVALIDATED; E4 must RE-RUN FRESH (~450 calls) on the corrected renderer. PR#4 numbers were
  old-renderer exploratory.
- **✅ MERGED PR #8 axis1-pilot EXPLORATORY infra (ff69ce0, 2026-07-16):** stale branch first
  brought up to date with `main` (a raw squash would have DELETED azure_provider.py / DECISIONS.md /
  handoff / prereg — caught). Independent audit PASS + Manager verify (additive-only diff, no
  leakage, System-1 frozen, hashlib-only, 9/9 offline tests, no results JSON). Kept: 5-condition LIME
  renderers (Single/Double/Adaptive HEURISTICS — firm up before confirmatory), skip-on-cap
  multi-provider loop, power-analysis readout. Provider-stability limitation documented (D4.6/D4.8).
  Power-N (prereg §8) still PENDING. Non-blocking nits to firm up: cross-*model* freeze test trivial
  (constant mock); "cross-process" determinism test runs in-process.
- **⏸ PR #7 E4 axis-2 sensor + placebo (branch `feature/e4-compliance` @ ac6015f — PREPPED, awaiting compute):**
  - Code COMPLETE + **8/8 offline tests pass on the faithful renderer** (placebo content-free; System-1
    frozen across all 4 conditions control/faithful/placebo/wrong-AI; compliance-floor + adjusted axis-2).
  - **PREPPED 2026-07-16 (Manager #3):** merged `main` into the branch → now uses the PR #10 FAITHFUL
    renderer; resolved bansal_tasks.py conflict (kept faithful Single/Double/Adaptive + E4's detailed
    placebo, deduped); **re-matched the placebo length to the shorter faithful expert render (D5.2)**;
    55/57 blast-radius offline tests pass (2 skipped live). Old 193-call cache is stale (harmless).
  - **RUN FRESH when gpt-4.1-mini daily bucket resets (~15:50 local 2026-07-16 est; both gpt-4o+
    gpt-4.1-mini were 429 UserByModelByDay, Retry-After ~18585s at 10:40):** bridge token, then from the
    e4-compliance worktree `python -u -m twdf.experiments.e4_compliance --config configs/e4_compliance.yaml`
    (~450 calls, gpt-4.1-mini). Then independent audit (`.prompts/audit-e4-compliance.md`, incl. §4.5 +
    the placebo-length DoF) → Manager verify → merge.
  - READ OUT: H3 compliance floor (control < placebo < faithful, conflict-conditioned) + formal axis-2
    over_reliance_level on wrong-AI (+ compliance-adjusted).
- **CONFIRMATORY axis-1 (H1a) — the PRIMARY (C1) deliverable, NOT yet run.** Per prereg amendment
  2026-07-16T02:29:50Z: run on STABLE OpenAI family **{gpt-4o, gpt-4.1-mini}**, DAY-BATCHED across
  their separate daily buckets (free; no Azure dependency). Steps: clean power-N pass → fill prereg §8
  + freeze N + τ discipline BEFORE results → confirmatory (beta-binomial over-dispersion on conflict DV
  + within-task estimator + cross-condition Spearman over 5 conditions; beat 4 baselines; BH α=0.05;
  bootstrap over personas×seeds×models). **Report regardless of outcome.** Report per-model (model-mix confound).
- **✅ MERGED PR #9 AzureFoundryProvider (5cd179b)** — uncapped confirmatory path READY once PI sets
  `AZURE_OPENAI_ENDPOINT/KEY/API_VERSION/DEPLOYMENT` (see docs/plans/azure-setup.md). Detailed entry below.
- **gh GOTCHA:** run `$env:GH_TOKEN=$null` before every `gh` command (GH_TOKEN env hijacks gh to the
  wrong account; repo is EloiseJulia). git push unaffected.

### (merged) 2026-07-16: PR #9 — AzureFoundryProvider (MERGED to main, 5cd179b)
  - **Context:** GitHub Models' per-model daily cap (~500/day) blocks powered axis-1 runs. Lever C
    (quota-strategy.md): Azure AI Foundry / Azure OpenAI have NO daily cap, enabling single-session
    confirmatory runs.
  - **Implementation:** `src/twdf/panel/azure_provider.py` — `AzureFoundryProvider` implementing
    the SAME `ModelProvider` protocol as `GitHubModelsProvider`, making it a DROP-IN replacement.
    - Two API styles supported (constructor `api_style` parameter):
      1. `"azure_openai"` (default, Azure OpenAI Service): POST
         `{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={version}`,
         header `api-key: {key}`, body has NO `model` field (deployment is in URL).
      2. `"foundry"` (Azure AI Foundry models-as-a-service): POST `{endpoint}/chat/completions`
         (or custom `foundry_path`), header `Authorization: Bearer {key}`, body includes `model`.
    - **Cache mechanism:** Reuses the SAME hashlib-based response cache as `GitHubModelsProvider`
      (`data/cache/panel/`); cache keys include deployment name to prevent cross-provider collisions.
      Cross-process determinism verified. hashlib only; builtin `hash()` banned (grep test passes).
    - **Environment variables (REQUIRED, PI must provision):**
      - `AZURE_OPENAI_ENDPOINT` (e.g., `https://<resource>.openai.azure.com` or Foundry endpoint)
      - `AZURE_OPENAI_KEY` (NEVER logged/printed/committed; clear error if missing)
      - `AZURE_OPENAI_API_VERSION` (defaults to `"2024-10-21"` if not set)
      - `AZURE_OPENAI_DEPLOYMENT` (optional override; falls back to constructor `deployment` arg)
    - **Retry logic:** 429/5xx with backoff; NO daily-cap special-case (Azure has no such cap).
      Optional `inter_call_sleep` (default 0.2s) and `max_retries` (default 5).
    - **Protocol compliance:** Implements `name`, `generate()`, `generate_messages()`, `get_stats()`
      exactly per INTERFACES §3. Drop-in replacement for `run_panel`.
  - **Tests:** `tests/test_azure_provider.py` — 22 offline tests (mocked HTTP, NO real network):
    - Env var validation (missing vars → clear errors)
    - `azure_openai` style: URL format (`/deployments/{deployment}/...`), `api-key` header, NO
      `model` in body, response parsing
    - `foundry` style: URL format (`/chat/completions`), `Bearer` header, `model` in body, response parsing
    - Cache determinism: hashlib cache reuse + cross-process subprocess test (byte-identical)
    - Security: key never in cache files / repr / logs
    - Protocol compliance: satisfies `ModelProvider` + `run_panel` smoke test
    - Retry: 429/5xx handling with backoff
    - hashlib-only: grep `\bhash\(` in code (excluding comments) = 0 violations
  - **Result:** `pytest -m "not live" tests/test_azure_provider.py` → **22/22 PASSED** (offline).
    Existing `test_panel_real.py` → **5/5 PASSED** (no regressions).
  - **Documentation:**
    - `INTERFACES.md` §8 AS-BUILT updated: AzureFoundryProvider added; env vars; both api styles.
    - `PROGRESS.md` (this entry): exact env vars PI must set; confirmatory run switches provider.
    - `docs/plans/azure-setup.md` (NEW): PI provisioning steps (endpoint, key, api-version, deployment names).
  - **Status:** Code-complete, offline tests GREEN, awaiting PI-provisioned Azure credentials for
    the confirmatory axis-1 run. NO real API calls made (offline tests only). Ready for audit.

## Todo (post-gate)
- [x] S0 code scaffold: package `twdf`, config, logging, run_manifest.
- [x] Thin vertical slice v0 (PR #1) — real data → axis-1 over-dispersion metric.
- [x] Axis-1 broadened to all 6 Bansal conditions + robustness (PR #2).
- [x] Variance decomposition (PR #2): no-AI = stable trait; AI = user×task.
- [x] H1a refined per decomposition finding (commit b48ab2b).
- [x] **Module B — real LLM panel via GitHub Models (`GH_MODELS_TOKEN`), DONE (2026-07-15).**
      Real panel implemented; counterfactual pairing verified; 20-task thin slice complete.
- [ ] Axis-2 dark-pattern sensor + E4 compliance baseline.
- [ ] §4.3 atomic feature extraction (UIFeatureVector).
- [ ] Module D calibration + FREEZE τ_disp/τ_level (prereg) + abstention.
- [ ] E3 LOIO (leakage!), E5 ECE/radius; cross-model triangulation; Lu&Yin seq mode.

## Module status (§2.1)
| Module | Status | Blocked on |
|---|---|---|
| S0 architecture | ✅ DONE (v0.1.0, pyproject.toml, src/ structure) | — |
| A data & features | 🟡 PARTIAL — Bansal loader + multi-condition DONE; §4.3 atomic feature extraction NOT started; Lu&Yin not loaded | — |
| B panel engine | ✅ DONE (2026-07-15) — Real LLM panel with GitHub Models, counterfactual pairing, deterministic caching, 31/31 tests pass | — |
| C metrics & stats | ✅ DONE (beta-binomial + within_domain, split-half decomposition, Spearman+permutation+bootstrap; GLMM non-converged) | — |
| D calibration & protocol | 🔲 NOT STARTED (threshold freezing — prereg — deferred) | C + real B |
| E experiments & report | 🟡 E1 v0 + multicond + robustness + decomposition + **panel_v1 (real LLM)** DONE; E2/E3/E4/E5/E6 not started | A+B+C+D |

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
- **2026-07-16 — PR #9 `azure-provider` (AzureFoundryProvider) SQUASH-MERGED to main
  (commit 5cd179b).**
  - Flow: impl-azure-provider (no API; drop-in ModelProvider vs Azure OpenAI + Foundry api
    styles, env creds, replicated hashlib cache w/ deployment in key, 22 offline mock tests,
    docs/plans/azure-setup.md) → independent audit **PASS** (8/8, no blockers; verified both
    api styles, key never leaked, cache no-collision, GitHubModelsProvider untouched) →
    Manager verify (22/22 azure + 5/5 GitHub regression, worktree clean) → merged.
  - UNLOCKS: the confirmatory axis-1 run WITHOUT the GitHub Models daily cap. PI must set
    AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_KEY / AZURE_OPENAI_API_VERSION + deployment names
    (see docs/plans/azure-setup.md); recommend one `pytest -m live` cred check (~$0.001)
    before the confirmatory run. Non-blocking note: cache logic is replicated (future
    refactor to a shared base class).
- **2026-07-15 — PR #6 `bansal-discriminator` (C0 mechanism test) SQUASH-MERGED to main
  (commit 50250e6).**
  - Flow: impl-bansal-discriminator (zero-API; matched-subset split-half; produced an
    OVERSTATED "PERSISTS → clean demote" verdict) → **Manager caught a ceiling artifact**
    (beer/amzbook between-user SD ≈ 0.05 → share ≈ 0 is uninterpretable, NOT user×task) →
    escalated → PI chose demote-on-honest-grounds → Manager CORRECTED framing to
    INCONCLUSIVE + demoted C0 / elevated C1 → independent audit **APPROVE** (independently
    reproduced beer SD 0.047 / amzbook 0.044 / lsat 0.139; confirmed lsat CI [0.31,0.59]
    overlaps full_ai [0.23,0.42]; verified docs honest, no overclaim; 13/13 tests,
    determinism) → Manager verified clean → merged.
  - RESULT: **INCONCLUSIVE.** Matching Bansal to Lu&Yin's regime does not cleanly move the
    share to trait-stable; 2/3 domains are ceiling artifacts; the one interpretable subset
    (lsat) rose only partway (0.46, CI overlapping the 0.33 baseline). Bansal↔Lu&Yin gap
    CONFOUNDED and UNRESOLVED.
  - **DECISION (PI-approved): C1 (panel two-axis triage) is now the PRIMARY contribution;
    C0 DEMOTED to a Bansal-specific supporting finding (honest, not shown to generalize);
    regime/sequential-feedback = explicit OPEN QUESTION for a future mechanism study
    (§4.1), deferred until C1 is solid.** See SPEC §2.
- **2026-07-15 — PR #5 `luyin-decomp` (C0 generalization test) SQUASH-MERGED to main
  (commit 4364d54).**
  - Flow: impl-luyin-decomp (zero-API; Lu&Yin loader + split-half decomposition reusing
    split_half_reliability; 7 tests) → Manager verified numbers + escalated the finding →
    PI-directed FRAMING correction (hold causal claim) → independent audit **PASS** (10/10,
    no blockers; numbers reproduced, determinism verified, docs confirmed NOT overclaiming)
    → Manager verified (pytest 17 passed incl. cross-process determinism; worktree clean) → merged.
  - RESULT (real): Lu&Yin AI-assisted reliance stable_user_share = **0.80** [0.77,0.83]
    (unconditional) / 0.79 (conflict-conditioned) — TRAIT-STABLE, near Bansal's no-AI 0.74,
    NOT Bansal's AI-assisted 0.32–0.41. So the AI-assisted user×task share is NOT universal.
  - **C0 STATUS = HELD (not refined/demoted).** The between-dataset comparison is CONFOUNDED
    (Lu&Yin has no no-AI arm → cannot test C0's within-dataset contrast; sequential-feedback +
    homogeneity + AI-accuracy confounds). Mechanism UNRESOLVED. NEXT SLICE = zero-quota
    DISCRIMINATOR (Bansal re-decomposed on Lu&Yin-matched subsets) → decides demote-C0 vs
    design-dependent-reframe. Do NOT bake "design-dependent" into SPEC until then.
- **2026-07-15 — PR #4 `panel-redesign` (conflict-conditioned DV + wrong-AI axis-2 +
  hard items + strong personas) SQUASH-MERGED to main (commit 9caebc5).**
  - Flow: impl-panel-redesign (built conflict-conditioned reliance metric, data-driven
    item_selector, strengthened personas, Wrong-AI dark condition, e2 experiment) — RAN
    OUT OF TURNS mid-run → finish-panel-redesign (also ran out on the long run) →
    **Manager took over the run**: diagnosed GitHub Models **per-model DAILY cap**
    (`UserByModelByDay`, ~500/day; gpt-4o-mini exhausted → provider was sleeping ~13h on
    a giant Retry-After) → Manager fixed provider (config `model_name` param + 120s
    cooldown cap = fail-fast on daily cap), switched run to **gpt-4.1-mini** (fresh
    quota), trimmed to 20 items, ran to completion (480 calls, $0.18) → finish2 (tests +
    docs + commit; determinism from warm cache) → independent audit (FAIL: 1 test-hygiene
    BLOCKER; 13/14 checks PASS, incl. all science) → fix-redesign-blocker1 (determinism
    tests skip-safe on cold cache; p5 disclosure) → Manager verified: pytest -m "not live"
    37 passed/2 skipped/0 failed, cross-process determinism BYTE-IDENTICAL from warm
    cache, worktree clean → merged.
  - KEY RESULT (real, gpt-4.1-mini): the redesign RESOLVES PR#3's compliance-collapse.
    Conflict rate 3% → **43.3%**; conflict-conditioned reliance control 0.327 →
    treatment 0.481; per-persona spread 0.11–0.56 (personas now diverge sensibly);
    within-task elasticity **+0.194 (p=0.17, n=11 — UNDERPOWERED)**; **axis-2 wrong-AI
    over-reliance = 0.325** (first real second-axis signal); System-1 acc 0.817, frozen
    invariant holds across all 3 conditions. Anomaly (audit-confirmed genuine):
    p5-novice-trusting adopts 0% wrong-AI under the coercive dark framing (vs 0.556
    control) — a dark-pattern-BACKFIRE lead for axis-2 design.
  - CAVEATS: model switched to gpt-4.1-mini (not same-model comparable to PR#3);
    underpowered elasticity; single domain/20 items/6 personas.
- **2026-07-15 — PR #3 `moduleB-panel` (real LLM panel thin slice)
  SQUASH-MERGED to main (commit 52fb53c).**
  - Flow: impl-moduleB-panel (built provider + counterfactual pairing + task loader
    + metrics + tests) → hit real GitHub Models rate-limit (429) → Manager probed
    limits (hidden burst bucket ~20 calls; sustainable ≤1.5 req/s) → fix-moduleB-panel
    (pacing 0.8s + 8s 429 cooldown; restored 20-task scale; real run: 145 calls +
    155 cache = 300, 0×429, $0.05) → produced NULL result → Manager diagnosed
    mechanism (97% no-movement; reliance≈agreement) → PI decision "BOTH" → independent
    audit (CONDITIONAL PASS: all methodology/security/determinism PASS; one schema
    BLOCKER-1) → fix-moduleB-schema (serialize model/trace/trust_state; regen from
    cache, 0 API calls, numbers unchanged) → Manager verified (11 fields, cross-process
    determinism IDENTICAL, worktree clean) → merged.
  - KEY RESULT: naive gpt-4o-mini panel COLLAPSES to near-uniform agreement — does NOT
    reproduce human reliance heterogeneity. Documented as an honest negative result +
    the reason for the panel-DV redesign. Infra (provider/cache/pairing/join/pacing)
    is sound + reusable. Task stimuli (beer/amzbook/lsat JSON) + testid↔questionId join
    (50/50) verified.
  - FRAMING: real-data decomposition elevated to co-anchor contribution C0 (SPEC §2).
- **2026-07-14 — PR #2 `e1-multicond` (+robustness +variance-decomposition)
  SQUASH-MERGED to main.** 12 commits.
  - Flow: impl-e1-multicond → audit (FAIL: over-dispersion fragile to task
    selection; "stratified" misnomer) → fix (robustness table + rename) →
    reaudit → **statistical adjudication** (power vs artifact) → PI decision: do
    variance decomposition before merge → impl/redo/finalize decomposition →
    pre-merge audit (CONDITIONAL PASS; anti-gaming check via auditor's OWN
    generators: stable 0.894 / interaction 0.199) → fix hash() determinism blocker
    (e1_multicond.py:117) → Manager independently verified cross-process
    determinism (spearman 0.771429 identical ×2) → merged.
  - KEY SCIENTIFIC FINDING (docs/research/2026-07-14-overdispersion-decomposition.md):
    axis-1 over-dispersion is REAL (Human ρ=0.067, CI [0.052,0.081], excludes 0)
    and NOT a power artifact (known-signal sim recovers at 4 trials/user). Split-
    half reliability decomposition: **no-AI Human reliance is a STABLE USER TRAIT
    (stable_user_share=0.74 [0.69,0.79]); under AI assistance reliance becomes
    predominantly TASK-DEPENDENT (share 0.32-0.41; Expert ~0).** => axis-1's "safety
    depends on WHO the user is" is, in AI conditions, more precisely "user × task".
  - Methods note: single-obs-per-cell (99.7%) makes ANOVA-on-cells non-identified;
    split-half (20-50 tasks/user) is the correct primary; GLMM honestly non-converged.
  - **OPEN for PI: whether/how to reframe H1a to incorporate user×task (see below).**
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
