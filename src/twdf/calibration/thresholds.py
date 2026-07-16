"""High-recall threshold calibration and abstaining triage.

This module builds the Module D machinery only. Freshly fitted thresholds are
unfrozen (``timestamp is None``); freezing thresholds on real calibration data is
a later, deliberate, logged step after the required axis-2 data exist.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Literal

import numpy as np

from twdf.features.ui_features import (
    FEATURE_NAMES,
    UIFeatureVector,
    feature_distance,
    feature_vector_to_array,
)

RELEASE = "RELEASE"
HUMAN_STUDY = "HUMAN_STUDY"
ABSTAIN = "ABSTAIN"
DecisionLabel = Literal["RELEASE", "HUMAN_STUDY", "ABSTAIN"]


@dataclass(frozen=True)
class CalibrationExample:
    """One calibration design with observed two-axis signals and danger label."""

    features: UIFeatureVector
    axis1_overdispersion: float
    axis2_over_reliance: float
    is_dangerous: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "features": self.features.to_dict(),
            "axis1_overdispersion": float(self.axis1_overdispersion),
            "axis2_over_reliance": float(self.axis2_over_reliance),
            "is_dangerous": bool(self.is_dangerous),
        }


@dataclass(frozen=True)
class ThresholdModel:
    """Unfrozen/frozen dual-threshold model plus feature-space OOD reference."""

    tau_disp: float
    tau_level: float
    calibration_features_ref: tuple[UIFeatureVector, ...]
    ood_radius: float
    target_recall: float
    precision_at_target_recall: float
    achieved_recall: float
    feature_mins: tuple[float, ...]
    feature_maxs: tuple[float, ...]
    seed: int = 42
    timestamp: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable representation."""

        return {
            "tau_disp": float(self.tau_disp),
            "tau_level": float(self.tau_level),
            "calibration_features_ref": [f.to_dict() for f in self.calibration_features_ref],
            "ood_radius": float(self.ood_radius),
            "target_recall": float(self.target_recall),
            "precision_at_target_recall": float(self.precision_at_target_recall),
            "achieved_recall": float(self.achieved_recall),
            "feature_names": list(FEATURE_NAMES),
            "feature_mins": [float(x) for x in self.feature_mins],
            "feature_maxs": [float(x) for x in self.feature_maxs],
            "seed": int(self.seed),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class TriageDecision:
    """Decision and audit reason returned by the pre-deployment triage screen."""

    decision: DecisionLabel
    reason: str
    trigger: str | None = None
    nearest_feature_distance: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def fit_thresholds(
    calibration: list[CalibrationExample],
    *,
    target_recall: float = 0.9,
    seed: int = 42,
) -> ThresholdModel:
    """Fit unfrozen high-recall screening thresholds on calibration examples only.

    The rule is ``axis1 >= tau_disp OR axis2 >= tau_level``. Candidate threshold
    pairs are scanned deterministically; among pairs meeting ``target_recall``,
    the model keeps the highest precision-at-recall operating point. The returned
    model is deliberately unfrozen (``timestamp=None``).
    """

    if not calibration:
        raise ValueError("calibration must contain at least one example")
    if not 0.0 < target_recall <= 1.0:
        raise ValueError("target_recall must be in (0, 1]")

    axis1 = np.array([_finite_float(ex.axis1_overdispersion, "axis1_overdispersion") for ex in calibration])
    axis2 = np.array([_finite_float(ex.axis2_over_reliance, "axis2_over_reliance") for ex in calibration])
    labels = np.array([bool(ex.is_dangerous) for ex in calibration], dtype=bool)
    if not np.any(labels):
        raise ValueError("calibration must include at least one dangerous example")

    best = _fit_threshold_pair(axis1, axis2, labels, target_recall)
    arrays = np.vstack([_feature_array_checked(ex.features) for ex in calibration])
    radius = _default_ood_radius([ex.features for ex in calibration])

    return ThresholdModel(
        tau_disp=best["tau_disp"],
        tau_level=best["tau_level"],
        calibration_features_ref=tuple(ex.features for ex in calibration),
        ood_radius=radius,
        target_recall=float(target_recall),
        precision_at_target_recall=best["precision"],
        achieved_recall=best["recall"],
        feature_mins=tuple(float(x) for x in np.min(arrays, axis=0)),
        feature_maxs=tuple(float(x) for x in np.max(arrays, axis=0)),
        seed=int(seed),
        timestamp=None,
    )


def precision_at_recall(
    axis1: Iterable[float],
    axis2: Iterable[float],
    labels: Iterable[bool],
    tau_disp: float,
    tau_level: float,
) -> dict[str, float]:
    """Compute precision and recall for the dual-threshold screening rule."""

    a1 = np.array([_finite_float(x, "axis1") for x in axis1], dtype=float)
    a2 = np.array([_finite_float(x, "axis2") for x in axis2], dtype=float)
    y = np.array([bool(x) for x in labels], dtype=bool)
    if not (len(a1) == len(a2) == len(y)):
        raise ValueError("axis1, axis2, and labels must have the same length")
    if not np.any(y):
        raise ValueError("labels must include at least one positive example")

    predicted = (a1 >= tau_disp) | (a2 >= tau_level)
    true_positive = int(np.sum(predicted & y))
    predicted_positive = int(np.sum(predicted))
    positive = int(np.sum(y))
    precision = true_positive / predicted_positive if predicted_positive else 0.0
    recall = true_positive / positive
    return {"precision": float(precision), "recall": float(recall)}


def triage(
    features: UIFeatureVector,
    axis1_signal: float,
    axis2_signal: float,
    model: ThresholdModel,
    *,
    reversal_flag: bool = False,
    ece: float | None = None,
    ece_threshold: float | None = None,
) -> TriageDecision:
    """Triage a design with abstention overriding release/human-study decisions."""

    a1 = _finite_float(axis1_signal, "axis1_signal")
    a2 = _finite_float(axis2_signal, "axis2_signal")
    distance = _nearest_reference_distance(features, model)

    novel_reason = _novel_dimension_reason(features, model)
    if novel_reason is not None:
        return TriageDecision(ABSTAIN, novel_reason, "novel_feature_dim", distance)
    if distance > model.ood_radius:
        return TriageDecision(
            ABSTAIN,
            "feature-space OOD: nearest calibration distance exceeds OOD radius",
            "ood_feature_distance",
            distance,
        )
    if reversal_flag:
        return TriageDecision(ABSTAIN, "human-agent effect reversal flag", "reversal_flag", distance)
    if ece is not None and ece_threshold is not None and ece > ece_threshold:
        return TriageDecision(ABSTAIN, "ECE exceeds abstention threshold", "ece", distance)

    if a1 >= model.tau_disp:
        return TriageDecision(HUMAN_STUDY, "axis-1 over-dispersion signal over threshold", "axis1", distance)
    if a2 >= model.tau_level:
        return TriageDecision(HUMAN_STUDY, "axis-2 over-reliance level signal over threshold", "axis2", distance)
    return TriageDecision(RELEASE, "both axis signals below calibrated thresholds", None, distance)


def freeze_thresholds(model: ThresholdModel, *, timestamp: str) -> ThresholdModel:
    """Return a timestamped copy of a threshold model.

    Freezing thresholds on real data must be a later, deliberate, logged UTC
    step after the required calibration data (including E4 axis-2) are available.
    This helper provides the mechanism only and does not write artifacts.
    """

    if not timestamp or not isinstance(timestamp, str):
        raise ValueError("timestamp must be a non-empty UTC timestamp string")
    return replace(model, timestamp=timestamp)


def threshold_model_to_json(model: ThresholdModel, path: str | Path | None = None) -> str:
    """Serialize a frozen threshold model to deterministic JSON.

    If ``path`` is provided, the model must already be frozen and the JSON is
    written there. The fit path never calls this helper, so no frozen-τ artifact
    is produced accidentally.
    """

    if model.timestamp is None:
        raise ValueError("refusing to serialize unfrozen thresholds as a frozen artifact")
    text = json.dumps(model.to_dict(), indent=2, sort_keys=True)
    if path is not None:
        Path(path).write_text(text + "\n", encoding="utf-8")
    return text


def _fit_threshold_pair(
    axis1: np.ndarray,
    axis2: np.ndarray,
    labels: np.ndarray,
    target_recall: float,
) -> dict[str, float]:
    axis1_candidates = _threshold_candidates(axis1)
    axis2_candidates = _threshold_candidates(axis2)
    best: dict[str, float] | None = None

    for tau_disp in axis1_candidates:
        for tau_level in axis2_candidates:
            metrics = precision_at_recall(axis1, axis2, labels, float(tau_disp), float(tau_level))
            if metrics["recall"] + 1e-12 < target_recall:
                continue
            flagged = int(np.sum((axis1 >= tau_disp) | (axis2 >= tau_level)))
            candidate = {
                "tau_disp": float(tau_disp),
                "tau_level": float(tau_level),
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "flagged": float(flagged),
            }
            if best is None or _is_better_threshold(candidate, best):
                best = candidate

    if best is None:
        raise RuntimeError("no threshold pair met target_recall; candidate construction is invalid")
    return best


def _threshold_candidates(values: np.ndarray) -> list[float]:
    unique = sorted(float(x) for x in np.unique(values))
    above_max = math.nextafter(max(unique), math.inf)
    below_min = math.nextafter(min(unique), -math.inf)
    return [below_min, *unique, above_max]


def _is_better_threshold(candidate: dict[str, float], incumbent: dict[str, float]) -> bool:
    fields = ("precision", "recall", "tau_disp", "tau_level")
    for field in fields:
        if not math.isclose(candidate[field], incumbent[field], rel_tol=0.0, abs_tol=1e-12):
            return candidate[field] > incumbent[field]
    return candidate["flagged"] < incumbent["flagged"]


def _default_ood_radius(features: list[UIFeatureVector]) -> float:
    if len(features) == 1:
        return 0.0
    nearest: list[float] = []
    for i, feature in enumerate(features):
        distances = [feature_distance(feature, other) for j, other in enumerate(features) if i != j]
        nearest.append(min(distances))
    return float(np.percentile(np.array(nearest, dtype=float), 95))


def _nearest_reference_distance(features: UIFeatureVector, model: ThresholdModel) -> float:
    if not model.calibration_features_ref:
        raise ValueError("model must contain at least one calibration reference feature vector")
    _feature_array_checked(features)
    return float(min(feature_distance(features, ref) for ref in model.calibration_features_ref))


def _novel_dimension_reason(features: UIFeatureVector, model: ThresholdModel) -> str | None:
    array = _feature_array_checked(features)
    if len(model.feature_mins) != len(FEATURE_NAMES) or len(model.feature_maxs) != len(FEATURE_NAMES):
        return "model feature bounds do not match FEATURE_NAMES"
    mins = np.array(model.feature_mins, dtype=float)
    maxs = np.array(model.feature_maxs, dtype=float)
    tolerance = 1e-12
    below = array < (mins - tolerance)
    above = array > (maxs + tolerance)
    if np.any(below | above):
        index = int(np.flatnonzero(below | above)[0])
        return f"novel/uncalibrated feature dimension: {FEATURE_NAMES[index]}"
    return None


def _feature_array_checked(features: UIFeatureVector) -> np.ndarray:
    array = feature_vector_to_array(features)
    if array.shape != (len(FEATURE_NAMES),):
        raise ValueError("feature vector shape does not match FEATURE_NAMES")
    if not np.all(np.isfinite(array)):
        raise ValueError("feature vector contains non-finite values")
    return array


def _finite_float(value: float, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number
