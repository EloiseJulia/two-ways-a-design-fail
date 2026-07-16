"""Leakage-safe leave-one-item-out generalization metrics for E3.

The core firewall is structural: fitting sees only train items with targets.
The held-out item is passed to ``predict_fn`` as a target-free view containing
only its id and train-usable features.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Mapping, Protocol, Sequence

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class LOIOItem:
    """One intervention/item with an observed axis-1 target and non-leaky features."""

    item_id: str
    target: float
    features: Mapping[str, float]

    def heldout_view(self) -> "LOIOHeldoutItem":
        """Return the target-free view that predictors receive for the held-out item."""

        return LOIOHeldoutItem(item_id=self.item_id, features=dict(self.features))

    def to_dict(self) -> dict[str, object]:
        return {"item_id": self.item_id, "target": float(self.target), "features": dict(self.features)}


@dataclass(frozen=True)
class LOIOHeldoutItem:
    """Target-free held-out item view used to prevent LOIO label leakage."""

    item_id: str
    features: Mapping[str, float]

    def to_dict(self) -> dict[str, object]:
        return {"item_id": self.item_id, "features": dict(self.features)}


@dataclass(frozen=True)
class LOIOPredictionRow:
    """Per-item LOIO prediction and scoring row."""

    item_id: str
    actual: float
    predicted: float
    actual_direction: int
    predicted_direction: int
    direction_hit: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class LOIOResult:
    """LOIO direction and ranking generalization summary."""

    n: int
    hit_rate: float
    hit_p: float
    spearman_rho: float
    spearman_p: float
    degenerate: bool
    per_item: tuple[LOIOPredictionRow, ...]
    seed: int
    n_perm: int
    note: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "n": self.n,
            "hit_rate": self.hit_rate,
            "hit_p": self.hit_p,
            "spearman_rho": self.spearman_rho,
            "spearman_p": self.spearman_p,
            "degenerate": self.degenerate,
            "per_item": [row.to_dict() for row in self.per_item],
            "seed": self.seed,
            "n_perm": self.n_perm,
            "note": self.note,
        }


class PredictFn(Protocol):
    def __call__(self, *, train: Sequence[LOIOItem], heldout: LOIOHeldoutItem) -> float:
        ...


def loio_generalization(
    items: Sequence[LOIOItem],
    predict_fn: PredictFn,
    *,
    seed: int = 42,
    n_perm: int = 10000,
) -> LOIOResult:
    """Run leakage-safe leave-one-item-out prediction and score E3 metrics.

    For each held-out item, ``predict_fn`` receives exactly two arguments:
    (1) target-bearing train items that exclude the held-out item, and
    (2) a target-free held-out view. Any normalization, thresholds, or model
    parameters must therefore be fit from the train split only.
    """

    if n_perm < 0:
        raise ValueError("n_perm must be non-negative")

    item_tuple = tuple(items)
    if not item_tuple:
        raise ValueError("items cannot be empty")
    if len({item.item_id for item in item_tuple}) != len(item_tuple):
        raise ValueError("LOIO item_id values must be unique")

    rows: list[LOIOPredictionRow] = []
    for i, heldout in enumerate(item_tuple):
        train = tuple(item for j, item in enumerate(item_tuple) if j != i)
        predicted = float(predict_fn(train=train, heldout=heldout.heldout_view()))
        actual = float(heldout.target)
        actual_direction = _direction(actual)
        predicted_direction = _direction(predicted)
        rows.append(
            LOIOPredictionRow(
                item_id=heldout.item_id,
                actual=actual,
                predicted=predicted,
                actual_direction=actual_direction,
                predicted_direction=predicted_direction,
                direction_hit=actual_direction == predicted_direction,
            )
        )

    n = len(rows)
    hits = sum(row.direction_hit for row in rows)
    hit_rate = hits / n
    degenerate = n < 3
    note = None
    if degenerate:
        note = (
            f"DEGENERATE LOIO WARNING: n={n} items. Direction/ranking metrics "
            "with n<3 are plumbing checks only, not scientific evidence."
        )
        return LOIOResult(
            n=n,
            hit_rate=float(hit_rate),
            hit_p=1.0,
            spearman_rho=0.0,
            spearman_p=1.0,
            degenerate=True,
            per_item=tuple(rows),
            seed=seed,
            n_perm=n_perm,
            note=note,
        )

    hit_p = stats.binomtest(hits, n, p=0.5, alternative="greater").pvalue
    actuals = np.array([row.actual for row in rows], dtype=float)
    predicted = np.array([row.predicted for row in rows], dtype=float)
    spearman_rho = _safe_spearman(predicted, actuals)
    spearman_p = _spearman_permutation_pvalue(
        predicted,
        actuals,
        observed_rho=spearman_rho,
        seed=seed,
        n_perm=n_perm,
    )

    return LOIOResult(
        n=n,
        hit_rate=float(hit_rate),
        hit_p=float(hit_p),
        spearman_rho=float(spearman_rho),
        spearman_p=float(spearman_p),
        degenerate=False,
        per_item=tuple(rows),
        seed=seed,
        n_perm=n_perm,
        note=note,
    )


def _direction(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _safe_spearman(predicted: np.ndarray, actuals: np.ndarray) -> float:
    result = stats.spearmanr(predicted, actuals)
    rho = result.correlation
    return 0.0 if np.isnan(rho) else float(rho)


def _spearman_permutation_pvalue(
    predicted: np.ndarray,
    actuals: np.ndarray,
    *,
    observed_rho: float,
    seed: int,
    n_perm: int,
) -> float:
    if n_perm == 0:
        return 1.0

    seed_material = f"loio-spearman:{seed}:{len(predicted)}".encode()
    seed_bytes = hashlib.sha256(seed_material).digest()
    seed_int = int.from_bytes(seed_bytes[:4], "big") % (2**31)
    rng = np.random.RandomState(seed_int)

    count = 0
    for _ in range(n_perm):
        permuted = rng.permutation(actuals)
        perm_rho = _safe_spearman(predicted, permuted)
        if perm_rho >= observed_rho:
            count += 1
    return (count + 1) / (n_perm + 1)
