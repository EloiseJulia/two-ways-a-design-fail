from __future__ import annotations

import numpy as np
import pytest

from twdf.analysis.loio import LOIOHeldoutItem, LOIOItem, loio_generalization


def _linear_predict(train: tuple[LOIOItem, ...], heldout: LOIOHeldoutItem) -> float:
    x = np.array([item.features["x"] for item in train], dtype=float)
    y = np.array([item.target for item in train], dtype=float)
    slope, intercept = np.polyfit(x, y, deg=1)
    return float(slope * heldout.features["x"] + intercept)


def test_known_generalization_signal_direction_and_ranking_are_significant():
    items = [
        LOIOItem(item_id=f"item_{i}", target=float(x), features={"x": float(x)})
        for i, x in enumerate(range(-10, 0))
    ] + [
        LOIOItem(item_id=f"item_{i + 10}", target=float(x), features={"x": float(x)})
        for i, x in enumerate(range(1, 11))
    ]

    result = loio_generalization(items, _linear_predict, seed=123, n_perm=2000)

    assert result.hit_rate > 0.5
    assert result.hit_p < 0.05
    assert result.spearman_rho > 0
    assert result.spearman_p < 0.05
    assert not result.degenerate


def test_null_signal_is_not_significant():
    targets = [
        1.764,
        0.400,
        0.979,
        2.241,
        1.868,
        -0.977,
        0.950,
        -0.151,
        -0.103,
        0.411,
        0.144,
        1.454,
        0.761,
        0.122,
        0.444,
        0.334,
        1.494,
        -0.205,
        0.313,
        -0.854,
        -2.553,
        0.654,
        0.864,
        -0.742,
        2.270,
        -1.454,
        0.046,
        -0.187,
        1.533,
        1.469,
    ]
    items = [
        LOIOItem(item_id=f"item_{i}", target=target, features={"x": float(i)})
        for i, target in enumerate(targets)
    ]

    result = loio_generalization(items, _linear_predict, seed=123, n_perm=2000)

    assert 0.25 <= result.hit_rate <= 0.75
    assert result.hit_p >= 0.05
    assert result.spearman_p >= 0.05


def test_leakage_firewall_withholds_heldout_target_from_predict_fn():
    items = [
        LOIOItem(item_id=f"item_{i}", target=float(i - 2), features={"x": float(i)})
        for i in range(5)
    ]
    seen_calls: list[tuple[str, set[str], bool]] = []

    def spy_predict(train: tuple[LOIOItem, ...], heldout: LOIOHeldoutItem) -> float:
        train_ids = {item.item_id for item in train}
        heldout_has_target = hasattr(heldout, "target")
        seen_calls.append((heldout.item_id, train_ids, heldout_has_target))
        assert heldout.item_id not in train_ids
        assert not heldout_has_target
        with pytest.raises(AttributeError):
            getattr(heldout, "target")
        return float(heldout.features["x"] - 2)

    loio_generalization(items, spy_predict, seed=7, n_perm=100)

    assert len(seen_calls) == len(items)
    assert all(not heldout_has_target for _, _, heldout_has_target in seen_calls)


def test_degenerate_guard_for_fewer_than_three_items():
    items = [
        LOIOItem(item_id="a", target=-1.0, features={"x": -1.0}),
        LOIOItem(item_id="b", target=1.0, features={"x": 1.0}),
    ]

    result = loio_generalization(items, lambda train, heldout: heldout.features["x"])

    assert result.degenerate
    assert result.hit_p == 1.0
    assert result.spearman_p == 1.0
    assert result.spearman_rho == 0.0
    assert result.note is not None


def test_determinism_same_seed_same_json():
    items = [
        LOIOItem(item_id=f"item_{i}", target=float(x), features={"x": float(x)})
        for i, x in enumerate([-4, -3, -2, -1, 1, 2, 3, 4])
    ]

    first = loio_generalization(items, _linear_predict, seed=99, n_perm=500).to_dict()
    second = loio_generalization(items, _linear_predict, seed=99, n_perm=500).to_dict()

    assert first == second
