"""
Powered axis-2 experiment runner.

Build-only/offline-safe implementation for the preregistered later run:
multi-model panel, clean guaranteed-wrong "Wrong-AI-GT (dark)" condition, and
E4-style compliance-floor analysis.

Usage:
    python -m twdf.experiments.axis2_powered --config configs/axis2_powered.yaml
"""

import argparse
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np
import yaml
from scipy import stats

from twdf.data.item_selector import ItemSelectionCriteria, select_hard_items
from twdf.experiments.provider_factory import build_provider_from_config, model_names_from_config
from twdf.metrics.overdispersion import conflict_conditioned_reliance, over_reliance_level
from twdf.panel.provider import ModelProvider
from twdf.panel.real_panel import run_panel
from twdf.panel.stub import AgentResponse, Persona


CONFIRMATORY_LABEL = "CONFIRMATORY-PENDING-PREREG"


def _hash_seed(label: str, seed: int) -> int:
    digest = hashlib.sha256(f"{label}:{seed}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % (2**31)


def _personas_from_config(config: dict) -> list[Persona]:
    return [
        Persona(
            persona_id=p["persona_id"],
            domain_skill=p["domain_skill"],
            ai_literacy=p["ai_literacy"],
            risk_sensitivity=p["risk_sensitivity"],
            caution=p["caution"],
            temperature=p["temperature"],
            prior_mix=p["prior_mix"],
        )
        for p in config["personas"]
    ]


def _model_names(config: dict) -> list[str]:
    return model_names_from_config(config)


def build_provider(config: dict, model_name: str) -> ModelProvider:
    return build_provider_from_config(config, model_name)


def _per_persona_adoption(responses: Iterable[AgentResponse]) -> dict[str, float]:
    by_persona: dict[str, list[float]] = {}
    for r in responses:
        by_persona.setdefault(r.persona_id, []).append(float(str(r.final_decision) == str(r.trace["ai_advice"])))
    return {pid: float(np.mean(vals)) for pid, vals in by_persona.items()}


def _per_persona_placebo_floor(responses: Iterable[AgentResponse]) -> dict[str, float]:
    by_persona: dict[str, list[float]] = {}
    for r in responses:
        system1 = str(r.system1_decision)
        ai_advice = str(r.trace.get("ai_advice", ""))
        if system1 != ai_advice:
            by_persona.setdefault(r.persona_id, []).append(float(str(r.final_decision) == ai_advice))
    return {pid: float(np.mean(vals)) for pid, vals in by_persona.items()}


def _bootstrap_ci(values: list[float], *, seed: int, n: int = 10000) -> dict:
    if not values:
        return {"estimate": 0.0, "ci_lower": 0.0, "ci_upper": 0.0, "se": 0.0, "n": 0}
    arr = np.asarray(values, dtype=float)
    rng = np.random.RandomState(_hash_seed("axis2-bootstrap", seed))
    stats_ = []
    for _ in range(n):
        stats_.append(float(np.mean(rng.choice(arr, size=len(arr), replace=True))))
    boot = np.asarray(stats_)
    return {
        "estimate": float(np.mean(arr)),
        "ci_lower": float(np.percentile(boot, 2.5)),
        "ci_upper": float(np.percentile(boot, 97.5)),
        "se": float(np.std(boot, ddof=1)) if len(boot) > 1 else 0.0,
        "n": int(len(arr)),
    }


def adoption_exceeds_placebo_test(
    wrong_responses: list[AgentResponse],
    placebo_responses: list[AgentResponse],
    *,
    seed: int = 2024,
    n_permutations: int = 10000,
    n_bootstrap: int = 10000,
) -> dict:
    """One-sided sign-flip permutation/bootstrap: wrong-AI adoption > placebo floor."""
    wrong = _per_persona_adoption(wrong_responses)
    placebo = _per_persona_placebo_floor(placebo_responses)
    personas = sorted(set(wrong) | set(placebo))
    diffs = [wrong.get(pid, 0.0) - placebo.get(pid, 0.0) for pid in personas]
    observed = float(np.mean(diffs)) if diffs else 0.0

    rng = np.random.RandomState(_hash_seed("axis2-permutation", seed))
    diffs_arr = np.asarray(diffs, dtype=float)
    perm_stats = []
    for _ in range(n_permutations):
        signs = np.where(rng.rand(len(diffs_arr)) < 0.5, -1.0, 1.0)
        perm_stats.append(float(np.mean(diffs_arr * signs)) if len(diffs_arr) else 0.0)
    pvalue = float(np.mean(np.asarray(perm_stats) >= observed)) if perm_stats else 1.0

    ci = _bootstrap_ci(diffs, seed=seed, n=n_bootstrap)
    return {
        "observed_diff": observed,
        "pvalue_one_sided": pvalue,
        "n_permutations": n_permutations,
        "bootstrap_ci": ci,
        "per_persona_diff": {pid: wrong.get(pid, 0.0) - placebo.get(pid, 0.0) for pid in personas},
    }


def binomial_vs_half(wrong_responses: list[AgentResponse]) -> dict:
    adopted = [str(r.final_decision) == str(r.trace["ai_advice"]) for r in wrong_responses]
    k = int(sum(adopted))
    n = len(adopted)
    p = float(stats.binomtest(k, n, 0.5, alternative="greater").pvalue) if n else 1.0
    return {"k_adopted": k, "n": n, "rate": (k / n if n else 0.0), "pvalue_greater_than_0_5": p}


def analyze_axis2(responses: list[AgentResponse], ui_conditions: tuple[str, ...]) -> dict:
    control_cond, placebo_cond, faithful_cond, dark_cond = ui_conditions
    by_cond = {cond: [r for r in responses if r.ui_condition == cond] for cond in ui_conditions}
    placebo = conflict_conditioned_reliance(by_cond[placebo_cond])
    dark = over_reliance_level(by_cond[dark_cond])
    significance = adoption_exceeds_placebo_test(by_cond[dark_cond], by_cond[placebo_cond])
    binom = binomial_vs_half(by_cond[dark_cond])

    return {
        "conditions": {
            "control": control_cond,
            "faithful": faithful_cond,
            "placebo": placebo_cond,
            "dark": dark_cond,
        },
        "placebo_floor": {
            "conflict_reliance": placebo.reliance_rate,
            "unconditional_reliance": placebo.unconditional_reliance,
            "n_conflict": placebo.n_conflict,
            "n_total": placebo.n_total,
            "conflict_fraction": placebo.conflict_fraction,
        },
        "axis2_over_reliance": {
            "raw_over_reliance_level": dark.over_reliance_level,
            "over_reliance_on_wrong": dark.over_reliance_on_wrong,
            "n_truly_wrong": dark.n_truly_wrong,
            "clean_equals_raw": abs(dark.over_reliance_level - dark.over_reliance_on_wrong) < 1e-12,
            "compliance_adjusted_level": dark.over_reliance_level - placebo.reliance_rate,
            "between_persona_spread": dark.between_persona_spread,
            "n_trials": dark.n_trials,
            "per_persona_adoption": dark.per_persona_adoption,
        },
        "significance": {
            "adoption_exceeds_placebo_floor": significance,
            "binomial_vs_0_5": binom,
        },
    }


def collect_panel_responses(
    config: dict,
    *,
    providers: Iterable[ModelProvider] | None = None,
) -> list[AgentResponse]:
    personas = _personas_from_config(config)
    criteria = ItemSelectionCriteria(**config["item_selection"])
    tasks = select_hard_items(criteria=criteria)
    ui_conditions = tuple(config["ui_conditions"])

    all_responses: list[AgentResponse] = []
    provider_list = list(providers) if providers is not None else [build_provider(config, model) for model in _model_names(config)]
    for provider in provider_list:
        responses = run_panel(
            personas=personas,
            tasks=list(tasks.values()),
            ui_pair=ui_conditions,
            providers=[provider],
            seeds=config["seeds"],
            mode=config["mode"],
        )
        all_responses.extend(responses)
    return all_responses


def _serialize_response(r: AgentResponse) -> dict:
    return {
        "persona_id": r.persona_id,
        "model": r.model,
        "task_id": r.task_id,
        "ui_condition": r.ui_condition,
        "seed": r.seed,
        "system1_decision": r.system1_decision,
        "final_decision": r.final_decision,
        "relied": r.relied,
        "confidence": r.confidence,
        "trace": r.trace,
        "trust_state": r.trust_state,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Powered clean axis-2 experiment")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    personas = _personas_from_config(config)
    criteria = ItemSelectionCriteria(**config["item_selection"])
    tasks = select_hard_items(criteria=criteria)
    ui_conditions = tuple(config["ui_conditions"])

    all_responses: list[AgentResponse] = []
    per_model_results = {}
    provider_stats_by_model = {}
    start = time.time()
    for model_name in _model_names(config):
        provider = build_provider(config, model_name)
        responses = run_panel(
            personas=personas,
            tasks=list(tasks.values()),
            ui_pair=ui_conditions,
            providers=[provider],
            seeds=config["seeds"],
            mode=config["mode"],
        )
        all_responses.extend(responses)
        per_model_results[model_name] = analyze_axis2(responses, ui_conditions)
        provider_stats_by_model[model_name] = provider.get_stats() if hasattr(provider, "get_stats") else {}

    wall_time = time.time() - start
    panel_results = analyze_axis2(all_responses, ui_conditions)

    results = {
        "run_manifest": {
            "experiment_name": config["experiment_name"],
            "exploratory_vs_confirmatory": CONFIRMATORY_LABEL,
            "config_hash": config_hash,
            "config_file": args.config,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "wall_time_seconds": wall_time,
            "domain": config["domain"],
            "n_personas": len(personas),
            "n_tasks": len(tasks),
            "n_models": len(_model_names(config)),
            "models": _model_names(config),
            "n_responses": len(all_responses),
            "ui_conditions": list(ui_conditions),
            "seeds": config["seeds"],
            "item_seed": config["item_selection"]["seed"],
            "provider_stats_by_model": provider_stats_by_model,
        },
        "per_model": per_model_results,
        "panel": panel_results,
        "responses": [_serialize_response(r) for r in all_responses],
    }

    output_file = Path(config["output_file"])
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Saved {output_file}")
    print(f"Label: {CONFIRMATORY_LABEL}")


if __name__ == "__main__":
    main()
