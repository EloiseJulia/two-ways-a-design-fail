
import json
from pathlib import Path

import pytest

from twdf.analysis.confirmatory_axis1 import analyze_confirmatory_axis1
from twdf.data.bansal_tasks import TaskStimulus
from twdf.experiments.confirmatory_axis1 import run_confirmatory_axis1
from twdf.panel.provider import ModelProvider
from twdf.panel.stub import Persona


CONDITIONS = [
    "Conf.",
    "Conf.+Single",
    "Conf.+Double",
    "Conf.+Adaptive",
    "Conf.+Adaptive (Expert)",
]
MODELS = ["openai/gpt-4o", "openai/gpt-4.1-mini"]


def _human_target(path: Path, values=None) -> Path:
    if values is None:
        values = [0.0, 0.1, 0.2, 0.3, 0.4]
    human = {
        cond: {"rho": value, "excess_var": value + 0.01, "mean_p": 0.5, "empirical_var": value + 0.02}
        for cond, value in zip(CONDITIONS, values)
    }
    human["Human"] = {"rho": 0.0, "excess_var": 0.0, "mean_p": 0.5, "empirical_var": 0.0}
    path.write_text(json.dumps({"results": {"human_overdispersion": human}}), encoding="utf-8")
    return path


def _row(persona, model, task, condition, rely, seed=42, ai_correct=True):
    return {
        "persona_id": persona,
        "model": model,
        "task_id": task,
        "ui_condition": condition,
        "seed": seed,
        "system1_decision": "0",
        "final_decision": "1" if rely else "0",
        "ai_advice": "1",
        "relied": bool(rely),
        "task_difficulty": 0.5,
        "trace": {"ai_advice": "1", "ground_truth": "1" if ai_correct else "0", "ai_correct": ai_correct},
    }


def _known_signal_responses(model_levels=None):
    if model_levels is None:
        model_levels = {MODELS[0]: [0, 2, 4, 6, 10], MODELS[1]: [0, 1, 2, 3, 5]}
    personas = [f"p{i}" for i in range(10)]
    tasks = [f"t{j}" for j in range(20)]
    rows = []
    for model in MODELS:
        levels = model_levels[model]
        for condition, gap in zip(CONDITIONS, levels):
            for persona_index, persona in enumerate(personas):
                for task_index, task in enumerate(tasks):
                    if gap == 0:
                        rely = task_index % 2 == 0
                    else:
                        high = persona_index < len(personas) // 2
                        cutoff = 10 + gap if high else 10 - gap
                        rely = task_index < cutoff
                    rows.append(_row(persona, model, task, condition, rely, ai_correct=(task_index % 3 != 0)))
    return rows


def _null_responses():
    personas = [f"p{i}" for i in range(8)]
    tasks = [f"t{j}" for j in range(16)]
    rows = []
    for model in MODELS:
        for condition_index, condition in enumerate(CONDITIONS):
            for persona in personas:
                for task_index, task in enumerate(tasks):
                    rely = (task_index + condition_index) % 2 == 0
                    rows.append(_row(persona, model, task, condition, rely))
    return rows


def test_known_signal_beats_all_baselines_and_ci_excludes_zero(tmp_path):
    result = analyze_confirmatory_axis1(
        _known_signal_responses(),
        _human_target(tmp_path / "human.json"),
        n_boot=200,
        n_perm=500,
        seed=7,
    )

    for model_result in result.to_dict()["per_model"].values():
        over = model_result["conflict_conditioned_overdispersion"]
        within = model_result["within_task_estimator"]
        corr = model_result["cross_condition_correspondence"]
        assert over["ci_lower"] > 0
        assert within["estimate"] > 0
        assert within["ci_lower"] > 0
        assert corr["spearman_rho"] > 0
        assert corr["spearman_p"] < 0.05
        for comparison in model_result["baseline_comparisons"].values():
            assert comparison["beaten"]


def test_null_is_fully_populated_and_does_not_beat_mean_predictor(tmp_path):
    result = analyze_confirmatory_axis1(
        _null_responses(),
        _human_target(tmp_path / "human.json"),
        n_boot=100,
        n_perm=200,
        seed=11,
    ).to_dict()

    assert result["exploratory_vs_confirmatory"] == "CONFIRMATORY"
    for model_result in result["per_model"].values():
        within = model_result["within_task_estimator"]
        assert within["ci_lower"] <= 0 <= within["ci_upper"]
        assert not model_result["baseline_comparisons"]["mean_predictor"]["beaten"]
        assert model_result["aligned_per_condition_table"]
        assert model_result["cross_condition_correspondence"]["shared_conditions"] == CONDITIONS


def test_mean_predictor_baseline_rho_is_zero(tmp_path):
    result = analyze_confirmatory_axis1(
        _known_signal_responses(),
        _human_target(tmp_path / "human.json"),
        n_boot=50,
        n_perm=100,
        seed=13,
    ).to_dict()

    for model_result in result["per_model"].values():
        assert model_result["baseline_comparisons"]["mean_predictor"]["value"] == pytest.approx(0.0)


def test_per_model_separation_no_pooling(tmp_path):
    result = analyze_confirmatory_axis1(
        _known_signal_responses({MODELS[0]: [0, 2, 4, 6, 10], MODELS[1]: [0, 0, 0, 0, 0]}),
        _human_target(tmp_path / "human.json"),
        n_boot=100,
        n_perm=200,
        seed=17,
    ).to_dict()

    assert set(result["per_model"]) == set(MODELS)
    strong = result["per_model"][MODELS[0]]["within_task_estimator"]["estimate"]
    weak = result["per_model"][MODELS[1]]["within_task_estimator"]["estimate"]
    assert strong > weak
    assert result["n"]["models"] == 2


def test_bh_adjusted_pvalues_are_reported_and_not_smaller_than_raw(tmp_path):
    result = analyze_confirmatory_axis1(
        _known_signal_responses(),
        _human_target(tmp_path / "human.json"),
        n_boot=50,
        n_perm=200,
        seed=19,
    ).to_dict()

    for model_result in result["per_model"].values():
        assert model_result["bh_adjusted_pvalues"]
        for item in model_result["bh_adjusted_pvalues"].values():
            assert item["adjusted_p"] >= item["raw_p"]


def test_determinism_same_inputs_same_json(tmp_path):
    responses = _known_signal_responses()
    target = _human_target(tmp_path / "human.json")
    first = analyze_confirmatory_axis1(responses, target, n_boot=80, n_perm=150, seed=23).to_dict()
    second = analyze_confirmatory_axis1(responses, target, n_boot=80, n_perm=150, seed=23).to_dict()
    assert first == second
    json.dumps(first, sort_keys=True)


class MockProvider(ModelProvider):
    def __init__(self, name="mock-model"):
        self.name = name
        self.calls = []

    def generate(self, prompt: str, *, seed: int, max_tokens: int, temperature: float) -> str:
        self.calls.append(prompt)
        if "WITHOUT any AI assistance" in prompt:
            decision = 0
        elif "Conf.+Adaptive (Expert)" in prompt or "Expert highlights" in prompt:
            decision = 1
        else:
            decision = 0
        return json.dumps({"decision": decision, "confidence": 0.8, "reasoning": "mock"})

    def generate_messages(self, messages, *, seed: int, max_tokens: int, temperature: float) -> str:
        return self.generate("\n".join(m["content"] for m in messages), seed=seed, max_tokens=max_tokens, temperature=temperature)


def test_mock_provider_runner_end_to_end_smoke(monkeypatch, tmp_path):
    from twdf.experiments import confirmatory_axis1 as runner

    tasks = [
        TaskStimulus(
            task_id=f"t{i}",
            domain="beer",
            text=f"Task {i}",
            ground_truth=1,
            ai_pred=1,
            ai_conf=0.9,
            expert_explanation="expert",
            system_highlights="<span class=class1>good</span>",
            expert_highlights_html="<span class='class1'>good expert</span>",
            testid=str(i),
        )
        for i in range(3)
    ]
    monkeypatch.setattr(runner, "build_tasks", lambda config: tasks)
    config = {
        "ui_conditions": ["Conf.", "Conf.+Adaptive (Expert)"],
        "models": ["mock-a", "mock-b"],
        "personas": [
            {"persona_id": "p1", "domain_skill": 0.5, "ai_literacy": 0.5, "risk_sensitivity": 0.5, "caution": 0.5, "temperature": 0.1, "prior_mix": 0.5},
            {"persona_id": "p2", "domain_skill": 0.5, "ai_literacy": 0.5, "risk_sensitivity": 0.5, "caution": 0.5, "temperature": 0.1, "prior_mix": 0.5},
        ],
        "seeds": [42],
        "human_overdispersion_path": str(_human_target(tmp_path / "human.json", [0.0, 0.4])),
        "analysis": {"seed": 5, "n_boot": 20, "n_perm": 50},
    }
    config_path = tmp_path / "config.yaml"
    import yaml
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    result = run_confirmatory_axis1(
        config_path,
        providers=[MockProvider("mock-a"), MockProvider("mock-b")],
    ).to_dict()

    assert result["n"]["responses"] == 2 * 2 * 3 * 2
    assert set(result["per_model"]) == {"mock-a", "mock-b"}
    for model_result in result["per_model"].values():
        assert model_result["cross_condition_correspondence"]["degenerate"]
