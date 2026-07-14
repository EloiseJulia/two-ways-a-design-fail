You are an INDEPENDENT reviewer performing a FOCUSED HOSTILE RE-AUDIT of draft
PR #1 (branch feature/vslice-v0) of the METHODS project "two-ways-a-design-fail".
A prior audit FAILED this PR with 3 blockers (B1 degenerate n=2 correlation, B2
non-reproducible panel values, B3 test_integration import). A fix subagent claims
all are fixed. Trust NOTHING it claims — re-verify from source + real re-runs.
You are READ-ONLY: report only; do NOT fix/commit/merge/push.

## WHERE
Worktree (read-only): C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail\.worktrees\vslice-v0
Confirm `pwd` + `git rev-parse --abbrev-ref HEAD` (feature/vslice-v0) first. You
may make a THROWAWAY venv/scratch dir but do NOT modify tracked files, and do NOT
touch the main checkout. Clean up any scratch files you create before finishing.

## VERIFY EACH BLOCKER IS ACTUALLY FIXED (with your own probes/runs)
### B3 — `pytest tests/` : do ALL tests pass on a fresh `pip install -e .`? Run
the FULL suite and paste the summary. Confirm test_integration no longer NameErrors.

### B2 — REPRODUCIBILITY (the serious one). The root cause was claimed to be
Python's non-deterministic `hash()`, replaced with hashlib. Independently verify:
- Run `python -m twdf.experiments.e1_vslice --config configs/vslice_v0.yaml` at
  least 3 times, in SEPARATE interpreter invocations (fresh process each time —
  this matters, because hash randomization differs per process). Extract the panel
  disagreement values + over-dispersion rho each run and confirm they are
  IDENTICAL across all 3 runs (ignore only a timestamp field).
- Confirm the COMMITTED `results/e1_vslice_v0.json` matches a fresh run's numbers.
- grep the source for any remaining use of builtin `hash(` or iteration over an
  unordered `set`/dict that feeds numeric output — any surviving nondeterminism
  is a BLOCKER. Confirm the new determinism test genuinely runs the stub twice in
  a way that would catch cross-process nondeterminism (a single-process
  double-call may NOT catch hash-seed differences — judge whether the test is
  actually meaningful, and say so).

### B1 — degenerate correlation. Confirm: when n_conditions < 3 the code does NOT
present r as a result — it sets a `degenerate: true` flag + explanatory note in
the JSON, warns at runtime, and PROGRESS.md discloses it as a plumbing-only,
non-evidence number. Confirm it does NOT hard-crash (v0 has 2 conditions).

## NO REGRESSION — re-confirm the previously-verified core is still correct
Re-probe `betabinom_overdispersion`: pure-binomial data → rho ≈ 0; over-dispersed
data → rho clearly > 0; mean-predictor baseline still p(1-p) and beaten. Confirm
the fixes did NOT alter/break the estimator. Skim the fix diff
(`git --no-pager diff` of the 6 fix commits) for any scope creep or newly
introduced bug.

## DIFF HYGIENE
AUDIT_REPORT.md and audit scratch removed; no stray artifacts; data/raw not
committed; diff only touches intended files.

## OUTPUT
Ranked findings (BLOCKER/MAJOR/MINOR/UNVERIFIED) with proof (your probe output),
then an explicit VERDICT: PASS or FAIL. PASS only if all 3 blockers are genuinely
resolved (especially B2 cross-process reproducibility), full pytest passes, and
the core estimator is intact. Return the report to the Manager; do NOT merge.
