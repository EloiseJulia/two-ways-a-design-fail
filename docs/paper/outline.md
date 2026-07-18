# Paper skeleton — "Two Ways a Design Fails" (working title)

> **Status:** living skeleton (updated 2026-07-18). Encodes the PIVOTED positioning (DECISIONS **D5.22**,
> PI-approved A+B) driven by the cross-vendor evidence (D5.20/D5.21, audit PASS). The "validated
> cross-vendor detector" framing is RETIRED. New main line: **panel deployment-screening signals are
> model-capability-dependent**; persona-level susceptibility is the robust positive result. Results
> marked ⟨PENDING⟩ fill in from the frozen GH-Models confirmatory axis-1 (D5.11, awaiting gpt-4o reset).
> Venue targets: HCOMP / FAccT / CHI (Methods). Report REGARDLESS of outcome; do NOT re-inflate a
> retired claim.

## Title candidates (align with the evidence: capability-dependence + persona-robust susceptibility)
- "When Does a Synthetic Panel See the Danger? Model-Capability-Dependence of Pre-Deployment Screening for Human–AI Decision Interfaces"
- "Frontier Models Resist the Trap Their Users Fall Into: Capability-Dependent Reliance Signals in LLM Panels"
- "Who the Panel Still Warns About: Persona-Robust Dark-Pattern Susceptibility Across Model Vendors"
- (avoid "validated detector" / "predicts humans" — the cross-vendor data do not support generalization)

## Abstract (sketch — PIVOTED, D5.22)
Deploying an AI-advice interface can fail in (at least) two ways: it can make reliance **heterogeneous
and user-sensitive** (an over-dispersion failure), or make users **uniformly over-rely on a confidently
wrong AI** (a dark-pattern failure). A tempting shortcut is to screen interfaces *before* a costly human
study with a **calibrated multi-agent LLM panel** as a synthetic cohort. We build that panel — two-axis
(over-dispersion; wrong-AI over-reliance), conflict-conditioned, preregistered — and ask whether its
danger signals are **robust across the LLMs that power it**. They are **not**: the signals are strongly
**model-capability-dependent**. A smaller model (gpt-4.1-mini) reproduces documented human failure modes
(wrong-AI over-reliance ≈0.69, p<0.01; real reliance heterogeneity), whereas **frontier models resist
the trap and homogenize** — gpt-5.5 adopts the guaranteed-wrong AI only 30% of the time (significantly
*below* chance), with near-zero cross-persona disagreement; claude-sonnet-4.5 and gemini-2.5-pro sit at
chance (0/3 vendors replicate). **Consequently, the choice of panel model is a first-order, under-
appreciated design decision, and a single-frontier-model panel can silently MASK deployment risks that a
weaker-model panel surfaces.** Yet one signal is **robust across all vendors**: dark-pattern
susceptibility **concentrates in a trusting-novice persona** (adoption 0.60–1.00) even when the model
mean collapses — so the panel reliably localizes *which user profiles* a coercive interface endangers,
even where aggregate rates do not transfer. We contribute (i) this capability-dependence finding as new,
head-on evidence for the silicon-sampling reliability debate, (ii) the persona-conditioned susceptibility
result, (iii) the two-axis over-dispersion-as-safety-DV protocol, and (iv) a rigorous, preregistered,
audit-gated pipeline (three self-caught silent-corruption bugs). We do not claim to predict individual
humans; we characterize when a synthetic panel does — and does not — see the danger, and preregister the
human study that grounds it.

## 1. Introduction
- Hook: mean accuracy hides *who* is endangered and *when* an interface weaponizes a wrong AI.
- Two failure modes → "two ways a design fails" (axis-1 over-dispersion; axis-2 wrong-AI over-reliance).
- The cost problem: human studies are expensive; we want a cheap **pre-deployment screen** (smoke
  alarm, high recall) — not a replacement for human studies.
- Thesis (D5.4): a calibrated synthetic panel can **triage** interfaces on these two axes; variance is
  the safety DV; preregistered + honest.
- Contributions (see §7).

## 2. Related work (from docs/research/2026-07-16-novelty-positioning.md — 22 cites)
- LLM/agent SIMULATED USERS for HCI eval + the "unreliable proxies" critiques (Park, Argyle, Santurkar,
  Aher, Seshadri ICLR'26, CoMPosT, Hämäläinen) → our answer: TRIAGE not prediction; calibration;
  conflict-conditioned DV; cross-model.
- Reliance / over-reliance from confidence & explanations (Bansal 2021; Buçinca 2021; Vasconcelos 2023;
  Zhang 2020; Lai&Tan 2019; Schemmer 2023; Gajos 2022) → we reframe heterogeneity (a known nuisance) as
  the safety DV.
- Dark patterns / coercive AI (Luguri&Strahilevitz; Mildner 2023) → we give a computational detection
  signal.
- Pre-deployment / offline evaluation of human–AI teams (Rastogi 2022/23 = routing, not UI-safety
  triage) → the GAP we fill.

## 3. The two-axis triage: definitions
- Axis-1: between-user reliance **over-dispersion** (beta-binomial excess over binomial p(1−p)),
  conflict-conditioned (System-1 ≠ AI). Interface-level DV.
- Axis-2: systematic adoption of a **wrong** AI under (dark) framing — "uniformly lethal" even at zero
  dispersion.
- The triage protocol (SPEC §6): learn τ_disp, τ_level ONCE in an atomic UI **feature space**; either
  axis over threshold ⇒ recommend human study; both low ⇒ release; OOD/uncertain ⇒ ABSTAIN
  (high-recall screen; SPEC §6.2).

## 4. Method: the calibrated synthetic panel
- Panel = personas × models; dual-system (System-1 no-AI anchor FROZEN; System-2 with AI+UI).
- Conflict-conditioned reliance DV (resolves the naive-panel compliance-collapse; PR#3→#4).
- Faithful Bansal condition rendering (D5.1: Single/Double/Adaptive = top-1/top-2/median-conf-adaptive
  label explanations; the fidelity fix that a sign/scoring bug taught us to take seriously).
- Atomic UI feature space (§4.3) + Module-D calibration/triage + E5 ECE/abstention (all built,
  audit-gated).
- **Rigor spine (a selling point):** preregistration frozen before results; analysis coded BLIND;
  audit-gated merges; a real axis-2 **sign-inversion bug caught by the two-layer gate** (D5.10) — we
  report our own error and its fix as evidence of process integrity.

## 5. Experiments & results
- E1 axis-1 over-dispersion on real Bansal humans: REAL (ρ=0.067, excludes 0); variance decomposition
  (no-AI trait 0.74 → AI user×task 0.32–0.41 on Bansal; C0 = Bansal-specific, does not generalize to
  Lu&Yin 0.80 — reported honestly).
- **Cross-vendor capability-dependence (D5.18/D5.20/D5.21 — the CENTERPIECE; audit PASS):** same
  preregistered protocol run on gpt-5.5 (OpenAI) + claude-sonnet-4.5 (Anthropic) + gemini-2.5-pro
  (Google), matched items, per-model (no pooling).
  - **Axis-2 does NOT replicate on frontier:** over-reliance on the guaranteed-wrong AI = gpt-5.5
    **0.300** (binomial vs 0.5 p=1.0 — significantly *below* chance, active resistance), claude
    **0.492** (p=0.61), gemini **0.525** (p=0.32); **0/3 significant** vs gpt-4.1-mini **0.690**
    (p=0.0098). 
  - **Axis-1 correspondence null/weak across all vendors:** panel↔human per-condition over-dispersion
    Spearman = −0.20 / −0.31 / +0.10 (n=5, none significant; swings to +0.63 dropping one condition =
    A4 fragility, not signal).
  - **Frontier-ceiling mechanism (preregistered risk, confirmed):** gpt-5.5 mean panel disagreement
    0.012 (vs claude 0.045, gemini 0.074) = near-homogeneous; conflict trials ARE present (n_conflict
    59–73/120) — the model *resists*, it is not a no-conflict artifact.
  - **ROBUST positive result (B):** dark-pattern susceptibility concentrates in the trusting-novice
    persona (p5) across ALL vendors — adoption gpt-5.5 0.60 / claude 0.95 / gemini 1.00 — even where the
    model mean collapses.
- Confirmatory axis-1 on the ORIGINAL provider (H1a, N=20, preregistered D5.11, GitHub Models
  gpt-4o+gpt-4.1-mini): ⟨PENDING — awaiting gpt-4o daily-reset; report per-model, regardless⟩.
- E3 LOIO generalization, E5 ECE/reliable-radius/abstention: ⟨report the offline/methodological results⟩.

## 6. Limitations & threats to validity (LOAD-BEARING — write honestly)
- **Synthetic personas ≠ real users** (the central threat). The cross-vendor result makes this concrete:
  the panel's danger signal depends on the model, so "the panel" is not one thing. E6 (future) is the
  direct human validation that grounds WHICH model, if any, tracks humans.
- **The screen is NOT model-agnostic:** our own evidence shows axis-2/axis-1 signals do not transfer
  across capability tiers. We therefore do NOT claim a validated, deployable, model-agnostic detector.
- **Small n / no power for axis-1 correspondence** (n=5 conditions; task-selection fragility) — disclosed;
  motivates the difficulty-stratified correspondence (D5.14) and E6.
- **Single domain (beer)**; axis-2 constructs a guaranteed-wrong AI (1−gt) = susceptibility to a coercive
  wrong AI, not naturalistic model error. amzbook 2nd-domain arm is queued.
- **Item selection uses human reliance variance** (A11, disclosed): correspondence-circularity risk;
  mitigation = held-out item correspondence + E6.
- **No human study yet** (E6 is the planned capstone; now sharply motivated by the capability-dependence).

## 7. Contributions (ranked; honest — PIVOTED per D5.22)
1. **Model-capability-dependence of LLM-panel screening signals** (primary empirical + cautionary
   methods): the same preregistered panel yields strong human-like failure signals on a smaller model
   but has them RESISTED/HOMOGENIZED by frontier models — new, direct evidence for the silicon-sampling
   reliability debate (Seshadri ICLR'26, Santurkar), and a concrete warning that panel-model choice is a
   first-order design decision that can mask deployment risks.
2. **Persona-conditioned dark-pattern susceptibility that IS robust across vendors** (positive result):
   even when the model mean collapses, the panel localizes the trusting-novice profile as highly
   susceptible — a detector-flavored contribution scoped to WHO, not aggregate rate.
3. **The two-axis protocol** (over-dispersion as a safety-relevant DV + wrong-AI over-reliance,
   conflict-conditioned, with calibrated thresholds + abstention) as the method.
4. **A rigorous, reproducible pipeline** — preregistration frozen before results, blind analysis,
   audit-gated merges, and THREE self-caught silent-corruption bugs (axis-2 sign-inversion D5.10,
   betabinom boundary D5.16, parser fabrication D5.19) reported as evidence of process integrity.
5. A **preregistered human-validation design (E6)**, now sharpened: which model's panel (if any) tracks
   real human reliance heterogeneity.

## 8. Ethics
- Dark-pattern deception (guaranteed-wrong coercive AI) → debrief; IRB for E6; no deployment of dark
  designs; the method's PURPOSE is to PREVENT shipping such designs.

## 9. Two nearly-free acceptance-movers (from docs/paper/reviewer-rebuttals.md)
- **Cost/ROI argument (answers A7):** the screen's value is asymmetric-cost triage. A panel run is
  ~$15–45 / hours; a human study is ~$5k–50k / weeks. A false alarm just means "run the human study you
  would have run anyway"; a MISS means shipping a design that endangers a subgroup or weaponizes a wrong
  AI. Optimizing for RECALL (SPEC §6.2) is therefore the right operating point, and even a modest-
  precision screen that reduces the *denominator* of required human studies pays for itself. Frame the
  method as a filter that makes human studies cheaper to target, not a replacement.
- **Process-rigor as a credibility asset (answers A10):** preregistration frozen before results (D5.11,
  D5.13), analysis coded BLIND, audit-gated merges, and — notably — we CAUGHT AND FIXED our own axis-2
  sign-inversion bug (D5.10) via a two-layer independent-audit + numeric-re-derivation gate, and we
  report it. In a field worried about irreproducible human-AI results, demonstrable process integrity is
  itself a contribution; methods venues reward it.

## Open decisions for the PI (paper-level)
- Venue + framing depth (methods-led vs empirical-led) — revisit once confirmatory + powered axis-2 land.
- Whether to include C0 (Bansal-specific) as a supporting section or cut to tighten the story.
- E6 go/no-go + timing (the capstone).
