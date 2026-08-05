# Preregistration — Human Validation of Synthetic-Panel Coercion Measurement (Axis-2)

*Companion human study to* **Don't Crash-Test with Your Safest Driver: A Backend-Sensitivity Audit of
Synthetic-User Interface-Content Risk Measurement.** Draft for OSF preregistration + IRB submission.
Status: **designed, not yet run or preregistered.**

---

## 1. Summary

Our main paper audits a *synthetic* panel (persona-conditioned LLMs) that screens an AI-advice interface for
its tendency to steer users into adopting a confidently **wrong** AI recommendation under a coercive ("dark")
framing. The synthetic panel shows a real coercive-framing effect (pooled item-clustered OR **1.90** beer /
**1.17** amzbook) but its magnitude is backend-dependent. **No human data yet anchor the coercion axis.**
This study collects that anchor: does the coercive framing raise **wrong-advice adoption in real people**,
does a trusting-novice disposition moderate it, and how does the human pattern compare to each backend?

We make **no** prediction-validity claim for the synthetic panel from this study; it establishes whether the
*human* coercion effect the synthetic panel is meant to stand in for exists and in what direction.

## 2. Background & link to synthetic findings

- The synthetic study renders one **unchanged** review-classification item under framing conditions and
  shows a **guaranteed-wrong** AI verdict. Adoption = the final decision matches the wrong AI.
- Headline synthetic results this study connects to: (i) coercive framing raises wrong-advice adoption over a
  matched neutral baseline (OR 1.90 / 1.17); (ii) a placebo (content-free explanation) sits at/below the
  neutral floor; (iii) an explicitly trusting-novice persona is the top adopter in all cells.
- We reuse the **same item pool** (Bansal CHI'21 beer & amazon-book sentiment items) and the **same three
  framings** so human and synthetic measurements are on the same scale (see `study/stimuli/`).

## 3. Hypotheses

**Confirmatory**
- **H1 (primary harm estimand).** Among trials on which the participant's **initial judgment is correct**,
  the probability of switching to the guaranteed-wrong AI recommendation is higher under the static
  coercive (**dark**) framing than under the matched **neutral** framing (one-sided). Initial correctness
  is measured and locked before the framing is shown, so this conflict-conditioned subset is pre-treatment.
- **H2 (secondary framing contrast).** The correct-to-wrong flip probability is higher under **dark** than
  under **placebo** (wrong AI + content-free explanation). The placebo-neutral difference is reported as an
  estimate + 95% CI; nonsignificance is **not** interpreted as equivalence.

**Secondary / exploratory**
- **S1 (scale-matched adoption).** Final wrong-advice agreement (final judgment = displayed wrong advice)
  is reported for comparability with the synthetic panel, but it includes people who were already wrong
  before seeing the AI and is not described as AI-caused movement.
- **E1 (dispositional moderation; estimation only).** Report the standardized association and CI between
  AI-deference / task self-confidence and the dark effect. No supported/not-supported decision is made at
  N=80. Components are reported separately as well as in the preregistered composite.
- **E2 (backend correspondence; descriptive only).** Place the human adoption/flip estimates relative to
  synthetic backends rerun on the **same final items and framings**, with participant-and-item bootstrap
  uncertainty. We do not designate any backend "most human-faithful."
- **E3 (escalation dose).** Compare three trailing **dark+directive** trials to the static-dark main-block
  estimate as an exploratory escalation result. Because this is a fixed end block, it is explicitly
  confounded with trial position and is not part of H1/H2.
- **E4 (own-sample human anchor).** Use the pre-advice initial judgments to estimate item difficulty and
  between-user variation on the exact study items, independently of the AI framing.

## 4. Design

- **Main framing block:** within-subject, 3 levels — **neutral**, **placebo**, **static dark** — with 4
  trials per level. The displayed AI advice is **guaranteed-wrong (1 − ground truth)** and its displayed
  confidence is fixed at **92% in every condition**; only framing/explanation language varies.
- **Exploratory escalation block:** after the 12 randomized main trials, participants complete 3 additional
  dark trials with an agreement-contingent directive: agreement is acknowledged and confidence encouraged;
  disagreement triggers a warning suggesting switching or lowering confidence. These trials are never
  included in the confirmatory dark-vs-neutral estimate.
- **Domain:** between-subjects — each participant is assigned to **one** dataset (beer *or* amzbook), ~half
  each, so items stay coherent and both datasets (as in the paper) are covered.
- **Items:** 12 main + 3 non-overlapping escalation items per participant, **selected in the
  "movable band"** — reviews where real humans (Bansal no-AI condition) are usually right but not certain
  (per-item human accuracy near ~0.70). This is where a confident wrong AI + coercion can plausibly move a
  correct answer; picking easy items would floor the clean flip outcome. Beer uses 8 NEGATIVE / 4 POSITIVE
  main items because only one beer-POSITIVE item falls in the movable band; amzbook uses 6/6. This
  domain-specific split is disclosed and label direction is entered in sensitivity analyses. Historical
  no-AI accuracy is used **only for item selection**, never shown to participants or used as an outcome
  predictor. On Bansal wrong-AI trials, humans adopted the wrong advice 27% (beer) / 30% (amzbook).
- **Trial:** two-stage to expose the mechanism — (1) read the review, make an **initial** binary judgment +
  1–5-star confidence; (2) see the AI-advice panel, then retain/revise the judgment and actively rerate
  confidence. The final answer is prefilled with the initial answer in every condition (symmetric status quo).

## 5. Participants, recruitment, power

- **Platform:** Prolific. **Target N = 80 analyzable** (≈40 beer, ≈40 amzbook); recruit ~**92** to absorb
  incomplete/withdrawn sessions.
- **Eligibility:** fluent English; US or UK; approval rating ≥ 95 %; ≥ 20 prior submissions; desktop.
- **Compensation:** pilot-timed payment at ≥£9/hour; current planning assumption is 12–15 minutes
  (approximately £1.80–£2.25 per completed participant).
- **Power:** `study/power_sim.py` simulates the actual two-stage process, exact final-item accuracies,
  balanced domains, Latin rotations, participant/item heterogeneity, and declining AI trust with trial
  position. The primary test is correct-to-wrong flip, participant-clustered, one-sided α=.05.

  | conditional flip scenario (neutral → static dark) | N=80 power: flip | N=80 power: raw adoption |
  |---|---:|---:|
  | small, 0.095 → 0.13 | 0.31 | 0.16 |
  | moderate, 0.095 → 0.16 | **0.64** | 0.34 |
  | strong, 0.095 → 0.22 | **0.97** | 0.74 |
  | domain-heterogeneous, 0.095 → 0.22 beer / 0.13 amzbook | 0.75 | 0.40 |

  N=80 is therefore powered for a **strong** effect and provides an informative bound for a moderate one;
  it is not powered to treat a null as evidence of absence. Under the moderate scenario, learning can move
  flip power from 0.75 (no decline) to 0.49 (strong decline). Trial position is recorded and modeled.

## 6. Materials

Stimuli are pre-rendered in `study/stimuli/stimuli_{beer,amzbook}.json` (reproducible via
`study/export_stimuli.py`), each item carrying `review_text`, `ground_truth`, `displayed_ai_advice`
(= 1 − ground truth), and the three framing renderings. Label semantics have been manually verified:
**1=POSITIVE, 0=NEGATIVE**. Framings mirror the synthetic renderers:

- **neutral:** `AI prediction: <LABEL> · AI confidence: 92%` (plain).
- **placebo:** neutral + a single content-free sentence ("The AI model analyzed the input using its trained
  parameters and generated this recommendation…") — matched shape, zero task-relevant content.
- **dark:** `⚠️ CRITICAL DECISION ⚠️` · 92 % confidence · expert-authority + **accountability** language
  ("…you will be held accountable for your decision… Your decision carries full responsibility. Choose
  wisely."). The main dark condition is static and construct-matched to the synthetic study. The trailing
  escalation block adds the separately identified response-contingent directive.

## 7. Procedure & timing (~12–15 min; finalized by internal pilot)

| step | ~time |
|---|---|
| Language choice + consent + instructions | 1.5 min |
| Pre-task survey (disposition + domain familiarity, 6 items) | 1.0 min |
| 12 two-stage trials × ~30 s | 6.0 min |
| 3 dark+directive escalation trials | 1.5–2.0 min |
| Perceived-AI-accuracy probe + debrief | 1.0 min |

Instructions state that "an AI assistant will give a recommendation" — participants are **not** told it is
always wrong (required for the manipulation); this is disclosed at debrief.

## 8. Measures

**Pre-task (individual differences).** 5-pt Likert unless noted.
- *AI-deference / trust* (3 items, e.g. "When an AI system is confident, I tend to go along with it";
  "I usually trust automated recommendations over my own first guess"; "If an AI expert system disagrees with
  me, it is probably right").
- *Domain skill / self-confidence* (2 items: self-rated familiarity with beer/book reviews; confidence in own
  judgment on this task).
- *AI-use frequency* (1 item).
- **Trusting-novice index** = z(AI-deference) − z(domain skill/self-confidence), preregistered composite.
  Survey controls use neutral midpoint defaults for convenience; because defaults can anchor responses,
  all individual-difference analyses are estimation-only and the components are reported separately.

**Per trial.** initial/final decisions, initial/final confidence (1–5 stars), condition, arm, item, displayed
confidence, trial position, response times, and whether the initial judgment was correct.

**Derived DVs.** correct-to-wrong **flip** (primary); raw final wrong-advice agreement; wrong-to-correct
recovery; confidently-wrong final judgment; confidence change.

**Post-task.** Perceived number of correct AI recommendations (five ordinal categories), used descriptively
to diagnose learning/suspicion. Response times are recorded but are not used to exclude participants.

## 9. Randomization & counterbalancing

Recruitment is split into two quota-balanced Prolific links/studies (40 beer, 40 amzbook). Within domain,
participant ID deterministically selects one of three item→condition Latin rotations; display order is
randomized. The 3 escalation items always follow the 12 main trials and are excluded from H1/H2.
One public experiment URL presents English/Chinese choice; language is recorded and entered as a descriptive
stratification/fixed covariate. Review content remains English.

## 10. Analysis plan

- **H1 primary:** initially-correct main-block trials only:
  `flipped_to_wrong ~ dark + domain + item + trial_position`, with participant-clustered inference.
  The dark>neutral test is one-sided α=.05; a two-sided 95% CI is always reported. The planned sensitivity
  ladder is GLMM with participant/item effects → participant-clustered logistic with item fixed effects →
  participant-cluster bootstrap.
- **H2:** same clean flip outcome, dark>placebo. H1/H2 p-values are Holm-adjusted. Placebo-neutral is
  estimation-only unless an equivalence margin is separately preregistered.
- **S1:** raw final wrong-advice agreement uses the same covariates, reported as a secondary scale-matched
  estimate, not causal movement.
- **E1:** trusting-novice index and component interactions are estimation-only (standardized OR + CI).
- **E2:** bootstrap participants and items when comparing human profiles to exact-stimulus backend reruns.
- **E3:** escalation effect reported descriptively and with a model adjusted for position; no causal claim
  separates directive from end-block order.
- **E4:** summarize own-sample initial accuracy and between-user variation by item/domain.
- **Domain/language:** domain is a fixed effect; domain×condition is secondary. Language is recorded and
  reported as a descriptive stratification/fixed-covariate sensitivity analysis.

**Analysis set.** Confirmatory analyses use completed, non-withdrawn, unique-participant sessions. We do not
exclude on attention checks, comprehension gates, response time, or response pattern. Partial/dropout data
are retained only for attrition reporting. No participant is excluded because of outcome values.

**Pilot.** An internal dry run verifies timing, rendering, complete data upload, and variable coding. It is
not included in confirmatory data and does not impose a statistical response-quality gate.

## 11. Ethics

- **Deception + debrief.** The AI advice is deliberately wrong and the dark condition applies accountability
  pressure; the escalation block adds an explicit contingent directive. A full debrief discloses all
  manipulations, states no real accountability existed, and offers a working data-withdrawal choice.
- **Consent.** Consent states that AI content may be manipulated/inaccurate. Prolific IDs are collected for
  payment, pseudonymized/hashed, and removed from released data.
- **Approvals.** IRB/ethics approval required before recruitment. OSF preregistration timestamped before data
  collection. No special-category personal data collected.

## 12. Data & reproducibility

DataPipe writes per-session CSV data to OSF after its experiment ID is configured. Released on acceptance:
de-identified trial data, stimuli, scripts, and analysis code. Raw Prolific IDs are never released.

## 13. Open decisions for the team (before locking)

1. **N=80 decided:** this detects strong effects and bounds moderate effects; null ≠ evidence of absence.
2. Configure the final **DataPipe experiment ID**, Prolific completion URL, and researcher/ethics details.
3. Implement/verify the two quota-balanced domain links and deterministic Latin rotation.
4. Complete the item content-warning scan and internal end-to-end dry runs before OSF locking.
