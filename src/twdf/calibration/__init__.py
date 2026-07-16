"""Calibration and triage machinery for the dual-threshold protocol."""

from twdf.calibration.thresholds import (
    ABSTAIN,
    HUMAN_STUDY,
    RELEASE,
    CalibrationExample,
    ThresholdModel,
    TriageDecision,
    fit_thresholds,
    freeze_thresholds,
    precision_at_recall,
    threshold_model_to_json,
    triage,
)

__all__ = [
    "ABSTAIN",
    "HUMAN_STUDY",
    "RELEASE",
    "CalibrationExample",
    "ThresholdModel",
    "TriageDecision",
    "fit_thresholds",
    "freeze_thresholds",
    "precision_at_recall",
    "threshold_model_to_json",
    "triage",
]
