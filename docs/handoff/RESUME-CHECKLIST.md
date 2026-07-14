# RESUME CHECKLIST — new Manager, first 5 minutes

1. **Read, in order:** `docs/handoff/2026-07-15-manager-handoff.md` (full state) →
   `SPEC.md` (design + refined H1a) → `PROGRESS.md` (progress + **preregistration
   freeze log** — τ_disp/τ_level are NOT frozen yet) → `INTERFACES.md` (contracts).
   Your launch prompt is `docs/manager-prompt-v2.md`.

2. **Confirm repo/env is sane:**
   ```powershell
   cd "C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail"
   git status ; git --no-pager log --oneline -5 ; git worktree list ; gh pr list
   if ($env:GH_MODELS_TOKEN) {"token in-process"} else {"reopen terminal after setx"}
   [Environment]::GetEnvironmentVariable('GH_MODELS_TOKEN','User') -ne $null   # True = set
   ```
   Expect: clean `main`, no open PRs, no extra worktrees, token present.

3. **Sanity-check the build once** (optional but recommended):
   `pip install -e .` then `pytest -q` (24 tests; slow ~6–9 min). Do NOT re-run the
   long experiments unless needed.

4. **Re-anchor on the science:** axis-1 over-dispersion is REAL (Human ρ=0.067,
   CI [0.052,0.081]); decomposition says no-AI reliance = stable user trait (0.74),
   AI-assisted = user×task (0.32–0.41). See
   `docs/research/2026-07-14-overdispersion-decomposition.md`.

5. **Start the next slice = Module B (real LLM panel via GitHub Models):** implement
   `ModelProvider` reading `GH_MODELS_TOKEN` from env (never commit it), dual-system
   personas → `AgentResponse`, counterfactual pairing, spanning DIVERSE tasks. Go
   SMALL first (few personas × ~10–20 tasks × 1 UI pair × 1 model) to validate loop
   + cost, then scale. Use the audit→(fix→reaudit)→merge gate; clean the worktree
   and verify determinism before every `gh pr merge`.

**Do NOT:** freeze thresholds after seeing results; merge on "it runs"; trust a
subagent self-report without independent audit + your own verification; leave a
dirty worktree at merge (restore timestamp-modified `results/*.json`, remove scratch).
