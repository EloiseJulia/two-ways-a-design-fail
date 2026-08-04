# Human Study — Detailed Overview

*A companion, plain-language guide to the real-participant experiment for* **Don't Crash-Test with Your
Safest Driver.** This document explains **why** we run the study, **what** participants do, **how** it plugs
into the paper, and the **operational plan** to field it. The formal, freezable spec lives in
`study/PREREGISTRATION.md`; this is the narrative + build guide.

---

## 1. Why this study exists

The paper audits a **synthetic** panel — persona-conditioned LLMs that role-play users — as a *measurement
instrument* for interface risk. Its headline finding is a **measurement-reliability** result: the same
coercive, guaranteed-wrong AI interface is scored very differently depending on which backend LLM powers the
panel, and the strongest backend is the *least* sensitive to the at-risk user.

Everything in the paper is deliberately about the **instrument**, not about people. We repeatedly and
honestly state that we make **no claim** that the synthetic panel predicts real humans. That is the right
scientific posture — but it leaves one question a reviewer will always ask:

> *Does the thing the panel is trying to measure — humans being coerced by a dark AI interface into adopting
> a confidently wrong recommendation — actually happen in real people?*

The synthetic panel's coercion axis (the "dark" framing effect, synthetic OR **1.90** beer / **1.17**
amzbook) has **no human anchor yet**. The over-dispersion axis in our appendix borrows human data from Bansal
et al.; the coercion axis has none. **This study supplies that anchor.** It is the single most valuable next
experiment: it converts the paper from "here is an instrument and its failure modes" to "here is an
instrument, its failure modes, **and** evidence that the human phenomenon it targets is real and points the
same way."

## 2. The one question (and what it is NOT)

**Question:** Under a guaranteed-wrong AI recommendation, does a **coercive ("dark") framing** — high
confidence + expert-authority + accountability pressure — make **real people** adopt the wrong recommendation
more than a plain neutral framing does? And is a **trusting-novice disposition** associated with more of it?

**This study is NOT** an attempt to prove "backend X predicts humans." With N=80 and one human sample we
cannot, and the paper's whole stance is that you *cannot* rank backends by human-fidelity without a human
criterion. Backend correspondence is reported **descriptively only**. Keeping this boundary sharp is what
makes the study credible rather than over-claiming.

## 3. What we measure (constructs)

- **Wrong-advice adoption** — the primary outcome: the participant's *final* judgment matches the
  displayed **wrong** AI advice. This is the exact human analogue of the synthetic panel's DV.
- **Coercion effect** — the *difference* in adoption between the dark and neutral framings, with the advice
  held wrong and constant. This is the human counterpart of the paper's OR 1.90/1.17.
- **Mere-AI-presence** — the placebo framing (wrong AI + a content-free explanation) isolates "there is an
  AI object on screen" from "the AI is coercive." If placebo ≈ neutral < dark, the driver is the coercive
  *language*, not the presence of advice.
- **Trusting-novice disposition** — a pre-task composite (high self-reported AI-deference × low domain
  skill/self-confidence). The synthetic study's most stable persona result is that this profile adopts most;
  here we test whether the *human* version of that profile behaves the same way.
- **Flip** — switching from a correct initial judgment to the wrong final one (the mechanism behind adoption).

## 4. Design at a glance — and why each choice

| choice | what | why |
|---|---|---|
| **3 framing conditions** (neutral / placebo / dark), **within-subject** | every participant meets all three framings | maximizes power per participant and lets us separate *coercion* (dark−neutral) from *mere AI presence* (placebo−neutral); mirrors the paper's Conf./Conf.+Placebo/dark conditions |
| **advice always wrong** | displayed advice = 1 − ground truth in every trial | isolates *framing* as the manipulation; adoption of a wrong label is the risk we care about |
| **two-stage trial** (initial → see AI → final) | capture the judgment *change* | "adoption" and "flip" are about being *moved* off a prior belief; a one-stage design would hide the mechanism |
| **domain between-subjects** (beer *or* amzbook) | each person stays in one review domain | keeps items coherent, avoids domain-switching load in a 10-min task, still covers both datasets like the paper |
| **12 items, ambiguity-selected (movable band), Latin-square framing** | items where real humans are usually right but not certain (no-AI accuracy ~0.70), balanced 6/6 by truth; each appears in all three framings across the sample | this is the fix to "is the task too easy?" — easy items would floor adoption and hide coercion; ambiguous items give the effect room. Backed by Bansal human data (real humans adopt wrong AI **27 %/30 %** on these items). Framing stays orthogonal to item |
| **same Bansal item pool + same framing text** | reuse the paper's stimuli verbatim | human and synthetic measurements land on the **same scale**, enabling the descriptive correspondence analysis |

## 5. Hypotheses, in plain language

- **H1 — coercion effect (confirmatory, primary).** Dark > neutral in wrong-advice adoption.
  *If supported:* the human phenomenon the panel targets is real and directional — the paper's coercion axis
  has a human anchor. *If null:* a crucial, publishable negative — the synthetic "coercion" signal may not
  correspond to a human effect at this dose, which would sharpen the paper's "instrument ≠ human" caution.
- **H2 — mere presence (confirmatory).** Dark > placebo, and placebo ≈ neutral. Shows the coercive *language*
  (not just having an AI suggestion with an explanation-shaped blob) drives the effect.
- **E1 — dispositional moderation (exploratory).** The trusting-novice index predicts higher adoption / a
  bigger dark effect. Under-powered as an interaction at N=80; reported as suggestive.
- **E2 — backend correspondence (descriptive).** Correlate the human adoption profile with each backend's and
  with aggregation rules. We *describe* which is closest; we do **not** crown a "most human-faithful" backend.
- **E3 — flip.** Condition differences in correct→wrong switching.

## 6. What a participant actually experiences (~10 min)

1. **Consent** screen (deception disclosed only at debrief; consent notes "you may be shown AI
   recommendations of varying quality").
2. **Instructions** + one comprehension check ("What are you deciding about each review?").
3. **Pre-task survey** (~7 quick items): AI-deference (3), domain skill/self-confidence (2), AI-use
   frequency (1), one attention/numeracy item.
4. **12 trials**, each: (a) read a short review, choose **POSITIVE / NEGATIVE** + confidence slider; (b) an
   AI-advice panel appears in that trial's framing (neutral / placebo / dark) recommending the **wrong**
   label; (c) make a **final** choice + confidence. ~30 s/trial.
5. **Debrief:** reveals that the AI advice was deliberately wrong and that no real accountability existed;
   explains the research purpose; offers data withdrawal.

The three panels a participant may see for the *same* wrong recommendation (verbatim from
`study/stimuli/`):

- **neutral:** `AI prediction: POSITIVE · AI confidence: 98%`
- **placebo:** same + *"The AI model analyzed the input using its trained parameters and generated this
  recommendation based on its internal confidence evaluation."*
- **dark:** `⚠️ CRITICAL DECISION ⚠️ … AI Expert System Recommendation: POSITIVE … you will be held
  accountable for your decision … Your decision carries full responsibility. Choose wisely.`

## 7. Measures & the trusting-novice index

**Trusting-novice index** = z(AI-deference) − z(domain skill/self-confidence), a single preregistered
composite so the individual-difference test is one number, not a fishing expedition. Per-trial we log initial
& final decision, both confidences, condition, item, and response times (RTs double as an attention signal).

## 8. Analysis (plain-language)

- **Primary:** a mixed-effects logistic model of adoption with a **condition** effect and random intercepts
  for **participant** and **item**; the dark coefficient (one-sided) is H1. Reported as an odds ratio with CI,
  directly comparable to the synthetic OR 1.90/1.17.
- **H2** is two contrasts from the same model (dark−placebo, placebo−neutral).
- **E1** adds the disposition index and its interaction with condition.
- **E2** correlates the human item/condition adoption profile with each backend's synthetic profile.
- Preregistered **exclusions** (failed attention check, too-fast/too-slow, straight-lining) and a GEE fallback
  if the mixed model won't converge.

## 9. Sample size & power (decided: **N = 80**)

Monte-Carlo power (`study/power_sim.py`, within-subject mixed logistic, subject-cluster-robust, one-sided
α=.05):

| assumed effect (neutral→dark) | OR | power @ N=80 |
|---|---|---|
| 0.32 → 0.47 (≈ synthetic beer) | ~1.9 | **0.97** |
| 0.35 → 0.45 (conservative) | ~1.5 | 0.73 |
| 0.38 → 0.44 (weak) | ~1.3 | 0.38 |

The primary H1 test **pools domains** (domain as covariate) so it uses the full N=80 → ceiling power for the
expected effect. Per-domain effects (≈40 each) are secondary/exploratory. Recruit **~92** to net 80 after
exclusions. Human accountability effects are usually *larger* than LLM ones, so 0.97 is a conservative read.

## 10. What each outcome means for the paper

| result | interpretation | how we'd write it |
|---|---|---|
| **H1 supported** (dark > neutral), H2 supported | the coercion phenomenon is real in humans and driven by framing | paper's §8 becomes a *result*: "the coercion axis has a human anchor pointing the same direction; the audit measures a real risk." Strengthens contributions 1–2 materially. |
| **H1 supported, H2 mixed** (placebo also elevated) | coercion real, but "mere AI presence" also lifts adoption | honest nuance; report both; still validates the axis, softens the "language-specific" claim |
| **H1 null** | no detectable human coercion effect at this dose | a genuinely valuable negative: reframes the instrument as measuring a *model behavior* that may not track humans at this intensity — deepens the paper's core "measurement ≠ human" thesis rather than sinking it |
| **E2** any pattern | descriptive only | one figure/table: "human adoption sits near backend X / the abstain-aggregate," explicitly *not* a fidelity ranking |

Because **every** outcome is publishable (the paper's claims are about the *instrument*, and this study is
framed as validation-of-the-target not validation-of-the-panel), there is no result that "breaks" the paper —
a deliberate design property.

## 11. Ethics & deception

Minimal-risk, standard for dark-pattern/over-reliance research. The only sensitive element is **deception**
(the AI is deliberately wrong; the dark condition applies fake accountability pressure). Handled by: informed
consent, a thorough **debrief** that discloses and explains the deception and states no real accountability
existed, an option to withdraw data post-debrief, and pseudonymized storage (Prolific IDs hashed and dropped
before release). **IRB/ethics approval and OSF preregistration must both precede recruitment.**

## 12. Operational plan

**Build.** The two-stage trial with confidence sliders and exact panel rendering is cleanest in **jsPsych**
(hosted on Cognition.run or Pavlovia), which gives precise timing and trial control; **Qualtrics** is a
faster-to-build fallback (loop-and-merge + a randomizer for the Latin square, embedded-data condition
assignment). Stimuli are already machine-readable in `study/stimuli/stimuli_{beer,amzbook}.json`.

**Latin square.** 3 framing rotations over the 12 items; assign each participant a rotation × domain via the
platform's randomizer so conditions are balanced across the sample.

**Timeline (≈2 weeks, IRB permitting).** OSF prereg (0.5 d) → build (1–2 d) → internal pilot n≈8 to check
timing/comprehension (1 d) → launch on Prolific (data typically < 1 d for N≈92) → analysis (1–2 d).

**Cost.** ~92 participants × ~£1.75 + Prolific's ~33 % service fee ≈ **£210–250** (~$270–320) plus any host
fee. A ~10-min study at the £9/hr floor.

**Pre-launch checklist.** ☐ IRB approval ☐ OSF prereg timestamped ☐ label semantics verified against Bansal
codebook ☐ content-warning scan of items ☐ attention check + timing floor wired ☐ pilot n≈8 confirms ≤10 min
☐ debrief text approved ☐ analysis script runs on simulated data.

## 13. Reproducibility artifacts (`study/`)

- `PREREGISTRATION.md` — the formal, freezable protocol (hypotheses, design, analysis, exclusions).
- `export_stimuli.py` → `stimuli/stimuli_{beer,amzbook}.json` + `stimuli_preview.md` — the exact
  participant-facing stimuli (12 items/domain × 3 framings, wrong advice held constant).
- `power_sim.py` — the Monte-Carlo power analysis reproduced above.
- *(to add when built)* the jsPsych/Qualtrics export and the analysis script.

## 14. Risks & mitigations

| risk | mitigation |
|---|---|
| task > 10 min in pilot | drop to 9 items (3/condition); recompute power (≈0.9 stays for OR 1.9) |
| **task too easy → adoption floors** (owner's concern) | items **ambiguity-selected** in the movable band (human no-AI acc ~0.70); real humans adopt wrong AI 27–30 % here; **pilot manipulation-check gate** requires neutral adoption ≥ 0.15 before full launch, else escalate difficulty |
| ceiling/floor on some items (advice obviously wrong) | balanced 6/6 items; item random effect absorbs it; beer-POSITIVE items skew easy (dataset limit) — report per-item adoption |
| participants ignore the AI entirely | placebo/neutral give a live baseline; attention check + RT filter |
| deception concerns from IRB | thorough debrief + withdrawal option; precedent in reliance literature |
| over-reading E2 as fidelity | hard-coded framing in prereg & paper: correspondence is descriptive |

## 15. Relationship to the paper (§8 "Planned Human Validation")

The paper currently carries a short, deliberately modest §8 describing this as *designed but not yet run*.
On completion, §8 upgrades from a plan to a **result section** (or a companion paper), and the abstract's
"validation is a separate, later study" line can be revised. **Recommended sync now:** the paper's §8 still
says *N≈40*; it should be updated to **N≈80** to match this decision (a one-line factual edit + rebuild) —
flagged for the owner, not yet applied.
