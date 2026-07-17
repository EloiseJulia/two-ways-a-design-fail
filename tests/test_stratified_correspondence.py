
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pytest

from twdf.analysis.stratified_correspondence import (
    confirmatory_robustness,
    load_real_bansal_human_raw,
    stratified_correspondence,
)


CONDITIONS = [
    "Conf.",
    "Conf.+Single",
    "Conf.+Double",
    "Conf.+Adaptive",
    "Conf.+Adaptive (Expert)",
]


@dataclass(frozen=True)
class Resp:
    persona_id: str
    model: str
    task_id: str
    ui_condition: str
    seed: int
    system1_decision: str
    final_decision: str
    trace: dict


def _make_signal(panel_mode: str = "signal"):
    tasks = [f"t{i:02d}" for i in range(45)]
    conf = {task: (i + 1) / 46 for i, task in enumerate(tasks)}
    rows = []
    panel = []
    users = [f"u{i}" for i in range(12)]
    personas = [f"p{i}" for i in range(12)]
    z = [-1.0, -0.82, -0.64, -0.45, -0.27, -0.09, 0.09, 0.27, 0.45, 0.64, 0.82, 1.0]
    null_ranks = [7, 2, 12, 0, 9, 4, 14, 1, 10, 5, 13, 3, 8, 6, 11]
    for ci, cond in enumerate(CONDITIONS):
        for si in range(3):
            cell_tasks = tasks[si * 15 : (si + 1) * 15]
            rank = ci * 3 + si
            amp = 0.01 + 0.49 * rank / 14
            for user, zv in zip(users, z):
                p = max(0.02, min(0.98, 0.5 + amp * zv))
                k = int(round(p * len(cell_tasks)))
                for ti, task in enumerate(cell_tasks):
                    relied = ti < k
                    rows.append({
                        "user_id": user,
                        "task_id": task,
                        "ui_condition": cond,
                        "ai_advice": "1",
                        "human_final": "1" if relied else "0",
                        "relied": relied,
                        "confidence": conf[task],
                    })
            panel_rank = rank if panel_mode == "signal" else null_ranks[rank]
            panel_amp = 0.01 + 0.49 * panel_rank / 14
            for persona, zv in zip(personas, z):
                p = max(0.02, min(0.98, 0.5 + panel_amp * zv))
                k = int(round(p * len(cell_tasks)))
                for ti, task in enumerate(cell_tasks):
                    relied = ti < k
                    panel.append(Resp(
                        persona_id=persona,
                        model="m1",
                        task_id=task,
                        ui_condition=cond,
                        seed=0,
                        system1_decision="0",
                        final_decision="1" if relied else "0",
                        trace={"ai_advice": "1", "ai_conf": conf[task]},
                    ))
    return panel, pd.DataFrame(rows)


def test_known_signal_rho_near_one_and_more_than_five_points():
    panel, human = _make_signal()
    result = stratified_correspondence(
        panel,
        human_raw_loader=lambda: human,
        n_boot=200,
        n_perm=500,
        seed=7,
    )
    assert result.n_points == 15
    assert result.n_points > 5
    assert result.spearman_rho is not None and result.spearman_rho > 0.95
    assert result.spearman_p is not None and result.spearman_p < 0.05


def test_null_reversed_signal_is_not_positive_claim():
    panel, human = _make_signal(panel_mode="null")
    result = stratified_correspondence(
        panel,
        human_raw_loader=lambda: human,
        n_boot=100,
        n_perm=300,
        seed=8,
    )
    assert result.n_points == 15
    assert result.spearman_rho is not None and abs(result.spearman_rho) < 0.4
    assert result.spearman_p is not None and result.spearman_p >= 0.05


def test_stratification_correctness_guard_and_no_leakage():
    panel, human = _make_signal()
    # Make one cell uninterpretable: fewer than three human users.
    mask = ~((human["ui_condition"] == "Conf.") & (human["task_id"].isin([f"t{i:02d}" for i in range(15)])) & (~human["user_id"].isin(["u0", "u1"])))
    human_small = human[mask].copy()
    human_small["ground_truth"] = object()
    result = stratified_correspondence(panel, human_raw_loader=lambda: human_small, n_boot=50, n_perm=50)
    assert [s.task_ids for s in result.strata] == [
        [f"t{i:02d}" for i in range(15)],
        [f"t{i:02d}" for i in range(15, 30)],
        [f"t{i:02d}" for i in range(30, 45)],
    ]
    bad_cell = next(c for c in result.cell_table if c.condition == "Conf." and c.stratum == 0)
    assert not bad_cell.included
    assert "too_few_human_users" in bad_cell.flags
    with pytest.raises(ValueError):
        stratified_correspondence(panel, human_raw_loader=lambda: human, stratify_by="ground_truth")
    with pytest.raises(ValueError):
        stratified_correspondence(panel, human_raw_loader=lambda: human, stratify_by="relied")


def test_confirmatory_robustness_leave_one_out_and_fields():
    pairs = [
        {"condition": "a", "panel_disagreement": 1, "human_rho": 1},
        {"condition": "b", "panel_disagreement": 2, "human_rho": 2},
        {"condition": "c", "panel_disagreement": 3, "human_rho": 3},
        {"condition": "d", "panel_disagreement": 4, "human_rho": 4},
        {"condition": "e", "panel_disagreement": 5, "human_rho": 0},
    ]
    robust = confirmatory_robustness({
        "per_model": {
            "m1": {
                "within_task_estimator": {"estimate": 0.2, "ci_lower": 0.1, "ci_upper": 0.3},
                "conflict_conditioned_overdispersion": {"estimate": 0.05, "ci_lower": 0.01, "ci_upper": 0.09},
                "cross_condition_correspondence": {"aligned_pairs": pairs, "spearman_rho": 0.3, "bootstrap_ci": [0.0, 1.0], "n_conditions": 5},
            }
        }
    })
    d = robust.to_dict()
    assert "m1" in d["per_model_stability"]
    assert d["per_model_stability"]["m1"]["within_task_estimator"]["ci_excludes_zero"] is True
    loo = d["leave_one_condition_out"]["m1"]
    omitted_e = next(x for x in loo if x["omitted_condition"] == "e")
    assert omitted_e["spearman_rho"] == pytest.approx(1.0)
    assert omitted_e["delta_from_full"] == pytest.approx(0.7)


def test_determinism():
    panel, human = _make_signal()
    a = stratified_correspondence(panel, human_raw_loader=lambda: human, n_boot=100, n_perm=100, seed=123).to_dict()
    b = stratified_correspondence(panel, human_raw_loader=lambda: human, n_boot=100, n_perm=100, seed=123).to_dict()
    assert a == b


def test_real_csv_loader_and_stratification_work_offline():
    csv_path = Path("data/raw/decision-result-filter.csv")
    assert csv_path.exists()
    human = load_real_bansal_human_raw(csv_path)
    assert set(human["ui_condition"].unique()) <= set(CONDITIONS)
    assert len(human) > 0

    tasks = sorted(human["task_id"].unique(), key=lambda x: int(x) if str(x).isdigit() else str(x))[:15]
    task_conf = human[human["task_id"].isin(tasks)].groupby("task_id")["ai_conf"].mean().to_dict()
    panel = []
    for cond in CONDITIONS:
        for task in tasks:
            advice = str(human.loc[(human["ui_condition"] == cond) & (human["task_id"] == task), "ai_advice"].iloc[0])
            other = "0" if advice != "0" else "1"
            conf = float(task_conf[task])
            for pi in range(5):
                relied = ((pi + int(float(conf) * 1000) + len(cond)) % 5) <= pi
                panel.append(Resp(
                    persona_id=f"p{pi}",
                    model="real-csv-smoke",
                    task_id=str(task),
                    ui_condition=cond,
                    seed=0,
                    system1_decision=other,
                    final_decision=advice if relied else other,
                    trace={"ai_advice": advice, "ai_conf": conf},
                ))
    result = stratified_correspondence(panel, human_raw_loader=lambda: human, n_boot=50, n_perm=50, seed=5)
    assert result.n_points >= 10
    assert len(result.cell_table) == 15
    assert result.to_dict()["exploratory_vs_confirmatory"].startswith("EXPLORATORY")
