# Human Study — Detailed Overview

*A companion, plain-language guide to the real-participant experiment for* **Don't Crash-Test with Your
Safest Driver.** The formal, freezable specification is `study/PREREGISTRATION.md`; this document explains
the rationale, participant experience, implementation, realistic power, and operational path to launch.

---

## 1. Why this study exists

The paper audits a **synthetic-user panel as a measurement instrument**. Its central result is internal:
the same coercive, guaranteed-wrong AI interface receives very different risk readings depending on which
backend LLM powers the panel, and the strongest backend is the least sensitive to the prompted at-risk
persona. The paper deliberately makes **no claim that the panel predicts real people**.

The missing link is narrower and important: does the *human phenomenon that the coercion axis targets*
actually occur? The synthetic matched contrast finds a dark-framing effect (pooled OR 1.90 beer / 1.17
amzbook), but this axis has no direct human anchor. This study tests whether real people who initially
judge a review correctly are more likely to switch to a confidently wrong AI recommendation when that
recommendation is wrapped in authority/accountability language.

The study does **not** prove that any backend is human-faithful. It supplies:

1. a human directional test of the coercion construct;
2. a clean measure of AI-caused harm (correct initial judgment → wrong final judgment);
3. a descriptive human point/band relative to synthetic backends rerun on exactly matched stimuli;
4. an exploratory escalation result for the owner's response-contingent directive design.

## 2. What we want to observe

- **Primary H1:** among initially-correct trials, static dark framing increases correct→wrong flips relative
  to matched neutral framing.
- **H2:** static dark also exceeds the generic-explanation placebo. Placebo-neutral is estimated with a CI;
  we do not equate nonsignificance with equivalence.
- **Raw agreement (secondary):** final answer = wrong AI advice, retained for scale comparability with the
  synthetic panel. It is not described as caused by the AI when the participant was already wrong.
- **Disposition (estimation only):** whether AI-deference and low task confidence are associated with more
  harmful flipping. N=80 is not sufficient for a strong confirmatory interaction claim.
- **Backend correspondence (descriptive only):** where human estimates sit relative to exact-stimulus
  synthetic reruns, with participant-and-item bootstrap uncertainty.
- **Escalation:** whether adding a live agreement-contingent directive after the static dark panel produces
  a stronger response. Because these are trailing trials, this is exploratory and position-confounded.

## 3. Design

| Component | Design | Why |
|---|---|---|
| Main block | 12 trials: 4 neutral, 4 placebo, 4 **static dark** | Gives a construct-matched human anchor for the synthetic framing |
| Escalation block | 3 non-overlapping **dark+directive** trials at the end | Preserves the directive idea without contaminating H1 |
| Advice | Guaranteed wrong on every trial; displayed confidence fixed at **92% in all conditions** | Holds advice accuracy/confidence constant so framing is the manipulation |
| Domain | Between-subject: beer or amzbook, quota-balanced ~40/~40 | Coherent task experience; both paper domains represented |
| Trial | Initial P/N + 1–5-star confidence → reveal AI → retain/revise + actively rerate confidence | Initial correctness is locked before treatment; clean flip is observable |
| Items | Ambiguity-enriched “movable band” from historical no-AI human accuracy | Avoids a floor where obvious wrong advice cannot move anyone |

Beer uses 8 NEGATIVE / 4 POSITIVE main items because the source dataset contains only one ambiguous
POSITIVE beer item; amzbook uses 6/6. This is disclosed and label direction is included in sensitivity
analyses. Label semantics have been manually verified: **1=POSITIVE, 0=NEGATIVE**.

## 4. What each participant does (~12–15 minutes)

1. **Choose language** (English / 中文). Review text remains English; language is recorded.
2. **Consent and instructions.** Participants are told AI content may be manipulated or inaccurate.
3. **Brief pre-survey** (6 items): three AI-deference questions, task familiarity, self-confidence, AI-use
   frequency. Neutral midpoint defaults are used for convenience; these analyses are estimation-only.
4. **12 randomized main trials.** Each trial stays on one page:
   - read the review;
   - choose Positive/Negative and actively click 1–5 confidence stars;
   - submit and reveal the AI panel;
   - retain or revise the answer (initial answer prefilled symmetrically in every condition);
   - actively rerate confidence and submit.
5. **3 escalation trials.** Same two-stage flow, but the dark panel additionally shows:
   - if initial answer agrees with the wrong AI: a congratulatory message encouraging higher confidence;
   - if it disagrees: a warning suggesting switching or lowering confidence.
6. **One post-task probe:** estimate how often the AI was correct, diagnosing learning/suspicion.
7. **Debrief:** disclose that the AI was deliberately wrong and the pressure/directive was manipulated;
   provide a working **withdraw my data** choice.

There is no attention-check item, comprehension gate, or response-time exclusion. Response times are logged
passively but are not used to exclude participants, per owner decision.

## 5. Measures

Per trial:

`subject, domain, language, position, arm, item, condition, displayed_conf, initial, conf_initial,
rt_initial, final, conf_final, rt_final, initial_correct, flipped_to_wrong, adopted_wrong, changed,
conf_change, directive_shown, directive_type`

Primary DV: `flipped_to_wrong` among `initial_correct=1` main-block trials.

Secondary DVs: raw final wrong agreement, wrong→correct recovery, confidently-wrong final answers,
confidence change. The own-sample initial judgments also provide item-difficulty and between-user anchors.

## 6. Realistic power (N=80)

`study/power_sim.py` now simulates the actual two-stage process, exact final-item accuracies, balanced
domains, Latin rotations, participant/item heterogeneity, and declining trust across trial position.
Results are stored in `study/power_results.json`.

| Neutral→dark conflict-conditioned flip | Flip power | Raw-adoption power |
|---|---:|---:|
| 0.095→0.13 (small) | 0.31 | 0.16 |
| 0.095→0.16 (moderate) | **0.64** | 0.34 |
| 0.095→0.22 (strong) | **0.97** | 0.74 |
| Beer strong / amzbook weak | 0.75 | 0.40 |
| Exact-stimulus synthetic reference (.221→.272/.345) | **0.64** | 0.38 |

Under the moderate scenario, N=100 gives ~0.69, N=120 ~0.78, N=150 ~0.88. Strong learning can reduce
N=80 moderate-effect power to ~0.49. The owner selected **N=80** for cost control. The honest claim is:
the study detects a strong effect and places a useful bound on a moderate one; a null is **not evidence of
absence**.

Recruit approximately 92 to obtain 80 completed, non-withdrawn sessions. Payment is set after timing the
final 15-trial instrument; current expectation is 12–15 minutes, paid at ≥£9/hour.

## 7. Analysis

- **H1:** participant-clustered logistic analysis of correct→wrong flip, static dark vs neutral, adjusting
  for domain, item, and trial position; one-sided directional test plus two-sided 95% CI.
- **H2:** same outcome, static dark vs placebo. H1/H2 use Holm adjustment.
- **Raw adoption:** secondary scale-matched model; not interpreted as movement when initial answer was wrong.
- **Sensitivity ladder:** GLMM with participant/item effects → participant-clustered logistic with item
  fixed effects → participant-cluster bootstrap.
- **E1:** standardized associations/CIs only; no binary hypothesis verdict.
- **E2:** participant-and-item bootstrap against exact-stimulus backend reruns.
- **Escalation:** descriptive/position-adjusted only; no causal separation from its fixed end-block order.

Completed, non-withdrawn, unique-participant sessions form the confirmatory set. There are no attention,
comprehension, RT, or response-pattern exclusions.

## 8. Ethics

The study uses incomplete disclosure/deception: every AI recommendation is deliberately wrong, static dark
uses fake accountability pressure, and escalation adds an explicit directive. Consent states that AI
messages may be manipulated/inaccurate. Debrief explains all manipulations, emphasizes that performance
does not reflect participant ability, and offers data withdrawal.

Prolific IDs are collected for payment, stored pseudonymously/hashed, and removed from released data.
IRB/ethics approval and OSF preregistration must precede recruitment.

## 9. Technical implementation

- `study/experiment/index.html`: bilingual jsPsych single-page judge-advisor instrument.
- `study/stimuli/*.json` and `stimuli.js`: 12 main + 3 escalation items/domain.
- DataPipe→OSF upload hook, Prolific URL-parameter capture, and completion redirect are implemented, but the
  real **DataPipe experiment ID**, completion code, and researcher/ethics details remain placeholders.
- `?debug=1` shows condition labels, preserves CSV download, and fixes an inspectable condition order. It is
  never used for participants.
- Strict ~40/~40 domain balance requires two quota-balanced Prolific links/studies or a server-side quota.
- Item→condition Latin rotation must be tied deterministically to participant ID before launch.

## 10. What each outcome means for the paper

| Outcome | Defensible interpretation |
|---|---|
| H1 supported | The human coercion target exists directionally under a construct-matched static framing |
| H1 null | No detectable effect at this dose/sample; because moderate-effect power is ~0.64, report a bound rather than absence |
| Dark>placebo | Authority/accountability adds harm beyond a generic explanation |
| Escalation stronger | A response-contingent compliance directive intensifies pressure; exploratory due to end-block order |
| Human/backend comparison | Descriptive placement only; does not validate a backend as human-faithful |

The study can strengthen the coercion-axis contribution. It does **not** validate individual predictions,
the trusting-novice persona ordering, backend fidelity rankings, or coverage-greedy selection.

## 11. Operational sequence before recruitment

1. Replace DataPipe/Prolific/researcher/ethics placeholders.
2. Implement quota-balanced domain links and participant-ID Latin rotation.
3. Run an internal end-to-end dry run: all 15 trials, upload, withdrawal, completion redirect, and variable
   coding.
4. Complete content-warning scan and IRB review.
5. Freeze OSF preregistration.
6. Recruit ~92; stop when 80 completed, non-withdrawn sessions are obtained.
7. Run exact-stimulus synthetic backend reruns before interpreting human/backend correspondence.

## 12. Repository artifacts

- `PREREGISTRATION.md` — formal protocol.
- `HUMAN_STUDY_OVERVIEW.md` — this guide.
- `export_stimuli.py` — deterministic item/framing exporter.
- `stimuli/` — final main/escalation JSON + preview.
- `power_sim.py` / `power_results.json` — realistic two-stage power analysis.
- `experiment/` — runnable jsPsych app.
