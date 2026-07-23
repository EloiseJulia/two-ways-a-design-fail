# Backend expansion to n=12 (preregistration) — HONEST full reporting

**Frozen:** 2026-07-23, before any new-backend results seen. PI-approved (owner "n=12就12吧").
Decision log: D5.51.

## Motivation
Reviewer/PI concern: n=6 backends leaves the capability↔vulnerability correlation underpowered
(Spearman directional but n.s.). Fix by adding backends and **reporting ALL of them** — no subset
selection. (An explicit cherry-pick-8-of-12 request was DECLINED as selective reporting that would
contradict the paper's own researcher-DoF thesis and preregistration contract; see D5.51 note.)

## Frozen backend set (12; report every one, regardless of fit)
Existing 6: gpt-4o-mini, gpt-4.1, gpt-4o, gpt-5.5, claude-sonnet-4.5, gemini-2.5-pro.
New 6 (smoke-tested working on the ghc-api proxy 2026-07-23):
| backend | vendor | token param | intended tier |
|---|---|---|---|
| gpt-3.5-turbo | OpenAI | max_tokens | weak / old |
| gpt-4 | OpenAI | max_tokens | mid / old |
| gpt-5.4 | OpenAI | max_completion_tokens (min 4096) | strong |
| claude-haiku-4.5 | Anthropic | max_tokens | small |
| claude-opus-4.6 | Anthropic | max_tokens | strong |
| gemini-3.1-pro-preview | Google | max_tokens | strong |
(claude-opus-4.5 was dropped — HTTP 400 on the proxy; replaced by the working claude-opus-4.6.)

## Frozen protocol
- Conditions: `Conf.` (faithful, for S1 + RAIR/RSR) and `Wrong-AI-GT (dark)` (coverage / adoption).
- Personas: the 6 policy personas p1..p6 (p5-novice-trusting = at-risk), matched to the main axis-2 run.
- Items: 20, seed 2024. Generation seed 42. Domains: **beer first** (Phase 1), then amzbook (Phase 2).
- Capability proxy: **data-derived** — mean System-1 accuracy per backend (NOT release order; the paper
  already disowns release order). Secondary proxy (Q5): external authoritative benchmark (LMArena Elo /
  Artificial-Analysis Index / MMLU / GPQA), verified per-model before use; if a model has no clean public
  score (e.g. some proxy-only variants), it is reported as "external score unavailable", never fabricated.

## Frozen primary analyses (report ALL 12; no subset)
1. capability (S1 acc) vs vulnerability metrics (p5 dark adoption, AI-induced flip, coverage) across all 12
   — Spearman + BH; now powered at n=12.
2. Vulnerability-coverage set-cover at n=12 (single frontier vs coverage-greedy vs capability-first).
3. RAIR/RSR appropriate reliance across all 12.
4. Robustness of (1) under the external-benchmark capability proxy (Q5).

## Integrity rules (frozen)
- **Report every backend.** No dropping, no subset "n=8", no post-hoc exclusion. Heterogeneity across
  backends IS the finding, consistent with the paper's thesis.
- Preregister the set BEFORE results (this doc, committed pre-run). Independent audit + Manager
  re-derivation gate integration, as for every prior merge.
