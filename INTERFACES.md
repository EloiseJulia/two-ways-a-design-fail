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

## 8. AS-BUILT (reconciliation — actual state after PR #1 + PR #2 + PR #3 + E2 Panel Redesign + PR #5 Lu&Yin)
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
  `twdf/panel/real_panel.py`: `run_panel()` implementing INTERFACES §3 exactly, dual-system
  flow (System-1 no-AI anchor → System-2 with AI + UI intervention), counterfactual pairing
  (System-1 frozen across UI arms), reliance definition aligned with Bansal adoption.
  **NEW (E2 — Fix C):** Stronger persona conditioning in System-2 prompt (explicit behavioral
  policies). **NEW (E2 — 3-condition support):** `ui_pair` now accepts tuple of 2 or 3 conditions
  (control, treatment, dark); dual-system flow runs for ALL conditions; System-1 frozen invariant
  tested across all 3. **NEW (E2 — Fix D):** `render_ui_condition()` in bansal_tasks.py handles
  "Wrong-AI (dark)" condition (renders WRONG label: 1 - ai_pred, with pseudo-high conf + oppressive
  framing).
- **experiments** — `e1_vslice`, `e1_multicond`, `e1_robustness`, `e1_decomposition`
  (each `python -m twdf.experiments.<name> --config configs/<name>.yaml`). `e1_panel_v1`
  (real LLM panel, counterfactual pairing, elasticity + permutation + bootstrap; PR#3).
  **NEW (E2):** `e2_panel_redesign` (3-condition panel with Fixes A-D: conflict-conditioned
  DV + data-driven items + strong personas + Wrong-AI axis-2; config `configs/e2_panel_redesign.yaml`).
  No single `run_experiment` dispatcher; each experiment is its own module.
- **calibration / features** — NOT YET IMPLEMENTED (`fit_thresholds`, `triage`,
  `extract_features`/`UIFeatureVector` are still designs above).
- **Determinism:** Use `hashlib` for any string→seed (builtin `hash()` is BANNED —
  non-deterministic across processes). Cross-process determinism tests use subprocesses.
  **E2 verified:** Cross-process cache determinism confirmed (0 API calls on rerun, byte-identical
  responses excluding manifest timestamp).
