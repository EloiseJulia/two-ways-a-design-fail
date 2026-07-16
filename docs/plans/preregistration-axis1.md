# Preregistration — Confirmatory Axis-1 Panel Run (H1a)

> **A-PRIORI DESIGN LOCK.** The choices in §§1–7 below are frozen **2026-07-15T09:23:55Z**,
> which is **BEFORE** the exploratory multi-family pilot (PR #8) is RUN. They were NOT chosen
> based on any axis-1 effect. The exploratory pilot may inform ONLY the **power target N**
> (§8), and its data are EXCLUDED from the confirmatory analysis. Any later change to §§1–7
> must be logged with a reason + timestamp (researcher-DoF discipline). This file is a DRAFT
> only in that §8 (N) is completed post-pilot; §§1–7 are LOCKED as of the timestamp above.

## 1. Hypothesis (confirmatory, falsifiable) — H1a (SPEC §3)
Under difficulty-controlled **within-task counterfactual differencing**, an increment in
multi-agent **panel disagreement** predicts an increment in human reliance **over-dispersion**
(between-user, beta-binomial, separated from binomial noise), **significantly better than four
noise baselines** (random, mean-predictor, prompt-only, single-model), with a bootstrap CI that
**excludes 0**. Secondary (mechanism) view: across the ≥5 UI conditions, the Spearman
correlation between panel disagreement and human over-dispersion is **significantly positive**.

## 2. Panel model set (frozen a-priori for DIVERSITY, independent of any pilot effect)

> **AMENDMENT 2026-07-16T02:29:50Z (PI decision, provider-stability driven — NOT effect
> driven):** The confirmatory panel model set is CHANGED from
> {`openai/gpt-4o`, `meta/Llama-3.3-70B-Instruct`, `microsoft/Phi-4`} to the STABLE
> OpenAI family on GitHub Models: **{`openai/gpt-4o`, `openai/gpt-4.1-mini`}**, run
> **day-batched** across their separate per-model daily buckets (no Azure dependency).
> **WHY:** the exploratory pilot (PR #8) invoked the pre-registered §2 PIPELINE-only
> exclusion rule — `meta/Llama-3.3-70B-Instruct` (and by extension the non-OpenAI
> families) exhibited a documented PIPELINE FAILURE on GitHub Models: frequent 60s read
> timeouts, HTTP 500s, and **unparseable System-2 outputs that defaulted to 0** (a
> degenerate parse). This exclusion is by the pre-committed rule, on a pipeline
> diagnostic, NOT on any axis-1 result (the pilot produced NO clean axis-1 estimate).
> The non-OpenAI families are retained as EXPLORATORY-ONLY and documented as a
> provider-stability limitation. This amendment REDUCES cross-family scope to
> capability-tier diversity WITHIN the OpenAI family (strong gpt-4o vs small
> gpt-4.1-mini); the multi-vendor triangulation (SPEC §4.2) is deferred to a future
> Azure run where non-OpenAI families can be hosted reliably. Original set preserved
> below for provenance.

**AMENDED confirmatory set (2026-07-16):** `openai/gpt-4o` (strong tier) +
`openai/gpt-4.1-mini` (small tier), GitHub Models, day-batched. Capability-tier diversity;
cross-vendor deferred to Azure.

**Original a-priori set (2026-07-15T09:23:55Z, superseded by the amendment above):**
Three families spanning ≥2 vendors + capability tiers (SPEC §4.2: separate preference-driven
vs capability-noise disagreement; trust only cross-family-consistent flags):
- `openai/gpt-4o` (strong, OpenAI), `meta/Llama-3.3-70B-Instruct` (strong, Meta open-weight),
  `microsoft/Phi-4` (small, Microsoft).
- **If Azure Foundry is used**, the equivalent deployments of these (or the nearest available)
  are used; substitutions logged with reason.
- **Exclusion rule (PIPELINE-only, decided before viewing axis-1 effect):** a model may be
  excluded ONLY for a documented pipeline failure — e.g. > 10% unparseable System-2 outputs,
  or a degenerate near-constant System-1 (no between-item variation) — NEVER for its axis-1
  result. Any exclusion logged with the pre-effect diagnostic that triggered it.

## 3. Conditions (≥5, a-priori = the human-data conditions, not pilot-selected)
Bansal's five AI conditions: `Conf.`, `Conf.+Single`, `Conf.+Double`, `Conf.+Adaptive`,
`Conf.+Adaptive (Expert)` (exact strings). Rendered faithfully from the task stimuli; the
condition→content mapping is documented in code + research doc and is fixed before the
confirmatory run.

## 4. Dependent variable & signals
- **Primary DV:** conflict-conditioned reliance (reliance on trials where System-1 ≠ AI advice);
  unconditional reliance reported for transparency.
- **Axis-1 target:** between-user reliance **over-dispersion** via beta-binomial
  (`betabinom_overdispersion_within_domain`), separated from binomial sampling noise.
- **Panel disagreement:** variance of per-(persona × model) conflict-conditioned reliance,
  per condition, over the full panel.
- **Primary estimator:** difficulty-controlled **within-task counterfactual difference**
  (within-pair; difficulty cancels). **Secondary:** cross-condition Spearman (n = 5 conditions).

## 5. Baselines that must be beaten (no watering down)
random; **mean-predictor** (outputs only p(1−p), ρ = 0 by construction); prompt-only;
single-model; plus a rational-Bayesian null as the "appropriate-reliance" anchor.

## 6. Statistics
Beta-binomial over-dispersion (separates noise); **bootstrap over (personas × seeds × models)**
for CIs; permutation tests for the disagreement→over-dispersion relationship; difficulty as a
controlled covariate (within-task differencing is primary); **Benjamini–Hochberg** correction,
**α = 0.05** (ratified here). Report effect sizes + CIs; per-model results + cross-family
agreement; contamination/training-cutoff caveats per model.

## 7. Thresholds τ (procedure pre-specified; VALUES stay UNFROZEN)
τ_disp / τ_level are learned ONCE in the atomic-feature space (Module D) and **frozen with a
UTC timestamp BEFORE any threshold results** — this axis-1 confirmatory run tests H1a and does
NOT set τ. Post-hoc τ tuning = misconduct. (Freeze log lives in PROGRESS §Preregistration.)

## 8. Power target N — TO BE COMPLETED FROM THE PILOT (the ONLY pilot→confirmatory feedback)
The exploratory pilot (PR #8) provides effect-size + variance-component estimates ONLY, used to
set the confirmatory **personas × items × models × conditions × seeds** so the axis-1 test has
adequate power (target ≈ 80%). No other pilot quantity feeds the confirmatory design.
> N (personas / items / seeds per model; models; conditions): **[PENDING — fill after pilot,
> then record the FINAL freeze timestamp in PROGRESS §Preregistration before the confirmatory run].**

## 9. Reporting commitment
The confirmatory result is reported **regardless of outcome** (including a null or a
directionally-wrong result), with the exploratory pilot kept clearly separate and its data
excluded from the confirmatory estimates.
