# Manager Handoff — two-ways-a-design-fail

> **Date:** 2026-07-15 · **Retiring Manager → fresh Manager session.**
> Launch prompt for the successor: `docs/manager-prompt-v2.md`
> Single sources of truth: `SPEC.md` (design), `INTERFACES.md` (contracts),
> `PROGRESS.md` (progress + prereg freeze log). Read those + this doc first.

---

## 1. PROJECT STATE (one paragraph)
Two thin-vertical slices are merged to `main` and the data→metrics→result chain is
proven end-to-end on REAL Bansal CHI'21 data through an audit-gated multi-agent
workflow. Axis-1 (between-user reliance over-dispersion) is implemented, validated,
and shown to be a REAL signal (bootstrap CIs exclude 0). A variance-decomposition
sub-study established the key scientific nuance: **no-AI reliance is largely a
stable user trait, but AI-assisted reliance is predominantly user×task** — H1a has
been refined accordingly. The panel engine is still a SYNTHETIC STUB. The
immediate next work is **Module B: the real LLM panel via GitHub Models**
(`GH_MODELS_TOKEN` is now set as a persistent User env var, so it is unblocked).
No thresholds have been frozen yet (correct — no calibrated E1 run has happened).

## 2. COMPLETED (merged, with refs + key numbers)
### PR #1 — `vslice-v0` (squash commit `e5a257b`)
Thin slice: Bansal loader → canonical per-trial schema → **beta-binomial
over-dispersion** (separates true between-user over-dispersion from binomial noise)
+ genuine **mean-predictor baseline** (p(1−p), ρ=0 by construction) + synthetic
panel stub → E1 runner. Result (10-task subset): Human over-dispersion **ρ=0.0369
[0.0087, 0.0681]**, beats mean-predictor. The 2-condition Pearson r=±1 is DEGENERATE
(flagged plumbing-only, not evidence). Loop: impl → audit **FAIL** (B1 degenerate
corr, B2 non-reproducible numbers, B3 test import) → fix → reaudit **PASS** → merge.
B2 root cause: Python builtin `hash()` non-deterministic across processes → replaced
with `hashlib.md5`.

### PR #2 — `e1-multicond` + robustness + variance-decomposition (squash commit `9ac818f`)
Three linked pieces:
1. **Multi-condition E1** across all 6 Bansal UI conditions with a Spearman +
   permutation + bootstrap cross-condition correlation (still stub → mechanism
   check, NOT evidence).
2. **Robustness** (`results/e1_multicond_robustness.json`): Human over-dispersion
   by task-selection scheme — `all` (50 tasks, ~40 trials/user) **0.0666**;
   `first_10_shared` (v0, ~8/user) **0.0369**; `min_per_domain` (~4/user) **~0**.
3. **Adjudication** (power vs artifact; evidence preserved in the session files
   store `adjudication-*`): real-data bootstrap CIs EXCLUDE 0 (`all` [0.052, 0.081];
   `first_10` [0.009, 0.069]); a known-signal simulation showed the estimator is
   UNBIASED even at 4 trials/user (recovers ~0.064–0.068), so the collapse at few
   tasks is NOT power loss → it is **task-dependent (user×task) heterogeneity**, not
   a stable trait or an artifact.
4. **Variance decomposition** (`results/e1_decomposition.json`,
   `docs/research/2026-07-14-overdispersion-decomposition.md`): SPLIT-HALF
   reliability (primary; well-identified because each user sees 20–50 tasks) —
   stable_user_share (Spearman-Brown reliability), 95% CI:
   - **Human 0.74 [0.69, 0.79]** · Conf.+Double 0.41 · Conf. 0.36 ·
     Conf.+Adaptive 0.33 · Conf.+Single 0.32 · Conf.+Adaptive (Expert) ~0.
   - GLMM (`BinomialBayesMixedGLM`) did NOT converge (bounded maxiter=10; reported
     honestly as corroboration-unavailable; headline rests on split-half alone).
Loop: impl → audit **FAIL** (fragility + "stratified pooling" misnomer) → fix
(robustness + rename → `betabinom_overdispersion_within_domain`) → reaudit →
adjudication → **PI: decompose before merge** → impl/redo/finalize decomposition
(redo needed because first attempt used a non-identified ANOVA-on-cells method AND
weakened its tests) → pre-merge audit **CONDITIONAL PASS** (anti-gaming check:
auditor's OWN independent generators gave 0.894 / 0.199) → fix `hash()` determinism
blocker at `e1_multicond.py:117` → Manager independently verified cross-process
determinism (spearman 0.771429 identical ×2) → merge.

### Also on main
Gate commits (`d7ee878`, `37ed051`), gitignore (`cfced4c`), H1a refinement
(`b48ab2b`), PROGRESS merge logs.

## 3. KEY DECISIONS & RATIONALE
- **Gate 1 (data) — CLEARED, independently verified (HTTP 200 + real headers):**
  - Bansal: `https://raw.githubusercontent.com/uw-hai/Complementary-Performance/main/experiment-data/decision-result-filter.csv`
    (66,040 rows; cols assignmentId/questionId/condition/choice/y/pred/conf).
  - Lu&Yin: `https://raw.githubusercontent.com/ZhuoranLu/Trustworthy-ML/main/data/expOneFinalPredictionsValid1125.csv`
    (9,031 rows). **NOT yet used in code** — reserved for §4.1 sequential/dynamic-trust mode.
  - Detail: `docs/research/2026-07-14-dataset-availability.md`. Rationale: never let
    a subagent write the data pipeline before real URLs verified (avoid fabricated links).
- **Gate 2 (batch API) — CLEARED:** GitHub Models via fine-grained PAT in env var
  **`GH_MODELS_TOKEN`** (now set persistently). Azure AI Foundry = high-throughput
  fallback for full-scale E1; verify GitHub Models rate limits for the tier before scaling.
- **Gate 3 (PI ownership) — CLEARED:** PI owns scientific correctness; independent
  hostile + §4.5 methodology audit is the merge gate; nothing merges on "it runs";
  τ_disp/τ_level frozen (timestamped) BEFORE any results.
- **H1a refinement (PI-approved, commit `b48ab2b`):** keep axis-1 core, but state that
  the over-dispersion is, under AI assistance, predominantly **user×task** (not a
  stable user trait). WHY: the decomposition proved it, and it has a concrete
  consequence — the panel + disagreement→over-dispersion mapping must span DIVERSE
  tasks or the signal attenuates.
- **v0 = data→metrics on real data with a synthetic panel stub (defer live panel):**
  lowest-risk way to prove the chain without live-API dependency. (PI choice.)
- **Split-half as PRIMARY decomposition method:** because 99.7% of
  (condition,user,task) cells have exactly 1 observation, ANOVA-on-cells cannot
  separate user×task from Bernoulli noise; but 20–50 tasks/user makes split-half
  well-powered. A subagent that used ANOVA-on-cells AND weakened its validation
  tests was rejected and redone.

## 4. SCIENTIFIC FINDINGS (what matters, honest)
1. **Axis-1 over-dispersion is REAL on Bansal** (not a task-selection artifact):
   Human ρ=0.067, 95% CI [0.052, 0.081] on full data; still excludes 0 at 10 tasks.
2. **It is NOT merely estimator power loss** — known-signal sim recovers unbiased at
   4 trials/user; null sim stays at floor (estimator doesn't invent over-dispersion).
3. **Decomposition:** no-AI Human reliance is substantially a STABLE USER TRAIT
   (share 0.74); under AI assistance reliance becomes predominantly TASK-DEPENDENT
   (share 0.32–0.41; Expert ~0). Implication: axis-1 "who the user is" → "user×task"
   in the AI-assisted regime; interventions must account for task context.
   CAVEATS: single dataset (Bansal); GLMM corroboration pending; replication needed.
4. **Correlation numbers involving the panel are still STUB-based** (mechanism
   checks, explicitly non-evidential) until Module B lands.

## 5. PREREGISTRATION LOG
- **τ_disp — NOT YET FROZEN.** **τ_level — NOT YET FROZEN.** BH alpha proposed 0.05,
  not ratified. This is CORRECT: no calibrated E1 threshold-learning run has been
  done. Freeze both (with UTC timestamp, in PROGRESS.md §Preregistration) in the
  design feature space BEFORE looking at any threshold results. Post-hoc tuning =
  research misconduct.

## 6. OPEN QUESTIONS / RISKS
- **Module B design under the user×task finding:** the panel must see DIVERSE tasks;
  few-task sampling will hide the signal. Bake task diversity into the panel config.
- **GitHub Models rate limits** at the PI's tier for E1-scale (persona×task×UI×seed×
  model = tens of thousands of calls). Plan batching/caching + Azure fallback.
- **GLMM non-convergence:** acceptable for now (split-half stands), but a converged
  crossed-random-effects model would strengthen the decomposition; revisit with a
  higher compute budget / different optimizer.
- **Lu&Yin dataset unused** — needed for §4.1 sequential/dynamic-trust calibration.
- **Axis-2 (dark-pattern / systematic over-reliance) + E4 not started** — this is the
  other half of the two-axis claim; the paper's blind-spot closure depends on it.
- **Two manager prompts exist**: `docs/manager-prompt.md` (v1) and
  `docs/manager-prompt-v2.md` (v2, handoff-aware, principal-researcher). Use v2.

## 7. NEXT PLANNED WORK (ordered)
1. **Module B — real LLM panel via GitHub Models** (immediate next slice). Implement
   the `ModelProvider` protocol against GitHub Models using `GH_MODELS_TOKEN`
   (read from env, NEVER hard-code/commit); dual-system personas producing
   `AgentResponse`; counterfactual pairing (freeze System-1 state across the UI
   pair); span DIVERSE Bansal tasks. Replace the stub in the E1 chain; recompute a
   REAL disagreement→over-dispersion relationship. Start SMALL (few personas ×
   ~10–20 tasks × 1 UI pair × 1 model) to validate the loop and cost, then scale.
2. **Axis-2 dark-pattern sensor + E4 compliance baseline** (systematic over-reliance
   on wrong AI; must trigger high-risk even where over-dispersion ≈ 0).
3. **§4.3 atomic feature extraction** (UIFeatureVector) for feature-space calibration.
4. **Module D**: threshold learning + FREEZE τ_disp/τ_level (prereg) + abstention.
5. **E3 LOIO** (leave-one-intervention-out; watch leakage) and **E5 ECE/radius**.
6. Cross-model triangulation (multi-family panel); Lu&Yin sequential mode.

## 8. KNOWN PITFALLS (traps hit or anticipated)
- **Python builtin `hash()` is non-deterministic across processes** → always
  `hashlib.md5`. Hit TWICE (stub.py in v0; e1_multicond.py:117 in PR#2). grep
  `\bhash\(` (excluding comments/hashlib) before every merge.
- **Determinism tests must be cross-process** — a single-process double-call does NOT
  catch hash-seed nondeterminism. The decomposition added a subprocess-based test;
  reuse that pattern.
- **beta-binomial over-dispersion MUST separate true over-dispersion from binomial
  noise** — never raw variance. `betaln` lives in `scipy.special`, not `scipy.stats`.
- **mean-predictor baseline** must be genuine p(1−p) and actually beaten; do not water it down.
- **Task-difficulty confound**: use within-task diff, not pooled correlation. Domain is
  BETWEEN-SUBJECTS on Bansal (each user 1 domain) → use `within_domain` aggregation
  (do NOT mislabel it "stratified pooling").
- **Single-observation-per-cell (99.7%)** → ANOVA-on-cells cannot separate user×task
  from noise; use split-half (well-powered via 20–50 tasks/user).
- **Degenerate correlation**: Pearson over n<3 conditions is ±1 by necessity → guard/flag.
- **Over-dispersion needs adequate trials/user AND task diversity**; always report CIs.
- **Bansal condition-name strings** are exact: `Human`, `Conf.`, `Conf.+Single`,
  `Conf.+Double`, `Conf.+Adaptive`, `Conf.+Adaptive (Expert)`. Tasks/domains:
  `beer`, `amzbook`, `lsat`. An impl initially guessed wrong names.
- **CSV dtype**: pass explicit dtype for choice/y/pred/pred2 (mixed-type warning).
- **Preregistration**: freeze τ before results; never back-fill.
- **Process pitfalls (IMPORTANT for the Manager):** subagents (a) sometimes DON'T
  commit/push their deliverables, (b) run out of turns mid-run, (c) leave the
  worktree dirty (tracked `results/*.json` re-modified via the run_manifest
  TIMESTAMP field, plus scratch venvs / *.txt / audit reports). ALWAYS verify
  committed+pushed state yourself and CLEAN the worktree (git checkout tracked
  results, rm scratch) BEFORE `gh pr merge`. Never trust a subagent's self-report —
  independent audit + Manager verification is the gate.

## 9. ENVIRONMENT
- Windows + PowerShell. Python 3.12
  (`C:\Users\v-elzhang\AppData\Local\Programs\Python\Python312\python.exe`).
  `uv` NOT installed → use `pip`.
- Tools: `copilot` CLI, `gh` (authed as EloiseJulia), `git`.
- **Secret:** `GH_MODELS_TOKEN` — persistent User env var (set via `setx`; reopen
  terminal to inherit). Read from env only; NEVER print/commit its value.
- **Build:** `pip install -e .` (deps: numpy, pandas, scipy, pyyaml, statsmodels;
  dev extra: pytest).
- **Test:** `pytest` (24 tests; ~6–9 min — GLMM + 10k bootstraps/permutations are slow).
- **Run (real artifacts):**
  - `python -m twdf.experiments.e1_vslice --config configs/vslice_v0.yaml`
  - `python -m twdf.experiments.e1_multicond --config configs/e1_multicond.yaml`
    (fast variant: `configs/e1_multicond_fast.yaml`)
  - `python -m twdf.experiments.e1_robustness --config configs/e1_multicond.yaml`
  - `python -m twdf.experiments.e1_decomposition --config configs/e1_decomposition.yaml`
- `data/raw/` gitignored (loader auto-downloads Bansal CSV); `results/*.json` committed.
- **Worktree/branch conventions:** slices in `.worktrees/<name>` (gitignored) on
  `feature/<name>`; early draft PR (empty bootstrap commit); squash-merge +
  `--delete-branch`; logs in `.copilot-logs/` (gitignored); subagent prompts in
  `.prompts/` (COMMITTED, for continuity).
- **Subagent dispatch pattern:**
  `copilot -p (Get-Content .\.prompts\<name>.md -Raw) --allow-all --name <name> --model claude-sonnet-4.5 --log-dir .\.copilot-logs`
  (launch impl/fix from the worktree; audits from repo root; `Tee-Object` the output).
  Only the Manager touches git on main + runs `gh pr merge`.

## 10. REPO STATE (at handoff)
- Branch `main` @ **`b48ab2b`** (before this handoff commit), synced with origin.
- **No open PRs. No extra worktrees** (both slice worktrees removed).
- Untracked at handoff (being committed with this doc): `.prompts/` (15 subagent
  prompts), `docs/manager-prompt-v2.md`, this handoff + RESUME-CHECKLIST.
- Adjudication + audit artifacts preserved in the session files store
  (`~/.copilot/session-state/.../files/`): `adjudication-verdict.md`,
  `adjudication-report.json`, `decomp-audit-report.md`, `decomp-attempt1/`. These are
  NOT in git (session-local); the essentials are captured in docs/research + here.

---
### SINGLE MOST IMPORTANT THING
Never freeze τ_disp/τ_level after seeing results, and never trust a subagent's
"it's done / all green" — the merge gate is an INDEPENDENT audit **plus** your own
verification (determinism + clean worktree). And when you build the panel, make it
span DIVERSE tasks (the over-dispersion axis-1 targets is user×task under AI).
