# Quota Strategy — unlocking the powered axis-1 (headline) result

> **Date:** 2026-07-15 · Author: Manager/PI session · Status: PLAN (pure planning, no code).
> Purpose: make large panel runs tractable given GitHub Models' per-model DAILY cap, so we
> can power axis-1 (C1, now the PRIMARY contribution) and add cross-model triangulation.
> Companion to SPEC §4.2 (multi-family panel) and the Known pitfalls / daily-cap memory.

## 1. The constraint (empirically established 2026-07-15)
- **GitHub Models enforces a per-USER, per-MODEL DAILY request cap ≈ 500/day**
  (`429`, header `x-ratelimit-type: UserByModelByDay`, `Retry-After` ≈ 18–19 h). This is
  SEPARATE from — and far below — the per-minute burst limit (10k–60k/window).
- We exhausted **gpt-4o-mini** and **gpt-4.1-mini** today (~450–500 calls each). As of now,
  **gpt-4o, meta/Llama-3.3-70B-Instruct, microsoft/Phi-4 still have fresh daily budget**
  (each model has its OWN bucket). Rotating the PAT does NOT reset the cap (it is per-user).
- Sustainable pacing per model ≈ **1.5 req/s** (burst bucket ~20, then throttle); the
  provider paces at 0.8 s and now **fails fast** on a daily-cap `Retry-After` (120 s cap)
  and **caches every completed call** (so any run is resumable for free).

## 2. Demand estimate for the headline "powered axis-1" run
Axis-1 H1a needs the disagreement→over-dispersion relationship across **≥5 UI conditions**
(the cross-condition correlation is degenerate below n=3–5), with enough personas (between-
user variance) and enough items (conflict-trial power). A defensible target:
- **8 personas × 40 diverse hard items × 5 Bansal AI conditions × 1 seed.**
- Calls per model = System-1 (shared across conditions) + System-2:
  - System-1 = 8 × 40 = **320**; System-2 = 8 × 40 × 5 = **1,600** → **~1,920 calls/model**.
- Cross-model triangulation (SPEC §4.2) wants **≥3 model families** → **~5,760 calls** total.
(A leaner first cut: 6 personas × 30 items × 5 conditions ≈ 1,080/model.)

At ~500/model/day, one model's 1,920 calls = ~4 days; but different models run against
DIFFERENT daily buckets IN PARALLEL, so 3 models finish in ~4 days wall-clock (not 12).
Caching makes any interrupted run resume at zero cost.

## 3. Four levers (use in combination)
### Lever A — Multi-family panel (quota AND science align) ★ primary
The daily cap is per-model, so **spreading the panel across model families multiplies daily
budget** — and this is EXACTLY the multi-family panel SPEC §4.2 already requires (distinguish
preference-driven vs capability-noise disagreement; cross-family robustness). So the quota
workaround is a scientific upgrade, not a hack.
- Candidate families (verify budget the day of the run): `openai/gpt-4o`,
  `openai/gpt-4o-mini`, `openai/gpt-4.1-mini`, `meta/Llama-3.3-70B-Instruct`,
  `microsoft/Phi-4` (+ others on the Marketplace: mistral, cohere, deepseek — verify).
- **Design coherence:** a model is a distinct AGENT — do NOT split one condition's calls
  across models arbitrarily. Use models AS panel members / capability tiers. Report per-model
  and pooled signals.
- **Provider already supports this** (`model_name` param, per-model cache keys). Add a small
  multi-provider run loop (config lists models; run each; cache dedups).

### Lever B — Caching + resumable day-batching ★ primary
- The hashlib response cache persists across runs and processes; System-1 is computed once
  and frozen across conditions; counterfactual pairing reuses it. **Maximize cache hits.**
- **Batch by day:** run until the daily cap hits (provider fails fast), then resume next day;
  cached calls cost 0, only new calls count. Make every experiment resumable (they already
  are). Track per-model "calls used today" to stop before the cap where possible.

### Lever C — Azure AI Foundry fallback (removes the cap; PI action) ★ for a single-session full run
- The `ModelProvider` protocol lets us drop in an `AzureFoundryProvider` (OpenAI-compatible)
  with **no daily cap** (pay-per-token, high throughput). This is the clean unlock for a full
  powered run in one sitting.
- **Cost is small:** ~1,920 calls × ~700 tok ≈ 1.3 M in + 0.4 M out per model. gpt-4o-class
  ≈ **$5–15/model**; a mini tier ≈ **$1–3/model**. A full 3-model run ≈ **$15–45 total**.
- **PI action required:** create an Azure AI Foundry (or Azure OpenAI) deployment + endpoint
  + key; put the key in an env var (e.g. `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT`), never
  commit it. Then a subagent implements `AzureFoundryProvider` (a thin slice).

### Lever D — Pacing / limited concurrency
- Keep 0.8 s pacing per model; on 429-daily, fail fast (done). Across DIFFERENT models
  (different buckets) we may run **a few models concurrently** to raise wall-clock throughput
  within a day — with care (separate processes, cache-safe writes).
- Local/open-weight (vLLM) is a further option but needs a GPU the PI can't easily provision;
  list as future, not near-term.

## 4. Rigor / preregistration implications (do not skip)
- **Freeze the panel model set BEFORE seeing results** (prereg): which families, which
  capability tiers, and the pooling rule. Post-hoc model selection = researcher DoF.
  Record the frozen model list + rationale in PROGRESS §Preregistration with a UTC timestamp.
- τ_disp / τ_level stay UNFROZEN until the calibrated run; freeze in feature space before
  results (unchanged).
- Report per-model results + the cross-family agreement (only trust cross-family-consistent
  flags, SPEC §4.2). Contamination/cutoff caveats per model.

## 5. Recommended plan (decision for the PI)
**Option 1 — GitHub Models, multi-family, day-batched (free, ~3–4 days wall-clock).**
- Preregister a 3-family panel (e.g. gpt-4o + Llama-3.3-70B + Phi-4), 6–8 personas × 30–40
  items × 5 conditions. Run one family/day per bucket; cache resumes. Zero cost.
- Pro: free, adds real cross-family science. Con: multi-day; must track buckets.

**Option 2 — Azure Foundry, single sitting (~$15–45, ~1–2 h).** ← recommended if the PI can
provision Azure.
- Implement `AzureFoundryProvider` (thin slice), run the full powered matrix at once, no cap.
- Pro: fast, clean, powers axis-1 immediately. Con: needs PI to set up Azure creds + small $.

**Hybrid (pragmatic):** Do a **leaner GitHub-Models multi-family pilot NOW** (fits today's
fresh budgets: gpt-4o / Llama-3.3-70B / Phi-4, ~300–400 calls each) to de-risk the powered
design + get a first cross-family axis-1 read, THEN scale via Azure (Option 2) for the
publication-grade run.

## 6. Immediate items unlocked
- **E4 (PR #7) resume:** either (a) wait ~19 h for gpt-4.1-mini reset and finish the cached
  ~190/450 for model-consistency with PR#4, OR (b) if the PI wants it NOW, re-run E4 on a
  fresh family (gpt-4o has budget) — accept a model-switch caveat (loses the 190-call cache;
  ~450 fresh calls). Recommend (a) unless E4 is urgent.
- **Next headline slice (axis-1 powered + first cross-condition correlation):** blocked only
  on the PI's Option-1-vs-Option-2 choice above. Everything else (code, cache, provider,
  item selector, conflict-conditioned DV, betabinom over-dispersion) is ready or a thin add.

## 7. Concrete next actions
1. PI: choose Option 1 (free/multi-day) vs Option 2 (Azure/fast/$15–45) vs Hybrid.
2. If Azure: PI provisions endpoint+key (env vars); Manager dispatches an `AzureFoundryProvider`
   thin slice (audit-gated).
3. Manager: preregister the frozen panel model set + matrix (timestamped) BEFORE the run.
4. Manager: implement the multi-provider run loop (small add to the experiment; config lists
   models) + a per-model daily-budget tracker; run day-batched or via Azure.
5. Manager: run powered axis-1 (over-dispersion betabinom on the conflict DV + cross-condition
   disagreement→over-dispersion correlation over ≥5 conditions) → audit → merge.
