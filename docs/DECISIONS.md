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

---

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
