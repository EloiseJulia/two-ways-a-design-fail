# GPT-5.6 review — one-shot human validation (N=80, ~£250)

# A. Fatal / must-fix before launch

**Launch status: NO-GO.**

1. **The primary manipulation is contaminated by an explicit compliance instruction.** The synthetic dark condition contains authority/accountability framing only; the human dark condition additionally tells dissenters to **"switch to the AI's answer"** and tells agreers to raise confidence. H1 therefore estimates *dark framing + adaptive behavioral directive*, not the paper's coercive-framing effect. Any large OR would not anchor the synthetic OR 1.90/1.17. (`study/experiment/index.html:103–108, 289, 348–370`; `docs/paper/main.tex §5 matched framing contrast`; `study/PREREGISTRATION.md §§3,6`)

2. **The field instrument currently loses all real data.** Non-debug mode neither uploads nor downloads data, captures Prolific IDs, nor redirects to a completion URL. Only debug mode can locally save a CSV. (`study/experiment/index.html:377–397`; `study/experiment/README.md "Before fielding"`)

3. **Implemented randomization contradicts the preregistration.**
   - Claimed: item×condition Latin square and balanced domain assignment.
   - Implemented: independently shuffle items and four copies of each condition; domain is an unconstrained coin flip.

   At 40 participants/domain, an item's expected condition count is 13.3 with SD≈3, so substantial item-condition imbalance is plausible—especially damaging given the five easy beer-positive items. Domain allocation has SD≈4.5 participants and can readily be 31/49. (`study/PREREGISTRATION.md §§4,9`; `study/experiment/index.html:226, 285–289`)

4. **The final-response UI mechanically favors retaining wrong answers.** Whenever the initial answer agrees with the wrong AI, the final wrong answer is preselected; when it disagrees, both choices are cleared. This applies across conditions and inflates "adoption" through asymmetric effort/default effects. In dark trials it compounds the green congratulation/red warning manipulation. Clear the final answer for everyone, or prefill the initial answer for everyone. (`study/experiment/index.html:342–351`)

5. **The beer item set has a severe low-information block.** Five of six beer-POSITIVE items have prior human accuracy 0.88–0.93. They are 42% of beer trials and 21% of all trials. An item random intercept cannot recover power from trials where the wrong recommendation is obvious. If those items carry little effect, OR=1.5 on the remaining trials is diluted toward roughly OR≈1.38, where power is near 0.5–0.6. Replace them now; do not rely on the pilot gate. (`study/stimuli/stimuli_preview.md`; `study/PREREGISTRATION.md §4`)

6. **"Adoption" conflates pre-existing error with AI-caused harm.** If participants are initially wrong, they already match the guaranteed-wrong AI; `adopted_wrong=1` even without changing. The clean harm estimand is correct→wrong switching, which the paper itself calls AI-induced flip. Raw final wrong agreement may remain the comparability outcome, but it must not be described as necessarily being "moved" by the AI. (`study/experiment/index.html:364–370`; `docs/paper/main.tex §5 capability–vulnerability`; `study/PREREGISTRATION.md E3`)

7. **Label semantics remain an explicit unresolved one-shot failure.** `export_stimuli.py` assumes `0=NEGATIVE, 1=POSITIVE`, while both the script and README say this remains unverified. If wrong, every "guaranteed-wrong" recommendation becomes correct. Add an automated codebook assertion and manually audit all 24 labels before launch. (`study/export_stimuli.py:32`; `study/PREREGISTRATION.md §6`; `study/experiment/README.md`)

8. **Ethics implementation does not match the protocol.**
   - Consent says "no known risks beyond everyday computer use," despite fake accountability pressure.
   - It says responses are anonymous, although Prolific IDs must be collected.
   - The promised post-debrief data-withdrawal option is absent.
   - The debrief displays potentially shaming personal "wrong-advice adoption" rates.

   IRB approval must cover the accountability deception, directive if retained, incomplete disclosure, withdrawal mechanism, and wording. (`study/experiment/index.html:62–122`; `study/PREREGISTRATION.md §11`)

9. **The preregistered confidence measure is not the implemented measure.** The preregistration specifies 0–100 confidence; the instrument uses five stars. Initial confidence silently defaults to three stars, while final confidence is cleared and required. Confidence-change estimates are therefore procedurally asymmetric and partly default-driven. (`study/PREREGISTRATION.md §8`; `study/experiment/index.html:211–223, 343–360`)

10. **The comprehension and disposition measures are pre-answered.** The correct comprehension response is preselected; deference items default to "Agree," skill to neutral, and AI use to weekly. Participants can generate fabricated trusting-novice scores by clicking through. Remove all defaults and require active responses. (`study/experiment/index.html:252–282`)

11. **Within-subject carryover is uncontrolled.** Twelve always-wrong recommendations—some obviously wrong—can teach participants to distrust the AI. A dark directive can also change behavior on later neutral trials. Use constrained, position-balanced sequences and model trial number/order; random shuffling alone does not eliminate carryover. (`study/PREREGISTRATION.md §§4,9`; `study/experiment/index.html:285–289`)

---

# B. Power & statistics

## Primary power

The reported **0.97 is credible only under its optimistic target model**: homogeneous conditional OR≈1.9 in both domains, four dark and four neutral observations per participant, no carryover, and no condition-slope heterogeneity. A strong participant intercept is not itself fatal because the within-subject contrast largely cancels it.

However, `power_sim.py` does **not** simulate or fit the claimed analysis:

- It fits ordinary logistic regression with participant-clustered SEs, not a participant+item GLMM.
- It omits item effects from the fitted model and ignores crossed item dependence.
- It has 12 shared items, whereas the experiment has 24 domain-specific items.
- It simulates no domain effect or domain heterogeneity.
- It simulates no participant/item random condition slopes.
- "0.32→0.47" are probabilities for a zero-random-effect subject/item, not marginal generated rates. With the stated SDs, marginal rates are approximately 0.36→0.48.
- Monte Carlo N=400 gives uncertainty of roughly ±0.02–0.05 for the non-ceiling estimates. (`study/power_sim.py`)

A paired re-simulation using two domains and exact rotations produced:

| Actual assumed effect | Approx. one-sided power |
|---|---:|
| OR 1.9 in both domains | 0.97 |
| Beer OR 1.9, amzbook OR 1.17 | **0.69** |
| OR 1.5 in both domains | **0.71** |
| OR 1.3 in both domains | 0.41 |
| OR 1.5, subject SD=1.5 | 0.64 |
| OR 1.5, item SD=1.0 | 0.64 |

The approximate 80%-power threshold is **OR≈1.6**. Thus N=80 is not "ceiling powered for the expected effect." The paper's own two-domain synthetic effects imply a pooled effect near geometric-mean OR≈1.49, not 1.9. The claim that human accountability effects are "typically larger" is unsupported and should not drive recruitment. (`study/PREREGISTRATION.md §5`; `HUMAN_STUDY_OVERVIEW.md §9`; `docs/paper/main.tex §5`)

A two-sided α=.05 test would reduce OR≈1.5 power to roughly 0.55–0.60. A one-sided test is defensible only if preregistered before data, reverse effects receive no significance credit, and a two-sided 95% CI is still reported. Given that reactance is scientifically meaningful, two-sided inference would be more credible.

## H2

"Placebo≈neutral" is not established by a nonsignificant difference. Define an equivalence margin and use TOST, or demote this claim. At N=80, the null CI will be roughly OR 0.69–1.45, far too wide to establish practically meaningful equivalence. Also, both conditions contain AI advice: placebo−neutral tests the addition of generic explanation text, **not mere AI presence**. (`study/PREREGISTRATION.md H2, §10`)

## E1 moderation

E1 is honestly underpowered and should remain exploratory or be removed. Idealized simulations give approximate two-sided interaction power:

- interaction OR/SD=1.3: 0.30
- OR/SD=1.5: 0.58
- OR/SD=1.75: 0.82

Measurement error from five ad hoc, defaulted items will reduce this further. The index also operationalizes `z(deference) − z(skill)`, not the claimed deference×low-skill conjunction; a person can score high from either component alone. Standardize skill within domain and report components separately. (`study/PREREGISTRATION.md E1, §§8,10`)

## E2 correspondence

Each item×condition cell will have only about 13 observations, giving binomial SE≈0.12–0.14 near typical adoption rates. One response moves a cell by ~7.5 percentage points. Backend rankings based on these noisy Spearman correlations will be unstable and attenuated. Bootstrap participants and items, show uncertainty for every correlation/rank, and retain "descriptive only." (`study/PREREGISTRATION.md E2`; `HUMAN_STUDY_OVERVIEW.md §§5,8`)

## Model specification

Domain should be a **fixed effect**, not random: there are only two purposively selected domains. Items are nested in domain and crossed with condition. Participants are nested in domain.

A defensible primary specification is approximately:

`final_wrong ~ condition + domain + item_fixed_effects`

with participant-clustered inference, plus a GLMM sensitivity analysis incorporating participant and item condition slopes where estimable. The current random-intercept-only model risks anti-conservative inference if coercion effects vary across participants/items. Prespecify the domain×condition interaction as secondary. (`study/PREREGISTRATION.md §10`)

## Pilot gate

The ≥0.15 pooled neutral-adoption gate is poorly targeted and noisy:

- n≈12 gives only 48 neutral trials.
- If true adoption is exactly .15, the gate passes only ~43% of pilots.
- At .20 it passes ~77%; at .25, ~94%, before clustering.
- Pooled adoption can hide a floor in beer-POSITIVE items.
- Raw adoption may come from initial errors rather than AI influence.

Gate separately on initial accuracy and neutral correct→wrong switching by domain/label. Pilot participants must be excluded from confirmatory data, and item changes locked before the final preregistration. (`study/PREREGISTRATION.md §10`)

---

# C. High-ROI, ~0-cost additions

1. **Promote correct→wrong flip to key secondary.** Report: correct→wrong harm; wrong→correct recovery; final wrong agreement; condition effects conditional on initial correctness. This directly anchors the paper's "AI-induced flip" metric and isolates actual causal movement.

2. **Add confidently-wrong harm.** Prespecify final wrong answers at high confidence and confidence among harmful flips. This matches the paper's motivating claim of being steered toward a *confidently wrong* recommendation. (`docs/paper/main.tex Abstract/Introduction`)

3. **Add one post-task item:** "Across the study, what percentage of the AI recommendations did you think were correct?" This diagnoses learning, skepticism, and whether easy items destroyed the manipulation. Keep it descriptive.

4. **Record and persist:** participant ID, Latin rotation, domain assignment, item order, condition order, trial index, language, initial/final raw responses, confidence, RT, completion status, withdrawal choice, and partial/dropout data. Current item/condition fields are sufficient only if the data are actually uploaded. (`study/experiment/index.html:324–370`)

5. **Require active confidence responses at both stages** using identical controls. Treat five-star confidence as ordinal or prespecify why a numeric difference is acceptable.

6. **Add trial-number and prior-dark-exposure diagnostics** for carryover. Do not condition the confirmatory result on these; use them as robustness checks.

7. **Do not add a fourth arm.** Equal allocation would reduce H1 from four to three trials per condition—a 25% loss, likely dropping OR≈1.5 power from ~0.71 toward ~0.60. The directive variant is not worth sacrificing the clean anchor.

8. **Include a small fresh-item component if possible.** The paper explicitly flags selection on prior human outcomes as unresolved. Reusing only "movable-band" items validates an enriched curated set, not generalization. Replace the easy beer items with preregistered fresh items selected without human reliance outcomes. (`docs/paper/main.tex Limitations`; `study/export_stimuli.py`)

---

# D. Paper alignment & narrative

The study can legitimately anchor only this claim:

> Real humans show a directional increase in harmful wrong-AI agreement/flip under the same bundled coercive text relative to a matched neutral presentation.

It cannot, by itself, validate: individual-human prediction; the trusting-novice persona ordering; backend fidelity rankings; the capability–vulnerability inversion; coverage-greedy backend selection. Those remain synthetic claims unless the human profile is measured reliably and compared under exactly matched stimuli and estimands. (`docs/paper/main.tex Abstract, Introduction, §5, Limitations`)

Current alignment failures:

1. **N≈40 versus N=80.** Update §8 before preregistration. (`docs/paper/main.tex §8`; `study/PREREGISTRATION.md §5`)
2. **Synthetic dark has no live directive.** The present human manipulation is strictly stronger and qualitatively different.
3. **Human dark adds pixel-level red styling, animation, green/red directive boxes and response defaults.** The paper explicitly claims prompt/content-level—not pixel-level—measurement. Magnitude comparisons are therefore invalid unless presentation is matched or described as a broader human-interface manipulation. (`docs/paper/main.tex Introduction scope, Limitations`; `study/experiment/index.html:27–38`)
4. **Neutral advice is not the paper's matched-natural-wrong contrast.** Human trials force every label wrong while retaining the original classifier confidence; the paper's OR 1.90/1.17 used naturally wrong matched items. Exact OR comparisons require rerunning the synthetic panel on these exact 24 guaranteed-wrong stimuli and exact three human framings. (`docs/paper/main.tex §5`; `study/export_stimuli.py`)
5. **Confidence is not held constant.** Neutral confidence averages 82% beer/77% amzbook and ranges 53–98%; dark is always 92%. Four beer items even show neutral confidence above dark. Consequently, dark−neutral is a bundled authority/accountability/confidence/style effect, not coercive "language" alone.
6. **Fresh-item limitation remains unresolved.** Selecting the human items using prior human accuracy enriches for responsiveness and may inflate apparent validity. Describe the result as validation on a preregistered high-movability set unless fresh items are included.

A supported clean H1 would strengthen contribution 1 by showing the target phenomenon exists. It would **not** show that "the audit measures real risk" broadly, nor that the frontier backend undershoots humans, unless exact-stimulus synthetic comparisons support that statement.

---

# E. Recommendation on the agreement-contingent directive

**Remove it from the study entirely. Do not add a fourth arm at N=80.**

Field the exact three synthetic-matched conditions: neutral, placebo, and dark text, with identical response mechanics. The directive directly instructs the outcome, contaminates confidence, creates carryover, and converts H1 from a coercive-framing test into a test of explicit compliance prompting. A fourth arm would preserve interpretability but wastes too much of the one-shot sample. Save the directive for a separately powered intervention study.

---

# F. Ranked TODO

1. **[fatal]** Remove the agreement-contingent directive and all directive-specific UI.
2. **[fatal]** Implement server-side data capture, Prolific URL parameters, completion redirect, partial-data handling, and test recovery.
3. **[fatal]** Implement actual item×condition Latin rotations and quota-balanced domain assignment.
4. **[fatal]** Make final-response mechanics identical regardless of initial AI agreement.
5. **[fatal]** Verify `0=NEGATIVE/1=POSITIVE` against the original codebook with automated assertions and manual 24-item audit.
6. **[fatal]** Replace the five beer-POSITIVE 0.88–0.93 items; do not trust a pooled n=12 gate to rescue them.
7. **[fatal]** Obtain ethics approval for deception; correct consent risk/anonymity language and implement post-debrief withdrawal.
8. **[fatal]** Remove every preselected comprehension, survey, answer, and initial-confidence default.
9. **[high]** Freeze one confidence scale and use identical active-response requirements pre/post.
10. **[high]** Make correct→wrong flip and confidently-wrong outcomes key preregistered secondaries.
11. **[high]** Rewrite H2 as generic-explanation placebo; specify equivalence bounds or remove the "≈neutral" confirmatory claim.
12. **[high]** Replace the power section: state ~0.70 power for OR≈1.5, ~80% MDE OR≈1.6, and run simulations matching the final analysis/design.
13. **[high]** Prespecify domain fixed effects, item nesting, trial order, and random-slope/fixed-item sensitivity analyses.
14. **[high]** Add perceived-AI-accuracy post-task probe and carryover/order diagnostics.
15. **[high]** Rerun synthetic backends on the exact final human stimuli/manipulations before claiming OR or backend correspondence.
16. **[high]** Update paper §8 from N≈40 to N=80 and remove any claim that this study validates coverage or backend fidelity.
17. **[nice]** Remove the Chinese option unless translation, recruitment, balancing, and analysis are explicitly approved and preregistered.
18. **[nice]** Remove personal adoption-rate feedback from the debrief unless ethics reviewers specifically approve it.
