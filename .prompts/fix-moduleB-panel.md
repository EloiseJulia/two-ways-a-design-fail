# fix-moduleB-panel — pacing fix + real run (thin slice)

You are a focused fix subagent on branch `feature/moduleB-panel` in worktree
`.worktrees/moduleB-panel`. The Module B code is already implemented and its 6
offline tests pass. It is NOT merged. Your ONLY jobs: fix API pacing so the real
run completes, restore the intended thin-slice scale, clean scratch files, run the
real experiment ONCE, commit + push. Do NOT change the science (counterfactual
pairing, reliance def, metrics) or interfaces. Do NOT merge.

## Manager's empirical rate-limit findings (use these; do not re-derive)
GitHub Models token tier is high on paper (20,000 req/min header) BUT there is a
hidden BURST/token-bucket limit: ~20 rapid calls succeed, then HTTP 429. Measured
sustainable steady rate ≈ **≤1.5 req/s**. At 150ms spacing: 20 ok then 429s. At
**700ms spacing: 12/12 clean, no 429.** No `Retry-After` header is returned on 429.
The previous run failed because `inter_call_sleep=0.2` (5/s) and a short exponential
backoff could not drain the sustained overload.

## Fix 1 — provider pacing/backoff (`src/twdf/panel/provider.py`)
- Raise the DEFAULT `inter_call_sleep` to **0.8s** (≈1.25/s, safe margin under 1.5/s).
- On HTTP 429 specifically: wait a LONGER fixed cool-down to let the bucket refill —
  e.g. `wait = max(retry_after_if_present, 8.0)` seconds — then retry. Keep the
  existing exponential backoff for 5xx. Increase `max_retries` to 8 for 429.
- Keep the hard `call_budget` guard. Keep hashlib caching (cache hits cost 0 calls,
  so reruns are free and determinism holds). Do NOT log/print the token.

## Fix 2 — restore thin-slice scale (`configs/e1_panel_v1.yaml`)
- `n_tasks: 20` (was reduced to 5 during testing; the slice target is ~20 DIVERSE
  beer tasks spanning AI-correct/incorrect + a conf range).
- `inter_call_sleep: 0.8`
- `call_budget: 350` (real cost = System-1 5×20=100 shared + System-2 5×20×2=200 =
  **300 calls**; 350 gives margin). Confirm System-1 is computed ONCE per
  (persona,task) and reused across both UI arms — if the code recomputes it per arm,
  STOP and report (that would break the counterfactual invariant and inflate calls).

## Fix 3 — clean scratch files
- `git rm` the committed scratch files `experiment_output.txt` and `manual_run.log`
  (they should never have been committed). Ensure `.gitignore` covers `*.log`,
  `data/cache/`, `data/raw/`, and any `*_output.txt` scratch. Do NOT gitignore
  `results/*.json` (those are committed artifacts).

## Fix 4 — run the real experiment ONCE
- `GH_MODELS_TOKEN` is in your env (bridged at launch). Run:
  `python -m twdf.experiments.e1_panel_v1 --config configs/e1_panel_v1.yaml`
- It must complete (~300 calls at 0.8s ≈ 4–5 min) and write
  `results/e1_panel_v1.json` with a full `run_manifest` (config hash, seeds, model,
  timestamp, total_api_calls, cache_hits, wall_time, est_cost).
- If you STILL hit sustained 429 after the fix, increase `inter_call_sleep` to 1.0s
  and rerun (cache preserves completed calls, so progress is not lost). Report the
  final pacing that worked.

## Fix 5 — verify + commit + push
- Rerun `pytest -q` (offline) — must stay green; report counts.
- Confirm no builtin `hash()` (`\bhash\(` excluding hashlib) and token not committed.
- Commit (trailer `Co-authored-by: Copilot <copilot@github.com>`) and push to
  `feature/moduleB-panel`.
- Update the `PROGRESS.md` Done entry with the REAL numbers from the JSON.

## Report back (facts only — do NOT claim "done/all green")
Return: the pacing that worked (final inter_call_sleep, any 429s hit + recovered),
total API calls + cache hits + wall time + est cost, and the REAL result numbers
read from `results/e1_panel_v1.json`:
- per-persona reliance rate (control vs treatment),
- panel disagreement per arm,
- within-task reliance elasticity (treatment−control) + permutation p + bootstrap CI,
- System-1 accuracy vs ground truth (sanity),
- task-diversity summary (AI-correct/incorrect counts, conf range).
Also list any methodology caveats. The Manager + an independent auditor verify before merge.
