from __future__ import annotations

from pathlib import Path

from twdf.calibration.thresholds import (
    ABSTAIN,
    HUMAN_STUDY,
    RELEASE,
    CalibrationExample,
    ThresholdModel,
    fit_thresholds,
    freeze_thresholds,
    precision_at_recall,
    triage,
)
from twdf.features.ui_features import UIFeatureVector, feature_distance


def _feature(
    *,
    spans: int = 2,
    confidence: float = 0.8,
    chars: int = 100,
    source: str = "lime",
    both: bool = False,
    wrong_ai: bool = False,
) -> UIFeatureVector:
    return UIFeatureVector(
        has_explanation=source != "none",
        explanation_source=source,
        explanation_faithfulness=1.0 if source in {"lime", "expert"} else 0.0,
        n_highlight_spans=spans,
        info_density=spans / 20.0,
        shows_predicted_class_only=not both and source != "none",
        shows_both_classes=both,
        is_adaptive=False,
        confidence_shown=True,
        confidence_value=confidence,
        authority_cue=wrong_ai,
        wrong_ai=wrong_ai,
        explanation_char_len=chars,
    )


def _calibration() -> list[CalibrationExample]:
    base = _feature()
    alt = _feature(spans=3, confidence=0.7, chars=130)
    return [
        CalibrationExample(base, 0.05, 0.04, False),
        CalibrationExample(base, 0.08, 0.05, False),
        CalibrationExample(alt, 0.12, 0.08, False),
        CalibrationExample(alt, 0.62, 0.10, True),
        CalibrationExample(base, 0.75, 0.15, True),
        CalibrationExample(alt, 0.81, 0.20, True),
        CalibrationExample(base, 0.18, 0.91, True),
    ]


def test_fit_thresholds_recovers_separator_and_reports_precision_above_chance() -> None:
    calibration = _calibration()
    model = fit_thresholds(calibration, target_recall=0.9)

    labels = [ex.is_dangerous for ex in calibration]
    report = precision_at_recall(
        [ex.axis1_overdispersion for ex in calibration],
        [ex.axis2_over_reliance for ex in calibration],
        labels,
        model.tau_disp,
        model.tau_level,
    )
    chance = sum(labels) / len(labels)

    assert report["recall"] >= 0.9
    assert report["precision"] > chance
    assert model.achieved_recall == report["recall"]
    assert model.precision_at_target_recall == report["precision"]
    assert (0.18 < model.tau_disp <= 0.62) or (0.08 < model.tau_level <= 0.10)


def test_high_recall_property_at_target_recall() -> None:
    calibration = _calibration()
    model = fit_thresholds(calibration, target_recall=0.9)
    report = precision_at_recall(
        [ex.axis1_overdispersion for ex in calibration],
        [ex.axis2_over_reliance for ex in calibration],
        [ex.is_dangerous for ex in calibration],
        model.tau_disp,
        model.tau_level,
    )

    assert report["recall"] >= model.target_recall


def test_triage_decisions_include_ood_abstention() -> None:
    calibration = _calibration()
    model = fit_thresholds(calibration, target_recall=0.9)
    in_dist = calibration[0].features
    ood = _feature(spans=60, confidence=0.99, chars=3000, source="expert", both=True, wrong_ai=True)

    assert triage(in_dist, model.tau_disp + 0.01, 0.0, model).decision == HUMAN_STUDY
    assert triage(in_dist, 0.0, 0.0, model).decision == RELEASE
    assert feature_distance(ood, in_dist) > model.ood_radius
    abstain = triage(ood, 0.0, 0.0, model)
    assert abstain.decision == ABSTAIN
    assert abstain.trigger in {"ood_feature_distance", "novel_feature_dim"}


def test_tau_stays_unfrozen_and_fit_writes_no_results_artifact() -> None:
    results_dir = Path.cwd() / "results"
    before = set(results_dir.glob("*threshold*")) if results_dir.exists() else set()

    model = fit_thresholds(_calibration(), target_recall=0.9)
    frozen = freeze_thresholds(model, timestamp="2026-07-16T00:00:00Z")

    after = set(results_dir.glob("*threshold*")) if results_dir.exists() else set()
    assert model.timestamp is None
    assert frozen.timestamp == "2026-07-16T00:00:00Z"
    assert after == before


def test_fit_thresholds_is_deterministic() -> None:
    calibration = _calibration()
    first: ThresholdModel = fit_thresholds(calibration, target_recall=0.9, seed=123)
    second: ThresholdModel = fit_thresholds(calibration, target_recall=0.9, seed=123)

    assert first.to_dict() == second.to_dict()
