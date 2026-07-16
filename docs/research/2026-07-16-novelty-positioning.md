<!-- Research deliverable produced by subagent research-novelty-positioning (2026-07-16),
     dispatched by Manager #3. Doc-only; verified against primary sources. Prompt:
     .prompts/research-novelty-positioning.md. Feeds paper positioning + reviewer defense. -->
# Research Report: Novelty Positioning for "Two Ways a Design Fail"
**Subagent Research Brief — DOC ONLY — Report to Manager/PI**
*Compiled 2026-07-16 · All citations verified against primary sources*

---

## I. Grounding: The Paper's Current Position

Based on reading all context documents, the paper's architecture is:

- **Core claim (C1):** A multi-agent LLM panel, calibrated on real reliance logs (Bansal CHI'21; Lu & Yin CHI'21), produces a **two-axis triage signal** for human-AI decision interfaces before a human study — Axis 1: panel *disagreement* → flags high over-dispersion ("safety depends on who the user is"); Axis 2: panel *convergent wrong-AI adoption* → flags uniformly lethal dark-pattern designs.
- **Status:** Redesigned panel (PR #4) resolves the initial collapse (conflict rate 3%→43%, persona spread 0.11–0.56, axis-2 signal 0.325, one backfire lead); powered confirmatory H1a NOT yet run. Over-dispersion signal on Bansal is task-selection-sensitive (ρ=0.000–0.067). Single LLM family (gpt-4.1-mini) for exploratory work; confirmatory set = {gpt-4o, gpt-4.1-mini}.
- **Target venues:** CHI Methods, FAccT, CSCW.

---

## II. Per-Question Findings

### RQ1 — LLM / Agent-Based Simulated Users for HCI/UX Evaluation

**The landscape:** This area has grown rapidly from 2022–2025. The community's consensus is that LLMs-as-simulated-users are useful for exploratory work but not validated replacements for real participants.

**Key papers with primary-source verified details:**

**[A] Park et al. (2023) "Generative Agents: Interactive Simulacra of Human Behavior"**
- Authors: Joon Sung Park, Joseph C. O'Brien, Carrie J. Cai, Meredith Ringel Morris, Percy Liang, Michael S. Bernstein (Stanford, Google)
- Venue: UIST 2023 | arXiv:2304.03442
- Claim: 25 LLM-powered agents in a sandbox town produce emergent behaviors (planning Valentine's Day party, spreading information organically). The paper is a proof-of-concept for social simulation, NOT a rigorous behavioral validation against real humans.
- **Relevance to our paper:** We cite this as the architecture ancestor, but our contribution is importantly different — we calibrate on real reliance logs and target a TRIAGE signal (not behavioral fidelity in general).

**[B] Aher, Burns & Zhou (2023) "Using Large Language Models to Simulate Multiple Humans in Psycholinguistic and Social Science Experiments"**
- arXiv:2302.06653
- Claim: LLMs can reproduce classic psycholinguistic and social psychology results (conformity, group polarization) at scale. BUT: not validated on real behavioral DVs with high stakes.
- **Failure mode noted:** real-world external validity is open; risk of amplifying training biases.

**[C] Argyle et al. (2023) "Out of One, Many: Using Language Models to Simulate Human Samples"**
- Published: Political Analysis, 31(3):337–351 (2023)
- Key concept: **"Algorithmic fidelity"** — the standard that LLMs must pass to be used as synthetic participants: they must statistically replicate patterns in real human survey data for the specific context.
- Findings: GPT-3 can reproduce aggregate group-level opinion distributions when conditioned on demographic information; fails for minority subgroups and out-of-distribution stances.
- **Critical for us:** Argyle's "algorithmic fidelity" is exactly what our PAS/ECS calibration metrics are supposed to measure. We can cite this as the standard we attempt to operationalize.

**[D] Santurkar et al. (2023, ICML) "Whose Opinions Do Language Models Reflect?"**
- Proceedings of ICML 2023 (PMLR v202)
- Core finding: Even with explicit demographic steering, LLMs converge toward majority/liberal perspectives — **opinion anchoring** and **limited steerability** undermine the promise of diverse synthetic panels.
- **This is the canonical "homogeneity" critique** our paper must address. PR #4's conflict-conditioned DV + persona conditioning are our partial answer.

**[E] Seshadri et al. (ICLR 2026) "Lost in Simulation: LLM-Simulated Users are Unreliable Proxies for Human Users in Agentic Evaluations"**
- OpenReview:WNlH0Tw585 | arXiv:2601.17087
- Key findings: Agent success rates **vary by ±9 percentage points** depending on which LLM simulates the user; AAVE and Indian English speakers especially poorly reproduced; LLM users are excessively polite and ask unnatural questions; **demographic disparities worsen with age**.
- **Most relevant quantitative critique:** their finding is about AGENTIC TASKS (retail customer service), not our domain (AI-assisted binary decisions). But the 9pp variance figure is a strong example of inter-model unreliability.

**[F] Pang et al. (CHI 2025) "Understanding the LLM-ification of CHI: Unpacking the Impact of LLMs at CHI through a Systematic Literature Review"**
- arXiv:2501.12557 | CHI 2025 Article 456
- Systematic review of 2020–2024 CHI papers; identifies 5 LLM roles including "simulated user."
- Key critique: papers using LLM-simulated users overwhelmingly rely on **closed/proprietary models** (reproducibility problem); validity concerns are often acknowledged but not addressed.
- **Quote (from review):** "questions about whether LLM-simulated behavior truly reflects real human users remain inadequately answered across the surveyed literature."

**[G] Hamalainen et al. (CHI 2023) "Evaluating Large Language Models in Generating Synthetic HCI Research Data"**
- DOI: 10.1145/3544548.3580688
- Tests LLMs for generating synthetic HCI data (questionnaire responses, open-ended comments). Conclusion: useful for pretest/piloting; not a replacement for real users in primary studies.

**[H] Cheng et al. (EMNLP 2023) "CoMPosT: Characterizing and Evaluating Caricature in LLM Simulations"**
- ACL Anthology: 2023.emnlp-main.669
- "Caricature" problem: LLMs exaggerate or oversimplify group traits when asked to simulate minority/politicized demographics — a distinct failure mode from pure homogeneity.

**What our paper's closest neighbors do that we do NOT:**
- Prior work validates LLMs against aggregated *opinion* or *survey* data (Argyle, Santurkar).
- Prior work validates against *agentic task performance* (Seshadri).
- NO prior work validates a synthetic panel against **within-condition reliance OVER-DISPERSION** across users as the DV, in a human-AI decision context, for the specific purpose of PRE-DEPLOYMENT SAFETY TRIAGE.

---

### RQ2 — Predicting Human (Over-)Reliance from AI/UI Properties

**Key papers:**

**[1] Bansal, Wu, Zhou, Fok, Nushi, Kamar, Ribeiro, Weld (CHI 2021) "Does the Whole Exceed its Parts? The Effect of AI Explanations on Complementary Team Performance"**
- DOI: 10.1145/3411764.3445717 | Dataset: github.com/uw-hai/Complementary-Performance (66,040 rows)
- Core finding (verified via multiple sources): *"Explanations increased the chance that humans will accept the AI's recommendation, regardless of its correctness."* Over-reliance increased with explanations even on WRONG-AI trials. Complementary team performance was NOT improved by adding explanations.
- **Heterogeneity:** Across three datasets (beer, Amazon book, LSAT), adoption rates varied substantially by domain and user; some users became over-reliant, others remained skeptical — but this was treated as a nuisance, not the DV.
- **Conditions:** Human-only; Conf+Single; Conf+Double; Conf+Adaptive (Expert); Conf+Adaptive — the five conditions our paper uses for the confirmatory panel run.
- **Our paper's use of this dataset:** we train/calibrate on Bansal to discover that AI-assisted over-dispersion is predominantly user×task (ρ=0.067, no-AI stable_user_share=0.74 vs AI-assisted 0.32–0.41).

**[2] Buçinca, Malaya, Gajos (CSCW 2021) "To Trust or to Think: Cognitive Forcing Functions Can Reduce Overreliance on AI in AI-assisted Decision-making"**
- DOI: 10.1145/3449287
- Core finding: Simply adding explanations did NOT reduce over-reliance; **cognitive forcing** interventions (e.g., force user to decide before seeing AI) DID reduce over-reliance, but were rated less favorably. **Heterogeneity:** effectiveness was moderated by Need for Cognition — showing user-level individual differences matter.
- **Relevance:** This is axis-1's origin story. Their "user × intervention" heterogeneity in reliance effects is exactly what our over-dispersion DV is designed to capture pre-deployment.

**[3] Vasconcelos, Jörke, Grunde-McLaughlin, Gerstenberg, Bernstein, Krishna (CSCW 2023) "Explanations Can Reduce Overreliance on AI Systems During Decision-Making"**
- DOI: 10.1145/3579605 | 5 studies, N=731
- Core finding: Over-reliance is a **strategic cost-benefit choice**, not purely cognitive bias. Explanations reduce over-reliance only when the cost of engaging with them is low enough. This means that DESIGNING explanations to be easy to verify lowers over-reliance.
- **Key nuance for our paper:** Their framework implies that different UI designs will produce different over-reliance rates ACROSS USERS as a function of individual cost-benefit calculus — which is the over-dispersion signal we aim to detect with axis-1.

**[4] Zhang, Liao, Bellamy (FAccT 2020) "Effect of Confidence and Explanation on Accuracy and Trust Calibration in AI-Assisted Decision Making"**
- DOI: 10.1145/3351095.3372852 | FAccT 2020 (formerly FAT*)
- Core finding: Confidence scores help calibrate trust; **local explanations did NOT reliably improve joint performance** and sometimes failed to help users distinguish correct vs. incorrect AI. Over-reliance persists even with confidence display.
- **Relevance to axis-2:** This paper shows confidence display alone is insufficient to prevent over-reliance on wrong AI — which is the scenario our axis-2 targets (coercive high-confidence framing).

**[5] Green & Chen (CHI 2019) "Disparate Interactions: An Algorithm-in-the-Loop Analysis of Fairness in Risk Assessments"**
- DOI: 10.1145/3290605.3300603 (CHI '19)
- Core finding: AI risk score predictions lead to over-reliance by human decision-makers in recidivism settings; explanations do NOT mitigate this; disparate impacts on racial fairness worsen when explanations are added for some user groups.
- **Relevance:** Different users (different background, race, context) show disparate reliance responses to the same AI — another heterogeneity observation directly motivating axis-1.

**[6] Lai & Tan (CHI 2019) "On Human Predictions with Explanations and Predictions of Machine Learning Models: A Case Study on Criminal Recidivism"**
- DOI: 10.1145/3290605.3300469
- Core finding: Human-AI complementarity exists but is conditional; human-ML predictions diverge systematically (not randomly) → selective reliance is possible in principle. Explanations have mixed effects on human accuracy.

**[7] Schemmer, Kühl, Benz, Satzger (IUI 2023) "Appropriate Reliance on AI Advice: Conceptualization and the Effect of Explanations"**
- DOI: 10.1145/3581641.3584066 | N=200
- **Most relevant framing:** proposes "Appropriateness of Reliance (AoR)" — accepting correct and rejecting incorrect AI recommendations. Explanations have **heterogeneous effects** on AoR depending on explanation quality and user characteristics.
- **Key claim:** "Not all users respond similarly—individual differences ... moderated the impact of explanations."

**[8] Gajos & Mamykina (IUI 2022) "Do People Engage Cognitively with AI?"**
- DOI: 10.1145/3490099.3511138
- Cognitive forcing UI interventions (explanation-only, no direct recommendation) improve learning but increase cognitive load — heterogeneous effects across user groups.

**What the literature collectively establishes (and what we add):**
- Explanations reliably INCREASE over-reliance on wrong AI (Bansal 2021 is the canonical evidence).
- Heterogeneity across users in reliance response to UI interventions is documented (Buçinca, Schemmer, Green & Chen) but treated as a confound or covariate, NOT as the dependent variable of a safety screening system.
- **Our paper's addition:** Operationalize inter-user over-dispersion as an explicit DV; pre-register a triage threshold; use a synthetic panel to predict it before running humans. No prior paper does this.

---

### RQ3 — Dark Patterns / Coercive AI Framing & Backfire Evidence

**Key papers:**

**[1] Luguri & Strahilevitz (2021) "Shining a Light on Dark Patterns"**
- Oxford Journal of Legal Analysis, 13(1):43–109 | DOI: 10.1093/jla/laaa006
- Large-scale experiment: **aggressive** dark patterns trigger **psychological reactance** (users reject the manipulative option or quit the service); **mild** dark patterns increase compliance without triggering resistance.
- **Key finding for us:** Reactance is NOT universal — it is moderated by education level and awareness of manipulation intent. This is exactly the pattern our axis-2 dark-pattern-backfire lead shows: one persona actively resists (0% adoption) while others comply.

**[2] Mildner, Savino, Doyle, Cowan, Malaka (CHI 2023) "About Engaging and Governing Strategies: A Thematic Analysis of Dark Patterns in Social Networking Services"**
- DOI: 10.1145/3544548.3580695
- Taxonomy of dark patterns: "authority/credibility cues," "emotional pressure," "behavioral coercion." These are exactly the types of dark patterns in our axis-2 condition (pseudo-high-confidence + oppressive responsibility framing).

**[3] "The Siren Song of LLMs: How Users Perceive and Respond to Dark Patterns in Conversational AI"**
- arXiv:2509.10830 (2025)
- Finds that LLM-native dark patterns (engagement manipulation, belief manipulation, decision manipulation) are recognized by some users who then resist — partial reactance evidence.

**On dark-pattern BACKFIRE in AI-decision-support specifically:**
- **No prior paper documents a quantified backfire** (e.g., 0% adoption under coercive framing) **within a computational synthetic panel for human-AI decision interfaces.** The closest evidence is from reactance psychology (Luguri & Strahilevitz) and from general LLM dark pattern user studies (Siren Song), which are with real humans, not synthetic panels, and not in a decision support context.
- **Our axis-2 finding is a genuine FIRST LEAD:** a single persona (p5) shows 0% wrong-AI adoption under the coercive condition, which if it replicates in powered confirmatory runs, would be the first such computational demonstration.
- **Honest caveat:** It is currently one data point in an underpowered run (exploratory, old renderer pre-D5.1 correction, n=20 items, gpt-4.1-mini only). The backfire cannot be claimed as a contribution yet; it is a PILOT LEAD.

---

### RQ4 — Pre-Deployment / Offline Evaluation Methods for Human–AI Teams

This is the sparsest literature — and the gap our paper most directly fills.

**[1] Rastogi, Liu, Hullman (EAAMO 2022, extended in HCOMP 2023)**
- arXiv:2204.10806 | HCOMP DOI:10.1609/hcomp.v11i1.27554
- "A Unifying Framework for Combining Complementary Strengths of Humans and ML toward Better Predictive Decision-Making"
- Proposes an optimization-based offline framework for identifying the optimal human-ML combination policy using historical data (counterfactual offline evaluation).
- **Critical difference from our paper:** Rastogi et al. optimize for joint ACCURACY (how to best combine human + AI). They do NOT triage UI DESIGNS for over-reliance safety; their "offline evaluation" is about routing tasks to human vs. AI, not about pre-screening whether a given UI will make users dangerously over-reliant.

**[2] Bansal 2021 dataset itself** is a form of retrospective characterization, not prospective triage.

**[3] "Pre-deployment evaluation" in the AI safety sense (EU AI Act, NIST AI RMF):** Focuses on technical safety testing (adversarial robustness, fairness audits), NOT on human behavioral reliance patterns pre-deployment.

**THE GAP (verified):** No prior published work proposes:
- A synthetic panel calibrated on real reliance logs to produce a **dual-axis triage signal** (over-dispersion + wrong-AI convergence)
- Used specifically to SCREEN human-AI DECISION INTERFACES before a human study
- With pre-registered thresholds and an explicit abstention rule

This gap is genuinely novel. The closest methodological cousin (Rastogi 2022/2023) addresses a different problem (optimal routing, not UI safety triage), and silicon sampling work (Argyle, Park) addresses behavioral simulation without the triage framing.

---

## III. Citation List (Deduplicated, Diverse)

| # | Citation | Year | Venue | DOI/URL | RQ |
|---|---|---|---|---|---|
| 1 | Bansal, Wu, Zhou, Fok, Nushi, Kamar, Ribeiro, Weld — "Does the Whole Exceed its Parts? The Effect of AI Explanations on Complementary Team Performance" | CHI 2021 | `10.1145/3411764.3445717` | RQ2, data |
| 2 | Lu, Yin — "Human Reliance on Machine Learning Models When Performance Feedback is Limited" | CHI 2021 | `10.1145/3411764.3445562` | RQ2, data |
| 3 | Buçinca, Malaya, Gajos — "To Trust or to Think: Cognitive Forcing Functions Can Reduce Overreliance on AI" | CSCW 2021 | `10.1145/3449287` | RQ2, axis-1 |
| 4 | Vasconcelos, Jörke et al. — "Explanations Can Reduce Overreliance on AI Systems During Decision-Making" | CSCW 2023 | `10.1145/3579605` | RQ2 |
| 5 | Zhang, Liao, Bellamy — "Effect of Confidence and Explanation on Accuracy and Trust Calibration" | FAccT 2020 | `10.1145/3351095.3372852` | RQ2, axis-2 |
| 6 | Green, Chen — "Disparate Interactions: An Algorithm-in-the-Loop Analysis of Fairness in Risk Assessments" | CHI 2019 | `10.1145/3290605.3300603` | RQ2, RQ3 |
| 7 | Lai, Tan et al. — "On Human Predictions with Explanations..." | CHI 2019 | `10.1145/3290605.3300469` | RQ2 |
| 8 | Schemmer, Kühl, Benz, Satzger — "Appropriate Reliance on AI Advice" | IUI 2023 | `10.1145/3581641.3584066` | RQ2 |
| 9 | Gajos, Mamykina — "Do People Engage Cognitively with AI?" | IUI 2022 | `10.1145/3490099.3511138` | RQ2 |
| 10 | Park, O'Brien, Cai, Morris, Liang, Bernstein — "Generative Agents: Interactive Simulacra of Human Behavior" | UIST 2023 | arXiv:2304.03442 | RQ1 |
| 11 | Argyle et al. — "Out of One, Many: Using Language Models to Simulate Human Samples" | Political Analysis 2023 | `10.1017/pan.2023.2` | RQ1 |
| 12 | Santurkar et al. — "Whose Opinions Do Language Models Reflect?" | ICML 2023 | PMLR v202 | RQ1 |
| 13 | Aher, Burns, Zhou — "Using Large Language Models to Simulate Multiple Humans in Psycholinguistic and Social Science Experiments" | 2023 | arXiv:2302.06653 | RQ1 |
| 14 | Seshadri et al. — "Lost in Simulation: LLM-Simulated Users are Unreliable Proxies for Human Users in Agentic Evaluations" | ICLR 2026 | OpenReview:WNlH0Tw585 | RQ1 |
| 15 | Pang, Schroeder, Smith, Barocas, Xiao, Tseng, Bragg — "Understanding the LLM-ification of CHI" | CHI 2025 | arXiv:2501.12557 | RQ1 |
| 16 | Hamalainen et al. — "Evaluating Large Language Models in Generating Synthetic HCI Research Data" | CHI 2023 | `10.1145/3544548.3580688` | RQ1 |
| 17 | Cheng et al. — "CoMPosT: Characterizing and Evaluating Caricature in LLM Simulations" | EMNLP 2023 | ACL:2023.emnlp-main.669 | RQ1 |
| 18 | Luguri, Strahilevitz — "Shining a Light on Dark Patterns" | JLA 2021 | `10.1093/jla/laaa006` | RQ3 |
| 19 | Mildner, Savino, Doyle, Cowan, Malaka — "About Engaging and Governing Strategies: Dark Patterns in SNS" | CHI 2023 | `10.1145/3544548.3580695` | RQ3 |
| 20 | Rastogi, Liu, Hullman — "A Unifying Framework for Combining Complementary Strengths of Humans and ML" | EAAMO 2022 / HCOMP 2023 | arXiv:2204.10806 | RQ4 |
| 21 | Jacovi, Goldberg — "Towards Faithfully Interpretable NLP Systems" | ACL 2020 | — | renderer fidelity (D5.1) |
| 22 | Jacovi et al. — "Diagnosing AI Explanation Methods with Folk Concepts of Behavior" | FAccT 2023 | `10.1145/3593013.3593993` | D5.1 / placebo |

---

## IV. Ranked Novelty Claims

### **Claim 1 (Most Novel, Load-Bearing):** Two-Axis Pre-Deployment Triage Signal with a Synthetic Panel

> *A multi-agent LLM panel calibrated on real human reliance logs produces a dual-axis triage signal — axis-1 predicts whether a UI design creates dangerous user-level reliance over-dispersion (safety depends on who uses it), and axis-2 detects whether a UI induces uniformly high over-reliance on a wrong AI (dark design) — enabling pre-deployment safety screening of human-AI decision interfaces before committing to a human study.*

**Why genuinely novel:** No prior paper (a) makes *over-dispersion* (not mean reliance) the triage target, (b) combines this with a wrong-AI detection axis, (c) uses a synthetic panel calibrated on real reliance logs for this purpose, or (d) pre-registers a dual-threshold screening protocol. Rastogi 2022/2023 is the closest neighbor but addresses performance optimization, not UI safety triage. Silicon sampling papers (Argyle, Park) address general behavioral simulation without the triage framing.

**Incremental aspect:** The synthetic panel architecture itself (LLM-as-participant) is not new (Park 2023, Aher 2023). The calibration idea echoes Argyle's "algorithmic fidelity." The novelty is in the WHAT (over-dispersion + wrong-AI triage) + WHY (pre-deployment safety screening) + HOW (calibrated dual-threshold protocol).

**Current evidence status:** Pilot evidence (underpowered, single-model, old renderer). Confirmatory H1a not yet run. This is a valid methods paper if the correspondence is n≥5 conditions with a significant correlation — but the signal is currently fragile (ρ=0.000–0.067 depending on task selection).

---

### **Claim 2 (Strong Supporting, more incremental):** Over-Dispersion as an Explicit Dependent Variable for UI Safety

> *We reframe the well-documented heterogeneity in human reliance on AI explanations (Bansal 2021; Buçinca 2021; Schemmer 2023) as the primary safety-relevant DV — operationalized as beta-binomial over-dispersion — rather than treating it as a confound. We show that AI-assisted reliance shifts from a stable user trait (no-AI: stable-user share ≈ 0.74) toward user×task interaction (AI-assisted: ≈ 0.32–0.41), implying that single-user or aggregate evaluations systematically underestimate the population safety risk.*

**Why novel:** The specific operationalization (beta-binomial over-dispersion; stable-user share decomposition) is new to the HCI reliance literature. Prior papers acknowledge heterogeneity but none quantify it as a safety-relevant DV with a formal over-dispersion estimator.

**Incremental aspect:** The heterogeneity observation itself is well-established. The beta-binomial model is a standard statistical tool. The novelty is in the specific use case and framing.

**Current evidence status:** CONFIRMED on Bansal (ρ=0.067, real data, PR #2); NOT confirmed to generalize (Lu&Yin is trait-stable 0.80, unresolved). Present as Bansal-specific observation + open question.

---

### **Claim 3 (Preliminary Lead, honest framing required):** Dark-Pattern-Backfire Detected in a Synthetic Decision Panel

> *Under a maximally coercive dark UI condition (pseudo-high-confidence + oppressive responsibility framing + wrong AI), one persona in our calibrated panel shows 0% wrong-AI adoption — a computational instance of psychological reactance. This provides a first computational panel-level detection of dark-pattern backfire, suggesting that axis-2 can detect not only compliance risk but also backfire risk in coercive designs.*

**Why potentially novel:** While psychological reactance is well-documented (Luguri & Strahilevitz 2021), no prior paper reports a quantified backfire within a computational synthetic panel for human-AI decision interfaces. This would be a methodologically distinct contribution.

**Why this is a LEAD, not a claim yet:** (a) Exploratory only (gpt-4.1-mini, n=20 items, old renderer); (b) single persona out of 6; (c) E4 completion is pending (193/450 calls cached). Can only be elevated to a claim after powered confirmatory E4 run on corrected renderer.

---

## V. Reviewer-Attack → Defense Table

| Attack | Strength | Current Evidence Answers? | Defense / Needed Evidence |
|---|---|---|---|
| **A1: "Synthetic personas aren't real users — the panel is just LLM self-report, not behavioral simulation"** | ★★★★★ (fatal if unanswered) | **PARTIAL.** Calibration against real Bansal + Lu&Yin data is the answer; pivot from "predict outcomes" to "triage signal" reduces the burden. Conflict-conditioned DV (S1≠AI trials only) measures movement, not agreement. | Defend via: (a) calibration protocol + PAS/ECS metrics; (b) cross-condition Spearman ρ correspondence on n≥5 conditions (confirmatory E1); (c) pre-registration as the claim-limiting device; (d) explicitly position as TRIAGE (smoke alarm) not PREDICTION. **OPEN: powered E1 must run.** |
| **A2: "Panel just re-encodes the LLM's own priors — the 'persona disagreement' reflects LLM stochasticity, not human heterogeneity"** | ★★★★ (serious) | **PARTIAL.** PR #4 distinguishes preference-driven vs. capability-noise disagreement; item selection used AI-side exogenous properties (not human DV → no leakage). But a skeptic can say the persona spread (0.11–0.56) reflects prompt sensitivity. | Defend via: (a) cross-model triangulation (gpt-4o vs gpt-4.1-mini in confirmatory; Azure cross-vendor); (b) D2.4 disclosure (no label leakage); (c) show that only CONFLICT-CONDITIONED cells (System-1≠AI) show spread, not trivial agreement cells; (d) ablation: frozen persona (C2 elasticity) vs. random temperature → distinguish sources of variance. **OPEN: cross-vendor triangulation not yet run.** |
| **A3: "Correspondence is only n=5 conditions — you can't do statistics on 5 points"** | ★★★★ (serious) | **PARTIALLY ANSWERED.** E3 (LOIO) and E2 (elasticity) add generalization evidence beyond 5 conditions. | Defend via: (a) E3 LOIO hit rate as primary generalization test; (b) Spearman ρ with bootstrapped CI; (c) note that 5 conditions is comparable to Bansal's study design (6 conditions); (d) E6 prospective mini-study with N≈80 as operating-point check. **OPEN: E3 and E6 not yet run.** |
| **A4: "Signal is fragile — ρ varies from 0.000 to 0.067 depending on task selection"** | ★★★★ (serious; our own disclosure in SPEC §5) | **DISCLOSED BUT NOT RESOLVED.** Robustness results in `e1_multicond_robustness.json` show task-selection sensitivity. 'all' (50 tasks) gives ρ=0.067; 'first_10_shared' gives 0.037; 'min_per_domain' gives 0.000. | Defend via: (a) pre-registered choice of 'all' tasks as the principled estimator; (b) report sensitivity as a known limitation in §5 E1 caveat; (c) frame: the beta-binomial estimator is unbiased but the SIGNAL magnitude is low — this motivates the calibrated threshold approach (τ_disp), not a binary hit/miss. **PARTIALLY ANSWERABLE now; full answer requires τ calibration.** |
| **A5: "Single domain (beer sentiment) — results don't generalize"** | ★★★ (moderate) | **PARTIALLY ADDRESSED.** Bansal has three domains (beer, Amazon book, LSAT); Lu & Yin adds a second dataset. The C1 panel result is currently beer-only (PR #4, 20 items). | Defend via: (a) E1 confirmatory will span all Bansal shared tasks across domains; (b) Lu&Yin replication adds a second dataset; (c) E3 LOIO tests cross-class generalization; (d) honest bound: position as a methods paper with two-dataset validation, with E6 as prospective scope extension. **OPEN: full multi-domain confirmatory not yet run.** |
| **A6: "Underpowered — key results are p=0.17 on n=11 items"** | ★★★★ (serious) | **HONEST DISCLOSURE IN SPEC.** Elasticity result is explicitly flagged as underpowered. The axis-2 signal (0.325) has no CI yet. | Defend via: (a) pre-registered power target N (currently PENDING — must be filled from a clean exploratory pass); (b) Azure confirmatory as the clean powered run; (c) distinguish exploratory (pilot, PR #4) from confirmatory (not yet run) — the paper presents BOTH honestly; (d) statistical plan: beta-binomial + bootstrap CI + BH correction + effect sizes already specified. **OPEN: power-N not yet frozen; confirmatory run not started.** |
| **A7: "Why not just run the human study? What is the cost saving?"** | ★★ (moderate; more about motivation) | **PARTIALLY ANSWERED by framing.** The smoke alarm argument: cheap pre-screening to avoid deploying dangerous interfaces; complements, not replaces, human studies. | Defend via: (a) quantify cost comparison (LLM panel run: ~$15–45 on Azure; human study: $5,000–50,000); (b) frame as a FILTER that reduces the denominator of required human studies; (c) analogize to A/B testing for safety before deployment; (d) emphasize the triage protocol's asymmetric cost: a false alarm (run human study anyway) is much cheaper than a miss (release a dangerous design). |
| **A8: "LLM homogeneity — your 'diverse panel' will converge to the same answer (silicon sampling critique)"** | ★★★★ (serious; Santurkar, Seshadri) | **ADDRESSED BY REDESIGN.** PR #3's naive panel showed near-uniform convergence (97% no-movement); PR #4's conflict-conditioned DV + hard items + persona conditioning + cross-model design resolves this (43% conflict, spread 0.11–0.56). | Defend via: (a) show conflict-conditioned DV eliminates the trivial agreement artifact; (b) show that disagreement varies BETWEEN CONDITIONS (not just noise), which is the cross-condition ρ; (c) multi-model confirmatory cross-model consistency; (d) "preference-driven vs. capability-noise" ablation (SPEC §4.2); (e) acknowledge Santurkar's steerability critique and show our calibration step (KL minimization) is the corrective. **PARTIALLY ANSWERED now; full answer needs cross-model run.** |

---

## VI. Honest Summary: Incremental vs. Genuinely Novel

**Genuinely novel (if confirmed):**
1. The **two-axis triage framing** — redefining the problem from "can we predict human reliance?" to "can we triage interfaces by over-dispersion risk and wrong-AI convergence risk?" This reframing is methodologically significant and has no direct prior art.
2. **Beta-binomial over-dispersion as an explicit UI safety DV** — no prior HCI reliance paper uses this formalism with this intent.
3. **Counterfactual difficulty-controlled pairing** (C2 elasticity) — within-pair cancellation of difficulty is a clean design; not found in prior panel simulation work.

**Incremental (prior art exists, we extend):**
1. LLM-as-simulated-participant — well-established; our contribution is the specific calibration + triage application.
2. Explanations increasing over-reliance — Bansal 2021 is the canonical finding; we replicate it in a new analysis (C0, Bansal-specific) and use the data to calibrate a panel.
3. Dark-pattern taxonomy — well-covered; our contribution is the first computational detection signal, not the taxonomy.

**Currently inconclusive (honest):**
1. The powered confirmatory H1a (axis-1 cross-condition correspondence) — NOT YET RUN.
2. Axis-2 E4 completion — PARTIAL (193/450 cached).
3. Cross-vendor triangulation — deferred to Azure.
4. Backfire lead — underpowered pilot; cannot be claimed as a contribution yet.

The paper is in a state where **the METHOD is plausible and the preliminary signals are present, but the load-bearing claim (H1a: panel disagreement predicts human over-dispersion significantly better than mean-predictor, n≥5 conditions, CI excludes 0) has not been tested**. For a top-venue methods paper, this is the critical gap to close before submission.

---

## VII. Recommended Positioning for Reviewers

**Lead with the methodological reframing, not the empirical magnitude.** The strongest positioning is:

> "Prior work measures over-reliance as a mean effect (Bansal 2021; Buçinca 2021); we propose that *variance* in reliance across users — over-dispersion — is the safety-relevant quantity, and that a pre-deployment synthetic panel can triage interfaces on this dimension plus a wrong-AI convergence dimension before expensive human studies. We validate this two-axis protocol against two real human decision datasets and pre-register the confirmatory test."

This framing:
- Neutralizes A7 (cost saving is built in)
- Positions against the "just a simulation" critique by emphasizing the triage framing
- Makes the modest empirical signal (ρ=0.067) a target for detection, not a boast
- Is defensible even if cross-condition ρ is small (because the *method* is the contribution, and small ρ motivates the abstention rule in E5)

**Do NOT lead with the backfire finding or claim it as a contribution** until E4 is fully powered and the renderer correction (D5.1) has been applied.

---

*End of research report. No repo files were created or modified. All findings are from primary web sources and the read-only context documents in the repo.*
