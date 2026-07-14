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
docs/{plans,research}/
```
