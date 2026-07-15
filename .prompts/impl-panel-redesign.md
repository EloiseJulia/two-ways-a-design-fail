# impl-panel-redesign — Panel DV redesign for dynamic range (axis-1 + first axis-2)

You are an implementation subagent working in worktree `.worktrees/panel-redesign`
(branch `feature/panel-redesign`). You implement code and push to draft PR #4. You
do NOT audit or merge your own work. Report FACTS; the Manager gates merge on an
independent audit. Do NOT claim "done/all green."

## 0. FIRST: read the source of truth
Read: `SPEC.md` (esp. §0 two-axis, §2 contributions incl. new **C0** + the honest
panel-status note, H1a), `INTERFACES.md` (§3 Panel, §4 metrics incl.
`over_reliance_level`, §8 AS-BUILT), `PROGRESS.md` (Known pitfalls, Preregistration,
and the **PR #3 Manager diagnosis** of the panel null), and the ALREADY-MERGED
Module B code you are extending:
`src/twdf/panel/provider.py` (GitHubModelsProvider + hashlib cache — REUSE as-is),
`src/twdf/panel/real_panel.py` (dual-system counterfactual pairing — EXTEND),
`src/twdf/data/bansal_tasks.py` (task stimuli loader + `render_ui_condition`),
`src/twdf/data/bansal.py` (CSV loader; `task_id`==`questionId`),
`src/twdf/metrics/overdispersion.py` (betabinom_overdispersion, within_task_diff,
bootstrap_ci, paired_permutation_test), `configs/e1_panel_v1.yaml`,
`results/e1_panel_v1.json`, `tests/test_panel_real.py`.

## 1. WHY (the problem you are fixing)
PR #3's first real panel run was a NULL diagnosed as **compliance-collapse**: in 97%
of cells the agent never moved from its own System-1 anchor, so measured "reliance"
≈ agent↔AI *agreement*, not adoption; personas barely diverged. Root causes: (a) the
reliance DV conflated agreement with adoption; (b) items were too easy (agent never
uncertain); (c) no wrong-AI pressure; (d) weak persona conditioning. This slice fixes
all four to give the axis-1 mechanism real dynamic range, and adds a first axis-2
reading. **A continued null after these fixes is itself a valid, important finding —
report it honestly; do NOT tune to manufacture a positive.**

## 2. Fix A — conflict-conditioned reliance DV (the core metric fix)
Define reliance on the subset of trials where the agent's **System-1 decision ≠ the
AI advice shown** (genuine conflict — the only trials where AI advice can actually
move the agent). Add to `src/twdf/metrics/overdispersion.py`:
- `conflict_conditioned_reliance(responses)` → per (persona[,condition]) the fraction
  of CONFLICT trials on which the agent SWITCHED to the AI advice (final == ai_advice
  given system1 != ai_advice). Also return `n_conflict` per cell.
- Keep the existing unconditional reliance too, and REPORT BOTH side by side for
  transparency. The conflict-conditioned one is the PRIMARY axis-1 DV now.
- Guard: if `n_conflict` is tiny for a cell, flag it (underpowered) rather than
  silently averaging. Report the per-cell conflict counts in the results JSON.

## 3. Fix B — data-driven hard/ambiguous item selection (PI-approved approach)
Add `select_hard_items(...)` (in `bansal_tasks.py` or a small new selector module).
Using the Bansal CSV + task JSON, deterministically (sorted + fixed seed) select
~30 beer items that concentrate CONFLICT/ambiguity, by these DATA-DRIVEN criteria:
- items where the **AI is WRONG** (`pred != Y`) and/or **low AI confidence** (`conf`
  in the lower range), AND
- items where **human reliance actually VARIES** across users (compute per-item human
  reliance rate + variance from the CSV; prefer higher-variance items).
Report the selection: counts of AI-wrong / low-conf / high-human-variance, and the
distribution of `conf`. This calibrates WHERE we look to the loci of real human
heterogeneity. **LEAKAGE GUARD:** using human reliance to SELECT items is allowed and
must be disclosed, but the panel agents MUST NOT see human outcomes/reliance in any
prompt, and human reliance MUST NOT be fed as a predictor. Item selection ≠ label leakage.

## 4. Fix C — stronger persona conditioning (make personas behaviorally distinct)
The current personas (trait floats → mild system-prompt text) barely change behavior.
Strengthen conditioning so personas actually diverge:
- Translate traits into an EXPLICIT decision policy in the system prompt (e.g., a
  skeptical/low-AI-literacy persona is instructed to distrust AI, demand strong
  textual evidence, and keep its own read unless clearly wrong; a trusting/high-AI-
  literacy persona is instructed to defer to confident AI). Make the instructions
  concrete and behaviorally consequential, tied to domain_skill / ai_literacy /
  risk_sensitivity / caution.
- Keep meaningful temperature + prior_mix variation across personas.
- Use ≥6 personas spanning the trait space.
- Personas remain SYNTHETIC proxies (disclose in SPEC/PROGRESS caveats — do not claim
  validated human archetypes).
- VERIFY + REPORT that personas now diverge: per-persona conflict-conditioned reliance
  and the between-persona spread (panel disagreement). If they STILL collapse, say so.

## 5. Fix D — first axis-2 (WRONG-AI dark condition)
Add a THIRD condition alongside control/treatment: a **dark "Wrong-AI"** condition
where the AI advice shown is the WRONG label (on the selected items), presented with
**pseudo-high confidence + oppressive responsibility framing** (cognitive-semantic
dark pattern; in scope). Render it via `render_ui_condition` (add the new condition
string; document the mapping; keep exact Bansal strings for the two existing ones).
- Compute axis-2 `over_reliance_level(responses)` per INTERFACES §4 = systematic
  adoption of WRONG AI advice across the panel (fraction adopting the wrong label).
- Axis-2 pass concept: even if between-persona disagreement ≈ 0 (uniform), high
  adoption of wrong AI ⇒ high-risk flag (closes the "uniformly lethal" blind spot).
  You are producing the SIGNAL here; NOT freezing τ_level (prereg stays unfrozen).

## 6. Panel run + config (`configs/e2_panel_redesign.yaml`, `experiments/e2_panel_redesign.py`)
- 3 conditions: control `"Conf."`, treatment `"Conf.+Adaptive (Expert)"`, dark
  `"Wrong-AI (dark)"` (or similar clearly-labeled string). System-1 computed ONCE per
  (persona,task,seed) and FROZEN across ALL three conditions (invariant MUST hold +
  be tested). ~6 personas × ~30 items × 3 conditions.
- Pacing (Manager-measured): `inter_call_sleep: 0.8`, 8s cool-down on 429,
  `call_budget` sized to (System-1 6×30=180 + System-2 6×30×3=540 = ~720) + margin,
  e.g. 800. Reuse the hashlib cache (new items/conditions = new entries; reruns free).
- CLI: `python -m twdf.experiments.e2_panel_redesign --config configs/e2_panel_redesign.yaml`
  → `results/e2_panel_redesign.json` with full `run_manifest` (config hash, seeds,
  model, timestamp, total_api_calls, cache_hits, wall_time, est_cost).

## 7. Metrics to report (raw JSON = source of truth)
- **Axis-1:** per-persona conflict-conditioned reliance (control, treatment) + n_conflict;
  between-persona over-dispersion (betabinom) + panel disagreement per condition;
  within-task elasticity (treatment−control) on conflict trials + paired permutation p
  + bootstrap CI.
- **Axis-2:** `over_reliance_level` on the Wrong-AI condition (+ per-persona spread).
- **Sanity:** System-1 accuracy vs ground truth; conflict rate (fraction of cells with
  system1 ≠ AI) — this should now be substantially >3% (the whole point).
- Report unconditional reliance too (comparison to PR #3's 0.73).

## 8. Tests (`tests/test_panel_redesign.py`)
- Conflict-conditioning correctness on synthetic data (known conflict/switch pattern).
- System-1-frozen invariant ACROSS ALL THREE conditions (fixed persona,task,seed).
- Wrong-AI condition renders the WRONG label (not the correct one) + over_reliance_level
  correctness on synthetic data.
- Cross-process cache determinism (subprocess pattern; reuse from existing tests).
- Item selector determinism + criteria (selected items really are AI-wrong/low-conf/
  high-variance). Keep the live-API end-to-end test `@pytest.mark.live` (skipped offline).
- Do NOT weaken any existing test. `pytest -q` must stay green overall.

## 9. Methodology guardrails (§4.5 — auditor WILL check)
Token never printed/committed; `data/cache/` + `data/raw/` gitignored; `hashlib` only
(grep `\bhash\(`); System-1 frozen across all 3 arms (tested cross-process); conflict-
conditioning defined a priori; NO human reliance in agent prompts / as predictor
(item-selection use disclosed); Wrong-AI condition genuinely shows the wrong label;
two axes computed SEPARATELY; NO threshold freezing (τ stays unfrozen); NO post-hoc
tuning toward a positive; exact Bansal condition strings for the two carried-over
conditions; every number reproducible from a clean (cached) rerun.

## 10. Deliverables + wrap-up
Code (metrics additions, selector, extended real_panel + render, new experiment +
config, tests); run the real experiment ONCE; commit `results/e2_panel_redesign.json`;
`pytest -q` green; update `PROGRESS.md` (Done entry with REAL numbers incl. conflict
rate + axis-2 level) and `INTERFACES.md` §8 AS-BUILT. Commit (trailer
`Co-authored-by: Copilot <copilot@github.com>`) + push to `feature/panel-redesign`.
Do NOT clean/commit scratch (*.log, *_output.txt). Return a concise FACTUAL report:
conflict rate (vs 3% before), per-persona conflict-conditioned reliance + spread,
axis-1 over-dispersion + elasticity + p + CI, axis-2 over-reliance level, System-1
accuracy, item-selection summary, API calls/cache/cost, and whether personas now
diverge or still collapse. Independent audit + Manager verification follow.
