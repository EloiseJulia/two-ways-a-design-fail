import json
from pathlib import Path

import pytest
import yaml

from twdf.data.bansal_tasks import TaskStimulus
from twdf.experiments import axis2_powered, confirmatory_axis1
from twdf.panel.azure_provider import AzureFoundryProvider
from twdf.panel.provider import GitHubModelsProvider


def _task(task_id: str = "t0") -> TaskStimulus:
    return TaskStimulus(
        task_id=task_id,
        domain="beer",
        text=f"Beer review {task_id}: clean malt aroma.",
        ground_truth=1,
        ai_pred=1,
        ai_conf=0.9,
        expert_explanation="clean malt",
        system_highlights="<span class=class1>clean</span>",
        expert_highlights_html="<span class='class1'>clean malt</span>",
        testid=task_id,
    )


def _persona() -> dict:
    return {
        "persona_id": "p1",
        "domain_skill": 0.5,
        "ai_literacy": 0.5,
        "risk_sensitivity": 0.5,
        "caution": 0.5,
        "temperature": 0.2,
        "prior_mix": 0.5,
    }


def _azure_env(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_KEY", "unit-test-key")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)


def _mock_post(monkeypatch, payloads: list[dict]):
    class Response:
        status_code = 200
        headers = {}
        text = "OK"

        def json(self):
            return {"choices": [{"message": {"content": json.dumps({"decision": 1, "confidence": 0.8, "reasoning": "mock"})}}]}

    def fake_post(url, *, headers, json, timeout):
        payloads.append(json)
        assert "example.openai.azure.com" in url
        return Response()

    monkeypatch.setattr("twdf.panel.azure_provider.requests.post", fake_post)


def test_confirmatory_runner_builds_azure_provider_and_collects_offline(monkeypatch, tmp_path):
    _azure_env(monkeypatch)
    payloads: list[dict] = []
    _mock_post(monkeypatch, payloads)
    monkeypatch.setattr(confirmatory_axis1, "build_tasks", lambda config: [_task()])

    config = {
        "models": ["gpt-5.2", "gpt-5.4"],
        "ui_conditions": ["Conf."],
        "personas": [_persona()],
        "seeds": [42],
        "mode": "static",
        "cache_dir": str(tmp_path),
        "provider": {
            "type": "azure",
            "api_style": "azure_openai",
            "call_budget": 20,
            "inter_call_sleep": 0,
            "token_param": "max_completion_tokens",
            "omit_temperature": True,
        },
    }

    provider = confirmatory_axis1.build_provider(config, "gpt-5.2")
    assert isinstance(provider, AzureFoundryProvider)
    assert provider.name == "gpt-5.2"

    responses = confirmatory_axis1.collect_panel_responses(config)
    assert {r.model for r in responses} == {"gpt-5.2", "gpt-5.4"}
    assert payloads
    assert all("max_completion_tokens" in payload for payload in payloads)
    assert all("max_tokens" not in payload for payload in payloads)
    assert all("temperature" not in payload for payload in payloads)


def test_axis2_runner_builds_azure_provider_and_collects_offline(monkeypatch, tmp_path):
    _azure_env(monkeypatch)
    payloads: list[dict] = []
    _mock_post(monkeypatch, payloads)
    monkeypatch.setattr(axis2_powered, "select_hard_items", lambda criteria: {"t0": _task()})

    config = {
        "models": [{"name": "gpt-5.2"}, {"name": "gpt-5.4"}],
        "ui_conditions": ["Wrong-AI-GT (dark)"],
        "item_selection": {"n_items": 1, "prefer_ai_wrong": 0.5, "prefer_low_conf": 0.3, "prefer_high_variance": 0.2, "seed": 2024},
        "personas": [_persona()],
        "seeds": [42],
        "mode": "static",
        "cache_dir": str(tmp_path),
        "provider": {"type": "azure", "api_style": "azure_openai", "call_budget": 20, "inter_call_sleep": 0},
    }

    provider = axis2_powered.build_provider(config, "gpt-5.4")
    assert isinstance(provider, AzureFoundryProvider)
    assert provider.name == "gpt-5.4"

    responses = axis2_powered.collect_panel_responses(config)
    assert {r.model for r in responses} == {"gpt-5.2", "gpt-5.4"}


def test_default_provider_path_remains_github(monkeypatch, tmp_path):
    monkeypatch.setenv("GH_MODELS_TOKEN", "unit-test-token")
    config = {
        "models": ["openai/gpt-4o"],
        "cache_dir": str(tmp_path),
        "provider": {"call_budget": 1, "inter_call_sleep": 0},
    }

    provider = confirmatory_axis1.build_provider(config, "openai/gpt-4o")
    assert isinstance(provider, GitHubModelsProvider)
    assert provider.name == "openai/gpt-4o"


def test_azure_gpt5_configs_parse_and_match_primary_seeds_outputs():
    primary_axis1 = yaml.safe_load(Path("configs/confirmatory_axis1.yaml").read_text(encoding="utf-8"))
    azure_axis1 = yaml.safe_load(Path("configs/confirmatory_axis1_azure_gpt5.yaml").read_text(encoding="utf-8"))
    primary_axis2 = yaml.safe_load(Path("configs/axis2_powered.yaml").read_text(encoding="utf-8"))
    azure_axis2 = yaml.safe_load(Path("configs/axis2_powered_azure_gpt5.yaml").read_text(encoding="utf-8"))

    assert azure_axis1["models"] == ["gpt-5.2", "gpt-5.4"]
    assert azure_axis1["provider"]["type"] == "azure"
    assert azure_axis1["output_file"] == "results/confirmatory_axis1_gpt5.json"
    assert azure_axis1["output_file"] != primary_axis1["output_file"]
    assert azure_axis1["item_selection"]["seed"] == primary_axis1["item_selection"]["seed"] == 42

    assert [m["name"] for m in azure_axis2["models"]] == ["gpt-5.2", "gpt-5.4"]
    assert azure_axis2["provider"]["type"] == "azure"
    assert azure_axis2["output_file"] == "results/axis2_powered_gpt5.json"
    assert azure_axis2["output_file"] != primary_axis2["output_file"]
    assert azure_axis2["item_selection"]["seed"] == primary_axis2["item_selection"]["seed"] == 2024


def test_azure_token_param_and_temperature_options_thread_to_payload(monkeypatch, tmp_path):
    _azure_env(monkeypatch)
    provider = AzureFoundryProvider(
        deployment="gpt-5.2",
        cache_dir=tmp_path,
        token_param="max_completion_tokens",
        omit_temperature=True,
    )
    payload = provider._build_payload([{"role": "user", "content": "hi"}], 0.7, 123, 42)
    assert payload["max_completion_tokens"] == 123
    assert "max_tokens" not in payload
    assert "temperature" not in payload
