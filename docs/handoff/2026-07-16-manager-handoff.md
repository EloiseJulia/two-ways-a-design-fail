# Manager Handoff — two-ways-a-design-fail

> **Date:** 2026-07-16 · **Retiring Manager → fresh Manager.**
> Launch prompt for successor: `docs/manager-prompt-v3.md`. Read-only watcher:
> `docs/watch-prompt.md`. Single sources of truth: `SPEC.md` (design), `INTERFACES.md`
> (contracts), `PROGRESS.md` (progress + prereg freeze log), **`docs/DECISIONS.md`
> (chronological paper-oriented change log — READ THIS for the "why" of every pivot).**
> Read those + this doc + `docs/handoff/RESUME-CHECKLIST.md` first.

---

## 1. PROJECT STATE (one paragraph)
The data→panel→metrics→result chain is proven end-to-end on REAL data through an
audit-gated multi-agent workflow; **7 PRs merged** (#1–#6, #9). The paper's contribution
structure has been RESOLVED by the data: **C1 (the agent-panel two-axis triage) is now the
PRIMARY contribution**; the earlier headline C0 (AI assistance turns reliance from a stable
user trait into user×task) has been **demoted to a Bansal-specific supporting finding**
because it did not generalize to Lu&Yin and a matched-subset discriminator was inconclusive
(ceiling artifacts). The real LLM panel initially produced a NULL (compliance-collapse),
which a redesign fixed (conflict-conditioned DV): conflict rate 3%→43%, personas diverge,
explanation elasticity +0.19 (underpowered), and a first axis-2 wrong-AI over-reliance signal
(0.325) plus a dark-pattern-backfire lead. **The powered, confirmatory axis-1 run has NOT yet
happened** — it is the single most important next deliverable. GitHub Models' per-model daily
cap (~200 strong / ~500 mini) and the instability of non-OpenAI families block a large run;
an `AzureFoundryProvider` was built and merged as the uncapped path, and the PI has decided to
run the confirmatory on GitHub's STABLE OpenAI family (gpt-4o + gpt-4.1-mini), day-batched, to
"keep going free" without blocking on Azure. Two draft PRs are open and IN FLIGHT: **#7 (E4
axis-2 sensor + placebo, code done, real run partially cached 193/450)** and **#8 (exploratory
multi-family pilot, code done, real run produced only noisy non-OpenAI data — see limitation).**
τ_disp/τ_level remain UNFROZEN (correct). main @ **d67f40e**.

## 2. COMPLETED (merged PRs + key numbers)
- **PR #1 `vslice-v0` (e5a257b):** Bansal loader → canonical schema → beta-binomial
  over-dispersion + genuine mean-predictor baseline + synthetic panel stub → E1 runner.
  Human over-dispersion ρ≈0.037 [0.009,0.068] (10-task). The 2-condition r=±1 flagged
  degenerate. (Fixed a `hash()` non-determinism pitfall.)
- **PR #2 `e1-multicond` (9ac818f) + robustness + variance-decomposition:** axis-1 across all
  6 Bansal conditions. **Axis-1 over-dispersion is REAL:** Human ρ=0.067 [0.052,0.081], excludes
  0; known-signal sim shows the estimator is unbiased at 4 trials/user (not a power artifact).
  **Variance decomposition (split-half, PRIMARY):** no-AI reliance = stable user trait
  (stable_user_share **0.74** [0.69,0.79]); AI-assisted = predominantly user×task (**0.32–0.41**;
  Expert ~0). GLMM did NOT converge (reported honestly). H1a refined accordingly (b48ab2b).
- **PR #3 `moduleB-panel` (52fb53c):** first REAL LLM panel via GitHub Models (counterfactual
  pairing, hashlib cache). Result = **NULL / compliance-collapse:** 97% of cells the agent never
  moved from its own System-1 anchor; measured "reliance" ≈ agent↔AI agreement, not adoption;
  persona disagreement ≈ 0. Diagnosed by Manager as a real mechanism, not a bug.
- **PR #4 `panel-redesign` (9caebc5):** conflict-conditioned reliance DV (System-1 ≠ AI trials)
  + data-driven hard-item selection + stronger persona conditioning + a WRONG-AI dark condition.
  **Resolves the collapse:** conflict rate 3%→**43.3%**; conflict-conditioned reliance control
  0.327 → treatment 0.481; per-persona spread **0.11–0.56** (personas diverge); within-task
  explanation elasticity **+0.19 (p=0.17, n=11 — UNDERPOWERED)**; **axis-2 wrong-AI over-reliance
  = 0.325**; System-1 acc 0.82; frozen invariant holds. Anomaly (audit-confirmed genuine):
  persona p5 adopts **0%** wrong-AI under the coercive dark framing (vs 0.556 control) —
  **dark-pattern-BACKFIRE lead** for axis-2. Model: gpt-4.1-mini (gpt-4o-mini daily-exhausted).
- **PR #5 `luyin-decomp` (4364d54):** replicate the split-half decomposition on Lu&Yin.
  **AI-assisted reliance is TRAIT-STABLE there: stable_user_share 0.80** [0.77,0.83]
  (unconditional) / 0.79 (conflict-conditioned) — near Bansal's no-AI 0.74, NOT its AI 0.32–0.41.
  ⇒ the AI-assisted user×task share is **NOT universal**. Comparison is confounded (Lu&Yin has
  no no-AI arm; sequential-feedback + homogeneity + accuracy differ). C0 HELD pending mechanism test.
- **PR #6 `bansal-discriminator` (50250e6):** re-decompose Bansal on Lu&Yin-matched subsets.
  **INCONCLUSIVE** — 2 of 3 domains (beer/amzbook) are **ceiling/low-variance artifacts**
  (between-user SD ≈ 0.05 → split-half ≈ 0, uninterpretable); the only interpretable matched
  subset (lsat, SD ≈ 0.14) rose only partway (**0.46** [0.31,0.59], CI overlapping the 0.33
  baseline). Gap remains confounded/unresolved. (Manager corrected an OVERSTATED subagent
  "clean persist" verdict; audit independently reproduced the SDs.)
- **PR #9 `azure-provider` (5cd179b):** `AzureFoundryProvider` — drop-in `ModelProvider` for
  Azure OpenAI + Foundry (two api styles), env creds, replicated hashlib cache (deployment in
  key → no collision), 22 offline mock tests, `docs/plans/azure-setup.md`. Audit PASS. Unlocks
  an uncapped confirmatory run once the PI provisions Azure creds. (Cache logic is replicated,
  not shared — future refactor noted, non-blocking.)

## 3. CONTRIBUTION STRUCTURE (current, PI-approved)
- **C1 = PRIMARY:** the agent-panel two-axis triage signal — axis-1 (disagreement →
  over-dispersion, user-sensitive) + axis-2 (systematic over-reliance on WRONG AI, uniformly
  lethal / dark). Preliminary real-panel evidence from PR #4. **Needs the powered confirmatory
  run to land H1a.**
- **C2 = support:** counterfactual reliance elasticity (frozen-persona paired UI swap).
- **C0 = DEMOTED** to a Bansal-specific supporting finding (no-AI stable trait 0.74 → AI
  user×task 0.32–0.41). NOT shown to generalize (Lu&Yin 0.80; discriminator inconclusive).
- **OPEN QUESTION (not a claim):** is reliance-stability **regime-dependent** — does
  **sequential feedback** (Lu&Yin) drive a stable trust policy vs static settings (Bansal)
  yielding user×task? Future §4.1 sequential-stateful (Bayesian-trust) study. Deferred.

## 4. IN FLIGHT (not merged)
- **PR #7 `e4-compliance` (branch @ f670b97):** E4 axis-2 dark-pattern sensor + PLACEBO
  compliance baseline (4 conditions: control/faithful/placebo/wrong-AI). Code + 8 offline tests
  DONE. Hypotheses to read out: H3 compliance floor **control < placebo < faithful**
  (conflict-conditioned) + a formal axis-2 `over_reliance_level` on wrong-AI, and a
  placebo-baselined "compliance-adjusted" axis-2. **Real run PARTIAL: 193/450 calls cached on
  gpt-4.1-mini** (its daily bucket was shared with the pilot and exhausted). RESUME after the
  gpt-4.1-mini daily window resets: bridge token, `python -u -m twdf.experiments.e4_compliance
  --config configs\e4_compliance.yaml` from the worktree (cache makes the remaining ~257 calls
  the only cost). Then audit → merge. (A resume schedule existed but was STOPPED at retirement
  to avoid orphaned wakeups — the next Manager resumes manually.)
- **PR #8 `axis1-pilot` (branch @ bba48dc):** EXPLORATORY multi-family axis-1 pilot — 5 Bansal
  condition renderers (LIME-based; Single/Double/Adaptive use documented heuristics — flag for
  confirmatory firming-up), multi-provider loop with **skip-on-cap resilience**, cross-family +
  power-analysis readout. Code + 9 offline tests DONE. **Real run did NOT yield a usable
  power/effect estimate:** gpt-4.1-mini skipped (capped), and Llama-3.3-70B/Phi-4 produced
  timeouts/500s/**unparseable outputs (defaulted to 0)**. `results/axis1_pilot.json` was NOT
  produced. **Takeaway (kept):** non-OpenAI families are unstable on GitHub Models → provider-
  stability limitation → confirmatory model set amended to stable OpenAI family (see §6). The
  pilot's power-N purpose is UNMET; get N from a clean exploratory pass on the amended stable
  set (or Azure) before the confirmatory run. The pilot cache holds 446 (mostly Llama/Phi noise).

## 5. ENVIRONMENT
- Windows + PowerShell. Python 3.12 (`...\Python312\python.exe`); `uv` absent → use `pip`.
- **Secret:** `GH_MODELS_TOKEN` — persistent User env var (rotated 2026-07-16, verified
  authenticates). Read from env only; NEVER print/commit its value. Bridge into subagent/child
  env at launch: `$env:GH_MODELS_TOKEN=[Environment]::GetEnvironmentVariable('GH_MODELS_TOKEN','User')`.
- **`gh` GOTCHA:** an env var `GH_TOKEN` (account `v-elzhang_microsoft`) HIJACKS `gh` and makes
  it fail to resolve the `EloiseJulia/two-ways-a-design-fail` repo. **Run `$env:GH_TOKEN=$null`
  before every `gh` command** so gh uses the EloiseJulia keyring account. (git push works fine.)
- **GitHub Models batch API (VERIFIED):** `POST https://models.github.ai/inference/chat/completions`,
  `Authorization: Bearer $GH_MODELS_TOKEN`, OpenAI-compatible body. Model ids e.g.
  `openai/gpt-4o`, `openai/gpt-4.1-mini`, `openai/gpt-4o-mini`, `meta/Llama-3.3-70B-Instruct`,
  `microsoft/Phi-4`.
- **DAILY quota (CRITICAL):** per-user-PER-MODEL daily cap (`429`, header
  `x-ratelimit-type: UserByModelByDay`), **TIER-DEPENDENT: strong models ~200/day, mini ~500/day**.
  Separate from the per-minute burst (~1.5 req/s sustainable). Provider **fails fast** if the
  429 cooldown > 120s (daily cap) and CACHES completed calls → any run is resumable for free.
  Spread across model families (separate buckets) + day-batch for scale; or use Azure (no cap).
- **Azure (NOT yet provisioned):** the PI must set env vars — **names only:**
  `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, `AZURE_OPENAI_API_VERSION`,
  `AZURE_OPENAI_DEPLOYMENT`. Steps in `docs/plans/azure-setup.md`. Then `AzureFoundryProvider`
  is a drop-in for `GitHubModelsProvider`. Recommend one `pytest -m live
  tests/test_azure_provider.py` cred check (~$0.001) before a big run.
- **Build:** `pip install -e .` (numpy, pandas, scipy, pyyaml, statsmodels, requests; dev: pytest).
- **Test:** `pytest -m "not live"` (offline; live tests need a token/Azure creds and are skipped).
  Cross-process determinism tests use subprocesses + are skip-safe on cold cache/quota.
- **Run (real artifacts):** each experiment is `python -m twdf.experiments.<name> --config
  configs/<name>.yaml` (`e1_vslice`, `e1_multicond`, `e1_robustness`, `e1_decomposition`,
  `luyin_decomposition`, `bansal_discriminator`, `e2_panel_redesign`, `e4_compliance`,
  `axis1_pilot`). Run unbuffered (`python -u`, `$env:PYTHONUNBUFFERED="1"`) for live logs.
- `data/raw/` + `data/cache/` gitignored (loaders auto-download; hashlib response cache in
  `data/cache/panel/`). `results/*.json` committed. Logs in `.copilot-logs/` (gitignored).
- **Worktree/branch conventions:** slices in `.worktrees/<name>` on `feature/<name>`; early
  DRAFT PR (empty bootstrap commit); squash-merge + `--delete-branch`; subagent prompts in
  `.prompts/` (COMMITTED for continuity). Only the Manager touches git on main + runs
  `gh pr merge` (with `$env:GH_TOKEN=$null`).
- **Subagent dispatch:** `copilot -p (Get-Content .\.prompts\<name>.md -Raw) --allow-all
  --name <name> --model claude-sonnet-4.5 --log-dir .\.copilot-logs`. Bridge token first. For
  long API runs, the Manager should RUN THEM ITSELF (detached) — subagents die mid-run on long
  API loops (hit repeatedly); build code + offline tests via subagent, run the experiment yourself.

## 6. PREREGISTRATION STATUS (`docs/plans/preregistration-axis1.md`; log in PROGRESS)
- **LOCKED a-priori 2026-07-15T09:23:55Z (before the pilot ran):** H1a; conflict-conditioned DV
  + beta-binomial over-dispersion; ≥5 Bansal conditions; 4 baselines (random, mean-predictor,
  prompt-only, single-model) + rational-Bayes null; BH **α=0.05** (ratified); within-task
  difficulty-controlled estimator (primary) + cross-condition Spearman (secondary). Pilot data
  EXCLUDED from confirmatory.
- **AMENDMENT 2026-07-16T02:29:50Z (PI, provider-stability driven, NOT effect-driven):**
  confirmatory model set changed {gpt-4o, Llama-3.3-70B, Phi-4} → **{gpt-4o, gpt-4.1-mini}**
  (stable OpenAI family on GitHub Models, DAY-BATCHED). Invoked the pre-committed PIPELINE-only
  exclusion rule (non-OpenAI models: timeouts/500s/unparseable→0). Non-OpenAI = exploratory-only,
  documented as a provider-stability limitation. Cross-vendor triangulation deferred to Azure.
- **STILL UNFROZEN — must be frozen BEFORE their respective results:**
  - **Power target N** (§8) — from a CLEAN exploratory pass (amended stable set / Azure); the
    GitHub pilot did NOT deliver it. Fill §8 + record a freeze timestamp BEFORE the confirmatory run.
  - **τ_disp / τ_level** — learned ONCE in the atomic-feature space (Module D), frozen with a UTC
    timestamp BEFORE any threshold results. This axis-1 confirmatory run tests H1a and does NOT
    set τ. Post-hoc τ tuning = misconduct.

## 7. OPEN QUESTIONS / RISKS
- **Powered axis-1 confirmatory not done** — the paper's primary (C1) result is still pending.
  Blocked only on compute: run day-batched on {gpt-4o, gpt-4.1-mini} (free) or on Azure (fast).
- **Sequential-feedback mechanism** (C0 open question) — needs the §4.1 sequential-stateful mode.
- **Panel realism / calibration** — personas are synthetic proxies; single domain (beer),
  small item counts; elasticity underpowered (n=11). Powered run + more diversity needed.
- **5-condition renderer fidelity** — Single/Double/Adaptive use documented LIME heuristics
  (Bansal's exact selection algorithm not fully specified). Firm up / sensitivity-check before
  confirmatory conclusions rest on cross-condition rank.
- **Model-mix confound** — PR#4/E4 ran on gpt-4.1-mini; a confirmatory on gpt-4o+gpt-4.1-mini is
  not same-model-comparable to earlier slices. Report per-model; don't pool across incomparable models.
- **Axis-2 / E4 not merged** — the second axis of the two-axis claim needs E4 finished.
- **Lu&Yin sequential mode + §4.3 atomic features + Module D calibration** — not started.
- **Cache logic duplicated** across the two providers (maintenance risk; non-blocking).

## 8. NEXT PLANNED WORK (ordered backlog)
1. **Resume E4 (PR #7)** on gpt-4.1-mini after daily reset (193/450 cached) → audit → merge.
2. **Clean exploratory pass for POWER N** on the amended stable set {gpt-4o, gpt-4.1-mini}
   (day-batched) — reliable parse — to size the confirmatory run. Fill prereg §8 + re-freeze.
3. **Merge PR #8** (pilot) as EXPLORATORY infrastructure + the provider-stability limitation
   (its run yielded no clean estimate; keep the renderers + multi-provider loop + skip-on-cap).
4. **Run the CONFIRMATORY axis-1** (H1a) on {gpt-4o, gpt-4.1-mini}, day-batched (or Azure if
   creds arrive): beta-binomial over-dispersion on the conflict DV + within-task
   difficulty-controlled estimator + cross-condition Spearman over the 5 conditions; beat the 4
   baselines; BH α=0.05; bootstrap over (personas×seeds×models). **Report regardless of outcome.**
5. **§4.3 atomic UI features (UIFeatureVector)** → **Module D calibration + FREEZE τ (prereg)**
   + abstention → **E3 LOIO (watch leakage!)** + **E5 ECE/radius**.
6. Cross-vendor triangulation + §4.1 sequential mode (C0 upside) — once Azure is available.

## 9. KNOWN PITFALLS (hit or anticipated)
- **Builtin `hash()` non-deterministic across processes** → always `hashlib`. Hit ≥twice. grep
  `\bhash\(` before merge. Determinism tests must be CROSS-PROCESS (subprocess), and skip-safe.
- **Bernoulli mean–variance coupling** → DV must be beta-binomial OVER-DISPERSION (excess over
  p(1−p)), never raw variance; the mean-predictor baseline must be genuine and actually beaten.
- **CEILING / low-variance artifacts** (PR#6): near-ceiling reliance (SD≈0.05) makes split-half
  ≈0 mechanically — UNINTERPRETABLE, not "user×task". Always check between-user SD before
  interpreting a low reliability share.
- **Task-difficulty confound** → within-task counterfactual differencing (difficulty cancels),
  not pooled correlation. Bansal domain is BETWEEN-subjects.
- **Degenerate correlation** over n<3 conditions = ±1 by necessity → guard/flag (n<3 guard exists).
- **Single-obs-per-cell (99.7%)** → ANOVA-on-cells NON-identified; split-half is the valid primary.
- **Model-mix confound** → don't pool axis-1 across models of different capability; report per-model.
- **Researcher DoF / preregistration** → freeze model set, N, τ BEFORE their results; log every
  change with reason + timestamp (see the §2 amendment as the template). Pilot data must NOT feed
  the confirmatory except the pre-declared power-N estimate.
- **Item selection must use AI-side EXOGENOUS properties** (AI wrong / low conf / high human
  reliance-variance for LOCATING heterogeneity) — human outcomes/reliance are NEVER put into agent
  prompts or used as a predictor. Item selection ≠ label leakage (disclosed).
- **LOIO (E3) leakage** — normalization/threshold params must be fit on TRAIN split only.
- **Subagent process pitfalls** — they (a) die mid-run on long API loops, (b) run out of turns,
  (c) leave scratch / dirty worktree, (d) sometimes OVERSTATE verdicts (caught twice: panel-null
  mechanism, discriminator ceiling artifact). Manager runs long experiments itself; independent
  audit + Manager verification is the gate; restore timestamped `results/*.json` + remove scratch
  before every merge.
- **GitHub Models daily cap + non-OpenAI instability** — see §5; plan compute accordingly.

## 10. REPO STATE (at handoff)
- Branch `main` @ **d67f40e** (this handoff commit adds more). Synced with origin.
- **Open DRAFT PRs:** #7 `feature/e4-compliance` (E4), #8 `feature/axis1-pilot` (pilot).
- **Worktrees:** `.worktrees/e4-compliance` (@ f670b97), `.worktrees/axis1-pilot` (@ bba48dc).
  Both have populated caches (e4 193, pilot 446) — do NOT delete before resuming/merging.
- No background jobs running (pilot process + E4 resume schedule STOPPED at retirement).
- `.prompts/` holds all subagent prompts (committed). `docs/manager-prompt-v3.md` +
  `docs/watch-prompt.md` are the successor launch + watcher prompts (committed with this handoff).

---
### SINGLE MOST IMPORTANT THING
The paper's PRIMARY contribution (C1 axis-1) still has **no powered confirmatory result** — get
it, honestly, next: (1) a CLEAN power-N pass on the amended stable OpenAI set, freeze §8 N + τ
discipline BEFORE results, then (2) the confirmatory run, reported regardless of outcome. And
never let a subagent's confident verdict stand without independent audit + your own numeric
re-derivation (we caught two overstated verdicts this way). Keep exploratory strictly separate
from confirmatory; log every prereg change with a timestamp.
