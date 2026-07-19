# RESUME CHECKLIST — new Manager, first 5 minutes (updated 2026-07-19)

1. **Read, in order:** `docs/handoff/2026-07-19-manager-handoff.md` (full current state) →
   `docs/DECISIONS.md` (esp. D5.19→D5.26 = the pivot + latest results) → `docs/paper/outline.md`
   + `docs/paper/reviewer-rebuttals.md`. Your launch prompt is **`docs/manager-prompt-v4.md`**.

2. **Confirm repo/env is sane:**
   ```powershell
   cd "C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail"
   $env:GH_TOKEN=$null ; git --no-pager log --oneline -5 ; git worktree list ; git status --short
   gh pr list --state open      # expect NONE (all era PRs #20-#23 merged)
   $env:PYTHONPATH=(Resolve-Path .\src).Path
   ```
   - **`gh` GOTCHA:** ALWAYS `$env:GH_TOKEN=$null` FIRST (else gh uses the wrong account).

3. **Verify the in-flight amzbook run + schedules:**
   ```powershell
   foreach($r in "axis2_powered_crossvendor_amzbook","axis2_powered_capladder_amzbook","confirmatory_axis1_crossvendor_amzbook","confirmatory_axis1_capladder_amzbook"){ "$r : $(Test-Path "results\$r.json")" }
   Get-CimInstance Win32_Process -Filter "Name='python.exe'" | ? { $_.CommandLine -match "twdf.experiments" } | Select @{n='cfg';e={($_.CommandLine -split '\\')[-1]}}
   try{Invoke-RestMethod "http://127.0.0.1:8787/v1/models" -TimeoutSec 8 | % {"proxy UP"}}catch{"proxy 429/down"}
   ```
   Arms 1–3 done; **arm 4 (`confirmatory_axis1_capladder_amzbook`) is the ONLY one still running**.
   **Schedule #5 (every 30m)** auto-finishes it. Schedules #3 (confirmatory) and #4 (capladder) are STOPPED.
   If the proxy is down, restart: `ghc-api -p 8787 -a 127.0.0.1 --no-enable-auth` (detached).

4. **Re-anchor on the science (honest, PIVOTED — D5.22):** main line = **panel signals are
   model-capability-dependent** (gpt-5.5 resists wrong-AI on both domains; gpt-4.1 the sole over-relier;
   axis-1 heterogeneity collapses at the frontier) + **persona-p5 susceptibility is robust** (positive
   result). Panel↔human correspondence is NULL everywhere (n=5) → **E6 is the only validator**. The
   "validated cross-vendor detector" claim is RETIRED. amzbook (D5.26) tests cross-domain generalization
   and (arms 1–3) it GENERALIZES.

5. **FIRST ACTIONS:**
   (a) When all 4 amzbook results exist → execute Schedule #5 STEP 4: Manager re-derive the amzbook
       axis-1 capability curve (arm 4), compare to beer D5.24, dispatch an INDEPENDENT audit, record
       **D5.27** (honest generalizes/boundary), update outline §5 + rebuttals A5, commit, STOP Schedule #5.
   (b) Then escalate to the PI: amzbook generalization result + recommend **E6** as the next (decisive) step.

**Do NOT:** freeze thresholds/N after seeing results; merge on "it runs"; trust a subagent verdict
without an independent audit + YOUR own numeric re-derivation (recompute displayed_ai_advice = 1-ground_truth
yourself — the E4 sign-inversion trap); pool axis-1 across incomparable models; run 2 proxy arms in
parallel (crashes it) or without throttle; put human outcomes into agent prompts; commit scratch
(`*.log`, `_warmup_mini.json`); forget `$env:GH_TOKEN=$null` before `gh`.
