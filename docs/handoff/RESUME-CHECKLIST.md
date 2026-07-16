# RESUME CHECKLIST — new Manager, first 5 minutes

1. **Read, in order:** `docs/handoff/2026-07-16-manager-handoff.md` (full state) →
   `docs/DECISIONS.md` (chronological WHY of every pivot) → `SPEC.md` §2 (contribution
   structure: C1 primary, C0 demoted) + `PROGRESS.md` (§Preregistration freeze log +
   §Doing) → `INTERFACES.md`. Your launch prompt is `docs/manager-prompt-v3.md`.

2. **Confirm repo/env is sane:**
   ```powershell
   cd "C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail"
   git --no-pager log --oneline -3 ; git worktree list ; git status --short
   $env:GH_TOKEN=$null ; gh pr list --state open     # expect drafts #7 (E4), #8 (pilot)
   if ([Environment]::GetEnvironmentVariable('GH_MODELS_TOKEN','User')) {"token set"} else {"set GH_MODELS_TOKEN"}
   ```
   - **`gh` GOTCHA:** always run `$env:GH_TOKEN=$null` FIRST, else gh uses the wrong account
     (v-elzhang_microsoft) and can't resolve the EloiseJulia repo. git push is unaffected.
   - Expect: main @ `d67f40e`+, worktrees `.worktrees/e4-compliance` (@f670b97) and
     `.worktrees/axis1-pilot` (@bba48dc), two draft PRs. Do NOT delete those worktrees (they
     hold populated caches: e4 193, pilot 446).

3. **Verify compute:** GitHub Models daily cap is per-user-PER-MODEL and TIER-DEPENDENT
   (strong ~200/day, mini ~500/day). Probe today's budget (200 = has budget) for
   `openai/gpt-4o`, `openai/gpt-4.1-mini`. If the PI provisioned Azure, check env NAMES
   `AZURE_OPENAI_ENDPOINT/KEY/API_VERSION/DEPLOYMENT` and run one `pytest -m live
   tests/test_azure_provider.py` cred check (~$0.001). Non-OpenAI families (Llama/Phi) are
   UNSTABLE on GitHub Models — exploratory-only.

4. **Re-anchor on the science (honest):** C1 (agent-panel two-axis triage) is the PRIMARY
   contribution but its **powered confirmatory axis-1 (H1a) has NOT been run** — that is the
   #1 job. C0 (AI→user×task) is real on Bansal but DEMOTED (Lu&Yin trait-stable 0.80;
   discriminator inconclusive/ceiling artifacts). Panel redesign works (conflict 3%→43%,
   axis-2 wrong-AI 0.325, p5 backfire).

5. **First actions (do NOT freeze τ/N after seeing results):**
   (a) Resume E4 (PR #7) on gpt-4.1-mini after daily reset (193/450 cached) → audit → merge.
   (b) Run a CLEAN exploratory power-N pass on {gpt-4o, gpt-4.1-mini} (reliable parse), fill
       prereg §8 N + record a freeze timestamp BEFORE the confirmatory run.
   (c) Merge PR #8 as exploratory infra + the provider-stability limitation.
   (d) Run the CONFIRMATORY axis-1 on {gpt-4o, gpt-4.1-mini} day-batched (prereg amendment
       2026-07-16T02:29:50Z) — report regardless of outcome; report per-model.

**Do NOT:** freeze thresholds/N after seeing results; merge on "it runs"; trust a subagent's
verdict without an independent audit + your OWN numeric re-derivation (two overstated verdicts
were caught this way); pool axis-1 across incomparable models; put human outcomes into agent
prompts (item selection uses AI-side exogenous properties only); leave a dirty worktree at merge
(restore timestamped `results/*.json`, remove scratch); run long API loops inside a subagent
(they die mid-run — run experiments yourself, detached).
