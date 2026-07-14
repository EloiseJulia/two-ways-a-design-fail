You are the FIX subagent for draft PR #2 (branch feature/e1-multicond) of the HCI
METHODS project "two-ways-a-design-fail". An independent hostile audit FAILED the
PR with 2 BLOCKERS + minors. Fix exactly these; do NOT expand scope beyond what's
listed; do NOT alter the verified-correct `betabinom_overdispersion` estimator's
math. NEVER merge.

## WHERE
Worktree: C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail\.worktrees\e1-multicond
Confirm `pwd` + branch (feature/e1-multicond) first. Work ONLY here; not the main
checkout. Commit trailer EVERY commit: `Co-authored-by: Copilot <copilot@github.com>`.
Push to the draft PR; do NOT mark ready; NEVER merge.

## BLOCKER-1 — over-dispersion fragile to UNDOCUMENTED task selection
The audit verified: v0 (Human rho=0.0369, ~2340 trials, 10 tasks) vs multicond
(Human rho=0.0000, ~1220 trials, min 3 tasks/domain). The signal VANISHED because
task selection changed silently. For a methods paper this fragility must be faced
honestly, not hidden. Do ALL of:
1. **Make per-condition over-dispersion use the MAXIMUM principled data**, not an
   arbitrary small shared-task subset. For axis-1 cross-condition comparison,
   compute each condition's human over-dispersion from ALL that condition's
   trials/users (within-domain aggregation — see BLOCKER-2), since domain is
   between-subjects. Make the task-selection knob explicit in the config with a
   documented default (e.g. `task_selection: all`), not a magic number buried in
   code.
2. **Add a ROBUSTNESS analysis**: compute and report Human (and ideally each
   condition's) over-dispersion under >=3 task-selection schemes — e.g. (a) ALL
   trials per condition, (b) v0's first-10-shared-tasks, (c) the current
   min-3/domain. Write these to a small table in `results/e1_multicond_robustness.json`
   and summarize in PROGRESS.md. The point is to SHOW whether the over-dispersion
   signal is robust or fragile — report the truth either way. Do NOT cherry-pick.
3. **Document** the chosen default selection + rationale in SPEC.md (a short note
   under E1) and PROGRESS.md, and explicitly state the fragility finding as a
   known caveat/limitation if the robustness table shows the signal is sensitive.
   Do NOT overclaim a "genuine finding" that only appears under one selection.

## BLOCKER-2 — misleading "stratified pooling" terminology
The code does NOT stratify (no per-stratum fits/weighting); it aggregates each
user's trials within their single domain. The audit verified every user saw
exactly 1 domain (between-subjects on domain). Fix:
1. Rename the function / variables from "stratified pooling" to accurate wording,
   e.g. `betabinom_overdispersion_within_domain` (or similar precise name), and
   update all call sites.
2. Fix the docstring to describe what the code ACTUALLY does, and state the
   between-subjects-on-domain fact (each user = one domain) so difficulty is not
   confounded across conditions BECAUSE users are compared within their domain.
   If you keep a difficulty-control abstraction for future within-subjects data,
   clearly mark it as such and note it is a no-op on this dataset.

## MINORS
- Remove any stray untracked results file (e.g. `results/e1_multicond_run2.json`);
  ensure `git status` is clean and no audit scratch is committed.
- Fix the permutation-test docstring so it matches the implementation (state
  exactly what is permuted — condition-level pairing/labels).
- Enhance `test_panel_stub_determinism` (carryover TODO) to actually catch
  CROSS-PROCESS nondeterminism: spawn a fresh subprocess (e.g. via
  `subprocess.run([sys.executable, ...])` running a tiny script that prints the
  stub disagreement) twice and assert identical output — a single-process double
  call does NOT catch hash-seed differences. If truly impractical, at minimum add
  `PYTHONHASHSEED` variation in the test and document the limitation.

## VERIFY BEFORE FINISHING
- `pip install -e .`; `pytest` ALL pass (incl. the enhanced determinism test).
- Both experiments run: `python -m twdf.experiments.e1_vslice --config
  configs/vslice_v0.yaml` (regression) and `python -m twdf.experiments.e1_multicond
  --config configs/e1_multicond.yaml`, TWICE each in separate processes → identical
  numbers.
- Robustness table generated and honestly summarized.
- `git status` clean; data/raw not committed.

## DELIVERY
Commit in logical steps; push to feature/e1-multicond (draft, never merge). Return
to Manager: exactly what changed for BLOCKER-1/2 + minors; the ROBUSTNESS TABLE
(quote the numbers) and your honest read of whether axis-1 over-dispersion is
robust or fragile on Bansal; the renamed function; full pytest summary. Flag
clearly if the robustness result is something the PI must interpret.
