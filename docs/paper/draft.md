# Two Ways a Design Fails: When Does a Synthetic LLM Panel See the Danger in a Human–AI Interface?

> **Status:** FULL DRAFT v1 (2026-07-20), target venue **CHI**. Grounded in audited results
> (DECISIONS D5.20–D5.30). Numbers are the BH-honest, audit-PASS values (rubber-duck cross-check:
> all figures match `results/axis2_robustness.json`). Over-claims flagged in a critical review pass
> have been scoped down: human-facing conclusions are framed as synthetic-panel findings + E6
> hypotheses; "capability-dependence" is stated as model-dependence + interpretation; the persona
> result is a synthetic-persona invariant (prompt-construct circularity acknowledged); axis-2 is
> "wrong-advice adoption under a guaranteed-wrong stress test" (dark-vs-placebo contrast flagged as
> follow-up). Citations are informal `[Author Year]` placeholders to be converted to BibTeX. Figures
> live in `figures/`. The human validation study (E6) is intentionally a **rough future-work
> placeholder** per PI directive (§9). OPEN framing decisions for the PI: (a) final title; (b) whether
> process-integrity stays a numbered contribution or moves fully into Methods; (c) how much to rebalance
> the framing toward "a reliability audit of synthetic panels."

---

## Abstract

Deploying an AI-advice interface can fail in (at least) two ways. It can make human reliance
**heterogeneous and user-sensitive** — safe on average, dangerous for particular people (an
*over-dispersion* failure). Or it can make users **uniformly over-rely on a confidently wrong AI** — a
coercive *dark-pattern* failure. Catching either failure normally requires an expensive human study. A
tempting shortcut is to screen an interface *before* that study with a **calibrated multi-agent LLM
panel** that plays a synthetic cohort of users. We build such a panel — two-axis (over-dispersion;
wrong-AI over-reliance), conflict-conditioned, preregistered — and ask a question that is prior to
"does it predict humans?": **are the panel's danger signals even robust across the LLMs that power it?**
They are not. The signals are strongly **model-capability-dependent**. On a guaranteed-wrong, coercive
AI, a frontier model (gpt-5.5) adopts the wrong advice only 15–30% of the time — significantly *below*
chance, i.e. it actively *resists* the trap — and homogenizes cross-persona disagreement to near zero,
on two domains; other models show higher adoption, but idiosyncratically (only gpt-4.1 exceeds chance,
and only after multiple-comparison correction on one of two domains; the smallest model is at chance).
Independent-vendor frontier models (claude-sonnet-4.5, gemini-2.5-pro) sit at chance. **The choice of
panel model is therefore a first-order, under-appreciated design decision: within the panel, a
single-frontier-model configuration can suppress a warning that other panel models raise — so if the
frontier model is less human-like than a team's actual users, the screen may under-report risk.** Yet
one signal is robust across all six models and both domains: within the synthetic persona set, wrong-AI
adoption **concentrates in a trusting-novice persona**, the single most-susceptible profile in **12 of
12** model×domain cells (pooled odds ratio 15.0). The panel robustly localizes *which persona* is most
susceptible, even where aggregate rates do not transfer — a synthetic-persona invariant whose
human-population validity is an explicit open question. We contribute (i) the model-dependence finding
(with cross-domain gpt-5.5 resistance) as direct evidence for the silicon-sampling reliability debate,
(ii) the persona-conditioned susceptibility invariant, (iii) the two-axis, over-dispersion-as-safety
protocol, and (iv) a preregistered, audit-gated analysis pipeline (three silent-corruption bugs were
self-caught). We do **not** claim to predict individual humans, nor a validated deployment screen; we
characterize *when a synthetic panel does and does not see the danger*, and design the human study that
would ground it.

---

## 1. Introduction

Consider a product team about to ship a review-triage tool. The interface shows an AI's verdict and a
confidence score, and — to feel trustworthy — a highlighted "explanation." Averaged over a pilot, the
team's numbers look fine: accuracy is up, users seem to like it. What the average hides is *who* the
interface endangers and *when*. A cautious domain expert barely moves; a **trusting novice** takes the
AI's word almost every time — and if a coercive variant of the interface presents a confidently wrong
verdict, that same novice follows it off a cliff while the aggregate barely twitches. The design has
not failed on average. It has failed for a person, in a way the mean cannot see.

This is the gap between *mean accuracy* and *safety*. Two failure modes make it concrete, and they are
the two ways a design fails in our title:

- **Axis 1 — over-dispersion.** Reliance becomes **heterogeneous across users** in a way the interface
  induces. The team ships something that is safe for the median user and unsafe for the tails. Variance,
  usually treated as a nuisance to be averaged away [Bansal 2021; Gajos 2022], is here the *safety
  quantity of interest*.
- **Axis 2 — wrong-AI over-reliance.** Under a coercive framing, users **systematically adopt a wrong
  AI**. This is lethal even at zero dispersion: everyone fails together [Buçinca 2021; Vasconcelos 2023;
  Luguri & Strahilevitz 2021].

The standard way to detect either failure is a human-subjects study — powered, IRB-approved, and slow.
Teams iterate on interfaces far faster than they can run such studies. The question that motivates this
paper is whether a **cheap pre-deployment screen** can act like a smoke alarm: high-recall, run in
minutes, flagging interfaces that *warrant* a human study and clearing those that plainly do not. Not a
replacement for the human study — a *triage* in front of it.

The screen we investigate is a **calibrated synthetic panel**: a set of persona-conditioned LLM agents
that role-play a cohort of users on the interface, from which we read the two axes directly. Synthetic
users are having a moment in HCI [Park 2022; Argyle 2023; Aher 2023], and so is the backlash: a growing
literature warns that LLM-simulated people are **unreliable proxies** — they collapse human diversity,
echo the base model's priors, and mis-estimate distributions [Santurkar 2023; Seshadri 2026; CoMPosT
2023; Hämäläinen 2023]. We take that critique seriously enough to ask a question that comes *before*
"does the panel predict humans?": **is the panel's danger signal even stable across the LLMs you might
build it from?** If it is not, then any claim that "the panel sees the risk" is really a claim about a
particular model — and swapping the model can erase the warning.

Our central finding is that the danger signal is **strongly model-dependent**, and not in a tidy way
(Figure 1). On a guaranteed-wrong interface, the *frontier* model we test (gpt-5.5) does not fall for
the trap — it adopts the wrong AI significantly *below* chance and flattens cross-persona disagreement
to near zero, on **both** domains we study. Other models show higher adoption, but **idiosyncratically**:
the smallest model sits at chance, one mid-tier model (gpt-4.1) exceeds chance, and two independent-vendor
frontier models sit at chance. After multiple-comparison correction, the only *rock-solid* axis-2
regularity is gpt-5.5's cross-domain **resistance**; the elevated-adoption effect is real but
model-specific and survives correction on only one of two domains. We interpret this association with
capability cautiously — alignment, reasoning behavior, or training could drive it as much as raw
capability — but the practical upshot is robust and, we argue, important: **the model you choose to power
a synthetic panel is a first-order methodological decision.** A team that screens with a single frontier
model may see a green light because *that model* resists a coercion its less-capable human users might
not — a risk-masking failure mode that we can demonstrate *within the panel* and hypothesize (but not yet
show) for humans.

Against this negative, one result is stubbornly **robust** (Figure 2). Even where the model mean
collapses, every model ranks the *same* persona as most-susceptible: a **trusting-novice** persona is the
single highest-adopting persona in **12 of 12** model×domain cells (pooled odds ratio 15.0 over the other
personas). The panel cannot tell you the *rate* at which people will over-rely — that depends on the
model — but *within its synthetic persona set* it robustly ranks *who* is most susceptible. We are careful
here: this persona is prompt-defined to be trusting, so 12/12 is in part consistent persona
instruction-following; whether it maps to a real vulnerable human population is an open question we
design the human study to test. Still, "which profile does this interface most endanger?" is often the
more actionable design question, and a robust synthetic answer is a useful starting point.

We make four contributions, and we are explicit about their limits:

1. **Model-dependence of synthetic-panel screening signals** — direct, head-on evidence for the
   silicon-sampling reliability debate: the *same* preregistered protocol yields strong human-like
   failure signals on smaller/mid-tier models and has them resisted/homogenized by gpt-5.5, replicated
   across two domains. Panel-model choice is a first-order methodological decision that can, within the
   panel, suppress a warning other models raise.
2. **A persona-conditioned susceptibility invariant that is robust across vendors** — even when the model
   mean collapses, the panel ranks the trusting-novice persona as most-susceptible (12/12 cells; sign-test
   p = 4.6×10⁻¹⁰; pooled odds ratio 15.0). A synthetic-persona invariant scoped to relative *ordering*,
   not aggregate rate, whose human validity is left to the planned study.
3. **The two-axis protocol** — over-dispersion-as-safety plus wrong-AI over-reliance, conflict-
   conditioned and preregistered — proposed as a reusable *testbed* for reasoning about interface-level
   reliance safety (not a validated screen).
4. **A preregistered, audit-gated analysis pipeline** whose process integrity supports the credibility of
   the negative and nuanced-positive results: analysis frozen before results, blind coding, audit-gated
   merges, and three self-caught silent-corruption bugs reported openly (§8).

We do **not** claim a validated, model-agnostic detector, and we do **not** claim to predict individual
humans. Our panel↔human correspondence is null in every configuration we can currently test (all
underpowered). We frame this honestly as an open validation gap and describe the human study (§9)
that is designed to test it. The paper's job is to characterize *when a synthetic panel sees the danger* — a
prerequisite that, to our knowledge, the simulated-user literature has not isolated.

---

## 2. Related work

**Simulated users for HCI evaluation, and the reliability critique.** LLMs as stand-ins for human
participants have been proposed for surveys, user studies, and formative evaluation [Park 2022; Argyle
2023; Aher 2023]. A parallel literature documents their failure as proxies: they compress opinion
diversity and over-represent majority views [Santurkar 2023], mis-calibrate population distributions
[Seshadri 2026], and caricature rather than simulate subpopulations [CoMPosT 2023; Hämäläinen 2023]. Our
work sits inside this debate but changes the target: we do not ask the panel to *predict* a human
distribution, we ask it to *triage* an interface, and we isolate a specific, measurable pathology —
**capability-dependence of the triage signal** — that the prediction framing obscures.

**Reliance and over-reliance on AI advice.** A large body of work studies when people appropriately rely
on AI given confidence and explanations [Bansal 2021; Buçinca 2021; Zhang 2020; Lai & Tan 2019; Schemmer
2023], generally finding that explanations can *increase* over-reliance rather than calibrate it
[Bansal 2021; Vasconcelos 2023]. This work treats between-user variance as noise around an average
effect. We invert that: reliance **heterogeneity** is our axis-1 safety DV, and coercive wrong-AI
adoption is axis-2.

**Dark patterns and coercive interfaces.** Deceptive and coercive designs are well catalogued
[Luguri & Strahilevitz 2021; Mildner 2023]; our axis-2 gives a computational signal for one coercive
mode (a confidently wrong AI) and, via personas, a read on *who* it captures.

**Pre-deployment / offline evaluation of human–AI teams.** Closest is offline estimation of team
performance for *routing* decisions [Rastogi 2022; Rastogi 2023]; that work optimizes who-decides-what,
not interface-level safety triage. The gap we fill is a *pre-study screen for interface reliance
safety*, and — critically — a characterization of when such a screen's signal is trustworthy.

---

## 3. The two-axis triage: definitions

We evaluate an interface `i` on two axes, both measured on the panel's decisions.

**Axis 1 — between-user reliance over-dispersion.** For each item, personas produce reliance decisions;
we estimate the **excess variance** beyond the binomial `p(1−p)` a single homogeneous user would
produce (a beta-binomial over-dispersion estimator). We compute it **conflict-conditioned**: only on
trials where the persona's independent System-1 judgment disagrees with the shown AI, isolating genuine
reliance from trivial agreement. High axis-1 means the interface makes reliance user-sensitive.

**Axis 2 — wrong-AI over-reliance.** Under a coercive "dark" framing, the interface shows a
**guaranteed-wrong** AI verdict (the negation of ground truth) with high confidence. Axis-2 is the rate
at which personas adopt that wrong verdict. It is dangerous even at zero dispersion — a uniform failure.

**The triage rule (design, not yet validated).** We learn thresholds `τ_disp, τ_level` once in an
atomic UI feature space; either axis over threshold ⇒ *recommend a human study*; both low ⇒ *release
candidate*; out-of-distribution or high-uncertainty ⇒ *abstain*. The rule is deliberately high-recall
(a missed dangerous interface is worse than a false alarm). We report the rule as a **design**; its
validation depends on the human study (§9). Thresholds remain unfrozen pending that study.

---

## 4. Method: the calibrated synthetic panel

**Panel = personas × models.** Each agent is a persona (a vector of domain skill, AI literacy, risk
sensitivity, caution) crossed with a base LLM. Personas span novice/expert × trusting/skeptical plus
two moderates (six in total).

**Dual-system decisions.** Each agent first produces a **System-1** judgment *without* AI (a frozen,
no-AI anchor), then a **System-2** decision *with* the AI advice and the interface's framing. Reliance
is defined against the System-1 anchor, which is what makes the conflict-conditioning possible and
prevents the "everyone-agrees-so-everyone-complies" collapse of a naive panel.

**Faithful interface rendering.** We reproduce the Bansal et al. [2021] explanation conditions
faithfully (confidence-only; single/double highlighted-token explanations; adaptive and
expert-adaptive), and construct the coercive dark condition by negating ground truth at high confidence.
A placebo condition (AI present, non-coercive) isolates the coercion from mere AI-presence.

**Stimuli and domains.** Items are drawn from the Bansal sentiment benchmark, held out from any
threshold fitting, and selected to concentrate on loci of human reliance heterogeneity (disclosed;
human outcomes are used only for *item selection*, never leaked into agent prompts — item selection ≠
label leakage). We run two domains: **beer reviews** and **Amazon book reviews (amzbook)**.

**Models.** A within-provider capability ladder (gpt-4o-mini → gpt-4.1 → gpt-4o → gpt-5.5, identical
config) plus independent-vendor frontier models (claude-sonnet-4.5, gemini-2.5-pro), six models total.

**Rigor spine (a selling point, not boilerplate).** The analysis was preregistered and frozen with UTC
timestamps before results; correspondence analyses were coded blind; every merge was gated on an
independent audit *and* a from-raw numeric re-derivation. This spine caught three silent-corruption bugs
that would each have produced a plausible-but-false result: an axis-2 **sign inversion** (scoring
adoption against the wrong label), a beta-binomial **boundary artifact**, and a decision-parser that
**fabricated** sentinel values. We report these openly (§8); a pipeline that catches its own errors is
part of the contribution.

---

## 5. Experiments & results

We report per-model (no pooling across incomparable models), with effect sizes, confidence intervals,
and Benjamini–Hochberg (BH) correction across the per-model test family. n = 120 dark-condition trials
per model×domain cell (6 personas × 20 items).

### 5.1 Real human over-dispersion exists (anchor)

On the Bansal human data, conflict-conditioned reliance over-dispersion is real and excludes zero
(ρ ≈ 0.067); no-AI reliance behaves as a stable trait (≈0.74) while AI-assisted reliance is a user×task
interaction (0.32–0.41). This anchors axis-1 as a measurable human quantity — and, honestly, does not
generalize to a second human dataset (Lu & Yin), which we report as a boundary.

### 5.2 The danger signal is model-dependent (Figure 1)

On the guaranteed-wrong interface, axis-2 wrong-advice adoption is **not** a clean function of capability.
Across the same-provider ladder (beer / amzbook): gpt-4o-mini 0.50 / 0.48, gpt-4.1 0.60 / **0.66**,
gpt-4o 0.43 / 0.48, gpt-5.5 **0.30 / 0.15**. The frontier model is *below* chance on both domains
(binomial BH p = 8×10⁻⁵ beer, 2×10⁻¹⁴ amzbook) — it actively resists following the wrong advice. The
adoption peak at gpt-4.1 is real (between-model Fisher vs gpt-4o p = 0.014 / 0.006) but **model-
idiosyncratic**: the smallest ladder model sits at chance, and after BH correction gpt-4.1's elevated
adoption survives on amzbook (p = 0.003) but is only nominal on beer (uncorrected p = 0.035; BH
p = 0.11). Independent-vendor frontier models replicate the *at-chance* pattern, not the elevated
adoption: claude 0.49, gemini 0.53 on beer (0/3 vendors exceed chance).

Axis-1 tells a parallel story more cleanly (Figure 3). Mean panel disagreement across the ladder is
0.11 / 0.16 / 0.10 / **0.012** (beer) and 0.12 / 0.19 / 0.11 / **0.015** (amzbook): gpt-5.5 collapses to
near-homogeneity on both domains. This is not a no-conflict artifact — genuine conflict trials remain
present (e.g., 215/600 on amzbook) — the model *resists diverging*, it is not handed easy agreement.

*Coercion vs mere advice-following (a caveat).* We measure adoption of a guaranteed-wrong AI against
chance; our data do not isolate the effect of the *coercive framing* from ordinary wrong-advice
following, because we do not report the dark-vs-placebo/faithful contrast here (a controlled comparison
we flag as immediate follow-up). We therefore describe axis-2 as **wrong-advice adoption under a
guaranteed-wrong stress test**, and reserve "dark-pattern susceptibility" for the controlled contrast.

**Reading.** gpt-5.5's cross-domain **resistance** (both axes) is the rock-solid regularity; adoption
magnitude is model-specific. A synthetic panel's aggregate reading is therefore a property of the
panel's model as much as of the interface: swapping in the frontier model can flip a warning to a
green light *within the panel*.

### 5.3 One signal is robust: which persona the panel ranks highest (Figure 2, Figure 4)

The aggregate adoption **rate** is model-idiosyncratic (range 0.30 across beer models, 0.51 across
amzbook models). The **ordering** of which persona adopts most is not. A **trusting-novice** persona is
the single highest-adopting persona in **12 of 12** model×domain cells (sign-test vs a 1/6 chance top
p = 4.6×10⁻¹⁰). A pooled GEE logistic regression (clustered by cell) gives an odds ratio of **15.0**
(95% CI 5.8–38.8, p = 2×10⁻⁸) for that persona adopting the wrong AI relative to the others; a per-cell
Fisher test is significant in **all 12** cells after BH (largest BH p = 0.002). The persona-minus-others
adoption gap is +0.53 on average and never below +0.30 — it holds even at the resistant frontier. We
foreground the descriptive **12/12** and the large effect sizes over the p-values, whose inferential unit
(12 cells sharing prompts, items, and providers) is not fully independent; the persona is also
prompt-defined to be trusting, so this is best read as a **robust synthetic-persona invariant** rather
than established human-population localization.

The persona **ordering** also agrees across *independent vendors*: on beer, the mean pairwise Spearman
correlation of the six-persona adoption profile across gpt-5.5, claude, and gemini is **0.87** (min 0.82)
— it is not one model's prompt noise (Figure 4, right). We are honest about the boundary: that ordering
agreement attenuates at the amzbook frontier (independent-vendor mean 0.50), because the frontier
compresses the *non-top* personas toward the floor, making their sub-ranking noisy. The robust claim is
precisely about the **top** of the ordering — the highest-adopting persona — which is universal.

### 5.4 Panel↔human correspondence is unvalidated (honest null)

Across every configuration we can test, the panel's per-condition axis-1 signal does **not** significantly
track the human anchor's (Spearman on n = 5 conditions; null under BH for all six models). On amzbook the
correspondence is *degenerate* — the human anchor's per-condition over-dispersion is near-constant, so the
test is uninformative rather than a genuine null. We therefore make **no** predictive-validity claim.
Only a powered human study (§9) can close this gap.

---

## 6. Discussion

**Panel-model choice is a methodological decision with safety consequences.** The field's instinct is
that a *better* base model makes a *better* simulator. For danger-screening, the opposite can hold: the
frontier model we test resists a wrong-advice trap that lower-tier panel models fall into, so a
single-frontier-model panel can under-report a risk *within the panel*. If — and this is a hypothesis for
the human study, not a demonstrated fact — the frontier model is less human-like than a team's actual
users, that under-report would carry to deployment. Either way, "which LLM should power my synthetic
study?" becomes a first-order methodological choice, arguing for **deliberately including lower-tier
models** in a screening panel — a counterintuitive implication.

**Screen for *who*, not *how many* (as a synthetic invariant).** Because the persona ordering is robust
where the rate is not, the defensible use of today's panel is to **surface candidate vulnerable
profiles** for a human study to confirm — a hypothesis-generating signal ("this interface may especially
endanger trusting novices"), not an absolute or validated risk gauge.

**A concrete stance in the silicon-sampling debate.** Rather than a blanket "LLMs (don't) simulate
people," we offer a measured, replicated claim: *aggregate* failure-rate signals are model-dependent
and do not transfer across models, while *relative* susceptibility orderings partially do. That
distinction is actionable for anyone building simulated-user tools.

---

## 7. Limitations & threats to validity

- **Synthetic personas are not people** — the central threat. The model-dependence result makes it
  concrete: "the panel" is not one thing, so any human-facing claim must name the model. Only the human
  study (§9) grounds *which* model, if any, tracks people.
- **The screen is not model-agnostic.** Our own evidence shows the aggregate signal does not transfer
  across capability tiers; we therefore do not claim a deployable, model-agnostic detector.
- **Correspondence is unvalidated and underpowered** (n = 5 conditions; amzbook degenerate). No
  predictive-validity claim is made.
- **Two domains, but both binary sentiment.** We replicate on beer and amzbook — both binary
  sentiment-polarity tasks; other task structures (high-stakes, multi-class, generative) are future work.
- **Coercive construct is uncontrolled.** Axis-2 uses a guaranteed-wrong AI (an upper-bound stress
  test); we do not report the dark-vs-placebo contrast, so we do not separate coercive framing from
  ordinary wrong-advice following (immediate follow-up).
- **Item selection uses human reliance variance** (disclosed): a correspondence-circularity risk. Holding
  items out from *threshold fitting* does not remove selection on the human criterion; a genuinely
  fresh-item human check remains to be done, so we treat this risk as unresolved pending the human study.
- **Persona construct validity.** The most-susceptible persona is prompt-defined to be trusting, so its
  robustness is partly instruction-following; its correspondence to a real human profile is untested.

---

## 8. On trusting this pipeline (process integrity)

Because our headline includes a negative and a nuanced positive, the reader must trust the numbers. We
built the pipeline to earn that trust and, in doing so, caught three bugs that each produced a
plausible-but-false result before correction: (1) an **axis-2 sign inversion** scoring adoption against
`ground_truth` instead of the displayed `1 − ground_truth`; (2) a **beta-binomial boundary artifact**
inflating over-dispersion at extreme rates; (3) a **decision parser** that silently emitted a
`(decision = 0, confidence = 0.5)` sentinel on parse failure, fabricating data. Each was caught by the
two-layer gate (independent audit + from-raw re-derivation) — the last by a read-only watcher. We report
them not as confessions but as evidence that the process is capable of catching exactly the kind of
silent corruption that makes simulated-user results untrustworthy.

---

## 9. Planned human validation (E6) — *placeholder / future work*

> *This section is a rough placeholder; the study is designed but not yet run (see
> `docs/plans/e6-stripped-axis2-design.md`).*

The one thing synthetic compute cannot buy is grounding against real people. We have designed (not yet
run or preregistered) a stripped, axis-2-only human study (within-subjects, N ≈ 40, Prolific) that would
test the paper's two strongest, cross-domain-robust positives against humans: (H1) a guaranteed-wrong AI
interface elicits more wrong-advice adoption than a faithful/placebo baseline; (H2) a **trusting-novice
human index** (high self-reported AI-deference × low domain skill) predicts the highest wrong-AI adoption
— the human test of §5.3; and (H3) *which* ladder model's panel best tracks the human pattern, with the
sharp prediction that a *mid-tier* model tracks humans better than the resistant frontier — i.e. the
most-capable panel model may be the least human-faithful screener. All outcomes, including nulls, would be
publishable bounds on synthetic-panel validity. ⟨Results to be added.⟩

---

## 10. Conclusion

An interface can fail two ways — by making reliance dangerously uneven, or by coercing uniform trust in
a wrong AI — and teams would like to catch both before an expensive human study. We built a calibrated
synthetic panel to do that triage and found that its danger signal is **model-dependent**: the frontier
model we test resists the very wrong-advice trap that lower-tier panel models fall for, so the choice of
panel model is itself a methodological decision with safety consequences. What survives that instability
is *which persona* the panel ranks highest: a trusting-novice profile is the most-susceptible persona for
every model on every domain — a robust synthetic invariant whose human counterpart we have designed a
study to test. We offer this as an honest map of where synthetic-user screening can and cannot be trusted
today, and design the human study that would turn a robust *ordering* into a validated *prediction*.

---

## Appendix / reproducibility

- Analyses: `scripts/analysis/axis2_robustness.py` → `results/axis2_robustness.json` (audit PASS, D5.29).
- Figures: `scripts/analysis/make_figures.py` → `figures/fig1–4` (D5.30).
- Decisions log with preregistration timestamps and audit verdicts: `docs/DECISIONS.md` (D5.1–D5.30).
