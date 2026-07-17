# SOTA idea + top-venue viability assessment (independent subagent)

> Produced by an independent `idea-eval-sota` research subagent on 2026-07-17, at PI request.
> This is an ASSESSMENT/record, not a design change. Any framing pivot it motivates is logged
> separately in `docs/DECISIONS.md` once approved by the PI.

---

# Brutally Honest Assessment: "Two Ways a Design Fails" (as of 2026-07-17)

---

## 0. State of the Evidence (Ground Truth Before Verdict)

Let me be completely precise about what **actually exists** vs what is pending:

| Claim | Status | Evidence |
|---|---|---|
| Human over-dispersion is real (ρ=0.067) | **✅ Confirmed, published** | Bansal CHI'21 dataset, verified estimator |
| Panel redesign produces heterogeneity | **✅ Confirmed, preliminary** | gpt-4.1-mini, 6 personas, 20 beer items, old renderer |
| Axis-2 wrong-AI over-reliance (0.69, p=0.0098) | **✅ Significant but underpowered** | 42 truly-wrong trials, 1 model, 1 domain, preliminary run |
| Axis-1 confirmatory H1a (N=20 per model) | **❌ NOT RUN** | Preregistered; power-N hinted weak/null |
| Panel↔human correspondence (Spearman, 5 pts) | **❌ NOT RUN** | Code built; "likely weak" per D5.11 |
| Powered axis-2 (D5.13, clean 1−gt, multi-model) | **❌ NOT RUN** | Preregistered |
| Cross-generation robustness (gpt-5.x, D5.15) | **❌ NOT RUN** | Awaiting Azure creds |
| Human validation study (E6, N≈60) | **❌ NOT DESIGNED/RUN** | Deferred to "last"; no IRB |

The paper has a preregistered design, a real bug caught and fixed, honest negative results, and one significant preliminary result. **Nothing that would currently constitute a complete paper has landed.** The PI is building a rigorous pipeline and positioning for future results. That matters for the assessment.

---

## 1. Novelty Verdict

### Core idea: genuinely novel in the specific combination

The exact framing — **a calibrated multi-LLM panel producing a dual-axis triage signal (over-dispersion + wrong-AI convergence), validated against real human reliance logs, with preregistered thresholds and an explicit abstention rule, specifically for pre-deployment screening of human-AI decision interfaces** — has no direct prior art. I verified this across multiple searches.

**Closest prior art and exact deltas:**

**[1] Rastogi, Liu, Hullman (EAAMO 2022 / HCOMP 2023)** — The most methodologically adjacent work. Proposes an offline evaluation framework for optimizing human-ML task routing using historical data. **Delta:** Rastogi optimizes who does *a given task* (human vs. AI), taking the interface as fixed. This paper triages whether *an interface design* needs a human study. The DVs, goals, and methods are entirely different. Not prior art.

**[2] Park et al. UIST 2023, Argyle et al. Political Analysis 2023, Aher et al. 2023** — Silicon sampling / generative agents. Establish that LLMs can simulate aggregate opinion/behavioral distributions. **Delta:** None of these (a) focus on human-AI decision interfaces, (b) use reliance variance/over-dispersion as the DV, (c) propose a triage with calibrated thresholds, or (d) frame the problem as pre-deployment safety screening. Pure simulation, no safety-triage framing.

**[3] Seshadri et al. ICLR 2026 ("Lost in Simulation")** — The most damaging challenge paper, not prior art per se. Shows LLM-simulated users are unreliable proxies in *agentic* retail tasks (±9pp across user-LLM choice, demographic disparities). **Delta:** Seshadri's domain is agentic task evaluation; this paper's domain is binary AI-advice reliance. More importantly, Seshadri is an *attack* on the validity of LLM simulation that this paper must directly rebut — and the framing ("triage, not prediction") is the intended rebuttal. But Seshadri does NOT specifically pre-empt the over-dispersion-as-DV + triage framing.

**[4] Buçinca et al. CSCW 2021, Schemmer et al. IUI 2023** — Document that over-reliance is heterogeneous across users (Need for Cognition, user×intervention). **Delta:** These papers observe heterogeneity as a *nuisance covariate*; this paper proposes operationalizing it as the *primary safety DV* for screening. That flip is the genuine methodological contribution.

**[5] "Measuring and mitigating overreliance" (arXiv 2509.08010, 2025)** — Appeared in fresh search; a review/position paper on overreliance. **Delta:** It's a literature review / call to action, not a computational triage methodology.

**[6] Nature Medicine 2024 (radiologist heterogeneity study)** — Documents heterogeneous AI assistance effects in radiology. **Delta:** observational; no synthetic panel or triage protocol; different domain entirely.

**[7] Dark Patterns Meet GUI Agents (arXiv 2509.10723, 2025); Siren Song of LLMs (2509.10830, 2025)** — New 2025 work on dark patterns in AI. **Delta:** Both are empirical human-subject studies of *how users respond* to dark patterns, not pre-deployment computational detection. No LLM panel, no triage protocol.

**Novelty verdict: GENUINE, but narrow.** The specific combination is novel. The component pieces (silicon sampling, over-reliance literature, dark patterns) are not new. The synthesis — calibrated panel + over-dispersion DV + dual-axis triage + abstention rule — is original. However, the novelty is primarily a *framing and protocol proposal*, not (yet) a validated empirical finding. A CHI/FAccT reviewer will acknowledge the novelty of framing, then immediately ask: "Does it actually work?"

---

## 2. Top-Venue Viability: Objective Assessment

**Bottom line: As it stands (July 2026), this paper is NOT ready for a CHI/FAccT/CSCW full paper submission. Realistic acceptance probability at a top venue with the current evidence: ≤10–15%.** With the confirmatory + powered axis-2 results in hand, that rises to ~25–35% — still below the bar without E6. With E6, it becomes a legitimate ~50–60% full paper.

Here is the honest breakdown:

### What would reviewers actually say

**Reviewer 1 (likely CHI AC with methods background):** "This is an interesting methodological proposal. However, the central claim — that the panel's axis-1 disagreement predicts human reliance over-dispersion — is not empirically demonstrated. The Spearman correlation is computed over 5 conditions (n=5 data points), which has essentially no statistical power to distinguish from noise. The confirmatory run is pending, and the authors acknowledge it may be null or weak. The axis-2 result is significant but based on 42 trials from a single model on beer reviews. Without E6, I cannot evaluate whether this triage system actually triages anything correctly. **REJECT** (revise and resubmit after E6)."

**Reviewer 2 (likely FAccT reviewer focused on accountability):** "The framing is compelling — over-dispersion as a safety DV, dark pattern detection. But the single domain (beer), single vendor (OpenAI family), no human validation, and the panel-only nature of all results makes this a tool proposal, not a validated tool. Per Seshadri et al. (ICLR 2026), LLM simulations are demonstrably unreliable proxies. The authors' rebuttal ('triage, not prediction') is intellectually valid but untested. **REJECT** (interesting; submit after human validation)."

**Reviewer 3 (likely CSCW methods/empirical):** "Where are the humans? This paper studies how LLMs simulate human reliance decisions as a proxy for studying human reliance decisions. But the panel↔human correspondence is the entire load-bearing claim, and it's not established. The calibration on Bansal/Lu&Yin is not a validation — it's training data. **REJECT**."

### Single biggest rejection risk

**The load-bearing claim is unvalidated.** The paper's thesis is: "A calibrated LLM panel can triage interfaces before a human study." This requires showing that when the panel flags a design as risky, it actually IS risky for real humans. Currently, *there is no such evidence.* 

- The 5-condition Spearman (panel vs. human over-dispersion) is statistically trivial (5 points). Even a strong result here — Spearman ρ = 0.9, p = 0.04 — wouldn't persuade reviewers because n=5.
- The "calibration" on Bansal/Lu&Yin uses real human data to set up the panel, but doesn't show the panel generalizes to *new interfaces*.
- E6 is the only thing that answers this, and it's deferred.

The PI's framing defense ("triage not prediction") is logically correct but empirically undefended. A reviewer can acknowledge the logical distinction and still say "you haven't shown the triage is better than chance on new interfaces."

### Additional specific liabilities
- **N=5 conditions for the axis-1 correspondence** is the paper's Achilles heel. Five conditions is not enough to fit a Spearman ρ at CHI standards. This is known and partially addressed by the D5.14 stratified correspondence, but that's exploratory.
- **Axis-2 underpowered** (42 truly-wrong trials, 1 model, beer only): significant at p=0.0098 but the powered run hasn't landed.
- **OpenAI-only confirmatory**: the reviewer will immediately ask "maybe this is an artifact of GPT's training." Cross-vendor is planned but not done.
- **Single domain (beer)**: The method's applicability to real HCI design decisions is unclear. Beer review sentiment is about as artificial as it gets.
- **The C0 demotion** is the right call (honest) but it removes one of the paper's two anchor results, leaving the thin axis-2-only story even thinner.

---

## 3. Strongest Framing Given Current Evidence

The strongest defensible framing right now — one that doesn't overclaim — is:

> **"Operationalizing Over-Dispersion and Wrong-AI Convergence as Pre-Deployment Safety Signals: A Calibrated Synthetic Panel Protocol for Human-AI Decision Interfaces"**

This framing:
1. **Leads with the protocol** (not the empirical result), which is the most solid contribution
2. **Names the two signals** (not "triage" which implies the triage has been validated)  
3. **Does not claim prediction** — it claims a new DV operationalization and a protocol
4. Can honestly report: "preliminary evidence of axis-2 significance (0.69, p=0.0098, underpowered); axis-1 confirmed [or: found weak/null — report honestly]; panel↔human correspondence pending; human validation design (E6) specified and preregistered"
5. Positions the human ρ=0.067 on real data as "the magnitude of the target signal the protocol is designed to detect, motivating the calibrated threshold"

**What NOT to frame as:**
- Do NOT frame as "validated pre-deployment triage" — it isn't validated
- Do NOT frame axis-1 as a confirmed finding until the confirmatory lands
- Do NOT frame as "the panel predicts humans" — this is factually unsupported

The secondary value prop — the **process rigor story** (preregistration, caught bug, blind analysis) — is genuinely differentiating for a methods venue and should be front-loaded, not buried in a footnote. It converts a "we propose a method" paper into "here is how to do LLM-panel research responsibly."

---

## 4. Concrete, Prioritized Suggestions (Ranked by Impact/Effort)

### P1 — Run the powered axis-2 (D5.13) IMMEDIATELY [HIGH impact, LOW cost, ~$15-45]
**The confirmatory axis-2 (N=20 × 2 models × 4 conditions, clean `1-ground_truth`) is the paper's best shot at a strong empirical claim.** The preliminary result (0.69, p<0.01) on underpowered n=42 is the strongest evidence in the paper. Getting this on a powered, preregistered, clean, two-model run would produce a result that stands up: "a calibrated LLM panel reliably flags coercive wrong-AI designs; this signal is robust across GPT-4o and GPT-4.1-mini." 

Even if axis-1 is weak/null, a powered axis-2 + the methodological contribution is a credible FAccT paper (dark pattern detection + accountability framing). Without it, axis-2 is a "trend" not a finding. **Run this first.**

### P2 — Run the confirmatory axis-1 (D5.11) and report honestly [MUST DO, ~$0 free tier]
The confirmatory has to run and be reported regardless. If it's weak/null, the paper *shrinks* to "we propose a two-axis protocol; axis-2 is empirically validated; axis-1 is harder to detect and requires larger N / richer task diversity." That's a legitimate honest result. The temptation to not run it (or to quietly reframe before running) would be scientifically dishonest and would prevent the paper from existing at all.

**Important:** The power-N suggesting N=20 is barely powered means the axis-1 confirmatory has low sensitivity. The result will almost certainly be: "axis-1 detects a weak signal in the expected direction but does not reach significance at our alpha with this N and domain." The paper should preemptively frame this: "the small human ρ=0.067 is a difficult target requiring large N or task diversity; a single-domain panel at N=20 is probably underpowered; we report the result as a rigorous lower-bound on effect size."

### P3 — Add amzbook domain (axis-1 and axis-2) [HIGH impact for cost, ~$30-60, days not weeks]
**"Single domain (beer)"** will be on every rejection form. amzbook is binary sentiment, uses the same Bansal pipeline, costs one more panel run. It directly answers A5 and adds more correspondence points (A3). If axis-1 is beer-null but amzbook-significant (or vice versa), that's a domain-dependence finding worth reporting. If both are null, you report the boundary honestly. Do this before submission.

### P4 — Build the difficulty-stratified correspondence harness and run it [COMPUTE-FREE on existing data]
D5.14 is already built. When the confirmatory lands, immediately compute condition × difficulty-stratum correspondence (gives ~10-15 points instead of 5). This doesn't require new LLM calls — it runs on the confirmatory output. It's the cheapest way to upgrade the statistical power of the cross-condition validation and directly answers reviewer A3 ("you can't do statistics on 5 points").

### P5 — Cross-vendor arm (gpt-5.x via Azure, D5.15) [HIGH impact for credibility, ~$100-200, days]
The single-vendor limitation is a credibility ceiling. The planned gpt-5.x robustness arm directly answers the strongest reviewer attack (A2: "this is just GPT's priors"). If the signal holds on gpt-5.2/5.4, you have cross-generation evidence. If it collapses, that's a publishable finding about model-capability sensitivity. The PI should provision Azure credentials and run this before submission. The concern about frontier-model ceiling on beer (near-perfect System-1 → few conflicts) is real and pre-registered — report it honestly if it happens.

### P6 — Run E6 [EXPENSIVE but the only thing that fully validates the method; ~$5-10k for N=60 Prolific + IRB time]
This is the single highest-impact change but also the most expensive and time-gated (IRB, platform setup, 6+ weeks realistic). The paper currently cannot claim the panel "triages" interfaces without E6. With E6:
- If axis-2 predicts humans: you have a validated dark-pattern detector. This is CHI full paper.
- If axis-1 also predicts: you have the full two-axis validated triage. That's CHI Best Paper territory.
- If E6 is null: you have a cautionary result ("synthetic panels fail to predict human reliance heterogeneity") which is itself publishable and important.

**Recommendation on E6:** Don't defer it indefinitely. The axis-2 result is already strong enough to design a tight E6 around axis-2 only (N≈40, within-subjects, 2 conditions: faithful vs. wrong-AI-GT) as a fast-tracked test. This is much cheaper than the full 6-interface design. A focused E6 would let you submit a "validated axis-2 + proposed axis-1 protocol" paper to CHI/FAccT.

---

## 5. Venue Recommendation

### Current state (no new runs done, as of 2026-07-17):

**HCOMP 2026** — The best immediate fit. HCOMP specifically welcomes work on human computation, algorithmic evaluation, and using computational methods for human-centered evaluation. A methods paper with one significant result (axis-2) + a rigorous protocol + honest negative findings + preregistration is strong for HCOMP. The silicon-sampling critique literature is directly relevant. **Realistic acceptance ~50%.** Verdict: submit here while running experiments.

**CHI 2027 LBW** — If the confirmatory axis-1 + powered axis-2 land before the LBW deadline (typically early August for LBW), a 4-page LBW with both results would generate productive feedback from the CHI community. The "work in progress with a deferred human study" framing is exactly what LBW is designed for.

**FAccT 2027 (full paper)** — With powered axis-2 + amzbook + cross-vendor arm, but still without E6: **realistic acceptance ~25-35%**. FAccT accepts computational methodology papers without human validation more than CHI does, IF the accountability framing is crisp (dark pattern detection as an accountability tool). The axis-2 "uniformly lethal design detector" story is exactly FAccT's register. Position this as "a computational auditing tool for detecting coercive AI-advice interfaces" — axis-2 is the anchor, axis-1 is the boundary.

**CHI 2027 (full paper, Methods track)** — With powered axis-2 + confirmatory axis-1 (regardless of outcome) + amzbook + cross-vendor + E6: **realistic acceptance ~50-60%**. Without E6, ~20-25%. CHI Methods papers have gotten through without full human validation of a proposed method, but they need a compelling protocol + honest evaluation + preliminary evidence. The five-condition n=5 Spearman is the bottleneck; the stratified correspondence helps but doesn't substitute.

**CSCW 2027** — CSCW is currently the *least* favorable for this paper in its current form because CSCW reviewers strongly prefer human-centered empirical work. Without E6, expect rejection. After E6, CSCW becomes viable.

### My concrete recommendation:
1. **Now:** Run D5.13 (powered axis-2) + D5.11 (confirmatory axis-1) + amzbook. Takes 1-2 weeks compute, days of analysis.
2. **August 2026:** Submit a tight HCOMP paper (axis-2 + methodology + honest bounds on axis-1). Get community feedback.
3. **Parallel:** Scope a fast E6 (axis-2 only, N=40, Prolific, 6-week turnaround). IRB submission now.
4. **Spring 2027:** Submit CHI/FAccT full paper with powered axis-2 + confirmatory axis-1 + E6 (even axis-2-only version).

---

## 6. Summary Table: Genuinely Novel vs. Empirically Unvalidated

| Claim | Novel? | Validated? | Honest label |
|---|---|---|---|
| Over-dispersion as safety DV (framing) | ✅ Yes | N/A (definitional) | **Genuine conceptual contribution** |
| Dual-axis triage protocol (design) | ✅ Yes | ❌ Not yet | **Protocol proposal, unvalidated** |
| Real human over-dispersion exists (ρ=0.067) | 🔶 Partially novel | ✅ Yes (Bansal) | **Solid supporting finding** |
| Panel redesign produces heterogeneity | 🔶 Method contribution | ✅ Yes (prelim) | **Preliminary method validation** |
| Axis-2: wrong-AI over-reliance 0.69, p<0.01 | 🔶 Novel application | ✅ Preliminary | **Significant but underpowered** |
| Axis-1 H1a: panel predicts human dispersion | ✅ Novel | ❌ PENDING (likely weak) | **Central claim, unconfirmed** |
| Panel↔human correspondence | ✅ Novel | ❌ NOT MEASURED | **Fatal gap without E6** |
| "Triage works before human study" | ✅ Novel framing | ❌ Completely unvalidated | **Will be rejected as overclaiming** |

---

## Final Verdict

**The idea is genuinely novel and intellectually important. The execution is disciplined and honest. The evidence is far too thin for a top-venue full paper right now, with the central claim (panel triages → humans agree) completely unvalidated.**

The PI has correctly identified this — the positioning lock, the "triage not prediction" framing, and the E6 deferral are all evidence of genuine scientific maturity. The question is whether the paper can be submitted in a form that matches the evidence. Currently, it cannot. The paper that can be written from what *actually exists* is: "We propose a two-axis triage protocol for pre-deployment screening of human-AI decision interfaces; we show that axis-2 (wrong-AI over-reliance detection) is promising in preliminary calibration runs; we preregister a complete validation program." That is a workshop paper or HCOMP, not CHI.

**The fastest path to a top-venue full paper is:** Run D5.13 (powered axis-2) now, scope and run a stripped E6 (axis-2 validation only, N=40, 6 weeks), then submit a tight FAccT/CHI paper leading with "we validated an LLM panel detector for coercive wrong-AI over-reliance in human-AI decision interfaces" with the axis-1 as honest secondary evidence and the triage protocol as the broader contribution.
