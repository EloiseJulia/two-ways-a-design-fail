You are the FIX subagent for draft PR #1 (branch feature/vslice-v0) of the
research METHODS project "two-ways-a-design-fail". An independent hostile audit
FAILED the PR with 3 BLOCKERS. Your job: fix exactly those blockers (plus two
trivial minors), re-run to prove it, push. Do NOT expand scope. Do NOT touch the
core beta-binomial methodology (the audit verified it CORRECT). NEVER merge.

## WHERE
Worktree: C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail\.worktrees\vslice-v0
Confirm `pwd` + `git rev-parse --abbrev-ref HEAD` (feature/vslice-v0) first. Work
only here. Commit trailer on EVERY commit: `Co-authored-by: Copilot
<copilot@github.com>`. Push to feature/vslice-v0; do NOT mark ready; NEVER merge.
The full audit is in `AUDIT_REPORT.md` (untracked) in this worktree — READ IT.

## BLOCKERS TO FIX

### B3 (trivial) — integration test import
`tests/test_integration.py` uses `np` but only imports numpy inside the
`__main__` guard. Move `import numpy as np` to the top of the file so
`pytest tests/test_integration.py` passes.

### B1 — degenerate correlation over n=2 conditions
`src/twdf/experiments/e1_vslice.py` computes a Pearson correlation between panel
disagreement and human over-dispersion over only 2 UI conditions. With n=2, r is
ALWAYS ±1.0 — mathematically meaningless. Fix:
- Only compute the correlation when there are >= 3 UI conditions. When < 3, set
  the correlation field to null and add an explicit boolean/flag like
  `"correlation_degenerate": true` and a `"correlation_note"` string in the output
  JSON stating it is a v0 PLUMBING CHECK, NOT a scientific result, and that a
  meaningful correlation needs >= 3 (ideally >= 5) UI conditions. Do NOT hard
  `assert`/crash (v0 intentionally has 2 conditions) — degrade gracefully and label.
- Print/log the same explicit warning at run time.
- Update PROGRESS.md to state clearly that the v0 r=±1 number is degenerate
  (n=2) and is a plumbing check only, not evidence.

### B2 — non-reproducible panel disagreement values (reproducibility break)
The committed `results/e1_vslice_v0.json` reports panel disagreement
(Human=0.008, Conf.+Adaptive=0.163) that a fresh run from the COMMITTED
`configs/vslice_v0.yaml` does NOT reproduce (fresh run gave different values).
For a methods paper, the committed config MUST reproduce the committed results.
Fix:
- Find the root cause (config edited after the run, or a seed/param not actually
  threaded into the synthetic stub, or a nondeterministic ordering). Ensure the
  synthetic stub and the whole E1-v0 chain are FULLY deterministic given the
  committed config + seed (thread the seed everywhere; sort any dict/collection
  iteration; no reliance on unordered set/hash iteration).
- Then re-run `python -m twdf.experiments.e1_vslice --config configs/vslice_v0.yaml`
  ONE time and COMMIT the regenerated `results/e1_vslice_v0.json` so that the
  committed config reproduces the committed results BYTE-FOR-BYTE on re-run
  (except an allowed timestamp field). Include the config hash in the
  run_manifest and verify it matches the config.
- Add a test that asserts determinism: running the stub / the E1 summary twice
  with the same seed yields identical disagreement values.

### Minors (do while you're here, cheap)
- MIN2: `pd.read_csv` DtypeWarning in `src/twdf/data/bansal.py` — pass explicit
  `dtype=` for the mixed-type columns (choice/y/pred/pred2) to silence it.
- Leave print→logging (MIN1) as a post-merge TODO note in PROGRESS.md; do NOT
  do the full logging refactor now (out of scope for the fix).

## VERIFY BEFORE FINISHING
- `pip install -e .` works; `pytest` → ALL tests pass (including test_integration
  and the new determinism test).
- `python -m twdf.experiments.e1_vslice --config configs/vslice_v0.yaml` run
  TWICE yields identical disagreement + over-dispersion numbers; the committed
  results file matches a fresh run.
- `git status` clean of stray artifacts. DELETE `AUDIT_REPORT.md` and any audit
  scratch files (do NOT commit them). data/raw not committed.

## DELIVERY
Commit the fixes in logical steps; push to feature/vslice-v0 (do NOT mark ready,
NEVER merge). Return to the Manager: exactly what you changed for B1/B2/B3, the
ROOT CAUSE of B2, the final reproduced numbers (quote results file), and full
pytest output summary.
