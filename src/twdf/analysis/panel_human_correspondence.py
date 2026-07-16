"""Panel-to-human cross-condition correspondence for preregistered H1a readout.

This module is intentionally blind to confirmatory panel results: it accepts only
panel disagreement by condition and the fixed human over-dispersion target.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any
import warnings

import numpy as np
from scipy import stats
from scipy.stats import ConstantInputWarning

from twdf.metrics.overdispersion import condition_correlation


HUMAN_BASELINE_CONDITION = "Human"
CANONICAL_AI_CONDITION_ORDER: tuple[str, ...] = (
    "Conf.",
    "Conf.+Single",
    "Conf.+Double",
    "Conf.+Adaptive",
    "Conf.+Adaptive (Expert)",
)
DEFAULT_EXCESS_VAR_CEILING_THRESHOLD = 1e-4
DEFAULT_MEAN_EXTREME_DELTA = 0.30
DEFAULT_TINY_EMPIRICAL_VAR = 0.005


@dataclass(frozen=True)
class AlignedConditionPair:
    """One aligned condition point for panel-human correspondence."""

    condition: str
    panel_disagreement: float
    human_rho: float


@dataclass(frozen=True)
class CeilingFlag:
    """Human-target diagnostic for near-ceiling/low-variance conditions."""

    flagged: bool
    reason: str | None
    excess_var: float | None
    mean_p: float | None
    empirical_var: float | None


@dataclass(frozen=True)
class CorrespondenceResult:
    """Cross-condition panel-disagreement vs human-overdispersion readout."""

    shared_conditions: list[str]
    aligned_pairs: list[AlignedConditionPair]
    spearman_rho: float | None
    spearman_p: float | None
    bootstrap_ci: tuple[float, float] | None
    pearson_r: float | None
    n_conditions: int
    degenerate: bool
    ceiling_flags: dict[str, CeilingFlag]
    ceiling_excluded: "CorrespondenceResult | None" = None
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        result = asdict(self)
        if self.bootstrap_ci is not None:
            result["bootstrap_ci"] = list(self.bootstrap_ci)
        if self.ceiling_excluded is not None:
            result["ceiling_excluded"] = self.ceiling_excluded.to_dict()
        return result


def _load_human_overdispersion(path: str | Path) -> dict[str, dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    try:
        human = data["results"]["human_overdispersion"]
    except KeyError as exc:
        raise ValueError(
            "human_overdispersion_path must contain results.human_overdispersion"
        ) from exc
    if not isinstance(human, dict):
        raise ValueError("results.human_overdispersion must be a condition mapping")
    return human


def _canonical_shared_conditions(
    panel_disagreement_by_condition: dict[str, float],
    human_overdispersion: dict[str, dict[str, Any]],
) -> list[str]:
    shared = (
        set(panel_disagreement_by_condition)
        & set(human_overdispersion)
        - {HUMAN_BASELINE_CONDITION}
    )
    canonical = [c for c in CANONICAL_AI_CONDITION_ORDER if c in shared]
    extras = sorted(shared - set(CANONICAL_AI_CONDITION_ORDER))
    return canonical + extras


def _ceiling_flag(entry: dict[str, Any]) -> CeilingFlag:
    excess_var = entry.get("excess_var")
    mean_p = entry.get("mean_p")
    empirical_var = entry.get("empirical_var")

    reasons: list[str] = []
    if excess_var is not None and float(excess_var) < DEFAULT_EXCESS_VAR_CEILING_THRESHOLD:
        reasons.append(f"excess_var<{DEFAULT_EXCESS_VAR_CEILING_THRESHOLD:g}")
    if (
        mean_p is not None
        and empirical_var is not None
        and abs(float(mean_p) - 0.5) >= DEFAULT_MEAN_EXTREME_DELTA
        and float(empirical_var) < DEFAULT_TINY_EMPIRICAL_VAR
    ):
        reasons.append(
            "mean_p near boundary with tiny empirical_var "
            f"(|mean_p-0.5|>={DEFAULT_MEAN_EXTREME_DELTA:g}, "
            f"empirical_var<{DEFAULT_TINY_EMPIRICAL_VAR:g})"
        )

    return CeilingFlag(
        flagged=bool(reasons),
        reason="; ".join(reasons) if reasons else None,
        excess_var=float(excess_var) if excess_var is not None else None,
        mean_p=float(mean_p) if mean_p is not None else None,
        empirical_var=float(empirical_var) if empirical_var is not None else None,
    )


def _build_result(
    panel_disagreement_by_condition: dict[str, float],
    human_overdispersion: dict[str, dict[str, Any]],
    *,
    seed: int,
    n_boot: int,
    n_perm: int,
    include_sensitivity: bool,
) -> CorrespondenceResult:
    conditions = _canonical_shared_conditions(panel_disagreement_by_condition, human_overdispersion)
    if not conditions:
        raise ValueError("No shared non-Human conditions between panel input and human target")

    pairs = [
        AlignedConditionPair(
            condition=condition,
            panel_disagreement=float(panel_disagreement_by_condition[condition]),
            human_rho=float(human_overdispersion[condition]["rho"]),
        )
        for condition in conditions
    ]
    ceiling_flags = {condition: _ceiling_flag(human_overdispersion[condition]) for condition in conditions}
    n_conditions = len(conditions)
    degenerate = n_conditions < 3

    spearman_rho: float | None = None
    spearman_p: float | None = None
    bootstrap_interval: tuple[float, float] | None = None
    pearson_r: float | None = None
    note: str | None = None

    disagreement_for_corr = {p.condition: p.panel_disagreement for p in pairs}
    overdispersion_for_corr = {p.condition: p.human_rho for p in pairs}

    if not degenerate:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConstantInputWarning)
            corr = condition_correlation(
                disagreement_by_condition=disagreement_for_corr,
                overdispersion_by_condition=overdispersion_for_corr,
                permutation_n=n_perm,
                bootstrap_n=n_boot,
                bootstrap_seed=seed,
                permutation_seed=seed,
            )
        spearman_rho = corr.spearman_rho
        spearman_p = corr.permutation_pvalue
        bootstrap_interval = (corr.bootstrap_ci_lower, corr.bootstrap_ci_upper)
        panel_values = np.array([p.panel_disagreement for p in pairs], dtype=float)
        human_values = np.array([p.human_rho for p in pairs], dtype=float)
        pearson = stats.pearsonr(panel_values, human_values)
        pearson_r = float(pearson.statistic)
        note = corr.note
    else:
        note = (
            f"DEGENERATE CORRELATION WARNING: n={n_conditions} shared non-Human "
            "conditions. Spearman rho with n<3 has no statistical meaning; "
            "no correlation, p-value, CI, or Pearson r is reported."
        )

    sensitivity: CorrespondenceResult | None = None
    if include_sensitivity:
        non_ceiling_panel = {
            condition: panel_disagreement_by_condition[condition]
            for condition in conditions
            if not ceiling_flags[condition].flagged
        }
        if set(non_ceiling_panel) != set(conditions):
            sensitivity = _build_result(
                non_ceiling_panel,
                human_overdispersion,
                seed=seed,
                n_boot=n_boot,
                n_perm=n_perm,
                include_sensitivity=False,
            )

    return CorrespondenceResult(
        shared_conditions=conditions,
        aligned_pairs=pairs,
        spearman_rho=spearman_rho,
        spearman_p=spearman_p,
        bootstrap_ci=bootstrap_interval,
        pearson_r=pearson_r,
        n_conditions=n_conditions,
        degenerate=degenerate,
        ceiling_flags=ceiling_flags,
        ceiling_excluded=sensitivity,
        note=note,
    )


def panel_human_condition_correspondence(
    panel_disagreement_by_condition: dict[str, float],
    human_overdispersion_path: str | Path = "results/e1_multicond.json",
    *,
    seed: int = 42,
    n_boot: int = 10000,
    n_perm: int = 10000,
) -> CorrespondenceResult:
    """Compare panel disagreement with fixed human over-dispersion across conditions.

    The human target is loaded from the committed E1 multi-condition JSON. The
    no-AI ``"Human"`` baseline is always excluded. The confirmatory panel run can
    later pass its condition-level disagreement mapping directly into this function.
    """
    human_overdispersion = _load_human_overdispersion(human_overdispersion_path)
    return _build_result(
        panel_disagreement_by_condition,
        human_overdispersion,
        seed=seed,
        n_boot=n_boot,
        n_perm=n_perm,
        include_sensitivity=True,
    )
