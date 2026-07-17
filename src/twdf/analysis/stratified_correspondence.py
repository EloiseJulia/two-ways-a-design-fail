
"""Exploratory difficulty-stratified panel-to-human correspondence.

This module adds a higher-power exploratory readout: condition x AI-side
difficulty strata cells, never human-outcome strata.  It does not alter the
frozen confirmatory five-condition preregistered analysis.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable
import hashlib
import math
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import ConstantInputWarning

from twdf.analysis.panel_human_correspondence import (
    CANONICAL_AI_CONDITION_ORDER,
    CeilingFlag,
)
from twdf.metrics.overdispersion import (
    OverdispersionResult,
    baseline_mean_predictor,
    betabinom_overdispersion,
    condition_correlation,
)


AI_SIDE_STRATIFIERS = frozenset({
    "ai_conf",
    "confidence",
    "conf",
    "task_difficulty",
    "difficulty",
})
FORBIDDEN_STRATIFIERS = frozenset({
    "ground_truth",
    "y",
    "human_final",
    "human_initial",
    "choice",
    "relied",
    "reliance",
    "user_id",
    "assignmentId",
    "assignment_id",
})
DEFAULT_AI_CONDITIONS = CANONICAL_AI_CONDITION_ORDER
MIN_USERS_PER_CELL = 3
MIN_ITEMS_PER_CELL = 1
LOW_VARIANCE_THRESHOLD = 1e-8
CEILING_EXCESS_VAR_THRESHOLD = 1e-4


@dataclass(frozen=True)
class DifficultyStratum:
    stratum: int
    label: str
    lower: float
    upper: float
    n_items: int
    task_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StratifiedCell:
    condition: str
    stratum: int
    stratum_label: str
    cell_id: str
    n_items: int
    n_human_users: int
    n_human_trials: int
    n_panel_members: int
    n_panel_conflict_trials: int
    human_rho: float | None
    human_mean_p: float | None
    human_excess_variance: float | None
    human_empirical_variance: float | None
    panel_disagreement: float | None
    included: bool
    flags: list[str]
    ceiling_flag: CeilingFlag

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["ceiling_flag"] = self.ceiling_flag.__dict__.copy()
        return result


@dataclass(frozen=True)
class StratifiedCorrespondenceResult:
    exploratory_vs_confirmatory: str
    stratify_by: str
    n_strata: int
    strata: list[DifficultyStratum]
    cell_table: list[StratifiedCell]
    included_cell_ids: list[str]
    spearman_rho: float | None
    spearman_p: float | None
    bootstrap_ci: tuple[float, float] | None
    pearson_r: float | None
    n_points: int
    degenerate: bool
    note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "exploratory_vs_confirmatory": self.exploratory_vs_confirmatory,
            "stratify_by": self.stratify_by,
            "n_strata": self.n_strata,
            "strata": [s.to_dict() for s in self.strata],
            "cell_table": [c.to_dict() for c in self.cell_table],
            "included_cell_ids": list(self.included_cell_ids),
            "spearman_rho": self.spearman_rho,
            "spearman_p": self.spearman_p,
            "bootstrap_ci": list(self.bootstrap_ci) if self.bootstrap_ci is not None else None,
            "pearson_r": self.pearson_r,
            "n_points": self.n_points,
            "degenerate": self.degenerate,
            "note": self.note,
        }


@dataclass(frozen=True)
class RobustnessResult:
    exploratory_vs_confirmatory: str
    per_model_stability: dict[str, dict[str, Any]]
    leave_one_condition_out: dict[str, list[dict[str, Any]]]
    task_selection_note: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _stable_seed(*parts: Any) -> int:
    payload = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % (2**31)


def _get(record: Any, field: str, default: Any = None) -> Any:
    if isinstance(record, dict):
        if field in record:
            return record[field]
        trace = record.get("trace") or {}
        extra = record.get("extra") or {}
        if field in trace:
            return trace[field]
        return extra.get(field, default)
    if hasattr(record, field):
        return getattr(record, field)
    trace = getattr(record, "trace", None) or {}
    if isinstance(trace, dict) and field in trace:
        return trace[field]
    extra = getattr(record, "extra", None) or {}
    if isinstance(extra, dict):
        return extra.get(field, default)
    return default


def _canonical_condition_order(conditions: Iterable[str]) -> list[str]:
    observed = set(str(c) for c in conditions)
    canonical = [c for c in DEFAULT_AI_CONDITIONS if c in observed]
    return canonical + sorted(observed - set(canonical))


def _validate_stratifier(stratify_by: str) -> None:
    if stratify_by in FORBIDDEN_STRATIFIERS or stratify_by not in AI_SIDE_STRATIFIERS:
        raise ValueError(
            f"stratify_by={stratify_by!r} is not allowed. Use an AI-side exogenous "
            "property such as ai_conf/confidence/conf/task_difficulty; never human outcomes."
        )


def _normalise_panel_row(record: Any) -> dict[str, Any]:
    ai_advice = _get(record, "ai_advice")
    if ai_advice is None:
        raise ValueError("panel response missing ai_advice/trace.ai_advice")
    system1 = _get(record, "system1_decision")
    final = _get(record, "final_decision")
    return {
        "persona_id": str(_get(record, "persona_id", "persona")),
        "model": str(_get(record, "model", "model")),
        "task_id": str(_get(record, "task_id")),
        "ui_condition": str(_get(record, "ui_condition")),
        "seed": int(_get(record, "seed", 0) or 0),
        "system1_decision": str(system1),
        "final_decision": str(final),
        "ai_advice": str(ai_advice),
        "ai_conf": _first_present(record, ("ai_conf", "confidence", "conf")),
        "confidence": _first_present(record, ("confidence", "ai_conf", "conf")),
        "conf": _first_present(record, ("conf", "ai_conf", "confidence")),
        "task_difficulty": _first_present(record, ("task_difficulty", "difficulty")),
        "difficulty": _first_present(record, ("difficulty", "task_difficulty")),
    }


def _first_present(record: Any, fields: tuple[str, ...]) -> Any:
    for field in fields:
        value = _get(record, field)
        if value is not None and not (isinstance(value, float) and math.isnan(value)):
            return value
    return None


def _normalise_human_df(raw: Any) -> pd.DataFrame:
    df = raw.copy() if isinstance(raw, pd.DataFrame) else pd.DataFrame(raw)
    if df.empty:
        return pd.DataFrame(columns=["user_id", "task_id", "ui_condition", "ai_advice", "human_final", "relied"])

    rename = {
        "assignmentId": "user_id",
        "assignment_id": "user_id",
        "questionId": "task_id",
        "condition": "ui_condition",
        "pred": "ai_advice",
        "choice": "human_final",
        "conf": "ai_conf",
        "confidence": "confidence",
    }
    for src, dst in rename.items():
        if src in df.columns and dst not in df.columns:
            df[dst] = df[src]
    required = {"user_id", "task_id", "ui_condition", "ai_advice", "human_final"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"human raw data missing columns: {sorted(missing)}")
    df = df.copy()
    df["user_id"] = df["user_id"].astype(str)
    df["task_id"] = df["task_id"].astype(str)
    df["ui_condition"] = df["ui_condition"].astype(str)
    df["ai_advice"] = df["ai_advice"].astype(str)
    df["human_final"] = df["human_final"].astype(str)
    if "relied" not in df.columns:
        df["relied"] = df["human_final"] == df["ai_advice"]
    df["relied"] = df["relied"].astype(bool)
    return df


def load_real_bansal_human_raw(path: str | Path = "data/raw/decision-result-filter.csv") -> pd.DataFrame:
    """Load committed Bansal raw decisions, filtered to beer and the five AI conditions."""
    csv_path = Path(path)
    if not csv_path.exists():
        alt = Path("data/raw/bansal_chi21_decisions.csv")
        if alt.exists():
            csv_path = alt
        else:
            raise FileNotFoundError(f"Bansal raw CSV not found: {csv_path}")
    df = pd.read_csv(csv_path, dtype={"choice": str, "y": str, "pred": str, "pred2": str})
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])
    df = df[(df["task"] == "beer") & (df["condition"].isin(DEFAULT_AI_CONDITIONS))].copy()
    return _normalise_human_df(df)


def _item_values_from_panel(panel_rows: list[dict[str, Any]], stratify_by: str) -> dict[str, float]:
    values: dict[str, list[float]] = {}
    for row in panel_rows:
        value = row.get(stratify_by)
        if value is None and stratify_by == "ai_conf":
            value = row.get("confidence") or row.get("conf")
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if not np.isfinite(numeric):
            continue
        values.setdefault(row["task_id"], []).append(numeric)
    return {task: float(np.mean(vals)) for task, vals in sorted(values.items()) if vals}


def _item_values_from_human_ai_side(human_df: pd.DataFrame, stratify_by: str) -> dict[str, float]:
    column = stratify_by
    if column not in human_df.columns and stratify_by == "ai_conf":
        if "confidence" in human_df.columns:
            column = "confidence"
        elif "conf" in human_df.columns:
            column = "conf"
    if column not in human_df.columns:
        return {}
    values: dict[str, float] = {}
    for task_id, group in human_df.groupby("task_id", sort=True):
        numeric = pd.to_numeric(group[column], errors="coerce").dropna()
        if len(numeric):
            values[str(task_id)] = float(numeric.mean())
    return values


def _assign_strata(item_values: dict[str, float], n_strata: int) -> list[DifficultyStratum]:
    if n_strata < 1:
        raise ValueError("n_strata must be >= 1")
    if not item_values:
        raise ValueError("No item-level AI-side values available for stratification")
    ordered = sorted(item_values.items(), key=lambda item: (item[1], item[0]))
    chunks = np.array_split(np.array([task for task, _ in ordered], dtype=object), n_strata)
    strata: list[DifficultyStratum] = []
    for idx, chunk in enumerate(chunks):
        task_ids = [str(task) for task in chunk.tolist()]
        vals = [item_values[task] for task in task_ids]
        label = "hard_low_ai_conf" if idx == 0 else ("easy_high_ai_conf" if idx == n_strata - 1 else f"middle_{idx}")
        strata.append(DifficultyStratum(
            stratum=idx,
            label=label,
            lower=float(min(vals)) if vals else float("nan"),
            upper=float(max(vals)) if vals else float("nan"),
            n_items=len(task_ids),
            task_ids=task_ids,
        ))
    return strata


def _human_counts(df: pd.DataFrame) -> dict[str, tuple[int, int]]:
    if "human_initial" in df.columns:
        mask = df["human_initial"].isna() | (df["human_initial"].astype(str) != df["ai_advice"].astype(str))
        df = df[mask]
    counts: dict[str, tuple[int, int]] = {}
    for user_id, group in df.groupby("user_id", sort=True):
        n_trials = int(len(group))
        if n_trials > 0:
            counts[str(user_id)] = (int(group["relied"].sum()), n_trials)
    return counts


def _panel_member_rates(rows: list[dict[str, Any]]) -> tuple[dict[str, float], int]:
    counts: dict[str, list[int]] = {}
    n_conflict = 0
    for row in rows:
        if row["system1_decision"] == row["ai_advice"]:
            continue
        key = f"{row['persona_id']}|{row['model']}"
        counts.setdefault(key, [0, 0])
        counts[key][0] += int(row["final_decision"] == row["ai_advice"])
        counts[key][1] += 1
        n_conflict += 1
    rates = {key: k / n for key, (k, n) in sorted(counts.items()) if n > 0}
    return rates, n_conflict


def _safe_overdispersion(counts: dict[str, tuple[int, int]]) -> OverdispersionResult:
    if len(counts) >= 2:
        return betabinom_overdispersion(counts)
    if len(counts) == 1:
        only = next(iter(counts.values()))
        return baseline_mean_predictor({"observed": only, "pseudo": only})
    return baseline_mean_predictor({"pseudo_a": (0, 1), "pseudo_b": (0, 1)})


def _ceiling_flag(overdispersion: OverdispersionResult | None, panel_disagreement: float | None) -> CeilingFlag:
    reasons: list[str] = []
    if overdispersion is not None and overdispersion.excess_variance < CEILING_EXCESS_VAR_THRESHOLD:
        reasons.append(f"human_excess_var<{CEILING_EXCESS_VAR_THRESHOLD:g}")
    if panel_disagreement is not None and panel_disagreement < LOW_VARIANCE_THRESHOLD:
        reasons.append(f"panel_disagreement<{LOW_VARIANCE_THRESHOLD:g}")
    return CeilingFlag(
        flagged=bool(reasons),
        reason="; ".join(reasons) if reasons else None,
        excess_var=float(overdispersion.excess_variance) if overdispersion is not None else None,
        mean_p=float(overdispersion.mean_p) if overdispersion is not None else None,
        empirical_var=float(overdispersion.empirical_variance) if overdispersion is not None else None,
    )


def _build_cell(condition: str, stratum: DifficultyStratum, human_df: pd.DataFrame, panel_rows: list[dict[str, Any]]) -> StratifiedCell:
    task_set = set(stratum.task_ids)
    human_cell = human_df[(human_df["ui_condition"] == condition) & (human_df["task_id"].isin(task_set))]
    panel_cell = [r for r in panel_rows if r["ui_condition"] == condition and r["task_id"] in task_set]
    flags: list[str] = []

    counts = _human_counts(human_cell)
    rates, n_panel_conflict = _panel_member_rates(panel_cell)
    overdispersion: OverdispersionResult | None = None
    disagreement: float | None = None

    if stratum.n_items < MIN_ITEMS_PER_CELL:
        flags.append("too_few_items")
    if len(counts) < MIN_USERS_PER_CELL:
        flags.append("too_few_human_users")
    if len(rates) < 2:
        flags.append("too_few_panel_members")
    if n_panel_conflict < 1:
        flags.append("no_panel_conflicts")

    if len(counts) >= MIN_USERS_PER_CELL:
        overdispersion = _safe_overdispersion(counts)
    if len(rates) >= 2:
        values = np.array(list(rates.values()), dtype=float)
        disagreement = float(np.var(values, ddof=1))
        if disagreement < LOW_VARIANCE_THRESHOLD:
            flags.append("low_panel_variance")

    included = overdispersion is not None and disagreement is not None and "too_few_items" not in flags
    ceiling = _ceiling_flag(overdispersion, disagreement)
    if ceiling.flagged:
        flags.append("ceiling_or_low_variance")

    return StratifiedCell(
        condition=condition,
        stratum=stratum.stratum,
        stratum_label=stratum.label,
        cell_id=f"{condition}::stratum_{stratum.stratum}",
        n_items=stratum.n_items,
        n_human_users=len(counts),
        n_human_trials=int(sum(n for _, n in counts.values())),
        n_panel_members=len(rates),
        n_panel_conflict_trials=n_panel_conflict,
        human_rho=float(overdispersion.rho) if overdispersion is not None else None,
        human_mean_p=float(overdispersion.mean_p) if overdispersion is not None else None,
        human_excess_variance=float(overdispersion.excess_variance) if overdispersion is not None else None,
        human_empirical_variance=float(overdispersion.empirical_variance) if overdispersion is not None else None,
        panel_disagreement=disagreement,
        included=included,
        flags=sorted(set(flags)),
        ceiling_flag=ceiling,
    )


def stratified_correspondence(
    panel_responses: Iterable[Any],
    *,
    human_raw_loader: Callable[[], Any],
    stratify_by: str = "ai_conf",
    n_strata: int = 3,
    seed: int = 42,
    n_boot: int = 10000,
    n_perm: int = 10000,
) -> StratifiedCorrespondenceResult:
    """Exploratory condition x difficulty-stratum human/panel correspondence.

    Strata are built only from AI-side exogenous item properties. Human outcomes,
    ground truth, and reliance are never read to place items into strata.
    """
    _validate_stratifier(stratify_by)
    panel_rows = [_normalise_panel_row(record) for record in panel_responses]
    if not panel_rows:
        raise ValueError("panel_responses cannot be empty")
    human_df = _normalise_human_df(human_raw_loader())

    item_values = _item_values_from_panel(panel_rows, stratify_by)
    if not item_values:
        item_values = _item_values_from_human_ai_side(human_df, stratify_by)
    strata = _assign_strata(item_values, n_strata)

    conditions = _canonical_condition_order({r["ui_condition"] for r in panel_rows} & set(human_df["ui_condition"].unique()))
    if not conditions:
        raise ValueError("No shared AI conditions between panel responses and human raw data")

    cells = [_build_cell(condition, stratum, human_df, panel_rows) for condition in conditions for stratum in strata]
    included = [cell for cell in cells if cell.included]
    disagreement = {cell.cell_id: float(cell.panel_disagreement) for cell in included if cell.panel_disagreement is not None}
    human_rho = {cell.cell_id: float(cell.human_rho) for cell in included if cell.human_rho is not None}
    n_points = len(set(disagreement) & set(human_rho))
    degenerate = n_points < 3

    spearman_rho: float | None = None
    spearman_p: float | None = None
    bootstrap_interval: tuple[float, float] | None = None
    pearson_r: float | None = None
    if not degenerate:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConstantInputWarning)
            corr = condition_correlation(
                disagreement,
                human_rho,
                permutation_n=n_perm,
                bootstrap_n=n_boot,
                bootstrap_seed=_stable_seed(seed, "stratified-bootstrap"),
                permutation_seed=_stable_seed(seed, "stratified-permutation"),
            )
        spearman_rho = corr.spearman_rho
        spearman_p = corr.permutation_pvalue
        bootstrap_interval = (corr.bootstrap_ci_lower, corr.bootstrap_ci_upper)
        xs = np.array([disagreement[k] for k in sorted(disagreement)], dtype=float)
        ys = np.array([human_rho[k] for k in sorted(disagreement)], dtype=float)
        pearson = stats.pearsonr(xs, ys).statistic
        pearson_r = float(pearson) if not np.isnan(pearson) else 0.0
        note = corr.note or "EXPLORATORY condition x difficulty-stratum readout; does not change frozen D5.11 prereg."
    else:
        note = "DEGENERATE: fewer than 3 interpretable condition x stratum points; exploratory readout not inferential."

    return StratifiedCorrespondenceResult(
        exploratory_vs_confirmatory="EXPLORATORY; does not change frozen confirmatory D5.11 five-condition prereg",
        stratify_by=stratify_by,
        n_strata=n_strata,
        strata=strata,
        cell_table=cells,
        included_cell_ids=[cell.cell_id for cell in included],
        spearman_rho=spearman_rho,
        spearman_p=spearman_p,
        bootstrap_ci=bootstrap_interval,
        pearson_r=pearson_r,
        n_points=n_points,
        degenerate=degenerate,
        note=note,
    )


def _ci_summary(entry: dict[str, Any]) -> dict[str, Any]:
    estimate = entry.get("estimate")
    lo = entry.get("ci_lower")
    hi = entry.get("ci_upper")
    width = None
    excludes_zero = None
    if lo is not None and hi is not None:
        width = float(hi) - float(lo)
        excludes_zero = bool(float(lo) > 0 or float(hi) < 0)
    return {
        "estimate": float(estimate) if estimate is not None else None,
        "ci_lower": float(lo) if lo is not None else None,
        "ci_upper": float(hi) if hi is not None else None,
        "ci_width": width,
        "ci_excludes_zero": excludes_zero,
    }


def _loo_spearman(pairs: list[dict[str, Any]], omit: str | None = None) -> dict[str, Any]:
    kept = [p for p in pairs if omit is None or p.get("condition") != omit]
    if len(kept) < 3:
        return {"spearman_rho": None, "n_conditions": len(kept), "degenerate": True}
    xs = np.array([float(p["panel_disagreement"]) for p in kept], dtype=float)
    ys = np.array([float(p["human_rho"]) for p in kept], dtype=float)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConstantInputWarning)
        rho = stats.spearmanr(xs, ys).correlation
    return {
        "spearman_rho": float(rho) if not np.isnan(rho) else 0.0,
        "n_conditions": len(kept),
        "degenerate": False,
    }


def confirmatory_robustness(confirmatory_result: dict[str, Any]) -> RobustnessResult:
    """Pure JSON robustness readout for ConfirmatoryAxis1Result.to_dict()."""
    per_model = confirmatory_result.get("per_model", {})
    stability: dict[str, dict[str, Any]] = {}
    loo: dict[str, list[dict[str, Any]]] = {}

    for model, result in sorted(per_model.items()):
        within = _ci_summary(result.get("within_task_estimator", {}))
        overdisp = _ci_summary(result.get("conflict_conditioned_overdispersion", {}))
        corr = result.get("cross_condition_correspondence", {})
        pairs = list(corr.get("aligned_pairs", []))
        full = corr.get("spearman_rho")
        if full is None:
            full_calc = _loo_spearman(pairs)
            full = full_calc["spearman_rho"]
        stability[model] = {
            "within_task_estimator": within,
            "conflict_conditioned_overdispersion": overdisp,
            "cross_condition_spearman": full,
            "cross_condition_ci": corr.get("bootstrap_ci"),
            "n_conditions": corr.get("n_conditions", len(pairs)),
            "interpretation": "Per-model readout; no pooling hides model-family instability.",
        }
        model_loo: list[dict[str, Any]] = []
        for pair in pairs:
            omitted = str(pair.get("condition"))
            recomputed = _loo_spearman(pairs, omit=omitted)
            rho = recomputed["spearman_rho"]
            delta = None if full is None or rho is None else float(rho) - float(full)
            model_loo.append({
                "omitted_condition": omitted,
                **recomputed,
                "delta_from_full": delta,
            })
        loo[model] = model_loo

    return RobustnessResult(
        exploratory_vs_confirmatory="ROBUSTNESS READOUT over frozen confirmatory result; does not change D5.11 prereg",
        per_model_stability=stability,
        leave_one_condition_out=loo,
        task_selection_note=(
            "Task-selection sensitivity must be interpreted against the frozen confirmatory item set. "
            "This function does not re-run or retune tasks; it summarizes stability of the supplied JSON only."
        ),
        note="Exploratory robustness diagnostics for reviewer A4; pure function over ConfirmatoryAxis1Result.to_dict().",
    )
