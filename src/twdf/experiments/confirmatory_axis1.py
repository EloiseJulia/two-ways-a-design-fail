
"""Thin runner for the BLIND confirmatory Axis-1 panel.

The analysis lives in :mod:`twdf.analysis.confirmatory_axis1`.  This module only
collects panel responses using the existing provider/run_panel loop and then
hands them to the pure analysis.  Tests exercise it with mock providers only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable, Iterable

import yaml

from twdf.analysis.confirmatory_axis1 import analyze_confirmatory_axis1
from twdf.data.item_selector import ItemSelectionCriteria, select_hard_items
from twdf.experiments.provider_factory import build_provider_from_config, model_names_from_config
from twdf.panel.provider import ModelProvider
from twdf.panel.real_panel import run_panel
from twdf.panel.stub import Persona


def load_config(config_path: str | Path) -> dict[str, Any]:
    with Path(config_path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_personas(config: dict[str, Any]) -> list[Persona]:
    return [
        Persona(
            persona_id=p["persona_id"],
            domain_skill=float(p["domain_skill"]),
            ai_literacy=float(p["ai_literacy"]),
            risk_sensitivity=float(p["risk_sensitivity"]),
            caution=float(p["caution"]),
            temperature=float(p["temperature"]),
            prior_mix=float(p["prior_mix"]),
        )
        for p in config.get("personas", [])
    ]


def build_tasks(config: dict[str, Any]) -> list[Any]:
    item_cfg = config.get("item_selection", {})
    criteria = ItemSelectionCriteria(
        n_items=int(config.get("n_items", item_cfg.get("n_items", 10))),
        prefer_ai_wrong=float(item_cfg.get("prefer_ai_wrong", 0.5)),
        prefer_low_conf=float(item_cfg.get("prefer_low_conf", 0.3)),
        prefer_high_variance=float(item_cfg.get("prefer_high_variance", 0.2)),
        seed=int(item_cfg.get("seed", config.get("seeds", [42])[0])),
    )
    return list(select_hard_items(criteria=criteria).values())


def build_provider(config: dict[str, Any], model_name: str) -> ModelProvider:
    return build_provider_from_config(config, model_name)


def collect_panel_responses(
    config: dict[str, Any],
    *,
    providers: Iterable[ModelProvider] | None = None,
    provider_factory: Callable[[str], ModelProvider] | None = None,
) -> list[Any]:
    personas = build_personas(config)
    tasks = build_tasks(config)
    ui_conditions = tuple(config["ui_conditions"])
    seeds = list(config.get("seeds", [42]))
    mode = config.get("mode", "static")

    if providers is None:
        factory = provider_factory or (lambda model: build_provider(config, model))
        providers = [factory(model) for model in model_names_from_config(config)]

    responses: list[Any] = []
    for provider in providers:
        responses.extend(
            run_panel(
                personas=personas,
                tasks=tasks,
                ui_pair=ui_conditions,
                providers=[provider],
                seeds=seeds,
                mode=mode,
            )
        )
    return responses


def run_confirmatory_axis1(
    config_path: str | Path,
    *,
    providers: Iterable[ModelProvider] | None = None,
    provider_factory: Callable[[str], ModelProvider] | None = None,
    responses: Iterable[Any] | None = None,
) -> Any:
    config = load_config(config_path)
    panel_responses = list(responses) if responses is not None else collect_panel_responses(
        config,
        providers=providers,
        provider_factory=provider_factory,
    )
    return analyze_confirmatory_axis1(
        panel_responses,
        config.get("human_overdispersion_path", "results/e1_multicond.json"),
        control_condition=config.get("control_condition", "Conf."),
        treatment_condition=config.get("treatment_condition", "Conf.+Adaptive (Expert)"),
        seed=int(config.get("analysis", {}).get("seed", config.get("seeds", [42])[0])),
        n_boot=int(config.get("analysis", {}).get("n_boot", 1000)),
        n_perm=int(config.get("analysis", {}).get("n_perm", 1000)),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Confirmatory Axis-1 H1a runner (do not run live during BLIND build)")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    result = run_confirmatory_axis1(args.config)
    output = args.output or load_config(args.config).get("output_file", "results/confirmatory_axis1.json")
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with Path(output).open("w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, sort_keys=True)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
