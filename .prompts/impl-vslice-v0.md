You are the IMPLEMENTATION subagent for thin-vertical-slice v0 of the research
project "two-ways-a-design-fail" (a top-venue HCI METHODS paper). Rigor > speed.

## READ FIRST (in the main checkout, read-only)
- SPEC.md  (frozen design; focus on §0 axis-1, §5 E1, §8 statistics)
- INTERFACES.md  (implement STRICTLY to these signatures/schema; do NOT invent
  divergent schemas — this is the contract that keeps multi-session code fitting)
- PROGRESS.md  (context; Gate 1/2/3 all cleared)
- docs/research/2026-07-14-dataset-availability.md (verified dataset URLs)

## WHERE YOU WORK
Your worktree is: C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail\.worktrees\vslice-v0
Branch: feature/vslice-v0 (draft PR #1). Confirm `pwd` / `git rev-parse
--abbrev-ref HEAD` before editing. Work ONLY inside this worktree. DO NOT touch
the main checkout. NEVER merge. NEVER push to main. Commit trailer on EVERY
commit: `Co-authored-by: Copilot <copilot@github.com>`. Push to the draft PR
branch; do NOT mark ready.

## GOAL (the thin slice — prove the chain end-to-end)
Bansal real per-trial data -> canonical schema -> [SYNTHETIC panel stub, NOT a
live model] -> axis-1 beta-binomial OVER-DISPERSION metric + mean-predictor
baseline -> ONE "panel-disagreement vs human-over-dispersion" correlation number,
runnable via a CLI. The live panel engine (Module B) is DEFERRED — use a
deterministic synthetic panel stub so the whole pipeline runs offline.

## SCOPE — build exactly this
1. **Scaffold (S0):** `pyproject.toml` (package `twdf`, Python 3.12, deps: numpy,
   pandas, scipy; dev: pytest), `src/twdf/__init__.py`, package subdirs
   `data/ metrics/ panel/ experiments/`, and `configs/vslice_v0.yaml`. Installable
   with `pip install -e .`. Add a `run_manifest` helper that records config hash +
   seeds + package version for reproducibility.
2. **Data (Module A, partial):** `twdf/data/bansal.py` — download (if absent) the
   VERIFIED Bansal CSV to `data/raw/` (gitignored) from
   `https://raw.githubusercontent.com/uw-hai/Complementary-Performance/main/experiment-data/decision-result-filter.csv`
   and load it into the canonical per-trial schema from INTERFACES.md §1. Column
   mapping (verified real headers): assignmentId->user_id, questionId->task_id,
   condition->ui_condition, choice->human_final, y->ground_truth, pred->ai_advice,
   conf->confidence; derive `relied` (human_final == ai_advice) and `ai_correct`
   (ai_advice == ground_truth). Keep a passthrough `extra`. Provide a selector to
   pick ~10 tasks and ONE UI-condition pair (control vs one treatment) actually
   present in the data — inspect the real `condition` values and pick a valid pair;
   document which pair you chose and why.
3. **Metrics (Module C, axis-1 core) — HIGHEST RIGOR:** `twdf/metrics/overdispersion.py`
   - `betabinom_overdispersion(relied_by_user: dict[str,(int,int)]) -> result`:
     MUST separate TRUE between-user over-dispersion from binomial sampling noise
     (fit a hierarchical/beta-binomial model; report the dispersion parameter /
     excess variance over the p(1-p) binomial floor). It MUST NOT just return raw
     empirical variance — that is the #1 methodology failure and it silently
     collapses hypothesis H1a. Document the estimator and its assumptions in the
     docstring.
   - `within_task_diff(...)`: difficulty-controlled WITHIN-TASK counterfactual
     difference (difficulty cancels within the pair), NOT a pooled correlation.
   - `baseline_mean_predictor(...)`: a GENUINE baseline that outputs only p(1-p)
     and BY CONSTRUCTION cannot produce over-dispersion. Do not water it down.
   - `bootstrap_ci(stat_fn, data, over=("persona","seed"), n=10000, seed)`.
4. **Synthetic panel stub (Module B placeholder):** `twdf/panel/stub.py` — a
   DETERMINISTIC (seeded) generator that, given personas × the chosen tasks × the
   UI pair, emits AgentResponse-shaped records (INTERFACES §3) with a tunable
   disagreement level per UI condition. Clearly named/commented as a STUB standing
   in for the real model panel. It must let us compute a panel-disagreement signal
   per UI condition.
5. **E1-v0 glue:** `twdf/experiments/e1_vslice.py` (+ `python -m
   twdf.experiments.e1_vslice --config configs/vslice_v0.yaml`) that runs the
   whole chain and prints/saves: human between-user over-dispersion per UI
   condition, the synthetic panel disagreement per UI condition, and ONE
   correlation number between them, plus the mean-predictor baseline comparison,
   with a run_manifest. Output raw numbers to a file — never rely on restating
   numbers from memory.
6. **Tests:** `tests/` unit tests for the schema mapping, and CRITICAL tests for
   `betabinom_overdispersion`: (a) on pure-binomial synthetic data (all users same
   p) it returns ~zero over-dispersion; (b) on deliberately over-dispersed data
   (users split into high/low reliance) it returns clearly positive over-dispersion
   and BEATS the mean-predictor baseline. An integration test that runs the E1-v0
   chain on a tiny fixture. Keep any network-dependent test skippable offline.

## METHODOLOGY GUARDRAILS (this is a methods paper — see SPEC §8, and the
## project's §4.5 / §6 checklist). Your code will be hostilely audited for:
- over-dispersion truly SEPARATED from binomial noise (not raw variance);
- mean-predictor baseline genuine (p(1-p)) and actually beaten;
- difficulty controlled via within-task diff, not pooled correlation;
- no train/test leakage, no hidden global normalization;
- identity keys include EVERY output-affecting dimension
  (dataset/task/ui/persona/seed) — no silent collisions;
- deterministic under fixed seed; reruns converge;
- NO hallucinated numbers — results come from the actual re-run.
Do NOT freeze or invent τ_disp/τ_level thresholds — v0 is plumbing only; the PI
freezes thresholds later before real results.

## SELF-CHECK before you finish
- `pip install -e .` works; `pytest` passes; `python -m twdf.experiments.e1_vslice
  --config configs/vslice_v0.yaml` runs end-to-end and emits the correlation number.
- diff only touches your intended files; no debug residue; data/raw not committed.
- Update PROGRESS.md (Doing/Done + module status) inside your worktree.

## DELIVERY
Commit in logical steps to feature/vslice-v0; push to the draft PR (do NOT mark
ready, NEVER merge). Return to the Manager: what you built, the chosen UI pair,
the actual correlation number from the real run (quote the output file), test
results, and any assumptions/limitations the auditor should scrutinize.
