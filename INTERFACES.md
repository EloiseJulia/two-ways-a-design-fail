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

## 8. AS-BUILT (reconciliation — actual state after PR #1 + PR #2 + Module B impl)
> This section reflects what is ACTUALLY implemented on `main`, to prevent drift.
- **data** — `twdf/data/bansal.py`: auto-downloads + loads Bansal to the canonical
  schema; multi-condition selector with `task_selection` config
  (`all` | `first_10_shared` | `min_per_domain`; default `all`). Lu&Yin NOT loaded yet.
  **NEW (Module B):** `twdf/data/bansal_tasks.py`: Beer task stimulus loader with
  AI predictions + expert explanations; testid→questionId join verified (50/50 overlap).
- **metrics** — `twdf/metrics/overdispersion.py`: `betabinom_overdispersion`,
  `betabinom_overdispersion_within_domain` (renamed from a misleading "stratified
  pooling"; domain is BETWEEN-SUBJECTS), `baseline_mean_predictor`, `within_task_diff`,
  `bootstrap_ci`, and the cross-condition correlation (Spearman + permutation +
  bootstrap, with an n<3 `degenerate` guard). **NEW (Module B):** `paired_permutation_test()`
  for within-task elasticity significance testing (hashlib-seeded, paired permutation scheme).
  `twdf/metrics/variance_decomposition.py`: `split_half_reliability` (PRIMARY,
  ICC(2,1) + Spearman-Brown → `stable_user_share` + CI) and
  `variance_components_glmm` (`BinomialBayesMixedGLM`, bounded maxiter=10; currently
  NON-CONVERGENT, reported honestly as corroboration-unavailable).
- **panel** — `twdf/panel/stub.py`: SYNTHETIC deterministic stub only (v0/PR#1/PR#2).
  **NEW (Module B, IMPLEMENTED):** `twdf/panel/provider.py`: `GitHubModelsProvider`
  implementing `ModelProvider` protocol, reads `GH_MODELS_TOKEN` from env, hashlib-based
  deterministic caching to `data/cache/panel/`, retry with exponential backoff, call budget.
  `twdf/panel/real_panel.py`: `run_panel()` implementing INTERFACES §3 exactly, dual-system
  flow (System-1 no-AI anchor → System-2 with AI + UI intervention), counterfactual pairing
  (System-1 frozen across UI arms), reliance definition aligned with Bansal adoption.
  **Status:** Code complete, offline tests pass (6/6), cross-process determinism verified.
  **BLOCKER:** Real API run hits GitHub Models rate limits (HTTP 429) despite retry logic.
- **experiments** — `e1_vslice`, `e1_multicond`, `e1_robustness`, `e1_decomposition`
  (each `python -m twdf.experiments.<name> --config configs/<name>.yaml`). **NEW (Module B):**
  `e1_panel_v1` (real LLM panel, counterfactual pairing, elasticity + permutation + bootstrap).
  No single `run_experiment` dispatcher; each experiment is its own module.
- **calibration / features** — NOT YET IMPLEMENTED (`fit_thresholds`, `triage`,
  `extract_features`/`UIFeatureVector` are still designs above).
- Determinism: use `hashlib` for any string→seed (builtin `hash()` is banned —
  non-deterministic across processes). Cross-process determinism tests use subprocesses.
