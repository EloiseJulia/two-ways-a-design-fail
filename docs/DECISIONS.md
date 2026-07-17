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

## Cross-cutting rigor commitments (standing)
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
