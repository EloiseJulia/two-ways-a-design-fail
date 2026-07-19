# AUDIT — amzbook 2nd-domain arm (D5.26 → D5.27), read-only, hostile + methodology

You are an INDEPENDENT auditor (fresh eyes). Read-only: do NOT modify code, results, or docs. Your job
is to reproduce, from RAW responses, the Manager's cross-domain (amzbook) numeric claims and to hunt for
silent corruption, sign-inversion, leakage, and over-claims. Report PASS/FAIL per claim with the numbers
you independently computed.

## Context
- Repo: `C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail`. `$env:PYTHONPATH=(Resolve-Path .\src).Path`.
- This arm (preregistered D5.26) replicates the beer capability findings (D5.22/D5.24) on a 2nd domain
  (amzbook). Result files (all committed/untracked in results/):
  - `results/axis2_powered_capladder_amzbook.json`   (axis-2 over-reliance, OpenAI ladder)
  - `results/axis2_powered_crossvendor_amzbook.json` (axis-2, gpt-5.5/claude/gemini)
  - `results/confirmatory_axis1_crossvendor_amzbook.json` (axis-1, cross-vendor)
  - `results/confirmatory_axis1_capladder_amzbook.json`   (axis-1 capability ladder — the just-finished arm 4)
- Models in the ladder: gpt-4o-mini → gpt-4.1 → gpt-4o → gpt-5.5 (all via ghc-api proxy, identical config).

## Claims to INDEPENDENTLY reproduce from RAW responses (recompute yourself; do not just read reported fields)

### Claim 1 — axis-2 over-reliance on the guaranteed-wrong AI (capability ladder, amzbook)
- The dark condition is `Wrong-AI-GT (dark)`. **CRITICAL SIGN CHECK (the E4 trap):** for every dark-condition
  response, verify `trace.ai_advice == 1 - trace.ground_truth` (guaranteed wrong). For non-dark conditions it
  should NOT hold universally.
- Over-reliance = fraction of dark-condition trials where `int(final_decision) == (1 - int(trace.ground_truth))`.
- Manager claims: gpt-4o-mini **0.475**, gpt-4.1 **0.658**, gpt-4o **0.475**, gpt-5.5 **0.150** (n=120 each).
  Confirm gpt-4.1 is the sole significant over-relier (binomial vs 0.5) and gpt-5.5 is significantly BELOW chance.

### Claim 2 — axis-1 heterogeneity collapse at the frontier (capability ladder, amzbook)
- From `results/confirmatory_axis1_capladder_amzbook.json`, per model recompute mean panel disagreement
  across the 5 conditions (aligned_per_condition_table[*].panel_disagreement) and total conflict trials
  (sum of n_conflict).
- Manager claims mean disagreement: **0.124 / 0.192 / 0.108 / 0.015**; conflict over-dispersion estimates
  **0.343 / 0.577 / 0.440 / 0.000**; and gpt-5.5 has **215/600 conflict trials present** (so the 0.000
  over-dispersion is genuine RESISTANCE, NOT a no-conflict artifact — verify conflict trials are non-trivial
  at the frontier).

### Claim 3 — persona p5 (novice-trusting) robustness
- From axis-2 dark-condition raw, per model compute adoption per persona. Manager claims
  `p5-novice-trusting` is the single highest-adopting persona in EVERY ladder model
  (1.00 / 1.00 / 1.00 / 0.40).

### Claim 4 — correspondence is null AND (honesty check) whether it is INFORMATIVE
- amzbook axis-1 cross_condition_correspondence reports rho=0.0 / p=1.0 for all models. The Manager asserts
  this is a DEGENERATE/uninformative null because the human-side per-condition over-dispersion on the amzbook
  anchor (`results/e1_multicond_amzbook.json`) is near-zero/near-constant (aligned_pairs[*].human_rho ~1e-6..3e-3).
  Verify this characterization from the file — is the null informative or vacuous? Flag if the Manager
  over- or under-states it.

## Also check (hostile)
- Parser cleanliness: no fabricated `(decision=0, confidence=0.5)` sentinel rows in the dark condition (the
  D5.19 bug). Spot-check final_decision parses against trace.response JSON.
- Leakage: confirm human reliance/outcomes are NOT in the panel prompt (item selection ≠ label leakage).
- No pooling across models; n's are as claimed (per-model n=120 axis-2 dark; axis-1 5 cond × 6 persona × 20
  items × 1 seed).
- Any mismatch between your recomputed numbers and the Manager's → FAIL that claim with your number.

## Deliverable
A concise verdict: per-claim PASS/FAIL with YOUR independently computed numbers, the sign-check result,
and any red flags. If everything reproduces within rounding, overall PASS.
