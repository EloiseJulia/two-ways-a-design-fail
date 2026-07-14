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
- C1 (core): propose + validate the two-axis triage signal.
- C2 (support): "counterfactual reliance elasticity" — difficulty-controlled
  sensitivity estimate via frozen-persona paired UI swap.
- (RTI = follow-up second paper, out of scope here.)

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
- Two-axis positioning (co-equal vs primary/secondary).
- Target venue (CHI Methods primary?) + scope narrowing in title; RTI → FAccT.
- Whether to run prospective E6 + sequential stateful extension.
- Availability of a public 2024–2026 modern reliance dataset.
