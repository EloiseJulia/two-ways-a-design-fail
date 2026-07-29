# RESUME CHECKLIST — new session, first 5 minutes (updated 2026-07-29, Writing Lead)

You are the **WRITING LEAD** (HCI/AI, target CHI). Chat Chinese with @EloiseJulia; paper is English.
Owner has final say on framing/claim-strength/structure/venue; language smoothing can proceed but stay
diffable. Rebuild+commit `main.pdf` after every `main.tex` edit; log decisions in `docs/DECISIONS.md`.

1. **Read, in order:** `docs/handoff/2026-07-29-writing-lead-handoff.md` (full current state) ->
   `docs/DECISIONS.md` (esp. **D5.62 -> D5.86** = this round) -> `docs/paper/main.tex` (deliverable, **26pp,
   single-axis**, Figure 1 = teaser). Skim `comment2.md` (owner strategy) + the 3 reviews in
   `~/.copilot/session-state/<id>/files/reviews/`.

2. **Confirm repo/env:**
   ```powershell
   cd "C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail"
   $env:GH_TOKEN=$null ; git --no-pager log --oneline -6 ; git status --short
   $env:PYTHONPATH=(Resolve-Path .\src).Path
   try{Invoke-RestMethod "http://127.0.0.1:8787/v1/models" -TimeoutSec 8 | %{"proxy UP"}}catch{"proxy 429/down"}
   ```
   - `gh` GOTCHA: ALWAYS `$env:GH_TOKEN=$null` first. Proxy is **serial only** (429 under concurrency).

3. **Check IN-FLIGHT A1 (50-item rerun):**
   ```powershell
   Get-ChildItem results\*n50*.json | Select Name,LastWriteTime
   ```
   - Need all 4: capladder + crossvendor, each beer + amzbook. beer x2 DONE; amzbook x2 was running at handoff.
   - Missing any? Re-run it: `python -m twdf.experiments.axis2_powered --config configs/<name>_n50.yaml`
     (cache-resumable). Never run two configs at once (429).

4. **Re-anchor (honest):** measurement-audit of synthetic-user interface-CONTENT risk, **single axis**
   (coercion/wrong-advice). Robust: backend non-invariance (adoption 0.15-0.66, flip 0.60/0.33);
   **capability-vulnerability inversion** (strong gpt-5.5 least reproduces the at-risk p5; coverage saturates
   at the weak pair 4/6, 5/6). Manipulation-check p5 + dispositional ablation (low self-confidence is the
   lever, not the label). **panel<->human = NULL everywhere -> E6 is the only validator.** No human-predictive claim.

5. **FIRST ACTIONS (once A1 4 configs done):** (a) refresh all axis-2 numbers 20->50 items (abstract, Fig 1
   caption, sec:modeldep/coercion/instability/capvuln); (b) **panel #1** - bootstrap flip-*probability* +
   CI-disjoint-straddle "significant flip" + foreground threshold-free evidence; (c) capability-vulnerability
   mechanical decomposition + bootstrap CIs on variance shares; (d) re-run the review panel to confirm.
   Then escalate **D1 (E6 pilot)** to owner - the decisive lever (owner deferred it).

**Do NOT:** freeze thresholds/N after seeing results; trust a subagent verdict without your own numeric
re-derivation (recompute `displayed_ai_advice = 1-ground_truth` yourself - sign-trap); pool axis-1 across
incomparable backends; run 2 proxy arms in parallel; expect claude-haiku-4.5 to work; use reasoning models
without `max_completion_tokens`+min 4096; fabricate BibTeX; mass-replace "interface"->"interface framing";
put `teaserfigure` after `\maketitle` (acmart drops the label); forget to rebuild+commit main.pdf; forget
`$env:GH_TOKEN=$null`.
