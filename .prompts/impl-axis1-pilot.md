# impl-axis1-pilot — EXPLORATORY multi-family axis-1 pilot (CODE + OFFLINE TESTS ONLY)

You are an implementation subagent in worktree `.worktrees/axis1-pilot` (branch
`feature/axis1-pilot`, draft PR #8). **Build CODE + OFFLINE TESTS ONLY. Do NOT run the
real GitHub Models experiment** — the Manager runs the multi-family pilot. You do NOT
audit/merge. Report FACTS; do NOT claim "done/all green".

## ⚠️ EXPLORATORY STATUS (read carefully — this governs the whole slice)
This pilot is **EXPLORATORY ONLY**: (i) de-risk the multi-family, 5-condition pipeline
end-to-end, and (ii) produce **power-analysis input** (effect-size + variance estimates)
to size a later CONFIRMATORY run. It is **SEPARATE from the confirmatory analysis** and
must NEVER be used to tune conditions, thresholds (τ), or the model set. Label all outputs
(results JSON, docs, PROGRESS) **EXPLORATORY / NON-CONFIRMATORY**. Freeze NO thresholds.

## 0. FIRST: read the source of truth
Read: `SPEC.md` (§2 **C1 PRIMARY**; §3 **H1a**; §4.2 multi-family panel; §5 E1),
`INTERFACES.md` (§3 panel, §4 metrics, §8 AS-BUILT), `PROGRESS.md` (PR#4 panel redesign +
Known pitfalls + Preregistration), `docs/plans/2026-07-15-quota-strategy.md` (multi-family
rationale). Reuse the MERGED code: `src/twdf/panel/provider.py` (GitHubModelsProvider —
`model_name` param, hashlib cache, 0.8 s pacing, fail-fast on daily cap),
`src/twdf/panel/real_panel.py` (dual-system counterfactual pairing; strong personas; System-1
frozen across conditions), `src/twdf/data/bansal_tasks.py` (`render_ui_condition`),
`src/twdf/data/item_selector.py`, `src/twdf/metrics/overdispersion.py`
(`conflict_conditioned_reliance`, `betabinom_overdispersion_within_domain`,
`condition_correlation` = Spearman+permutation+bootstrap with n<3 degenerate guard,
`bootstrap_ci`), `src/twdf/experiments/e2_panel_redesign.py` (mirror), and
`results/e1_decomposition.json` / the Bansal loader for the per-condition HUMAN over-dispersion.

## 1. Two NEW infrastructure pieces (the real deliverables)
### (a) Faithful renderers for the 5 Bansal AI conditions (`bansal_tasks.py`)
H1a's cross-condition test requires ≥5 conditions MATCHED to the human data. Implement
`render_ui_condition` for all 5 Bansal AI conditions (exact strings):
`"Conf."`, `"Conf.+Single"`, `"Conf.+Double"`, `"Conf.+Adaptive"`, `"Conf.+Adaptive (Expert)"`.
- First, DERIVE + DOCUMENT the condition→content mapping. Inspect the task JSON fields (`X`
  raw text, `expert` = expert-highlighted spans with `class0/class1`, `system` = token-level
  model highlights) and the Bansal repo README
  (`https://github.com/uw-hai/Complementary-Performance`). Reasonable, DOCUMENTED mapping:
  Conf. = pred+conf, NO explanation; Conf.+Single/Double/Adaptive = pred+conf + top-1 / top-2 /
  adaptive-N model highlights derived from `system`; Conf.+Adaptive (Expert) = pred+conf +
  `expert` highlights. If the exact Bansal semantics are unclear, pick a defensible mapping,
  DOCUMENT it + flag the uncertainty for the auditor (exploratory tolerance).
- Keep the existing "Wrong-AI (dark)" + "Conf.+Placebo" (if present on main) intact.

### (b) Multi-provider run loop (`experiments/axis1_pilot.py`)
Run the panel across MULTIPLE model families (config lists models). For each model: run the
static counterfactual panel over all 5 conditions (System-1 computed once per
(persona,item,model,seed), FROZEN across the 5 conditions). The PANEL = personas × models;
compute panel disagreement per condition ACROSS personas×models. Reuse `GitHubModelsProvider`
per model (`model_name`), one provider per model; the cache dedups per (model,messages,...).

## 2. Config (built to RUN; you do NOT run it) — budget-conscious
`configs/axis1_pilot.yaml`:
- models: `["openai/gpt-4o", "meta/Llama-3.3-70B-Instruct", "microsoft/Phi-4"]`
- 6 personas (reuse PR#4's), **n_items: 10**, 5 conditions above, 1 seed,
  `inter_call_sleep: 0.8`, per-model `call_budget: 450`.
- Per model: System-1 = 6×10 = 60; System-2 = 6×10×5 = 300 → **360/model** (fits today's
  fresh per-model daily budget ~500). 3 models → ~1080 calls total.
- CLI: `python -m twdf.experiments.axis1_pilot --config configs/axis1_pilot.yaml` → writes
  `results/axis1_pilot.json` (labeled EXPLORATORY) with full run_manifest. **Do NOT execute.**
- Serialize ALL AgentResponse fields (incl. model, trace, trust_state).

## 3. Metrics + power-analysis readout (reuse Module C; label EXPLORATORY)
- Per (model, condition): panel disagreement (variance of per-persona conflict-conditioned
  reliance) + per-condition conflict-conditioned reliance.
- Per (pooled personas×models, condition): panel disagreement across the FULL panel.
- **Cross-condition axis-1 (mechanism view):** `condition_correlation` (Spearman + permutation
  + bootstrap, n=5 conditions → non-degenerate) between panel disagreement and the per-condition
  HUMAN over-dispersion (from Bansal `betabinom_overdispersion_within_domain` /
  e1_decomposition). Report per-model and pooled.
- **Cross-family agreement:** correlation/agreement of the per-condition disagreement RANKING
  across the 3 models (do families agree? SPEC §4.2 — trust only cross-family-consistent flags).
- **POWER INPUT (the pilot's main purpose):** report the observed effect-size estimate(s)
  (Spearman ρ + CI width; between-condition variance; between-persona/model variance
  components) and a short note on what N (personas × items × models × conditions) the
  CONFIRMATORY run would need for adequate power. This is an estimate ONLY; it must NOT feed
  back into choosing conditions/τ/model-set.

## 4. Tests (`tests/test_axis1_pilot.py`) — OFFLINE, mock providers (your validation gate)
- 5-condition renderers: each of the 5 produces DISTINCT content; Single⊂Double in highlight
  count (or documented ordering); Expert uses `expert`; Conf. has no explanation. No leakage of
  ground-truth label into any explanation.
- Multi-provider loop with 2–3 MOCK providers: System-1 FROZEN across all 5 conditions AND
  identical for a given (persona,item,seed) regardless of model's System-2; well-formed
  AgentResponses for every (model,condition).
- Cross-condition correlation + cross-family agreement on synthetic data with a KNOWN pattern
  (STRONG thresholds; do NOT weaken). Degenerate guard (n<3) respected.
- Cross-process determinism (subprocess). Mark any real-API test `@pytest.mark.live`, skip-safe.
- `pytest -m "not live"` GREEN; report counts.

## 5. Guardrails (§4.5)
System-1 frozen across all 5 conditions AND across models (tested); condition→content mapping
documented + faithful-as-possible (flag uncertainty); no label leakage; conflict-conditioned
DV; two axes separate; NO threshold freezing; EXPLORATORY labels everywhere; `hashlib` only
(grep `\bhash\(`); token never printed/committed; `data/cache/` + `data/raw/` gitignored;
exact Bansal condition strings; serialize all response fields; do NOT weaken tests.

## 6. Deliverables + wrap-up
Code (5-condition renderers, multi-provider `axis1_pilot.py`, config, any metric helpers),
`tests/test_axis1_pilot.py` (offline, green), update `PROGRESS.md` (a "Doing / EXPLORATORY
pilot code-complete, REAL RUN PENDING (Manager, multi-family)" entry) and `INTERFACES.md` §8
AS-BUILT (5 condition renderers + multi-provider loop). Commit (trailer `Co-authored-by:
Copilot <copilot@github.com>`) + push. Do NOT run the real experiment; do NOT commit
`results/axis1_pilot.json`. Return a FACTUAL report: the documented 5-condition mapping (+ any
uncertainty), the multi-provider design, metrics + power-readout plan, `pytest -m "not live"`
counts, and confirmation you did NOT call the real API. Manager runs the pilot, then audit + merge.
