You are an INDEPENDENT reviewer performing a HOSTILE pre-merge audit of draft
PR #2 (branch feature/e1-multicond) of the top-venue HCI METHODS project
"two-ways-a-design-fail". A single silent statistical error voids the paper. You
did NOT write this code; you have NO prior context. Treat the PR description, all
commit messages, the impl agent's "14/14 pass / determinism verified / honest
caveat" claims, and every reported number as UNTRUSTED. Re-derive from source +
real re-runs. Assume defects exist. READ-ONLY: report only; do NOT fix/commit/
merge/push. Clean up any scratch files you create.

## WHERE
Worktree (read-only): C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail\.worktrees\e1-multicond
Confirm `pwd` + `git rev-parse --abbrev-ref HEAD` (feature/e1-multicond) first.
Read SPEC.md (§0 axis-1, §5 E1, §8 stats), INTERFACES.md, PROGRESS.md. You may
build/run in a THROWAWAY venv; do NOT modify tracked files or the main checkout.

## WHAT THIS SLICE CLAIMS
Broadens axis-1 to all 6 real Bansal conditions (Human, Conf., Conf.+Single,
Conf.+Double, Conf.+Adaptive, Conf.+Adaptive (Expert)) x 3 domains
(beer/amzbook/lsat); per-condition human beta-binomial over-dispersion, difficulty-
controlled; cross-condition correlation via Spearman + permutation + bootstrap.
Panel is still a SYNTHETIC STUB, so the correlation is claimed to be a
mechanism/plumbing check, NOT evidence.

## PHASE 1 — logic bugs in the diff
`git --no-pager diff main...feature/e1-multicond`. Identity-dimension gaps
(dataset/task/condition/user/seed all in keys?), silent row drops in the multi-
condition selector, off-by-one, code paths bypassing validation, any surviving
builtin `hash(` or unordered set/dict iteration feeding numeric output
(nondeterminism), and whether v0's `e1_vslice` still works after the API change.

## PHASE 2 — METHODOLOGY (§4.5). For EACH, read the impl AND run your own probe:
1. **beta-binomial reused correctly**: confirm the per-condition over-dispersion
   uses the SAME verified `betabinom_overdispersion` and still separates true
   over-dispersion from binomial noise (pure-binomial→~0, over-dispersed→>0). No
   regression to the v0 estimator.
2. **DISCREPANCY vs v0 — investigate**: v0 (PR #1) reported Human over-dispersion
   rho=0.0369 [0.0087, 0.0681] on ~2340 trials. This slice reports Human
   rho=0.0000 [0.0000, 0.0386] on ~1220 trials. WHY did it change? Determine the
   exact cause (task subset selection differs? fewer trials? domain restriction?).
   Judge whether the multicond task/condition selection is PRINCIPLED and
   documented, or arbitrary in a way that makes the "genuine finding" fragile. A
   result that flips to zero under an undocumented task-selection change is a
   MAJOR concern for a methods paper — report it clearly with the root cause.
3. **difficulty control**: the impl uses "stratified pooling" across domains and
   claims users each saw only ONE domain (between-subjects on domain).
   INDEPENDENTLY VERIFY that claim from the raw data (group users by domain — does
   any user appear in >1 domain?). If the claim is true, does the difficulty
   control actually do anything here, and is it honestly described? If FALSE, is
   difficulty confounding the cross-condition comparison?
4. **stub not rigged**: the stub disagreement is "hash-based from fixed condition
   properties", disclosed as circular-by-design. Confirm it is NOT tuned to
   manufacture a significant correlation (the reported Spearman is -0.23, p=0.58 —
   non-significant, consistent with an honest stub). Confirm the JSON + PROGRESS
   explicitly label the correlation as non-evidence.
5. **permutation test null**: verify shuffling CONDITION labels (not users) is the
   correct null for the cross-condition correlation, and it is implemented that
   way with enough perms, seeded.
6. **bootstrap CI**: at n=6 conditions the reported bootstrap CI is [-1,1]
   (uninformative). Confirm this is honestly reported (not hidden) and that
   resampling is over the correct unit.
7. **degenerate guard** retained (n<3 flagged).
8. **no premature threshold freezing**; **no leakage / no cross-condition global
   normalization that peeks**.
9. **hallucinated numbers**: re-run and confirm results/e1_multicond.json matches
   a fresh run.

## PHASE 3 — artifact + full suite
Throwaway venv: `pip install -e .`; run BOTH
`python -m twdf.experiments.e1_vslice --config configs/vslice_v0.yaml` (regression)
and `python -m twdf.experiments.e1_multicond --config configs/e1_multicond.yaml`.
Run the multicond experiment in >=2 SEPARATE processes and confirm byte-identical
numbers (cross-process determinism — the v0 hash bug must not have returned). Run
FULL `pytest`; attribute any failure by reproducing on a throwaway clean `main`
worktree (do not assume pre-existing). Judge whether the new determinism-related
tests would actually catch cross-process nondeterminism (a single-process double
call may not — flag if the automated test is weaker than claimed).

## PHASE 4 — diff hygiene
No debug residue / accidental deletions; data/raw not committed; diff only intended
files; no scratch artifacts committed.

## OUTPUT
Ranked findings (BLOCKER/MAJOR/MINOR/UNVERIFIED) with file:line + proof (your
probe code + output) + minimal fix, then explicit VERDICT: PASS or FAIL. For a
methods paper "it runs" != "correct". Especially: if the v0->multicond
over-dispersion discrepancy stems from an undocumented/arbitrary selection, weigh
whether that is a BLOCKER (mandatory documentation/justification) before merge.
Return the report to the Manager; do NOT merge.
