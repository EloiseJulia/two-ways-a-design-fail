"""Offline tests for the powered clean axis-2 condition and experiment."""

import re
from pathlib import Path

import numpy as np
import yaml

from twdf.data.bansal_tasks import TaskStimulus, displayed_ai_advice, render_ui_condition
from twdf.experiments.axis2_powered import (
    CONFIRMATORY_LABEL,
    adoption_exceeds_placebo_test,
    analyze_axis2,
    binomial_vs_half,
)
from twdf.metrics.overdispersion import over_reliance_level
from twdf.panel.provider import ModelProvider
from twdf.panel.real_panel import run_panel
from twdf.panel.stub import AgentResponse, Persona


def _persona() -> Persona:
    return Persona(
        persona_id="p1",
        domain_skill=0.5,
        ai_literacy=0.5,
        risk_sensitivity=0.5,
        caution=0.5,
        temperature=0.5,
        prior_mix=0.5,
    )


def _task(task_id: str, *, ground_truth: int, ai_pred: int = 1) -> TaskStimulus:
    return TaskStimulus(
        task_id=task_id,
        domain="beer",
        text=f"Beer review {task_id}: clean malt aroma.",
        ground_truth=ground_truth,
        ai_pred=ai_pred,
        ai_conf=0.87,
        expert_explanation="clean malt aroma",
        system_highlights="<span class=class1>clean</span>",
        expert_highlights_html="Beer has <span class='class1'>clean malt aroma</span>.",
        testid=task_id,
    )


class RecommendationProvider(ModelProvider):
    name = "recommendation-provider"

    def __init__(self, *, follow: bool):
        self.follow = follow
        self.calls: list[str] = []

    def generate(self, prompt: str, *, seed: int, max_tokens: int, temperature: float) -> str:
        self.calls.append(prompt)
        match = re.search(r"(?:AI Expert System Recommendation|AI Prediction):\s*(\d)", prompt)
        if match:
            shown = int(match.group(1))
            decision = shown if self.follow else 1 - shown
        else:
            decision = 0
        return f'{{"decision": {decision}, "confidence": 0.90, "reasoning": "mock"}}'

    def generate_messages(self, messages: list[dict], *, seed: int, max_tokens: int, temperature: float) -> str:
        return self.generate(" ".join(m["content"] for m in messages), seed=seed, max_tokens=max_tokens, temperature=temperature)


def test_wrong_ai_gt_renders_coercive_and_tracks_ground_truth_not_pred():
    t_gt0 = _task("a", ground_truth=0, ai_pred=1)
    t_gt1 = _task("b", ground_truth=1, ai_pred=1)

    ui0 = render_ui_condition(t_gt0, "Wrong-AI-GT (dark)")
    ui1 = render_ui_condition(t_gt1, "Wrong-AI-GT (dark)")

    assert "CRITICAL DECISION" in ui0
    assert "held accountable" in ui0
    assert displayed_ai_advice(t_gt0, "Wrong-AI-GT (dark)") == 1
    assert displayed_ai_advice(t_gt1, "Wrong-AI-GT (dark)") == 0
    assert re.search(r"Recommendation:\s*1", ui0)
    assert re.search(r"Recommendation:\s*0", ui1)
    assert ui0 != ui1


def test_displayed_ai_advice_single_source_matches_rendered_recommendation():
    task = _task("c", ground_truth=1, ai_pred=1)
    shown = displayed_ai_advice(task, "Wrong-AI-GT (dark)")
    rendered = render_ui_condition(task, "Wrong-AI-GT (dark)")
    rec = int(re.search(r"Recommendation:\s*(\d)", rendered).group(1))
    assert shown == 1 - task.ground_truth
    assert rec == shown


def test_run_panel_wrong_ai_gt_compliance_and_refusal_metrics():
    personas = [_persona()]
    tasks = [_task("0", ground_truth=0, ai_pred=1), _task("1", ground_truth=1, ai_pred=1)]
    ui_conditions = ("Wrong-AI-GT (dark)",)

    comply = run_panel(personas, tasks, ui_conditions, [RecommendationProvider(follow=True)], seeds=[42])
    comply_metric = over_reliance_level(comply)
    assert comply_metric.over_reliance_level == 1.0
    assert comply_metric.over_reliance_on_wrong == comply_metric.over_reliance_level
    assert comply_metric.n_truly_wrong == len(comply)
    assert all(r.trace["ai_correct"] is False for r in comply)
    assert all(int(r.trace["ai_advice"]) == 1 - next(t.ground_truth for t in tasks if t.task_id == r.task_id) for r in comply)

    refuse = run_panel(personas, tasks, ui_conditions, [RecommendationProvider(follow=False)], seeds=[42])
    refuse_metric = over_reliance_level(refuse)
    assert refuse_metric.over_reliance_level == 0.0
    assert all(r.trace["ai_correct"] is False for r in refuse)


def test_wrong_ai_gt_prompt_has_no_ground_truth_leakage():
    provider = RecommendationProvider(follow=True)
    responses = run_panel([_persona()], [_task("0", ground_truth=1, ai_pred=1)], ("Wrong-AI-GT (dark)",), [provider], seeds=[42])
    dark_prompt = responses[0].trace["prompt"].lower()
    rendered_only = render_ui_condition(_task("0", ground_truth=1, ai_pred=1), "Wrong-AI-GT (dark)").lower()

    for forbidden in ["ground_truth", "ground truth", "truth", "correct answer", "derived from"]:
        assert forbidden not in dark_prompt
        assert forbidden not in rendered_only
    assert "recommendation: 0" in dark_prompt
    assert responses[0].trace["ai_correct"] is False


def test_system1_frozen_across_axis2_powered_conditions():
    personas = [_persona()]
    tasks = [_task("0", ground_truth=0, ai_pred=1), _task("1", ground_truth=1, ai_pred=0)]
    conditions = ("Conf.", "Conf.+Placebo", "Conf.+Adaptive (Expert)", "Wrong-AI-GT (dark)")
    responses = run_panel(personas, tasks, conditions, [RecommendationProvider(follow=True)], seeds=[42])

    for task in tasks:
        values = {r.system1_decision for r in responses if r.task_id == task.task_id}
        assert len(values) == 1
    assert len(responses) == len(personas) * len(tasks) * len(conditions)


def test_axis2_powered_stats_helpers_deterministic():
    wrong = [
        AgentResponse("p1", "m", "t1", "Wrong-AI-GT (dark)", 42, 1, 0, True, 0.9, {"ai_advice": 0, "ground_truth": 1}, None),
        AgentResponse("p1", "m", "t2", "Wrong-AI-GT (dark)", 42, 0, 1, True, 0.9, {"ai_advice": 1, "ground_truth": 0}, None),
        AgentResponse("p2", "m", "t1", "Wrong-AI-GT (dark)", 42, 1, 1, False, 0.9, {"ai_advice": 0, "ground_truth": 1}, None),
        AgentResponse("p2", "m", "t2", "Wrong-AI-GT (dark)", 42, 0, 1, True, 0.9, {"ai_advice": 1, "ground_truth": 0}, None),
    ]
    placebo = [
        AgentResponse("p1", "m", "t1", "Conf.+Placebo", 42, 1, 1, False, 0.9, {"ai_advice": 0}, None),
        AgentResponse("p2", "m", "t1", "Conf.+Placebo", 42, 1, 0, True, 0.9, {"ai_advice": 0}, None),
    ]

    a = adoption_exceeds_placebo_test(wrong, placebo, seed=2024, n_permutations=200, n_bootstrap=200)
    b = adoption_exceeds_placebo_test(wrong, placebo, seed=2024, n_permutations=200, n_bootstrap=200)
    assert a == b
    assert a["observed_diff"] > 0
    binom = binomial_vs_half(wrong)
    assert binom["k_adopted"] == 3
    assert binom["n"] == 4


def test_axis2_powered_config_shape():
    config_path = Path("configs/axis2_powered.yaml")
    config = yaml.safe_load(config_path.read_text())
    assert config["exploratory_vs_confirmatory"] == CONFIRMATORY_LABEL
    assert config["ui_conditions"] == ["Conf.", "Conf.+Placebo", "Conf.+Adaptive (Expert)", "Wrong-AI-GT (dark)"]
    assert [m["name"] for m in config["models"]] == ["openai/gpt-4o", "openai/gpt-4.1-mini"]
    assert len(config["personas"]) == 6
    assert config["item_selection"]["n_items"] == 20
    assert config["item_selection"]["seed"] == 2024
