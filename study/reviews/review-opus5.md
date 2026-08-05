# Review: one-shot human validation (N=80, ~£250)

**Verdict: do not launch as built.** There are three launch-blockers that would burn the sample outright (no data capture, pre-checked survey defaults, a contaminated "dark" cell), plus one interpretive trap that could make the money actively *harmful* to the paper. Everything below is checked against the files.

---

## A. Fatal / must-fix before launch

**A1. [FATAL] The instrument saves no data.** `study/experiment/index.html:~450` — the only export path is `jsPsych.data.get().localSave(...)` gated on `DEBUG`. A real participant finishes and their data evaporates. `study/experiment/README.md` lists this as a TODO, but it is not a TODO, it is the whole study. Wire DataPipe→OSF (or any backend) with **per-trial** writes (not end-of-session), capture `PROLIFIC_PID/STUDY_ID/SESSION_ID` from the URL, and redirect to the completion URL. Verify end-to-end with 3 dummy runs before spending a penny.

**A2. [FATAL] Every individual-difference item is pre-answered.** `index.html` `likert(...)` renders `likert('def1',T('def1'),4)`, `def2`,`def3` → **default "Agree" (4)**; `skill1`,`selfconf` → default 3; `aiuse` → default index 3 ("Weekly"). The only item with no default is the attention check. So a satisficer submits the survey having actively answered *one* item, and their trusting-novice index = z(4,4,4) − z(3,3) = the same value for everyone who clicked through. This destroys E1's variance, injects an acquiescence artifact into the AI-deference scale, and makes the "index" partly a measure of who bothered to click. **Remove all `checked` defaults.** Same file: the comprehension check pre-selects the *correct* option (`${i===0?'checked':''}`) and is non-gating — `PREREGISTRATION.md` §7 claims "1 comprehension check". It currently checks nothing.

**A3. [FATAL] "Dark" is not the dark condition the paper needs anchoring.** In `index.html`, `DIRECTIVE_CONDS = ['dark']` and neutral/placebo get **no second-stage element at all**. So `dark − neutral` conflates (i) coercive framing text, (ii) the existence of a contingent pop-up, and (iii) an explicit instruction *"we recommend you switch to the AI's answer"*. That is three manipulations, and (iii) is an instruction, not an interface property. See §E for the recommendation. As built, H1 measures instruction compliance, not coercion.

**A4. [FATAL] The final-answer widget is asymmetric between agreers and disagreers.** `index.html` on `#submit1`: if `init === AIADVICE` the final radio is **pre-checked** with their answer; if they disagree, *both* radios are cleared and they must re-choose from scratch. Status quo is preserved for people who already agree with the wrong AI and removed for people who don't — a structural push toward adoption, applied to exactly the subgroup the DV is about. It is constant across conditions so H1 partly survives, but the **absolute adoption level is inflated**, which is the quantity E2 and the paper's Figure-5 placement depend on. Fix: same behaviour in both branches (recommend pre-fill the initial answer in both — that is what a real UI does).

**A5. [FATAL] Displayed AI confidence is confounded with framing, with random sign.** Checked the stimuli: neutral/placebo show the item's own confidence (`export_stimuli.py`: `conf if c != "dark" else DARK_CONF`), which ranges **53–98% (beer) / 53–90% (amzbook)**, while dark is fixed at 92%. So on one item dark is +38 points of stated confidence vs neutral; on another it is **−6**. The "framing" contrast is partly a randomly-signed confidence manipulation. Fix (one line in `export_stimuli.py`): hold displayed confidence at 92% in **all three** framings, so the only thing that varies is language. Then H2 (placebo) still isolates the explanation object.

**A6. [FATAL for the paper's payoff] E2 has no synthetic counterpart on these items.** `results/coercion_fewcluster.json` shows `n_item_clusters = 8`, `n_obs = 864` (8 items × 6 personas × 6 backends × 3 conds), and `scripts/analysis/coercion_fewcluster.py:45` builds the frame from `neutral_wrong_items` — items where the *real* AI was naturally wrong. The human study uses **12 different, ambiguity-selected items** (`export_stimuli.py::select_items`, target acc 0.70). There is no item-matched synthetic profile to correlate against, so E2 as written reduces to 3 condition-level points. **Before fielding, re-run the six backends × six personas on the exact 12-item × 3-framing human stimulus JSON.** This costs zero participants and is what turns the human number into a band on Figure~\ref{fig:flip} — the single highest-value output of the whole £250.

**A7. [FATAL interpretive trap] 12/12 guaranteed-wrong trials → within-session learning that the synthetic panel structurally cannot have.** Each synthetic trial is memoryless; a human who sees the AI blow 5 items in a row stops believing it. Adoption will decay with trial position, depressing the **human level** (not the contrast, which is interleaved). That biases the human point *downward* on Figure 5 — i.e. toward gpt-5.5's low 0.42 — and could manufacture apparent support for "the frontier backend is the most human-like," the exact opposite of the paper's capability–vulnerability inversion message. Mitigations, all free: **record trial position** (currently `idx` is used in `T('review_of')` but is *not* in the trial `data` object — add `position: idx`), preregister E2's headline level on **trials 1–4 only**, and report adoption by trial-third.

**A8. [FATAL] The manipulation-check gate is vacuous.** `PREREGISTRATION.md` §10 gate: "neutral-condition wrong-advice adoption ≥ 0.15". Mean human no-AI accuracy on the selected items is **0.772 (beer) / 0.748 (amzbook)** → ~24% of trials *start* on the wrong label and are essentially immovable. Neutral adoption will clear 0.15 even if the AI moves literally nobody. Replace with a gate on the **conflict-conditioned flip rate** (initial-correct → final-wrong) ≥ ~0.08 in neutral, plus a sanity band on initial accuracy (0.60–0.90). Also, pilot n≈12 gives ~36 conflict-conditioned neutral trials — the gate is coin-flip noisy; use n≈20 or treat it as a directional stop-rule only.

**A9. [FATAL for IRB] Instrument does not deliver what the protocol promises.** The instructions literally say *"There are no trick instructions — just give your best honest judgment each time."* while the dark condition then instructs them to switch — that is a false statement to participants, and a reviewer/IRB will read it as gratuitous deception. Also: `PREREGISTRATION.md` §11 and `HUMAN_STUDY_OVERVIEW.md` §11 promise "an option to withdraw data post-debrief" — **there is no withdraw button**; the debrief has no researcher/IRB contact, no data-retention statement, no mention of Prolific ID hashing. Fix all four before submission.

**A10. [FATAL for budget] The task is not 10 minutes.** Total review words: **1,136 (beer) / 1,273 (amzbook)**, median 95/108 words per review, max 133. Add ~450 words of dark panels, consent, two instruction screens, a 7-item survey, 24 decisions + 24 confidence ratings. Realistic median is **13–17 min**, not 10. At Prolific's £9/hr floor that is £1.95–£2.55/person; 92 × £2.10 × 1.33 fee ≈ **£257 before VAT on the fee**, and the n≈12 pilot adds ~£32 — you are over £250 with N=80. Decide now: (a) cut to 9 items (3/condition; power cost quantified in §C), (b) raise the budget to ~£320, or (c) accept N≈70. Do not discover this at launch and quietly underpay — Prolific flags it.

**A11. [HIGH→FATAL if unnoticed] The bilingual language selector.** Eligibility is "fluent English; US or UK" (`PREREGISTRATION.md` §5), yet the first screen offers 中文 while the **review text stays English**. Any participant choosing 中文 gets a Chinese-framed dark panel over an English review — an uncontrolled framing/comprehension nuisance in a 3-condition within-subject design with n=4 trials/cell. For the Prolific run, force `LANG='en'` and remove the selector (keep the zh path behind a URL flag for a future replication).

**A12. [HIGH] Prereg ↔ instrument drift on randomization.** §9 preregisters a **Latin square** for item→framing and **alternation** for domain. `index.html` does `shuffle([...4 neutral, 4 placebo, 4 dark])` assigned by position, and `DOMAIN = Math.random() < 0.5 ? ...` per session. Random domain assignment at N=80 has SD ≈ 4.5 → a 32/48 split is unremarkable and would gut one domain's secondary estimate. Implement balanced domain assignment (server-side counter or Prolific-side two-study split) and either implement the Latin square or amend §9 to "random within-participant balanced assignment".

**A13. [HIGH] Beer POSITIVE items are dead weight and confounded with label.** `stimuli_preview.md`: beer POSITIVE items sit at 0.63, **0.88, 0.88, 0.90, 0.91, 0.93**; all six NEGATIVE items are 0.58–0.81. So in beer, "AI shows POSITIVE" ⟺ movable and "AI shows NEGATIVE" ⟺ floored — direction of the wrong advice is perfectly confounded with difficulty, and sentiment tasks have a known positivity bias. That is ~5 of 12 beer items contributing near-zero information. `select_items` already picks nearest-to-0.70, so the dataset has nothing better. Options: relax the 6/6 label balance for beer to 8 NEG/4 POS (item random effect absorbs it; disclose), or reallocate the sample toward amzbook (spread 0.57–0.85). Also **block condition assignment within difficulty tercile** rather than pure shuffle — free variance reduction.

**A14. [HIGH] Exclusion rules don't match the instrument.** "> 20% missing trials" is impossible (the UI forces completion) — drop it. "< 4 min" is ~20 s/trial *including reading a 100-word review* — far too lenient; preregister a trial-level RT floor instead (e.g. flag participants whose median `rt_initial` < 8 s, or whose `rt_final` < 2 s on >50% of trials). The attention check exists but nothing computes it — write the exclusion code now and run it on simulated data.

---

## B. High-value additions that cost ≈0 participant time

| # | Add | Why it's worth it |
|---|---|---|
| **B1** | **`position: idx`, `displayed_conf`, and `initial_correct` in the trial `data` object** (`index.html` trial `data:{...}` currently lacks all three) | Without position you cannot run A7's learning analysis at all. Zero seconds. |
| **B2** | **Use the initial judgments you already collect as a second human anchor.** | You are collecting 80 humans × 12 items of **pre-advice, no-AI** judgments on the exact Bansal items. That (a) validates the movable-band selection in your own sample rather than borrowing Bansal's accuracies, and (b) lets you compute **axis-1 between-*user* reliance over-dispersion** (`main.tex` §Axis-1's $D$, with P=80 humans instead of P=6 personas) on the *same* items and the *same* 3 conditions. Today the paper's axis-1 human anchor is borrowed from Bansal, is $n=5$ conditions, null under BH, and **degenerate on amzbook** (`main.tex:984–988`). This gives you an own-sample anchor for free. Add as **E4** in the prereg. This is the biggest free win in the study. |
| **B3** | **Post-task suspicion probe (~20 s):** "Out of the 12 items, on how many do you think the AI was correct?" + "Did you notice anything unusual about the AI?" (free text) | Directly measures A7's learning artifact, gives a preregistered sensitivity analysis (exclude/segment the suspicious), and is a defensible answer to the reviewer question "didn't they figure it out?" |
| **B4** | **Perceived-coercion manipulation check (~30 s):** after debrief-consent but before debrief text, show the three panels side by side, ask "which felt most pressuring?" (forced choice) + 1 Likert "how much pressure did you feel from the AI messages?" | Without this, an H1 null is uninterpretable (failed manipulation vs. real null). `HUMAN_STUDY_OVERVIEW.md` §10 claims "H1 null is a valuable negative" — it only is if you can show the dark framing *was perceived* as coercive. |
| **B5** | **Preregister confidence change as a secondary confirmatory DV** (`conf_change ~ condition`, LMM) | Continuous/ordinal, so far better powered than a 0.30-base binary with 4 trials/cell. It rescues the study if H1 is null: "coercion moved confidence even when it didn't move the decision" is a real, publishable finding on the same axis. **Requires fixing B6.** |
| **B6** | **Fix the confidence asymmetry.** `confI` is pre-set to `data-val="3"`; `confF` is reset to 0 and *required* ≥1 | Non-clickers get initial=3 by default and a deliberate final → `conf_change` is systematically biased. Make both require an active click (or both default). |
| **B7** | **Second attention check mid-task** (e.g. an instructed-response line inside trial 7) | One pre-task check cannot detect drop-off during the 12 trials. ~5 s. |
| **B8** | **A real "withdraw my data" button on the debrief** | Costs nothing, closes the IRB gap in A9, and is already promised in both study docs. |
| **B9** | **One-line free text on a single random trial:** "In one sentence, why did you keep / change your answer?" | Qualitative colour for the paper at ~15 s total; also a bot/LLM-farm detector. |
| **B10** | **Log `screen_width`, device, and Prolific demographics** (free from Prolific export) | Zero participant time; supports the "desktop only" eligibility claim and a robustness slice. |

---

## C. Power & analysis

**C1. The published power table is optimistic because `power_sim.py` simulates the wrong generative process.** It draws `adopt ~ Bernoulli(p_cond)` directly, with no two-stage structure. In reality, mean human no-AI accuracy on the selected items is 0.772/0.748 → **~24% of trials begin already agreeing with the wrong AI** and are near-immovable, so a large condition-invariant mass sits inside the DV and attenuates the odds ratio.

I re-ran the power analysis with a realistic two-stage generator (initial judgment ~ item accuracy + subject ability; if initially wrong, adopt with p=0.95; if initially correct, flip with a condition-dependent rate; subject+item random effects; subject-cluster-robust logistic, one-sided α=.05, 250 sims, N=80):

| scenario (conflict-conditioned flip, neutral→dark) | implied unconditional | implied OR | power, **unconditional** DV | power, **conflict-conditioned** DV |
|---|---|---|---|---|
| 0.095 → 0.13 (small) | 0.30 → 0.33 | 1.13 | 0.22 | 0.38 |
| 0.095 → 0.16 (moderate) | 0.30 → 0.35 | 1.25 | **0.46** | **0.71** |
| 0.095 → 0.22 (strong) | 0.30 → 0.40 | 1.52 | 0.84 | 0.96 |
| 0.095 → 0.29 (directive-sized) | 0.30 → 0.45 | **1.90** | 0.98 | 1.00 |

Read this carefully: **the prereg's headline "0.97 power for OR≈1.9" requires the conflict-conditioned flip rate to *triple* (0.095→0.29).** A static dark panel plausibly does not do that; the *agreement-contingent directive* is what would. In other words, the current N=80 justification is silently leaning on the very manipulation that §E says you should remove. Be honest about that in the prereg.

**C2. Switch the primary DV to the conflict-conditioned (initial-correct) subset.** It buys 15–25 power points at every effect size, for free. Crucially, **this is not conditioning on a post-treatment variable**: the framing is revealed only *after* `#submit1` (`index.html` stage-2 is hidden until the initial answer is locked and disabled), so initial correctness is strictly pre-treatment — no collider bias. It also matches the quantity the paper actually reports as the mechanism (`main.tex:484`, "conflict-conditioned switch-to-wrong: beer gpt-4.1 $0.19\to0.51$"). Keep the unconditional adoption model as a **scale-matched co-primary** (it is what `coercion_fewcluster.py:49` computes for OR 1.90), Holm-adjusted across the two.

**C3. Model spec.** `adopt ~ condition + (1|participant) + (1|item)` is right, with two additions: (i) enter **domain** and **trial position** as covariates (position is the A7 control); (ii) with only 12 items per domain the item random intercept is estimated from few clusters — preregister the fallback ladder explicitly (GLMM → subject-clustered logistic with item fixed effects → item-cluster bootstrap), i.e. exactly the ladder you already built in `coercion_fewcluster.py`. Note the power sim ignores item clustering entirely; since condition is randomized within participant and orthogonal to item, this is roughly fine, but say so.

**C4. Item budget.** Dropping to 9 items (3/condition; also what a 4th condition on 12 items costs you) reduces power from 0.46→0.34 (unconditional) and 0.71→0.56 (conflict-conditioned) at the moderate effect. Given A10's timing problem, this is the real trade-off to price.

**C5. Honest N framing.** At N=80 you are powered for a *large* effect and roughly coin-flip for a moderate one. N sensitivity (moderate scenario, conflict-conditioned DV): N=80 → 0.68, N=100 → 0.80, N=120 → 0.86, N=150 → 0.91. If the budget is hard-capped, **say in the prereg that the study is powered to detect OR ≥ ~1.5 and that a null is a bound, not evidence of absence** — do not repeat the "0.97" headline unqualified.

**C6. One-sided test:** defensible (a strong directional prior from the synthetic result + the literature) and preregistered. Keep it, but preregister that a *significant negative* effect will be reported descriptively with its CI.

**C7. H2 is not confirmatory as written.** "placebo ≈ neutral" is a null-accept dressed up. Either (a) reframe H2's confirmatory part as **dark > placebo** only (one-sided), with placebo−neutral reported as an estimate + CI (which is what §10 actually says), or (b) preregister a **TOST** with an explicit margin (e.g. OR ∈ [0.67, 1.5]) and state honestly that N=80 is under-powered for equivalence at that margin. Do not let §3's "Confirmatory" label cover an untested equivalence claim.

**C8. E1 is not powered and should stop pretending.** A cross-level interaction (continuous index × condition) at N=80 with 4 trials/cell needs several times the sample. `PREREGISTRATION.md` §3 and `HUMAN_STUDY_OVERVIEW.md` §5 already say "exploratory/suggestive" — go further: preregister E1 as **estimation-only** (report the standardized OR + CI, no p-value, no "supported/not supported" language). Otherwise a reviewer reads a null E1 as evidence against the paper's most stable persona result.

**E2/E3:** E3 (flip) is fine — it becomes the primary under C2. E2 is blocked on A6 and A7; with those fixed it is a genuinely good descriptive figure.

---

## D. Paper alignment

**D1. §8 says N≈40; the plan is N=80.** `main.tex:887`: "within-subjects, $N\approx 40$, Prolific". One-line factual edit. `HUMAN_STUDY_OVERVIEW.md` §15 already flags it and it is still unapplied.

**D2. §8 mis-describes the baseline.** `main.tex:888` says the study tests coercion "relative to a **faithful**/placebo baseline". It does not — the human neutral condition shows a **guaranteed-wrong** label (`export_stimuli.py`: `wrong = 1 - gt`, used for all three framings). Change to "relative to matched neutral (same wrong label, non-coercive) and placebo baselines". A reviewer who reads both documents will catch this.

**D3. §8 over-promises E2.** `main.tex:889`: "and **which backend or aggregation rule best approximates the human pattern**". `PREREGISTRATION.md` §3 explicitly refuses that claim ("we do not claim any backend is 'most human-faithful'; we report correspondence, not validation"). The paper's own §7 limitation (`main.tex:799`) says the claim "requires the human study we have not run". Weaken §8 to "how the human adoption level sits relative to the backend distribution (descriptive)". Otherwise you preregister a refusal and advertise the claim.

**D4. What the study actually buys the paper — and the one thing it must produce.** The study cannot speak to backend *sensitivity* (contributions 1 and 3); it produces one human number. Its value is concentrated in two deliverables: (i) a human coercion OR placed next to the synthetic pooled OR 1.90/1.17 — which requires the confidence fix (A5) and a construct-matched dark (§E); and (ii) **a human adoption band drawn on Figure~\ref{fig:flip}'s 0.12–0.62 backend range** — which requires the item-matched synthetic re-run (A6) and the position-controlled level (A7). Deliverable (ii) is what lets §6's capability–vulnerability inversion say "and the frontier backend under-shoots *humans*, not just its peers". Without A6+A7 you will have paid £250 for a number that cannot legally be put on that axis.

**D5. Abstract sync.** `main.tex:~68` — "that validation is a separate, later study" — needs revising on completion, and the abstract's "we do not claim the panel predicts individual humans" must survive intact (the study does not license dropping it).

**D6. One reconcilable-but-must-disclose mismatch.** The synthetic contrast rests on **8 naturally-wrong items** (`coercion_fewcluster.json: n_item_clusters = 8`) with the real AI's confidence; the human study uses **12 ambiguity-selected items** with forced-wrong advice. Even after A6, the human and synthetic estimands differ in item sampling. Say so in one sentence in both §8 and the prereg; don't let it be discovered.

---

## E. The agreement-contingent directive — recommendation

**It hurts more than it helps in its current form. Do not ship it as part of `dark`.**

Four specific reasons, beyond A3:

1. **Construct drift.** The synthetic dark (`main.tex:387`) is a *static textual interface framing*: negated ground truth + high confidence + authority/accountability. The directive is a **live, response-contingent instruction** (`dir_warn`: "we recommend you **switch to the AI's answer**"). That is persuasion/instruction-following, adjacent to demand characteristics — a different construct from an interface dark pattern. The entire point of reusing "the same three framings so human and synthetic measurements are on the same scale" (`PREREGISTRATION.md` §2) is defeated by adding a fourth cue to only one cell.

2. **The manipulation is structurally asymmetric and item-dependent.** The `agree` branch congratulates people who *already* adopt the wrong label — it cannot raise the binary DV at all (they're at ceiling), it can only move confidence. So the entire dark effect on adoption comes from the `warn` branch, and the dark cell's effect size is mechanically diluted by the already-agree rate, which is set by item difficulty (~24% here). Your human OR then depends on your item mix in a way the synthetic OR does not. It is not comparable by construction.

3. **It will overshoot and break the anchor.** Compliance with an explicit switch instruction is high. My simulation shows exactly this: reproducing the prereg's headline "OR 1.90, power 0.97" requires the flip rate to triple — a directive-sized effect. You would then report a human OR well above 1.90 and place a human level above every backend, and the honest reading would be "we measured obedience to an instruction, not the interface". E2 dies.

4. **Collateral damage.** It corrupts the confidence DV in the dark cell (you *told* them to raise/lower confidence — B5 becomes unusable there); it makes the instruction text *"There are no trick instructions"* a falsehood (A9); and it raises the deception burden at IRB for no confirmatory gain.

**Recommended resolution (in priority order):**

- **Best (if you can afford ~13 min / 15 items):** confirmatory design stays 4 neutral / 4 placebo / 4 **dark-static** (identical to the synthetic dark, no pop-up in any cell) in randomized order; then append **3 `dark+directive` trials as a fixed end-block** on 3 additional movable items, analyzed as a **separate exploratory escalation**. You get a clean anchor *and* a dose–response result (neutral < dark < dark+directive) that is genuinely new and quotable, without contaminating H1. Order is confounded with the block — fine for an exploratory arm, and say so.
- **Fallback (budget-tight, 12 items):** drop the directive entirely. Preregister the conflict-conditioned DV as primary (C2) so N=80 remains defensible (power 0.71 at a moderate plain-dark effect), and note the directive as the planned follow-up.
- **If you insist on keeping it in the confirmatory design:** then it must be **matched across all three conditions** — every cell gets an agreement-contingent echo, differing only in wording (neutral: *"Your answer differs from the AI's recommendation."*; placebo: same + the content-free blurb; dark: the current coercive text). That restores a single-factor contrast and keeps the extra potency. But note the absolute adoption level is then inflated relative to the synthetic panel, so E2's Figure-5 placement must be reported with an explicit caveat — and A3's "dark ≠ synthetic dark" objection is only half-answered.
- **Do not** ship the current configuration (directive in dark only, nothing in neutral/placebo). It is the single most likely reason a CHI reviewer rejects the human study.

---

## F. Ranked TODO

**Before anything else (instrument correctness — a bug here voids the whole spend)**
1. `[fatal]` Wire per-trial server-side data capture (DataPipe/OSF) + Prolific PID capture + completion redirect; verify with 3 dummy runs. *(A1)*
2. `[fatal]` Remove every pre-checked default in the pre-survey and the comprehension check; make the comprehension check gating (or drop the claim from prereg §7). *(A2)*
3. `[fatal]` Make the final-answer widget symmetric for agreers and disagreers. *(A4)*
4. `[fatal]` Make `confI` require an active click, matching `confF`. *(B6)*
5. `[fatal]` Restructure the directive: dark-static confirmatory + directive as separate escalation arm (or matched echo in all three cells). *(§E, A3)*
6. `[fatal]` Force `LANG='en'` and remove the language selector for the Prolific run. *(A11)*
7. `[high]` Add `position`, `displayed_conf`, `initial_correct` to the trial data object. *(B1)*
8. `[high]` Balanced domain assignment (not `Math.random()`); implement the Latin square or amend prereg §9. *(A12)*

**Stimuli**
9. `[fatal]` Fix displayed confidence at 92% across all three framings in `export_stimuli.py`; regenerate JSON + `stimuli.js` (bump `?v=`). *(A5)*
10. `[fatal]` Re-run the six backends × six personas on the exact regenerated 12-item × 3-framing stimulus set; store as the E2 comparison table. *(A6)*
11. `[high]` Resolve the beer POSITIVE dead weight: 8 NEG/4 POS for beer, or reweight the sample toward amzbook; block condition assignment within difficulty tercile. *(A13)*
12. `[high]` Verify label semantics (1 = POSITIVE) against the Bansal codebook — still an open TODO in three files.

**Protocol / prereg (before OSF timestamp)**
13. `[fatal]` Primary DV → conflict-conditioned switch-to-wrong (initial-correct subset); unconditional adoption as Holm-adjusted co-primary; state the pre-treatment argument explicitly. *(C2)*
14. `[fatal]` Replace the manipulation-check gate with a conflict-conditioned flip-rate gate; raise pilot to n≈20 or downgrade the gate to a stop-rule. *(A8)*
15. `[fatal]` Rewrite the power section with the two-stage simulation; delete the unqualified "0.97"; state the detectable-effect floor (OR ≈ 1.5). *(C1, C5)*
16. `[fatal]` Preregister the position/learning analysis and E2-on-trials-1–4. *(A7)*
17. `[high]` Reframe H2 (dark > placebo confirmatory; placebo−neutral as estimation or an explicit TOST margin). *(C7)*
18. `[high]` Downgrade E1 to estimation-only. *(C8)*
19. `[high]` Add **E4: own-sample axis-1 human anchor** from the pre-advice judgments. *(B2)*
20. `[high]` Rewrite exclusions to match the instrument (drop "missing trials", add trial-level RT floors, write and test the exclusion script on simulated data). *(A14)*

**Ethics / ops**
21. `[fatal]` Delete "There are no trick instructions"; add IRB/researcher contact, data-retention statement, and a working **withdraw-my-data** button to the debrief. *(A9, B8)*
22. `[fatal]` Re-time the study honestly in the pilot; then pick one of {9 items, +£70 budget, N≈70} and lock it. *(A10, C4)*
23. `[high]` Add the suspicion probe and the perceived-coercion manipulation check. *(B3, B4)*
24. `[high]` Preregister `conf_change` as the secondary confirmatory DV. *(B5)*
25. `[nice]` Second mid-task attention check; one-line free-text "why did you change/keep?"; log device/screen. *(B7, B9, B10)*

**Paper edits (do now, they're one-liners)**
26. `[high]` `main.tex:887` N≈40 → N≈80. *(D1)*
27. `[high]` `main.tex:888` "faithful/placebo baseline" → "matched neutral (same wrong label) and placebo baselines". *(D2)*
28. `[high]` `main.tex:889` weaken "which backend best approximates the human pattern" to descriptive correspondence. *(D3)*
29. `[nice]` Add one sentence in §8 disclosing the 8-item-vs-12-item estimand difference. *(D6)*

**Do not launch until 1–6, 9–10, 13–16, and 21–22 are done and a 3-person internal dry run produces a complete, correctly-coded data file.**
