# SPEC.md — Frozen Design (technical version of v2.4)

> Single source of scientific truth. Everything traces back to
> `开题沟通稿_分歧度分诊_部署前评估_v2.4.md`. Do NOT diverge from it silently;
> propose changes to the PI before editing this file.

## 0. One-line claim (single, falsifiable)
A multi-agent panel calibrated on real reliance logs produces a **two-axis
triage signal**:
- **Axis 1 · Disagreement (user-sensitive):** panel disagreement flags
  high-**over-dispersion** designs ("safety depends on who the user is").
- **Axis 2 · Systematic over-reliance level (uniformly lethal / dark pattern):**
  panel convergent high adoption of **wrong** AI advice flags "uniformly harmful
  to everyone", **even when over-dispersion ≈ 0**.

**Either axis over threshold ⇒ must go to human study; release on synthetic
evidence only when BOTH axes are low.** Low disagreement ≠ safe: convergence at
low reliance = truly robust; convergence at high (wrong-AI) reliance = uniformly
lethal dark design.

## 1. Scope
IN: cognitive-semantic interaction interventions (explanation format, confidence
presentation, responsibility framing, cognitive forcing).
OUT (→ abstain / send to human study): pure perceptual-motor visual mechanisms
(font size, color, button size, Fitts-law effects, pure visual fatigue).

## 2. Contributions

> **POSITIONING LOCKED 2026-07-16T06:15:38Z (PI; see DECISIONS D5.4), BEFORE the confirmatory
> axis-1 run so the result cannot bias the framing.** The HEADLINE is a **methodological reframe,
> not an effect-size claim**: (i) treat cross-user **variance / over-dispersion** in reliance as the
> *safety-relevant* DV (vs the prior literature's mean over-reliance effect); (ii) a **two-axis
> pre-deployment triage protocol** that SCREENS human–AI decision interfaces before an expensive
> human study, **validated by panel↔human correspondence on two real datasets + preregistration.**
> The empirical signal (e.g. ρ≈0.067) is the **TARGET the method detects, NOT a boast** — a small ρ
> motivates the calibrated threshold/abstention rule. Head-on defense vs "LLM-simulated users are
> unreliable proxies" (Seshadri ICLR'26; Santurkar; CoMPosT): we **triage designs that need a human
> study; we do NOT claim to predict individual humans.**

- **C1 (PRIMARY / core, elevated 2026-07-15 PR #6):** propose + validate the two-axis
  triage signal (panel-disagreement over-dispersion axis + systematic wrong-AI
  over-reliance axis). This is the paper's load-bearing contribution. Preliminary
  real-panel evidence: PR #4 shows the redesigned panel produces genuine heterogeneity
  (conflict rate 43%, personas diverge) and a first axis-2 wrong-AI signal (0.325).
  Axis-2 dark-pattern **backfire** stays a tentative SUPPORTING lead — promoted only if E4 on the
  faithful renderer (D5.1/D5.2) reaches significance.
- C2 (support): "counterfactual reliance elasticity" — difficulty-controlled
  sensitivity estimate via frozen-persona paired UI swap.
- **C0 (DEMOTED to a Bansal-specific SUPPORTING finding, 2026-07-15 PR #6 —
  was briefly elevated to co-anchor, now demoted on honest grounds):** On **Bansal**,
  AI assistance is associated with reliance shifting from a stable user trait (no-AI
  split-half stable-user share ≈ 0.74) toward user×task (AI-assisted ≈ 0.32–0.41). This
  motivates task-spanning screening. **It is NOT shown to generalize:** on Lu&Yin,
  AI-assisted reliance is trait-stable (≈ 0.80) (PR #5). The zero-quota discriminator
  (PR #6) was **INCONCLUSIVE** — 2 of 3 Bansal domain subsets are ceiling/low-variance
  artifacts (between-user SD ≈ 0.05 → share ≈ 0, uninterpretable); the one interpretable
  Lu&Yin-matched subset (lsat) rose only partway (0.46 [0.31, 0.59], CI overlapping the
  0.33 baseline). So the Bansal↔Lu&Yin gap is CONFOUNDED and UNRESOLVED. C0 is therefore
  presented as a Bansal-specific observation with an explicit **OPEN QUESTION** (below),
  not a general law.
- **OPEN QUESTION (future mechanism study, not a claim):** is reliance stability
  **regime-dependent** — specifically, does **sequential feedback** (Lu&Yin) drive users
  toward a stable trust policy, vs static settings (Bansal) yielding user×task? Testable
  via the §4.1 sequential-stateful (Bayesian-trust) mode. Deferred as optional upside
  AFTER C1 is solid.
- (RTI = follow-up second paper, out of scope here.)

> **Empirical status of the panel (C1/C2), honest — updated 2026-07-15, PR #4:**
> PR #3 (naive gpt-4o-mini panel) produced a NULL: near-uniform agreement (97%
> no-movement; "reliance" ≈ agreement, not adoption; disagreement ≈ 0). PR #4's
> REDESIGN (conflict-conditioned reliance DV on System-1≠AI trials + data-driven
> hard/ambiguous item selection + stronger persona conditioning + a WRONG-AI dark
> condition; model gpt-4.1-mini) RESOLVES the collapse: conflict rate 3% → **43%**,
> personas now DIVERGE on the conflict-conditioned DV (0.11–0.56), the explanation
> shows a positive within-task elasticity **+0.19 (p=0.17, n=11 — UNDERPOWERED, not
> yet significant)**, and axis-2 gives a first real signal — **over-reliance on WRONG
> AI = 0.325**, with one persona actively resisting the coercive dark framing (a
> dark-pattern-BACKFIRE lead, audit-confirmed genuine). So the mechanism CAN produce
> heterogeneity + an axis-2 reading; it is not yet powered/multi-model/calibrated.
> CAVEATS: single model (gpt-4.1-mini; not same-model comparable to PR #3), 20 items /
> 6 personas / beer only, elasticity underpowered. C1 is now the PRIMARY contribution;
> C0 demoted to a Bansal-specific supporting finding (PR #6; generalization unresolved).
> Next: power up + betabinom over-dispersion on conflict DV + axis-2/E4 build-out + cross-model.

## 3. RQ / Hypotheses (pass criteria)
- **RQ1 (core, two-axis).**
  - H1a (axis 1, over-dispersion, E1): difficulty-controlled within-task
    counterfactual difference — disagreement increment predicts human reliance
    **over-dispersion** (excess over p(1−p) floor), significantly better than
    random / **mean-predictor** / prompt-only / single-model; CI excludes 0.
    - **Refinement (empirical, PR #2 decomposition on Bansal):** the between-user
      reliance over-dispersion axis-1 targets is, under AI assistance,
      predominantly a **user × task** interaction rather than a stable user trait.
      Split-half reliability: no-AI baseline reliance is substantially a stable
      user trait (stable-user share ≈ 0.74, 95% CI [0.69, 0.79]), but AI-assisted
      conditions drop to ≈ 0.32–0.41 (task-dependent). So axis-1's "safety depends
      on *who the user is*" is, in the AI-assisted regime, more precisely "depends
      on **user × task**": whether a user over-relies is contingent on the specific
      task. Consequence: the agent panel and the disagreement→over-dispersion
      mapping must span **diverse tasks** to expose the signal (few-task samples
      attenuate it). Single dataset; replication + GLMM corroboration pending.
      See docs/research/2026-07-14-overdispersion-decomposition.md.
  - H1b (axis 2, level/dark, E1+E4): systematic over-reliance on wrong AI gives
    a high-risk reading **even where over-dispersion ≈ 0**; converges with E4
    compliance sensor.
- **RQ2 (support).** H2: leave-one-intervention-out (LOIO, whole unseen *class*)
  directional hit-rate > random; intervention-ranking Spearman ρ significantly
  positive.
- **RQ3 (boundary).** H3: placebo explanation induces reliance > 0 but
  significantly < faithful explanation; ECE boundary map + feature-distance +
  effect-reversal region define the applicability radius → abstention rule.

## 4. Method (summary)
- Dual-system flow: System-1 (no AI anchor) → inject UI intervention → System-2
  reflection → final decision + trace.
- Counterfactual pairing: same System-1 internal state exposed to control vs
  treatment UI, else bit-identical → reliance diff = internal causal effect of UI
  (difficulty cancels within pair).
- Two run modes: (i) static counterfactual pairing (single item, difficulty
  controlled) → axis-1 over-dispersion + C2 elasticity; (ii) sequential stateful
  (Bayesian trust state variable, fed the same AI right/wrong sequence as target
  humans; calibrate update dynamics on Lu & Yin dynamic trust curves).
- Friction proxy layer: cognitive-load component only (token truncation,
  max_tokens cap, forced delay cost); NOT retinal fatigue; calibrated + ablated.
- Diverse panel: personas (domain skill, AI literacy, risk sensitivity, caution)
  × temperature variance × prior mixing; multi-capability tier + multi-family
  models. Distinguish preference-driven vs capability-noise disagreement.
- Statistical calibration: minimize KL(agent ‖ human reliance); report PAS, ECS.
- Atomic feature representation (§4.3): decompose each UI into a
  cognitive-interaction feature vector (info density, salience, authority cue,
  interruption frequency, explanation faithfulness, latency, ...). Calibrate +
  compute OOD distance in **feature space**, not whole-UI surface. Partitioned /
  non-linear calibration; human↔agent effect-reversal region → high ECE → abstain.

## 5. Experiments (E1–E6)
| Exp | RQ | Operation | Pass |
|---|---|---|---|
| **E1★ two-axis** | RQ1 | axis1: per-user reliance over-dispersion (beta-binomial) + difficulty-controlled within-task counterfactual diff; axis2: panel over-reliance level on wrong AI; both vs 4 baselines. **Task selection:** Uses ALL shared tasks across conditions (task_selection='all') to maximize statistical power. Robustness analysis (results/e1_multicond_robustness.json) shows signal is FRAGILE to task selection (Human rho: 0.0000–0.0666 depending on scheme). This is a KNOWN LIMITATION. | axis1 significant vs mean-predictor after difficulty control, CI∌0; axis2 flags dark low-dispersion design as high risk, converges with E4. **Caveat:** Over-dispersion magnitude is task-selection-sensitive on small Bansal dataset. |
| **E2☆ elasticity** | RQ2 | frozen persona, paired control/treatment swap, dReliance/dIntervention | paired effect direction matches human empirics; permutation-test significant |
| **E3★◆ LOIO** | RQ2 | train on one class, zero-shot predict another class direction + ranking | direction hit > random; Spearman ρ > 0 significant |
| **E4☆ compliance (axis-2 dark sensor)** | RQ1/3 | placebo explanation + pseudo-high-confidence + oppressive responsibility framing → compliance floor; feeds axis-2 | placebo reliance ∈ (0, faithful); dark condition convergent high reliance judged high-risk |
| **E5☆ ECE / radius / abstain** | RQ3 | ECE + generalization gradient by persona/difficulty/feature-distance/reversal | failure-region map, reliable radius, measured abstention rate |
| **E6◆ prospective mini** | RQ1/2 | 1 max-separation new intervention, within-subjects preregistered; a-priori power → N≈80 | directional prediction hit; even null gives predictive-validity upper bound |

## 6. Pre-registered dual-threshold triage protocol
1. Learn τ_disp (axis 1) and τ_level (axis 2) ONCE in the calibration feature
   space; **freeze BEFORE seeing results** (log timestamp in PROGRESS.md).
   Either axis over threshold ⇒ trigger human study; both low ⇒ release.
2. Screening favors high recall (miss = releasing a dangerous design = far worse
   than false alarm); report precision at given recall.
3. Abstention rule: uncertainty band / high ECE / novel uncalibrated feature dim
   / human-agent reversal region → abstain + recommend human study. Abstain =
   safe default for zero-history novel designs.
4. Report measured abstention rate on real modern-design sample.
5. E6 N≈80 within-subjects as the protocol's real operating-point check.

## 7. Datasets & baselines
- Primary: **Bansal et al. CHI'21** (adoption, explanation effect, over-reliance
  on wrong AI). Secondary: **Lu & Yin CHI'21** (dynamic trust update / switching).
- Contamination mitigation: perturbed data + E3 cross-class extrapolation;
  honestly report model training cutoff vs data release date.
- Baselines (per axis): random, **mean-predictor** (outputs only p(1−p)),
  prompt-only, single-model; plus rational-Bayesian null model.

## 8. Statistics
Hierarchical **beta-binomial** to separate true over-dispersion from binomial
sampling noise; bootstrap over (personas × seeds) for CI; LOIO permutation test;
difficulty as control covariate (partial correlation / mixed-effects);
**Benjamini–Hochberg** multiple-comparison correction; report effect sizes + CI.

## OPEN (PI to confirm) — see §15 of v2.4
- Target venue (CHI Methods primary?) + scope narrowing in title; RTI → FAccT.
- Whether to run prospective E6 + sequential stateful extension (also the C0 open
  question: is reliance-stability regime-dependent / sequential-feedback-driven?).
- Availability of a public 2024–2026 modern reliance dataset.
- **Powered confirmatory axis-1 (H1a) NOT yet run** — the PRIMARY (C1) result is pending.

## DECIDED (log) — full chronology + WHY in docs/DECISIONS.md
- Gate 1 data = Bansal + Lu&Yin CHI'21 (verified URLs; see PROGRESS §Gate status).
- Gate 2 batch API = GitHub Models via env var `GH_MODELS_TOKEN`; AzureFoundryProvider
  merged (PR #9) as the uncapped fallback (per-model DAILY cap is tier-dependent
  ~200 strong / ~500 mini).
- Gate 3 = PI owns correctness; independent audit + Manager numeric re-derivation is the merge gate.
- **POSITIONING LOCKED (2026-07-16T06:15:38Z, PI; DECISIONS D5.4): headline = methodological reframe
  (over-dispersion as a safety DV + two-axis pre-deployment triage), validated by panel↔human
  correspondence on two datasets + prereg; the empirical signal is the DETECTION TARGET, not an
  effect-size boast; axis-2 backfire = tentative lead pending powered E4; locked BEFORE the
  confirmatory so the result can't bias framing. Novelty gap verified in docs/research/2026-07-16-novelty-positioning.md.**
- H1a refined: axis-1 over-dispersion is user×task under AI ON BANSAL (2026-07-15, b48ab2b).
- **CONTRIBUTION STRUCTURE (2026-07-15, PR #6): C1 (panel two-axis) = PRIMARY; C0
  (trait→user×task) = DEMOTED to a Bansal-specific supporting finding (Lu&Yin PR#5
  trait-stable 0.80; discriminator PR#6 INCONCLUSIVE — ceiling artifacts);
  sequential-feedback = OPEN QUESTION.** (C0 was briefly elevated to co-anchor 2026-07-15
  then demoted on honest grounds.)
- **Panel: PR #3 NULL (compliance-collapse) → PR #4 redesign (conflict-conditioned DV +
  wrong-AI axis-2 + hard items + strong personas) RESOLVES it (conflict 3%→43%, personas
  diverge, elasticity +0.19 underpowered, axis-2 wrong-AI 0.325, p5 backfire).**
- **PREREG amendment (2026-07-16T02:29:50Z): confirmatory model set → {gpt-4o, gpt-4.1-mini}
  (stable OpenAI, day-batched); non-OpenAI (Llama/Phi) = EXPLORATORY-ONLY — provider-stability
  limitation on GitHub Models (timeouts/500s/unparseable→0). Cross-vendor deferred to Azure.**
- Prereg: axis-1 design LOCKED 2026-07-15T09:23:55Z; τ_disp/τ_level + power-N NOT YET FROZEN.
