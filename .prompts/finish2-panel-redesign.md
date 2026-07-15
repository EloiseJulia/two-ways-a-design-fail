# finish2-panel-redesign — tests + determinism + docs + commit (run ALREADY DONE)

You are a finishing subagent in worktree `.worktrees/panel-redesign` (branch
`feature/panel-redesign`, draft PR #4). The real experiment has ALREADY COMPLETED
and `results/e2_panel_redesign.json` exists; the response cache is fully populated,
so any rerun is FREE (0 API calls). Do NOT audit/merge your own work. Report FACTS.

## What is already done (do NOT redo the run)
- Code written: `src/twdf/data/item_selector.py`, `src/twdf/experiments/e2_panel_redesign.py`,
  `configs/e2_panel_redesign.yaml`, edits to `overdispersion.py` (conflict_conditioned_reliance,
  over_reliance_level), `real_panel.py` (strong personas + 3-cond), `bansal_tasks.py` (Wrong-AI).
- Manager also made these (uncommitted) fixes you must KEEP + commit:
  `provider.py` now takes `model_name` param + caps 429 cooldown at 120s (fails fast on
  daily-cap instead of sleeping ~13h); experiment passes `config['model']['name']`; config
  switched to `openai/gpt-4.1-mini`, `n_items: 20`, `call_budget: 560` (gpt-4o-mini daily
  quota was exhausted; per-model daily cap ≈500).
- REAL RESULT (from `results/e2_panel_redesign.json`, model gpt-4.1-mini, 480 calls, $0.18):
  * Overall CONFLICT RATE (System-1 ≠ AI) = **43.3%** (vs PR#3's 3% collapse).
  * Conflict-conditioned reliance: control Conf. = 0.327, treatment Conf.+Adaptive(Expert)
    = 0.481. Unconditional: 0.708 / 0.775.
  * Per-persona conflict reliance DIVERGES: control range 0.111 (p2-expert-trusting) →
    0.556 (p5-novice-trusting).
  * Axis-1 within-task elasticity (treatment−control, conflict trials) = +0.194,
    permutation p = 0.174, n_pairs=11 (positive direction, UNDERPOWERED / not significant).
  * Axis-2 Wrong-AI over-reliance level = 0.325 (per-persona 0.000–0.450); between-persona
    spread 0.0287.
  * System-1 accuracy 0.817; System-1 frozen invariant HOLDS across all 3 conditions.

## Your tasks
1. **Write `tests/test_panel_redesign.py`** (STRONG thresholds; do NOT weaken):
   - conflict_conditioned_reliance correctness on synthetic data (known conflict/switch);
   - System-1-frozen invariant across ALL 3 conditions (fixed persona,task,seed);
   - Wrong-AI condition renders the WRONG label (1 - ai_pred) + over_reliance_level
     correctness on synthetic data;
   - item selector determinism + criteria (selected items really are AI-wrong/low-conf/
     high-human-variance);
   - CROSS-PROCESS cache determinism (subprocess pattern from test_variance_decomposition.py
     / test_panel_real.py): rerun the experiment (or a small panel) in a separate process,
     assert byte-identical results EXCLUDING the run_manifest timestamp/wall_time; confirm
     total_api_calls==0 on the cached rerun.
   - Keep any live-API test `@pytest.mark.live` (skipped offline).
2. **Verify determinism yourself:** run the experiment once more (cache → expect
   `total_api_calls: 0`, `cache_hits: 480`); confirm the metric numbers above are UNCHANGED;
   then restore the committed results file if the rerun only changed the manifest timestamp
   (i.e. `git checkout -- results/e2_panel_redesign.json` after confirming non-manifest bytes
   match). If ANY metric number changed, STOP and report.
3. `pytest -q` — green overall; report counts. Grep `\bhash\(` (excl hashlib/comments)=0.
   Confirm token not committed; `data/cache/` + `data/raw/` gitignored.
4. **Update docs:** `PROGRESS.md` Done entry (real numbers above; frame HONESTLY: the
   redesign RESOLVES the compliance-collapse — conflict rate 3%→43%, personas now diverge,
   positive-but-underpowered explanation elasticity, real axis-2 wrong-AI signal; CAVEATS:
   model switched to gpt-4.1-mini (not same-model comparable to PR#3), elasticity not
   significant (n=11), single domain/20 items/6 personas, one persona shows axis-2=0).
   `INTERFACES.md` §8 AS-BUILT (new metrics conflict_conditioned_reliance + over_reliance_level;
   item_selector; provider model_name param + 120s cooldown cap; 3-condition panel; e2 experiment).
5. **Commit + push:** stage source/config/tests/results/docs (NOT scratch: *.log, *_output.txt,
   data/cache, data/raw). Trailer `Co-authored-by: Copilot <copilot@github.com>`. Push to
   `feature/panel-redesign`.

## Report (FACTS)
pytest counts; determinism result (cached rerun api_calls, non-manifest bytes identical y/n);
confirmation the metric numbers match; any issue found (e.g. the p5 axis-2=0 anomaly — note
whether it's a parsing artifact or genuine). Independent audit + Manager verification follow.
