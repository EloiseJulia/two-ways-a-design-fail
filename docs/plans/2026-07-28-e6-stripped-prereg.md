# E6-stripped — PREREGISTRATION (DRAFT) : human validation of the synthetic panel

> **STATUS: DRAFT — not yet frozen, not yet IRB-approved, NO recruitment.**
> Freeze rule: §§1–7 are frozen verbatim with a UTC timestamp in `docs/DECISIONS.md`, and the four
> ladder models' predictions (§6) are generated + committed, **before any human data is collected**.
> IRB/ethics approval is required first (deliberate-deception design → mandatory debrief).
> Supersedes nothing; complements the design in `docs/plans/e6-stripped-axis2-design.md`.
> Drafted 2026-07-28.

## 0. Purpose (read this first — it fixes the framing)
E6 exists to **validate the synthetic LLM panel against real people**, i.e. to close the
panel↔human NULL that the paper is honest about. **It is NOT a demonstration that "AI can mislead
humans"** — that is established prior work (Bansal 2021; Vasconcelos 2023; Luguri 2021; Bo 2024) and
would draw a "we already know this" rejection. Here, human over-reliance under coercion (H1) is only a
**manipulation-validity precondition**; the scientific payload is **whether the panel predicts (H2) the
at-risk *person* and (H3) which *backend* best tracks humans** — the human test of the paper's
capability–vulnerability inversion.

**Integrity note.** This preregistration is written to *maximize the sensitivity* of the study to a
real effect and to make **every outcome publishable**, NOT to bias participants toward a conclusion.
The only thing that "pushes" a participant is the disclosed independent variable (the coercive
interface), with matched controls and a full debrief. See §8.

## 1. Hypotheses (frozen; report ALL regardless of outcome)
Predictions are the panel's pre-logged values (§6), fixed before data.

- **H1 (primary, confirmatory — manipulation validity).** On the guaranteed-wrong **Dark** interface,
  conflict-conditioned human adoption of the wrong AI advice is **higher** than on the **Faithful** and
  **Placebo** interfaces. *Directional.* If H1 fails, the coercion construct is externally invalid — a
  critical, publishable bound.
- **H2 (secondary, confirmatory — WHO).** Participants high on a preregistered **trusting-novice index**
  (high self-reported AI-deference × low domain skill) show **higher** Dark wrong-AI adoption than
  low-index participants. *Directional interaction.* Human test of the persona-localization result.
- **H3 (exploratory-confirmatory — WHICH backend).** Ranking the four ladder backends' panels by how
  well their per-interface and per-persona-index axis-2 predictions match the observed human pattern, we
  predict a **mid-tier model (gpt-4.1) tracks humans better than the resistant frontier (gpt-5.5)** —
  i.e. the most-capable panel model is the least human-faithful screener. Report the full
  model×human correspondence regardless of direction.

## 2. Design
- **Type:** within-subjects, counterbalanced interface order, attention/quality checks.
- **Interfaces (3):** `Faithful` (honest AI = model prediction), `Placebo` (AI present, non-coercive —
  isolates coercion from mere AI-presence), `Dark` (guaranteed-wrong 1−ground_truth + coercive
  high-confidence/authority framing, byte-identical construction to the synthetic dark arm).
- **Manipulation decision (frozen).** Dark is **cue-only** (confidence + authority/accountability), with
  **no fabricated per-item rationale**, so the human manipulation stays **matched to the synthetic panel**
  (protects H3). Basis: an exploratory panel A/B (DECISIONS D5.72) showed a fabricated rationale *reduced*
  synthetic adoption (agents refute a checkable wrong rationale), so a rationale would (i) not help and
  (ii) de-match the arms. If a rationale arm is ever wanted, it is a **separate** arm with its own matched
  panel re-run, not a change to Dark.
- **Room to move (frozen).** To avoid ceiling/floor "too-obvious" items, stimuli are selected to be
  **conflict-eligible / ambiguous** (items where the reviewer's sentiment is genuinely mixed and human
  System-1 plausibly differs from the shown AI) — this raises sensitivity to a real effect without
  touching the manipulation.

## 3. Domain, stimuli, leakage firewall
- **One domain:** beer reviews (richer human anchor).
- **~15 held-out Bansal items per interface**, selected on conflict-eligibility/ambiguity. Items are
  **held out from the panel's item selection** (item-level firewall). Human reliance variance may inform
  selection but human outcomes are **never** shown to participants or used as predictors (item
  selection ≠ label leakage).
- **Stimuli language: English** (the benchmark language). UI/instructions may be localized (the prototype
  supports en/zh/ja/de), but translating the *reviews* changes item difficulty and breaks panel
  comparability — deferred as a separate research decision.

## 4. Participants, recruitment, sampling caveat, power
- **Recruitment:** volunteers via the advisor's network (not Prolific). **One-shot, non-renewable sample**
  → freeze the design and pilot on cheap non-precious people (labmates/friends) first.
- **Sampling caveat (pre-declared).** An academic network likely skews skilled/AI-literate, which
  **compresses the trusting-novice-index variance** and can underpower H2. **Mitigation (frozen):**
  purposively recruit for a spread — deliberately include non-experts / older / less-AI-savvy people —
  and **report the achieved index range**. H1 is unaffected by this skew.
- **N ≈ 40** target; primary power is the within-subject Dark−Faithful gap (H1), well-powered at N≈40 for
  the large paired contrast the panel predicts. **H2 floor→60 rule (frozen):** if an a-priori power
  analysis shows the index×interface interaction is underpowered at N=40, extend to N≈60 — **decided
  before data, in one wave** (no "run-more-later" second wave; that confounds sample/time).
- **A-priori power analysis** for H1 (primary) and H2 (secondary) is run and recorded **before** data.

## 5. Measures (frozen)
- Per trial: initial (no-AI) decision, final decision, AI advice shown, confidence (both stages),
  reaction times.
- **Trusting-novice index (frozen composite, standardized):** self-reported AI trust/deference (≥2 items),
  AI-literacy (reverse), domain familiarity (reverse); scoring + reverse-keys fixed here. Plus AI-use
  frequency, age band, minimal demographics.
- Debrief on the Dark deception.

## 6. Pre-logged panel predictions (generate + COMMIT before recruitment)
For the frozen item set, generate and commit — before any human data — each of the four ladder backends'
(gpt-4o-mini, gpt-4.1, gpt-4o, gpt-5.5) predictions: per-interface axis-2 adoption and per-persona /
per-index ordering. Reference synthetic anchors (beer): dark adoption ≈ 0.50 / 0.60 / 0.43 / 0.30; p5
(trusting-novice) dark adoption ≈ 1.0 for weaker backends vs ≈0.60 for gpt-5.5. These logged values are
the fixed comparison targets for H1–H3.

## 7. Analysis plan (frozen)
- **Human axis-2 DV:** conflict-conditioned adoption of the shown wrong AI on Dark vs Faithful/Placebo
  floors; recompute displayed_ai_advice = 1−ground_truth from ground_truth (the sign-inversion firewall).
- **H1:** paired test (Dark vs Faithful; Dark vs Placebo) on per-participant adoption; effect size + CI;
  item-level permutation.
- **H2:** mixed-effects logistic, adoption ∼ index × interface + (1|participant) + (1|item); report the
  high-vs-low-index Dark adoption gap with CI; robustness = raw novice/trusting subgroup.
- **H3:** for each backend, correlate its panel's per-interface and per-index predictions with the human
  pattern; report the model ranking + which (if any) is the best human-faithful screener.
- **Multiple comparisons:** Benjamini–Hochberg **within the pre-declared H1/H2/H3 family**; effect sizes
  and CIs throughout; per-interface reporting.
- **Deferred (declared):** axis-1 over-dispersion correspondence (needs a larger/richer sample) → full E6.

## 8. Integrity commitments (what we will and will NOT do)
- **No optional stopping.** N (and the floor→60 rule) is fixed before data; we do not peek-and-stop at
  significance.
- **No post-hoc exclusion or item-dropping to chase significance.** Exclusion rules are pre-specified:
  attention-check failure; median RT < 2 s or all-same-label (Bansal §4.4); incomplete blocks.
- **No p-hacking / garden of forking paths.** The analyses in §7 are the analyses; anything else is
  labelled exploratory.
- **No experimenter demand beyond the disclosed IV.** Instructions are **identical across the three
  interfaces**; the only difference between arms is the interface framing itself. Full debrief on the
  deception.
- **Blind-ish scoring / from-raw re-derivation**, mirroring the paper's audit spine.

## 9. What each outcome means (all honest, all publishable)
| Outcome | Meaning for the paper |
|---|---|
| **H1 + H2 hold** | Panel's axis-2 signal AND its at-risk-person localization are human-validated → a validated pre-deployment screen for *who* a coercive interface endangers. Strong result even without axis-1. |
| **H1 holds, H2 null** | Humans are coerced but not along the panel's persona axis → scope the claim to aggregate axis-2; drop persona-localization honestly. |
| **H3: gpt-4.1 > gpt-5.5 as human-faithful screener** | Direct human evidence that the *most-capable* panel model is the *least* faithful risk screener — headline for the silicon-sampling debate. |
| **H3: frontier tracks humans best** | The capability–vulnerability inversion does NOT transfer to humans → an important, honest bound; reframe coverage as a synthetic-only property. |
| **Any null** | A publishable bound on synthetic-panel predictive validity (the paper's honest-map framing). |

## 10. Freeze checklist (do all before data)
1. Pick domain (beer) + freeze the 3 interfaces and ~15 held-out conflict-eligible items.
2. Freeze the trusting-novice index composite + scoring.
3. Generate + COMMIT all four backends' per-interface / per-index predictions (§6).
4. A-priori power analysis (H1 primary, H2 secondary) → confirm N=40 or trigger floor→60.
5. Freeze §§1–7 with a UTC timestamp in `docs/DECISIONS.md`.
6. IRB/ethics approval (deception + debrief + fair treatment of volunteers).
7. Pilot the instrument on cheap non-precious people; fix comprehension/bugs; THEN spend the one-shot
   sample once.
