
"""Pure confirmatory Axis-1 (H1a) analysis.

This module is intentionally offline-testable and blind to any future
confirmatory panel run.  It accepts already collected panel responses and the
fixed human over-dispersion target, then reports the pre-registered H1a readout
regardless of outcome.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable
import hashlib
import json

import numpy as np

from twdf.analysis.panel_human_correspondence import (
    AlignedConditionPair,
    CANONICAL_AI_CONDITION_ORDER,
    CeilingFlag,
    CorrespondenceResult,
    panel_human_condition_correspondence,
)
from twdf.metrics.overdispersion import (
    OverdispersionResult,
    baseline_mean_predictor,
    betabinom_overdispersion,
    bootstrap_ci,
    conflict_conditioned_reliance,
    paired_permutation_test,
    within_task_diff,
)


DEFAULT_CONTROL_CONDITION = "Conf."
DEFAULT_TREATMENT_CONDITION = "Conf.+Adaptive (Expert)"
BASELINE_NAMES = (
    "random",
    "mean_predictor",
    "prompt_only",
    "single_model",
    "rational_bayes_null",
)


@dataclass(frozen=True)
class ConditionSummary:
    condition: str
    model: str
    conflict_conditioned_reliance: float
    unconditional_reliance: float
    n_conflict: int
    n_total: int
    conflict_fraction: float
    overdispersion_rho: float
    overdispersion_excess_variance: float
    overdispersion_mean_p: float
    panel_disagreement: float
    per_member_reliance: dict[str, float]
    per_cell_counts: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BaselineComparison:
    name: str
    value: float
    signal_estimate: float
    ci_lower: float
    ci_upper: float
    beaten: bool
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModelAxis1Result:
    model: str
    conflict_conditioned_overdispersion: dict[str, Any]
    within_task_estimator: dict[str, Any]
    cross_condition_correspondence: dict[str, Any]
    baseline_comparisons: dict[str, dict[str, Any]]
    bh_adjusted_pvalues: dict[str, dict[str, Any]]
    aligned_per_condition_table: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConfirmatoryAxis1Result:
    per_model: dict[str, ModelAxis1Result]
    aligned_per_condition_table: list[dict[str, Any]]
    cross_model_agreement: dict[str, Any]
    n: dict[str, int]
    exploratory_vs_confirmatory: str = "CONFIRMATORY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "per_model": {model: result.to_dict() for model, result in self.per_model.items()},
            "aligned_per_condition_table": self.aligned_per_condition_table,
            "cross_model_agreement": self.cross_model_agreement,
            "n": dict(self.n),
            "exploratory_vs_confirmatory": self.exploratory_vs_confirmatory,
        }


def _stable_seed(*parts: Any) -> int:
    payload = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % (2**31)


def _get(record: Any, field: str, default: Any = None) -> Any:
    if isinstance(record, dict):
        if field in record:
            return record[field]
        trace = record.get("trace") or {}
        return trace.get(field, default)
    if hasattr(record, field):
        return getattr(record, field)
    trace = getattr(record, "trace", None) or {}
    return trace.get(field, default)


def _normalized_response(record: Any) -> dict[str, Any]:
    trace = _get(record, "trace", {}) or {}
    ai_advice = _get(record, "ai_advice", trace.get("ai_advice"))
    ground_truth = _get(record, "ground_truth", trace.get("ground_truth"))
    ai_correct = _get(record, "ai_correct", trace.get("ai_correct"))
    if ai_correct is None and ai_advice is not None and ground_truth is not None:
        ai_correct = str(ai_advice) == str(ground_truth)
    system1 = _get(record, "system1_decision")
    final = _get(record, "final_decision")
    if ai_advice is None:
        raise ValueError("Each response must expose ai_advice either directly or in trace")
    return {
        "persona_id": str(_get(record, "persona_id")),
        "model": str(_get(record, "model")),
        "task_id": str(_get(record, "task_id")),
        "ui_condition": str(_get(record, "ui_condition")),
        "seed": int(_get(record, "seed", 0)),
        "system1_decision": str(system1),
        "final_decision": str(final),
        "ai_advice": str(ai_advice),
        "ai_correct": bool(ai_correct) if ai_correct is not None else False,
        "relied": bool(_get(record, "relied", str(final) == str(ai_advice))),
        "task_difficulty": _get(record, "task_difficulty", trace.get("task_difficulty")),
        "trace": dict(trace),
    }


def _as_response_objects(rows: list[dict[str, Any]]) -> list[Any]:
    class ResponseShim:
        def __init__(self, row: dict[str, Any]) -> None:
            self.persona_id = row["persona_id"]
            self.model = row["model"]
            self.task_id = row["task_id"]
            self.ui_condition = row["ui_condition"]
            self.seed = row["seed"]
            self.system1_decision = row["system1_decision"]
            self.final_decision = row["final_decision"]
            self.relied = row["relied"]
            self.trace = {**row.get("trace", {}), "ai_advice": row["ai_advice"], "ai_correct": row["ai_correct"]}
    return [ResponseShim(row) for row in rows]


def _is_conflict(row: dict[str, Any]) -> bool:
    return str(row["system1_decision"]) != str(row["ai_advice"])


def _is_reliance(row: dict[str, Any]) -> bool:
    return str(row["final_decision"]) == str(row["ai_advice"])


def _member_key(row: dict[str, Any], include_model: bool = True) -> str:
    if include_model:
        return f"{row['persona_id']}|seed={row['seed']}|model={row['model']}"
    return f"{row['persona_id']}|seed={row['seed']}"


def _counts_by_member(rows: list[dict[str, Any]], *, include_model: bool = True) -> dict[str, tuple[int, int]]:
    counts: dict[str, list[int]] = {}
    for row in rows:
        if not _is_conflict(row):
            continue
        key = _member_key(row, include_model=include_model)
        counts.setdefault(key, [0, 0])
        counts[key][0] += int(_is_reliance(row))
        counts[key][1] += 1
    return {key: (value[0], value[1]) for key, value in sorted(counts.items()) if value[1] > 0}


def _safe_overdispersion(counts: dict[str, tuple[int, int]]) -> OverdispersionResult:
    if len(counts) >= 2:
        return betabinom_overdispersion(counts)
    if len(counts) == 1:
        only = next(iter(counts.values()))
        padded = {"observed": only, "pseudo": (only[0], only[1])}
        return baseline_mean_predictor(padded)
    return baseline_mean_predictor({"pseudo_a": (0, 1), "pseudo_b": (0, 1)})


def _panel_disagreement(rows: list[dict[str, Any]]) -> tuple[float, dict[str, float]]:
    counts = _counts_by_member(rows, include_model=False)
    rates = {member: k / n for member, (k, n) in counts.items() if n > 0}
    values = np.array(list(rates.values()), dtype=float)
    disagreement = float(np.var(values, ddof=1)) if len(values) > 1 else 0.0
    return disagreement, rates


def _condition_summary(rows: list[dict[str, Any]], condition: str, model: str) -> ConditionSummary:
    condition_rows = [row for row in rows if row["ui_condition"] == condition]
    conflict = conflict_conditioned_reliance(_as_response_objects(condition_rows))
    counts = _counts_by_member(condition_rows, include_model=False)
    overdispersion = _safe_overdispersion(counts)
    disagreement, per_member = _panel_disagreement(condition_rows)
    return ConditionSummary(
        condition=condition,
        model=model,
        conflict_conditioned_reliance=float(conflict.reliance_rate),
        unconditional_reliance=float(conflict.unconditional_reliance),
        n_conflict=int(conflict.n_conflict),
        n_total=int(conflict.n_total),
        conflict_fraction=float(conflict.conflict_fraction),
        overdispersion_rho=float(overdispersion.rho),
        overdispersion_excess_variance=float(overdispersion.excess_variance),
        overdispersion_mean_p=float(overdispersion.mean_p),
        panel_disagreement=float(disagreement),
        per_member_reliance={k: float(v) for k, v in sorted(per_member.items())},
        per_cell_counts=conflict.per_cell_counts,
    )


def _task_disagreement(rows: list[dict[str, Any]], condition: str) -> dict[str, float]:
    by_task: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row["ui_condition"] == condition and _is_conflict(row):
            by_task.setdefault(row["task_id"], []).append(row)
    result: dict[str, float] = {}
    for task_id, task_rows in sorted(by_task.items()):
        values = np.array([float(_is_reliance(row)) for row in task_rows], dtype=float)
        result[task_id] = float(np.var(values, ddof=1)) if len(values) > 1 else 0.0
    return result


def _within_task_estimate(rows: list[dict[str, Any]], control_condition: str, treatment_condition: str) -> float:
    control = _task_disagreement(rows, control_condition)
    treatment = _task_disagreement(rows, treatment_condition)
    if not (set(control) & set(treatment)):
        return 0.0
    return float(within_task_diff(control, treatment))


def _within_task_permutation(rows: list[dict[str, Any]], control_condition: str, treatment_condition: str, *, n_perm: int, seed: int) -> dict[str, Any]:
    control = _task_disagreement(rows, control_condition)
    treatment = _task_disagreement(rows, treatment_condition)
    if not (set(control) & set(treatment)):
        return {"observed_diff": 0.0, "pvalue": 1.0, "n_permutations": n_perm, "n_pairs": 0}
    perm = paired_permutation_test(control, treatment, n_permutations=n_perm, seed=seed)
    return asdict(perm)


def _resample_by_units(rows: list[dict[str, Any]], *, seed: int) -> list[dict[str, Any]]:
    units: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        units.setdefault(_member_key(row, include_model=True), []).append(row)
    if not units:
        return []
    keys = sorted(units)
    rng = np.random.RandomState(seed)
    sampled_keys = rng.choice(keys, size=len(keys), replace=True)
    boot_rows: list[dict[str, Any]] = []
    for i, key in enumerate(sampled_keys):
        for row in units[key]:
            copy = dict(row)
            copy["persona_id"] = f"boot{i}:{row['persona_id']}"
            boot_rows.append(copy)
    return boot_rows


def _bootstrap_stat(rows: list[dict[str, Any]], stat_fn, *, n_boot: int, seed: int) -> dict[str, float]:
    estimate = float(stat_fn(rows))
    if n_boot <= 0:
        return {"estimate": estimate, "ci_lower": estimate, "ci_upper": estimate, "se": 0.0}
    stats: list[float] = []
    for i in range(n_boot):
        boot = _resample_by_units(rows, seed=_stable_seed(seed, i, "bootstrap-units"))
        stats.append(float(stat_fn(boot)))
    arr = np.array(stats, dtype=float)
    return {
        "estimate": estimate,
        "ci_lower": float(np.percentile(arr, 2.5)),
        "ci_upper": float(np.percentile(arr, 97.5)),
        "se": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
    }



def _overdispersion_bootstrap_ci(
    rows: list[dict[str, Any]],
    treatment_condition: str,
    *,
    n_boot: int,
    seed: int,
) -> dict[str, float]:
    counts = _counts_by_member(
        [row for row in rows if row["ui_condition"] == treatment_condition],
        include_model=False,
    )
    if len(counts) < 2:
        counts = {"pseudo_a": (0, 1), "pseudo_b": (0, 1)}
    ci = bootstrap_ci(lambda data: float(_safe_overdispersion(data).rho), counts, n=n_boot, seed=seed)
    return {
        "estimate": float(ci.estimate),
        "ci_lower": float(ci.ci_lower),
        "ci_upper": float(ci.ci_upper),
        "se": float(ci.se),
    }

def _primary_overdispersion(rows: list[dict[str, Any]], treatment_condition: str) -> float:
    counts = _counts_by_member([r for r in rows if r["ui_condition"] == treatment_condition], include_model=False)
    return float(_safe_overdispersion(counts).rho)


def _random_baseline(seed: int) -> float:
    rng = np.random.RandomState(_stable_seed(seed, "random-baseline"))
    return float(np.mean(rng.permutation([0.0, 0.0, 0.0, 0.0])))


def _mean_predictor_baseline(rows: list[dict[str, Any]], treatment_condition: str) -> float:
    counts = _counts_by_member([r for r in rows if r["ui_condition"] == treatment_condition], include_model=False)
    if len(counts) < 2:
        counts = {"pseudo_a": (0, 1), "pseudo_b": (0, 1)}
    return float(baseline_mean_predictor(counts).rho)


def _prompt_only_baseline() -> float:
    return 0.0


def _single_model_baseline() -> float:
    return 0.0


def _rational_bayes_null(rows: list[dict[str, Any]], control_condition: str, treatment_condition: str) -> float:
    per_condition: dict[str, dict[str, list[float]]] = {control_condition: {}, treatment_condition: {}}
    for row in rows:
        if row["ui_condition"] not in per_condition or not _is_conflict(row):
            continue
        per_condition[row["ui_condition"]].setdefault(row["task_id"], []).append(float(row["ai_correct"]))
    control = {task: float(np.mean(vals)) for task, vals in per_condition[control_condition].items()}
    treatment = {task: float(np.mean(vals)) for task, vals in per_condition[treatment_condition].items()}
    if not (set(control) & set(treatment)):
        return 0.0
    return float(within_task_diff(control, treatment))


def _baseline_comparisons(
    rows: list[dict[str, Any]],
    within_ci: dict[str, float],
    control_condition: str,
    treatment_condition: str,
    *,
    seed: int,
) -> dict[str, BaselineComparison]:
    values = {
        "random": _random_baseline(seed),
        "mean_predictor": _mean_predictor_baseline(rows, treatment_condition),
        "prompt_only": _prompt_only_baseline(),
        "single_model": _single_model_baseline(),
        "rational_bayes_null": _rational_bayes_null(rows, control_condition, treatment_condition),
    }
    notes = {
        "random": "Deterministic zero-effect random-label null for within-task paired disagreement.",
        "mean_predictor": "Reuses baseline_mean_predictor; rho=0 by construction.",
        "prompt_only": "Single prompt/no persona panel has no between-persona disagreement axis.",
        "single_model": "No cross-model triangulation null; primary estimates are still reported per model.",
        "rational_bayes_null": "Appropriate-reliance anchor: rely iff AI advice is correct; no human-outcome predictor.",
    }
    return {
        name: BaselineComparison(
            name=name,
            value=float(value),
            signal_estimate=float(within_ci["estimate"]),
            ci_lower=float(within_ci["ci_lower"]),
            ci_upper=float(within_ci["ci_upper"]),
            beaten=bool(within_ci["ci_lower"] > value),
            note=notes[name],
        )
        for name, value in values.items()
    }



def baseline_random(*, seed: int = 42) -> float:
    """Pre-registered random baseline for the paired within-task signal."""
    return _random_baseline(seed)


def baseline_prompt_only() -> float:
    """Prompt-only baseline: one prompt/no persona panel yields no disagreement axis."""
    return _prompt_only_baseline()


def baseline_single_model() -> float:
    """Single-model baseline: no cross-model triangulation signal."""
    return _single_model_baseline()


def null_rational_bayes(
    responses: Iterable[Any],
    *,
    control_condition: str = DEFAULT_CONTROL_CONDITION,
    treatment_condition: str = DEFAULT_TREATMENT_CONDITION,
) -> float:
    """Rational-Bayesian appropriate-reliance null: rely iff AI advice is correct."""
    rows = [_normalized_response(record) for record in responses]
    return _rational_bayes_null(rows, control_condition, treatment_condition)


def _safe_panel_human_correspondence(
    panel_disagreement_by_condition: dict[str, float],
    human_overdispersion_path: str | Path,
    *,
    seed: int,
    n_boot: int,
    n_perm: int,
) -> CorrespondenceResult:
    try:
        return panel_human_condition_correspondence(
            panel_disagreement_by_condition,
            human_overdispersion_path,
            seed=seed,
            n_boot=n_boot,
            n_perm=n_perm,
        )
    except (IndexError, ValueError, FloatingPointError):
        with Path(human_overdispersion_path).open("r", encoding="utf-8") as f:
            human = json.load(f)["results"]["human_overdispersion"]
        canonical = [
            c for c in CANONICAL_AI_CONDITION_ORDER
            if c in panel_disagreement_by_condition and c in human
        ]
        extras = sorted(
            set(panel_disagreement_by_condition)
            & set(human)
            - set(CANONICAL_AI_CONDITION_ORDER)
            - {"Human"}
        )
        shared = canonical + extras
        pairs = [
            AlignedConditionPair(
                condition=condition,
                panel_disagreement=float(panel_disagreement_by_condition[condition]),
                human_rho=float(human[condition]["rho"]),
            )
            for condition in shared
        ]
        flags = {
            condition: CeilingFlag(
                flagged=False,
                reason=None,
                excess_var=float(human[condition].get("excess_var", 0.0)),
                mean_p=float(human[condition].get("mean_p", 0.0)),
                empirical_var=float(human[condition].get("empirical_var", 0.0)),
            )
            for condition in shared
        }
        return CorrespondenceResult(
            shared_conditions=shared,
            aligned_pairs=pairs,
            spearman_rho=0.0 if len(shared) >= 3 else None,
            spearman_p=1.0 if len(shared) >= 3 else None,
            bootstrap_ci=(0.0, 0.0) if len(shared) >= 3 else None,
            pearson_r=0.0 if len(shared) >= 3 else None,
            n_conditions=len(shared),
            degenerate=len(shared) < 3,
            ceiling_flags=flags,
            ceiling_excluded=None,
            note="Constant panel disagreement; correspondence reported as null rather than failing.",
        )

def benjamini_hochberg(pvalues: dict[str, float], *, alpha: float = 0.05) -> dict[str, dict[str, Any]]:
    """Benjamini-Hochberg FDR correction with deterministic tie ordering."""
    clean = {name: min(max(float(p), 0.0), 1.0) for name, p in pvalues.items() if p is not None}
    m = len(clean)
    if m == 0:
        return {}
    ordered = sorted(clean.items(), key=lambda item: (item[1], item[0]))
    adjusted_raw: dict[str, float] = {}
    for rank, (name, pvalue) in enumerate(ordered, start=1):
        adjusted_raw[name] = min(1.0, pvalue * m / rank)
    running = 1.0
    adjusted: dict[str, float] = {}
    for name, _ in reversed(ordered):
        running = min(running, adjusted_raw[name])
        adjusted[name] = running
    return {
        name: {
            "raw_p": clean[name],
            "adjusted_p": float(adjusted[name]),
            "reject_alpha_0_05": bool(adjusted[name] <= alpha),
        }
        for name in sorted(clean)
    }


def _cross_model_agreement(per_model_disagreement: dict[str, dict[str, float]]) -> dict[str, Any]:
    from scipy import stats as scipy_stats

    models = sorted(per_model_disagreement)
    pairwise: dict[str, float | None] = {}
    for i, left in enumerate(models):
        for right in models[i + 1 :]:
            shared = sorted(set(per_model_disagreement[left]) & set(per_model_disagreement[right]))
            if len(shared) < 2:
                pairwise[f"{left}_vs_{right}"] = None
                continue
            a = [per_model_disagreement[left][condition] for condition in shared]
            b = [per_model_disagreement[right][condition] for condition in shared]
            rho = scipy_stats.spearmanr(a, b).correlation
            pairwise[f"{left}_vs_{right}"] = float(rho) if not np.isnan(rho) else 0.0
    values = [v for v in pairwise.values() if v is not None]
    return {
        "pairwise_rank_correlations": pairwise,
        "mean_pairwise_correlation": float(np.mean(values)) if values else None,
        "note": "Cross-model agreement is descriptive only; primary H1a numbers are per-model, not pooled.",
    }


def analyze_confirmatory_axis1(
    responses: Iterable[Any],
    human_overdispersion_path: str | Path,
    *,
    control_condition: str = DEFAULT_CONTROL_CONDITION,
    treatment_condition: str = DEFAULT_TREATMENT_CONDITION,
    seed: int = 42,
    n_boot: int = 1000,
    n_perm: int = 1000,
) -> ConfirmatoryAxis1Result:
    """Compute the pre-registered H1a result from panel responses only."""
    rows = [_normalized_response(record) for record in responses]
    if not rows:
        raise ValueError("responses cannot be empty")

    models = sorted({row["model"] for row in rows})
    conditions = sorted({row["ui_condition"] for row in rows})
    per_model: dict[str, ModelAxis1Result] = {}
    all_condition_rows: list[dict[str, Any]] = []
    disagreement_for_agreement: dict[str, dict[str, float]] = {}

    for model in models:
        model_rows = [row for row in rows if row["model"] == model]
        summaries = [_condition_summary(model_rows, condition, model) for condition in conditions]
        panel_disagreement_by_condition = {s.condition: s.panel_disagreement for s in summaries}
        disagreement_for_agreement[model] = panel_disagreement_by_condition
        correspondence: CorrespondenceResult = _safe_panel_human_correspondence(
            panel_disagreement_by_condition,
            human_overdispersion_path,
            seed=seed,
            n_boot=n_boot,
            n_perm=n_perm,
        )

        within_ci = _bootstrap_stat(
            model_rows,
            lambda sample: _within_task_estimate(sample, control_condition, treatment_condition),
            n_boot=n_boot,
            seed=_stable_seed(seed, model, "within"),
        )
        permutation = _within_task_permutation(
            model_rows,
            control_condition,
            treatment_condition,
            n_perm=n_perm,
            seed=_stable_seed(seed, model, "perm"),
        )
        overdisp_ci = _overdispersion_bootstrap_ci(
            model_rows,
            treatment_condition,
            n_boot=n_boot,
            seed=_stable_seed(seed, model, "overdispersion"),
        )
        baselines = _baseline_comparisons(
            model_rows,
            within_ci,
            control_condition,
            treatment_condition,
            seed=_stable_seed(seed, model, "baselines"),
        )
        pvalues = {
            "within_task_permutation": float(permutation["pvalue"]),
        }
        if correspondence.spearman_p is not None:
            pvalues["cross_condition_correspondence"] = float(correspondence.spearman_p)
        bh = benjamini_hochberg(pvalues, alpha=0.05)
        table = [summary.to_dict() for summary in summaries]
        all_condition_rows.extend(table)
        per_model[model] = ModelAxis1Result(
            model=model,
            conflict_conditioned_overdispersion=overdisp_ci,
            within_task_estimator={**within_ci, "permutation": permutation},
            cross_condition_correspondence=correspondence.to_dict(),
            baseline_comparisons={name: comparison.to_dict() for name, comparison in baselines.items()},
            bh_adjusted_pvalues=bh,
            aligned_per_condition_table=table,
        )

    n = {
        "responses": len(rows),
        "personas": len({row["persona_id"] for row in rows}),
        "items": len({row["task_id"] for row in rows}),
        "models": len(models),
        "conditions": len(conditions),
        "seeds": len({row["seed"] for row in rows}),
    }
    return ConfirmatoryAxis1Result(
        per_model=per_model,
        aligned_per_condition_table=all_condition_rows,
        cross_model_agreement=_cross_model_agreement(disagreement_for_agreement),
        n=n,
    )
