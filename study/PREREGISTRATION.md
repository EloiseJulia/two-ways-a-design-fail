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
- **H1 (coercion effect).** Under a guaranteed-wrong AI, wrong-advice adoption is **higher in the coercive
  (dark) framing than in the neutral framing** (one-sided). *Primary.*
- **H2 (mere-presence control).** The **placebo** framing (wrong AI + content-free explanation) does **not**
  exceed the neutral floor (i.e. the effect is driven by coercive language, not the presence of an
  explanation-shaped object). Tested as dark > placebo AND placebo ≈ neutral.

**Exploratory (no confirmatory claim; N is modest for these)**
- **E1 (dispositional moderation).** A *trusting-novice index* (higher self-reported AI-deference × lower
  domain skill/self-confidence) predicts higher wrong-advice adoption and/or a larger dark−neutral effect.
- **E2 (backend correspondence).** Which single backend or aggregation rule best matches the human adoption
  *level and pattern*. **Descriptive only** — with no independent human criterion we do not claim any backend
  is "most human-faithful"; we report correspondence, not validation.
- **E3 (flip).** Rate of switching from a correct initial judgment to the wrong final one, by condition.

## 4. Design

- **Framing:** within-subject, 3 levels — **neutral**, **placebo**, **dark**. The AI advice is
  **guaranteed-wrong (displayed = 1 − ground truth) in every trial**; only the framing varies.
- **Domain:** between-subjects — each participant is assigned to **one** dataset (beer *or* amzbook), ~half
  each, so items stay coherent and both datasets (as in the paper) are covered.
- **Items:** 12 per participant (balanced 6 ground-truth-NEGATIVE / 6 POSITIVE), **selected in the
  "movable band"** — reviews where real humans (Bansal no-AI condition) are usually right but not certain
  (per-item human accuracy near ~0.70). This is where a confident wrong AI + coercion can plausibly move a
  correct answer; picking easy items would floor adoption and hide any effect. Each item appears once per
  participant; framing is assigned by a **Latin square** across participants so every item is seen in all
  three framings across the sample and framing is orthogonal to item. *Item-selection disclosure:* per-item
  human no-AI accuracy is used **only to select** items; no human outcome is shown to participants or used as
  a predictor (selection ≠ label leakage). Empirical floor check: on Bansal's wrong-AI trials real humans
  adopted the wrong advice **27 % (beer) / 30 % (amzbook)** — well off the floor.
  *Known dataset limitation:* the beer set has few ambiguous POSITIVE reviews, so its 6 POSITIVE items skew
  easy (human acc 0.88–0.93); the item random effect absorbs this and the pilot gate (§10) verifies the
  baseline is off the floor.
- **Trial:** two-stage to expose the mechanism — (1) read the review, make an **initial** binary judgment +
  confidence; (2) see the AI-advice panel (per condition) and make a **final** binary judgment + confidence.

## 5. Participants, recruitment, power

- **Platform:** Prolific. **Target N = 80 analyzable** (≈40 beer, ≈40 amzbook); recruit ~**92** to absorb
  ~10–15 % exclusions.
- **Eligibility:** fluent English; US or UK; approval rating ≥ 95 %; ≥ 20 prior submissions; desktop.
- **Compensation:** ~£1.5–2.0 for a ~10-minute task (≥ Prolific's £9/hr floor).
- **Power (Monte-Carlo, `study/power_sim.py`; within-subject mixed logistic, participant+item random
  intercepts, subject-cluster-robust test, one-sided α = .05, ~4 dark + 4 neutral wrong-AI trials/person):**

  | assumed effect (neutral → dark) | odds ratio | power at N = 80 |
  |---|---|---|
  | 0.32 → 0.47 (matches synthetic beer) | ~1.9 | **0.97** |
  | 0.35 → 0.45 (conservative) | ~1.5 | 0.73 |
  | 0.38 → 0.44 (weak) | ~1.3 | 0.38 |

  **Read:** N = 80 is at ceiling (0.97) for an effect the size of the synthetic beer OR, and ~0.73 for a
  merely moderate effect (OR ≈ 1.5). The **primary H1 test pools across domain** (domain as a covariate), so
  it uses the full N = 80; per-domain dark effects (secondary) rest on ≈40 each and are reported as
  exploratory. Human authority/accountability effects are typically **larger** than LLM ones, so the primary
  test is expected to be well-powered.

## 6. Materials

Stimuli are pre-rendered in `study/stimuli/stimuli_{beer,amzbook}.json` (reproducible via
`study/export_stimuli.py`), each item carrying `review_text`, `ground_truth`, `displayed_ai_advice`
(= 1 − ground truth), and the three framing renderings. Framings (participant-facing, mirroring the synthetic
renderers):

- **neutral:** `AI prediction: <LABEL> · AI confidence: <NN%>` (plain).
- **placebo:** neutral + a single content-free sentence ("The AI model analyzed the input using its trained
  parameters and generated this recommendation…") — matched shape, zero task-relevant content.
- **dark:** `⚠️ CRITICAL DECISION ⚠️` · 92 % confidence · expert-authority + **accountability** language
  ("…you will be held accountable for your decision… Your decision carries full responsibility. Choose
  wisely."). The dark condition is a **bundle** (pseudo-high confidence + authority + accountability co-vary),
  exactly as in the paper; isolating individual cues is out of scope.

> **Verify before fielding:** the binary label semantics (currently mapped 1 = POSITIVE, 0 = NEGATIVE) against
> the Bansal CHI'21 codebook, and that item text contains no offensive content requiring a content warning.

## 7. Procedure & timing (~10 min)

| step | ~time |
|---|---|
| Consent + task instructions + 1 comprehension check | 1.5 min |
| Pre-task survey (disposition + domain familiarity, ~7 items) | 1.0 min |
| 12 two-stage trials × ~30 s | 6.0 min |
| Debrief (reveals the AI advice was deliberately wrong) | 0.5 min |

Instructions state that "an AI assistant will give a recommendation" — participants are **not** told it is
always wrong (required for the manipulation); this is disclosed at debrief.

## 8. Measures

**Pre-task (individual differences).** 5-pt Likert unless noted.
- *AI-deference / trust* (3 items, e.g. "When an AI system is confident, I tend to go along with it";
  "I usually trust automated recommendations over my own first guess"; "If an AI expert system disagrees with
  me, it is probably right").
- *Domain skill / self-confidence* (2 items: self-rated familiarity with beer/book reviews; confidence in own
  judgment on this task).
- *AI-use frequency* (1 item) and a single numeracy/attention item.
- **Trusting-novice index** = z(AI-deference) − z(domain skill/self-confidence), preregistered composite.

**Per trial.** initial decision (0/1), initial confidence (0–100), final decision (0/1), final confidence,
condition, item, response times.

**Derived DVs.** wrong-advice **adoption** (final = displayed wrong advice); **flip** (initial correct →
final wrong); confidence change.

**Attention/quality.** 1 embedded instructed-response check; completion-time floor; straight-lining flag.

## 9. Randomization & counterbalancing

Participant → domain (beer/amzbook) by alternation; item → framing by Latin square (3 squares over the 12
items) rotated across participants; item presentation order randomized within participant.

## 10. Analysis plan

- **Primary (H1).** Mixed-effects logistic regression on wrong-AI trials:
  `adopt ~ condition + (1 | participant) + (1 | item)`, `condition` ∈ {neutral (ref), placebo, dark}.
  Test the **dark** coefficient, **one-sided**, α = .05. Report OR + 95 % CI. (Fallback if the GLMM fails to
  converge: logistic GEE / subject-cluster-robust logistic, prespecified.)
- **H2.** From the same model: dark − placebo contrast (> 0 expected) and placebo − neutral (≈ 0; report CI,
  not a null-accept).
- **E1.** Add `trusting_novice_index` main effect and `× condition`; report standardized OR. Exploratory.
- **E2.** Compute human per-item/per-condition adoption; correlate (Spearman) the human adoption profile with
  each backend's synthetic profile and with aggregation rules (mean / median / abstain-on-disagreement).
  Descriptive; no "most faithful backend" claim.
- **E3.** flip rate by condition (McNemar / mixed logistic on the correct-initial subset).
- **Domain** entered as a covariate / moderator (between-subjects); report the dark effect within each domain.

**Exclusions (preregistered).** Fail the instructed-response check; completion < 4 min or > 30 min;
straight-lining on the pre-survey; > 20 % missing trials. Excluded participants replaced up to the target N.

**Manipulation-check gate (prespecified, pilot n ≈ 12).** Before the full launch we confirm the task is not
floored: **neutral-condition wrong-advice adoption ≥ 0.15** pooled (the Bansal human anchor is ~0.27–0.30).
If it floors, we escalate item difficulty (swap in more ambiguous items / drop the easy beer-POSITIVE items)
before locking — recorded as a pilot amendment, not a post-hoc analysis change.

**Multiplicity.** H1 is the single confirmatory test. H2 uses Holm across its two contrasts. All E* are
exploratory and reported as such.

## 11. Ethics

- **Deception + debrief.** The AI advice is deliberately wrong and the dark condition applies accountability
  pressure. A full debrief discloses this, explains the research purpose, states no real accountability
  existed, and offers withdrawal of data. Minimal risk; standard for dark-pattern/reliance research.
- **Consent.** Informed consent screen before any task; right to withdraw; data pseudonymized (Prolific ID
  hashed, dropped from released data).
- **Approvals.** IRB/ethics approval required before recruitment. OSF preregistration timestamped before data
  collection. No special-category personal data collected.

## 12. Data & reproducibility

Released on acceptance: de-identified trial data, the stimulus JSON, `export_stimuli.py`, `power_sim.py`, and
the analysis script. Raw Prolific IDs never released.

## 13. Open decisions for the team (before locking)

1. **N = 80 (decided).** Recruit ~92 to net 80 analyzable (≈40/domain). Primary H1 pools domains at full N.
2. **12 vs 9 items** if piloting shows > 10 min (drops to 3/condition; recompute power).
3. Confirm **label semantics** (1 = POSITIVE?) and add a content warning if any item is offensive.
4. Whether to also field the **dark-rationale** variant (dark + a fabricated item-specific justification;
   already prototyped synthetically) as a 4th condition — costs time/power; likely a separate study.
