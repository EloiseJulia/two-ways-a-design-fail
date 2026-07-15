# audit-bansal-discriminator — INDEPENDENT hostile audit (PR #6)

You are a FRESH, independent auditor. You did NOT write this code. This decides the
paper's co-anchor C0, so be maximally hostile on methodology + interpretation. REPORT
ONLY; do NOT fix or merge. Zero API needed (pure real-data compute; rerun freely).
Evidence = file:line + reproduced numbers.

## Context
Branch `feature/bansal-discriminator` (draft PR #6) re-decomposes Bansal on subsets
MATCHED to Lu&Yin's regime to probe whether Bansal's AI-assisted user×task (split-half
stable_user_share ≈ 0.32–0.41) is driven by controllable regime confounds. The original
impl produced a "PERSISTS → clean demote C0" verdict; the **Manager corrected this to
INCONCLUSIVE** (ceiling artifacts in 2/3 domains; lsat rises only partway with overlapping
CI) and demoted C0 to a Bansal-specific supporting finding while elevating C1 to PRIMARY.
Your job: independently verify BOTH the methodology AND that the corrected framing is honest.

Read: `SPEC.md` (§2 — C1 now PRIMARY, C0 demoted, OPEN QUESTION), `PROGRESS.md` (discriminator
entry + PR#5 Lu&Yin + Known pitfalls), `docs/research/2026-07-15-bansal-discriminator.md`
(corrected report), `docs/research/2026-07-15-luyin-decomposition-replication.md`,
`.prompts/impl-bansal-discriminator.md`. Diff: `git --no-pager diff main...feature/bansal-discriminator`.
Key files: `src/twdf/experiments/bansal_discriminator.py`, `configs/bansal_discriminator.yaml`,
`src/twdf/metrics/variance_decomposition.py` (reused split_half_reliability),
`tests/test_bansal_discriminator.py`, `results/bansal_discriminator.json`.

## Checks (PASS/FAIL + evidence + reproduction)
### A. Method
1. Uses `split_half_reliability` (seed=43, n_splits=100, min_tasks=8) on each subset —
   NOT ANOVA-on-cells. Subsets are PRE-SPECIFIED in the config (no post-hoc/gamed subsets).
2. Subset filters correct: single-domain filters select the right domain (difficulty
   1=beer/2=amzbook/3=lsat); AI-accuracy band + tasks_per_user subsampling do what they claim.
   Spot-check by re-running the experiment and re-deriving each subset's n_users, tasks/user,
   reliance, AI-acc, stable_user_share + CI. Must match `results/bansal_discriminator.json`.
3. Reproduce the headline: full_ai ≈ 0.334 [0.228,0.416], domain_lsat ≈ 0.464 [0.309,0.587],
   beer ≈ 0.00, amzbook ≈ 0.00.

### B. The CEILING-ARTIFACT catch (the crux of the correction — verify INDEPENDENTLY)
4. Independently compute the BETWEEN-USER SD of per-user reliance for beer, amzbook, lsat
   (AI conditions). Confirm beer/amzbook SD ≈ 0.05 (near-ceiling, mean ~0.81–0.85) vs lsat
   SD ≈ 0.135. Confirm that near-zero split-half share in beer/amzbook is a LOW-VARIANCE /
   CEILING artifact (no between-user signal), hence UNINTERPRETABLE — NOT evidence of
   "user×task". If you find the beer/amzbook zeros are actually interpretable, say so (that
   would challenge the Manager's correction).
5. Confirm lsat's CI [0.309,0.587] OVERLAPS full_ai's [0.228,0.416] → the "rise" is not
   statistically clean → the corrected "INCONCLUSIVE" verdict is warranted (NOT a clean
   persist, NOT a clean collapse).

### C. Framing honesty (verify the docs are NOW correct, not overstated)
6. SPEC §2: C1 is PRIMARY; C0 is DEMOTED to a Bansal-specific supporting finding with the
   ceiling-artifact + overlapping-CI + confounded-gap caveats; the regime/sequential-feedback
   idea is an explicit OPEN QUESTION, not a claim. No leftover "clean persist / design-
   dependent as established" language. Research doc + PROGRESS consistent with this.
7. Confirm the docs do NOT overclaim in EITHER direction (neither "user×task persists,
   demote proven" NOR "design-dependent proven"). The honest position is INCONCLUSIVE /
   generalization unresolved.

### D. Determinism & hygiene
8. Cross-process determinism (two separate processes → byte-identical excl. manifest
   timestamp). Builtin `hash()` banned (grep). `pytest -q` green; report counts; tests not
   weakened. `data/raw/` gitignored; no scratch committed; no secrets.

## Output
Markdown report: overall verdict (PASS / FAIL / CONDITIONAL PASS); 8-check table with
PASS/FAIL + evidence + reproduced numbers (esp. the independent between-user SD by domain);
an explicit statement on whether (a) the ceiling-artifact correction is CORRECT and (b) the
docs are now honestly INCONCLUSIVE; and any BLOCKERS. Do NOT modify code or merge. Print the
report in your final message.
