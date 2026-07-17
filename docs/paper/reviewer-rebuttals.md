# Reviewer attacks → rebuttals → evidence-gap plan

> **Purpose:** maximize top-venue odds by (a) drafting the honest rebuttal to each likely attack, and
> (b) identifying the CHEAPEST evidence that closes each gap — which prioritizes the remaining work.
> Builds on `docs/research/2026-07-16-novelty-positioning.md` (attack table) + the current evidence
> (confirmatory axis-1 ⟨pending, power-N weak⟩; axis-2 significant clean 0.69 p=0.0098; no human
> validation yet). Severity ★=minor … ★★★★★=fatal-if-unanswered. Honest throughout.

## The attacks (ranked by threat to acceptance)

### A1 ★★★★★ — "Synthetic personas aren't real users; this doesn't predict humans."
- **Current evidence:** panel is calibrated/anchored on real Bansal+Lu&Yin data; conflict-conditioned
  DV; the framing is TRIAGE, not prediction (D5.4).
- **Rebuttal:** we explicitly do NOT claim individual-human prediction; we test whether the panel's
  *interface-level* risk ranking matches humans'. Positioning + preregistration limit the claim.
- **Residual gap (the big one):** no held-out human validation of the panel's per-interface flags. The
  power-N even hints axis-1 correspondence is weak.
- **Cheapest closer:** **E6** (the ~60-subject study) — directly tests panel↔human interface ranking.
  Nothing synthetic substitutes. **PRIORITY 1 (but deferred by PI to last).** Interim: report the
  Bansal/Lu&Yin *calibration* correspondence + be explicit this is screening, not prediction.

### A2 ★★★★ — "The panel just re-encodes the LLM's own priors; 'persona disagreement' is prompt noise."
- **Current evidence:** conflict-conditioned DV (only System-1≠AI cells); item selection uses AI-side
  exogenous props (no human-DV leakage); PR#4 distinguishes preference vs capability-noise disagreement.
- **Rebuttal + gap:** strongest answer is **cross-model / cross-vendor consistency** — if disagreement
  is prompt noise it won't agree across gpt-4o vs gpt-4.1-mini (and ideally a non-OpenAI vendor).
- **Cheapest closer:** the confirmatory already runs 2 models (report cross-model agreement). **Add a
  cross-vendor model via Azure** (the provider exists) for a stronger claim. PRIORITY 3.

### A3 ★★★★ — "Correspondence is only n=5 conditions — you can't do statistics on 5 points."
- **Current evidence:** the frozen prereg uses 5-condition Spearman as SECONDARY; the PRIMARY is the
  within-task difficulty-controlled estimator (scales with items, not conditions).
- **Rebuttal + gap:** lean on the within-task primary; add MORE correspondence points via
  **condition × difficulty-stratum** (single-domain, valid) and **domain × condition** (multi-domain).
- **Cheapest closer:** **difficulty-stratified correspondence** (compute-free on the confirmatory data
  → ~10–15 points) + **multi-domain amzbook** (adds points + generalization). PRIORITY 2.

### A4 ★★★★ — "The axis-1 signal is fragile (ρ swings 0.00–0.067 by task selection)."
- **Current evidence:** disclosed in SPEC §5; the frozen estimator uses all shared tasks; the power-N
  suggests axis-1 is weak/near-null.
- **Rebuttal:** this is WHY the method uses a *calibrated threshold + abstention*, not a point estimate;
  a small/fragile signal motivates the screen's conservatism (D5.4). Report the confirmatory honestly.
- **Residual gap:** if the confirmatory is null, axis-1 as an *empirical* result is weak — pivot weight
  to axis-2 + the method + honest boundary. **Cheapest closer:** honest reporting + robustness readout;
  do NOT chase significance. PRIORITY 2 (robustness harness).

### A5 ★★★ — "Single domain (beer)."
- **Cheapest closer:** **amzbook** (binary, cheap) gives a 2nd domain now; lsat later. PRIORITY 3.

### A6 ★★★★ — "Underpowered."
- **Current:** axis-1 now N=20 (preregistered, powered per the power-N projection); axis-2 powered clean
  run preregistered (D5.13). **Rebuttal:** preregistered, powered, reported regardless. Gap largely
  addressed by the runs in flight. PRIORITY: none extra (in progress).

### A7 ★★ — "Why not just run the human study? What's the saving?"
- **Rebuttal:** quantify cost asymmetry (panel run ~$15–45 / hours vs a human study $5k–50k / weeks);
  the screen's asymmetric cost (a false alarm = run the study anyway; a miss = ship a dangerous design).
  Add a short cost/ROI paragraph. PRIORITY 4 (writing).

### A8 ★★★★ — "LLM homogeneity / silicon-sampling (Santurkar, Seshadri, CoMPosT)."
- **Current:** PR#3 naive-panel collapse → PR#4 conflict-conditioned DV + hard items + persona
  conditioning resolves it (43% conflict, spread 0.11–0.56); calibration step.
- **Rebuttal + gap:** cite the critiques head-on; show conflict-conditioned disagreement is not trivial
  agreement; **cross-model consistency** is the empirical answer (see A2). Cheapest closer = A2's.

### A9 ★★★ (NEW) — "Your dark condition shows a guaranteed-wrong AI (1−gt) — that's not naturalistic."
- **Rebuttal:** it's a deliberate stress test of *susceptibility to a coercive wrong AI* (a dark
  pattern), not a claim about natural model error; the E4 variant (flip ai_pred, more naturalistic)
  corroborates on its truly-wrong subset (0.69). Report both. PRIORITY: none extra.

### A10 ★★ (NEW, disarming) — "How do we trust your pipeline?"
- **Rebuttal (a strength):** preregistration frozen before results; analysis coded BLIND; audit-gated
  merges; **we caught and fixed our own axis-2 sign-inversion bug** (D5.10) via the two-layer gate and
  report it. Turn process rigor into a credibility asset (methods venues reward this).
- **Second self-caught class (D5.16):** a whole-codebase hostile bug-hunt found three latent metric
  bugs BEFORE they touched a merged result — a beta-binomial boundary case that returned ρ≈0.999
  ("maximal over-dispersion") for users pinned at the reliance floor/ceiling (a 0/0→NaN→clamp
  inversion, the SAME failure family as D5.10), a `Wrong-AI-GT` condition not flagged in the UI
  feature vector, and a degenerate-correlation guard that ran AFTER the resampling loop. All three
  are fixed with regression tests; we verified no already-merged number changed. Report this as
  evidence the two-layer gate catches its own errors.

### A11 ★★★ (NEW) — "Item selection is circular: you pick items on human reliance variance, then validate against human reliance."
- **The risk (disclosed, NOT a code bug):** `item_selector.py:10-17` selects the confirmatory item set
  partly on human reliance signal; the panel↔human correspondence check then uses human reliance as the
  criterion. A reviewer can call this circular / an optimistic bias on the correspondence estimate.
- **Rebuttal / mitigation:** (1) selection is preregistered and frozen BEFORE any panel run, so it cannot
  be tuned on a peeked panel↔human effect; (2) selection uses human data only — the panel never sees it —
  so it cannot inflate the panel's *independent* prediction, only the difficulty of the benchmark; (3) the
  honest fix is a **held-out / non-selected item correspondence check** (compute-free on existing Bansal
  rows) reported alongside the primary — add to the confirmatory readout; (4) E6 on fresh items removes it
  entirely. Log as an explicit Limitation, not a silent assumption.

## Synthesis — what actually moves acceptance (ranked)
1. **E6 human validation** — the only thing that answers A1/A8 decisively (deferred to last, by design).
2. **Difficulty-stratified + (later) domain×condition correspondence** — answers A3, boosts the core
   validation power CHEAPLY (compute-free / amzbook). ← do the stratified analysis when confirmatory lands.
3. **Cross-model (have) + cross-vendor (Azure) agreement** — answers A2/A8.
4. **Honest robustness readout + cost/ROI paragraph + the "we caught our own bug" rigor story** —
   answers A4/A7/A10, nearly free.
5. **Multi-domain amzbook** — answers A5, adds A3 points.

## Immediate compute-free actions this implies (no new experiments needed)
- Build the **difficulty-stratified correspondence** + **robustness readout** harness (answers A3/A4),
  ready for the confirmatory data.
- Build **amzbook loader/config** (answers A5, adds A3 points), ready for compute/Azure.
- Write the **cost/ROI** paragraph + the **process-rigor** paragraph (A7/A10) into the paper outline.
- The **cross-vendor** and **E6** items need Azure / human subjects respectively (flagged for the PI).
