# Manager Handoff — 2026-07-19 (Manager #3 → Manager #4)

> Read this FIRST, then `docs/DECISIONS.md` (D5.1→D5.26 = this era), then
> `docs/paper/outline.md` + `docs/paper/reviewer-rebuttals.md`. Your launch prompt is
> `docs/manager-prompt-v4.md`. This handoff supersedes the 2026-07-16 one.

## 0. TL;DR — where the paper stands
The paper **PIVOTED** (D5.22, PI-approved) from "a validated cross-vendor dual-axis triage
DETECTOR" (overclaimed, would be rejected) to an honest, results-driven contribution:

**Main line (contribution #1): LLM-panel deployment-screening signals are MODEL-CAPABILITY-DEPENDENT.**
- **Frontier resistance (robust):** gpt-5.5 adopts a guaranteed-wrong AI *below* chance (beer 0.30,
  amzbook 0.15) and homogenizes cross-persona disagreement to ~0 — on BOTH domains.
- **Model-idiosyncrasy (not a clean size law):** wrong-AI over-reliance is model-specific — gpt-4.1
  is the SOLE significant over-relier (beer 0.60/p=0.018, amzbook 0.658/p=0.0003); gpt-4o-mini/gpt-4o
  sit at chance. The strong small-model effect was gpt-4.1-**mini** (GitHub Models), NOT a general
  "smaller=more over-reliance" law.
- **Persona-robust susceptibility (contribution #2, the positive result):** the trusting-novice
  persona (p5) is the most-susceptible persona in EVERY model on BOTH domains (adoption 0.9–1.0 for
  non-frontier, attenuated at the frontier). The panel robustly localizes WHICH user profile a
  coercive interface endangers, even where aggregate rates don't transfer.
- **Panel↔human correspondence is NULL everywhere** (n=5 conditions, no power): 4 independent nulls
  (GH-Models gpt-4o+gpt-4.1-mini confirmatory D5.25; cross-vendor D5.21; capability ladder D5.24;
  amzbook). The predictive link is UNVALIDATED — only **E6 (human study)** can close it.
- **Cross-domain generalization (amzbook, D5.26):** the capability-dependence + persona-robustness
  pattern GENERALIZES to amzbook (answers reviewer A5 "single domain (beer)").

**Contribution #3 (method):** the two-axis over-dispersion-as-safety-DV + wrong-AI over-reliance
protocol, conflict-conditioned, preregistered. **Contribution #4 (rigor):** preregistration frozen
before results, blind analysis, audit-gated merges, and THREE self-caught silent-corruption bugs
(axis-2 sign-inversion D5.10; betabinom boundary D5.16; parser fabrication D5.19 — the last caught
by a read-only watcher). Turn process integrity into a credibility asset.

**Honest publishability (unchanged, objective):** solid **HCOMP/workshop-tier** now; **borderline
top-venue full paper**. The load-bearing gap is the unvalidated panel↔human link → **E6 is the
decisive move** from ~20-30% to ~50-60% at CHI/FAccT. amzbook (2nd domain) meaningfully hardens it.

## 1. What is DONE + AUDITED (all committed, all audit-PASS)
| Result | DECISIONS | Finding |
|---|---|---|
| Cross-vendor arm (gpt-5.5/claude-sonnet-4.5/gemini-2.5-pro) | D5.20/D5.21 | both axes fail frontier replication; gpt-5.5 resists; persona p5 robust |
| Capability ladder (gpt-4o-mini→gpt-4.1→gpt-4o→gpt-5.5, same proxy/config) | D5.23/D5.24 | model-idiosyncrasy + frontier resistance; axis-1 heterogeneity collapse; NOT a monotone |
| Frozen confirmatory axis-1 (GH-Models gpt-4o+gpt-4.1-mini, N=20) | D5.11/D5.25 | H1a NULL both models (pre-expected); correspondence n.s. |
| P0 parser bug fix | D5.19 | robust parser, never fabricate (0,0.5); self-healed; primaries clean |
| Framing pivot A+B | D5.22 | main line = capability-dependence + persona robustness; "validated detector" RETIRED |
| Domain generalization infra (PR #23) | — | beer-hardcoded → `domain` param (beer backward-compat byte-identical) |

Merged PRs this era: #20 (metric bug-fixes), #21 (OpenAICompatibleProvider), #22 (parser fix),
#23 (amzbook domain). All via impl→independent audit→Manager merge.

## 2. IN-FLIGHT right now (the ONE thing to finish)
**amzbook 2nd-domain arm (D5.26), 4 configs, running on the proxy via Schedule #5.**
- Arms 1–3 DONE + Manager-re-derived (generalization holds — see §0 + the stored memory).
  Results: `results/{axis2_powered_crossvendor,axis2_powered_capladder,confirmatory_axis1_crossvendor}_amzbook.json`.
- **Arm 4 (`confirmatory_axis1_capladder_amzbook`) is STILL RUNNING** (detached; gpt-4o-mini tier;
  gpt-5.5 tier = cache-hits from arm 3). `results/confirmatory_axis1_capladder_amzbook.json` NOT yet written.
- **Schedule #5 (every 30m)** auto-runs the arms sequentially, probes the proxy, resumes on
  rate-window recovery. When all 4 exist → STEP 4: Manager re-derivation of the cross-domain curve +
  independent audit + record **D5.27** + update outline §5 + reviewer-rebuttals A5 + STOP Schedule #5.
- **YOUR FIRST JOB:** let Schedule #5 finish arm 4, then execute its STEP 4 (re-derive amzbook axis-1
  capability curve, compare to beer D5.24, dispatch audit, record D5.27, update docs, commit, stop #5).

## 3. COMPUTE INFRA (critical — read before running anything)
- **`ghc-api` proxy (the workhorse):** local GitHub Copilot API proxy, OpenAI-compatible,
  `http://127.0.0.1:8787/v1`, **NO token**. Start: `ghc-api -p 8787 -a 127.0.0.1 --no-enable-auth`
  (detached). Exposes gpt-4o, gpt-4.1, gpt-4o-mini, gpt-5.5, gpt-5.6-*, claude-*, gemini-*.
  gpt-5.x + gemini-2.5-pro are REASONING models → need `max_completion_tokens` + `min_completion_tokens≥4096`
  (configs already set this per-model). Provider = `OpenAICompatibleProvider` (`provider.type: ghc`),
  cache key carries a `provider:"openai_compat"` discriminator so proxy entries never collide with the
  primary GitHub-Models cache.
- **Proxy is NOT truly unlimited:** under sustained volume (~5-6k calls/day) its upstream returns
  HTTP 429 on ALL calls until the rate window recovers (hours). RULES: throttle (`inter_call_sleep 2.0`),
  run arms SEQUENTIALLY (never 2 parallel — parallel fast-model load crashes it), `max_retries 8`,
  resume (cache-backed) after recovery. Machine also SLEEPS overnight (suspends detached runs → they
  resume on wake). All runs are hashlib-cached + resumable.
- **GitHub Models (`GH_MODELS_TOKEN`, User env var):** per-user-PER-MODEL DAILY cap (gpt-4o ~200/day,
  gpt-4.1-mini ~500/day). Used ONLY for the frozen confirmatory (D5.11) — now COMPLETE, so no longer
  needed. Schedule #3 (confirmatory grinder) is STOPPED.
- **Azure:** never provisioned; the D5.15 Azure plan was superseded by the free proxy (D5.18). Ignore.

## 4. GOTCHAS (hard-won)
- **`gh` account:** ALWAYS `$env:GH_TOKEN=$null` before any `gh` (else it uses the wrong account and
  can't resolve the EloiseJulia repo). git push is unaffected.
- **PYTHONPATH:** `twdf` is not pip-installed → `$env:PYTHONPATH=(Resolve-Path .\src).Path` to run anything.
- **Stale-branch deletion trap:** every feature branch is cut from an earlier main → `git merge origin/main`
  into the branch and confirm `git diff --diff-filter=D` is EMPTY before merging, else the squash DELETES
  newer files. Merge = `gh pr ready N; gh pr merge N --squash --delete-branch`; then remove the worktree,
  `git branch -D`, checkout main, pull.
- **Full test suite HANGS** on network downloads (test_bansal_discriminator/decomposition). Run offline
  test files individually.
- **Detached experiment runs, NOT subagents:** long API loops die inside subagents. Run experiments
  yourself detached; subagents do impl (worktree→draft PR, no live calls) + audit (read-only) ONLY.
- **displayed_ai_advice single source of truth:** axis-2 scores over-reliance against `1-ground_truth`
  on the dark condition; ALWAYS recompute it yourself from ground_truth (the E4 sign-inversion trap).
- **Scratch hygiene:** `*.log`, `results/_warmup_mini.json` are gitignored/scratch — never commit; clean
  before recording. Prompt files under `.prompts/` ARE tracked (audit trail).

## 5. RIGOR CONTRACT (do not break)
- Preregister (freeze model set / N / analysis / prediction with a UTC timestamp + commit) BEFORE any
  powered/confirmatory run. Never tune framing/thresholds on a peeked effect. τ_disp/τ_level remain UNFROZEN.
- Every merge gated on an INDEPENDENT audit (fresh session) + YOUR OWN numeric re-derivation from raw
  responses (two overstated subagent verdicts + three silent-corruption bugs were caught this way).
- Per-model, NO pooling across incomparable models. Report REGARDLESS of outcome (nulls are results).
- Log EVERY non-trivial change in `docs/DECISIONS.md` in the same commit. Commit trailer:
  `Co-authored-by: Copilot <copilot@github.com>`.

## 6. BACKLOG (after amzbook D5.27 lands)
1. **E6 human study** (the decisive capstone; `docs/plans/e6-human-study-design.md`). PI-approved as the
   final step. Sharpened question: "WHICH model's panel (if any) tracks real human reliance heterogeneity?"
   A stripped axis-2-only E6 (N≈40, Prolific) is the fastest path (idea-eval P6).
2. Non-blocking follow-ups (todos): axis-2 pooled block "descriptive-only" label; caller-level
   `PanelParseError` guard in run_panel (prevent a future resume-crash-loop; current risk 0/thousands).
3. Optional: cross-domain difficulty-stratified correspondence (more n than 5) once amzbook lands.
4. Venue: interim HCOMP 2026; CHI/FAccT 2027 with E6.

## 7. PI PREFERENCES (durable)
- Owner @EloiseJulia prefers **Chinese (中文)** replies.
- Caution on large/confirmatory runs: verify effect replicates first, control budget (lean on cache,
  no re-runs), never scale without explicit PI sign-off.
- Autonomy: the PI does NOT hand-review PRs (full-auto merge on audit PASS); escalate only the gates,
  genuine methodology disputes, and framing/scope/venue calls.
