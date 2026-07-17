"""Offline tests for the OpenAI-compatible proxy provider."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from twdf.experiments.provider_factory import build_provider_from_config
from twdf.panel.openai_compat_provider import OpenAICompatibleProvider


class FakeResponse:
    def __init__(self, status_code=200, content="ok", finish_reason="stop"):
        self.status_code = status_code
        self.headers = {}
        self.text = "fake response text"
        self._json = {
            "choices": [
                {"message": {"content": content}, "finish_reason": finish_reason}
            ]
        }

    def json(self):
        return self._json


def make_provider(tmp_path, **kwargs):
    return OpenAICompatibleProvider(
        model_name=kwargs.pop("model_name", "gpt-4o"),
        cache_dir=tmp_path,
        inter_call_sleep=0,
        **kwargs,
    )


def test_default_url_and_model_in_body(monkeypatch, tmp_path):
    monkeypatch.delenv("COPILOT_PROXY_ENDPOINT", raising=False)
    monkeypatch.delenv("COPILOT_PROXY_KEY", raising=False)
    post = Mock(return_value=FakeResponse(content="hello"))
    monkeypatch.setattr("twdf.panel.openai_compat_provider.requests.post", post)

    provider = make_provider(tmp_path, model_name="gpt-4.1")
    assert provider._build_url() == "http://127.0.0.1:8787/v1/chat/completions"
    assert "Authorization" not in provider._build_headers()

    assert provider.generate("hi", seed=7, max_tokens=123, temperature=0.2) == "hello"
    payload = post.call_args.kwargs["json"]
    assert payload["model"] == "gpt-4.1"
    assert payload["max_tokens"] == 123


def test_env_base_url_override_and_optional_auth(monkeypatch, tmp_path):
    monkeypatch.setenv("COPILOT_PROXY_ENDPOINT", "http://proxy.test/v1/")
    monkeypatch.setenv("COPILOT_PROXY_KEY", "secret-token")

    provider = make_provider(tmp_path)
    assert provider._build_url() == "http://proxy.test/v1/chat/completions"
    headers = provider._build_headers()
    assert headers["Content-Type"] == "application/json"
    assert headers["Authorization"] == "Bearer secret-token"


def test_token_param_routing_and_omit_temperature(tmp_path):
    messages = [{"role": "user", "content": "hi"}]
    standard = make_provider(tmp_path / "standard", token_param="max_tokens")
    reasoning = make_provider(
        tmp_path / "reasoning",
        token_param="max_completion_tokens",
        omit_temperature=True,
        min_completion_tokens=4096,
    )

    standard_payload = standard._build_payload(messages, 0.7, 600, 42)
    assert standard_payload["max_tokens"] == 600
    assert "max_completion_tokens" not in standard_payload
    assert standard_payload["temperature"] == 0.7

    reasoning_payload = reasoning._build_payload(messages, 0.7, 600, 42)
    assert reasoning_payload["max_completion_tokens"] == 4096
    assert "max_tokens" not in reasoning_payload
    assert "temperature" not in reasoning_payload


def test_min_completion_tokens_not_in_cache_key(tmp_path):
    messages = [{"role": "user", "content": "hi"}]
    small_floor = make_provider(
        tmp_path / "a",
        token_param="max_completion_tokens",
        min_completion_tokens=1000,
    )
    large_floor = make_provider(
        tmp_path / "b",
        token_param="max_completion_tokens",
        min_completion_tokens=4096,
    )

    assert small_floor._build_payload(messages, 0.1, 600, 1)["max_completion_tokens"] == 1000
    assert large_floor._build_payload(messages, 0.1, 600, 1)["max_completion_tokens"] == 4096
    assert small_floor._compute_cache_key(messages, 0.1, 600, 1) == large_floor._compute_cache_key(messages, 0.1, 600, 1)


def test_empty_content_retries_raises_and_does_not_cache(monkeypatch, tmp_path):
    monkeypatch.setattr("twdf.panel.openai_compat_provider.time.sleep", lambda _seconds: None)
    post = Mock(return_value=FakeResponse(content="   ", finish_reason="length"))
    monkeypatch.setattr("twdf.panel.openai_compat_provider.requests.post", post)

    provider = make_provider(tmp_path, model_name="gpt-5.5", max_retries=2)
    with pytest.raises(RuntimeError, match="Empty content.*gpt-5.5.*finish_reason=length"):
        provider.generate("hi", seed=1, max_tokens=100, temperature=0.2)

    assert post.call_count == 2
    assert list(Path(tmp_path).glob("*.json")) == []


def test_deterministic_cache_hit_avoids_second_http_call(monkeypatch, tmp_path):
    post = Mock(return_value=FakeResponse(content="cached answer"))
    monkeypatch.setattr("twdf.panel.openai_compat_provider.requests.post", post)

    provider = make_provider(tmp_path)
    kwargs = {"seed": 3, "max_tokens": 50, "temperature": 0.4}
    assert provider.generate("hello", **kwargs) == "cached answer"
    assert provider.generate("hello", **kwargs) == "cached answer"

    assert post.call_count == 1
    assert provider.api_calls == 1
    assert provider.cache_hits == 1


@pytest.mark.parametrize("provider_type", ["openai_compatible", "copilot_proxy", "proxy", "ghc"])
def test_provider_factory_builds_aliases(tmp_path, provider_type):
    config = {
        "models": [{"name": "gpt-5.5"}],
        "cache_dir": str(tmp_path),
        "provider": {
            "type": provider_type,
            "base_url": "http://proxy.test/v1",
            "call_budget": 9,
            "inter_call_sleep": 0,
            "max_retries": 2,
            "token_param": "max_completion_tokens",
            "omit_temperature": True,
            "min_completion_tokens": 4096,
        },
    }

    provider = build_provider_from_config(config, "gpt-5.5")
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.name == "gpt-5.5"
    assert provider.base_url == "http://proxy.test/v1"
    assert provider.token_param == "max_completion_tokens"
    assert provider.omit_temperature is True
    assert provider.min_completion_tokens == 4096


def test_provider_factory_per_model_overrides(tmp_path):
    config = {
        "models": [
            {"name": "gpt-5.5", "provider": {"token_param": "max_completion_tokens", "omit_temperature": True, "min_completion_tokens": 4096}},
            {"name": "claude-sonnet-4.5", "provider": {"token_param": "max_tokens", "omit_temperature": False}},
        ],
        "cache_dir": str(tmp_path),
        "provider": {"type": "ghc", "base_url": "http://proxy.test/v1", "inter_call_sleep": 0},
    }

    gpt = build_provider_from_config(config, "gpt-5.5")
    claude = build_provider_from_config(config, "claude-sonnet-4.5")
    assert gpt.token_param == "max_completion_tokens"
    assert gpt.omit_temperature is True
    assert gpt.min_completion_tokens == 4096
    assert claude.token_param == "max_tokens"
    assert claude.omit_temperature is False
