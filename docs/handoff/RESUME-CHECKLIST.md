# RESUME CHECKLIST — new Manager, first 5 minutes (updated 2026-07-24, Manager #5)

1. **Read, in order:** `docs/handoff/2026-07-24-manager-handoff.md` (full current state) →
   `docs/manager-prompt-v4.md` (your role/contract) → `docs/DECISIONS.md` (esp. **D5.44→D5.57** = this
   round's increments) → `docs/paper/main.tex` (the deliverable, 15pp).

2. **Confirm repo/env is sane:**
   ```powershell
   cd "C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail"
   $env:GH_TOKEN=$null ; git --no-pager log --oneline -8 ; git status --short
   $env:PYTHONPATH=(Resolve-Path .\src).Path
   try{Invoke-RestMethod "http://127.0.0.1:8787/v1/models" -TimeoutSec 8 | % {"proxy UP"}}catch{"proxy 429/down"}
   ```
   - **`gh` GOTCHA:** ALWAYS `$env:GH_TOKEN=$null` FIRST.
   - If proxy down: `ghc-api -p 8787 -a 127.0.0.1 --no-enable-auth` (its exe is on PATH under Python312\Scripts).

3. **Check the IN-FLIGHT LSAT run (the one open task):**
   ```powershell
   Test-Path results\lsat_axis2.json ; Get-Content lsat_run.log -Tail 6
   ```
   - If not done: it's `scripts/analysis/lsat_panel.py --config configs/lsat_axis2.yaml` (multiple-choice,
     6 backends x {Conf.,dark} x 6 personas x 20 items). Resumable (cache-backed). ~4-6h.
   - If done: write a small analysis (adopt=final==ai_advice on dark; s1_correct; flip; coverage) -> get an
     INDEPENDENT audit -> integrate as a task-structure-generalization paragraph. No LSAT paper text yet.

4. **Re-anchor on the science (honest):** measurement-audit of synthetic-user interface-CONTENT risk.
   Robust anchors: (i) backend non-invariance / **risk-classification flip rate** up to 0.60; (ii)
   **capability-vulnerability mismatch** — at **n=11** backends, agg_adopt-capability rho=-0.82 (BH .006,
   ROBUST); flip/p5 rho~-0.66 (BH .03, SUGGESTIVE, amzbook-carried, single-backend fragile); coverage: single
   frontier 1/9, capability-first needs k=10; (iii) protective interventions cut synthetic over-reliance
   (direction backend-robust, magnitude not; H2/H3 refuted); (iv) persona-p5 = manipulation check, only the
   background-only arm is a true deference-free control. **panel<->human = NULL everywhere -> E6 is the only
   validator.** No human-predictive-validity claim.

5. **FIRST ACTIONS:**
   (a) Finish/verify LSAT -> analyze -> independent audit -> integrate (closes the "one task family" critique).
   (b) Then escalate to PI: **E6 is the decisive next lever** (design in docs/plans/e6-stripped-axis2-design.md;
       running/preregistering/recruiting is a PI decision). Synthetic-only ceiling ~= 35-40%; E6 -> >50%.

**Do NOT:** freeze thresholds/N after seeing results; merge on "it runs"; trust a subagent verdict without an
INDEPENDENT audit + YOUR own numeric re-derivation (recompute displayed_ai_advice = 1-ground_truth yourself —
the sign-inversion trap); pool axis-1 across incomparable models; run 2 proxy arms in parallel or without
throttle; expect claude-haiku-4.5 to work (it can't); use reasoning models without max_completion_tokens+min
4096; fabricate BibTeX (verify every cite); cherry-pick/subset backends (report all; disclose exclusions with
a mechanical reason); forget to rebuild+commit main.pdf after editing main.tex; forget `$env:GH_TOKEN=$null`.
