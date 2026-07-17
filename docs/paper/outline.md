# Paper skeleton — "Two Ways a Design Fails" (working title)

> **Status:** living skeleton (2026-07-17). Encodes the LOCKED positioning (DECISIONS D5.4) and the
> honest evidentiary state. Results marked ⟨PENDING⟩ fill in from the confirmatory axis-1 (D5.11) and
> powered axis-2 (D5.13) runs. Venue targets: CHI (Methods) / FAccT / CSCW. Do NOT overclaim the
> empirical magnitude — the signal is the TARGET the method detects (D5.4).

## Title candidates (align with the evidence: validated axis-2 + preliminary axis-1 + method)
- "Two Ways a Design Fails: Pre-Deployment Triage of Human–AI Decision Interfaces with a Synthetic Agent Panel"
- "Over-Dispersion as a Safety Signal: Triaging AI-Advice Interfaces Before the Human Study"
- (avoid claiming "predicting humans" in the title until E6; frame as "triage"/"screening")

## Abstract (sketch)
Deploying an AI-advice interface can fail in (at least) two ways: it can make reliance **heterogeneous
and user-sensitive** (safe for some users, dangerous for others — an over-dispersion failure), or it
can make users **uniformly over-rely on a confidently wrong AI** (a dark-pattern failure). Both are
invisible to mean-accuracy evaluation. We propose a **pre-deployment triage** that runs a calibrated
**multi-agent LLM panel** as a synthetic cohort and screens an interface on two axes — reliance
**over-dispersion** (axis-1) and **wrong-AI over-reliance** (axis-2) — flagging designs that warrant a
(costly) human study before release. We treat cross-user **variance** as the safety-relevant dependent
variable (not the mean effect), validate the panel against two real human decision datasets (Bansal,
Lu&Yin), and preregister our confirmatory tests. ⟨Findings: axis-2 = strong, significant over-reliance
on a coercive wrong AI (clean 0.69, p<0.01); axis-1 = ⟨PENDING confirmatory⟩; panel↔human
correspondence = ⟨PENDING⟩.⟩ The empirical signal is the target the method detects; small effects
motivate a calibrated-threshold abstention rule rather than undermining the screen. We do not claim to
predict individual humans — we triage designs that need human study.

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
- Confirmatory axis-1 (H1a, N=20, preregistered D5.11): ⟨PENDING — report per-model, regardless⟩.
- Panel↔human cross-condition correspondence (secondary): ⟨PENDING; power-N suggested weak⟩.
- Axis-2 (E4 → powered D5.13): E4 = strong significant over-reliance on a coercive wrong AI (clean 0.69,
  binomial p=0.0098, p5=100%, near-uniform); powered clean 1−gt multi-model = ⟨PENDING⟩.
- E3 LOIO generalization, E5 ECE/reliable-radius/abstention: ⟨report the offline/methodological results⟩.

## 6. Limitations & threats to validity (LOAD-BEARING — write honestly)
- **Synthetic personas ≠ real users** (the central threat). Mitigations: calibration; conflict-
  conditioned DV; cross-model; and — critically — E6 (future) is the direct human validation. Until
  E6, claims are TRIAGE/screening, not human prediction.
- **Panel↔human predictive validity is not yet established** (axis-1 correspondence looks weak in the
  power-N). We state this plainly; the confirmatory settles it; a null is reported as a bound.
- **Single domain (beer) for the panel**; single-vendor (OpenAI family, capability-tier not cross-
  vendor); axis-2 domain/model coverage limited.
- **Axis-2 manipulation:** the dark condition constructs a guaranteed-wrong AI (1−gt) — measures
  susceptibility to a coercive wrong AI, not naturalistic model error.
- **Small effect sizes / task-selection sensitivity** for axis-1 over-dispersion (disclosed; motivates
  the calibrated threshold + abstention).
- **No human study yet** (E6 is the planned capstone).

## 7. Contributions (ranked; honest)
1. **Framing/method:** over-dispersion as a safety-relevant DV + a two-axis pre-deployment triage
   protocol with calibrated thresholds + abstention. (Novel; no direct prior art.)
2. **A significant axis-2 dark-pattern susceptibility result** in a calibrated panel (E4/D5.13).
3. **A rigorous, reproducible pipeline** (preregistration, blind analysis, audit-gated, a caught-and-
   fixed bug) — a methods contribution in itself.
4. ⟨If it lands: axis-1 confirmatory + panel↔human correspondence.⟩
5. A **preregistered human-validation design (E6)** as the path to full validation.

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
