import json
from pathlib import Path

import pytest

from twdf.analysis.panel_human_correspondence import (
    CANONICAL_AI_CONDITION_ORDER,
    CorrespondenceResult,
    panel_human_condition_correspondence,
)


REAL_HUMAN_PATH = Path(__file__).resolve().parents[1] / "results" / "e1_multicond.json"


def _rank_identical_panel() -> dict[str, float]:
    return dict(zip(CANONICAL_AI_CONDITION_ORDER, [0.70, 0.20, 0.90, 0.40, 0.10]))


def _rank_opposite_panel() -> dict[str, float]:
    return dict(zip(CANONICAL_AI_CONDITION_ORDER, [0.20, 0.40, 0.10, 0.30, 0.50]))


def test_known_positive_signal_matches_real_human_ranks():
    result = panel_human_condition_correspondence(
        _rank_identical_panel(),
        REAL_HUMAN_PATH,
        seed=123,
        n_boot=1000,
        n_perm=2000,
    )

    assert isinstance(result, CorrespondenceResult)
    assert result.shared_conditions == list(CANONICAL_AI_CONDITION_ORDER)
    assert result.spearman_rho == pytest.approx(1.0)
    assert result.spearman_p < 0.05
    assert result.bootstrap_ci is not None
    assert result.bootstrap_ci[0] > 0
    assert result.pearson_r is not None


def test_known_negative_signal_opposes_real_human_ranks():
    result = panel_human_condition_correspondence(
        _rank_opposite_panel(),
        REAL_HUMAN_PATH,
        seed=123,
        n_boot=1000,
        n_perm=2000,
    )

    assert result.spearman_rho == pytest.approx(-1.0)
    assert result.spearman_p < 0.05
    assert result.bootstrap_ci is not None
    assert result.bootstrap_ci[1] < 0


def test_null_shuffled_panel_is_not_significant():
    shuffled_panel = dict(
        zip(CANONICAL_AI_CONDITION_ORDER, [0.12, 0.88, 0.34, 0.65, 0.51])
    )

    result = panel_human_condition_correspondence(
        shuffled_panel,
        REAL_HUMAN_PATH,
        seed=123,
        n_boot=500,
        n_perm=2000,
    )

    assert not result.degenerate
    assert result.spearman_p is not None
    assert result.spearman_p > 0.05


def test_degenerate_guard_for_less_than_three_shared_conditions():
    panel = {
        "Conf.": 0.10,
        "Conf.+Double": 0.20,
        "Human": 0.99,
    }

    result = panel_human_condition_correspondence(
        panel,
        REAL_HUMAN_PATH,
        seed=123,
        n_boot=100,
        n_perm=100,
    )

    assert result.shared_conditions == ["Conf.", "Conf.+Double"]
    assert result.n_conditions == 2
    assert result.degenerate
    assert result.spearman_rho is None
    assert result.spearman_p is None
    assert result.bootstrap_ci is None
    assert result.pearson_r is None
    assert result.note is not None and "DEGENERATE" in result.note


def test_ceiling_flag_on_real_json_and_sensitivity_drops_expert():
    result = panel_human_condition_correspondence(
        _rank_identical_panel(),
        REAL_HUMAN_PATH,
        seed=123,
        n_boot=500,
        n_perm=1000,
    )

    expert_flag = result.ceiling_flags["Conf.+Adaptive (Expert)"]
    assert expert_flag.flagged
    assert expert_flag.excess_var is not None and expert_flag.excess_var < 1e-4

    for condition in CANONICAL_AI_CONDITION_ORDER:
        if condition != "Conf.+Adaptive (Expert)":
            assert not result.ceiling_flags[condition].flagged

    assert result.ceiling_excluded is not None
    assert "Conf.+Adaptive (Expert)" not in result.ceiling_excluded.shared_conditions
    assert result.ceiling_excluded.shared_conditions == [
        "Conf.",
        "Conf.+Single",
        "Conf.+Double",
        "Conf.+Adaptive",
    ]
    assert result.ceiling_excluded.n_conditions == 4
    assert not result.ceiling_excluded.degenerate


def test_determinism_and_json_serializable_output():
    kwargs = dict(seed=777, n_boot=500, n_perm=1000)
    first = panel_human_condition_correspondence(
        _rank_identical_panel(), REAL_HUMAN_PATH, **kwargs
    )
    second = panel_human_condition_correspondence(
        _rank_identical_panel(), REAL_HUMAN_PATH, **kwargs
    )

    assert first.to_dict() == second.to_dict()
    json.dumps(first.to_dict(), sort_keys=True)


def test_loader_uses_real_human_target_values_without_hardcoded_module_values():
    result = panel_human_condition_correspondence(
        _rank_identical_panel(),
        REAL_HUMAN_PATH,
        seed=123,
        n_boot=100,
        n_perm=100,
    )

    with REAL_HUMAN_PATH.open("r", encoding="utf-8") as f:
        human = json.load(f)["results"]["human_overdispersion"]

    aligned = {pair.condition: pair.human_rho for pair in result.aligned_pairs}
    assert aligned["Conf.+Adaptive (Expert)"] == pytest.approx(
        human["Conf.+Adaptive (Expert)"]["rho"]
    )
    assert "Human" not in result.shared_conditions
