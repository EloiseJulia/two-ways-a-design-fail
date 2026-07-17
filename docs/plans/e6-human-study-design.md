# E6 — Human-Subjects Validation Study (DESIGN, to be run LAST)

> **Status:** DESIGN ONLY (2026-07-17). Per PI directive, the synthetic-panel + method work is
> maximized first; this ~60-subject human study is the FINAL capstone that converts the paper from
> "rigorous but unvalidated" into a validated pre-deployment method. **This document is a design; it
> is NOT preregistered yet — freeze §§Hypotheses/Design/Analysis with a UTC timestamp in
> `docs/DECISIONS.md` BEFORE any data collection.**

## 0. Why E6 exists (the one thing synthetic compute cannot buy)
The paper's load-bearing claim is that an **LLM agent-panel can triage human–AI decision interfaces
before a human study** — i.e. the panel's per-interface risk flags predict what REAL humans do on the
SAME interfaces. Every result so far is either (a) real human data used to *calibrate/anchor* (Bansal
over-dispersion; C0), or (b) *panel* behavior (axis-2 over-reliance; the confirmatory axis-1). None
yet shows the panel PREDICTS held-out human behavior on interfaces it flagged. E6 closes exactly that
gap. It is the direct rebuttal to the "LLM-simulated users are unreliable proxies" attack (Seshadri
ICLR'26; Santurkar; CoMPosT): we do not claim to predict individuals — we test whether the panel's
**interface-level triage ranking** matches humans'.

## 1. Research questions / hypotheses (validation-oriented; freeze before data)
Let the panel produce, per interface `i`: a predicted axis-1 over-dispersion `D̂1(i)`, a predicted
axis-2 over-reliance `D̂2(i)`, and a triage decision `T(i) ∈ {RELEASE, HUMAN_STUDY, ABSTAIN}`.
Humans on the same interfaces yield observed `D1(i)` (between-user reliance over-dispersion),
`D2(i)` (adoption of a wrong AI), etc.
- **H-E6-1 (axis-1 predictive validity):** across the E6 interfaces, panel `D̂1` rank-correlates with
  human `D1` (Spearman ρ > 0, preregistered one-sided), and interfaces the panel flags high-axis-1
  show significantly higher human over-dispersion than low-axis-1 interfaces.
- **H-E6-2 (axis-2 predictive validity):** the interface the panel flags as high axis-2 (a coercive
  wrong-AI / dark design) produces significantly higher human adoption of the wrong AI than the
  faithful/control interface (within-subject contrast).
- **H-E6-3 (triage operating point):** treating "either axis over τ ⇒ recommend human study" as a
  binary screen, the panel achieves high **recall** on interfaces humans reveal as risky (a miss =
  releasing a dangerous design; recall is prioritized over precision, per SPEC §6.2). Report
  precision-at-recall + the confusion matrix over the E6 interface set.
- **H-E6-4 (abstention / applicability radius):** on a NOVEL interface outside the panel's calibration
  feature-space (OOD), the panel ABSTAINS (per Module D / E5), and we report whether human risk on
  that interface was indeed unpredicted — validating abstention as the safe default.
- **Reporting commitment:** report REGARDLESS of outcome. A null (panel does NOT predict humans) is a
  publishable, important bound on synthetic-panel validity and reframes the contribution honestly.

## 2. Design
- **Type:** within-subjects (each participant sees multiple interfaces), counterbalanced order,
  attention/quality checks. Within-subjects maximizes power at N≈60 and controls person effects
  (directly relevant to the axis-1 over-dispersion DV, which is between-user — see §4 for the
  estimator).
- **Task:** a binary decision task mirroring the calibration domain (Bansal-style sentiment, e.g.
  beer/AmzBook review polarity) so the panel's calibration transfers. Items drawn from held-out Bansal
  stimuli NOT used to fit the panel (leakage firewall at the item level).
- **Interfaces (conditions), chosen for MAXIMUM panel-predicted separation** to power N≈60:
  1. `Control` (Conf.: prediction + confidence, no explanation).
  2. `Low-axis-1` interface (panel predicts LOW reliance over-dispersion).
  3. `High-axis-1` interface (panel predicts HIGH over-dispersion — user-sensitive design).
  4. `Faithful explanation` (Conf.+Adaptive (Expert)).
  5. `Dark / wrong-AI` (the coercive guaranteed-wrong design; panel predicts HIGH axis-2).
  6. `Novel/OOD` interface (a modern design NOT in the panel's calibration set; panel is expected to
     ABSTAIN) — tests H-E6-4.
  (Exact interface set is finalized from the panel's confirmatory + axis-2 outputs — the ones with the
  largest predicted axis-1 / axis-2 separation — and FROZEN before recruitment.)
- **Trials:** ~15–20 items per interface (matched difficulty distribution), randomized; AI advice per
  item follows the same construction as the panel (Bansal pred/conf; dark = guaranteed-wrong 1−gt).

## 3. Participants, power, recruitment
- **N ≈ 60** (target; run an a-priori power analysis from the panel's predicted effect sizes +
  Bansal's observed human over-dispersion ρ≈0.067 and the axis-2 adoption gap; if the within-subject
  axis-2 contrast is the primary power driver, N≈60 is well-powered for the large adoption gaps the
  panel predicts; the axis-1 over-dispersion contrast is the harder target — pre-compute achievable
  power and, if needed, note N as a floor with a possible extension to ~80).
- **Recruitment:** Prolific (preferred for quality) or MTurk with Bansal-style qualification;
  attention checks + the Bansal-4.4 exclusion (median RT < 2s or all-same-label). Fair compensation
  (≥ local minimum wage equivalent). **IRB/ethics approval required before data collection.**
- **Measures:** per-trial initial (no-AI) decision if elicited (for a human System-1 anchor), final
  decision, AI advice shown, confidence, RT; post-task: AI-literacy, trust, demographics; the dark
  condition includes a debrief (deception via a deliberately-wrong coercive AI).

## 4. Analysis (freeze before data)
- **Human axis-1 DV:** between-user reliance **over-dispersion** per interface via the SAME
  beta-binomial estimator as the panel (`twdf.metrics.overdispersion`), on conflict-conditioned
  reliance (human System-1 ≠ AI); within-subjects lets each participant contribute across interfaces.
- **Human axis-2 DV:** adoption of the wrong AI on the dark interface (conflict-conditioned), vs the
  placebo/faithful floor — mirrors `over_reliance_on_wrong`.
- **Panel↔human validation:** Spearman of `D̂1` vs `D1` and `D̂2` vs `D2` across interfaces
  (reuse `twdf.analysis.panel_human_condition_correspondence`, generalized to the E6 interface set);
  triage precision/recall (H-E6-3); ECE / reliable-radius of the panel's predictions (reuse
  `twdf.analysis.reliability`); abstention correctness on the OOD interface (H-E6-4).
- **Stats:** mixed-effects where identified (participant random effect) OR the split-half / bootstrap
  estimators already validated offline; permutation tests; BH across the hypothesis family; effect
  sizes + CIs; report per-interface. **τ_disp/τ_level are FROZEN in the Module-D feature space BEFORE
  E6** (a separate timestamped step) — E6 tests the frozen triage, it does not tune τ.
- **Leakage firewalls:** E6 items are held out from panel calibration; τ frozen before E6; the panel's
  predictions `D̂` are generated + logged BEFORE any human data is seen (pre-registered predictions).

## 5. What each outcome means (all honest, all publishable)
- **Panel predicts humans (H-E6-1/2 hold):** the method is a validated pre-deployment screener — the
  strong top-venue result.
- **Partial (axis-2 predicts, axis-1 does not):** honest split — the panel validly flags dark-pattern
  over-reliance but not user-sensitivity heterogeneity; scope the claim accordingly.
- **Null:** an important, honest bound on synthetic-panel predictive validity + a cautionary
  contribution (when/why LLM panels fail as proxies), consistent with the locked D5.4 framing.

## 6. Dependencies / to-do before running E6
1. Confirmatory axis-1 (D5.11) + powered axis-2 (D5.13) complete → pick the max-separation interfaces.
2. Module-D τ_disp/τ_level FROZEN in the feature space (separate timestamped step; needs the axis-1 +
   axis-2 calibration data) → the triage decisions E6 tests are then fixed.
3. Generate + LOG the panel's per-interface predictions `D̂1, D̂2, T` BEFORE recruitment.
4. Freeze the E6 preregistration (§§1–4) with a UTC timestamp in `docs/DECISIONS.md`; IRB approval.
5. Build the E6 web task + logging (out of current scope; a separate engineering slice).
