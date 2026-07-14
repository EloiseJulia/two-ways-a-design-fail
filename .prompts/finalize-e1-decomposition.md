You are a FINALIZE subagent for slice "e1-decomposition" (branch
feature/e1-multicond, draft PR #2) of the HCI METHODS project
"two-ways-a-design-fail". The analysis is DONE and validated but a prior session
timed out before committing. Finish it cleanly. Rigor > speed. NEVER merge.

## WHERE
Worktree: C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail\.worktrees\e1-multicond
Confirm `pwd` + branch first. Work ONLY here. Commit trailer EVERY commit:
`Co-authored-by: Copilot <copilot@github.com>`. Push to draft PR #2; NEVER merge.

## CURRENT STATE (uncommitted, in the worktree)
- `src/twdf/metrics/variance_decomposition.py` — split-half reliability (PRIMARY,
  validated) + GLMM corroboration.
- `src/twdf/experiments/e1_decomposition.py`, `configs/e1_decomposition.yaml`.
- `tests/test_variance_decomposition.py` — 24 tests pass with STRONG thresholds
  (pure-stable reliability>=0.7 & share>=0.8; pure-interaction <=0.2). Do NOT weaken.
- `results/e1_decomposition.json` — real results already generated.
- `pyproject.toml` modified (added statsmodels).

## REAL RESULTS (already in results/e1_decomposition.json — verify, don't recompute
## unless needed). Split-half stable_user_share (Spearman-Brown reliability), 95% CI:
  Human=0.742 [0.693,0.787]; Conf.+Double=0.414 [0.314,0.505]; Conf.=0.358
  [0.271,0.463]; Conf.+Adaptive=0.334 [0.228,0.416]; Conf.+Single=0.321
  [0.166,0.442]; Conf.+Adaptive (Expert)~0.000. GLMM: did NOT converge (all
  conditions) — reported honestly.

## TASKS
1. **Bound the GLMM so reruns are fast + deterministic.** The GLMM is slow and
   non-converging; ensure `variance_components_glmm` has a strict max-iteration /
   time bound and returns `{converged: false, note: ...}` quickly and
   DETERMINISTICALLY rather than hanging. The experiment must complete fast on
   rerun. Keep GLMM as clearly-labeled corroboration; split-half stays PRIMARY.
   (Do NOT fabricate GLMM numbers; honest non-convergence is fine.)
2. **Determinism check:** run `python -m twdf.experiments.e1_decomposition --config
   configs/e1_decomposition.yaml` TWICE; confirm the split-half numbers are
   byte-identical across runs (separate processes). Fix any nondeterminism (seed
   everything; no builtin hash()). Confirm `pytest` ALL pass.
3. **Write `docs/research/2026-07-14-overdispersion-decomposition.md`** — the
   scientific write-up. Include:
   - The single-observation-per-cell identifiability issue (99.7% of
     (condition,user,task) cells have 1 obs) → why ANOVA-on-cells fails and
     split-half (leveraging 20-50 tasks/user) is the correct PRIMARY method.
   - A table of split-half stable_user_share + CI per condition (numbers above).
   - GLMM non-convergence, honestly noted as corroboration-not-available.
   - The HONEST CONCLUSION: in the no-AI Human baseline reliance is substantially a
     STABLE USER TRAIT (share 0.74), but under AI assistance reliance becomes
     predominantly TASK-DEPENDENT (share ~0.32-0.41; Expert ~0). Therefore axis-1's
     "safety depends on WHO the user is" is, in the AI-assisted conditions,
     more precisely "depends on USER x TASK". State this as the framing implication
     for SPEC/H1a, without overclaiming (single dataset; GLMM corroboration pending).
   - Reference that prior adjudication established the over-dispersion is real
     (CIs exclude 0) and not a pure power artifact.
4. **Update PROGRESS.md** (Done + module status + a note that PR #2 framing now
   rests on this decomposition finding).
5. **Commit** in logical steps (code, tests, results, docs, pyproject) and PUSH to
   feature/e1-multicond. `git status` must be clean (no venv/*.txt scratch;
   data/raw not committed).

## DELIVERY
Return to Manager: confirmation of clean commit+push (list commit hashes), the
determinism check result, full pytest summary, and the one-paragraph honest
conclusion. Do NOT merge.
