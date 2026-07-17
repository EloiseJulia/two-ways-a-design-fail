"""Shared provider construction for experiment runners."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from twdf.panel.azure_provider import AzureFoundryProvider
from twdf.panel.provider import GitHubModelsProvider, ModelProvider


def model_names_from_config(config: dict[str, Any]) -> list[str]:
    models = config.get("models")
    if models is None and "model" in config:
        models = [config["model"]]
    names = [m["name"] if isinstance(m, dict) else str(m) for m in (models or [])]
    if not names:
        raise ValueError("config requires at least one model")
    return names


def build_provider_from_config(config: dict[str, Any], model_name: str) -> ModelProvider:
    """Build the configured provider; absent provider.type preserves GitHub Models."""
    provider_cfg = dict(config.get("provider", {}) or {})
    runtime_cfg = dict(config.get("model_runtime", {}) or {})
    runtime_cfg.update(provider_cfg)

    provider_type = str(provider_cfg.get("type", "github")).lower()
    cache_dir = Path(config.get("cache_dir", runtime_cfg.get("cache_dir", "data/cache/panel")))
    call_budget = int(runtime_cfg.get("call_budget", config.get("call_budget", 450)))
    inter_call_sleep = float(runtime_cfg.get("inter_call_sleep", config.get("inter_call_sleep", 0.8)))
    max_retries = int(runtime_cfg.get("max_retries", config.get("max_retries", 5)))

    if provider_type in {"github", "github_models", "githubmodels"}:
        return GitHubModelsProvider(
            model_name=model_name,
            cache_dir=cache_dir,
            call_budget=call_budget,
            inter_call_sleep=inter_call_sleep,
            max_retries=max_retries,
        )

    if provider_type in {"azure", "azure_foundry", "azure_openai", "foundry"}:
        api_style = str(provider_cfg.get("api_style", "azure_openai"))
        if provider_type == "foundry" and "api_style" not in provider_cfg:
            api_style = "foundry"
        return AzureFoundryProvider(
            deployment=model_name,
            api_style=api_style,
            cache_dir=cache_dir,
            call_budget=call_budget,
            inter_call_sleep=inter_call_sleep,
            max_retries=max_retries,
            foundry_path=str(provider_cfg.get("foundry_path", "/chat/completions")),
            token_param=str(provider_cfg.get("token_param", "max_tokens")),
            omit_temperature=bool(provider_cfg.get("omit_temperature", False)),
        )

    raise ValueError(f"Unsupported provider.type: {provider_type}")
