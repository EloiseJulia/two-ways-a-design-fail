# Manager #4 → #5 Handoff (2026-07-24)

> Retiring Manager #4 (context full). This is the authoritative snapshot for the successor.
> Read order for the new session: this file → docs/manager-prompt-v4.md → docs/DECISIONS.md (D5.44–D5.57)
> → docs/paper/main.tex → this file's "IN-FLIGHT" section.

## 0. One-line status
Paper `docs/paper/main.tex` = **15 pp, compiles clean, double-blind anonymized**. A large increment round
(D5.44–D5.57) is integrated and audited. **One experiment still running: LSAT** (task-structure
generalization). Compute uses the local `ghc-api` proxy (serial only; 429s under concurrency).

## 1. What the paper is (unchanged framing)
HYBRID measurement-audit. Title kept ("Two Ways a Design Fails: When Does a Synthetic LLM Panel See the
Danger?"), subtitle now "A Backend-Sensitivity Audit of Synthetic-User Interface-**Content** Risk
Measurement". Claimed contribution = a backend-sensitivity **audit** of synthetic-user (LLM-panel)
interface-risk measurement. **No human-predictive-validity claim** until E6. panel↔human correspondence is
an honest NULL.

## 2. The 4 contributions (current wording in intro)
1. **Backend-sensitivity audit**, organized around a named **risk-classification flip rate** (up to 0.60):
   magnitude-shift (prior work) vs threshold-flip (ours).
2. **Capability–vulnerability mismatch + vulnerability-coverage panel selection** (submodular set-cover,
   greedy (1−1/e); the INVERSE of capability routing RouteLLM/MoA).
3. **Reusable audit + reporting protocol** (variance decomposition; behavior taxonomy; cross-backend
   decision-flip; disagreement-triggered abstention).
4. **Two-axis over-dispersion/coercion construct** on a preregistered audit-gated pipeline.
Plus: protective-intervention audit (sec:protective); commercial-tooling implications; honest null
correspondence; planned E6.

## 3. What this session (Manager #4) did — all committed, all audited
- **D5.44/D5.45 Experiment A (protective-intervention audit)**: added plain/forcing/verify wrong-AI
  conditions. Protective framings significantly cut synthetic over-reliance (pooled p=0.003; p5 0.78→0.46–
  0.53, p<1e-6); DIRECTION backend-robust (all benefits ≥0) but MAGNITUDE not; **preregistered H2/H3
  REFUTED** (frontier shows no floor; gemini nearly inert). sec:protective + fig8 (slopegraph).
- **D5.46 commercial-paradigm framing** (intro two untested assumptions + Discussion "Implications for
  commercial synthetic-user tooling"). Cites syntheticusers/uxia (verified @misc).
- **D5.47 holistic de-dup** of Discussion; abstract tightened ~350→~300 words; persona OR harmonized to 26.
- **D5.48 3 equations** (coverage set-cover+greedy; RAIR/RSR; axis-1 disagreement) + FIXED an axis-1
  prose/code mismatch (it is BETWEEN-persona rate variance, not per-item).
- **D5.49/D5.50 figures**: shared figstyle (Okabe–Ito CB-safe, Times serif) THEN a genuine chart-type
  redesign v3 (slopegraph/lollipop/marginal-heatmap/CI-bands/coverage-gap via SciencePlots) +
  **v3.1 review-refinements** (Wilson whiskers not band; stems-from-threshold; real step(); label declutter;
  effect sizes). **All versions archived** in figures/archive/{v0_first_D5.30, v1_pre_restyle,
  v2_okabe_recolor, v3_redesign, v3_1_review_refined}.
- **D5.51–D5.56 Backend expansion to n=11** (see memory + §5 below). agg_adopt–capability BH-robust; flip/p5
  suggestive. fig6b_expand11 added.
- **D5.53** UI/multimodal arm DEFERRED; scope tightened to interface-**content**; venue watermark anonymized.
- **D5.54 LSAT harness** built (self-contained multiple-choice, scripts/analysis/lsat_panel.py).
- **D5.55 novelty/collision audit** (research subagent): overall risk MEDIUM. Added metadata-verified cites
  Hu&Collier (ACL'24), Park et al. 2024 (arXiv:2411.10109), Bo et al. 2024 (arXiv:2412.15584), Haase et al.
  2026 (arXiv:2601.21339). P-SCA NOT cited (no verifiable authoritative source). Elevated C1 to flip-rate.
- **D5.57 Q1 persona-induction**: audit HIGH catch → claim NARROWED. Only the neutral **background-only**
  arm (D5.43) is a true deference-free control (p5 muted 0.65 but still weak top, ordering ρ=0.89);
  backstory/demonstration are alternative deference ENCODINGS, not controls (must not be used as
  anti-circularity evidence).

## 4. IN-FLIGHT right now (successor: pick this up first)
- **LSAT run** (async, shellId may be gone after retirement): `scripts/analysis/lsat_panel.py --config
  configs/lsat_axis2.yaml` → `results/lsat_axis2.json`. 6 backends × {Conf., dark} × 6 personas × 20 LSAT
  items; multiple-choice (4-way); dark = AI recommends a guaranteed-wrong option. Log: `lsat_run.log`.
  ~4–6 h total; resumable (cache-backed). **When done:** write a small analysis mirroring adopt/flip/coverage
  for the multiple-choice records (adopt = final==ai_advice on dark; s1_correct = system1==truth), get an
  INDEPENDENT audit, then integrate as a task-structure-generalization paragraph (answers "only one task
  family / binary sentiment" critique). No paper text for LSAT yet.
- **Queue is otherwise empty**; all other harnesses/configs already run.

## 5. n=11 expansion — exact honest numbers (for paper/rebuttal)
Backends (11): existing 6 (gpt-4o-mini, gpt-4.1, gpt-4o, gpt-5.5, claude-sonnet-4.5, gemini-2.5-pro) + new 5
(gpt-3.5-turbo, gpt-4, gpt-5.4, claude-opus-4.6, gemini-3.1-pro). **claude-haiku-4.5 EXCLUDED** (0 parseable
decisions, 3 attempts incl 4096 tokens — instrument failure, disclosed).
- capability(S1 acc) vs, pooled both datasets, BH over 3-test family:
  agg_adopt ρ=−0.82 BH p=0.006 **ROBUST** (sig each domain; jackknife worst-case p=0.01);
  flip ρ=−0.67 BH p=0.030 **SUGGESTIVE** (amzbook-carried; beer-only n.s.; drop gpt-4.1 → p=.087);
  p5 ρ=−0.65 BH p=0.030 **SUGGESTIVE** (drop gpt-5.5 → p=.094).
- Coverage (load-bearing, assumption-light): single frontier covers **1/9**; capability-first needs **k=10**;
  greedy k=1–2. Unchanged by expansion.
Data: results/axis2_expand12_{beer,amzbook}.json + _beer_fix.json (gemini-3.1). Analysis:
scripts/analysis/expand12_analysis.py → results/expand12_analysis.json. Fig: fig6b_expand11.

## 6. Environment / compute (critical)
- `$env:GH_TOKEN=$null` before any gh; `$env:PYTHONPATH=(Resolve-Path .\src).Path` before python.
- Proxy: `ghc-api` at http://127.0.0.1:8787/v1 — **serial only** (429 under concurrency), throttle
  inter_call_sleep≥2s, resumable (cache-backed in data/cache/panel). Reasoning models
  (gpt-5.x, gemini-*-pro) NEED token_param=max_completion_tokens + min_completion_tokens≥4096.
  claude-haiku-4.5 unusable (prose, no parseable decision).
- run_multigen.py rewrites its whole output_file per slice → rerun failed backends to a SEPARATE file and
  merge in analysis.
- Paper build: MiKTeX pdflatex at C:\Users\v-elzhang\AppData\Local\Programs\MiKTeX\miktex\bin\x64;
  sequence pdflatex→bibtex→pdflatex→pdflatex. **ALWAYS rebuild+commit main.pdf after any main.tex edit.**
- **NEVER fabricate BibTeX** — verify every cite against arXiv/ACL/DOI (this session caught web-search giving
  WRONG author lists for all 3 novelty cites; verified against authoritative sources before adding).

## 7. Rigor contract (keep doing this)
Every analysis feeding the paper gets an INDEPENDENT audit (code-review subagent) + Manager numeric
re-derivation BEFORE integration. This session the auditor caught 4 would-be overclaims: BH not called;
jackknife-fragility of flip/p5; (earlier) a capability-order reversed() bug; Q1 circularity. Preregister
frozen success criteria in docs/plans/ BEFORE running; report all directions incl. nulls/refutations.

## 8. Highest-leverage next steps (PI-level judgment)
1. **Finish LSAT** → analyze → audit → integrate (closes the task-family critique). ~1 session.
2. **E6 human study** — STILL the single decisive lever (only thing that lifts acceptance past ~40%→~50-60%).
   Design exists: docs/plans/e6-stripped-axis2-design.md. It is a PI decision to run/preregister/recruit.
3. Optional polish: fig6 (6-backend) vs fig6b (11-backend) — consider consolidating; camera-ready bib page
   numbers.
Honest acceptance estimate (synthetic-only ceiling): ~35–40%. E6 is the gate to >50%.

## 9. Owner preferences (must honor)
- Reply in **Chinese (中文)**. Owner = @EloiseJulia.
- Caution on big/confirmatory runs: verify effect first, control budget, lean on cache, no re-runs, no
  scaling without explicit sign-off. Preregister + freeze criteria before results; report qualified negatives
  honestly. Integrity over cosmetically-stronger numbers (declined a cherry-pick-8-of-12 request).
- PI decisions reserved for owner: gates / methodology disputes / framing / venue / E6. Everything else the
  manager decides, logging each non-trivial change in docs/DECISIONS.md.
