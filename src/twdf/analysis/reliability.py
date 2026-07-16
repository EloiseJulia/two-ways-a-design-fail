"""E5 reliability metrics: calibration error, failure-region gradients, and abstention rates.

The functions in this module are deterministic and offline-only. They accept
already collected predictions/signals and deliberately reuse the Module D feature
space and triage machinery instead of learning or freezing thresholds here.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from twdf.calibration.thresholds import ABSTAIN, HUMAN_STUDY, RELEASE, ThresholdModel, triage
from twdf.features.ui_features import UIFeatureVector, feature_distance


@dataclass(frozen=True)
class ReliabilityBin:
    bin_index: int
    lower: float
    upper: float
    count: int
    mean_confidence: float | None
    empirical_accuracy: float | None
    calibration_error: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ECEResult:
    expected_calibration_error: float
    max_calibration_error: float
    n: int
    n_bins: int
    bins: tuple[ReliabilityBin, ...]

    @property
    def ece(self) -> float:
        return self.expected_calibration_error

    @property
    def reliability_bins(self) -> tuple[ReliabilityBin, ...]:
        return self.bins

    def to_dict(self) -> dict[str, Any]:
        return {
            "expected_calibration_error": float(self.expected_calibration_error),
            "ece": float(self.expected_calibration_error),
            "max_calibration_error": float(self.max_calibration_error),
            "n": int(self.n),
            "n_bins": int(self.n_bins),
            "bins": [b.to_dict() for b in self.bins],
        }


@dataclass(frozen=True)
class GradientBin:
    label: str
    count: int
    lower: float | None
    upper: float | None
    mean_covariate: float | None
    mean_absolute_error: float
    expected_calibration_error: float
    max_calibration_error: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GradientResult:
    by: str
    metric: str
    n: int
    bins: tuple[GradientBin, ...]
    failure_region: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "by": self.by,
            "metric": self.metric,
            "n": int(self.n),
            "bins": [b.to_dict() for b in self.bins],
            "failure_region": self.failure_region,
        }


@dataclass(frozen=True)
class AbstentionReport:
    n: int
    counts: dict[str, int]
    fractions: dict[str, float]
    decisions: tuple[dict[str, Any], ...]

    @property
    def abstain_fraction(self) -> float:
        return self.fractions[ABSTAIN]

    def to_dict(self) -> dict[str, Any]:
        return {
            "n": int(self.n),
            "counts": {key: int(self.counts[key]) for key in (ABSTAIN, HUMAN_STUDY, RELEASE)},
            "fractions": {key: float(self.fractions[key]) for key in (ABSTAIN, HUMAN_STUDY, RELEASE)},
            "decisions": list(self.decisions),
        }


def expected_calibration_error(
    pred_probs: Iterable[float],
    outcomes: Iterable[bool | int | float],
    *,
    n_bins: int = 10,
) -> ECEResult:
    """Compute equal-width-bin ECE and MCE for binary predictions."""

    probs, y = _prediction_arrays(pred_probs, outcomes)
    if n_bins <= 0:
        raise ValueError("n_bins must be positive")

    bins: list[ReliabilityBin] = []
    ece = 0.0
    mce = 0.0
    n = len(probs)
    for i in range(n_bins):
        lower = i / n_bins
        upper = (i + 1) / n_bins
        if i == 0:
            mask = (probs >= lower) & (probs <= upper)
        else:
            mask = (probs > lower) & (probs <= upper)
        count = int(np.sum(mask))
        if count == 0:
            bins.append(ReliabilityBin(i, float(lower), float(upper), 0, None, None, None))
            continue
        confidence = float(np.mean(probs[mask]))
        accuracy = float(np.mean(y[mask]))
        gap = abs(confidence - accuracy)
        ece += (count / n) * gap
        mce = max(mce, gap)
        bins.append(
            ReliabilityBin(
                i,
                float(lower),
                float(upper),
                count,
                confidence,
                accuracy,
                float(gap),
            )
        )

    return ECEResult(float(ece), float(mce), n, int(n_bins), tuple(bins))


def generalization_gradient(
    records: Sequence[Any],
    *,
    by: str,
    n_bins: int = 5,
) -> GradientResult:
    """Map prediction error across feature-distance, difficulty, or persona regions."""

    if not records:
        raise ValueError("records must contain at least one item")
    probs, y = _record_prediction_arrays(records)
    covariates = [_covariate_value(record, by) for record in records]

    if all(_is_number(value) for value in covariates):
        bins = _numeric_gradient_bins(np.asarray(covariates, dtype=float), probs, y, n_bins)
    else:
        bins = _categorical_gradient_bins(covariates, probs, y)
    failure = _failure_region(bins)
    return GradientResult(by=by, metric="mean_absolute_error+ece", n=len(records), bins=tuple(bins), failure_region=failure)


def reliable_radius(
    records: Sequence[Any],
    *,
    ece_bound: float,
    distance_key: str = "feature_distance",
) -> float:
    """Return the largest distance whose in-radius prefix ECE is within bound.

    Records are sorted by feature-space distance. The returned radius is the
    largest observed distance such that all records at or below that distance
    have ECE <= ``ece_bound``. Designs beyond the radius are outside the measured
    reliable region and should feed the abstention rule.
    """

    bound = float(ece_bound)
    if bound < 0 or not math.isfinite(bound):
        raise ValueError("ece_bound must be a finite non-negative number")
    if not records:
        raise ValueError("records must contain at least one item")
    probs, y = _record_prediction_arrays(records)
    distances = np.asarray([_covariate_value(record, distance_key) for record in records], dtype=float)
    if not np.all(np.isfinite(distances)):
        raise ValueError("feature distances must be finite")

    radius = 0.0
    for distance in sorted(float(x) for x in np.unique(distances)):
        mask = distances <= distance
        result = expected_calibration_error(probs[mask], y[mask], n_bins=min(10, int(np.sum(mask))))
        if result.expected_calibration_error <= bound + 1e-12:
            radius = distance
        else:
            break
    return float(radius)


def measured_abstention_rate(
    designs: Sequence[Any],
    threshold_model: ThresholdModel,
    *,
    signals: Sequence[Any] | Mapping[Any, Any],
) -> AbstentionReport:
    """Run Module D triage on designs and report RELEASE/HUMAN_STUDY/ABSTAIN fractions."""

    if not designs:
        raise ValueError("designs must contain at least one item")
    counts = {ABSTAIN: 0, HUMAN_STUDY: 0, RELEASE: 0}
    decisions: list[dict[str, Any]] = []

    for index, design in enumerate(designs):
        signal = _signal_for_design(signals, design, index)
        features = _design_features(design)
        decision = triage(
            features,
            _required_float(signal, "axis1_signal", aliases=("axis1", "axis1_overdispersion")),
            _required_float(signal, "axis2_signal", aliases=("axis2", "axis2_over_reliance")),
            threshold_model,
            reversal_flag=bool(_get(signal, "reversal_flag", False)),
            ece=_optional_float(signal, "ece"),
            ece_threshold=_optional_float(signal, "ece_threshold"),
        )
        counts[decision.decision] += 1
        row = decision.to_dict()
        row["index"] = index
        design_id = _get(design, "design_id", _get(design, "id", None))
        if design_id is not None:
            row["design_id"] = design_id
        decisions.append(row)

    n = len(designs)
    fractions = {key: counts[key] / n for key in (ABSTAIN, HUMAN_STUDY, RELEASE)}
    return AbstentionReport(n=n, counts=counts, fractions=fractions, decisions=tuple(decisions))


def _prediction_arrays(pred_probs: Iterable[float], outcomes: Iterable[bool | int | float]) -> tuple[np.ndarray, np.ndarray]:
    probs = np.asarray([float(p) for p in pred_probs], dtype=float)
    y = np.asarray([float(o) for o in outcomes], dtype=float)
    if len(probs) == 0:
        raise ValueError("pred_probs/outcomes must be non-empty")
    if len(probs) != len(y):
        raise ValueError("pred_probs and outcomes must have the same length")
    if not np.all(np.isfinite(probs)) or np.any((probs < 0.0) | (probs > 1.0)):
        raise ValueError("pred_probs must be finite probabilities in [0, 1]")
    if not np.all(np.isfinite(y)) or np.any((y < 0.0) | (y > 1.0)):
        raise ValueError("outcomes must be finite binary/0-1 values")
    return probs, y


def _record_prediction_arrays(records: Sequence[Any]) -> tuple[np.ndarray, np.ndarray]:
    probs = [_required_float(record, "pred_prob", aliases=("prediction", "prob", "p", "confidence")) for record in records]
    outcomes = [_required_float(record, "outcome", aliases=("actual", "label", "y")) for record in records]
    return _prediction_arrays(probs, outcomes)


def _numeric_gradient_bins(values: np.ndarray, probs: np.ndarray, y: np.ndarray, n_bins: int) -> list[GradientBin]:
    if n_bins <= 0:
        raise ValueError("n_bins must be positive")
    if not np.all(np.isfinite(values)):
        raise ValueError("numeric covariates must be finite")
    unique = np.unique(values)
    if len(unique) == 1:
        return [_make_gradient_bin("all", probs, y, values, 0, float(unique[0]), float(unique[0]))]

    edges = np.linspace(float(np.min(values)), float(np.max(values)), num=n_bins + 1)
    bins: list[GradientBin] = []
    for i in range(n_bins):
        lower = edges[i]
        upper = edges[i + 1]
        if i == 0:
            mask = (values >= lower) & (values <= upper)
        else:
            mask = (values > lower) & (values <= upper)
        if not np.any(mask):
            continue
        bins.append(_make_gradient_bin(f"[{lower:.6g}, {upper:.6g}]", probs[mask], y[mask], values[mask], i, lower, upper))
    return bins


def _categorical_gradient_bins(values: Sequence[Any], probs: np.ndarray, y: np.ndarray) -> list[GradientBin]:
    labels = sorted({str(value) for value in values})
    bins: list[GradientBin] = []
    value_array = np.asarray([str(value) for value in values], dtype=object)
    for label in labels:
        mask = value_array == label
        bins.append(_make_gradient_bin(label, probs[mask], y[mask], None, len(bins), None, None))
    return bins


def _make_gradient_bin(
    label: str,
    probs: np.ndarray,
    y: np.ndarray,
    values: np.ndarray | None,
    _: int,
    lower: float | None,
    upper: float | None,
) -> GradientBin:
    ece = expected_calibration_error(probs, y, n_bins=min(10, len(probs)))
    mae = float(np.mean(np.abs(probs - y)))
    return GradientBin(
        label=label,
        count=len(probs),
        lower=None if lower is None else float(lower),
        upper=None if upper is None else float(upper),
        mean_covariate=None if values is None else float(np.mean(values)),
        mean_absolute_error=mae,
        expected_calibration_error=ece.expected_calibration_error,
        max_calibration_error=ece.max_calibration_error,
    )


def _failure_region(bins: Sequence[GradientBin]) -> dict[str, Any] | None:
    if not bins:
        return None
    worst = max(bins, key=lambda b: (b.mean_absolute_error, b.expected_calibration_error, b.label))
    return {
        "label": worst.label,
        "count": int(worst.count),
        "mean_absolute_error": float(worst.mean_absolute_error),
        "expected_calibration_error": float(worst.expected_calibration_error),
        "lower": worst.lower,
        "upper": worst.upper,
    }


def _covariate_value(record: Any, by: str) -> Any:
    if by == "feature_distance":
        distance = _maybe_feature_distance(record)
        if distance is not None:
            return distance
    value = _get(record, by, None)
    if value is None:
        raise ValueError(f"record is missing covariate {by!r}")
    return value


def _maybe_feature_distance(record: Any) -> float | None:
    features = _get(record, "features", _get(record, "design_features", None))
    reference = _get(record, "reference_features", _get(record, "calibration_reference", None))
    if isinstance(features, UIFeatureVector) and isinstance(reference, UIFeatureVector):
        return feature_distance(features, reference)
    refs = _get(record, "calibration_features_ref", None)
    if isinstance(features, UIFeatureVector) and refs is not None:
        return min(feature_distance(features, ref) for ref in refs)
    value = _get(record, "feature_distance", None)
    if value is None:
        return None
    return float(value)


def _design_features(design: Any) -> UIFeatureVector:
    if isinstance(design, UIFeatureVector):
        return design
    features = _get(design, "features", _get(design, "design_features", None))
    if isinstance(features, UIFeatureVector):
        return features
    raise ValueError("each design must be or contain a UIFeatureVector under 'features'")


def _signal_for_design(signals: Sequence[Any] | Mapping[Any, Any], design: Any, index: int) -> Any:
    if isinstance(signals, Mapping):
        design_id = _get(design, "design_id", _get(design, "id", index))
        if design_id in signals:
            return signals[design_id]
        if index in signals:
            return signals[index]
        raise ValueError(f"missing signals for design {design_id!r}")
    if index < len(signals):
        return signals[index]
    raise ValueError("signals must provide one item per design")


def _get(record: Any, field: str, default: Any = None) -> Any:
    if isinstance(record, Mapping):
        return record.get(field, default)
    return getattr(record, field, default)


def _required_float(record: Any, field: str, *, aliases: tuple[str, ...] = ()) -> float:
    value = _get(record, field, None)
    if value is None:
        for alias in aliases:
            value = _get(record, alias, None)
            if value is not None:
                break
    if value is None:
        raise ValueError(f"record is missing {field!r}")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def _optional_float(record: Any, field: str) -> float | None:
    value = _get(record, field, None)
    if value is None:
        return None
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def _is_number(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number)
