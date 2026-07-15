# finish-panel-redesign — complete the incomplete redesign slice

You are a continuation subagent in worktree `.worktrees/panel-redesign` (branch
`feature/panel-redesign`, draft PR #4). A previous impl subagent WROTE the code but
RAN OUT OF TURNS before finishing. Your job: finish it end-to-end. Do NOT redesign
the science; the design spec is `.prompts/impl-panel-redesign.md` (READ IT FIRST for
full context) — you are completing steps it didn't finish. Do NOT audit/merge your
own work. Report FACTS; do NOT claim "done/all green."

## Current state (verified by Manager)
- Modules already written + import cleanly: `src/twdf/data/item_selector.py`,
  `src/twdf/experiments/e2_panel_redesign.py`, `configs/e2_panel_redesign.yaml`, and
  edits to `src/twdf/metrics/overdispersion.py` (new `conflict_conditioned_reliance`,
  `over_reliance_level`), `src/twdf/panel/real_panel.py` (stronger personas + 3-cond),
  `src/twdf/data/bansal_tasks.py` (Wrong-AI render).
- NOT done: (a) the real experiment run never completed → `results/e2_panel_redesign.json`
  is MISSING; (b) NO test file `tests/test_panel_redesign.py`; (c) PROGRESS/INTERFACES
  not updated; (d) NOTHING committed. Cache has ~203 partial entries (completing the
  run is cheaper). Nothing is committed/pushed yet.

## Steps (do all)
1. **Sanity self-review** the written code against `.prompts/impl-panel-redesign.md`
   §2–§6: conflict-conditioned reliance is System-1≠AI→switched-to-AI; System-1 frozen
   across ALL 3 conditions; Wrong-AI condition shows the WRONG label; item selector is
   deterministic + data-driven (AI-wrong/low-conf/high-human-variance) and does NOT put
   human reliance into agent prompts. Fix any bug you find that would block a correct run.
2. **Run the real experiment ONCE** (token is in your env; pacing 0.8s / 8s cooldown on
   429; ~720 calls minus cache): `python -m twdf.experiments.e2_panel_redesign --config
   configs/e2_panel_redesign.yaml`. It must write `results/e2_panel_redesign.json` with a
   full `run_manifest` (config hash, seeds, model, timestamp, total_api_calls, cache_hits,
   wall_time, est_cost). If you hit sustained 429, raise inter_call_sleep to 1.0 and rerun
   (cache preserves progress). Report the pacing that worked.
3. **Write `tests/test_panel_redesign.py`** (per impl prompt §8, STRONG thresholds, do NOT
   weaken): conflict-conditioning correctness on synthetic data; System-1-frozen invariant
   across all 3 conditions; Wrong-AI renders the wrong label + `over_reliance_level`
   correctness; item-selector determinism + criteria; cross-process cache determinism
   (subprocess pattern from `tests/test_variance_decomposition.py` / `test_panel_real.py`).
   Keep any live-API test `@pytest.mark.live` (skipped offline).
4. **Verify:** `pytest -q` green overall (report counts); grep `\bhash\(` (excl hashlib/
   comments)=0; confirm token not committed; confirm `data/cache/` + `data/raw/` gitignored.
5. **Update docs:** `PROGRESS.md` Done entry with the REAL numbers (see §7 of impl prompt:
   conflict rate vs PR#3's 3%, per-persona conflict-conditioned reliance + between-persona
   spread, axis-1 over-dispersion + elasticity + p + CI, axis-2 over_reliance_level,
   System-1 accuracy, item-selection summary, API/cache/cost, and WHETHER personas now
   diverge or still collapse — report honestly either way). `INTERFACES.md` §8 AS-BUILT
   (new metrics, item_selector, 3-condition panel, e2 experiment).
6. **Commit + push:** stage ONLY source/config/tests/results/docs (NOT scratch like *.log,
   *_output.txt, data/cache, data/raw). Trailer `Co-authored-by: Copilot
   <copilot@github.com>`. Push to `feature/panel-redesign`.

## Report back (FACTS)
The headline make-or-break numbers: conflict rate (fraction of cells with System-1 ≠ AI,
vs 3% in PR#3), per-persona conflict-conditioned reliance + between-persona spread /
panel disagreement, axis-1 over-dispersion, within-task elasticity + permutation p +
bootstrap CI, axis-2 over_reliance_level on Wrong-AI, System-1 accuracy, item-selection
summary, API calls/cache hits/cost, pytest counts. State plainly whether the redesign
produced heterogeneity or the panel still collapses. Independent audit + Manager
verification follow — do not merge.
