# research-novelty-positioning — related work + novelty/attack map (doc-only)

Doc-only research. NO code, NO repo edits except this prompt is already committed. Deliver a
concise, well-cited findings report to the Manager. Goal: sharpen the novelty framing of
**"two-ways-a-design-fail"** and pre-empt reviewer attacks for a top venue (CHI Methods / FAccT /
CSCW).

## What the paper currently is (context — read these first)
- `开题沟通稿_分歧度分诊_部署前评估_v2.4.md` (core idea), `SPEC.md` §2–§5, `docs/DECISIONS.md`
  (esp. C1 PRIMARY / C0 demoted; D5.1 renderer fidelity), `PROGRESS.md`.
- One-line pitch: a **pre-deployment evaluation method** that uses an **LLM agent-panel as a
  synthetic user cohort** to triage human–AI decision *interfaces* on **two failure axes** BEFORE a
  human study — axis-1 (UI/explanation design → heterogeneous, user-sensitive reliance
  over-dispersion) and axis-2 (systematic over-reliance on a WRONG AI; uniformly lethal / dark
  patterns). Validated against REAL human datasets (Bansal CHI'21, Lu&Yin CHI'21). Preliminary
  signals: panel reproduces human patterns; a dark-pattern **backfire** (a persona adopts 0% under
  coercive framing). Manager's recommended headline validation: panel disagreement per UI condition
  ↔ REAL human reliance over-dispersion per condition (cross-condition correspondence).

## Research questions (each with citations: authors, year, venue, URL; quote where load-bearing)
1. **LLM / agent-based SIMULATED USERS for HCI/UX evaluation.** Find the strongest recent work
   using LLMs (or ABMs) as synthetic participants / simulated users to predict or pre-screen human
   study outcomes, usability, or survey responses. Who has done "LLM as participant"? What did they
   validate against real humans, and what were the documented FAILURE modes / criticisms (e.g.,
   homogeneity, mode collapse, miscalibration, "silicon sampling" critiques)? This is our closest
   methodological neighbor — map it precisely.
2. **Predicting human (over-)reliance on AI from model/UI properties.** Work relating AI confidence,
   explanations, and UI design to appropriate reliance / over-reliance / automation bias (e.g.,
   Bansal 2021, Buçinca, Vasconcelos, Zhang, Bansal, Lai & Tan, Passi, Green & Chen). What is
   known about *explanations increasing over-reliance*, and about *heterogeneity across users*?
   Position our axis-1 (over-dispersion as the DV) and axis-2 (wrong-AI over-reliance) against it.
3. **Dark patterns / manipulative AI framing in decision support.** Prior evidence on coercive/
   dark UI framing changing reliance, and any reports of BACKFIRE / reactance effects. How novel is
   our axis-2 "dark-pattern backfire" observation?
4. **Pre-deployment / offline evaluation methods for human–AI teams.** Are there existing "test the
   interface before running the human study" methods? What's the gap our two-axis triage fills?
5. **The novelty statement + attack map.** Given 1–4: (a) draft 2–3 candidate crisp novelty claims
   for our paper, ranked; (b) list the 5–8 most likely REVIEWER ATTACKS (e.g., "synthetic personas
   aren't real users", "single domain", "underpowered", "panel just re-encodes the LLM's own
   priors", "correspondence is n=5 conditions") and, for each, the strongest available DEFENSE or
   the experiment/analysis we'd need. Flag which attacks our current evidence already answers vs
   which are open.

## Deliverable
A structured report: per-question findings with a citation list (dedup, most-diverse set), a ranked
novelty-claim shortlist, and the reviewer-attack→defense table. Be honest where our contribution is
incremental vs genuinely new. Prefer primary sources (papers) over blogs. Do NOT edit repo files;
report to the Manager only.
