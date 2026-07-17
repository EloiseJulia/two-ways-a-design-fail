# INTERFACES.md — Data Schema & Function Signatures (contract)

> **The key artifact that keeps multi-session code from failing to fit together.**
> Every subagent implements STRICTLY to these signatures and NEVER changes another
> module's interface without escalating to the Manager/PI. This is a SKELETON —
> signatures are proposed defaults, to be ratified/refined during slice specs.
> Language: Python 3.12. Package name (proposed): `twdf`.

## 0. Conventions
- Immutable config via dataclasses / pydantic; all randomness takes an explicit
  `seed: int`. Every run writes a `run_manifest` (config hash + seeds + versions)
  for reproducibility & preregistration.
- DataFrames use snake_case columns; primary keys MUST include EVERY dimension
  that affects output (dataset, task, ui, persona, model, seed) to avoid silent
  collisions ("identity-dimension" rule).

## 1. Canonical per-trial schema (Module A output)
One row = one human decision trial after unification.
```
trial_id: str            # unique
dataset: str             # 'bansal21' | 'luyin21' | ...
user_id: str             # human participant id
task_id: str             # decision item id
ui_condition: str        # interaction condition / intervention label
ai_advice: int|str       # AI recommendation shown
ai_correct: bool         # was the AI advice correct
human_initial: int|str   # pre-AI decision (if available; else NA)
human_final: int|str     # final decision
ground_truth: int|str    # task correct answer
relied: bool             # did human adopt AI advice on this trial
task_difficulty: float   # controlled covariate (NA if unknown)
confidence: float|NA     # if logged
rt_ms: float|NA          # response time if logged
extra: dict              # dataset-specific passthrough
```

## 2. Atomic feature vector (Module A / §4.3)
```python
@dataclass(frozen=True)
class UIFeatureVector:
    ui_condition: str
    info_density: float
    visual_salience: float        # cognitive-semantic proxy only, not retinal
    authority_cue: float
    interruption_freq: float
    explanation_faithfulness: float
    latency_cost: float
    # ... extensible; keep documented + bounded [0,1] where possible

def extract_features(condition_meta: dict) -> UIFeatureVector: ...
```

## 3. Panel engine (Module B)
```python
@dataclass(frozen=True)
class Persona:
    persona_id: str
    domain_skill: float
    ai_literacy: float
    risk_sensitivity: float
    caution: float
    temperature: float
    prior_mix: float

@dataclass(frozen=True)
class AgentResponse:
    persona_id: str
    model: str
    task_id: str
    ui_condition: str
    seed: int
    system1_decision: int|str     # pre-AI anchor
    final_decision: int|str       # post-intervention
    relied: bool
    confidence: float
    trace: dict                   # full reasoning trace / logits if available
    trust_state: float|None       # sequential stateful mode only

class ModelProvider(Protocol):
    def generate(self, prompt: str, *, seed: int, max_tokens: int,
                 temperature: float) -> str: ...
    name: str

def run_panel(personas: list[Persona], tasks: list[str],
              ui_pair: tuple[str, str], providers: list[ModelProvider],
              *, seeds: list[int], mode: str = "static",
              friction: FrictionBudget | None = None) -> list[AgentResponse]: ...
```
- `mode`: "static" (counterfactual pairing) | "sequential" (Bayesian trust).
- Counterfactual pairing MUST hold System-1 state fixed across the UI pair.

## 4. Metrics & statistics (Module C) — highest verification priority
```python
# Axis 1: separate TRUE between-user over-dispersion from binomial noise.
def betabinom_overdispersion(relied_by_user: dict[str, tuple[int, int]]
                             ) -> OverdispersionResult: ...
#   input: user_id -> (n_relied, n_trials). MUST NOT return raw variance.

# Axis 1 main estimator: difficulty-controlled WITHIN-TASK counterfactual diff.
def within_task_diff(paired: PairedResponses) -> DiffResult: ...

# Axis 2: systematic over-reliance level on WRONG AI (separate from axis 1).
def over_reliance_level(responses: list[AgentResponse]) -> float: ...

# Baselines (must NOT be watered down). mean-predictor outputs only p(1-p).
def baseline_mean_predictor(...) -> ...: ...
def baseline_random(...) -> ...: ...
def baseline_prompt_only(...) -> ...: ...
def baseline_single_model(...) -> ...: ...
def null_rational_bayes(...) -> ...: ...

def bootstrap_ci(stat_fn, data, *, over=("persona", "seed"),
                 n: int = 10000, seed: int) -> tuple[float, float, float]: ...
def permutation_test(...) -> PValue: ...
def benjamini_hochberg(pvals: list[float], alpha: float = 0.05) -> list[bool]: ...
# alignment / calibration
def pas(...) -> float: ...
def ecs(...) -> float: ...
def ece(...) -> float: ...
```
LEAKAGE RULE: any normalization/standardization params for LOIO (E3) MUST be fit
on the TRAIN split only, never on the held-out intervention class.

## 5. Calibration & protocol (Module D)
```python
def fit_thresholds(calib: CalibrationSet) -> Thresholds:  # tau_disp, tau_level
    ...  # learned ONCE in feature space; FROZEN before results (log timestamp)

def triage(design_features: UIFeatureVector, signals: AxisSignals,
           thresholds: Thresholds) -> TriageDecision:
    ...  # -> "release" | "human_study" | "abstain"; either axis over -> human_study
```

## 6. Experiments & reporting (Module E)
```python
def run_experiment(name: str, config: ExperimentConfig) -> ExperimentResult: ...
# CLI: python -m twdf.experiments.e1 --config configs/vslice_v0.yaml
```
Any result summary is authoritative only from the re-run RAW output, never an
agent's chat restatement of numbers.

## 7. Directory layout (proposed)
```
src/twdf/{data,features,panel,metrics,calibration,experiments}/
configs/           # yaml run configs (vslice_v0.yaml, ...)
tests/             # unit + integration (module seams get tests)
docs/{plans,research,handoff}/
```

## 8. AS-BUILT (reconciliation — actual state after PR #1 + PR #2 + PR #3 + E2 Panel Redesign + PR #5 Lu&Yin + PR #6 Bansal Discriminator)
> This section reflects what is ACTUALLY implemented on `main`, to prevent drift.
- **data** — `twdf/data/bansal.py`: auto-downloads + loads Bansal to the canonical
  schema; multi-condition selector with `task_selection` config
  (`all` | `first_10_shared` | `min_per_domain`; default `all`). 
  `twdf/data/bansal_tasks.py`: Beer task stimulus loader with AI predictions + expert
  explanations; testid→questionId join verified (50/50 overlap).
  **NEW (PR #5):** `twdf/data/luyin.py`: Loader for Lu&Yin CHI'21 dataset (income prediction 
  tasks, 301 users × 30 tasks each, within-subject sequential design). Auto-downloads from 
  https://github.com/ZhuoranLu/Trustworthy-ML, canonical schema mapping with dtype coercion 
  (boolean strings → bool), ground_truth derivation from finalCorrect+finalPrediction. 
  Reliance = `finalPrediction == AI advice` (same as Bansal). Conflict-conditioned reliance 
  computed for robustness (reliance among `selfPrediction ≠ AI` trials). Determinism verified.
  **NEW (E2):** `twdf/data/item_selector.py`: Data-driven hard/ambiguous item selection
  (Fix B) using weighted criteria (AI-wrong, low-conf, high-human-variance); deterministic
  with sorted+seeded RNG; `ItemSelectionCriteria` dataclass + `select_hard_items()` +
  `compute_human_reliance_variance()` functions. Includes leakage guard (human variance
  used ONLY for selection, NOT in agent prompts).
- **metrics** — `twdf/metrics/overdispersion.py`: `betabinom_overdispersion`,
  `betabinom_overdispersion_within_domain` (renamed from misleading "stratified
  pooling"; domain is BETWEEN-SUBJECTS), `baseline_mean_predictor`, `within_task_diff`,
  `bootstrap_ci`, cross-condition correlation (Spearman + permutation + bootstrap,
  with n<3 `degenerate` guard), `paired_permutation_test()` for within-task elasticity
  (hashlib-seeded, paired permutation scheme).
  **NEW (E2 — Fixes A + D):** `conflict_conditioned_reliance()` (PRIMARY axis-1 DV,
  computes reliance ONLY on conflict trials where system1 ≠ AI, resolving PR#3's
  agreement-collapse; returns `ConflictConditionedRelianceResult` with conflict/unconditional
  rates + per-cell counts), `over_reliance_level()` (axis-2 DV for Wrong-AI dark condition,
  measures adoption of WRONG AI advice; returns `OverRelianceLevelResult` with panel-wide
  + per-persona adoption rates + between-persona spread).
  `twdf/metrics/variance_decomposition.py`: `split_half_reliability` (PRIMARY,
  ICC(2,1) + Spearman-Brown → `stable_user_share` + CI) and
  `variance_components_glmm` (`BinomialBayesMixedGLM`, bounded maxiter=10; currently
  NON-CONVERGENT, reported honestly as corroboration-unavailable).
- **panel** — `twdf/panel/stub.py`: SYNTHETIC deterministic stub only (v0/PR#1/PR#2).
  `twdf/panel/provider.py`: `GitHubModelsProvider` implementing `ModelProvider` protocol,
  reads `GH_MODELS_TOKEN` from env, hashlib-based deterministic caching to `data/cache/panel/`,
  retry with exponential backoff, call budget. **NEW (E2):** `model_name` parameter added
  to `GitHubModelsProvider.__init__()` (supports per-model caching + model switching on quota);
  429 cooldown capped at 120s (fails fast on daily quota exhaustion instead of sleeping ~13h).
  **NEW (PR #9 — Azure provider):** `twdf/panel/azure_provider.py`: `AzureFoundryProvider`
  implementing the SAME `ModelProvider` protocol, making it a DROP-IN replacement for
  `GitHubModelsProvider`. Supports two API styles: (1) `"azure_openai"` (Azure OpenAI Service,
  deployment in URL, api-key header, NO model field in body); (2) `"foundry"` (Azure AI Foundry
  models-as-a-service, model in body, Bearer token). Reuses the SAME hashlib-based cache
  mechanism as GitHub provider (cache keys include deployment name to prevent collisions).
  Azure has NO per-model daily cap (Lever C, quota-strategy.md), enabling powered single-session
  axis-1 runs. Environment variables: `AZURE_OPENAI_ENDPOINT` (required, endpoint URL),
  `AZURE_OPENAI_KEY` (required, NEVER logged/committed), `AZURE_OPENAI_API_VERSION` (defaults
  to `"2024-10-21"`), `AZURE_OPENAI_DEPLOYMENT` (optional override). Offline tests pass (22/22);
  cross-process cache determinism verified. See `docs/plans/azure-setup.md` for PI provisioning steps.
  `twdf/panel/real_panel.py`: `run_panel()` implementing INTERFACES §3 exactly, dual-system
  flow (System-1 no-AI anchor → System-2 with AI + UI intervention), counterfactual pairing
  (System-1 frozen across UI arms), reliance definition aligned with Bansal adoption.
  **NEW (E2 — Fix C):** Stronger persona conditioning in System-2 prompt (explicit behavioral
  policies). **NEW (E2 — 3-condition support):** `ui_pair` now accepts tuple of 2 or 3 conditions
  (control, treatment, dark); dual-system flow runs for ALL conditions; System-1 frozen invariant
  tested across all 3. **NEW (E2 — Fix D):** `render_ui_condition()` in bansal_tasks.py handles
  "Wrong-AI (dark)" condition (renders WRONG label: 1 - ai_pred, with pseudo-high conf + oppressive
  framing). **NEW (PR #8 — axis-1 multi-family pilot):** `ui_pair` now accepts tuple of 5 Bansal
  AI conditions (multi-condition support); `render_ui_condition()` handles all 5 Bansal AI conditions
  (`Conf.`, `Conf.+Single`, `Conf.+Double`, `Conf.+Adaptive`, `Conf.+Adaptive (Expert)`) via
  class-based extractors over raw Bansal HTML (`system_highlights` uses unquoted
  `<span class=class0>` token spans; `expert_highlights_html` uses single-quoted
  `<span class='class0'>` phrase spans). `Conf.+Single` shows ALL spans for the predicted label
  (`class{ai_pred}`); `Conf.+Double` shows ALL class0 and class1 spans; both preserve document order
  with direction labels (`class1` = supporting positive, `class0` = supporting negative).
  `Conf.+Adaptive` and `Conf.+Adaptive (Expert)` use fixed domain median-confidence thresholds
  (`beer`=0.892, `amzbook`=0.889): high confidence (`conf >= threshold`) uses Single, low confidence
  uses Double; missing domains raise an error. `TaskStimulus` retains backward-compatible
  `expert_explanation` and adds `expert_highlights_html` for raw class-tagged expert spans.
  Multi-provider run loop in `axis1_pilot.py` iterates model list, runs panel per model, System-1
  frozen across all 5 conditions AND models (tested). **NEW (E4 — 4-condition support + placebo):**
  `ui_pair` now accepts a 4-tuple; `render_ui_condition()` also handles "Conf.+Placebo" (content-free
  explanation: present, matched in format to faithful, but NO task-specific decision-relevant content;
  generic boilerplate, identical across tasks by construction). **NEW (PR #17 — clean axis-2):**
  `displayed_ai_advice()` and `render_ui_condition()` handle `"Wrong-AI-GT (dark)"`, which displays
  `1 - task.ground_truth` with the same coercive framing as `"Wrong-AI (dark)"`; `real_panel.run_panel()`
  accepts any condition sequence and stores/scores `trace['ai_advice']`, `ai_correct`, and `relied`
  from `displayed_ai_advice()` as the single source of truth.
- **experiments** — `e1_vslice`, `e1_multicond`, `e1_robustness`, `e1_decomposition`
  (each `python -m twdf.experiments.<name> --config configs/<name>.yaml`). `e1_panel_v1`
  (real LLM panel, counterfactual pairing, elasticity + permutation + bootstrap; PR#3).
  **NEW (E2):** `e2_panel_redesign` (3-condition panel with Fixes A-D: conflict-conditioned
  DV + data-driven items + strong personas + Wrong-AI axis-2; config `configs/e2_panel_redesign.yaml`).
  **NEW (PR #5):** `luyin_decomposition` (Lu&Yin C0 replication, split-half reliability on
  Lu&Yin dataset; config `configs/luyin_decomposition.yaml`).
  **NEW (PR #6):** `bansal_discriminator` (C0 mechanism test, matched-subset decompositions
  to test whether Bansal's user×task dominance PERSISTS or COLLAPSES under Lu&Yin-matched
  homogeneity; config `configs/bansal_discriminator.yaml`; subset filters: domain, AI-accuracy
  band, tasks-per-user subsampling, joint domain+accuracy; `filter_subset()` + `compute_subset_structure()`
  functions; PI-directed verdict decision rule with thresholds PERSIST ≤ 0.50, COLLAPSE ≥ 0.70).
  **NEW (E4 — PR #7):** `e4_compliance` (4-condition panel: control, faithful, placebo, dark; 
  formalizes H3 compliance floor + axis-2 sensor; config `configs/e4_compliance.yaml`; 
  compliance-adjusted axis-2 = over_reliance_level − placebo_floor; System-1 frozen across all 4 
  conditions; 15 items, 6 personas, gpt-4.1-mini; full response serialization).
  **NEW (PR #17):** `axis2_powered` (powered clean axis-2 one-shot runner; config
  `configs/axis2_powered.yaml`; conditions `Conf.`, `Conf.+Placebo`, `Conf.+Adaptive (Expert)`,
  `Wrong-AI-GT (dark)`; 6 personas × 20 beer items with item seed 2024 ×
  `{openai/gpt-4o, openai/gpt-4.1-mini}`; E4-style placebo-floor adjustment, per-model + pooled panel
  over-reliance, per-persona adoption/spread, sign-flip permutation/bootstrap test for adoption above
  placebo floor, and binomial test vs 0.5; output `results/axis2_powered.json` labeled
  `CONFIRMATORY-PENDING-PREREG`).
  **NEW (PR #8):** `axis1_pilot` (EXPLORATORY multi-family axis-1 pilot, 5 Bansal AI conditions,
  multi-provider run loop iterates models, System-1 frozen across conditions AND models; config
  `configs/axis1_pilot.yaml`; metrics: cross-condition correlation Spearman + permutation + bootstrap,
  cross-family agreement rank correlations, power-analysis readout; EXPLORATORY ONLY — not confirmatory).
  No single `run_experiment` dispatcher; each experiment is its own module.
- **analysis** — `twdf/analysis/panel_human_correspondence.py`: preregistered BLIND H1a secondary
  readout. `panel_human_condition_correspondence(panel_disagreement_by_condition:
  dict[str, float], human_overdispersion_path: str | Path = "results/e1_multicond.json", *,
  seed: int = 42, n_boot: int = 10000, n_perm: int = 10000) -> CorrespondenceResult`.
  Loads fixed `results.human_overdispersion`, excludes `"Human"`, aligns the five Bansal AI
  conditions in canonical order, reuses `metrics.overdispersion.condition_correlation` for
  Spearman + permutation + bootstrap, reports Pearson secondarily, and returns
  `CorrespondenceResult(shared_conditions, aligned_pairs, spearman_rho, spearman_p, bootstrap_ci,
  pearson_r, n_conditions, degenerate, ceiling_flags, ceiling_excluded, note)` with `to_dict()`.
  `Conf.+Adaptive (Expert)` is flagged as a near-ceiling/low-variance human target when the
  committed E1 JSON is used; `ceiling_excluded` recomputes the same readout without flagged
  conditions.
- **features** — `twdf/features/ui_features.py`: §4.3 atomic UI feature space for the 7 rendered
  Bansal/panel conditions (`Conf.`, `Conf.+Single`, `Conf.+Double`, `Conf.+Adaptive`,
  `Conf.+Adaptive (Expert)`, `Conf.+Placebo`, `Wrong-AI (dark)`). Exposes
  `@dataclass(frozen=True) UIFeatureVector` with documented JSON `to_dict()`;
  `extract_ui_features(task: TaskStimulus, ui_condition: str) -> UIFeatureVector`;
  `FEATURE_NAMES: tuple[str, ...]`; `feature_vector_to_array(v: UIFeatureVector) -> np.ndarray`;
  and `feature_distance(a: UIFeatureVector, b: UIFeatureVector, *, weights=None) -> float`.
  `FEATURE_NAMES` order is stable:
  `has_explanation`, `explanation_source_none`, `explanation_source_lime`,
  `explanation_source_expert`, `explanation_source_placebo`, `explanation_faithfulness`,
  `n_highlight_spans`, `info_density`, `shows_predicted_class_only`, `shows_both_classes`,
  `is_adaptive`, `confidence_shown`, `confidence_value`, `authority_cue`, `wrong_ai`,
  `explanation_char_len`. Extraction is deterministic, renderer-faithful, and non-leaky
  (visible prediction/confidence/explanation/framing only; never `ground_truth`). This PR builds
  feature space and OOD distance only; it does NOT learn or freeze τ.
- **analysis (PR #12 — confirmatory Axis-1 BLIND pipeline)** —
  `twdf/analysis/confirmatory_axis1.py`: pure offline H1a analysis accepting panel-response
  records (`persona_id`, `model`, `task_id`, `ui_condition`, `seed`, `system1_decision`,
  `final_decision`, `ai_advice`, `relied`, plus AI-correct/task metadata) and a fixed human target
  path. Returns `ConfirmatoryAxis1Result.to_dict()` with `per_model` results (no pooled primary
  model-mix estimate), conflict-conditioned beta-binomial over-dispersion + bootstrap CI,
  difficulty-controlled within-task estimator + CI + paired permutation p, PR #11
  `panel_human_condition_correspondence`, baseline comparisons, BH-adjusted p-values,
  aligned per-condition table, cross-model agreement summary, `n`, and
  `exploratory_vs_confirmatory="CONFIRMATORY"`. Reuses `conflict_conditioned_reliance`,
  `betabinom_overdispersion`, `baseline_mean_predictor`, `within_task_diff`,
  `paired_permutation_test`, and `bootstrap_ci`; adds the missing random, prompt-only,
  single-model, and rational-Bayesian null baselines.
- **analysis / experiments (PR #15 — E3 LOIO generalization)** —
  `twdf/analysis/loio.py`: pure offline leave-one-item-out core
  `loio_generalization(items: Sequence[LOIOItem], predict_fn, *, seed: int = 42,
  n_perm: int = 10000) -> LOIOResult`. `LOIOItem(item_id, target, features)` carries the
  observed axis-1 target for train folds; each held-out fold is exposed to `predict_fn` only as
  `LOIOHeldoutItem(item_id, features)` with no target. `LOIOResult.to_dict()` reports `n`,
  `hit_rate`, one-sided binomial `hit_p` vs 0.5, `spearman_rho`, one-sided seeded permutation
  `spearman_p`, `degenerate`, and a per-item prediction table. n<3 is degenerate plumbing only.
  `twdf/experiments/e3_loio.py` re-exports these entry points; no τ is learned or frozen here.
- **experiments (PR #12 — confirmatory runner)** — `twdf/experiments/confirmatory_axis1.py`
  plus `configs/confirmatory_axis1.yaml`: thin multi-provider runner over the frozen confirmatory
  model set `{openai/gpt-4o, openai/gpt-4.1-mini}` and five Bansal AI conditions. The runner only
  collects responses with `real_panel.run_panel()` and calls the pure analysis; tests exercise this
  path with mock providers only (no live/networked calls during the BLIND build).
- **calibration** — `twdf/calibration/thresholds.py`: Module D dual-threshold machinery for
  SPEC §6 is implemented. Exposes
  `CalibrationExample(features: UIFeatureVector, axis1_overdispersion: float,
  axis2_over_reliance: float, is_dangerous: bool)`,
  `ThresholdModel(tau_disp, tau_level, calibration_features_ref, ood_radius,
  target_recall, precision_at_target_recall, achieved_recall, feature_mins,
  feature_maxs, seed=42, timestamp=None)`,
  `fit_thresholds(calibration: list[CalibrationExample], *, target_recall: float = 0.9,
  seed: int = 42) -> ThresholdModel`,
  `triage(features: UIFeatureVector, axis1_signal: float, axis2_signal: float,
  model: ThresholdModel, *, reversal_flag: bool = False, ece: float | None = None,
  ece_threshold: float | None = None) -> TriageDecision`, and
  `freeze_thresholds(model: ThresholdModel, *, timestamp: str) -> ThresholdModel`.
  `fit_thresholds` scans dual-axis cutoffs for high recall and reports precision-at-recall;
  `triage` returns `RELEASE`, `HUMAN_STUDY`, or `ABSTAIN` with abstention for feature-space OOD,
  novel/uncalibrated dimensions, ECE, or reversal flags. **τ_disp/τ_level remain UNFROZEN on
  fresh fits (`timestamp is None`); no frozen τ artifact is committed in this PR.**
- **analysis (PR #16 — E5 reliability/abstention layer)** —
  `twdf/analysis/reliability.py`: pure offline reliability metrics for SPEC §5/E5 and §6.3–6.4.
  Exposes
  `expected_calibration_error(pred_probs, outcomes, *, n_bins=10) -> ECEResult`
  with weighted equal-width-bin ECE, MCE, and per-bin reliability rows
  (`bin_index`, `lower`, `upper`, `count`, `mean_confidence`, `empirical_accuracy`,
  `calibration_error`);
  `generalization_gradient(records, *, by: str, n_bins: int = 5) -> GradientResult`
  over `feature_distance`, `difficulty`, `persona`, or another supplied covariate, returning
  ordered gradient bins with `mean_absolute_error`, ECE/MCE, counts, and a worst-bin
  `failure_region`;
  `reliable_radius(records, *, ece_bound, distance_key="feature_distance") -> float`, the largest
  observed in-radius feature distance whose prefix ECE is within the bound; and
  `measured_abstention_rate(designs, threshold_model, *, signals) -> AbstentionReport`, which
  calls Module D `triage` for each design and reports counts/fractions for `ABSTAIN`,
  `HUMAN_STUDY`, and `RELEASE`. Result dataclasses (`ECEResult`, `GradientResult`,
  `AbstentionReport`) provide deterministic JSON `to_dict()` shapes. Feature-distance analyses
  reuse `twdf.features.ui_features.feature_distance`; abstention reuses
  `twdf.calibration.thresholds.triage`/`ThresholdModel`; this layer does **not** freeze τ.
- **analysis (PR #18 — EXPLORATORY stratified correspondence)** —
  `twdf/analysis/stratified_correspondence.py`: `stratified_correspondence(panel_responses, *,
  human_raw_loader, stratify_by="ai_conf", n_strata=3, seed=42, n_boot=10000, n_perm=10000)` returns
  `StratifiedCorrespondenceResult.to_dict()` with AI-side difficulty strata, a condition × stratum
  cell table, included cell ids, Spearman/permutation/bootstrap readout, n<3 degeneracy, and per-cell
  ceiling/low-variance/too-few-users flags. Strata are **exploratory only** and may use only AI-side
  exogenous properties (`ai_conf`/`confidence`/`conf`/difficulty), never `ground_truth`, human choices,
  or human reliance. `load_real_bansal_human_raw()` reads the committed beer/five-AI-condition raw CSV
  for offline human over-dispersion, while tests can inject synthetic loaders.
  `confirmatory_robustness(confirmatory_result_dict)` is a pure readout over
  `ConfirmatoryAxis1Result.to_dict()` reporting per-model CI stability, over-dispersion CI summaries,
  leave-one-condition-out Spearman sensitivity, and a task-selection sensitivity note; it does not
  re-run, retune, or alter the frozen D5.11 prereg.
- **Determinism:** Use `hashlib` for any string→seed (builtin `hash()` is BANNED —
  non-deterministic across processes). Cross-process determinism tests use subprocesses.
  **E2 verified:** Cross-process cache determinism confirmed (0 API calls on rerun, byte-identical
  responses excluding manifest timestamp).
  **PR #6 verified:** Cross-process determinism for bansal_discriminator (bit-identical
  stable_user_share across separate runs, excluding timestamp; tested via subprocess rerun).
- **AzureFoundryProvider (PR #9, MERGED):** `twdf/panel/azure_provider.py` — drop-in
  `ModelProvider` for Azure OpenAI (`azure_openai` style: deployment in URL, `api-key` header,
  no `model` in body) + Azure AI Foundry (`foundry` style: `{endpoint}/chat/completions`,
  `Authorization: Bearer`, `model` in body). Env creds `AZURE_OPENAI_ENDPOINT/KEY/API_VERSION/
  DEPLOYMENT`; replicated hashlib cache (deployment in key). Uncapped confirmatory path.
- **UNMERGED (branch-only) additions to be reconciled on merge:** E4's placebo renderer
  (`Conf.+Placebo`) + 4-condition experiment live on `feature/e4-compliance` (PR #7, NOT merged).
  The 5 Bansal-condition renderers and the multi-provider run loop with **skip-on-cap** resilience
  were merged via PR #8 and corrected on PR #10 from token-count heuristics to the class-based
  semantics described above.
