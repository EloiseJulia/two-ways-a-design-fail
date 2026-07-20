# E6-stripped — Axis-2-only Human Validation (DESIGN, review-only; N≈40 Prolific)

> **Status:** DESIGN ONLY — drafted 2026-07-19 for PI review, **NO recruitment**. Per PI directive
> (2026-07-19), this is the *stripped, fastest-path* E6 that validates only the paper's STRONGEST,
> most-robust positive findings (axis-2 wrong-AI over-reliance + persona-p5 susceptibility), deferring
> the harder axis-1 correspondence (which amzbook D5.27 showed is degenerate/underpowered even on
> synthetic anchors). This is NOT preregistered. Freeze §§1–4 with a UTC timestamp in
> `docs/DECISIONS.md` and obtain IRB approval BEFORE any data collection. The full 6-interface,
> N≈60 design remains in `docs/plans/e6-human-study-design.md` as the eventual capstone.

## 0. Why stripped, and why now
The paper's load-bearing gap is the **unvalidated panel↔human link**. After the pivot (D5.22) our two
most robust, cross-domain (beer+amzbook, D5.27), cross-model results are both **axis-2**:
1. **Wrong-AI over-reliance exists and is model-idiosyncratic with frontier resistance** (gpt-4.1 the
   sole over-relier; gpt-5.5 resists below chance).
2. **Persona-p5 (trusting-novice) is the single most-susceptible profile in EVERY model, both domains**
   (dark adoption 1.00/1.00/1.00/0.40 amzbook; 1.00/1.00/1.00/0.60 beer) — the paper's robust positive.

Axis-1 correspondence, by contrast, is null in all 4 synthetic runs AND degenerate on the amzbook human
anchor (D5.27) — it needs a much larger/richer human sample than N≈40 to test fairly. So the
**highest-leverage, cheapest human validation** is axis-2-only: does a coercive wrong-AI interface
actually over-coerce real humans, is the trusting-novice human the most susceptible, and **which
model's panel ranking best matches humans** (the sharpened capability-dependence question). A stripped
axis-2 E6 answers reviewers A1/A8 (synthetic ≠ real) for the paper's core positive claim at minimum
cost, and is honest about what it does NOT yet validate (axis-1 correspondence → future full E6).

## 1. Research questions / hypotheses (freeze before data; report REGARDLESS)
Per interface `i` and participant `u`, the panel pre-generates (and logs BEFORE recruitment) a
predicted axis-2 wrong-AI over-reliance `D̂2(i)` per model, and a per-persona prediction.
- **H1 (dark coercion works on humans — sanity/primary):** on the `Dark/Wrong-AI` interface, human
  adoption of the guaranteed-wrong AI (conflict-conditioned) is significantly HIGHER than on the
  `Faithful` interface. Within-subject contrast. (If this fails, the whole coercion construct is
  externally invalid — a critical, publishable bound.)
- **H2 (persona localization validates — the robust positive):** human participants scoring high on a
  pre-registered **trusting-novice index** (high self-reported trust/AI-deference × low domain skill —
  the human analogue of persona p5) show significantly higher wrong-AI adoption on the Dark interface
  than low-index (skeptical/expert) participants. This is the direct human test of the paper's most
  robust cross-model/cross-domain finding.
- **H3 (WHICH model's panel tracks humans — the sharpened capability-dependence question):** rank the
  4 ladder models' panels by how well their axis-2 predictions match the observed human pattern (per-
  interface adoption gap AND per-persona-index ordering). Preregistered exploratory-confirmatory:
  we predict the mid-tier model (gpt-4.1, the human-like over-relier) matches humans BETTER than the
  frontier gpt-5.5 (which resists below chance and would UNDER-predict human susceptibility) — i.e.
  the "safest" panel model is the LEAST human-faithful screener. Report the full model×human
  correspondence regardless.
- **Reporting commitment:** a null on any hypothesis is a publishable bound on synthetic-panel validity
  (locked D5.4 framing).

## 2. Design (minimal, powered for the within-subject axis-2 gap)
- **Type:** within-subjects, counterbalanced interface order, attention/quality checks.
- **Interfaces (3 only, to fit N≈40):**
  1. `Faithful` (Conf.+Adaptive (Expert)) — the honest-explanation baseline; AI advice = model pred.
  2. `Placebo` (Conf.+Placebo) — controls for a generic "AI present" nudge without coercion (isolates
     the DARK effect from mere AI-presence). AI advice = model pred, non-coercive framing.
  3. `Dark/Wrong-AI` — the coercive guaranteed-wrong design; AI advice = 1−ground_truth, coercive
     high-confidence framing (identical construction to the synthetic axis-2 dark condition).
- **Domain:** ONE calibration domain (beer OR amzbook — pick beer, richer human anchor). Held-out
  Bansal items NOT used to build the panel item-selection (item-level leakage firewall).
- **Trials:** ~15 items per interface (matched difficulty; conflict-eligible items where human
  System-1 is likely to differ from the shown AI advice), randomized order. Total ≈45 trials/participant.
- **AI advice construction:** faithful/placebo = Bansal pred+conf; dark = guaranteed-wrong 1−gt with a
  coercive high-confidence presentation — byte-identical logic to the synthetic dark arm.

## 3. Participants, power, recruitment (NOT executed — for PI review)
- **N ≈ 40** (target). Primary power driver = the within-subject Dark−Faithful adoption gap, which the
  panel predicts to be LARGE (synthetic dark adoption 0.5–0.66 for over-reliers vs faithful floor);
  N≈40 within-subject is well-powered for a large paired contrast (H1). H2 (subgroup interaction) is
  the harder target — pre-compute achievable power; if the trusting-novice split is underpowered at
  N=40, note N=40 as a FLOOR with a possible extension to ~60 (decided before data, not after).
- **Recruitment:** Prolific, Bansal-style qualification; attention checks + Bansal-4.4 exclusion
  (median RT < 2s or all-same-label). Fair pay ≥ local minimum-wage equivalent. **IRB/ethics approval
  REQUIRED before data collection** (deception via a deliberately-wrong coercive AI → mandatory debrief).
- **Measures:** per-trial initial (no-AI) decision, final decision, AI advice shown, confidence, RT;
  post-task battery to build the **trusting-novice index**: self-reported AI trust/deference,
  AI-literacy, domain familiarity, plus demographics. Debrief on the Dark condition.
- **Rough budget:** N=40 × ~12–15 min × fair rate ≈ £4–5/participant + Prolific fee → order **£250–350**
  (one-shot; no compute). Confirm exact figure at freeze.

## 4. Analysis (freeze before data)
- **Human axis-2 DV:** conflict-conditioned adoption of the shown wrong AI on Dark, vs Faithful/Placebo
  floors — mirrors `twdf` `over_reliance_on_wrong`; recompute displayed_ai_advice = 1−ground_truth
  from ground_truth (the E4 sign-inversion firewall, same as synthetic).
- **H1:** paired test (Dark vs Faithful; Dark vs Placebo) on per-participant adoption; effect size + CI;
  permutation.
- **H2:** trusting-novice index (pre-registered composite, standardized) × interface interaction on
  adoption (mixed-effects with participant random effect); report the high-vs-low-index adoption gap on
  Dark with CI. Robustness: also report the raw novice/trusting subgroup.
- **H3:** for each ladder model, correlate its panel's per-interface and per-persona-index axis-2
  predictions with the observed human pattern; report the model ranking + which model (if any) is the
  best human-faithful screener. This operationalizes "capability-dependence" against ground-truth humans.
- **Firewalls:** E6 items held out from panel calibration; panel predictions `D̂2` (all 4 models)
  generated + LOGGED before any human data is seen (pre-registered predictions); BH across the
  hypothesis family; report per-interface, effect sizes + CIs.
- **Explicitly deferred:** axis-1 over-dispersion correspondence (needs a larger, richer human sample;
  amzbook anchor degeneracy D5.27 shows N≈40 cannot test it fairly) → the full E6.

## 5. What each outcome means (all honest, all publishable)
- **H1+H2 hold:** the panel's axis-2 danger signal AND its persona localization are HUMAN-validated —
  the core positive claim becomes a validated pre-deployment screen for *who* a coercive interface
  endangers. Strong top-venue result even without axis-1.
- **H1 holds, H2 null:** humans are coerced but not along the panel's persona axis — scope the claim to
  aggregate axis-2, drop the persona-localization claim honestly.
- **H3 shows gpt-4.1 > gpt-5.5 as a human-faithful screener:** direct, novel evidence that the
  *most-capable* panel model is the *least* faithful deployment-risk screener — a headline cautionary
  result for the silicon-sampling debate.
- **Null:** an important, honest bound on synthetic-panel predictive validity (D5.4 framing).

## 6. Dependencies / to-do before running (none executed yet)
1. Pick the domain + freeze the 3 interfaces and the ~15 held-out items (leakage firewall).
2. Freeze the trusting-novice index composite + τ (if any triage claim is made) BEFORE data.
3. Generate + LOG all 4 ladder models' per-interface / per-persona axis-2 predictions BEFORE recruitment.
4. Freeze the E6-stripped preregistration (§§1–4) with a UTC timestamp in `docs/DECISIONS.md`; IRB approval.
5. Build the E6 web task + logging (separate engineering slice; out of current scope).
6. A-priori power analysis (H1 primary, H2 secondary) → confirm N=40 or set the floor→60 rule.
