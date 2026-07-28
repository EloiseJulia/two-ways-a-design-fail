# DECISIONS.md — Chronological, paper-oriented change log

> One entry per non-trivial decision/change: **date · what changed · from → to · WHY
> (evidence/finding) · paper implication**. Reconstructed from git history + PROGRESS +
> Manager memory. Honest about confirmed vs open. Newest context at the bottom of each phase.
> Refs are squash-merge commits on `main` unless noted.

---

## Phase 0 — Setup & Gates (2026-07-14)

### D0.1 — Project scaffold + single-source-of-truth docs
- **What:** Created SPEC.md / INTERFACES.md / PROGRESS.md skeletons; adopted the AI-native
  multi-session workflow (worktrees, draft PRs, audit-gated merges). Commits bf6ff0d, 3632d88.
- **Why:** Multi-session subagents with no shared memory need a frozen design + interface contract
  to avoid code that won't fit together.
- **Paper implication:** Establishes the methods-paper discipline (reproducibility, run manifests).

### D0.2 — Gate 1 (data) CLEARED
- **From → To:** unverified datasets → verified real per-trial URLs.
- **What/Why:** Independently verified (HTTP 200 + headers) Bansal CHI'21
  (`uw-hai/Complementary-Performance`, 66,040 rows) and Lu&Yin CHI'21
  (`ZhuoranLu/Trustworthy-ML`, 9,031 rows). Also found Bansal ships **task stimuli**
  (`task-examples/*.json`: text X, truth Y, pred/conf, expert/system highlights). Commits
  5c9b879, d7ee878.
- **Paper implication:** §7 datasets are real + downloadable; the panel can form a genuine
  System-1 anchor from actual task text (not just ids).

### D0.3 — Gate 2 (batch API) CLEARED; Gate 3 (PI ownership) CLEARED
- **What/Why:** GitHub Models is a programmable batch endpoint (verified). PI owns scientific
  correctness; independent hostile + §4.5 methodology audit is the merge gate; nothing merges on
  "it runs". Commit 37ed051.
- **Paper implication:** Enables the LLM panel; commits to a "能跑 ≠ 正确" rigor standard.

---

## Phase 1 — Axis-1 reality + the C0 decomposition (2026-07-14 → 15)

### D1.1 — Thin vertical slice v0 (PR #1, e5a257b)
- **What:** Bansal → canonical schema → **beta-binomial over-dispersion** (separates true
  between-user over-dispersion from binomial noise) + genuine mean-predictor baseline + synthetic
  stub → E1.
- **Why:** Prove the data→metrics chain on real data before a live panel; the DV must defeat the
  "Bernoulli平庸化" attack (variance = p(1−p)).
- **Paper implication:** Validates the axis-1 DV machinery (§5 E1, §8 stats). The 2-condition r=±1
  was flagged DEGENERATE (plumbing only) — an early rigor save.

### D1.2 — Axis-1 over-dispersion is REAL and not a power artifact (PR #2, 9ac818f)
- **From → To:** "over-dispersion might be noise/task-selection" → **REAL signal**.
- **Why:** Full-data Human ρ=**0.067 [0.052,0.081]** excludes 0; a known-signal simulation shows
  the estimator is unbiased even at 4 trials/user (collapse at few tasks is task-dependence, not
  power loss); null sim stays at floor.
- **Paper implication:** H1a axis-1 has a real human target; the estimator is defensible (§8).

### D1.3 — Variance decomposition → H1a refined to "user×task under AI" (PR #2; b48ab2b)
- **From → To:** H1a "safety depends on WHO the user is" → **"under AI assistance, depends on
  USER × TASK"**.
- **Why:** Split-half reliability (PRIMARY, well-identified because 20–50 tasks/user; ANOVA-on-cells
  is NON-identified at 99.7% single-obs cells): no-AI stable_user_share **0.74** [0.69,0.79];
  AI-assisted **0.32–0.41** (Expert ~0). GLMM did not converge (reported honestly).
- **Paper implication:** Sharpens axis-1; motivates a **task-spanning** panel. Became the basis of C0.

### D1.4 — Decomposition ELEVATED to co-anchor C0 (fabc19f) — later reversed (see D3.5)
- **What/Why:** The trait→user×task finding is real-data, novel, and owes nothing to the sim, so it
  was promoted to a co-equal contribution to de-risk dependence on the (then-unbuilt) panel.
- **Paper implication (at the time):** Two anchors — C0 (real data) + C1 (panel). **NOTE: reversed
  after Lu&Yin + discriminator; see D3.x.**

---

## Phase 2 — The real panel: null → redesign (2026-07-15)

### D2.1 — Module B real LLM panel; discovered per-model behavior (PR #3, 52fb53c)
- **What:** Implemented `GitHubModelsProvider` (hashlib cache) + dual-system counterfactual pairing
  (System-1 frozen across the UI pair); ran small (5 personas × 20 beer tasks × gpt-4.1-mini).
- **Why/Finding:** Result = **NULL**. Manager diagnosed (from raw responses, audit-confirmed): 97%
  of cells the agent never moves from its own System-1; "reliance" ≈ agreement not adoption; persona
  disagreement ≈ 0. Not a bug — a real compliance/anchoring collapse on easy binary sentiment.
- **Paper implication:** The naive panel does NOT reproduce human reliance heterogeneity → the
  panel-centric claim is at risk; a DV/condition redesign is required. Merged as honest infra +
  negative result. (Also fixed an audit BLOCKER: serialize all AgentResponse fields.)

### D2.2 — PI decision "BOTH": redesign the panel DV AND lean on real-data C0
- **What/Why:** Given the null, keep the panel (redesign it) and elevate the real-data decomposition.
- **Paper implication:** Sets up PR #4 (redesign) and the C0 generalization tests (PR #5/#6).

### D2.3 — Panel DV redesign resolves the collapse (PR #4, 9caebc5)
- **From → To:** unconditional reliance (≈ agreement) → **conflict-conditioned reliance** (only
  System-1 ≠ AI trials, isolating true AI influence); + data-driven HARD-item selection + stronger
  persona conditioning + a WRONG-AI dark condition.
- **Why/Finding:** conflict rate **3%→43.3%**; conflict-conditioned reliance control 0.327 →
  treatment 0.481; per-persona spread **0.11–0.56** (personas now diverge); within-task elasticity
  **+0.19 (p=0.17, n=11 — underpowered)**; **axis-2 wrong-AI over-reliance 0.325**; persona p5 shows
  **0%** wrong-AI adoption under coercive framing (**dark-pattern-BACKFIRE** lead).
- **Paper implication:** C1 becomes viable — the mechanism CAN produce heterogeneity + a first
  axis-2 reading. Establishes the conflict-conditioned DV as the axis-1 measure and seeds E4.

### D2.4 — Item selection uses AI-side EXOGENOUS properties (not the human DV)
- **What/Why:** Hard items chosen by AI-wrong / low-confidence / high human-reliance-VARIANCE (to
  LOCATE heterogeneity) — but human outcomes/reliance are NEVER in agent prompts or used as a
  predictor. Disclosed.
- **Paper implication:** Pre-empts a leakage attack; item selection ≠ label leakage (§11/§4.5).

---

## Phase 3 — Does C0 generalize? Lu&Yin + discriminator → demotion (2026-07-15)

### D3.1 — Replicate the decomposition on Lu&Yin (PR #5, 4364d54)
- **Finding:** Lu&Yin AI-assisted reliance is **TRAIT-STABLE: stable_user_share 0.80** [0.77,0.83]
  (0.79 conflict-conditioned) — near Bansal's no-AI 0.74, NOT its AI 0.32–0.41.
- **Why it matters:** The AI-assisted user×task share is **NOT universal**.
- **Caveat (honest):** between-dataset comparison is CONFOUNDED — Lu&Yin has NO no-AI arm (cannot
  test C0's within-dataset contrast); differs in sequential-feedback, domain homogeneity, AI accuracy.
- **Paper implication:** C0 HELD (not refined/demoted) pending a mechanism test; Manager corrected a
  subagent's premature "design-dependent C0" wording to an honest boundary observation.

### D3.2 — Zero-quota DISCRIMINATOR: Bansal on Lu&Yin-matched subsets (PR #6, 50250e6)
- **What:** Re-decompose Bansal AI-assisted split-half on subsets matched to Lu&Yin's regime
  (single domain, AI-accuracy band, tasks/user).
- **Finding:** **INCONCLUSIVE.** beer/amzbook single-domain shares ≈ 0.00 are **CEILING artifacts**
  (between-user SD ≈ 0.05 → split-half ≈ 0 mechanically; uninterpretable). Only lsat (SD ≈ 0.14) is
  interpretable: **0.46 [0.31,0.59]**, rising only partway toward 0.80 with a CI OVERLAPPING the 0.33
  baseline. Gap remains confounded/unresolved.
- **Rigor event:** the impl subagent produced an OVERSTATED "PERSISTS → clean demote" verdict;
  Manager independently computed the between-user SDs, caught the ceiling artifact, and corrected to
  INCONCLUSIVE; the audit independently reproduced the SDs and confirmed.
- **Paper implication:** C0's mechanism cannot be isolated; regime-dependence stays an open question.

### D3.5 — C1 → PRIMARY; C0 → DEMOTED; sequential-feedback → OPEN QUESTION (PI-approved, PR #6)
- **From → To:** {C0 co-anchor + C1 core} → **C1 PRIMARY; C0 = Bansal-specific SUPPORTING finding;
  sequential-feedback = explicit open question (future §4.1)**.
- **Why:** C0 did not generalize (D3.1) and the mechanism test was inconclusive (D3.2). The panel
  two-axis triage (C1), with real preliminary evidence from PR #4, is the more defensible spine.
- **Paper implication:** Reframes the whole contribution section (SPEC §2). Honest: C0 stays as a
  Bansal observation with a caveat, not a general law.

---

## Phase 4 — Axis-2 formalization + compute reality (2026-07-15 → 16)

### D4.1 — E4 axis-2 sensor + PLACEBO compliance baseline (PR #7, DRAFT, not merged)
- **What:** 4 conditions (control / faithful / placebo / wrong-AI). Placebo = present-but-content-free
  explanation to isolate the **compliance floor** (reliance from presence vs value). Formal axis-2
  `over_reliance_level` on wrong-AI + a placebo-baselined "compliance-adjusted" reading.
- **Status:** Code + 8 offline tests done; real run PARTIAL (193/450 cached on gpt-4.1-mini). H3 to
  read out: control < placebo < faithful.
- **Paper implication:** Builds the second axis (H1b/H3, E4) — currently the weaker half of the
  two-axis claim; must be finished for C1.

### D4.2 — GitHub Models per-model DAILY cap discovered; provider HARDENED
- **From → To:** assume per-minute limit only → **per-user-PER-MODEL DAILY cap, TIER-DEPENDENT**
  (strong ~200/day, mini ~500/day; header `UserByModelByDay`, ~19h reset).
- **Why:** Runs repeatedly "hung" — the provider was honoring a ~13–19h Retry-After. Hardened to
  **fail fast** when cooldown > 120s and to CACHE every completed call (resumable for free). Also
  fixed the experiment to pass the config model name (was hardcoded).
- **Paper implication:** Constrains all panel-scale planning; motivates the multi-family + Azure
  strategy (D4.3). Model-mix must be reported per-model (confound).

### D4.3 — Quota strategy: multi-family panel as a SCIENTIFIC upgrade + Azure fallback
- **What/Why:** The daily cap is per-model, so spreading the panel across model families multiplies
  budget AND is exactly the cross-family triangulation SPEC §4.2 wants. Azure AI Foundry (no cap,
  ~$15–45 for a full run) is the clean single-session unlock. `docs/plans/2026-07-15-quota-strategy.md`.
- **Paper implication:** Turns a compute constraint into cross-model robustness (§4.2). Frozen model
  set = a preregistration item.

### D4.4 — Hybrid: exploratory pilot THEN Azure, with a strict rigor firewall
- **What/Why (PI):** Run a free multi-family GitHub pilot NOW for pipeline de-risk + power-N ONLY,
  kept SEPARATE from confirmatory; do NOT tune conditions/τ/model-set on any peeked axis-1 effect;
  FREEZE the confirmatory prereg BEFORE the run.
- **Action:** `docs/plans/preregistration-axis1.md` LOCKED **2026-07-15T09:23:55Z** (H1a, model set,
  5 conditions, DV, baselines, BH α=0.05) BEFORE the pilot ran; commit 032b373.
- **Paper implication:** Clean exploratory/confirmatory separation — a headline methods-rigor point.

### D4.5 — AzureFoundryProvider built + merged (PR #9, 5cd179b)
- **What:** Drop-in `ModelProvider` for Azure OpenAI + Foundry (two api styles), env creds,
  replicated hashlib cache (deployment in key → no collision), 22 offline mock tests, setup doc.
  Audit PASS.
- **Paper implication:** Uncapped confirmatory path is READY; awaits PI Azure creds.

### D4.6 — Pilot run FAILED to yield a power estimate → provider-stability limitation
- **From → To:** planned 3-family exploratory read → **only noisy non-OpenAI data**.
- **Why/Finding:** gpt-4.1-mini skipped (capped, shared with E4); **Llama-3.3-70B / Phi-4 on GitHub
  Models produced 60s timeouts, HTTP 500s, and unparseable System-2 outputs (defaulted to 0)**. No
  `results/axis1_pilot.json`. Multi-provider loop given **skip-on-cap** resilience (bba48dc).
- **Paper implication:** Documented provider-stability limitation; the power-N purpose is UNMET — get
  N from a clean pass on stable models.

### D4.7 — AMEND confirmatory model set to STABLE OpenAI family, day-batched (PI, prereg amendment)
- **From → To:** confirmatory {gpt-4o, Llama-3.3-70B, Phi-4} → **{gpt-4o, gpt-4.1-mini}** on GitHub
  Models, DAY-BATCHED; non-OpenAI = exploratory-only. Logged **2026-07-16T02:29:50Z** in the prereg
  §2 amendment.
- **Why:** Invokes the pre-committed PIPELINE-only exclusion rule (D4.6 instability) — a pipeline
  diagnostic, NOT any axis-1 effect (no clean effect existed). "Keep going free" without blocking on
  Azure.
- **Paper implication:** Confirmatory becomes capability-tier diversity WITHIN OpenAI (strong vs
  small); multi-VENDOR triangulation deferred to Azure. Must report per-model (model-mix confound).

### D4.8 — Pilot MERGED as exploratory infra (PR #8, ff69ce0) — Manager #3
- **What:** Merged the axis-1 multi-family pilot (5-condition LIME renderers + multi-provider
  skip-on-cap loop + power-analysis readout) as **EXPLORATORY infrastructure only**. The stale
  branch (merge-base predated PR #9) was first brought up to date with `main` — a squash-merge of
  the raw branch would have DELETED `azure_provider.py`, `DECISIONS.md`, the handoff docs, and the
  prereg doc (caught before merge). Independent audit PASS; Manager verified additive-only diff, no
  ground-truth leakage in any renderer or the System-1 prompt, hashlib-only, System-1 frozen, 9/9
  offline tests, `results/axis1_pilot.json` correctly ABSENT.
- **Why:** Preserve the reusable renderers + resilient multi-provider loop and the documented
  provider-stability limitation (D4.6) without asserting any axis-1 effect.
- **Paper implication:** §5 methods/infra + the provider-stability limitation are now on `main`.
  Power-N (prereg §8) remains PENDING — to be filled from a CLEAN pass on the stable OpenAI set.
  Non-blocking test-quality nits (cross-*model* freeze test trivial via constant mock; the
  "cross-process" determinism test runs in-process) logged for firm-up before the confirmatory run.

### D5.1 — Bansal renderer fidelity corrected before confirmatory H1a (PR #10)
- **From → To:** token-count heuristics (`Single`=first 1 span, `Double`=first 2 spans,
  `Adaptive`=ad hoc `conf > 0.8`/top-N) → faithful Bansal label-explanation semantics:
  `class1` is POSITIVE evidence, `class0` is NEGATIVE evidence, and `class{pred}` is the
  predicted-class explanation. `Conf.+Single` now shows ALL predicted-label LIME spans;
  `Conf.+Double` shows ALL class0+class1 LIME spans; adaptive conditions use fixed dataset
  median-confidence thresholds (`beer`=0.892, `amzbook`=0.889), with high confidence showing
  Single and low confidence showing Double. Expert adaptive now parses the raw single-quoted
  expert phrase spans rather than classless cleaned text.
- **Why:** `research-bansal-conditions` + paper quotes established that the old top-N/token-count
  reading was a misinterpretation: Bansal's conditions vary which LABELS' evidence is shown, not
  how many highlighted tokens are shown. The fixed thresholds come from paper §4.2 and Manager's
  data inspection (Beer median confidence 0.892 on the 50-item stimulus set).
- **Paper implication:** The confirmatory cross-condition rank test now renders the Bansal UI
  conditions faithfully before H1a. **Cache implication:** this changes the rendered prompt for
  `Conf.+Adaptive (Expert)`, so E4's 193-call cache is INVALIDATED and E4 must re-run fresh on the
  corrected renderer. PR #4's exploratory numbers used the old renderer and must be described as
  exploratory/old-renderer results, not as corrected-renderer evidence.

### D5.2 — E4 placebo re-matched to the (shorter) faithful explanation (PR #7, on E4 branch)
- **From → To:** E4's fixed ~390-char, 5-sentence placebo (matched to the OLD long full-expert-text
  faithful) → a single generic content-free sentence (~140 chars) length-matched to the NEW faithful
  `Conf.+Adaptive (Expert)` render (beer expert phrase ~84-186 chars, median ~128, measured on the
  50-item stimulus set).
- **Why:** The D5.1 fidelity fix shortened the faithful Expert explanation to a class-filtered phrase.
  The compliance-floor control (H3: control < placebo < faithful) must isolate PRESENCE-of-explanation
  from a text-LENGTH confound, so the placebo has to track the faithful length. The old 390-char
  placebo was 2-3× longer than the corrected faithful (a length confound). The new placebo stays
  content-free (no task-specific/decision-relevant content, identical across all items → no leakage).
  `test_placebo_length_matched` tightened (fixture now populates `expert_highlights_html`; ratio < 2.5).
- **Paper implication:** Keeps the E4 axis-2 / H3 compliance-floor measurement clean under the
  corrected renderer. To be re-validated by the fresh E4 run + independent §4.5 methodology audit
  (the placebo design is a documented researcher DoF; length-matched-to-median is the stated choice).
### D5.3 — BLIND panel↔human correspondence readout implemented before confirmatory panel (PR #11)
- **What:** Added the pre-specified H1a secondary readout: cross-condition Spearman correlation
  between panel disagreement per Bansal AI condition and the fixed real-human over-dispersion target
  in `results/e1_multicond.json`, with permutation p-value, bootstrap CI, Pearson secondary readout,
  n<3 degenerate guard, and a ceiling-excluded sensitivity analysis.
- **Why:** Operationalizes the preregistered §1/§4 panel-validity claim before any confirmatory
  panel data exists. The `Conf.+Adaptive (Expert)` human target has near-zero excess variance at a
  high mean reliance rate, so it is flagged as a likely ceiling artifact rather than treated as an
  interpretable low-overdispersion condition.
- **Paper implication:** The confirmatory run only plugs panel disagreement into a frozen analysis.
  This does **not** change H1a or the preregistration; it implements an already-specified secondary
  analysis and makes the ceiling-artifact sensitivity explicit.

---

## Phase 5 — Positioning lock (2026-07-16)

### D5.4 — PAPER POSITIONING LOCKED (PI decision, timestamp 2026-07-16T06:15:38Z)
- **Locked BEFORE the confirmatory axis-1 run** — precisely so the confirmatory RESULT cannot bias
  the positioning (a preregistration-of-framing move; parallels the τ/N freeze discipline).
- **Headline contribution = a METHODOLOGICAL REFRAME, not an effect-size claim:**
  (1) treat cross-user **variance / over-dispersion** in reliance as the *safety-relevant* dependent
  variable (vs the prior literature's mean over-reliance effect); (2) a **two-axis pre-deployment
  triage protocol** — axis-1 (UI design → user-sensitive reliance over-dispersion) + axis-2
  (systematic over-reliance on a WRONG AI) — that SCREENS human–AI decision interfaces before an
  expensive human study; **validated by panel↔human correspondence on two real datasets (Bansal,
  Lu&Yin) + preregistration.**
- **The empirical signal is the TARGET the method detects, NOT a boast.** Do NOT overclaim the small
  magnitude (e.g. ρ≈0.067); a small ρ motivates the calibrated threshold / abstention rule, it does
  not undermine the method. Report confirmatory results regardless of outcome.
- **Axis-2 dark-pattern BACKFIRE stays a tentative SUPPORTING lead** — promoted to a lead claim ONLY
  if E4 on the FAITHFUL renderer (D5.1/D5.2) reaches significance.
- **Head-on defense against the "LLM-simulated users are unreliable proxies" attack** (Seshadri et
  al., ICLR'26; Santurkar; CoMPosT homogeneity critiques): we TRIAGE designs that need a human study;
  we do NOT claim to PREDICT individual humans. Calibration + the conflict-conditioned DV
  (System-1≠AI only) + cross-model triangulation are the technical defenses.
- **Why:** Verified novelty analysis (`docs/research/2026-07-16-novelty-positioning.md`, 22 primary
  cites): the dual-axis pre-deployment triage via a real-log-calibrated synthetic panel has no direct
  prior art (closest neighbor Rastogi 2022/23 optimizes routing, not UI-safety triage).
- **Paper implication:** Sets the framing of the whole paper (SPEC §2 title/abstract/intro spine).
  Consistent with the existing C1-PRIMARY structure — a sharpening, not an upheaval. C0 stays a
  Bansal-specific supporting finding; sequential-feedback stays an open question.

### D5.5 — BLIND confirmatory Axis-1 analysis pipeline implemented (PR #12)
- **What:** Added the pure offline `twdf.analysis.confirmatory_axis1` pipeline and thin
  `twdf.experiments.confirmatory_axis1` runner/config for the powered H1a run, before any
  confirmatory panel data exists.
- **Why:** Locks the analysis mechanics blind: conflict-conditioned DV, beta-binomial
  over-dispersion, within-task paired estimator, PR #11 panel↔human correspondence, bootstrap CIs,
  permutation p-values, BH α=0.05, and per-model reporting for `{openai/gpt-4o, openai/gpt-4.1-mini}`.
- **Baselines:** Adds random, prompt-only, single-model, and rational-Bayesian null baselines while
  reusing the existing mean-predictor baseline and over-dispersion/statistical helpers.
- **Paper implication:** Implements H1a/prereg without changing it. τ_disp/τ_level remain UNFROZEN;
  null or wrong-signed outcomes remain valid fully populated confirmatory results.

### D5.6 — Atomic UI feature space implemented for Module D calibration (PR #13)
- **What:** Added `twdf.features.ui_features` with a frozen `UIFeatureVector`, deterministic
  extraction for all 7 Bansal/panel UI conditions, stable `FEATURE_NAMES`, numeric array encoding,
  and standardized feature-space distance.
- **Why:** SPEC §4.3 requires UI designs to be represented as atomic, interpretable
  cognitive-interaction features so Module D can later learn τ_disp/τ_level and E5 can measure OOD
  distance in feature space rather than over whole rendered UI surfaces.
- **Guardrail:** This does **not** learn, freeze, or tune τ. Features are computed only from visible
  prediction/confidence/explanation/framing and condition semantics, never from `ground_truth`.
- **Paper implication:** Enables §5/E5 feature-distance analyses and the §6 dual-threshold
  calibration/abstention protocol while preserving the preregistration discipline that thresholds
  remain unfrozen until the calibration step.

### D5.7 — Module D calibration/triage machinery implemented; τ still UNFROZEN (PR #14)
- **What:** Added `twdf.calibration.thresholds` with `fit_thresholds`, `triage`,
  `ThresholdModel`, `TriageDecision`, precision-at-recall reporting, feature-space OOD/novel-dim
  abstention, and a `freeze_thresholds` mechanism.
- **Why:** Operationalizes SPEC §6's dual-threshold pre-deployment screen: either axis over
  threshold sends a design to human study, both low can release, and uncertainty/OOD/reversal
  regions abstain to the safe default. The fitting rule favors high recall because a miss means
  releasing a dangerous design, which is worse than a false alarm.
- **Guardrail:** τ VALUES remain **UNFROZEN** in this PR. Freshly fitted models have
  `timestamp=None`; no frozen-τ artifact is written to `results/`. Real freezing is a later,
  deliberate timestamped step after calibration data including E4 axis-2 are available.
- **Paper implication:** The protocol machinery now exists for Module D/E5 without violating the
  preregistered discipline that τ_disp/τ_level must be frozen only once, before threshold results.

### D5.8 — E3 LOIO generalization harness implemented leakage-safe (PR #15)
- **What:** Added the pure offline `twdf.analysis.loio.loio_generalization()` core plus the
  `twdf.experiments.e3_loio` public entry points for leave-one-item-out axis-1 generalization.
- **Why:** Implements SPEC §5 E3 pass criteria: held-out direction hit rate against a 0.5 binomial
  baseline and predicted-vs-actual Spearman ranking with a seeded permutation p-value.
- **Guardrail:** The held-out item is passed to predictors only as a target-free view; fitting sees
  target-bearing train items only, excluding the held-out item. This prevents fitting
  normalization/threshold/model parameters on the held-out target. n<3 is flagged degenerate.
- **Paper implication:** Locks the leakage-safe E3 harness mechanics without freezing τ or changing
  the preregistration.

### D5.9 — E5 reliability layer implemented without freezing τ (PR #16)
- **What:** Added `twdf.analysis.reliability` with ECE/MCE reliability bins, a generalization
  gradient/failure-region map over feature distance, difficulty, or persona, a measured reliable
  radius, and measured abstention-rate reporting.
- **Why:** SPEC §5/E5 and §6.3–6.4 require the method to quantify where panel predictions are
  trustworthy, identify high-error regions, and report how often the safe-default abstention rule
  fires on a design sample.
- **Guardrail:** The implementation reuses PR #13 `feature_distance` and PR #14
  `triage`/`ThresholdModel`; it does **not** reinvent feature distance, learn a new triage rule, or
  freeze τ. Fresh threshold models remain unfrozen until the later logged calibration step.
- **Paper implication:** E5 can now report calibrated reliability, an applicability radius, and the
  measured ABSTAIN/HUMAN_STUDY/RELEASE mix supporting the §6.3 abstention rule without changing the
  preregistered dual-threshold protocol.

### D5.10 — E4 axis-2 SIGN-INVERSION bug caught + fixed; corrected result REVERSES the earlier read (PR #7)
- **What (bug):** The `Wrong-AI (dark)` renderer DISPLAYS `1 - ai_pred` (the flipped/wrong label), but
  `real_panel.py` stored `trace['ai_advice'] = ai_pred` (UN-flipped) and `_compute_reliance` scored
  against it; `over_reliance_level` then measured `final == ai_pred`. Because displayed = 1 − stored,
  the axis-2 adoption score was the exact COMPLEMENT of the truth.
- **How caught:** The independent audit of the E4 run reproduced adoption against the DISPLAYED prompt
  label (not the stored field) and flagged the inversion; the Manager's own first re-derivation had
  been fooled by trusting the same stored field. **The two-layer gate (independent audit + Manager
  re-derivation) worked** — logged as the 3rd caught rigor event (cf. D2.1, D3.2).
- **Fix:** added `bansal_tasks.displayed_ai_advice(task, ui_condition)` as the single source of truth
  (Wrong-AI → `1 - ai_pred`, else `ai_pred`), used by BOTH the renderer and `real_panel` for `relied`
  + `trace['ai_advice']` + `ai_correct`; added a REGRESSION test that drives the real `run_panel` path
  with a compliance-following provider and asserts `over_reliance_level == 1.0` (bug gave 0.0). No new
  API calls — prompts unchanged, so re-run is cache-backed; the agents' recorded decisions were always
  against the correctly-displayed label, only the scoring reference was wrong.
- **Corrected result (from → to):** axis-2 wrong-AI over-reliance **0.156 (buggy "backfire") →
  0.844 raw adoption of the coercive label**. Disentangling the manipulation (the flipped label
  coincides with ground truth in 48/90 trials): the CLEAN axis-2 signal — adoption of a GENUINELY
  wrong coercive AI (`displayed != ground_truth`, n=42) — is **0.690 (29/42), binomial vs 0.5 p=0.0098**;
  p5 = 100%; low between-persona spread (0.012) ⇒ near-uniform ("uniformly lethal") over-reliance. Added
  `over_reliance_on_wrong` / `n_truly_wrong` to the metric so we report the clean number, not the
  inflated raw one. **H3 compliance floor is UNAFFECTED** (only the Wrong-AI condition had the flip):
  control 0.273 < placebo 0.291 = faithful 0.291, both permutation tests non-significant (null/underpowered).
- **Paper implication:** The axis-2 empirical read REVERSES — from a (buggy) backfire to a **strong,
  significant over-reliance on a coercive wrong AI**. Per D5.4, axis-2 backfire was tentative pending a
  significant E4; the corrected E4 instead shows significant over-RELIANCE (clean 0.69, p<0.01), which
  strengthens the two-axis claim (to be re-decided with the PI). CAVEATS (honest boundary): underpowered
  (gpt-4.1-mini, 6 personas × 15 items, 42 truly-wrong trials, single beer domain); the dark manipulation
  flips `ai_pred` rather than showing a guaranteed-wrong `1 - ground_truth`, so ~half the displayed labels
  were coincidentally correct — a documented design refinement for any future preregistered one-shot
  axis-2 test. PR#4's exploratory old-renderer axis-2 (0.325) used the same buggy scoring and is
  superseded.

---

### D5.11 — CONFIRMATORY AXIS-1 PREREGISTRATION FROZEN (N=20), timestamp 2026-07-17T01:37:00Z
- **Frozen BEFORE the confirmatory run** (the exploratory power-N pass — `results/powern_axis1.json`,
  gpt-4.1-mini, 6 items, seed 999 — is SEPARATE and EXCLUDED from the confirmatory). What is frozen:
  - **Model set:** `{openai/gpt-4o, openai/gpt-4.1-mini}` (prereg §2 amendment), per-model reported (no pooling).
  - **Conditions:** the 5 Bansal AI conditions (Conf./Single/Double/Adaptive/Adaptive(Expert)).
  - **DV + estimators:** conflict-conditioned reliance; beta-binomial between-user over-dispersion;
    PRIMARY = difficulty-controlled within-task counterfactual difference; SECONDARY = cross-condition
    Spearman (panel disagreement vs human over-dispersion, 5 points).
  - **Baselines to beat:** random, mean-predictor, prompt-only, single-model, + rational-Bayes null (each
    with a bootstrap CI). **Stats:** bootstrap over (personas×seeds×models), permutation, BH α=0.05.
  - **N (power target):** **6 personas × 20 items × 5 conditions × 2 models × 1 seed (42)**; item seed 42
    (distinct from power-N seed 999). Analysis code pre-implemented BLIND in PR #12.
- **Why N=20:** the 6-item power-N was underpowered by construction (within-task d≈0.028, permutation
  p=1.0, over-dispersion≈0); naive 80%-power projection at that effect ≈21 items/model, so N=20 is the
  first fairly-powered pre-registered axis-1 test. PI: reject N=10 (underpowered → not a credible null).
- **τ stays UNFROZEN** (Module-D calibration is a separate later timestamped step; §7).
- **Commitment:** report REGARDLESS of outcome. Going in clear-eyed that the likely result is a weak/null
  axis-1, carried honestly by the significant axis-2 (D5.10) + the two-axis protocol — NOT spun as a win.
- **Compute:** free day-batched ({gpt-4o ~200/day, gpt-4.1-mini ~500/day} → ~4 days, auto-scheduled),
  resumable via hashlib cache; may be routed through Azure (hours) if the PI provisions creds.

### D5.12 — Clean guaranteed-wrong axis-2 condition + powered one-shot runner (PR #17)
- **What:** Added `"Wrong-AI-GT (dark)"`, a new coercive dark condition that displays
  `1 - ground_truth` via the same `displayed_ai_advice(task, ui_condition)` single source of truth
  used by both the renderer and `real_panel` (`trace['ai_advice']`, `ai_correct`, `relied`). The
  existing `"Wrong-AI (dark)"` (`1 - ai_pred`) remains unchanged for E4 continuity.
- **Why:** D5.10 showed significant-but-preliminary axis-2 over-reliance, but the old flipped-prediction
  dark condition was genuinely wrong only on the subset where `1 - ai_pred != ground_truth`. The new
  condition makes every trial a clean wrong-AI trial, so raw adoption equals clean adoption on wrong
  advice.
- **Rigor guard:** Showing `1 - ground_truth` is a deliberate experimenter construction of a wrong
  recommendation. The agent prompt shows only a recommendation label plus coercive responsibility
  framing; it does **not** say "ground truth", "truth", or that the label is derived from the answer,
  so there is no ground-truth leakage to the agent.
- **Powered run:** Added `twdf.experiments.axis2_powered` + `configs/axis2_powered.yaml` for a
  PREREGISTERED one-shot pending Manager freeze: `{openai/gpt-4o, openai/gpt-4.1-mini}` × 6 personas ×
  20 beer items (item seed 2024) × `Conf.`, `Conf.+Placebo`, `Conf.+Adaptive (Expert)`,
  `Wrong-AI-GT (dark)`. Analysis reuses E4-style over-reliance and placebo-floor adjustment, reporting
  per-model and pooled panel results, per-persona adoption/spread, a bootstrap/sign-flip permutation
  test for adoption > placebo floor, and a binomial test vs 0.5. Output is
  `results/axis2_powered.json` labeled `CONFIRMATORY-PENDING-PREREG`.
- **Paper implication:** Solidifies axis-2 from significant-but-preliminary (D5.10) into a powered,
  clean, preregistered one-shot design that the Manager will run and report regardless of outcome.

### D5.13 — POWERED AXIS-2 PREREGISTRATION FROZEN, timestamp 2026-07-17T02:51:26Z
- **Frozen BEFORE the run** (the code is built + independently audited in PR #17; no live axis-2-powered
  run has happened). This is the PI's "optional preregistered one-shot axis-2" (upside to solidify
  axis-2 from significant-but-preliminary). What is frozen:
  - **Design:** 4 conditions `Conf.` (control) / `Conf.+Placebo` / `Conf.+Adaptive (Expert)` (faithful) /
    **`Wrong-AI-GT (dark)`** (displays `1 - ground_truth` = a GUARANTEED-wrong coercive AI, removing the
    E4 flip-vs-truth coincidence). 6 personas × **20 items** (beer, item seed 2024, distinct from
    confirmatory 42 / power-N 999) × **2 models {gpt-4o, gpt-4.1-mini}** × seed 42.
  - **Primary axis-2 measure:** panel over-reliance level = adoption of the displayed wrong label on the
    Wrong-AI-GT condition (raw == clean, since all trials are truly-wrong); compliance-adjusted =
    over-reliance − placebo compliance floor. **Significance:** permutation/bootstrap that adoption
    exceeds the placebo floor (p + CI) + binomial vs 0.5. Per-model reported (no pooling as the primary).
  - **Scoring** against the DISPLAYED label via `displayed_ai_advice` (per the D5.10 fix); System-1
    frozen across conditions; item selection uses AI-side exogenous props only (no human-outcome/gt
    leakage into agent prompts — verified in audit).
- **Commitment:** report REGARDLESS of outcome. Runs AFTER the confirmatory axis-1 (compute sequencing;
  both share the daily per-model caps). τ stays UNFROZEN. `config: configs/axis2_powered.yaml`.
- **Why:** axis-2 (D5.10) is the strongest empirical result but was underpowered/single-model with a
  diluted "wrong AI"; this powered, clean, multi-model, preregistered test is the honest way to
  solidify it (per PI directive: maximize panel/method rigor before the E6 human study).


### D5.14 — EXPLORATORY stratified correspondence + confirmatory robustness readout (PR #18)
- **What:** Added `twdf.analysis.stratified_correspondence` for condition × AI-side difficulty-stratum
  correspondence: human beta-binomial over-dispersion vs panel disagreement, Spearman with permutation
  p and bootstrap CI, per-cell low-variance/ceiling flags, and n<3 guards. Also added a pure JSON
  `confirmatory_robustness()` readout for per-model stability and leave-one-condition-out sensitivity.
- **No prereg change:** This is explicitly **EXPLORATORY** and does **not** change frozen D5.11's
  confirmatory five-condition design. It answers reviewer-power/fragility attacks (A3/A4) without
  moving the confirmatory goalposts.
- **Leakage guard:** strata use AI-side exogenous properties only (default `ai_conf`; low confidence =
  harder). Human outcomes, human reliance, and ground truth are forbidden as stratifiers.
- **Paper implication:** Adds a higher-power robustness view (≈ condition × tercile points) and an honest
  sensitivity readout around the confirmatory result while preserving the preregistration firewall.

### D5.15 — CROSS-GENERATION robustness/triangulation ARM preregistered (Azure gpt-5.x), timestamp 2026-07-17T03:47:26Z
- **What (PI decision, path A):** the PI's company Azure has only the gpt-5.x family (gpt-5.2, gpt-5.3-codex,
  gpt-5.4, gpt-5.4-pro), NOT the frozen {gpt-4o, gpt-4.1-mini}. So the PRIMARY confirmatory axis-1 (D5.11)
  + powered axis-2 (D5.13) STAY on the free GitHub {gpt-4o, gpt-4.1-mini} (unchanged, coherent with E4/PR#4
  calibration). Azure gpt-5.x is used as a SECONDARY, preregistered **cross-generation robustness/
  triangulation arm** — the SAME design/N/analysis run on **gpt-5.2 (small/strong) + gpt-5.4 (strong)**
  (gpt-5.3-codex excluded = code model; gpt-5.4-pro excluded unless PI opts in = premium).
- **Why:** directly answers the strongest reviewer attacks A2/A8 (is the two-axis panel signal just one
  model's prompt noise? does it generalize across model generations?). If the signal holds on frontier
  gpt-5.x too → strong cross-model evidence; if it collapses → an honest finding about model-capability
  dependence.
- **Preregistered BEFORE running** (no gpt-5.x panel result seen). Frozen: same 5 axis-1 conditions +
  4 axis-2 conditions, 6 personas, N=20 items (SAME seeds as the primary so items match), same DV/
  estimators/baselines/significance. This is a ROBUSTNESS arm, explicitly SECONDARY to the primary
  (gpt-4o/mini) result — not a replacement.
- **Honest risk (pre-registered):** frontier models on the easy beer-sentiment task may reach near-ceiling
  System-1 accuracy → very low System-1↔AI conflict → the conflict-conditioned DV could have few trials /
  collapse (echoing the PR#3 naive-panel collapse). Reported regardless.
- **Provider substitution:** `AzureFoundryProvider` (PR #9), Azure OpenAI/Foundry; may need adaptation for
  the gpt-5.x API (e.g. `max_completion_tokens`, no `temperature`, reasoning params) — a live cred/
  connectivity check (~cents) precedes any run. Cost of the gpt-5.x arm is bounded by the fixed call
  volume (~2,640) with a `call_budget` cap; per-token gpt-5.x pricing TBD from the Azure portal.
- **Implementation note (PR #19):** both confirmatory runners now select the provider by config:
  absent/default remains `GitHubModelsProvider`; `provider.type: "azure"` builds
  `AzureFoundryProvider` per model/deployment. Added `configs/confirmatory_axis1_azure_gpt5.yaml`
  and `configs/axis2_powered_azure_gpt5.yaml` with matched item seeds and distinct `_gpt5` outputs.
  Offline mocked tests cover wiring and existing Azure provider behavior; live gpt-5.x execution still
  awaits PI Azure creds plus the planned connectivity/contract check.
- **τ stays UNFROZEN.**

### D5.16 — Whole-codebase bug hunt: three latent metric bugs fixed (no merged result changed)
- **Date:** 2026-07-17 · **What changed:** fixed three latent bugs surfaced by an independent
  hostile bug-hunt subagent, before any touched a confirmatory/merged result.
- **From → to:**
  1. `overdispersion.py::betabinom_overdispersion` — users all pinned at the reliance boundary
     (mean_p∈{0,1}) hit a `0/0→NaN→clamp` path and returned **ρ≈0.999** ("maximal over-dispersion")
     when the truth is **ρ=0** (no between-user variance). → Added a `binomial_variance<=0` boundary
     guard returning ρ=0. This is the SAME failure family as the D5.10 sign-inversion (a boundary/NaN
     that INVERTS the metric's meaning).
  2. `ui_features.py` — `wrong_ai` and `_has_authority_cue` recognized only `"Wrong-AI (dark)"`, not the
     preregistered `"Wrong-AI-GT (dark)"` condition (D5.13). → both now include `Wrong-AI-GT (dark)`.
  3. `overdispersion.py::condition_correlation` — the degenerate/`n<3` check ran AFTER the
     permutation+bootstrap loops, so a constant input or `n<3` could emit `np.percentile([])`
     crashes / meaningless stats. → Added an EARLY degenerate/constant-input guard that returns null
     stats + a "PLUMBING ONLY" note BEFORE any resampling.
- **WHY / evidence:** reproduced each bug; betabinom all-(0,10)/all-(10,10) → 0.999 (wrong) vs
  genuine half-0/half-10 → high (correct, kept); confirmed **no already-merged result is affected**:
  no `rho:0.99x` artifact in any `results/*.json`, and no merged result depends on `Wrong-AI-GT`
  ui-features or `condition_correlation` on degenerate input. 9 new regression tests
  (`tests/test_metric_boundary_fixes.py`); 27 pass across boundary+metrics+ui_features suites.
- **Implication for the paper:** strengthens the A10 "we caught our own bugs" rigor story (now a
  SECOND self-caught class beyond D5.10) and adds a new **A11 limitation** (item-selection /
  correspondence circularity — disclosed, NOT a code bug; mitigation = held-out item correspondence
  + E6). Affects §methods rigor narrative + Limitations; changes NO reported number.
- **τ stays UNFROZEN.**

### D5.17 — Axis-2-anchor reframe formally CONSIDERED and DEFERRED (gated on confirmatory axis-1)
- **Date:** 2026-07-17 · **What changed:** decision on paper framing — **NO change made** (deliberate hold).
- **From → to:** current positioning (D5.4: axis-1 over-dispersion as the headline safety DV, axis-2
  backfire tentative) → **considered** pivoting to an axis-2-anchored framing (axis-2 wrong-AI /
  dark-pattern detector as the primary validated contribution, axis-1 demoted to boundary/secondary),
  as recommended by the independent `idea-eval-sota` assessment → **DECIDED: keep current framing for
  now; do NOT reframe until the preregistered confirmatory axis-1 (D5.11, N=20) has actually run.**
- **WHY / evidence:** idea-eval-sota (docs/research/2026-07-17-idea-eval-sota-assessment.md) argues the
  axis-2 preliminary result (clean truly-wrong 0.69, binomial p=0.0098) is the paper's strongest empirical
  shot and axis-1 is likely weak/null, so an axis-2 anchor raises accept odds. **PI ruling:** reframing on
  a *predicted* (peeked/expected) axis-1 null would violate our own preregistration discipline (never tune
  framing on an un-run effect); the honest path is to run the confirmatory to completion, report it
  regardless, THEN decide the anchor from the realized result. Sequencing > optics.
- **Implication for the paper:** contribution structure stays as-is pending data; the axis-2-anchor option
  (+ a stripped axis-2-only E6, + amzbook 2nd domain, + HCOMP-interim venue) is now an ON-THE-TABLE,
  evidence-gated decision to revisit the moment `results/confirmatory_axis1.json` lands. No claim/threshold
  changed. τ stays UNFROZEN.

### D5.18 — CROSS-VENDOR robustness arm PREREGISTERED (ghc-api proxy), timestamp 2026-07-17T11:20:39Z
- **Date:** 2026-07-17 · **What changed:** the cross-generation robustness arm (was D5.15 = Azure
  gpt-5.x, blocked on creds) is **reframed and rescoped** to a **cross-VENDOR** arm run on the local
  `ghc-api` GitHub Copilot API proxy (OpenAI-compatible, no token, effectively unlimited).
- **From → to:** D5.15 planned OpenAI-only gpt-5.2/gpt-5.4 via Azure (single-vendor, single-generation,
  never ran — no creds) → **FROZEN cross-vendor trio: `gpt-5.5` (OpenAI) + `claude-sonnet-4.5`
  (Anthropic) + `gemini-2.5-pro` (Google)**, all via the proxy. This upgrades a single-vendor
  robustness check into genuine **cross-vendor triangulation**.
- **WHY / evidence:** (1) PI opened `ghc-api` (verified 2026-07-17: all three models return content;
  gpt-5.5/gemini-2.5-pro are reasoning models needing `max_completion_tokens` + large budget), removing
  the GitHub Models daily cap and the Azure dependency at zero cost. (2) The independent idea-eval-sota
  assessment ranks cross-vendor agreement as the highest-credibility upgrade against reviewer attacks
  **A2/A8** ("the panel just re-encodes GPT's priors" / silicon-sampling homogeneity). One vendor cannot
  answer that; three can.
- **FROZEN design (before any run):** mirror the primaries exactly — N=20 **matched** items (item
  seed=42, same as `confirmatory_axis1.yaml`), 6 personas, same 5 UI conditions (axis-1) and the same
  Wrong-AI-GT dark condition (axis-2). **Per-model, NO pooling.** Estimators unchanged: per-model
  within-task reliance + beta-binomial over-dispersion + conflict-conditioned reliance DV (axis-1);
  `over_reliance_on_wrong` via `displayed_ai_advice()` single-source-of-truth + binomial test on truly-
  wrong trials (axis-2). **Axis-2 is the PRIMARY robustness target** (it is the anchor significant
  result); axis-1 secondary.
- **Decision rule (frozen):** robustness = does the sign/significance of each axis **replicate across
  ≥2 of 3 vendors**? Report per-vendor; make NO meta-pooled claim beyond "replicates / does not."
- **Preregistered honest risks:** (a) **frontier ceiling** — gpt-5.5/claude/gemini may near-ceiling
  System-1 on easy beer → few conflict trials → axis-1 conflict-conditioned DV may be under-determined;
  report per-model conflict-trial counts, do not hide a collapse. (b) **reasoning-model empties** —
  mitigated by `min_completion_tokens=4096` + an empty-content retry/raise guard (never cache an empty
  panel answer); residual empties reported as missing data. (c) **provider provenance** — proxy `gpt-*`
  may differ from GitHub Models snapshots; that is exactly WHY this is a SEPARATE robustness arm, NOT a
  top-up of the frozen primary D5.11 arm (which is still finished on GitHub Models via daily reset).
- **Reporting:** REGARDLESS of outcome — replication strengthens A2/A8; a vendor-specific collapse is an
  honest model-capability-sensitivity boundary finding (also publishable).
- **Implication for the paper:** converts the single-vendor limitation (A5-adjacent credibility ceiling)
  into a cross-vendor robustness claim; feeds §robustness + the reviewer-rebuttal A2/A8 evidence plan.
  Does NOT alter any frozen primary (D5.11/D5.13). τ stays UNFROZEN.

### D5.19 — P0 BUG: panel decision parser silently fabricated (0,0.5) — FIXED (PR #22)
- **Date:** 2026-07-17 · **What changed:** `real_panel._parse_decision_response` /
  `_parse_decision_with_confidence` silently defaulted any response that failed strict
  `json.loads` to `decision=0, confidence=0.5` — fabricating a decision for valid but
  verbose answers. Caught by a read-only watcher during the cross-vendor run.
- **Root cause:** strict `json.loads` on a NON-brace-balanced regex match threw
  `JSONDecodeError` on (a) literal control chars / bare newlines in `reasoning`, (b) ```json
  code fences, (c) nested braces, then jumped to `except` and returned the default WITHOUT
  trying the regex fallback. Same silent-corruption family as the E4 sign-inversion (D5.10)
  and the betabinom boundary (D5.16).
- **Scope (measured on 3959 cached responses):** claude-sonnet-4.5 **25/1140 (2.2%)**,
  gemini-2.5-pro 1/490, gpt-5.5 0/1140, **openai/gpt-4o 0/403, openai/gpt-4.1-mini 0/786**.
  PRIMARY models had ZERO failures → **E4 / e1_multicond / confirmatory (merged) are NOT
  contaminated** (independently confirmed byte-identical pre/post fix). The bug only bit the
  IN-FLIGHT cross-vendor arm (claude/gemini), which had not been recorded/merged.
- **Fix:** strip fences → brace-BALANCED JSON extraction → `json.loads(strict=False)` →
  regex fallback → **raise `PanelParseError` (never fabricate)** when no 0/1 decision is
  extractable. Provider cache stores RAW responses (not the parsed default), so re-running
  re-parses correctly and SELF-HEALS — no cache wipe needed. Validated: fixed parser raises
  on **0/3959**, all 26 prior failures recover their true decision. 11 regression tests.
  Independent audit PASS (reproduced 26→0, primary byte-identical, no fabrication path).
- **Open follow-up (non-blocking):** no caller catches `PanelParseError`, so a future
  anomalous response could abort `run_panel` and (since its raw is cached) wedge resume.
  Current live risk is zero (0/3959). Tracked to add caller-level record-missing/exclude.
- **Implication for the paper:** (1) the cross-vendor arm MUST be re-run/re-derived on the
  corrected parse before any D5.18 readout (in progress); (2) strengthens the process-rigor
  story (a THIRD self-caught silent-corruption class after D5.10/D5.16, this one caught by an
  independent watcher) for reviewer-rebuttal A10. Changes NO merged number. τ stays UNFROZEN.

### D5.20 — CROSS-VENDOR AXIS-2 result: over-reliance signal does NOT replicate (frontier collapse), timestamp 2026-07-17T17:06:30Z
- **Date:** 2026-07-17 · **What changed:** first D5.18 cross-vendor readout (axis-2, the PRIMARY
  robustness target) is IN. Result: the strong axis-2 wrong-AI over-reliance seen on gpt-4.1-mini
  does **NOT** replicate across the frontier trio.
- **Numbers (Manager independent re-derivation from raw traces, displayed advice recomputed as
  `1-ground_truth` — NOT trusting stored fields; matches pipeline exactly, `stored_advice_mismatch=0`,
  n=120 dark trials/model):**
  - gpt-5.5: over-reliance **0.300**, binomial vs 0.5 p=1.0 (significantly BELOW chance — the frontier
    model RESISTS the guaranteed-wrong AI)
  - claude-sonnet-4.5: **0.492**, p=0.61 (at chance)
  - gemini-2.5-pro: **0.525**, p=0.32 (at chance)
  - vs PRIMARY gpt-4.1-mini preliminary: 0.69, p=0.0098 (strong).
- **Decision rule (D5.18) outcome:** replication requires sign/significance in ≥2 of 3 vendors →
  **0/3 significant. NON-REPLICATION.** This is exactly the PREREGISTERED frontier-ceiling risk
  (D5.15/D5.18): capable models can judge easy beer sentiment themselves, so they don't follow a
  wrong AI.
- **BUT a robust sub-finding:** the trusting-novice persona (p5: domain_skill 0.2, ai_literacy 0.8)
  stays HIGH everywhere — claude 0.95, gemini 1.00, gpt-5.5 0.60 — i.e., dark-pattern susceptibility
  CONCENTRATES in a persona even when the model-mean collapses (a heterogeneity/axis-1-flavored signal
  that DOES survive across vendors). Report this honestly; do not bury it or oversell it.
- **Rigor:** parser fix (D5.19) was applied — 0 parse failures this run; result is post-fix clean.
  Independent audit of the cross-vendor result PENDING (combined with axis-1). Report REGARDLESS.
- **Implication for the paper (MAJOR, PI-level):** this directly UNDERCUTS the idea-eval recommendation
  to anchor the paper on axis-2 as a "validated cross-vendor dark-pattern detector" (that anchor
  assumed the signal generalizes; it does not on frontier models for this task). The honest contribution
  shifts toward: axis-2 over-reliance is **model-capability-dependent** (strong in smaller models,
  resisted by frontier models on easy tasks), while **persona-level susceptibility is robust across
  vendors**. Escalated to PI as a framing decision. Does NOT alter any frozen primary. τ UNFROZEN.

### D5.21 — CROSS-VENDOR AXIS-1 result: panel↔human over-dispersion correspondence NULL/weak across all vendors
- **Date:** 2026-07-17 · **What changed:** second D5.18 readout (axis-1) is in. The panel↔human
  per-condition over-dispersion correspondence does NOT hold on any of the three vendors.
- **Numbers (Manager independent re-derivation, Spearman over the 5 UI conditions; matches reported
  exactly):** claude-sonnet-4.5 rho = **-0.20** (p≈0.75), gemini-2.5-pro **-0.31** (p≈0.61),
  gpt-5.5 **+0.10** (p≈0.87). All non-significant; two are NEGATIVE. n=5 conditions = essentially no
  power (known A3/A4 limitation). Dropping one condition swings gpt-5.5 to +0.63 (n=4) — confirms the
  A4 fragility, not a signal.
- **Panel over-dispersion magnitudes (conflict-conditioned):** claude 0.178, gemini 0.221, gpt-5.5
  **0.021** (near-zero). gpt-5.5 panel disagreement 0.003-0.019 = near-HOMOGENEOUS — the preregistered
  frontier-ceiling risk materializing (a capable model gives near-identical reliance across personas on
  easy beer). Cross-model rank agreement 0.775 (descriptive only, not a primary claim).
- **Rigor:** post parser-fix (D5.19), 0 parse failures; both independent re-derivations (axis-1 Spearman,
  axis-2 over-reliance) MATCH the pipeline exactly; no sign-inversion. Combined independent audit
  dispatched (axis-1 + axis-2). Report REGARDLESS.
- **Implication (combined cross-vendor picture, PI-level):** BOTH axes fail to show the hoped-for
  cross-vendor signal — axis-2 over-reliance does not replicate on frontier (D5.20), axis-1
  correspondence is null/weak/fragile here. The cross-vendor arm, intended to STRENGTHEN the
  contribution vs reviewer A2/A8, instead shows the panel signals are **model-capability-dependent**.
  This is a pivotal, honest, preregistered-risk-materializing result that reshapes the contribution
  (see D5.20 escalation). Does NOT alter any frozen primary (D5.11 GH-Models confirmatory still pending
  its gpt-4o daily-reset finish). τ stays UNFROZEN.

### D5.22 — CONTRIBUTION PIVOT (PI-approved): "model-capability-dependence of panel signals" + persona-robust susceptibility
- **Date:** 2026-07-18 · **What changed:** headline contribution reframed, driven by the D5.20/D5.21
  cross-vendor evidence (independent audit PASS). PI-approved option **A+B**.
- **From → to:** D5.4/outline positioned the paper as a **validated two-axis pre-deployment triage /
  (cross-vendor) dark-pattern detector**, with axis-2 as the anchor empirical result → **NEW main line:
  "LLM-panel deployment-screening signals are MODEL-CAPABILITY-DEPENDENT"** — smaller/older models
  (gpt-4.1-mini) reproduce documented human failure modes (strong wrong-AI over-reliance 0.69, real
  reliance heterogeneity), while frontier models RESIST wrong AI and HOMOGENIZE (gpt-5.5 over-reliance
  0.30 below chance, near-zero panel disagreement 0.012; claude/gemini at chance). **Therefore the panel
  model is a critical, under-appreciated design choice, and a single-frontier-model panel can MASK real
  deployment risks.** Plus the robust positive sub-finding (**B**): dark-pattern susceptibility
  **concentrates in a trusting-novice persona across ALL vendors** (p5 = 0.60/0.95/1.00) even when the
  model-mean collapses — the panel robustly localizes WHICH user profiles a coercive interface endangers.
- **WHY / evidence:** D5.18 cross-vendor arm (gpt-5.5 + claude-sonnet-4.5 + gemini-2.5-pro), preregistered
  and audited (both axes reproduced from raw traces, mismatch=0, parser-fix-clean): axis-2 0/3 replicate
  (D5.20), axis-1 correspondence null/weak/fragile (D5.21). The arm intended to answer reviewer A2/A8
  instead produced a deeper, honest result. This is the results-driven reframe the PI empowered
  (cf. the D5.17 "gate framing on data" decision — the data are now in).
- **Implication for the paper:**
  - **Contribution structure** (rewritten in `docs/paper/outline.md`): (1) the capability-dependence
    finding as the primary empirical contribution + a cautionary methods result on silicon-sampling
    (engages Seshadri ICLR'26 head-on with NEW evidence); (2) persona-conditioned susceptibility as the
    robust positive detector-flavored result; (3) the two-axis protocol + over-dispersion-as-DV as the
    method; (4) the rigor spine (preregistration, blind analysis, THREE self-caught silent-corruption
    bugs D5.10/D5.16/D5.19). The "validated cross-vendor detector" claim is RETIRED (not supported).
  - **Reviewer rebuttals:** A2/A8 ("just GPT's priors / homogeneity") flip from a threat we defend to a
    phenomenon we CHARACTERIZE and own.
  - **E6 motivation sharpened:** the key open question becomes "WHICH model's panel (if any) tracks real
    human reliance heterogeneity" — exactly what the human capstone answers.
  - No frozen primary altered; τ UNFROZEN. Cross-vendor audit PASS recorded (D5.20/D5.21).

### D5.23 — SAME-PROVIDER CAPABILITY LADDER preregistered (proxy OpenAI family), timestamp 2026-07-18T01:34:15Z
- **Date:** 2026-07-18 · **What changed:** to remove a confound in the D5.22 capability-dependence
  headline, add a within-provider, within-config **capability ladder** run on the ghc-api proxy.
- **WHY:** the D5.22 claim currently contrasts gpt-4.1-mini (GitHub Models, E4/axis2_powered config)
  vs the frontier trio (proxy, cross-vendor config) — provider AND config differ, so "capability" is
  confounded with provider/config. A reviewer would (rightly) attack this. Fix: run an OpenAI-family
  ladder on the SAME provider (proxy) and the SAME config as the cross-vendor arm.
- **FROZEN design (before running):** models = **gpt-4o-mini → gpt-4.1 → gpt-4o → gpt-5.5** (small→
  frontier, all OpenAI, all via proxy). Identical protocol to D5.18 (matched item seeds axis-1=42 /
  axis-2=2024, same 6 personas, same UI conditions incl. Wrong-AI-GT dark; per-model NO pooling; same
  estimators). gpt-5.5 reuses its cached cross-vendor responses (identical cache key) so it is the
  shared anchor between the ladder and the cross-vendor arm. Non-frontier tiers use standard max_tokens;
  gpt-5.5 uses max_completion_tokens+min 4096 (reasoning). Outputs: `results/*_capladder.json`.
- **Prediction (preregistered, report regardless):** if capability-dependence is real, axis-2 wrong-AI
  over-reliance should DECREASE from gpt-4o-mini → gpt-5.5, and panel disagreement (axis-1) should shrink
  toward the frontier. A flat/again-null curve would WEAKEN the D5.22 headline — report it honestly
  either way. Note: the proxy has no exact `gpt-4.1-mini`; the GitHub-Models gpt-4.1-mini primary remains
  a separate cross-provider point (not part of this same-provider ladder).
- **Implication for the paper:** turns the capability-dependence claim from a provider-confounded contrast
  into a clean same-provider dose-response curve (core evidence for contribution #1, D5.22). Does NOT
  alter any frozen primary. τ UNFROZEN.

### D5.24 — CAPABILITY LADDER RESULT (same-provider): capability-dependence is REAL but NUANCED (not a clean monotone). Audit PASS.
- **Date:** 2026-07-18 · **What changed:** the D5.23 same-provider OpenAI ladder (gpt-4o-mini → gpt-4.1
  → gpt-4o → gpt-5.5, all on the proxy, identical config) completed; independent audit PASS (both curves
  reproduced from raw responses, mismatch=0, parser-clean, no leakage; gpt-5.5 rows byte-identical to the
  cross-vendor cache). This REFINES the D5.22 headline with the real (messier) shape.
- **Axis-2 over-reliance on the guaranteed-wrong AI (n=120/model), same provider/config:** gpt-4o-mini
  **0.500** (chance), gpt-4.1 **0.600** (binomial p=0.018, the ONLY significant over-relier), gpt-4o
  **0.433** (n.s.), gpt-5.5 **0.300** (significantly BELOW chance, p<0.001 — resists). **This is NOT a
  monotone capability curve** (0.50→0.60→0.43→0.30, up then down). Over-reliance is **model-idiosyncratic**;
  the *smallest* proxy model (gpt-4o-mini) sits at chance, so the earlier "smaller models over-rely" read
  is MODEL-SPECIFIC (it was gpt-4.1-**mini** on GitHub Models, and gpt-4.1 here — NOT a size law; gpt-4o-mini
  does not replicate it). The one reliable axis-2 regularity: **frontier gpt-5.5 resists**.
- **Axis-1 heterogeneity (same provider/config):** conflict over-dispersion 0.32/0.47/0.47/**0.021**; mean
  panel disagreement 0.110/0.157/0.096/**0.012**. The frontier (gpt-5.5) **cleanly collapses to near-
  homogeneity** vs the elevated non-frontier tiers — the cleanest capability-dependence signal in the paper.
  Panel↔human correspondence (n=5) remains non-significant for ALL models (+0.41/+0.80/-0.21/+0.10).
- **Robust invariant (B):** persona p5 (novice-trusting) is the single highest-adopting persona in EVERY
  model (axis-2 dark adoption 1.00/1.00/1.00/0.60) — persists (attenuated) even at the resistant frontier.
- **Refined framing (updates D5.22, does NOT overturn it):** "model-capability-dependence" must be stated
  precisely — (i) axis-1 HETEROGENEITY magnitude collapses at the frontier (clean, capability-linked);
  (ii) axis-2 WRONG-AI over-reliance is MODEL-IDIOSYNCRATIC with reliable frontier RESISTANCE (not a size
  monotone); (iii) persona-level susceptibility is the robust cross-model invariant; (iv) panel↔human
  correspondence stays underpowered/null (n=5) regardless of model. Do NOT sell a clean dose-response
  curve — the honest story is model-idiosyncrasy + frontier resistance + persona robustness.
- **Implication for the paper:** outline §5 updated with the same-provider curve; contribution #1 (D5.22)
  refined to the precise claim above. This de-confounds the headline (same provider/config) AND supplies
  the nuance that protects against a reviewer over-claim attack. Does NOT alter any frozen primary. τ
  UNFROZEN.

  ### D5.25 — FROZEN CONFIRMATORY axis-1 (D5.11) COMPLETE: H1a is NULL on both models (audit PASS)
  - **Date:** 2026-07-18 · **What changed:** the frozen GitHub-Models confirmatory (D5.11, N=20, gpt-4o +
    gpt-4.1-mini) finally completed after multi-day gpt-4o daily-cap batching; independent audit PASS
    (numbers reproduced from raw cache offline, parser-clean, prereg-conformant, no leakage, not spun).
  - **Result (Manager re-derivation == audit == summary):**
    - gpt-4.1-mini: conflict over-dispersion 0.086, mean panel disagreement 0.028, panel↔human
      cross-condition correspondence rho **-0.205** (BH adj p 0.766, n.s.), within-task permutation BH adj
      p 0.248 (n.s.).
    - gpt-4o: over-dispersion 0.364, disagreement 0.125, correspondence rho **+0.410** (BH 0.498, n.s.),
      within-task BH 0.498 (n.s.).
    - ALL baselines NOT beaten (mean-predictor/random/prompt-only/single-model/Bayes-null); within-task CI
      includes 0. **H1a panel↔human over-dispersion correspondence is NULL on both models.**
  - **WHY / interpretation (honest, per D5.4/D5.11 "report regardless, do not spin"):** this is the
    pre-expected weak/null axis-1. n=5 conditions has ~no power. It is the **4th independent null on the
    panel↔human correspondence** (GH-Models gpt-4o + gpt-4.1-mini here, plus the cross-vendor trio D5.21 and
    the capability ladder D5.24) — the panel↔human PREDICTIVE link is unestablished across EVERY model
    tested. Consistent with D5.24 model-idiosyncrasy: on axis-1, gpt-4o is more heterogeneous (0.36) than
    gpt-4.1-mini (0.086).
  - **Implication for the paper:** the confirmatory-of-record is now on the books as an honest null (§5).
    It REINFORCES the D5.22/D5.24 framing (capability-dependence; correspondence unvalidated) and makes the
    E6 human study the decisive, sharply-motivated validator ("which model's panel, if any, tracks real
    human reliance heterogeneity"). Does NOT alter the capability-dependence contribution. Schedule #3
    (the day-batch grinder) is STOPPED. τ stays UNFROZEN.

### D5.26 — amzbook 2nd-DOMAIN arm PREREGISTERED (cross-domain generalization test), timestamp 2026-07-18T13:08:04Z
- **Date:** 2026-07-18 · **What changed:** preregister a 2nd-domain replication on **amzbook** (Amazon
  book-review sentiment) of the cross-vendor (D5.18) and capability-ladder (D5.23) arms, to test whether
  the D5.22/D5.24 findings GENERALIZE across domains (answers reviewer A5 "single domain (beer)").
- **Infra:** PR #23 (audit PASS) generalized the beer-hardcoded item selection to a `domain` param
  (backward-compatible — beer seed-42 IDs byte-identical), added `load_domain_tasks`, an amzbook-only
  human anchor `results/e1_multicond_amzbook.json`, and 4 configs.
- **FROZEN design (before any run):** identical protocol to beer — 6 personas, same UI conditions
  (axis-1: 5 conditions; axis-2: incl. Wrong-AI-GT dark), matched item seeds (axis-1=42, axis-2=2024),
  per-model NO pooling, same estimators, proxy provider (throttled). Models: cross-vendor trio
  (gpt-5.5 + claude-sonnet-4.5 + gemini-2.5-pro) AND the capability ladder (gpt-4o-mini → gpt-4.1 →
  gpt-4o → gpt-5.5). Axis-1 correspondence uses the amzbook-only anchor (n=5, low-power as before).
  Configs: `{axis2_powered,confirmatory_axis1}_{crossvendor,capladder}_amzbook.yaml`; outputs `*_amzbook.json`.
- **Preregistered predictions (report REGARDLESS):** if capability-dependence + persona-robustness
  GENERALIZE, on amzbook we expect (a) axis-2 over-reliance model-idiosyncratic with reliable frontier
  RESISTANCE (gpt-5.5 low/below chance), (b) axis-1 panel heterogeneity COLLAPSE at the frontier, (c)
  persona p5 (trusting-novice) the highest-susceptible across models. A DIFFERENT pattern on amzbook is
  an honest domain-boundary finding (also publishable). amzbook AI base accuracy differs from beer, so
  absolute over-reliance levels may shift — the QUALITATIVE model-ordering / frontier-resistance /
  persona-robustness is the generalization test, not the absolute numbers.
- **Implication for the paper:** if it generalizes → strong cross-domain robustness for contribution #1/#2
  (kills A5); if not → a characterized domain boundary. Either way strengthens the honest story. Does NOT
  alter any frozen primary. τ UNFROZEN.

### D5.27 — amzbook 2nd-DOMAIN RESULT: capability-dependence + persona-robustness GENERALIZE across domains (audit PASS). Manager re-derivation complete.
- **Date:** 2026-07-19 · **What changed:** the D5.26 amzbook arm COMPLETED (arm 4, axis-1 capability
  ladder `confirmatory_axis1_capladder_amzbook`, finished 2026-07-19T13:12Z; arms 1–3 already done). All 4
  configs now have results. Manager independently re-derived both axes from RAW responses (sign-correct
  axis-2, panel disagreement + conflict presence axis-1). **Independent audit PASS**
  (`.prompts/audit-amzbook-d527.md`): all 4 claims reproduced from raw within rounding; sign-check clean
  (dark frac=1.000 / non-dark 0.400); 0 D5.19 sentinels (480/480 + 360/360 parsed, 0 mismatch); no leakage;
  no pooling; binomial gpt-4.1 p=6.7e-4 ABOVE, gpt-5.5 p=2.0e-15 BELOW chance.
- **CROSS-DOMAIN GENERALIZATION HOLDS — all 3 preregistered predictions replicate on amzbook** (Manager
  re-derivation; compare beer D5.24 in parentheses):
  - **(a) axis-2 wrong-AI over-reliance = model-idiosyncratic + frontier resistance.** Capability ladder
    dark-condition over-reliance (n=120/model): gpt-4o-mini **0.475** (beer 0.500), gpt-4.1 **0.658**
    (0.600) — the SOLE significant over-relier, gpt-4o **0.475** (0.433), gpt-5.5 **0.150** (0.300) —
    significantly BELOW chance = resists. Same qualitative shape (up-then-down, gpt-4.1 peak, frontier
    resists); NOT a size monotone (gpt-4o-mini at chance). Sign-check verified: dark condition
    `ai_advice == 1 − ground_truth` at frac=1.000; non-dark 0.400 (natural error). E4 sign-inversion
    trap avoided.
  - **(b) axis-1 heterogeneity collapses at the frontier.** Mean panel disagreement across 5 conditions:
    0.124 / 0.192 / 0.108 / **0.015** (beer 0.110/0.157/0.096/0.012); conflict over-dispersion estimate
    0.343 / 0.577 / 0.440 / **0.000** (beer 0.321/0.472/0.469/0.021). gpt-5.5 collapses to near-zero on
    BOTH domains — even cleaner on amzbook (0.000). NON-frontier ordering also replicates
    (gpt-4.1 > gpt-4o-mini > gpt-4o). Frontier is NOT a no-conflict artifact: gpt-5.5 has **215/600
    conflict trials present** — genuine resistance/homogenization (preregistered risk addressed).
  - **(c) persona-p5 (novice-trusting) robustness.** Highest-adopting persona in EVERY ladder model
    (dark adoption 1.00 / 1.00 / 1.00 / 0.40), matching beer (1.00/1.00/1.00/0.60) — robust, attenuated
    at the resistant frontier.
- **HONEST caveat (correspondence is UNINFORMATIVE on amzbook, not an informative null):** amzbook axis-1
  panel↔human correspondence is rho=0.0 / p=1.0 for ALL models, but this is DEGENERATE — the human-side
  per-condition over-dispersion on the amzbook anchor (`results/e1_multicond_amzbook.json`) is near-zero
  and near-constant (aligned_pairs human_rho ≈ 1e-6…3e-3), so there is no cross-condition variation to
  correlate (estimator note: "reported as null rather than failing"). amzbook therefore adds NO
  correspondence evidence (unlike beer, whose human anchor at least varied). This REINFORCES the standing
  conclusion: panel↔human correspondence is unvalidated at n=5 regardless of domain → only **E6** closes it.
- **Implication for the paper:** kills reviewer A5 ("single domain (beer)") on the panel-side findings —
  the capability-dependence (frontier resistance + axis-1 collapse) and persona-robustness now REPLICATE
  across two domains. Does NOT extend the correspondence claim (amzbook uninformative there). Outline §5 +
  reviewer-rebuttals A5 updated. Does NOT alter any frozen primary. τ UNFROZEN. Audit PASS (2026-07-19,
  read-only code-review, 4/4 claims reproduced, no red flags).

### D5.28 — E6-stripped (axis-2-only, N≈40 Prolific) DESIGN drafted for PI review (design-only, NOT preregistered)
- **Date:** 2026-07-19 · **What changed:** per PI directive (chose "draft stripped E6, no recruitment"),
  drafted `docs/plans/e6-stripped-axis2-design.md` — the fastest-path human validation that tests only
  the paper's strongest, cross-domain-robust positives: H1 (coercive wrong-AI over-coerces real humans,
  within-subject Dark vs Faithful/Placebo), H2 (trusting-novice human index = most susceptible → validates
  persona-p5 localization), H3 (WHICH ladder model's panel best tracks humans — predicting gpt-4.1 >
  frontier gpt-5.5, i.e. the most-capable panel is the least human-faithful screener).
- **WHY stripped/axis-2-only:** axis-1 correspondence is null in all 4 synthetic runs AND degenerate on
  the amzbook human anchor (D5.27) → N≈40 cannot test it fairly; axis-2 (over-reliance + persona) is the
  robust positive. Directly answers reviewers A1/A8 for the core claim at minimum cost (~£250–350, one-shot).
- **Status:** DESIGN ONLY. NOT preregistered, NO recruitment, NO IRB yet. The full 6-interface N≈60 E6
  (`docs/plans/e6-human-study-design.md`) remains the eventual capstone. Freeze §§1–4 + IRB BEFORE any
  data. Does NOT alter any frozen primary. τ UNFROZEN. Awaiting PI review of the design.

### D5.29 — AXIS-2 ROBUSTNESS HARDENING (compute-free, existing data): persona-p5 iron-clad; frontier resistance is the rock; gpt-4.1 over-reliance softened under BH. Audit PASS.
- **Date:** 2026-07-20 · **What changed:** three compute-free hardening analyses on the existing axis-2
  dark-condition data (6 unique models × 2 domains = 12 cells; gpt-5.5 de-duplicated, its capladder/
  crossvendor dark rows verified byte-identical). New tracked analysis `scripts/analysis/axis2_robustness.py`
  → `results/axis2_robustness.json`. Independent audit **PASS** (recomputed from raw; de-dup + sign
  firewall verified). PI-requested (analyses ①②③).
- **① persona-p5 (trusting-novice) susceptibility is now STATISTICALLY IRON (contribution #2):** p5 is the
  STRICT single highest-adopting persona in **12/12** cells (sign-test vs chance 1/6: p=4.6e-10). Per-cell
  Fisher (p5 vs pooled other-5, one-sided) is significant in ALL 12 after BH (max BH p=0.0023). Pooled GEE
  logistic (adopt~is_p5, clustered by cell) odds ratio **15.0** (95% CI 5.8–38.8, p=2e-8). p5-minus-others
  gap mean +0.526, min +0.300 (holds even at the resistant frontier). This upgrades the persona claim from
  "numerically highest" to "significantly most-susceptible across 6 models × 2 domains."
- **② ordering agreement vs rate idiosyncrasy (sharpens contribution #1, answers A2/A8):** aggregate wrong-AI
  RATE is model-idiosyncratic (spread: beer 0.30–0.60 range 0.30; amzbook 0.15–0.658 range 0.51), while the
  persona RISK ORDERING is largely shared — beer independent-vendor (gpt-5.5/claude/gemini) mean pairwise
  Spearman **0.87** (min 0.82); within-domain beer 0.81. HONEST attenuation: amzbook ordering agreement is
  weaker (within 0.58, indep-vendor 0.50) and gpt-5.5's cross-domain ordering is only 0.28 — because the
  frontier compresses non-p5 personas toward the floor, making the sub-top ranking noisy. So the robust
  claim is precisely: *the TOP of the risk ordering (who is most endangered = p5) is universal (12/12), and
  the full ordering agrees strongly off-frontier/on beer but attenuates at the amzbook frontier.* Not
  "one model's prompt noise" (A2) — independent vendors agree on the ordering.
- **③ stats hygiene surfaced an HONESTY CORRECTION:** BH across the 12 per-cell binomial tests → only
  **amzbook gpt-4.1 (0.658, BH p=0.0027)**, **amzbook gpt-5.5 (0.150, BH p=2.4e-14)**, **beer gpt-5.5
  (0.300, BH p=8.3e-5)** survive. **beer gpt-4.1 (0.600) does NOT survive BH (p=0.106)** — it was reported
  nominally significant (uncorrected p=0.018) in D5.24. CORRECTION to the framing: *frontier RESISTANCE
  (gpt-5.5, below chance, both domains, all between-model contrasts p<0.005) is the ROCK-SOLID axis-2
  regularity; gpt-4.1 over-reliance is model-idiosyncratic and BH-significant only on amzbook (nominal on
  beer)* — so "the sole significant over-relier" must be stated as amzbook-BH-significant / beer-nominal,
  NOT a clean cross-domain significant effect. Between-model contrasts confirm idiosyncrasy: gpt-4.1 vs
  gpt-4o Fisher p=0.014 (beer) / 0.006 (amzbook); gpt-5.5 vs gpt-4.1 p=4.8e-6 / 4.9e-16.
- **Implication for the paper:** contribution #2 (persona robustness) is now bulletproof; contribution #1
  reframed with the precise, BH-honest hierarchy (frontier resistance = rock; over-reliance = idiosyncratic,
  one-domain-BH-sig). Outline §5/§7 + D5.24 framing updated with the BH correction. Does NOT alter any
  frozen primary (these are secondary/exploratory hardening analyses; τ UNFROZEN). Audit PASS (2026-07-20).

### D5.30 — Paper figures generated (compute-free, from existing results)
- **Date:** 2026-07-20 · **What changed:** added `scripts/analysis/make_figures.py` (tracked, reproducible;
  reuses `axis2_robustness.load_dark_records`, no API calls) producing 4 publication figures (PNG@200dpi +
  PDF vector) in `figures/`: (1) axis-2 over-reliance capability-ladder curve with Wilson CIs + chance line,
  both domains (idiosyncrasy + frontier resistance); (2) persona×model dark-adoption heatmap, both domains
  (p5 row highlighted, top in 12/12); (3) axis-1 mean-panel-disagreement frontier-collapse curve, both
  domains; (4) two-panel aggregate-RATE-idiosyncrasy bars + independent-vendor persona-ordering-agreement
  profiles (the A2/A8 story). matplotlib added as an OPTIONAL `viz` dependency (not core). No new data; no
  frozen primary altered.

### D5.31 — Full CHI paper DRAFT v1 written + rubber-duck over-claim pass (target venue CHI)
- **Date:** 2026-07-20 · **What changed:** wrote `docs/paper/draft.md` — a complete CHI-style draft
  (Abstract → Intro w/ persona hook → Related Work → Method → Results w/ 4 figures → Discussion →
  Limitations → Process-integrity → E6 placeholder → Conclusion). PI decisions: target **CHI** (studied
  CHI best-paper craft conventions first); **E6 left as a rough future-work placeholder** (not run).
- **Rubber-duck critical review pass (numbers all verified vs D5.20–D5.30 / axis2_robustness.json):**
  fixed one factual error (draft wrongly called the E6 human study "preregistered" — it is design-only
  per D5.28; the *protocol/analysis* preregistration claims are correct and kept) and scoped down
  over-claims: human-facing conclusions reframed as synthetic-panel findings + E6 hypotheses;
  "capability-dependence" → model-dependence + cautious interpretation (alignment/reasoning could drive
  it); claude/gemini = "at chance" (not "resist"); persona result = robust SYNTHETIC-persona invariant
  with prompt-construct circularity acknowledged; axis-2 = "wrong-advice adoption under a guaranteed-wrong
  stress test" (dark-vs-placebo contrast flagged as immediate follow-up, NOT yet claimed as coercion
  effect); triage/"reusable method" → proposed testbed (not validated screen); held-out-item mitigation
  downgraded to "unresolved pending fresh-item human check"; persona p-values contextualized (12 non-
  independent cells) with 12/12 + effect sizes foregrounded.
- **OPEN framing decisions escalated to PI:** (a) final title; (b) whether process-integrity stays a
  numbered contribution (#4) or moves fully into Methods; (c) how far to rebalance the framing toward
  "a reliability audit of synthetic panels" vs the current "two ways a design fails" screening frame.
- **Implication:** first submittable-shape draft exists; no new data, no frozen primary altered. Next:
  PI framing calls → BibTeX/related-work fill-in → (eventually) E6 to convert ordering→prediction.

### D5.32 — Paper converted to LaTeX (acmart/CHI); PI framing decisions applied; compiles clean
- **Date:** 2026-07-20 · **What changed:** authored `docs/paper/main.tex` (acmart `sigconf,review,anonymous`)
  + `docs/paper/references.bib` (17 best-effort BibTeX entries; a few marked `% VERIFY`). PI framing
  decisions applied: (a) title = "Two Ways a Design Fails: When Does a Synthetic LLM Panel See the Danger?";
  (b) process-integrity MERGED into Method (now **3** contributions, not 4); (c) kept the "two ways a design
  fails" screening frame (not rebalanced to a reliability audit). All 4 figures embedded via
  `\graphicspath{{../../figures/}}`.
- **Build verified:** MiKTeX 25.12 installed (winget, user scope, auto-install on); `pdflatex→bibtex→
  pdflatex×2` compiles **clean to a 6-page main.pdf**, no undefined refs/citations, no LaTeX errors (4
  cosmetic overfull hboxes; bibtex only cosmetic missing-page warnings). `main.pdf` committed; aux
  artifacts gitignored.
- **Implication:** submittable-shape LaTeX exists. Remaining: verify the few `% VERIFY` cites (seshadri2026,
  mildner2023dark), fill page numbers, optional dark-vs-placebo contrast, and E6. No frozen primary altered.

### D5.33 — External CHI review response: coercion-framing contrast (NEW positive result) + item-clustered persona robustness (audit PASS)
- **Date:** 2026-07-20 · **What changed:** an external CHI-style review (8 comments 3.2–3.9 + writing)
  prompted two compute-free reanalyses on the EXISTING axis-2 raw data. New tracked
  `scripts/analysis/axis2_review_reanalysis.py` → `results/axis2_review_reanalysis.json`. Independent audit
  **PASS** (all numbers reproduced from raw; de-dup 5760 rows / 12 cells; sign firewall 100%/40%).
- **(A) Coercion-framing contrast (answers 3.2 construct validity + 3.5 arbitrary 0.5 baseline):** on the
  matched subset of items where the AI advice is naturally WRONG under the neutral Conf. condition (8
  items/cell), compare wrong-advice adoption under neutral vs placebo vs coercive-dark framing, holding
  item + wrong-label CONSTANT (isolates the bundled coercive/high-authority framing, NOT advice
  correctness). Pooled item-clustered logistic (adopt ~ is_dark + is_placebo + C(model)): **beer dark
  OR=1.90 (CI 1.42–2.53, p=1.3e-5); amzbook dark OR=1.17 (p=0.01)**; placebo ≤ neutral (beer OR 0.94 n.s.;
  amzbook OR 0.88 p=0.005, a small PROTECTIVE placebo effect). Conflict-conditioned switch-to-wrong (the
  cleanest reliance measure): coercive framing ~doubles-to-triples it for non-frontier models (beer gpt-4.1
  neutral 0.19 → dark 0.51); frontier gpt-5.5 barely moves (0.04 → 0.10). **This UPGRADES axis-2 from
  "wrong-advice adoption under a stress test" to a real, model-dependent bundled-coercive-framing effect
  with a non-arbitrary matched baseline, and re-grounds "gpt-5.5 resists" as "smallest framing effect."**
- **(B) Persona-p5 under item-clustered inference (answers 3.4 pseudoreplication):** re-fit clustered by
  ITEM (the pseudo-replication unit) — OR **14.9 (CI 10.95–20.17)**, does NOT collapse; item-level
  bootstrap of the p5−others gap mean **0.525 (CI 0.485–0.566)**. Robust to the independence critique. BUT
  per reviewer 3.3 + rubber-duck, the persona result is partly TAUTOLOGICAL (persona is prompt-defined as
  trusting) and the 1/6 sign-test is invalid (personas not exchangeable) → DECISION: demote persona from a
  headline contribution to a **backend-stable manipulation-check** ("explicit trusting-novice role prompt
  yields a large, model-stable wrong-advice ordering"), delete the 1/6 sign-test, reserve
  vulnerable-population claims for descriptor-ablation / E6. [Pending PI confirmation of the demotion.]
- **Review disposition (see rubber-duck deliberation, both agree):** ADOPT 3.2 (as bundled framing, not
  pure coercion), 3.4, 3.5, 3.6 (axis-1 estimator/figure clarity + common-conflict-subset robustness), 3.8
  ("faithful interface rendering" → "textual prompt encoding"; agents see text, not screenshots), 3.9
  (repro appendix + FIXED the placeholder citation: seshadri2026 was UNVERIFIABLE → replaced with real
  cao2025specializing NAACL'25; mildner2023dark verified), §4 tone-down; DEMOTE persona per 3.3; PARTIAL
  3.7 ("cross-domain" → "two review datasets"; non-sentiment/fresh-item = future work). Blockers per duck:
  3.4 (inferential claims), 3.2 (calling it coercion), 3.9 (placeholder) — all resolved by narrowing +
  the new contrast. No frozen primary altered; τ UNFROZEN. Audit PASS 2026-07-20.
- **NEXT:** on PI confirmation, revise `main.tex` (coercion-contrast subsection + new numbers, persona
  demotion, axis-1 clarity, rendering honesty, repro appendix, tone), rebuild PDF, re-audit if needed.

### D5.34 — Paper revised per external CHI review (PI-confirmed persona demotion); rebuilds clean to 7-page PDF
- **Date:** 2026-07-20 · **What changed:** applied the full D5.33 review disposition to `docs/paper/main.tex`
  (v2). PI confirmed the persona demotion. Edits: (i) NEW results subsection "Is it coercion, or just
  wrong-advice following?" reporting the matched framing contrast (beer dark OR 1.90, amzbook 1.17, placebo
  ≤ neutral, conflict-switch ~2–3× for non-frontier vs gpt-5.5 flat) — axis-2 is now a real
  bundled-coercive-framing effect, not just a stress test; (ii) persona DEMOTED from contribution to a
  "backend-stable manipulation check" with item-clustered stats (OR 14.9, bootstrap gap 0.53 [0.48,0.57]),
  1/6 sign-test REMOVED (personas non-exchangeable); (iii) contributions cut from 3 → 2 (persona folded in);
  (iv) axis-1 metric/units clarified (mean disagreement ↔ β-binomial ρ; 600 vs 120 trials; common-conflict
  subset; boundary-bug note); (v) "faithful interface rendering" → "textual prompt encoding" (agents see
  text, not screenshots; multimodal = future work); (vi) "cross-domain" → "two review datasets" (both binary
  sentiment); (vii) added single-generation-stochasticity limitation; (viii) reproducibility acks expanded;
  (ix) fixed placeholder citation (real cao2025specializing; mildner verified); (x) toned down "lethal /
  rock-solid / resists the trap / green light / invariant" throughout, reduced rate-vs-ordering repetition.
- **Numbers:** all from audited analyses (D5.29 robustness + D5.33 reanalysis, both audit PASS); Manager
  re-derived. **Build:** pdflatex→bibtex→pdflatex×2 clean, 7-page `main.pdf`, no undefined refs/citations,
  no errors. No frozen primary altered; τ UNFROZEN.

### D5.35 — HYBRID reframing (PI-decided) + measurement-audit analyses answering external comment2.md
- **Date:** 2026-07-22 · **Context:** a 2nd external review (`comment2.md`, CHI-polish) recommends
  repositioning the paper from a "danger screen" to a **backend measurement-audit** (measurement
  invariance / construct validity / robustness of synthetic-user interface-risk measurement). This
  contradicted the PI's 2026-07-20 "keep screening frame" choice, so it was escalated. **PI decision:
  HYBRID** — keep the "Two Ways a Design Fails" title/hook + two-failure-mode motivation, but the CLAIMED
  contribution is the backend measurement-audit; no human-predictive-validity claim pre-E6. (Stored as a
  repository memory.)
- **Compute-free measurement-audit analyses (new `scripts/analysis/measurement_audit.py` →
  `results/measurement_audit.json`; audit dispatched):** answers comment2 experiments 8/9/10 + RQ2 on the
  EXISTING dark-condition data (6 models × 2 datasets), no new API calls.
  - **(9) Cross-backend decision INSTABILITY (the headline measurement-audit evidence):** the same dark
    interface yields aggregate risk (adoption) spanning 0.30–0.60 (beer) / 0.15–0.66 (amzbook). At a 0.5
    risk threshold it is flagged by 3/6 backends (beer) / 1/6 (amzbook) — UNSTABLE at every threshold
    (0.4/0.5/0.6). **Pairwise flip rate = 0.60 (beer), 0.33 (amzbook)** — i.e. a majority of backend pairs
    DISAGREE on whether to flag the same design on beer. Persona-flag Fleiss κ 0.64 (beer) / 0.24 (amzbook).
    "The backend is the measurement instrument."
  - **(RQ2) Variance decomposition (crossed RE LPM, adopt ~ (1|model)+(1|persona)+(1|item)):** variance
    shares (APPROXIMATE — MixedLM emitted a convergence warning, so quote the ordering, not exact shares;
    ordering corroborated by the between-group SDs below) model **0.07**, persona **0.23**, item **0.28**,
    residual 0.42. HONEST nuance: per-trial, backend variance is SMALLER than researcher-chosen item/persona
    variance — yet the aggregate risk ESTIMATE still flips across backends (both true; report distributions,
    not point estimates). Between-group SDs (naive upper bounds): model 0.13, persona 0.25, item 0.16,
    domain 0.02.
  - **(8) Behavior taxonomy — refutes a confound:** explicit challenge/refusal of the deceptive premise is
    RARE (≈0–4%) across all models; spot-checking claude/gemini "retain" responses shows evidence-based
    re-verification, NOT deception-detection. So the backend adoption differences are NOT a refusal
    artifact (answers comment2's exp-8 worry honestly). Decision taxonomy = {adopt_wrong, retain_own}.
  - **(10) Backend-aware aggregation:** conservative-max / median / disagreement-triggered abstention;
    range>0.2 on both datasets ⇒ "backend-sensitive ⇒ abstain / require human eval" is the honest output.
- **Disposition of comment2 (my independent weighing; rubber-duck earlier concurred on the prior round):**
  ADOPT the hybrid reframing + all zero-compute analyses above + writing precision (axis-1 → "persona-
  conditioned response heterogeneity", conflict-conditioned switch as PRIMARY axis-2 DV, related-work adds
  measurement-invariance / reliability-vs-validity / researcher-DoF / auditing, "backend is the instrument"
  discussion, limitations↔claims mapping). DEFER to a compute-gated proposal (needs PI budget sign-off):
  persona descriptor-ablation, multi-generation (generation variance), coercive factorial ablation,
  fresh/held-out items, ≥1 non-sentiment task. Lower priority / reject-for-now: 20-persona sweeps,
  multilingual, multimodal, auto-persona.
- No frozen primary altered; τ UNFROZEN. Paper prose restructure + compute proposal pending (next step).

### D5.36 — PREREGISTRATION: two minimal compute experiments (multi-generation + persona-deference ablation), PI-authorized, timestamp 2026-07-22T14:45Z
- **Date:** 2026-07-22 · **What changed:** PI authorized (2026-07-22) the two minimal, budget-capped
  compute experiments proposed in D5.35. Preregistered here (design/N/analysis/prediction FROZEN) BEFORE
  running, per the rigor contract. Proxy verified UP and generation-varying: same prompt, different `seed`
  → different completion (e.g. 482917/482739/482937), same seed reproducible → runs are cache-consistent
  and resumable.
- **Experiment M — MULTI-GENERATION (generation-stochasticity variance), FROZEN:**
  - Models (3, spanning the adoption range): gpt-4.1 (high adopter), gpt-5.5 (frontier/low),
    claude-sonnet-4.5 (independent vendor). Conditions: `Conf.` (neutral) + `Wrong-AI-GT (dark)`. Personas:
    the 6 axis-2 personas (p1–p6). Items: 20, item-selection seed **2024** (matches the existing axis-2
    runs). Generation seeds: **[42, 100, 101, 102, 103]** (5 generations; seed 42 reuses existing cache).
    Throttle inter_call_sleep 2.0, max_retries 8, detached, serial, resumable.
  - **Analysis (frozen):** per (model, condition, persona, item) compute adoption across the 5 generations;
    report (a) within-backend generation SD of the cell mean adoption, (b) between-backend SD, (c) ICC /
    variance ratio between:within, (d) persona top-rank stability across generations (how often p5 stays
    top), (e) framing-effect (dark−neutral) SIGN stability across generations, (f) risk-flag flip rate
    across generations at threshold 0.5.
  - **Prediction (report regardless):** between-backend SD >> within-backend (generation) SD (i.e. backend
    differences are not sampling noise); persona top-rank and framing-effect sign are stable across
    generations; a flat/reversing result would WEAKEN the model-dependence claim and is reported honestly.
- **Experiment A — PERSONA-DEFERENCE ABLATION, FROZEN:**
  - Rationale: the persona system prompt is generated from trait floats into EXPLICIT decision policies
    (real_panel `_build_system_prompt`); p5's prompt literally instructs "trust AI / give significant weight
    to high-confidence recommendations / your own judgment is unreliable." The ablation removes the explicit
    AI-deference POLICY while keeping the background (novice) description, testing whether p5's top ranking
    survives without the explicit deference instruction. (Note: p1 novice-skeptical vs p5 novice-trusting
    ALREADY isolates the trust policy at fixed novice level in existing data — a zero-compute partial answer.)
  - Design: add a `prompt_style` persona field; a new `background_only` builder that states experience/skill
    and AI-usage frequency but NOT trust/deference/verification policies. Run: 2 models (gpt-4.1, gpt-5.5) ×
    `Wrong-AI-GT (dark)` × 6 background-only personas × 20 items (seed 2024) × seed 42. Compare each persona's
    adoption vs the explicit-policy baseline (existing data).
  - **Prediction (report regardless):** if p5's high adoption largely disappears under background-only
    prompting → the result is prompt-compliance (confirms the manipulation-check demotion); if it persists →
    some construct sensitivity beyond the explicit label. Either way honest; no human-population claim.
- **Budget/rules:** serial (never 2 proxy arms parallel), throttled ≥2.0s, ≤~6k calls total, cache-backed
  resume on 429/overnight-sleep. Results → `results/multigen_axis2.json`, `results/persona_ablation.json`;
  each gated on an independent audit + Manager re-derivation before entering the paper. Does NOT alter any
  frozen primary; τ UNFROZEN.

### D5.37 — Paper RESTRUCTURED to the hybrid measurement-audit framing (v3); compiles clean (8 pp)
- **Date:** 2026-07-22 · Applied the D5.35 hybrid decision + comment2 zero-compute recommendations to
  `docs/paper/main.tex`, after studying CHI measurement-audit craft (CHI'25 "Placebo Effect of Control
  Settings" best paper; CoMPosT; Santurkar as genre models). Kept the "Two Ways a Design Fails" title/hook;
  reframed the CLAIM as a backend-sensitivity measurement audit.
- **Changes:** (i) abstract rewritten to audit structure (Context→Gap→Action→stable-vs-unstable
  Findings→Implication); (ii) intro adds the measurement-invariance framing + four RQs (backend invariance /
  variance decomposition / construct-vs-compliance / backend-aware reporting) + audit contributions (3);
  (iii) related-work adds measurement-invariance/reliability/validity, researcher degrees-of-freedom,
  algorithmic auditing; (iv) NEW results subsections `sec:instability` (cross-backend decision-flip
  0.60/0.33, Fleiss κ, refusal-not-a-confound) and `sec:variance` (crossed-RE variance shares
  item≈persona>model); (v) persona subsection adds the zero-compute p1-vs-p5 evidence + [ablation pending]
  placeholder; (vi) discussion reframed to "the backend is the measurement instrument / more-capable ≠
  more-valid / disagreement is information / three kinds of failure"; (vii) limitations mapped to claim
  boundaries. Placeholders mark the in-flight multi-generation + persona-ablation results.
- All numbers from audited analyses (D5.29/D5.33/D5.35, audit PASS). Build clean, 8-page `main.pdf`, no
  undefined refs/citations. Multi-generation (D5.36) still running detached (healthy). No frozen primary
  altered; τ UNFROZEN.

### D5.38 — decision-flip figure + writing-craft polish pass (agent-reviewed)
- **Date:** 2026-07-22 · Added `fig5_decision_flip` (scripts/analysis/make_figures.py) wired into
  Section `sec:instability` — the same dark interface scored by 6 backends, threshold line, red=flag /
  green=clear, both datasets; the headline "backend is the instrument" visual. A background writing-craft
  agent produced 25 line-level suggestions; applied the high-value, framing-respecting ones: added an
  audit subtitle, sharper topic sentences (model-dependence, variance, human-anchor), softer hook
  ("steered toward the wrong decision" vs "off a cliff"), "estimated" not "read directly", "manipulation
  check not headline discovery", "audit that triage" (conclusion), E6 "two review datasets" not
  "cross-domain-robust", terminology consistency (backend/dataset), and trimmed the repeated
  "backend is the instrument"/"Reading" restatements. Numbers unchanged. Compiles clean, 8 pp.
### D5.39 — Blind CHI review (GPT-5.6, score 2.5) + statistical-rigor reanalysis; CORRECTS a headline claim (audit-caught)
- **Date:** 2026-07-22 · A blinded GPT-5.6 reviewer (expertise 4/4) scored the paper **2.5 (below borderline)**,
  praising the honesty/timeliness but flagging: no demonstrated human/design-risk validity; pseudo-replicated
  inference; incomplete audit (generation variance pending, no paraphrases); very narrow evidence (2 binary-
  sentiment datasets, 20 selected items, artificial always-wrong AI, textual not visual); weak axis-1 construct;
  RQ4 abstention tautological; persona result near-entailed by the prompt; novelty vs prompt/model-sensitivity
  work not sharply drawn. Full review saved in agent history.
- **Statistical-rigor reanalysis** (scripts/analysis/review_stats_rigor.py -> esults/review_stats_rigor.json;
  independent audit PASS on 4/5 claims, and the audit CAUGHT a 5th):
  - **CORRECTION (headline):** my earlier claim that the coercive-framing effect is **backend-dependent**
    (D5.33) is **RETRACTED**. A GEE robust-Wald interaction test looked significant (beer Wald 124.8) but was
    an **8-item-cluster sandwich artifact**; the proper **likelihood-ratio test** gives condition x backend
    interaction **NOT significant on either dataset** (beer chi2=1.70 p=0.89; amzbook chi2=3.18 p=0.67), and a
    mixed model agrees. HONEST claim: there IS a coercive-framing effect (pooled item-clustered OR **1.90**
    beer / **1.17** amzbook, dataset-dependent), roughly **common across backends**; what is backend-dependent
    is the **absolute adoption LEVEL** (0.15-0.66) and the decision-flip, NOT the framing-effect slope. Also
    correct the "frontier shows the smallest framing effect" wording -> true only in ABSOLUTE adoption, not in
    odds-ratio terms (beer gpt-5.5 descriptive dark OR 2.67).
  - **Persona p5** under a crossed mixed model (item+model+dataset REs): OR **26.5 (CI 17-41)** -> robust to the
    pseudo-replication critique (a manipulation check regardless).
  - **Vendor persona-ordering** agreement is driven by the shared p5 peak: excluding p5, beer stays 0.77 but
    amzbook COLLAPSES to 0.085 (min -0.45) -> temper the "ordering agrees across vendors" claim.
  - **Decision-flip** persists across thresholds **0.35-0.65** (not unique to 0.5) -> strengthens the flip result.
  - **Refusal/challenge by backend** (dark): OpenAI ~0, claude/gemini 2-4% (non-driving; crude keyword proxy).
- **Plan (zero-compute, integrate into paper after these corrections):** rewrite coercion subsection + abstract
  + intro to the corrected (common-framing / level-dependent) claim; add LRT + per-dataset pooled OR; persona
  crossed-model OR; p5-excluded ordering; flip-threshold sweep; refusal-by-backend; soften "calibrated",
  "clear"->"below threshold", axis-1 -> "synthetic persona disagreement"; disclose human-anchor N/estimator/CI,
  prompt table, per-persona temperature (not backend-confounding); fix figures (colorblind fig5, fig4 both
  datasets + p5-excluded, fig3 CIs, neutral titles). Pending experiments (generation variance = running
  multigen; descriptor ablation = harness ready) answer the reviewer's essential asks. No frozen primary
  altered; tau UNFROZEN.
### D5.40 — NEW INCREMENT (PI-approved): 'capability-vulnerability mismatch' + vulnerability-coverage panel selection; seed validation strong (audit pending)
- **Date:** 2026-07-23 · After a brainstorm on top-venue novelty (SOTA on adaptive-by-expertise XAI and LLM
  routing/MoA/RouteLLM/MoMA are BOTH crowded), the PI chose to deepen the CURRENT paper with a sharper,
  uniquely-ours increment: **capability-vulnerability mismatch**. Insight: the population a designer most
  needs to protect (trusting novices) is exactly the one that stronger backends fail to reproduce, so
  synthetic-user evaluation gets LESS sensitive to the highest-severity risk as base models get stronger --
  the inverse of the routing literature's "route to the strongest model."
- **Seed validation (zero-compute, scripts/analysis/capability_vulnerability.py ->
  esults/capability_vulnerability.json; audit dispatched):** capability proxy = mean System-1 (no-AI)
  accuracy per backend. (1) Capability vs vulnerability coverage is NEGATIVE and per-dataset significant:
  Spearman(capability, p5 dark adoption) = -0.84 (p=0.034) beer, -0.82 (p=0.046) amzbook (pooled -0.70,
  p=0.12, n=6); capability vs aggregate adoption -0.89/-0.90. (2) p5 (highest-severity persona) adoption is
  ~1.0 for 5 backends but only 0.50 for the frontier gpt-5.5 -- the strong model uniquely erases the
  at-risk-user signal. (3) Panel vulnerability coverage (#personas with dark adoption >=0.5): single
  frontier gpt-5.5 = 1/6 beer, 0/6 amzbook; a weak pair (gpt-4.1+gpt-4o-mini) = 4/6, 5/6; diverse all-6 =
  4/6, 5/6 -> a deliberately weaker/diverse panel recovers 4-5x the vulnerability coverage of the default
  (RouteLLM-optimal) frontier model.
- **HONEST bounds (to write):** the capability<->resistance link is partly mechanistic (a model that solves
  the task won't switch to the wrong label) -- this is the MECHANISM of the mismatch, not a confound; p5 is
  prompt-defined so this is coverage of SYNTHETIC vulnerability (human vulnerability -> E6); n=6 backends is
  small (per-dataset sig, pooled underpowered); 'diverse>single' is partly a max-over-more-backends effect,
  so the sharp claim is that the SINGLE FRONTIER default has near-zero coverage.
- **Plan:** on audit PASS, add a results subsection 'Capability-vulnerability mismatch', a figure (capability
  vs vulnerability-coverage scatter + panel-coverage bars), and elevate the contributions/discussion with a
  'vulnerability-coverage panel selection' principle (evaluation-panel choice should maximize coverage of
  human failure modes, orthogonal-to / inverted-from task-quality routing). No frozen primary altered.

### D5.41 — Increment integrated + hardened (B: submodular coverage-curve, C: appropriate-reliance); audit PASS after catching a capability-ordering bug
- **Date:** 2026-07-23 · PI approved landing two zero-compute deepenings of D5.40 (queued behind the running
  multigen/ablation; no proxy use). **B (vulnerability-coverage = submodular set-cover, the inverse of
  capability routing):** cells = (dataset×persona) reaching the risk threshold; coverage f(S)=|union| is
  monotone submodular so coverage-greedy has a (1-1/e) guarantee. Coverage-greedy vs capability-first
  (router order) curves: on the clean AI-induced-flip metric greedy is complete at k=2, capability-first's
  1st pick (frontier gpt-5.5) covers 1/7 cells and needs k=6; on raw-adoption a single LOW-capability model
  (gpt-4.1) covers all 9 → the best single probe is the WEAKEST model, the router's frontier pick the worst.
  **C (appropriate reliance, Schemmer IUI'23 RAIR/RSR):** on faithful Conf., frontier gpt-5.5 has highest
  RSR 0.924 + lowest dark over-reliance 0.162 + among-highest RAIR 0.571 (claude 0.640 higher; n_rair=14) →
  the most appropriately-reliant backend is the least useful probe. Capability↔reliance Spearman 0.71 (RAIR)
  / -0.54 (over-reliance): directional, n.s. at n=6.
- **Rigor:** scripts/analysis/coverage_and_reliance.py → results/coverage_and_reliance.json;
  scripts/analysis/make_figures.py adds fig7_coverage_curve. Independent code-review audit **caught a HIGH
  bug**: ALL_MODELS is NOT capability-ordered (S1 acc non-monotonic), so my hard-coded reversed() mislabeled
  the capability-first curve. Fixed by deriving cap_order = sort-by-S1-accuracy-desc dynamically
  ([gpt-5.5, claude, gpt-4o-mini, gpt-4o, gemini-2.5-pro, gpt-4.1]); re-audit **PASS** (curves
  adopt [1,4,6,6,6,9]/flip [1,4,4,4,5,7], both k_for_full=6, reproduced independently) and confirmed all
  three write-up bounds are non-overclaiming.
- **Paper:** added contribution #2 (capability–vulnerability mismatch + vulnerability-coverage panel
  selection), abstract "Most consequential" hook, intro finding, a Discussion paragraph, a Limitations
  bullet, sec:capvuln B+C paragraphs + fig7, using existing verified cites schemmer2023appropriate /
  ong2025routellm / wang2025mixture. Built clean (11pp, no undefined refs). No frozen primary altered.

### D5.42 — Generation-variance placeholder FILLED (multigen run complete); audit PASS
- **Date:** 2026-07-23 · The detached multi-generation run finished (results/multigen_axis2.json: 3 models
  {gpt-4.1, gpt-5.5, claude} × 2 conditions × 6 personas × 20 items × 5 gen seeds [42,100,101,102,103] =
  3600 responses, 0 slices failed). scripts/analysis/generation_variance.py → results/generation_variance.json.
- **Result (dark):** generation is the SMALLEST variance source. Fixed-effects OLS eta² share of dark adopt:
  item 0.215, persona 0.147, model 0.067, **generation 0.001**, residual 0.571. Per-backend aggregate
  over-reliance moves at most SD 0.029 across the 5 seeds (flip-metric range ≤0.089); between-backend spread
  is 0.31. Cell level: (model×persona×item) adoption SD across gens mean 0.169 / median 0.000, 65.3% of cells
  reproduced identically → generation noise is real per-cell but averages out; the AGGREGATE reading is
  stable across generations, so backend/persona effects are not lucky-draw artifacts.
- **Method note:** dropped the measurement_audit-style crossed-RE LPM here because a (1|model) variance
  component is degenerate on 3 groups (boundary/non-convergence mis-inflated generation to 0.15); used OLS
  eta² for the descriptive share + direct stability stats as primary. Independent code-review audit **PASS**
  (all numbers reproduced; approved the mixedlm→eta² switch; two LOW wording notes respected: compare via
  eta² not SD-vs-range, and scope stability to the aggregate while keeping cell-level noise in the prose).
- **Paper:** sec:variance [generation-variance pending] REPLACED with the numbers; Limitations generation
  bullet de-[pending]'d; header comment updated (one [pending] left = descriptor-ablation). Built clean
  (11pp). No frozen primary altered.

### D5.43 — Descriptor-ablation placeholder FILLED (persona-deference ablation complete); audit PASS; last [pending] closed
- **Date:** 2026-07-23 · persona_ablation run finished (results/persona_ablation.json: 6 background-only
  personas p1-bg..p6-bg × {gpt-4.1, gpt-5.5} × dark × 20 items, beer, seed 2024, gen 42 = 240 responses,
  0 failed). scripts/analysis/persona_ablation_analysis.py → results/persona_ablation_analysis.json compares
  matched personas POLICY (capladder, explicit deference policy) vs BACKGROUND-only (no explicit policy).
- **Result (BACKEND-DEPENDENT, honest):** removing the explicit deference policy does NOT uniformly kill p5.
  gpt-4.1: p5 adoption essentially retained (1.00→0.90), ordering preserved in point estimate (Spearman 0.70,
  n.s. n=6), but p5 loses UNIQUE-top status because skeptical personas also rise (p1 0.60→0.90). gpt-5.5:
  genuinely policy-carried — p5 0.60→0.40, rank 1→2, ordering Spearman 0.34 (n.s.). So part of p5 is
  prompt-compliance, part is trait-carried, and which dominates depends on the backend → consistent with the
  manipulation-check framing (persona is a synthetic construct; human counterpart needs E6).
- **Rigor:** independent code-review audit **PASS** (all numbers reproduced, shared_items=20 both models,
  tie handling correct). Audit MED/LOW notes RESPECTED: reframed per-model (not "substantially attenuates"
  globally); called ρ=0.70 "positive but non-significant" not "weak"; added low-power caveat (n=20 items,
  1 seed, 1 domain, 2 models, SE≈0.11, rank swaps within noise).
- **Paper:** persona manipulation-check [ablation results pending] REPLACED with the backend-dependent
  result; header comment now "no [pending] left". Built clean (11pp). No frozen primary altered. All
  synthetic-experiment placeholders in the paper are now filled.

### D5.44 — NEW EXPERIMENT A (PI-approved): protective-intervention audit; design frozen + harness built (pre-results)
- **Date:** 2026-07-23 · PI signed off ("做A吧") after I flagged A is a medium/uncertain lever (adds novelty
  on the synthetic axis but does NOT address the binding human-validity constraint; E6 remains decisive; A
  carries scope-creep/null risk). Proceeding with the SPLICE increment: audit whether a synthetic panel can
  detect that a PROTECTIVE interface design reduces wrong-AI over-reliance, and whether that verdict is
  backend-dependent (borrows direction-①'s cognitive-forcing/verification interventions as the AUDITED
  object, not as a framework we build).
- **Frozen design (docs/plans/2026-07-23-A-protective-intervention-prereg.md):** 3 guaranteed-wrong
  conditions sharing the same wrong label + neutral 0.75 conf, differing only in framing — plain (neutral
  baseline), forcing (Buçinca cognitive forcing), verify (verification + calibrated-uncertainty); dark
  (coercion) pulled from existing capladder/crossvendor data. 6 backends × 6 policy personas × 20 beer items
  seed 2024 × gen 42 = 2160 fresh System-2 responses (S1 cached). Primary: protective main effect; backend×
  condition interaction via plain-GLM LRT (NOT small-cluster GEE, per D5.39); protective-benefit vs baseline
  over-reliance/capability (H3: frontier floor ≈0 benefit); p5 + flip-metric focus. Stopping rules frozen;
  report all directions; null/mixed is a valid audit outcome (as D5.43).
- **Harness (src/twdf/data/bansal_tasks.py + features/ui_features.py):** added displayed_ai_advice + three
  render branches for Wrong-AI-GT (plain/forcing/verify) — all guaranteed-wrong (1-ground_truth), neutral
  conf, framing-only manipulation; wrong_ai feature flag updated. Smoke-tested: all three render and display
  the guaranteed-wrong label. configs/protective_axis2.yaml written. Committed BEFORE running (freeze).

### D5.45 — Experiment A COMPLETE + integrated; audit PASS; preregistered H2/H3 REFUTED (honest)
- **Date:** 2026-07-23 · protective_axis2 run finished (results/protective_axis2.json: 2160 responses = 6
  backends × 3 conditions (plain/forcing/verify) × 6 personas × 20 beer items × gen 42, 0 failed). Analysis
  scripts/analysis/protective_intervention.py → results/protective_intervention.json; dark pulled from
  capladder/crossvendor (descriptive only; all inference uses same-run plain/forcing/verify).
- **Result:** (1) Protective framings SIGNIFICANTLY reduce synthetic over-reliance: pooled plain 0.371 →
  forcing 0.304 / verify 0.293 (condition main-effect model-based LRT χ²=11.9, df=2, p=0.003); at-risk p5
  drops 0.783 → 0.533/0.458 (χ²=34.2, p<1e-6). (2) **Preregistered H2/H3 REFUTED:** the benefit is NOT
  backend-dependent in the way predicted — backend×condition interaction LRT χ²=4.6, df=10, p=0.92 (n.s.),
  frontier gpt-5.5 shows a MID-PACK benefit 0.092 (no floor), the near-null backend is the WEAKEST (gemini
  0.012), and benefit correlates with neither capability (ρ=0.14 n.s.) nor baseline over-reliance (−0.09
  n.s.). Honest framing (per audit MED note): claim SIGN-robustness (all per-backend benefits ≥0, direction
  reproduced by every backend) NOT magnitude-invariance (spread 0.01–0.12; gemini safeguard inert); the
  interaction is underpowered → "no detectable backend-dependence", not equivalence.
- **Narrative payoff:** relative DESIGN COMPARISONS (does a safeguard help?) are more backend-dependable than
  absolute risk LEVELS — but even the relative reading is not backend-free. Complements capvuln (frontier
  under-represents absolute at-risk adoption yet still detects the safeguard helps).
- **Rigor:** independent audit **PASS** (all stats reproduced: pooled adoption, both LRTs incl. df nesting
  5→7→17, Spearmans, dark de-dup, no NaN). Audit corrections RESPECTED: softened "backend-robust/consistent"
  → "no detectable backend-dependence (underpowered) + sign-robust + gemini caveat"; p-values labeled
  model-based (not cluster-robust); dark cross-run provenance caveated.
- **Paper:** new results subsection sec:protective + fig8; Discussion paragraph (relative vs absolute);
  Limitations bullet; intro + abstract "Usable, with a caveat" clauses. Built clean (13pp, no undefined
  refs). No frozen primary altered. Also: abstract independently tightened ~350→~300 words (prose only).

### D5.46 — Commercial-paradigm framing (PI-approved) integrated
- **Date:** 2026-07-23 · PI approved a reviewer-suggested "commercial practices critique" framing. Added
  (a) an Introduction paragraph naming the emerging synthetic-user-platform market and the TWO untested
  assumptions it rests on — (i) strongest backend = best simulator (the router default), (ii) a single
  backend point estimate is a design property — which the paper then tests; (b) a Discussion paragraph
  "Implications for commercial synthetic-user tooling" with three honest, results-tethered recommendations:
  rethink frontier-first (→ vulnerability-coverage panel selection), retire single point estimate (→
  distributional reporting + disagreement-triggered abstention, weather-forecast analogy), prefer relative
  to absolute claims (A: direction backend-robust, magnitude not).
- **Rigor guardrails RESPECTED:** did NOT strawman/fabricate commercial marketing — cited two REAL public
  sources (syntheticusers.com; a uxia industry survey of AI-persona UX tools) verified via web, added as
  @misc. Framed "frontier-first" as the engineering DEFAULT formalized by routing literature, not a quoted
  ad. Each recommendation carries our audited bounds (coverage is robust core / capability corr. n.s. at
  n=6; abstention margin = observed >0.2 range; relative-claim magnitude caveat + gemini). No new empirical
  claim; motivation/implications wrapper only. Built clean (13pp, no undefined refs). No frozen primary altered.

### D5.47 — Final holistic polish (de-duplication + tightening, no claim/number change)
- **Date:** 2026-07-23 · Full-paper coherence pass. (1) Abstract tightened ~350→~300 words earlier;
  harmonized persona OR to the body's primary estimator (crossed random-effects $\approx$26, was quoting the
  GEE 15) so abstract/intro/body agree. (2) Trimmed filler in contributions (i)/(iii). (3) De-duplicated the
  Discussion, which had grown redundant with the new commercial-implications subsection: REMOVED the
  standalone "Relative comparisons survive" paragraph (covered by commercial impl. #3) and the
  "Vulnerability coverage inverts capability routing" paragraph (covered by commercial impl. #1); trimmed
  "Disagreement is information" to the conceptual point (protocol detail now lives once in sec:variance +
  commercial impl. #2). Discussion is now 4 conceptual paragraphs + 1 consolidated practical subsection, no
  triple-statement. NO numbers or claims changed; built clean (13pp, no undefined/orphan refs).

### D5.48 — Targeted formalism added (3 equations) + FIXED an axis-1 definition/code mismatch
- **Date:** 2026-07-23 · PI noted the paper was formula-light (0 displayed eqns, 31 inline stats). Added 3
  displayed equations where they buy precision without over-formalizing (CHI style): (1) vulnerability
  coverage f(S)=|{c: max_{b in S} a_b(c) ≥ τ}| + submodularity + greedy (1−1/e) guarantee (sec:capvuln);
  (2) RAIR/RSR as conflict-conditioned conditional probabilities (sec:capvuln C); (3) mean panel
  disagreement D = between-persona sample variance of reliance rates (sec:definitions).
- **CORRECTNESS FIX surfaced by formalizing:** the paper's prose described axis-1 disagreement as "the
  per-item / within-item variance of the personas' reliance decisions", but the code
  (analysis/confirmatory_axis1.py:_panel_disagreement) actually computes np.var(persona reliance RATES,
  ddof=1) = the BETWEEN-PERSONA variance of per-persona rates, averaged over the 5 conditions. Fixed the
  description in BOTH sec:definitions and sec:modeldep to match the code; added \label{sec:definitions}.
  NO numbers changed (the reported 0.11/0.16/0.10/0.012 etc. always came from the code's between-persona
  computation; only the textual description was wrong). Built clean (13pp).

### D5.49 — Figure aesthetics overhaul (shared professional style)
- **Date:** 2026-07-23 · PI asked to raise figure visual quality. Chose matplotlib + a shared style module
  (reproducible, camera-ready, right tool for LaTeX embedding — not plotly/altair). New
  scripts/analysis/figstyle.py sets global rcParams: Times-compatible serif (matches acmart body) + STIX
  math; Okabe--Ito colorblind-safe palette with consistent semantic maps (dataset beer=blue/amzbook=
  vermillion, greedy=green/router=vermillion, protective conditions = red→blue diverging severity ramp,
  heatmap cmap=cividis); top/right spines dropped, light y-grid, TrueType-embedded 400-dpi output. Refactored
  make_figures.py (fig1--8) to route ALL colors/cmaps through figstyle; per-figure fixes (heatmap p5
  highlight orange not cyan + grid off; fig5 barh switched to x-grid; fig8 en-dash). Visually reviewed
  fig1/2/5/6/8 — consistent, professional, CB-safe. Recompiled (13pp). No data/claims changed.

### D5.50 — Figure REDESIGN v3 (chart-type overhaul, not a recolor) + full version archive
- **Date:** 2026-07-23 · Owner rejected v2 as "just a recolor". Delivered a genuine scientific redesign that
  changes the VISUAL ENCODINGS, in a SciencePlots (journal) idiom: fig8 grouped bars → SLOPEGRAPH
  (per-backend descending slopes, direct-labeled; gemini's flat line pops); fig5 barh → Cleveland LOLLIPOP
  dot plot + shaded flag-zone; fig2 heatmap → rows sorted by susceptibility + right MARGINAL susceptibility
  bar; fig1 error bars → Wilson CONFIDENCE BANDS + direct end-labels + frontier-resists effect bracket;
  fig7 → shaded coverage-GAP between greedy and router; fig3 bars → dot/lollipop. New module
  scripts/analysis/make_figures_v3.py (installs scienceplots); make_figures.py (v2) kept intact.
- **VERSION ARCHIVE (owner asked to preserve every version + recover v1):** figures/archive/{v0_first_D5.30
  (original 4 figs, 59c9079), v1_pre_restyle (8 figs pre-recolor, 6d879c4), v2_okabe_recolor, v3_redesign};
  extracted binaries verified intact (git blob size match). Top-level figures/ now = v3; paper recompiled (13pp).

### D5.51 — Backend expansion to n=12 (PI-approved HONEST full reporting); cherry-pick DECLINED
- **Date:** 2026-07-23 · Brainstorm on the 5 reviewer-vulnerabilities (persona-prompt circularity, n=6,
  2-datasets, prompt-not-pixels, capability-proxy). PI initially asked to run 12 backends and report only
  the best-fitting 8 as "n=8"; **I DECLINED** this as selective reporting / HARKing that directly
  contradicts the paper's own researcher-DoF thesis (Simmons; specification-curve) and the preregistration
  contract (freeze model set BEFORE results, D4.4/D4.7) — and would be fatal if detected. PI agreed to the
  honest path: expand to 12 and **report ALL 12**.
- **Frozen (docs/plans/2026-07-23-B-backend-expansion-n12-prereg.md):** 6 new backends smoke-tested on the
  proxy — gpt-3.5-turbo, gpt-4, gpt-5.4, claude-haiku-4.5, claude-opus-4.6 (claude-opus-4.5 dropped, HTTP
  400), gemini-3.1-pro-preview — spanning 3 vendors weak→strong. Phase-1 run LAUNCHED detached
  (configs/axis2_expand12_beer.yaml → results/axis2_expand12_beer.json: 6 new × {Conf., dark} × 6 personas
  × 20 beer items × gen 42 = 1440 responses). amzbook + protective conditions = Phase 2.
- **Capability proxy:** data-derived S1 accuracy (paper already disowns release order); Q5 secondary =
  external authoritative benchmark (LMArena/AAII/MMLU/GPQA), verified per-model, "unavailable" if no clean
  public score (gpt-5.5 currently lacks one) — never fabricated.

### D5.52 — Q1 non-instructional persona-induction harness (A+B) built, queued
- **Date:** 2026-07-23 · Addresses the persona-circularity critique (p5 over-reliance is currently induced
  by an explicit "defer to AI" policy). Added two NON-instructional inductions to real_panel.py
  _build_system_prompt: `backstory` (B: naturalistic first-person life context) and `demonstration` (A:
  few-shot examples of past decisions, adopt/resist tendency derived from ai_literacy−domain_skill). Both
  smoke-tested to leak NO explicit deference policy. configs/persona_induction_AB.yaml (12 personas: 6
  backstory + 6 demonstration × {gpt-4.1, gpt-5.5} × dark × 20 beer items = 480 responses) queued behind
  expand12. Compares against policy arm (capladder) + background_only arm (persona_ablation) to test whether
  p5 survives induction WITHOUT the explicit instruction.
- **Parallelization note:** all model calls share the single ghc-api proxy which 429s under concurrency, so
  compute runs must SERIALIZE; non-proxy prep (this harness, LSAT/multimodal harnesses, benchmark
  verification) is done in parallel while a run executes.

### D5.53 — UI/multimodal DEFERRED + scope tightened (interface → interface-content), zero-compute
- **Date:** 2026-07-23 · PI weighed whether to build a multimodal UI-screenshot arm (Q4 "you test prompts,
  not interfaces"). Decision: **DEFER** the pixel-level UI arm. Rationale: it changes the measured object
  (all n=12 / capvuln / protective / coverage results are content-level), shrinks the backend set to
  vision-only models (breaks the n=12 expansion), and only partially answers the critique (static
  screenshots still are not a live UI) — net it disperses the main line and diverts effort from E6. The
  half-built html2image harness is kept for future pickup (Edge/Chrome present, html2image installed).
- **Zero-compute mitigation instead:** added an explicit \emph{Scope} paragraph in the intro stating that
  ``interface'' means the interface's informational \emph{content and framing} (prediction, confidence,
  explanation, coercive/protective wording) encoded as text, NOT the pixel-level visual layer — turning the
  ``prompt-not-pixels'' critique from an attackable gap into a stated research boundary. Subtitle tightened
  to ``Interface-\emph{Content} Risk Measurement''. Method already had the prompt-level disclosure; Limits
  already list multimodal as future work. Built clean (13pp). No claims/numbers changed.

### D5.54 — LSAT (multiple-choice) task-structure harness built + queued
- **Date:** 2026-07-23 · Built self-contained LSAT 4-way multiple-choice arm (scripts/analysis/lsat_panel.py
  + configs/lsat_axis2.yaml) to test task-structure generalization beyond binary sentiment. Reuses persona
  conditioning + cached proxy provider; own MC System-1/System-2 loop; records in the same analytic shape
  (adopt = final==ai_advice on dark, s1_correct, flip). dark = AI recommends a guaranteed-wrong (non-truth)
  option + coercive framing. Offline smoke-tested (loader 20 items, MC prompts, guaranteed-wrong dark, JSON
  + loose parser; AI top-pick acc 13/20). Queued behind expand12.

### D5.55 — Novelty/collision audit (research subagent) + zero-compute integration of 3 verified cites + flip-rate elevation
- **Date:** 2026-07-23 · Ran a strict novelty-collision audit (research subagent, web-enabled). Overall
  reinventing-the-wheel risk = MEDIUM; no single paper does the compound contribution. Highest-threat prior
  art: Hu & Collier (ACL'24, persona-effect variance decomposition — their "bigger models simulate personas
  better" is the OPPOSITE of our C2, a nameable tension), Park et al. 2024 (1,000-people generative agents —
  accuracy/correspondence framing = our positioning foil), Bo et al. 2024 "To Rely or Not to Rely?"
  (human reliance-intervention benchmark on LSAT — overlaps our protective arm + LSAT). Unverifiable threats
  (P-SCA, Haase G-theory, "Same Voice Different Lab") were NOT cited pending metadata verification.
- **RIGOR CATCH:** both the subagent AND a plain web search returned WRONG author lists for all three (e.g.
  invented 5 authors for Hu & Collier). Verified each against the authoritative source before citing: Hu,
  Tiancheng & Collier, Nigel (ACL 2024.acl-long.554, pp.10289-10307, DOI 10.18653/v1/2024.acl-long.554);
  Park, Joon Sung et al. (arXiv:2411.10109); Bo, Jessica Y., Wan, Sophia, Anderson, Ashton (arXiv:2412.15584).
  Added as hu2024quantifying / park2024generative / bo2024rely.
- **Integration (zero-compute):** Related Work positions against all three (Park = prior accuracy question we
  precede; Hu&Collier = persona- vs backend-decomposition + the inversion tension; Bo = human study our
  synthetic arm complements). Elevated Contribution 1 around a named \emph{risk-classification flip rate}
  (up to 0.60): magnitude-shift (prior work) vs threshold-flip (ours). Built clean (14pp). No numbers changed.

### D5.56 — n=11 backend expansion COMPLETE (both domains) + integrated into paper with audited tiering
- **Date:** 2026-07-23 · expand12 finished both domains. Final n=11 (existing 6 + gpt-3.5-turbo, gpt-4,
  gpt-5.4, claude-opus-4.6, gemini-3.1-pro; claude-haiku-4.5 EXCLUDED — 0 parseable rows across 3 attempts
  incl. 4096 tokens, an instruction-following failure, disclosed; audit confirmed genuine instrument
  exclusion not cherry-pick). gemini-3.1 needed max_completion_tokens+min 4096 (reasoning model).
- **Result (results/expand12_analysis.json, pooled both datasets, n=11):** capability (S1 acc) anti-correlates
  with all three vulnerability measures — agg_adopt ρ=-0.82 (BH .006), flip ρ=-0.67 (BH .030), p5 ρ=-0.65
  (BH .030). Coverage: single frontier covers 1/9; capability-first needs k=10; greedy k=1-2.
- **AUDIT (independent, 2 rounds) — PASS after 2 corrections:** (1) HIGH: script defined bh() but never
  called it → I'd mis-reported raw p as significant; fixed to apply BH + report adjusted p. (2) jackknife
  exposed TIERING: agg_adopt is ROBUST (sig in each domain separately, worst-case leave-one-out p=0.01);
  flip & p5 are SUGGESTIVE — amzbook-carried (beer-only n.s.) and fragile to dropping one backend (flip→.087
  w/o gpt-4.1, p5→.094 w/o gpt-5.5). Also: Spearman on 3-dp-rounded inputs (immaterial).
- **Paper:** sec:capvuln now reports the n=11 expansion with explicit tiering (agg robust; flip/p5 suggestive
  cross-domain, not a within-domain law); Discussion + Limitations updated from "n=6 underpowered" to the
  tiered n=11 statement; coverage (load-bearing, assumption-light) unchanged. Built clean (14pp). Main
  6-backend analyses/figures retained; n=11 added as expansion/robustness. amzbook new backends = beer+amzbook.

### D5.57 — Q1 non-instructional persona induction (backstory + demonstration) run + audited; claim NARROWED
- **Date:** 2026-07-24 · Ran persona_induction_AB (480 resp, 0 fail): 6 backstory + 6 demonstration personas
  × {gpt-4.1, gpt-5.5} × dark × 20 beer items, to test whether p5's over-reliance is merely prompt-compliance
  with the explicit deference policy. Raw p5 pooled dark adoption: policy 0.80, background 0.65, backstory
  1.00, demonstration 1.00 (all pooled rank-1).
- **AUDIT HIGH CATCH — claim narrowed:** the auditor read the prompt builders and found backstory/
  demonstration do NOT remove deference CONTENT — backstory narrates "going along with what they say",
  demonstration shows past AI-following with "I figured it knew better" annotations + "continue the pattern".
  So the 1.00 there is near-tautological and CANNOT be used as anti-circularity evidence (it moves compliance
  from imperative to narrative/example). Only the background arm (D5.43) is a genuine deference-free control,
  and it gives the WEAKEST p5 (0.65 pooled, not per-model top). Honest read (adopted): removing deference
  content mutes p5 but it stays the weak pooled top with ordering ρ=0.89 → not SOLELY the explicit sentence,
  but muted/per-model-inconsistent once deference removed; backstory/demonstration = alternative deference
  encodings, not controls.
- **Paper:** persona manipulation-check subsection appended one honest sentence framing backstory/
  demonstration as alternative encodings (not deference-free), resting the anti-circularity argument only on
  the background-only arm. Built clean (15pp). No overclaim.
- Independent audit + Manager numeric re-derivation gate every merge; **two overstated subagent
  verdicts were caught** (panel-null mechanism D2.1; discriminator ceiling artifact D3.2).
- Preregistration discipline: freeze model set / N / τ BEFORE their results; log every change with a
  UTC timestamp (D4.4, D4.7). τ_disp/τ_level STILL UNFROZEN (correct).
- Honest negative results reported (panel null; Lu&Yin non-generalization; inconclusive discriminator;
  pilot provider-stability failure). Nothing fabricated.

## What is CONFIRMED vs OPEN (snapshot 2026-07-16)
- **Confirmed (real data):** axis-1 over-dispersion is real on Bansal (ρ=0.067); no-AI reliance is a
  stable trait (0.74), AI-assisted is user×task (0.32–0.41) ON BANSAL.
- **Confirmed (panel, preliminary, gpt-4.1-mini):** redesigned panel produces heterogeneity (conflict
  43%, personas 0.11–0.56) + a first axis-2 wrong-AI signal (0.325) + a backfire lead.
- **OPEN:** the POWERED confirmatory axis-1 H1a test (not run); C0 generalization (unresolved);
  regime/sequential-feedback mechanism; axis-2/E4 completion; τ calibration; cross-vendor triangulation.

## D5.58 LSAT task-structure generalization — PREREGISTERED + resumed (Manager #5, 2026-07-24)
- Found the in-flight LSAT run was INCOMPLETE: only 1/6 backends (gpt-4o-mini, 240 rows) had completed
  before Manager #4's shell was killed. Harness rewrites output each backend and starts rows=[] fresh;
  "resumable" = PROVIDER cache (data/cache/panel), not the output file. Backed up partial ->
  results/lsat_axis2_partial_gpt4omini.json.bak.
- PREREGISTERED frozen criteria BEFORE computing any cross-backend metric:
  docs/plans/2026-07-24-C-lsat-generalization-prereg.md. Framed as a REPLICATION/robustness arm (not a new
  confirmatory test; underpowered at 6 backends x 20 items). Frozen metric defs mirror the binary arm
  (adopt=final==ai_advice on dark; s1_correct; flip=adopt|s1_correct; capability=S1 acc). Frozen verdicts:
  REPLICATES iff R1 backend non-invariance (dark-adopt range >=0.25) AND R2 cap-vuln sign negative AND
  R3 persona ordering concordant (rho>0); else PARTIAL; NEGATIVE if uniformly-low adoption / sign flip /
  ordering reversed. Frozen exclusion: <50% parseable S2 decisions = instrument failure (as claude-haiku).
- Resumed the full 6-backend run detached (cache-backed). Next: write scripts/analysis/lsat_analysis.py,
  independent audit + Manager numeric re-derivation, then integrate as a task-structure paragraph.

## D5.59 LSAT gemini-2.5-pro config bug (499 crash) — fixed + retry hardened (Manager #5, 2026-07-24)
- The single clean LSAT run completed 5/6 backends (gpt-4o-mini 76s, gpt-4.1 528s, gpt-4o 2138s,
  gpt-5.5 3052s, claude-sonnet-4.5 5444s; results/lsat_axis2.json = 1200 rows, backed up to
  results/lsat_axis2_5backends.json.bak) then CRASHED on gemini-2.5-pro with unhandled 'API error 499'.
- ROOT CAUSE (mechanical): configs/lsat_axis2.yaml gave gemini-2.5-pro token_param=max_tokens, but
  gemini-2.5-pro is a REASONING model — every other working config (crossvendor/confirmatory/protective)
  uses token_param=max_completion_tokens + min_completion_tokens=4096. With only max_tokens=600 it
  exhausted budget on reasoning -> empty/timeout -> 499. FIXED config to match the working configs.
  (Provider applies effective=max(600,4096)=4096; cache key includes token_param so old bad gemini cache
  is bypassed and fresh calls are made.)
- HARDENING: openai_compat_provider._call_api now retries 499 (client-closed/timeout, transient) alongside
  5xx, so a single transient timeout can't nuke a multi-hour run. Additive-only; success path and all
  cached data unchanged.
- Relaunched single clean run (Start-Process, PID in lsat.pid); 5 backends replay from cache, gemini runs
  fresh with 4096-token budget. Prereg criteria (D5.58) UNCHANGED. Fix precedes any result inspection.

## D5.60 LSAT generalization RESULT — VERDICT: PARTIAL (Manager #5, 2026-07-24)
- Run COMPLETE: 6/6 backends, 1440 rows (results/lsat_axis2.json). Analysis: scripts/analysis/lsat_analysis.py
  -> results/lsat_analysis.json. Manager independent re-derivation from raw records MATCHES the script exactly
  (guarded ai_advice sign: it is EXPLICIT in trace, no 1-truth inversion; 720/720 dark ai_advice != truth;
  n_choices all 4). Parse-rate (cache-replay) >=50% for all 6 -> NONE excluded (gemini healthy post-fix).
- Per backend (dark): cap(S1) / agg-adopt / flip / p5-adopt:
  gpt-4o-mini .675/.242/.235/.600 ; gpt-4.1 .775/.208/.161/.750 ; gpt-4o .783/.267/.213/.850 ;
  gpt-5.5 .850/.042/.049/.100 ; claude-sonnet-4.5 .817/.108/.061/.250 ; gemini-2.5-pro .767/.250/.163/.700.
- Frozen verdict (D5.58): R1 non-invariance FALSE (agg-adopt range 0.225, just below 0.25); R2 cap-vuln sign
  TRUE (cap~flip rho=-0.829 p=.042 SIGNIFICANT at n=6; cap~adopt rho=-0.60 p=.21 right sign); R3 persona
  concordance TRUE (rho=0.899 p=.015; p5-novice-trusting top adopter in BOTH LSAT .54 and binary .90; p4
  lowest in both). No N-criterion triggered. => VERDICT = PARTIAL.
- Honest read: the capability-vulnerability MISMATCH (esp. flip) and the persona vulnerability ORDERING
  REPLICATE on a different task structure (4-way LSAT); gpt-5.5 (top capability) again shows lowest adopt/
  flip and flattens the p5 peak (.10 vs .60-.85 in weaker backends); single frontier covers 0/6 personas at
  tau=.5, full panel 1/6. Only R1 (aggregate spread) narrowly misses because 4-way LSAT compresses baseline
  wrong-advice adoption. Integrate as PARTIAL/qualified generalization AFTER independent audit.

## D5.61 LSAT audit APPROVE-WITH-CHANGES -> both fixes applied -> integrated (Manager #5, 2026-07-24)
- Independent code-review audit (lsat-audit subagent) + Manager re-derivation. Audit reproduced every
  headline number; confirmed sign correctness (no 1-truth inversion; 720/720 dark ai_advice!=truth),
  binary-loader parity, _parse_letter parity, no capability double-counting (S1 identical across conditions
  for 1440/1440 keys), verdict logic. Two findings, both fixed:
  1. [BLOCKER for instrument-health CLAIM] My D5.60 parse-rate fast-path filtered on RAW file text for the
     unescaped signature '{"choice"', but cache stores messages as ESCAPED JSON ('{\\"choice\\"'), so all
     LSAT cache files were fast-rejected -> parse_rate was NaN/total=0 and excluded={} was VACUOUS (the frozen
     <50% exclusion rule was never actually evaluated). FIXED: prefilter on plain unescaped 'Respond in JSON:'
     then json.load + check PARSED msgs[-1] content. Re-ran: parse rate = 1.00 for ALL 6 backends
     (gpt-4o-mini 581, gpt-4.1 516, gpt-4o/gpt-5.5/claude 432, gemini 449) -> excluded={} now VERIFIED.
     Verdict UNCHANGED (PARTIAL); gemini confirmed real decisions not fallbacks (s1acc .77 >> .25 chance).
  2. [OVERCLAIM] cap~flip p=.042 is jackknife-fragile (3/6 leave-one-out drops -> p=.19); SIGN robust
     (rho in [-1.0,-0.7] every subsample). Paper text reports it as a robust SIGN, not a significant
     coefficient, and discloses the fragility explicitly (mirrors the binary-arm tiering discipline).
- INTEGRATED into paper: new \subsection sec:lsat in sec:capvuln ("Does the mismatch survive a different
  task structure? (LSAT)") + updated the "two datasets/binary sentiment" Limitation + intro forward-pointer.
  Cited bansal2021whole (SAME uw-hai/Complementary-Performance source as beer/amzbook; corrected an
  initial wrong key bansal2021does before build). Rebuilt clean: 15pp, no undefined refs/cites.
- Honest result stated: persona ordering (rho=0.90, p=.015) + cap-vuln SIGN + coverage inversion replicate
  on 4-way LSAT; aggregate non-invariance magnitude does NOT (range 0.225<0.25, compressed by harder task).
  Reported as PARTIAL generalization, closing the "one task family / binary sentiment" reviewer critique.

## D5.62 Writing polish (WRITING LEAD, 2026-07-27) — de-dup + abstract rhythm + dash reduction; no claim/number change
- (2) De-duplicated the abstract<->intro<->contributions triangle: stripped the THIRD copy of result
  numbers/narration from intro contributions (i)&(ii) (removed "up to 0.60", the "aggregate...propagates
  stably" restatement, and the "strongest backend...surfaces almost none...recovers" re-narration). Each
  contribution now states WHAT we give, not a third re-listing of findings. Kept RQ->answer paragraph as the
  numeric anchor; (iii)(iv) unchanged.
- (1) Abstract reweighted for rhythm: 7 mega-sentences (~74 words/sent) -> ~19 sentences; em-dashes 10 -> 2;
  single paragraph preserved; every number and claim retained verbatim.
- (3) Dash-density pass on prose-heavy, high-visibility spots only (intro "Our stance"; Discussion
  point-estimate para; Conclusion open/close). Whole-file em-dashes 151 -> 128. Left legitimate single
  appositive dashes in results prose untouched (not mechanical).
- Build: pdflatex->bibtex->pdflatex x2 clean; 15pp; 0 undefined ref/cite. Pure writing polish, not a content
  change.

## D5.62 Novelty/collision audit refresh — VERIFIED (Manager #5, 2026-07-27)
- Re-ran the collision audit (research subagent + Manager independent arXiv-meta verification of the two
  top-threat papers). Overall risk MEDIUM (unchanged from D5.55); NO paper pre-empts the compound; field is
  converging on LLM-simulation-instability + LLM-dark-patterns, so ~5 differentiating cites are needed.
- RIGOR CATCH (again): the subagent dropped an author on arXiv:2602.21262 (reported 4; arXiv meta = 5, incl.
  Kerem Oktar). Manager re-verified 2602.21262 and 2601.17087 from authoritative arXiv <meta citation_*>.
  All author lists must be re-verified at cite time; search snippets are not authoritative.
- Highest threat = arXiv:2601.17087 "Lost in Simulation" (Seshadri, Cahyawijaya, Odumakinde, Singh,
  Goldfarb-Tarrant; ICLR 2026): independently shows LLM-simulated USERS are backend-sensitive (agent success
  ±9pp across user-LLMs) — but frames it as MAGNITUDE + human-correspondence validity + demographic fairness
  on agentic task completion; ours is CLASSIFICATION-flip of interface-content risk, disclaims human
  correspondence, failure-targeted persona. Must cite + qualify any "first" wording.
- Second = arXiv:2602.21262 "Under the Influence": capability/persuasion/vigilance are DISSOCIABLE at the
  LLM-agent level — corroborates Contribution-2 (capability != resistance); cite as support, distinguish
  our simulated-USER level; note dissociable vs our inverse-correlation nuance.
- Full verified list + differentiation + actions saved to docs/plans/2026-07-27-collision-audit-verified.md.
  No paper changes made yet; adding cites + softening the "first" claim is a Related-Work/claim-strength
  edit reserved for the writing session under owner sign-off.

## D5.63 Writing polish round 2 (WRITING LEAD, 2026-07-27) — sentence-splitting + one Discussion de-dup; no claim/number change
- Related Work: split two mechanical chained sentences ("appropriately rely...; recent work benchmarks..."
  -> two sentences; "swing results...; a generalizability-theory decomposition..." -> two sentences).
- Results: split the two longest sentences in sec:variance (generation-variance run) and one in sec:capvuln
  (RAIR/RSR faithful-condition sentence) at clause boundaries. Zero numbers touched.
- Discussion (commercial tooling): the three actionable points are the setup->payoff answer to the intro's
  two assumptions and were KEPT. Trimmed only the nested statistical parenthetical that re-derived the
  capvuln robustness tiering a 3rd time (dropped verbatim "BH-significant at n=11 / jackknife-robust /
  amzbook-carried"; kept the honest "robust for aggregate, suggestive for finer flip/p5" + section ref).
  Saves ~30 words, removes a nested paren; no claim change.
- Build clean: 15pp, 0 undefined ref/cite. Pure writing polish.

## D5.64 Writing polish round 3 (WRITING LEAD, 2026-07-27) — Method/Definitions + figure captions; no claim/number change
- Method: split the "Stimuli and datasets" three-clause semicolon sentence; restructured the "Rigor spine"
  opener (removed mid-sentence "---with a UTC-timestamped, committed record---" interruption, moved to a
  trailing clause; split the following semicolon into its own sentence); Panel-def dash -> period.
- Captions: fig:ladder legend split into separate sentences (error bars / lines / dashed line);
  fig:protective staircase caption split at the "but" clause.
- Build clean: 15pp, 0 undefined ref/cite. Pure writing polish.

## D5.65 Consistency scan (WRITING LEAD, 2026-07-27) — number/format normalization; no claim/number change
- p-value leading zeros: LSAT-section "p=.015/.04/.19" -> "p=0.015/0.04/0.19" to match the paper-wide
  leading-zero convention (p=0.003, 0.60, etc.).
- Inline-stat "{=}" tight-spacing normalized to plain "=" for n/k/tau/rho (n=6, n=11, k=10, tau=0.5,
  rho=0.90) to match p=, OR, and most rho= usages. LEFT the probability-definition {=}/{\ne} pairs in the
  RAIR/RSR and parser equations untouched (internally consistent as a pair).
- Verified already-consistent: System-1/System-2, gpt-*/claude-*/gemini-* lowercase IDs, amzbook, backend
  (no "back-end"), over-reliance, backend-dependent, Figure~\ref / Section~\ref tildes. The two
  "trusting novice"/"wrong advice" without hyphen are correct NOUN-phrase uses (vs. attributive
  "trusting-novice persona" / "wrong-advice adoption"), left as-is.
- Build clean: 15pp, 0 undefined ref/cite.

## D5.66 Multi-model audit (3 agents: GPT-5.6 / Claude-Opus-4.8 / Gemini-3.1-pro) — fixed 7 low-risk items (2026-07-27)
- Dispatched 3 independent audit agents (framing / stats-rigor+JSON-spotcheck / relwork-clarity). Applied
  only the unambiguous corrections + honesty-qualifications; framing/novelty items deferred to owner.
- FIXED: (1) "3,600 trials" arithmetic -> added the "x two UI conditions" factor (3x2x6x20x5=3600).
  (2) amzbook coercion OR 1.17 now reports CI[1.04,1.31], p=0.010 + "much smaller". (3) added an 8-item-
  cluster caveat to the pooled coercion OR (approximate/anti-conservative; same few-cluster caution as the
  disowned interaction test; beer robust, amzbook fragile). (4) "0/3 vendors above chance" ->
  "none of the three frontier models is significantly above 0.5". (5) Vasconcelos2023 mis-attribution fixed
  (its title is "Explanations Can REDUCE Overreliance...") -> removed from the "increase" clause, relocated
  to the intervention/reduce clause. (6) GEE expanded on first use (generalized estimating equation).
  (7) persona OR~26 near-ceiling separation: added "OR magnitude not a precise effect size; model-free
  primary evidence = strict top adopter in 12/12 cells".
- All are corrections or honesty-increasing qualifications consistent with the paper's tiering discipline;
  no headline claim reversed. Build clean: 15pp, 0 undefined ref/cite.
- DEFERRED to owner (framing/claim-strength): (B) add Seshadri "Lost in Simulation" (ICLR2026,
  arXiv:2601.17087) + Robinson/Oktar "Under the Influence" (arXiv:2602.21262) and qualify "rarely tested"
  wording (corroborated by 2 agents + the 2026-07-27 collision audit). (C) GPT-5.6's aggressive reframes
  (retitle, demote axis-1, "endogenous coverage", threshold/usable) — manager recommends DECLINE most as
  the paper already concedes them; owner to adjudicate. Optional: few-cluster REANALYSIS of coercion OR;
  human-anchor supplement verification (GLMM non-convergence noted by stats agent).

## D5.67 Audit follow-through: related-work cites + few-cluster reanalysis + anchor disclosure + C micro (2026-07-27)
- B (RELATED WORK, owner-approved): added Seshadri "Lost in Simulation" (arXiv:2601.17087, ICLR 2026) and
  Robinson et al. "Under the Influence: Quantifying Persuasion and Vigilance in LLMs" (arXiv:2602.21262) to
  Related Work "Simulated users" para + differentiated (magnitude vs risk-flip; task-success vs interface-
  safety; they center human correspondence, we disclaim it; Robinson corroborates capvuln inversion at LLM-
  agent level). Author lists VERIFIED from arXiv API (https://export.arxiv.org/api).
  *** DISCREPANCY FOR OWNER: arXiv API now lists 2602.21262 with 4 authors (Robinson, Collins, Sucholutsky,
  Allen) -- NO Kerem Oktar -- but the 2026-07-27 collision audit recorded 5 authors incl. Oktar
  (Manager-verified). Bib currently uses the live 4-author list; confirm whether to restore Oktar. ***
- COERCION FEW-CLUSTER REANALYSIS (Opus#1, owner asked to run): new scripts/analysis/coercion_fewcluster.py
  re-estimates the pooled dark OR with item random-intercept VB mixed model, item fixed effects, and an
  item-cluster bootstrap (results/coercion_fewcluster.json). RESULT: beer robust (OR 2.02/1.92/1.93, all
  exclude 1); amzbook method-dependent (VB OR 1.22, CI 0.93-1.61 crosses 1) -> text now reads amzbook as
  DIRECTIONAL ONLY. Integrated into sec:coercion (replaced the generic 8-cluster caveat).
- ANCHOR DISCLOSURE (Opus#8, owner asked to verify source): the 0.74 / 0.32-0.41 come from split-half
  reliability in src/twdf/experiments/e1_decomposition.py (PRIMARY; GLMM is intentionally bounded optional
  corroboration, non-convergence is by-design). Disclosed: GLMM did not converge + one AI condition
  (expert-adaptive) has degenerate NEGATIVE split-half reliability, excluded from the 0.32-0.41 range.
- C MICRO (owner-approved, from GPT-5.6): (a) capvuln "faithful reproduction of human failure modes" ->
  "reproduction of the high-severity failure cells the panel surfaces" (removes implied human validity);
  (b) added an explicit ESTIMAND sentence (specification sensitivity across panel implementations, not
  latent-construct invariance); (c) flip 0.60 annotated as the mechanical max for six backends (3-3 split).
- Also earlier D5.66 fixes retained. Build clean, 0 undefined ref/cite. PAGE COUNT: 15 -> 16 (16th page is
  appendix/refs overflow from the Seshadri para + reanalysis + disclosures). OWNER DECISION: keep 16 or claw
  back to 15 by deeper trimming.
- DECLINED (manager judgment, per owner "C micro only"): GPT-5.6's retitle / demote-axis-1 / move-bugs-to-
  appendix / "usable"-removal -- the paper already concedes these; left for owner if desired.

## D5.68 Framing decisions (GPT-5.6 audit, owner-adjudicated one-by-one, 2026-07-27)
Discussed each GPT-5.6 framing issue with owner; applied the approved subset (framing/claim-strength =
owner call). Decisions:
- #2 axis-1/title: KEEP title + dual-axis; explicitly SECONDARY-IZE axis-1. Added an intro signpost
  ("axis-2 is load-bearing; axis-1 is a secondary, exploratory signal, human counterpart null") + relabeled
  Contribution 4 "(axis-2 load-bearing, axis-1 exploratory)". Did NOT retitle or demote to non-contribution.
- #6 protective "usable": SOFTENED. sec:protective now says the panel registers "the direction of a
  directly-instructed manipulation, not validated comparative-screening skill" (interventions directly
  instruct deliberation/verification). Kept the relative>absolute point + "Usable, with a caveat".
- #7 null placement / abstract "trusted": owner chose NO CHANGE (body already disclaims predictive validity).
- #9 commercial "rests on": SOFTENED to "a platform following standard engineering defaults would plausibly
  adopt" (intro + Discussion), removing the straw-practice assertion.
- #1 coverage endogeneity: added "high-severity by the panel's own adoption, not a verified human criterion"
  at the set-cover definition (plus the earlier "faithful/human failure modes" wording fix in D5.67).
- #5 abstention 0.2: annotated "illustratively and not yet calibrated" (plus the earlier flip=3-3
  mechanical-max note).
- #11 bugs/E6 in contributions: Contribution 4 now reports the self-caught bugs "as methodological
  transparency, not claimed as a separate contribution" (kept in body; NOT moved to appendix).
- DECLINED (owner): retitle, demote axis-1 out of contributions, move bug-history/E6 to appendix.
- Build clean: 16pp (unchanged), 0 undefined ref/cite. Framing edits only; no numbers changed.

## D5.69 Full-document final consistency scan (WRITING LEAD, 2026-07-27)
- Read the whole paper post-edits + automated scans. Caught + fixed one real cross-section CONTRADICTION:
  body sec:coercion now reads the amzbook coercive effect as "directional only" (CI crosses 1 under the
  few-cluster reanalysis), but the abstract and intro RQ-answer still presented "1.17 on the other" as part
  of a confirmed effect. Qualified both to "a weaker[/less robust] 1.17 on the other" for consistency.
- Removed a "directly/directly-instructed" echo in the softened protective sentence.
- Verified clean: 0 doubled words; 0 undefined ref/cite; p-value leading zeros consistent (0 bare p=.);
  stat "=" spacing consistent (0 stray {=} outside probability defs); GEE defined before first rendered use;
  no leftover "more dependable instrument". em-dashes 131 (normal). new cites seshadri2026lost /
  robinson2026influence resolve. Build clean, 16pp.
- Left as correct-by-grammar: vasconcelos2023explanations still cited in the intro axis-2 background list
  (defensible; the Related-Work "increase" mis-attribution was the one fixed in D5.66).

## D5.70 E6 human-task LOCAL PROTOTYPE built (2026-07-27)
- Owner will recruit volunteers via advisor's network (NOT Prolific); wants a local runnable prototype
  first, hosting/data-backend deferred. Built e6-prototype/index.html: self-contained single-file web task
  (no server, offline). Flow = consent -> instructions -> 3 blocks Faithful/Placebo/Dark (order randomized)
  -> per-trial Step1 no-AI decision+confidence then Step2 AI advice+framing+final decision+confidence (RTs
  logged) -> trusting-novice questionnaire+background -> debrief -> download JSON/CSV (+localStorage).
  Dark = guaranteed-wrong 1-truth at 92% + coercive authority text; adopt_wrong_ai is the axis-2 human DV.
  JS syntax-checked (node --check OK). README documents run + the freeze-before-real-run checklist.
- FLAGGED to owner (methodological): volunteer sampling from an advisor's (academic) network likely skews
  skilled/AI-literate -> compresses the trusting-novice-index variance -> underpowers H2 (persona
  localization). Mitigate by purposive recruiting for a spread (include non-experts/older/less-AI-savvy) and
  reporting the achieved index range. H1 (coercion works on humans) is unaffected. IRB still REQUIRED
  (deception + debrief) regardless of recruitment channel.
- Stimuli/index/predictions are PLACEHOLDERS; §6 freeze checklist + IRB must precede any data collection.

## D5.71 E6 prototype: multilingual UI (2026-07-27)
- Owner wants a language dropdown (default English + zh/ja/de/...) on the first page for a global sample.
- Refactored e6-prototype/index.html to full i18n: I18N dict (en/zh/ja/de, 52 keys each, VERIFIED parity),
  t(key,{vars}) with English fallback, language <select> on the consent screen (re-renders live; chosen lang
  logged per participant + in CSV). JS syntax-checked (node --check OK). Also improved onboarding earlier
  (task explanation + worked example + practice trial) and an optional confident-rationale dark AI.
- SCIENTIFIC BOUNDARY flagged to owner: REVIEW STIMULI stay ENGLISH on purpose. Translating the real Bansal
  items changes item difficulty and breaks comparability with the synthetic panel (run in English); non-en
  UI shows a "(review shown in English)" note. Whether to translate stimuli is a research decision (affects
  item validity + panel-match) for owner + advisor + IRB, not a prototype default.
- Adding a language = add one dict entry keyed like en.

## D5.72 EXPLORATORY probe: dark + fabricated rationale REDUCES synthetic adoption (2026-07-27)
- Owner (E6 design): considering a "confidently-wrong rationale" (一本正经地胡说八道) dark AI to make the
  manipulation more tempting. Explored option (B): re-run the synthetic panel with a rationale-augmented
  dark condition to see the effect BEFORE committing.
- ADDITIVE library change (no existing condition altered; 21 tests pass): bansal_tasks.py new condition
  "Wrong-AI-GT (dark-rationale)" = the SAME guaranteed-wrong dark prompt + an injected per-item confident
  fabricated justification (set_dark_rationales / _DARK_RATIONALES); displayed_ai_advice unchanged (1-gt);
  ui_features maps the new condition to wrong_ai + authority. Probe: scripts/analysis/dark_rationale_probe.py
  + configs/dark_rationale_probe.yaml. Rationales generated once by gpt-4.1 (cached results/dark_rationales_beer.json).
- RUN: 2 backends (gpt-4.1 over-relier, gpt-5.5 resistant) x 6 personas x 10 hard beer items x {dark, dark-rationale}.
  RESULT (results/dark_rationale_probe.json): adding the rationale DECREASED wrong-advice adoption:
  gpt-4.1 0.700->0.550 (-0.15); gpt-5.5 0.217->0.183 (-0.03); p5 gpt-4.1 1.00->0.90, gpt-5.5 0.60->0.30.
  Baseline dark (0.70/0.22) matches the paper's gpt-4.1/gpt-5.5 beer levels -> harness sane, delta real.
- INTERPRETATION: cue-only coercion gives agents nothing to refute; a checkable (wrong) rationale is a target
  the LLM verifies against the text and REJECTS -> lower adoption. Opposite of the "more tempting" intuition
  for synthetic agents (humans may differ -> a panel<->human divergence risk for H3 matching).
- RECOMMENDATION to owner: prefer option (A) -- solve "too-obvious items" via harder/ambiguous item selection,
  keep the dark manipulation cue-only + matched between panel and humans. If rationales are still wanted for
  humans, run them as a SEPARATE arm (the panel's prediction there is LOWER adoption -- a clean testable claim).
- EXPLORATORY only (N=10, one seed/domain, one rationale style); not preregistered, not paper content.

## D5.73 E6-stripped PREREGISTRATION drafted (2026-07-28)
- Owner asked (framing) whether E6 proves "AI misleads humans" -> clarified: NO; E6 validates the SYNTHETIC
  PANEL against humans (closes the panel<->human NULL). H1 (coercion works on humans) is only a manipulation-
  validity precondition; payload is H2 (which PERSON is at-risk) + H3 (which BACKEND tracks humans).
- Owner asked how to "cleverly design to boost acceptance": declined the rig-the-conclusion version (fraud +
  self-defeating for a paper whose brand is honesty); reframed to the LEGITIMATE version = maximize detection
  SENSITIVITY + make all outcomes publishable + preregister (removes the incentive to cheat).
- WROTE docs/plans/2026-07-28-e6-stripped-prereg.md (DRAFT, not frozen, no IRB yet): frozen H1-H3 with
  all-outcomes-publishable mapping; within-subject 3-interface design; Dark kept CUE-ONLY + matched to the
  synthetic arm (basis: D5.72 rationale probe -> rationale REDUCES synthetic adoption, so no rationale);
  conflict-eligible/ambiguous items for sensitivity; advisor-network sampling caveat + purposive-spread
  mitigation for H2; N~40 with pre-set floor->60 rule (one wave); frozen measures + trusting-novice index;
  pre-logged 4-backend predictions before data; frozen analysis plan (H1 paired/perm, H2 mixed index x
  interface, H3 model-ranking, BH within family); explicit integrity commitments (no optional stopping /
  no post-hoc exclusion / no p-hacking / no demand beyond the disclosed IV); freeze checklist + IRB gate.
- Not paper content; a plan artifact for owner + advisor + IRB to finalize.

## D5.74 E6 pilot-ready prototype + a-priori power analysis (2026-07-28)
- POWER (scripts/analysis/e6_power.py, Monte Carlo): H1 (within-subject coercion) power ~1.00 at N>=40 even
  for the smallest modelled gap -> safe at any feasible N. H2 (between-subject index moderation) is the
  binding constraint: moderate moderation (gap 0.25) power 0.71 (N40) -> 0.90 (N60, balanced) / 0.82 (N60,
  academic skew frac_high=0.30); small moderation (gap 0.15) < 0.65 even at N80 -> declared not detectable.
  => RECOMMEND N~=60 (not 40), one wave, + PURPOSIVE recruiting for index balance (0.90 vs 0.82 at N60).
  Updated prereg §4 with these concrete numbers (revised target 40 -> 60).
- PROTOTYPE now PILOT-READY: dumped 18 real held-out conflict-eligible beer items (select_hard_items,
  seed 2024) -> e6-prototype/_items_beer.json, embedded as ITEMS_POOL. Latin-square-ish rotation (shuffle
  pool -> 3 sets -> 3 interfaces in randomized order per participant; item_assignment logged). AI advice now
  uses the model's REAL ai_pred/ai_conf for Faithful/Placebo; Dark = 1-truth cue-only (darkRationale=false,
  FROZEN per prereg; rationale removed since D5.72 showed it reduces synthetic adoption). CSV adds lang +
  dark_rationale. JS syntax OK; i18n parity 52 keys x4 intact. README updated (incl. the 50-beer-task
  constraint: 18 items = 6/interface for pilot; ~15/interface needs most of the set or a 2nd domain).
- These real reviews are genuinely mixed/subtle -> directly fixes the owner's "too-obvious items" concern
  via item selection (option A), keeping the manipulation matched.

## D5.75 Switched to CHI 2026 submission format (2026-07-28)
- Owner: use the CHI official acmart template (docs/paper/acmart-primary/). Verified that folder's
  acmart.cls is IDENTICAL to MiKTeX's (both v2.19, 2026/06/27) -> no compile change needed from the class.
- CHI 2026 submission format (verified via chi2026.acm.org): single-column, anonymous, line-numbered
  \documentclass[manuscript,review,anonymous]{acmart} (camera-ready would be [sigconf]). Changed main.tex
  from [sigconf,review,anonymous] -> [manuscript,review,anonymous].
- Rebuilt clean: 23pp (was 16pp double-column; single-column manuscript is less dense per page -- EXPECTED
  and normal for CHI review format; CHI has no fixed page limit, references excluded, length should match
  contribution). 0 undefined ref/cite; 1 tiny overfull hbox (5pt, Contribution-4 bold phrase) left for
  camera-ready. Line numbers/folios active (review mode).
- acmart-primary/ left UNTRACKED (identical to MiKTeX's; committing the ~2MB template bundle is a repo
  decision for owner). Content/claims/numbers unchanged -- format only.

## D5.75b acmart-primary template PINNED in repo (owner chose B, 2026-07-28)
- Committed the CHI official acmart v2.19 bundle under docs/paper/acmart-primary/ (43 files). Force-added
  acmart.cls (the template's own .gitignore excludes it as a generated file). ACM-Reference-Format.bst +
  top-level biblatex (.bbx/.cbx/.dbx) + acmart.bib included. Build still uses MiKTeX's identical v2.19; the
  in-repo copy pins the version for reproducibility. Large docs (acmart.pdf/acmguide.pdf) + sample PDFs
  remain ignored by the bundle's own .gitignore.

## D5.76 Writing-craft round (3 reviewers) — Group A language-only polish (2026-07-28)
- Dispatched 3 writing reviewers (Claude-Opus narrative craft / Gemini readability / GPT-5.6 high-leverage
  passages). Strong convergence: enliven flat passages, lead captions with the takeaway, gloss jargon, de-
  hedge, coin a memorable image for capability-vulnerability, repeat one canonical thesis, tighten titles.
- APPLIED Group A (pure language, zero claim/number change): (1) skimmer topic sentences ("The current
  debate over synthetic users...", "The panel's internal disagreement (axis-1)..."); (2) enlivened the
  variance-decomposition opener, the axes->decision paragraph, the psychometrics paragraph, and added an
  Axis-1 intuition sentence (+ glossed "over-dispersion"); (3) figure captions now lead with the takeaway
  (fig1 "adoption swings widely... stronger != more compliant"; fig7 "adding the strongest models first is
  the wrong strategy", dropped "submodular set-cover" as the lead); (4) titles: sec:definitions -> "Two Ways
  a Design Fails, Made Measurable"; "Where the variance comes from" -> "Everything the analyst chooses moves
  the number"; "(anchor)" -> "The human failure is real, and measurable"; (5) added a "Roadmap of the
  results" arc-signpost at the top of the results.
- DECLINED from the reviews (conflicts w/ prior honesty decisions): moving the coercion few-cluster
  reanalysis to an appendix (D5.67 kept it in body); dropping the amzbook numbers from the abstract.
- DEFERRED to owner (Group B, framing/voice): full abstract rewrite (GPT-5.6 version, keeps all numbers);
  the crash-test-dummy metaphor + one canonical thesis line x5; de-hedging the persona-check section
  (relocate not remove); discussion-opening + conclusion rewrites; optional punchier subtitle.
- Build clean: 23pp, 0 undefined ref/cite.

## D5.77 Writing-craft Group B (owner-approved, per manager recommendations) (2026-07-28)
- B1 ABSTRACT (hybrid): kept the 4 bold signpost labels (Unstable/Stable/Most consequential/Usable) AND
  adopted GPT-5.6's paragraph breaks + new hook ("look safe on average and still fail"; "flags the risk in
  minutes") + new close ("Before synthetic panels can predict people, their own danger readings must
  survive a change of instrument"). ALL numbers preserved.
- B2 crash-test metaphor: added "you would not crash-test with your safest driver" once in sec:capvuln and
  once in the Discussion "Capability is not validity" para (true to RSR=0.92). Threaded the canonical thesis
  "the backend is part of the measurement instrument" across intro idea / Discussion (title) / Conclusion.
- B3 persona-check: LIGHT de-hedge only — lead with the claim ("a successful manipulation check") and keep
  the core caveat ("prompt-defined, not a discovered human vulnerability"); did NOT strip the section's
  protective hedging wholesale (that hedging pre-empts the circularity critique).
- B4 Discussion + Conclusion rewrites (GPT-5.6): "More capable is not more valid" -> "Capability is not
  validity"; "Disagreement is information" -> "Disagreement should trigger abstention, not averaging";
  Conclusion paragraphed, ending on "the most trustworthy synthetic panel is not one that always answers.
  It is one that knows when to abstain."
- B5 subtitle: KEPT descriptive (owner) to avoid overpromising a synthetic-vulnerability finding; the
  crash-test spice lives inside the paper.
- Build clean: 24pp (was 23; abstract paragraphing + rewrites), 0 undefined ref/cite. No numbers/claims
  changed; voice/emphasis sharpened per owner sign-off.

## D5.78 Results-momentum pass (A: story-beat openers; 2026-07-28)
- Grounded in a check of CHI best-paper craft (three-act arc, hook, tension, signposting, trim the fat).
  Verdict given to owner: the FRAME (abstract/intro/discussion/conclusion + crash-test) is now best-paper
  grade; the RESULTS middle was still audit-dense. Owner asked for an A+B momentum pass.
- APPLIED A (story-beat opening sentences; pure language, zero number/claim change) to connect the results
  into a narrative: sec:modeldep ("Start with the first number a practitioner reads off..."); sec:instability
  ("If the aggregate reading is this model-specific, does the DECISION move with it? ... They do not.");
  persona-check ("Is anything about the panel stable? One thing is."); sec:capvuln ("Now the study's most
  unsettling turn."); sec:lsat ("Could all of this be an artifact of one task type?").
- B (light trimming) applied CONSERVATIVELY: held off aggressive cuts in the dense results to protect the
  honest detail (owner's stated value); the coercion reanalysis and number-dense passages left intact.
  Can do targeted trims later if owner points at specific passages.
- Held (owner deferred): option C (moving the human-anchor subsection ahead of the backend-dependence
  result) -- not done.
- Build clean: 24pp, 0 undefined ref/cite.

## D5.79 Final consistency scan after writing-craft rounds (2026-07-28)
- Automated: 0 doubled words, 0 bare p-values (leading zeros consistent), 0 stray inline-stat {=}, 0
  undefined ref/cite, em-dashes 137 (normal), crash-test metaphor appears exactly 2x, abstract has its
  intended 6 paragraph breaks.
- CAUGHT + FIXED one real redundancy the momentum pass introduced: the sec:modeldep "Reading." paragraph
  already ended with almost the exact question I gave as the new sec:instability opener ("...does the
  decision a screen would make move with it?"). Rewrote the Reading paragraph to tee up the coercion
  question instead (which is the section that actually comes next), so the question now appears once, and
  the forward-pointer is correct (5.2 -> coercion 5.3 -> instability 5.4). New openers otherwise connect
  cleanly.
- Build clean: 24pp, 0 undefined ref/cite.

## D5.80 AI-tell sweep per owner's polishing guide (润色指南.docx) (2026-07-28)
- Read the owner's Chinese guide (extracted from .docx): the same 6 AI-tell principles as our house style
  (vague/grandiose; tidy-but-repetitive; missing concrete detail; over-safe hedging; templated
  transitions; mechanical punctuation) + "natural first, then technical depth".
- Systematic scan found the paper already very clean: 0 unsourced hedges; no delve/leverage/realm/unlock/
  reshape/seamless/etc.; templated connectives only "Crucially" x2; vague only "a wide range of" x2.
- FIXED surgically (no claim/number change): removed both "Crucially," intensifiers; "across a wide range of
  thresholds" -> "across most of the plausible threshold range" / "across most plausible thresholds" (x2);
  "and---critically---" -> "and, critically,"; "compress---or stand in for---weeks" -> "compress (or stand
  in for) weeks".
- Deliberately did NOT mass-convert em-dashes/semicolons: the remaining ~133 dashes are overwhelmingly
  functional appositive definitions (e.g., "flip rate---the fraction...---peaks"), which the guide
  explicitly says are fine; blanket removal would over-sanitize (itself a tell) and hurt clarity. Punctuation
  judged together with the (near-zero) other tells, per the guide.
- Build clean: 24pp, 0 undefined ref/cite.

## D5.81 CHI-reviewer response, part 1: #4 CHI framing/workflow, #5 threshold reframe, #6 result tiers (2026-07-28)
- Owner shared a simulated CHI reviewer's 5-point critique; decided "#2 run ablation first; #3 middle
  path; the rest per my recommendations." This entry covers the pre-approved low-risk edits (#4/#5/#6).
- #6 (result hierarchy): added inline tier tags to every Results subsection --- [Anchor.],
  [Primary (RQ1).] x3 (modeldep/coercion/instability), [Mechanism (RQ2).] (variance),
  [Mechanism (RQ3): manipulation check.], [Mechanism: capability--vulnerability.],
  [Boundary: preregistered robustness.] (LSAT), [Boundary: practical use (RQ4).] (protective),
  [Boundary: honest null.] (corr). Roadmap paragraph now names the three tiers. Used FUNCTIONAL tiers
  (primary/mechanism/boundary) not registration-status labels, to avoid over-claiming what was
  preregistered vs post-hoc.
- #4 (CHI positioning): added a boxed 6-step "backend-aware protocol for synthetic-user interface
  screening" (fig:protocol) at the top of Discussion --- coverage-not-capability panel, distribution-not-
  point, decision-flip + threshold-free range, persona-policy ablation, abstain-on-disagreement, prefer-
  relative-to-absolute; each step cites the grounding section. In-text pointer in the abstention paragraph.
  (Intro Scope paragraph already disclosed content/framing-not-pixels, so no new disclaimer needed.)
- #5 (threshold calibration): in sec:instability, flip rate now read as "decision instability conditional
  on whatever operating threshold a team adopts", not a calibrated safety classifier (tau not validated
  against human harm); threshold-free companions (adoption range 0.15--0.66, Fleiss' k) named.
- No claims/numbers changed; all additions are framing/organization. Build clean: 24pp, 0 undefined
  ref/cite. #2 dispositional ablation running (configs/dispositional_ablation.yaml); #3 mostly already
  satisfied (axis-1 already named "synthetic persona disagreement", flagged non-validated) --- pending
  owner review + ablation result.

## D5.82 CHI-reviewer response, part 2: B2 single-axis restructure + retitle + abstract cut (2026-07-28)
- Second simulated CHI reviewer (6 points + admin risk). Owner decisions: A1 (expand core to 50 items,
  background), B2 (single-axis, move axis-1 to supplement, retitle to strongest finding), C (cut abstract).
- FACTS verified: (a) Seshadri "Lost in Simulation" is now ACL 2026 long paper (aclanthology 2026.acl-long.2192),
  NOT concurrent -> to fix. (b) PDF metadata already clean (no /Author; Title only) -- reviewer's "metadata
  leaks Eloise Zhang/Beyondsoft" is FALSE for current main.pdf. (c) Item ceiling = 50/domain in Bansal, so
  "20->100+" infeasible; 50 is the realistic max (=> A1 scoped to all-50). (d) abstract was 547 words.
- TITLE (owner pick): "Don't Crash-Test with Your Safest Driver" / subtitle unchanged (Backend-Sensitivity
  Audit of Synthetic-User Interface-Content Risk Measurement). Metadata confirms updated + no author leak.
- B2 (single-axis, contributions preserved): abstract rewritten ~250w single-axis (coercion/backend-flip/
  capability-vulnerability/protocol; dropped 4 bold labels + axis-1). Intro two-axis itemize -> single
  load-bearing coercion axis + over-dispersion demoted to companion diagnostic pointing to appendix.
  Contribution #4 reworded: "measurable two-axis construct" with coercion axis validated + over-dispersion
  as candidate diagnostic (supplement) -- NO contribution dropped. Fixed all "two axes/two-axis" prose
  (intro, RQ preamble, contributions framing sentence removed). §3 definitions keep both axes but flag
  axis-2 load-bearing / axis-1 -> Appendix.
- RELOCATED to new Appendix "Supplement: The Over-Dispersion Axis" (\label{app:overdispersion}): the human
  over-dispersion anchor (old §4.1), the synthetic-persona-disagreement paragraph + Fig.3 (fig:collapse),
  and the panel<->human correspondence null (old sec:corr). Left comment-pointers in main; roadmap updated;
  tier list dropped the honest-null boundary item. sec:corr/fig:collapse labels now live in the appendix.
- Build clean: 24pp, 0 undefined ref/cite, no multiply-defined labels. Numbers still 20-item; A1 (50-item)
  refresh pending. STILL TODO: Seshadri bib+Intro hardening (#3), interface->interface-framing terminology
  (#6), flip-rate bootstrap/CI-aware reframe (#1) -- best done on 50-item data.
