import math

import pytest

from twdf.analysis.reliability import (
    expected_calibration_error,
    generalization_gradient,
    measured_abstention_rate,
    reliable_radius,
)
from twdf.calibration.thresholds import ABSTAIN, HUMAN_STUDY, RELEASE, CalibrationExample, fit_thresholds
from twdf.features.ui_features import UIFeatureVector, feature_distance


def _features(*, confidence_shown=False, confidence_value=0.0, source="none", char_len=0, wrong_ai=False):
    return UIFeatureVector(
        has_explanation=source != "none",
        explanation_source=source,
        explanation_faithfulness=1.0 if source in {"lime", "expert"} else 0.0,
        n_highlight_spans=1 if source in {"lime", "expert"} else 0,
        info_density=0.1 if source in {"lime", "expert"} else 0.0,
        shows_predicted_class_only=source == "lime",
        shows_both_classes=False,
        is_adaptive=False,
        confidence_shown=confidence_shown,
        confidence_value=confidence_value,
        authority_cue=wrong_ai,
        wrong_ai=wrong_ai,
        explanation_char_len=char_len,
    )


def _gradient_records():
    records = []
    reference = _features()
    near = reference
    mid = _features(confidence_shown=True, confidence_value=0.5)
    far = _features(source="lime", char_len=40)

    for p, y in [(0.0, 0), (0.0, 0), (1.0, 1), (1.0, 1)]:
        records.append({"features": near, "reference_features": reference, "pred_prob": p, "outcome": y})
    for y in [0, 0, 1, 1]:
        records.append({"features": mid, "reference_features": reference, "pred_prob": 0.75, "outcome": y})
    for y in [0, 0, 0, 0]:
        records.append({"features": far, "reference_features": reference, "pred_prob": 0.9, "outcome": y})
    return records


def test_ece_zero_for_calibrated_and_hand_miscalibrated_example():
    calibrated = expected_calibration_error(
        [0.25] * 4 + [0.75] * 4,
        [1, 0, 0, 0, 1, 1, 1, 0],
        n_bins=4,
    )
    assert calibrated.expected_calibration_error == pytest.approx(0.0)

    hand = expected_calibration_error([0.9] * 10, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0], n_bins=10)
    assert hand.expected_calibration_error == pytest.approx(0.4)
    assert hand.max_calibration_error >= hand.expected_calibration_error
    assert sum(b["count"] for b in hand.to_dict()["bins"]) == 10


def test_generalization_gradient_is_monotone_with_feature_distance():
    result = generalization_gradient(_gradient_records(), by="feature_distance", n_bins=3)
    errors = [b.mean_absolute_error for b in result.bins]
    assert errors == sorted(errors)
    assert result.failure_region["label"] == result.bins[-1].label


def test_reliable_radius_excludes_high_distance_failure_region_and_full_calibration_gets_max():
    records = _gradient_records()
    radius = reliable_radius(records, ece_bound=0.2)
    distances = [feature_distance(r["features"], r["reference_features"]) for r in records]
    assert math.isfinite(radius)
    assert min(distances) <= radius < max(distances)

    calibrated = [dict(r, pred_prob=float(r["outcome"])) for r in records]
    assert reliable_radius(calibrated, ece_bound=0.0) == pytest.approx(max(distances))


def test_measured_abstention_rate_reuses_triage_and_fractions_sum_to_one():
    safe = _features()
    risky = _features(confidence_shown=True, confidence_value=0.5)
    ood = _features(source="placebo", char_len=500)
    model = fit_thresholds(
        [
            CalibrationExample(safe, axis1_overdispersion=0.1, axis2_over_reliance=0.1, is_dangerous=False),
            CalibrationExample(risky, axis1_overdispersion=0.8, axis2_over_reliance=0.1, is_dangerous=True),
        ],
        target_recall=1.0,
    )

    report = measured_abstention_rate(
        [safe, risky, ood],
        model,
        signals=[
            {"axis1_signal": 0.1, "axis2_signal": 0.1},
            {"axis1_signal": 0.8, "axis2_signal": 0.1},
            {"axis1_signal": 0.1, "axis2_signal": 0.1},
        ],
    )

    assert report.fractions[ABSTAIN] > 0.0
    assert report.counts[RELEASE] == 1
    assert report.counts[HUMAN_STUDY] == 1
    assert sum(report.fractions.values()) == pytest.approx(1.0)


def test_reliability_results_are_deterministic():
    records = _gradient_records()
    assert expected_calibration_error([0.9] * 10, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]).to_dict() == expected_calibration_error(
        [0.9] * 10, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    ).to_dict()
    assert generalization_gradient(records, by="feature_distance", n_bins=3).to_dict() == generalization_gradient(
        records, by="feature_distance", n_bins=3
    ).to_dict()
