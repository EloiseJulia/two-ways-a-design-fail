# impl-e4-compliance — axis-2 dark-pattern sensor + placebo baseline (CODE + OFFLINE TESTS ONLY)

You are an implementation subagent in worktree `.worktrees/e4-compliance` (branch
`feature/e4-compliance`, draft PR #7). **Build CODE + OFFLINE TESTS ONLY. Do NOT run the
real GitHub Models experiment** — the Manager runs it afterward (subagents keep dying on
long API runs, and daily quota is scarce). You do NOT audit/merge your own work. Report
FACTS; do NOT claim "done/all green".

## 0. FIRST: read the source of truth
Read: `SPEC.md` (§2 — **C1 is now PRIMARY**; §5 **E4** row; §3 **H3**), `INTERFACES.md`
(§3 panel, §4 metrics incl. `over_reliance_level`, §8 AS-BUILT), `PROGRESS.md` (PR#4 panel
redesign entry — conflict-conditioned reliance, wrong-AI 0.325, p5 backfire; Known pitfalls;
Preregistration). Reuse the MERGED PR#4 code you are extending:
`src/twdf/panel/provider.py` (GitHubModelsProvider — `model_name` param, hashlib cache, 0.8s
pacing, 120s cooldown cap), `src/twdf/panel/real_panel.py` (dual-system counterfactual
pairing; strong personas; System-1 frozen across conditions),
`src/twdf/data/bansal_tasks.py` (`render_ui_condition` with "Conf." / "Conf.+Adaptive
(Expert)" / "Wrong-AI (dark)"), `src/twdf/data/item_selector.py` (hard-item selection),
`src/twdf/metrics/overdispersion.py` (`conflict_conditioned_reliance`, `over_reliance_level`,
`paired_permutation_test`, `bootstrap_ci`), `src/twdf/experiments/e2_panel_redesign.py`
(the experiment to mirror), `configs/e2_panel_redesign.yaml`, `tests/test_panel_redesign.py`.

## 1. GOAL (E4 — formalize the axis-2 sensor + placebo compliance floor)
Per SPEC E4/H3: add a **PLACEBO-explanation** condition to isolate the "compliance floor"
(reliance induced by mere explanation PRESENCE, independent of explanation VALUE), alongside
the existing faithful and wrong-AI(dark) conditions, and formalize the **axis-2 systematic
over-reliance sensor**. Four conditions (System-1 frozen across ALL of them):
1. **control** = `"Conf."` — AI pred + conf, NO explanation.
2. **faithful** = `"Conf.+Adaptive (Expert)"` — pred + conf + the real `expert` highlight
   explanation.
3. **placebo** = `"Conf.+Placebo"` (NEW) — pred + conf + a NON-INFORMATIVE explanation:
   present, matched in length/format to faithful, but carrying NO task-specific
   decision-relevant content (generic boilerplate about "the model analyzed features and is
   confident", or non-diagnostic filler). Document the placebo text + that it is
   content-free by construction. The ONLY intended difference from faithful is
   informativeness.
4. **dark** = `"Wrong-AI (dark)"` — the WRONG label + pseudo-high-confidence + oppressive
   responsibility framing (reuse PR#4's rendering).
Add the `"Conf.+Placebo"` case to `render_ui_condition` (exact string; document mapping).

## 2. Metrics + hypotheses (reuse Module C; add only what's missing)
Use **conflict-conditioned reliance** (System-1 ≠ AI trials) as the primary DV (per PR#4).
- **Compliance floor (H3):** reliance(placebo) − reliance(control) ≥ 0 (presence alone
  induces reliance) AND reliance(placebo) < reliance(faithful) (genuine value beyond
  presence). i.e. **control < placebo < faithful**. Report all three conflict-conditioned
  reliances + per-persona, with `paired_permutation_test` for the placebo−control and
  faithful−placebo contrasts, and `bootstrap_ci`.
- **Axis-2 sensor (formalize):** `over_reliance_level` on the dark (wrong-AI) condition =
  systematic adoption of WRONG AI. Add a formal sensor value = over_reliance_level on
  wrong-AI, and ALSO report a placebo-baselined version (over_reliance minus the placebo
  compliance floor) as the "compliance-adjusted" axis-2 reading. Per-persona breakdown
  (surface any dark-pattern BACKFIRE persona like PR#4's p5).
- Also report unconditional reliance per condition for transparency, and System-1 accuracy.
Put any new stat helper in `overdispersion.py` following existing style + docstrings.

## 3. Experiment + config (built to RUN, but you do NOT run it)
- `configs/e4_compliance.yaml`: model `openai/gpt-4.1-mini` (consistent with PR#4), 6
  personas (reuse PR#4's), n_items 15 (budget-conscious: 6×15×(1 System-1 + 4 System-2) =
  90 + 360 = 450 calls), `inter_call_sleep: 0.8`, `call_budget: 520`, cache_dir
  `data/cache/panel`, 4 conditions above, seeds consistent with PR#4.
- `src/twdf/experiments/e4_compliance.py`: CLI `python -m twdf.experiments.e4_compliance
  --config configs/e4_compliance.yaml` → writes `results/e4_compliance.json` with full
  run_manifest. **Do NOT execute it.** System-1 computed ONCE per (persona,task,seed),
  FROZEN across all 4 conditions (invariant). Serialize ALL AgentResponse fields
  (persona_id, model, task_id, ui_condition, seed, system1_decision, final_decision,
  relied, confidence, trace, trust_state) — PR#3 had a bug here; do NOT regress.

## 4. Tests (`tests/test_e4_compliance.py`) — OFFLINE, mock provider (this is your validation)
Since you don't run the real API, tests are the main correctness gate:
- Placebo renderer: `"Conf.+Placebo"` produces a present-but-content-free explanation; it is
  DISTINCT from faithful and control; it does NOT leak the task's decision-relevant content.
- 4-condition panel with a MOCK provider: System-1 frozen across all 4 conditions (fixed
  persona,task,seed); `run_panel`/experiment wiring produces well-formed AgentResponses for
  all 4 conditions.
- Compliance-floor + axis-2 metrics on SYNTHETIC data with a KNOWN pattern (STRONG thresholds,
  do NOT weaken): e.g. construct responses where control<placebo<faithful and confirm the
  metric recovers it; construct a wrong-AI adoption pattern and confirm over_reliance_level +
  compliance-adjusted value.
- Cross-process determinism of the metric/pipeline on cached/mock inputs (subprocess pattern).
- `pytest -m "not live"` must be GREEN; report counts. Mark any real-API test `@pytest.mark.live`
  and make it skip-safe (skip if cache cold / quota — reuse the PR#4 skip-guard pattern; do
  NOT hard-fail).

## 5. Methodology guardrails (§4.5)
System-1 frozen across all 4 conditions (tested); placebo genuinely content-free (documented)
+ does not leak decision-relevant content; two axes computed SEPARATELY; conflict-conditioned
DV; NO threshold freezing (τ stays unfrozen); `hashlib` only (grep `\bhash\(`); token never
printed/committed; `data/cache/` + `data/raw/` gitignored; exact Bansal condition strings; do
NOT weaken tests. Serialize all response fields.

## 6. Deliverables + wrap-up
Code (placebo render, e4 experiment + config, metric helpers), `tests/test_e4_compliance.py`
(offline, green), update `PROGRESS.md` (a "Doing / code-complete, REAL RUN PENDING (Manager,
gpt-4.1-mini)" entry describing E4 + the 4 conditions + hypotheses) and `INTERFACES.md` §8
AS-BUILT. Commit (trailer `Co-authored-by: Copilot <copilot@github.com>`) + push to
`feature/e4-compliance`. Do NOT run the real experiment; do NOT commit `results/e4_compliance.json`
(it doesn't exist yet — the Manager will generate it). Return a FACTUAL report: what you built,
the 4 conditions + placebo text, the metrics + hypotheses, `pytest -m "not live"` counts, and
confirmation you did NOT call the real API. Manager runs the experiment, then audit + verify + merge.
