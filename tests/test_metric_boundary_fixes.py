"""Regression tests for boundary/degenerate bugs found by the whole-codebase bug hunt.

1. betabinom_overdispersion: all-identical-at-boundary must give rho=0 (was 0.999).
2. condition_correlation: n<3 / constant input must return degenerate WITHOUT crashing.
3. ui_features: Wrong-AI-GT (dark) must set wrong_ai=True and authority_cue=True.
"""

import numpy as np

from twdf.metrics.overdispersion import betabinom_overdispersion, condition_correlation
from twdf.data.bansal_tasks import TaskStimulus
from twdf.features.ui_features import extract_ui_features


def test_betabinom_all_identical_boundary_returns_zero_rho():
    # Everyone relies 0/10 (mean_p=0) or 10/10 (mean_p=1): no between-user over-dispersion.
    # Pre-fix this returned rho=0.999 (a 0/0 -> NaN -> clamp bug that INVERTED the meaning).
    assert betabinom_overdispersion({f"u{i}": (0, 10) for i in range(8)}).rho == 0.0
    assert betabinom_overdispersion({f"u{i}": (10, 10) for i in range(8)}).rho == 0.0


def test_betabinom_identical_interior_still_zero():
    # Everyone 5/10 (mean_p=0.5, no between-user variance) -> rho ~ 0 (already correct).
    assert betabinom_overdispersion({f"u{i}": (5, 10) for i in range(8)}).rho < 1e-3


def test_betabinom_genuine_overdispersion_still_detected():
    # Half at 0/10, half at 10/10 = genuine MAXIMAL between-user over-dispersion -> rho high.
    mix = {f"u{i}": ((0, 10) if i < 4 else (10, 10)) for i in range(8)}
    assert betabinom_overdispersion(mix).rho > 0.5


def test_condition_correlation_n2_degenerate_no_crash():
    r = condition_correlation({"a": 0.1, "b": 0.2}, {"a": 0.01, "b": 0.02})
    assert r.degenerate and r.n_conditions == 2


def test_condition_correlation_constant_input_degenerate_no_crash():
    # Constant overdispersion across 3 conditions -> undefined correlation -> degenerate, no crash.
    r = condition_correlation(
        {"a": 0.1, "b": 0.2, "c": 0.3}, {"a": 0.0, "b": 0.0, "c": 0.0}
    )
    assert r.degenerate


def test_condition_correlation_valid_case_unaffected():
    r = condition_correlation(
        {"a": 0.1, "b": 0.2, "c": 0.3, "d": 0.4, "e": 0.5},
        {"a": 0.01, "b": 0.02, "c": 0.03, "d": 0.04, "e": 0.05},
        permutation_n=200,
        bootstrap_n=200,
    )
    assert not r.degenerate
    assert r.spearman_rho > 0.9


def _task(gt=1, pred=1):
    return TaskStimulus(
        task_id="t", domain="beer", text="a beer review", ground_truth=gt, ai_pred=pred,
        ai_conf=0.8, expert_explanation="", system_highlights="", expert_highlights_html="", testid="t",
    )


def test_wrong_ai_gt_sets_wrong_ai_and_authority_cue():
    v = extract_ui_features(_task(), "Wrong-AI-GT (dark)")
    assert v.wrong_ai is True
    assert v.authority_cue is True


def test_wrong_ai_dark_still_flagged():
    v = extract_ui_features(_task(), "Wrong-AI (dark)")
    assert v.wrong_ai is True and v.authority_cue is True


def test_non_dark_condition_not_wrong_ai():
    v = extract_ui_features(_task(), "Conf.+Single")
    assert v.wrong_ai is False
