# impl-moduleB-panel — Module B: real LLM panel thin vertical slice

You are an implementation subagent. You implement code in a git worktree and push
to a draft PR. You do **NOT** audit or merge your own work. Return findings; the
Manager gates the merge on an independent audit.

## 0. FIRST: read the single source of truth
Read (in this order) before writing anything:
- `SPEC.md` (frozen design; esp. §0 two-axis, §4 method, H1a refinement),
- `INTERFACES.md` (contracts — you MUST implement to §3 Panel engine signatures
  and the §8 AS-BUILT reconciliation),
- `PROGRESS.md` (state + Known pitfalls + Preregistration log),
- `src/twdf/panel/stub.py` (the stub you are replacing — keep its `Persona` /
  `AgentResponse` dataclasses' field names EXACTLY; other modules import them),
- `src/twdf/metrics/overdispersion.py` (reuse `within_task_diff`, `bootstrap_ci`;
  do not duplicate),
- `src/twdf/data/bansal.py` (loader; `task_id` == `questionId` as str).

You are on branch `feature/moduleB-panel` in worktree
`.worktrees/moduleB-panel`. Work ONLY here. Do not touch other modules'
interfaces. Commit + push to the branch when done.

## 1. GOAL (scope — thin vertical slice, SMALL)
Replace the synthetic panel stub with a REAL LLM panel via GitHub Models, proving
the loop **data → real panel → metric → result** end-to-end, at small scale, with
determinism and a cost report. This slice targets the **counterfactual-pairing
loop + a clean within-pair reliance elasticity (E2)** — NOT the cross-condition
axis-1 correlation.

### CRITICAL design guardrail — do NOT reintroduce the degenerate-correlation trap
A Pearson/Spearman correlation over n=2 conditions is ±1 by necessity and is
meaningless (this bug was already fought in PR #1). This slice uses exactly ONE UI
pair, so **you MUST NOT compute or report any cross-condition disagreement↔
over-dispersion correlation.** The deliverable is the paired within-task elasticity
(over persona×task pairs), which is well-powered. The cross-condition correlation is
explicitly deferred to a later scaled run (≥5 conditions).

## 2. GitHub Models provider (verified working — do not re-derive the API)
- Endpoint: `POST https://models.github.ai/inference/chat/completions`
- Auth header: `Authorization: Bearer <token>` where token = **`os.environ["GH_MODELS_TOKEN"]`**.
  The token is injected into your process env at launch. **NEVER hard-code, log,
  print, echo, or commit the token value.** If the env var is missing, raise a
  clear error — do NOT invent a fallback.
- Body: OpenAI-compatible. `{"model": "openai/gpt-4o-mini", "messages": [...],
  "temperature": <t>, "max_tokens": <n>, "seed": <seed>}`. (Manager smoke-tested:
  returns `choices[0].message.content`, model resolves to `gpt-4o-mini-2024-07-18`.)
- Rate limits exist. Add: retry with exponential backoff on 429/5xx, a small
  inter-call sleep, and a hard cap on total calls (fail loudly if exceeded).

Implement in `src/twdf/panel/provider.py`:
```python
class ModelProvider(Protocol):  # per INTERFACES §3
    name: str
    def generate(self, prompt: str, *, seed: int, max_tokens: int,
                 temperature: float) -> str: ...

class GitHubModelsProvider:  # concrete
    name = "openai/gpt-4o-mini"
    # reads GH_MODELS_TOKEN from env; retries; obeys a call budget
```
Prefer using `messages` (system + user) internally; the `generate(prompt: str,...)`
signature must remain per INTERFACES (you may add a `generate_messages` helper).

### Determinism via CACHING (API `seed` is NOT reliably deterministic)
- Wrap the provider in a persistent response cache keyed by a **hashlib** hash of
  (model, normalized messages, temperature, max_tokens, seed). Builtin `hash()` is
  BANNED (non-deterministic across processes — this bit the project twice; grep
  `\bhash\(`). Use `hashlib.sha256`.
- Cache dir: `data/cache/panel/` (gitignore it — add to `.gitignore`). Cache
  entries are JSON. On cache hit, return stored content with zero API calls.
- This makes reruns free + byte-identical. Determinism tests rely on the cache.

## 3. Panel engine — `src/twdf/panel/real_panel.py`
Implement `run_panel(...)` per INTERFACES §3 exactly:
```python
def run_panel(personas: list[Persona], tasks: list[str],
              ui_pair: tuple[str, str], providers: list[ModelProvider],
              *, seeds: list[int], mode: str = "static",
              friction: "FrictionBudget | None" = None) -> list[AgentResponse]: ...
```
Reuse the EXISTING `Persona` and `AgentResponse` dataclasses (import from
`twdf.panel.stub` or move them to a shared module WITHOUT changing field names /
adding required fields; `trust_state` stays optional). For this slice `mode="static"`
only; `sequential`/`friction` may raise `NotImplementedError`.

### Dual-system flow + counterfactual pairing (the scientific core — get this RIGHT)
For each (persona, task, seed):
1. **System-1 (no-AI anchor):** prompt the agent with ONLY the task content `X`
   (no AI advice), persona in the system prompt → parse an initial decision. Compute
   this **ONCE** and FREEZE it.
2. **Inject UI intervention + System-2 reflection:** feed back the frozen System-1
   decision + the AI advice rendered per the UI condition → parse the final decision.
3. Run step 2 **twice** — once for the control UI, once for the treatment UI —
   **reusing the identical System-1 output and identical persona/seed**. Only the
   UI-condition rendering differs (bit-identical otherwise). This is the
   counterfactual pair; difficulty cancels within the pair.
4. `relied` = (final_decision == ai_advice) AND (final differs from system1 OR
   system1 already equalled ai_advice — define reliance precisely and document it;
   align with how Bansal defines adoption: final decision matches AI advice).
   Record `system1_decision`, `final_decision`, `relied`, `confidence`, full `trace`.

**INVARIANT (must hold + be tested): for a fixed (persona, task, seed), the
`system1_decision` is identical across the two UI arms.** If it isn't, the
counterfactual pairing is broken.

### UI conditions for this slice (ONE pair)
- `ui_pair = ("Conf.", "Conf.+Adaptive (Expert)")` — exact Bansal strings.
- **Control "Conf.":** show AI `pred` (label) + `conf` (confidence), plain text `X`,
  NO explanation.
- **Treatment "Conf.+Adaptive (Expert)":** show AI `pred` + `conf` + the
  **explanation** = the `expert` field (expert-highlighted rationale) from the task
  JSON. Render the highlight spans as readable emphasis (e.g. **bold** the
  highlighted phrases); document your rendering. This is a cognitive-semantic
  intervention (in scope), not a visual mechanism.
Document the condition→content mapping in a module docstring; the auditor will check
you did not mislabel conditions (a known pitfall).

## 4. Task stimuli loader — `src/twdf/data/bansal_tasks.py`
- Source: `https://raw.githubusercontent.com/uw-hai/Complementary-Performance/main/task-examples/task-sentiment-beer.json`
  (also amzbook, lsat — but this slice uses **beer** only). Download-if-missing to
  `data/raw/` (mirror `bansal.py` pattern; keep gitignored).
- Fields per item: `testid` (str), `X` (raw text), `Y` (0/1 truth), `pred` (AI
  label), `conf` (AI confidence), `expert` (highlighted explanation HTML), `system`.
- **VERIFY + REPORT the join:** `testid` must map to Bansal `questionId` (== canonical
  `task_id`). Load the Bansal CSV via existing loader, and report the overlap count
  between beer `testid`s and the beer-domain `questionId`s. If the join is weak/empty,
  STOP and report — do not fabricate a mapping.
- Provide `load_beer_tasks() -> dict[str, TaskStimulus]` keyed by task_id.

### Task selection (DIVERSE — the decomposition finding demands it)
Sample ~20 beer tasks **deterministically** (sorted by task_id, fixed seed) that
SPAN diversity: include both AI-correct and AI-incorrect items and a range of `conf`.
Document the selection. Few-task / low-diversity sampling attenuates the signal.

## 5. Metrics for this slice (reuse Module C; add only what's missing)
- Per-condition **panel disagreement** (variance of per-persona reliance rates) —
  compute for BOTH arms. You may reuse/relocate `compute_panel_disagreement`.
- **Within-pair reliance elasticity (E2 / C2):** per task, mean reliance in
  treatment − control across personas → use existing `within_task_diff`. Add a
  **paired permutation test** (shuffle control/treatment labels within each
  persona×task pair, ≥10k shuffles, hashlib/seeded) for significance, plus a
  `bootstrap_ci` over (persona) for the effect. Put any new stat fn in
  `twdf/metrics/overdispersion.py` following existing style + docstrings.
- Report reliance rates per persona, per arm; and per-persona System-1 accuracy vs
  ground truth (sanity: agents actually attempt the task).

## 6. Experiment + config
- `configs/e1_panel_v1.yaml`: personas (5, varied domain_skill/ai_literacy/
  risk_sensitivity/caution/temperature/prior_mix), n_tasks=20, ui_pair, model,
  seeds, max_tokens, call_budget, cache_dir.
- `src/twdf/experiments/e1_panel_v1.py`: CLI `python -m twdf.experiments.e1_panel_v1
  --config configs/e1_panel_v1.yaml`. Writes `results/e1_panel_v1.json` with a
  `run_manifest` (config hash, seeds, model, versions, timestamp, total_api_calls,
  cache_hits, wall_time, est_cost). Numbers in the JSON are the ONLY source of truth.

## 7. Tests (`tests/test_panel_real.py`)
- Provider contract test using a **mock/fake** provider (no network in unit tests):
  `run_panel` returns well-formed `AgentResponse`s.
- **Counterfactual invariant test:** System-1 identical across the two UI arms for
  fixed (persona, task, seed).
- **Cache determinism test — CROSS-PROCESS:** run a tiny panel twice in SEPARATE
  processes (subprocess), assert byte-identical results (reuse the subprocess pattern
  from `tests/test_variance_decomposition.py`). A single-process double-call does
  NOT catch hash-seed nondeterminism.
- Elasticity/permutation test on synthetic paired data with a known effect.
- Keep the ONE real-API end-to-end run OUT of the default pytest path (mark it
  `@pytest.mark.live` / skip if no token) so `pytest` stays offline + fast.

## 8. Methodology guardrails (§4.5 — the auditor WILL check these)
- Token never printed/committed; `data/cache/` and `data/raw/` gitignored.
- `hashlib` only for any string→seed; grep `\bhash\(` before you push.
- No n=2 cross-condition correlation anywhere (see §1).
- Counterfactual System-1-frozen invariant holds and is tested cross-process.
- Reliance definition documented + consistent with Bansal adoption.
- Condition→content mapping documented + faithful (no mislabeled conditions).
- No leakage of any kind; no post-hoc threshold tuning (this slice freezes NO
  thresholds — τ stays unfrozen).
- Every result number reproducible from a clean rerun (cache makes this cheap).

## 9. Deliverables + wrap-up
1. Code: `panel/provider.py`, `panel/real_panel.py`, `data/bansal_tasks.py`,
   `experiments/e1_panel_v1.py`, `configs/e1_panel_v1.yaml`, `tests/test_panel_real.py`,
   `.gitignore` updated.
2. Run the real end-to-end ONCE; commit `results/e1_panel_v1.json`.
3. `pytest -q` green (offline tests); report counts.
4. Update `PROGRESS.md` (Done entry with real numbers + cost) and `INTERFACES.md`
   §8 AS-BUILT (panel now real; provider + run_panel implemented).
5. Commit (trailer `Co-authored-by: Copilot <copilot@github.com>`) + push to
   `feature/moduleB-panel`. Do NOT open/merge a PR (draft PR #3 already exists).
6. Return a concise report: what you built, the REAL numbers (per-persona reliance,
   panel disagreement per arm, elasticity + p + CI, System-1 accuracy), total API
   calls / cache hits / wall time / est cost, the testid↔questionId join result, and
   any blockers or methodology caveats you hit. Do NOT claim "done/all green" —
   report facts; the Manager + an independent auditor verify.

## Known pitfalls (from PROGRESS §Known pitfalls — re-read them)
Builtin `hash()` banned; cross-process determinism only; beta-binomial separates
noise; mean-predictor genuine; within-task diff not pooled corr; two axes separate;
freeze τ before results; exact Bansal condition strings (`Human`, `Conf.`,
`Conf.+Single`, `Conf.+Double`, `Conf.+Adaptive`, `Conf.+Adaptive (Expert)`);
domains `beer`/`amzbook`/`lsat`; CSV explicit dtypes.
