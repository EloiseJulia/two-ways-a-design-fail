# Novelty / collision audit — VERIFIED (Manager #5, 2026-07-27)

Refresh of the D5.55 audit (2026-07-23). Method: research subagent web sweep + Manager independent
re-verification of the two highest-threat papers against authoritative arXiv HTML `<meta citation_*>` tags.

**Overall reinventing-the-wheel risk: MEDIUM** (unchanged from D5.55). No single paper pre-empts our
COMPOUND contribution; but 2025–2026 is converging on "LLM-simulation instability" + "LLM manipulation/
dark patterns", so reviewers will demand explicit differentiation from ~5 recent works.

## RIGOR NOTE — author lists must be re-verified at cite time
The research subagent DROPPED an author on 2602.21262 (reported 4; arXiv meta shows 5, incl. Kerem Oktar).
Manager personally verified 2602.21262 and 2601.17087 from arXiv meta. Treat every OTHER author list below
as subagent-reported and RE-VERIFY from arxiv.org/abs/<id> HTML meta before adding any \bibitem. Web/AI
search snippets are NOT authoritative (this is the same trap D5.55 caught).

## Highest-threat, VERIFIED
1. **HIGH / TENSION — Lost in Simulation** (arXiv:2601.17087, ICLR 2026 + ACL 2026). Seshadri, Preethi;
   Cahyawijaya, Samuel; Odumakinde, Ayomide; Singh, Sameer; Goldfarb-Tarrant, Seraphina. **[Manager-verified]**
   Independently shows LLM-simulated USERS are unreliable proxies: agent success on tau-Bench retail varies
   up to 9pp across user-LLMs; systematic miscalibration; AAVE/Indian-English/age fairness gaps.
   → Closest methodological collision. DIFFERENTIATION (all hold): (i) they show magnitude (±9pp), we show
   risk-CLASSIFICATION flip (≤0.60 of backend pairs); (ii) they measure agent task-completion, we measure
   interface-content SAFETY risk; (iii) they CENTER human-correspondence validity (human study = ground
   truth), we explicitly DISCLAIM it; (iv) failure-targeted at-risk persona vs generic populations.
   ACTION: must cite + QUALIFY any "first to show backend sensitivity" wording.
2. **MED-HIGH / COMPLEMENTARY+TENSION — Under the Influence** (arXiv:2602.21262, preprint 2026-02-24).
   Robinson, Sasha; **Oktar, Kerem**; Collins, Katherine M.; Sucholutsky, Ilia; Allen, Kelsey R.
   **[Manager-verified: 5 authors]** Sokoban LLM-vs-LLM advice game; task performance, persuasion, and
   vigilance are DISSOCIABLE (strong solver ≠ detects being misled). → Corroborates our Contribution-2
   "capability ≠ resistance", but at the LLM-as-agent level, not LLM-as-simulated-user. Note nuance: they
   say "dissociable"; we report an inverse correlation in our synthetic setting — state honestly.
   ACTION: cite as supporting; distinguish level of analysis.

## Medium / lower threat (subagent-reported; RE-VERIFY authors before citing)
3. COMPLEMENTARY — **Illusion of Intervention** (arXiv:2605.20767): "user drift" = within-backend
   treatment-induced population shift ⇒ LLM experiments are observational. Orthogonal validity threat to our
   between-backend one; cite alongside variance decomposition.
4. TENSION (terminology) — **Coin Flip Judge** (arXiv:2606.13685): "flip" = within-judge run-to-run
   stochasticity (~13.6%). MUST distinguish our CROSS-backend flip from within-backend stochastic flip.
5. COMPLEMENTARY — **Whose Personae?** (arXiv:2512.00461, AAAI/ACM AIES 2025): review of 63 synthetic-persona
   studies; persona-transparency checklist. Motivates audit need; we add the backend-invariance axis.
6. COMPLEMENTARY/FOIL — **DarkBench** (arXiv:2503.10728, ICLR 2025 Oral, OpenReview odjMSBSWRt): dark patterns
   EMBEDDED IN the LLM's own behavior. We study interface-content risk with the LLM as instrument — different
   subject; cite as motivation.
7. COMPLEMENTARY — **Measuring & mitigating overreliance** (arXiv:2509.08010, position/survey, 17 authors).
   Advocates exactly the overreliance measurement we instantiate; no backend-sensitivity claim.
8. COMPLEMENTARY (LLM-judge consistency context) — **TrustJudge** (arXiv:2509.21117, ICLR 2026);
   **Sage** (arXiv:2512.16041); **The Dual Nature of LLM Persona** (arXiv:2607.02368).
9. NOT A COLLISION — **Ensembling LLMs for Code Vulnerability Detection** (arXiv:2509.12629): "vulnerability"
   = software CVEs. Do NOT cite.
10. COMPLEMENTARY (HCI system) — **PersonaCite** (arXiv:2601.22288): grounds personas in VoC evidence.

## Capability-routing refs our Contribution 2 INVERTS (already cited, verified)
RouteLLM arXiv:2406.18665 (ICLR 2025); Mixture-of-Agents arXiv:2406.04692.

## Net recommendation (PI decision — owner)
No pivot needed; contribution stands. Before submission: add ~5 differentiating cites (esp. Lost in
Simulation + Under the Influence), and soften/qualify any "first"/"we are the first" wording about backend
sensitivity to "first to frame it as risk-classification flip in interface-safety measurement with
failure-targeted personas". This is a Related-Work + claim-strength edit → belongs in the writing session,
under owner sign-off.
