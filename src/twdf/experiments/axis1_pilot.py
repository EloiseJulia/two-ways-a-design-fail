"""
Axis-1 multi-family exploratory pilot experiment (E5).

EXPLORATORY ONLY — not confirmatory. Purpose:
1. De-risk the multi-family, 5-condition pipeline end-to-end
2. Produce power-analysis input (effect-size + variance estimates) for sizing a confirmatory run
3. MUST NOT be used to tune conditions, thresholds (τ), or model set

Multi-family panel design (SPEC §4.2):
- Run panel across MULTIPLE model families (config lists models)
- For each model: static counterfactual panel over all 5 Bansal AI conditions
- System-1 computed once per (persona, item, model, seed), FROZEN across all 5 conditions
- Panel = personas × models; compute disagreement per condition ACROSS personas×models

All outputs labeled EXPLORATORY / NON-CONFIRMATORY. Freeze NO thresholds.

Usage:
    python -m twdf.experiments.axis1_pilot --config configs/axis1_pilot.yaml
"""

import argparse
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

import yaml
import numpy as np

from twdf.panel.stub import Persona
from twdf.panel.provider import GitHubModelsProvider
from twdf.panel.real_panel import run_panel
from twdf.data.item_selector import ItemSelectionCriteria, select_hard_items
from twdf.data.bansal_tasks import TaskStimulus
from twdf.metrics.overdispersion import (
    betabinom_overdispersion_within_domain,
    condition_correlation,
    conflict_conditioned_reliance,
)


def compute_panel_disagreement_across_personas_models(
    responses: list,
    ui_condition: str
) -> dict:
    """
    Compute panel disagreement (variance in reliance) across FULL panel (personas × models).
    
    Args:
        responses: List of agent responses
        ui_condition: Which UI condition to analyze
    
    Returns:
        Dict with disagreement metrics (variance, per-persona-model reliance, etc.)
    """
    # Filter to this UI condition
    ui_responses = [r for r in responses if r.ui_condition == ui_condition]
    
    if not ui_responses:
        return {
            'disagreement': 0.0,
            'n_panel_members': 0,
            'panel_members': [],
            'per_member_reliance': {}
        }
    
    # Compute per (persona, model) reliance rate
    member_reliance = {}
    for resp in ui_responses:
        member_key = (resp.persona_id, resp.model)
        if member_key not in member_reliance:
            member_reliance[member_key] = []
        member_reliance[member_key].append(float(resp.relied))
    
    # Average reliance per panel member
    member_means = {k: np.mean(v) for k, v in member_reliance.items()}
    means_array = np.array(list(member_means.values()))
    
    # Disagreement = variance across panel members
    disagreement = float(np.var(means_array, ddof=1)) if len(means_array) > 1 else 0.0
    
    return {
        'disagreement': disagreement,
        'n_panel_members': len(member_means),
        'panel_members': [f"{p}_{m}" for (p, m) in member_means.keys()],
        'per_member_reliance': {f"{p}_{m}": v for (p, m), v in member_means.items()}
    }


def compute_cross_family_agreement(
    disagreement_by_model_condition: dict[tuple[str, str], float],
    models: list[str],
    conditions: list[str]
) -> dict:
    """
    Compute cross-family agreement: do different model families rank conditions similarly?
    
    SPEC §4.2: Only trust cross-family-consistent flags.
    
    Args:
        disagreement_by_model_condition: (model, condition) -> disagreement value
        models: List of model names
        conditions: List of UI condition names
    
    Returns:
        Dict with cross-family agreement metrics (rank correlations, etc.)
    """
    from scipy import stats as scipy_stats
    
    # Build per-model condition rankings
    model_rankings = {}
    for model in models:
        # Extract disagreement values for this model across conditions
        model_disagree = {}
        for cond in conditions:
            key = (model, cond)
            if key in disagreement_by_model_condition:
                model_disagree[cond] = disagreement_by_model_condition[key]
        
        if len(model_disagree) >= 2:
            # Rank conditions by disagreement (descending)
            sorted_conds = sorted(model_disagree.items(), key=lambda x: -x[1])
            model_rankings[model] = {c: rank for rank, (c, _) in enumerate(sorted_conds)}
    
    # Compute pairwise rank correlations between models
    pairwise_correlations = []
    model_pairs = []
    for i, m1 in enumerate(models):
        for j, m2 in enumerate(models):
            if i < j and m1 in model_rankings and m2 in model_rankings:
                # Get shared conditions
                shared = set(model_rankings[m1].keys()) & set(model_rankings[m2].keys())
                if len(shared) >= 2:
                    ranks1 = [model_rankings[m1][c] for c in sorted(shared)]
                    ranks2 = [model_rankings[m2][c] for c in sorted(shared)]
                    
                    # Spearman correlation
                    rho, pval = scipy_stats.spearmanr(ranks1, ranks2)
                    pairwise_correlations.append(rho)
                    model_pairs.append((m1, m2))
    
    return {
        'pairwise_rank_correlations': {
            f"{m1}_vs_{m2}": rho
            for (m1, m2), rho in zip(model_pairs, pairwise_correlations)
        },
        'mean_pairwise_correlation': float(np.mean(pairwise_correlations)) if pairwise_correlations else 0.0,
        'cross_family_agreement_note': (
            f"Mean pairwise rank correlation = {np.mean(pairwise_correlations):.3f}. "
            f"High agreement (ρ > 0.7) suggests cross-family robustness."
        ) if pairwise_correlations else "Insufficient data for cross-family agreement"
    }


def main():
    parser = argparse.ArgumentParser(
        description="Axis-1 multi-family EXPLORATORY pilot (CODE + OFFLINE TESTS ONLY)"
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to config YAML file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run: validate config and setup, do NOT call real API"
    )
    args = parser.parse_args()
    
    # Load config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"=== Axis-1 Multi-Family EXPLORATORY Pilot ===")
    print(f"⚠️  EXPLORATORY ONLY — not confirmatory ⚠️")
    print(f"Config: {args.config}")
    print(f"Experiment: {config['experiment_name']}")
    print(f"Description: {config['description']}")
    print()
    
    if args.dry_run:
        print("DRY RUN MODE — will NOT call real API")
        print()
    
    # Compute config hash (for reproducibility)
    config_str = json.dumps(config, sort_keys=True)
    config_hash = hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    # Extract config parameters
    models = config.get('models', [])
    n_items = config.get('n_items', 10)
    ui_conditions = config.get('ui_conditions', [])
    seeds = config.get('seeds', [42])
    inter_call_sleep = config.get('inter_call_sleep', 0.8)
    call_budget = config.get('call_budget', 450)
    
    print(f"Models: {models}")
    print(f"Items: {n_items}")
    print(f"Conditions: {ui_conditions}")
    print(f"Seeds: {seeds}")
    print(f"Call budget per model: {call_budget}")
    print()
    
    # Create personas (same as PR #4)
    persona_configs = config.get('personas', [])
    personas = [
        Persona(
            persona_id=p['persona_id'],
            domain_skill=p['domain_skill'],
            ai_literacy=p['ai_literacy'],
            risk_sensitivity=p['risk_sensitivity'],
            caution=p['caution'],
            temperature=p['temperature'],
            prior_mix=p['prior_mix']
        )
        for p in persona_configs
    ]
    
    print(f"Personas: {len(personas)}")
    for p in personas:
        print(f"  - {p.persona_id}: skill={p.domain_skill:.1f}, ai_lit={p.ai_literacy:.1f}, "
              f"risk={p.risk_sensitivity:.1f}, caution={p.caution:.1f}")
    print()
    
    # Select hard items (data-driven, Fix B)
    item_selection_config = config.get('item_selection', {})
    criteria = ItemSelectionCriteria(
        n_items=n_items,
        prefer_ai_wrong=item_selection_config.get('prefer_ai_wrong', 0.5),
        prefer_low_conf=item_selection_config.get('prefer_low_conf', 0.3),
        prefer_high_variance=item_selection_config.get('prefer_high_variance', 0.2),
        seed=seeds[0]
    )
    
    tasks = select_hard_items(criteria=criteria)
    task_list = list(tasks.values())
    
    print(f"Selected {len(task_list)} tasks")
    print()
    
    # Estimate total calls per model
    # System-1 = personas × items
    # System-2 = personas × items × conditions
    system1_calls = len(personas) * len(task_list)
    system2_calls = len(personas) * len(task_list) * len(ui_conditions)
    total_calls_per_model = system1_calls + system2_calls
    
    print(f"Call estimate per model:")
    print(f"  System-1 (shared): {system1_calls}")
    print(f"  System-2 (per condition): {system2_calls}")
    print(f"  Total: {total_calls_per_model}")
    print(f"  Budget: {call_budget}")
    
    if total_calls_per_model > call_budget:
        raise ValueError(
            f"Estimated calls ({total_calls_per_model}) exceed budget ({call_budget}). "
            f"Reduce n_items, personas, or conditions."
        )
    
    print()
    
    if args.dry_run:
        print("DRY RUN — stopping before API calls")
        print(f"Config validated. Would run {len(models)} models × {total_calls_per_model} calls each")
        return
    
    # Multi-provider run loop
    all_responses = []
    provider_stats = {}
    
    for model_name in models:
        print(f"\n{'='*60}")
        print(f"Running panel with model: {model_name}")
        print(f"{'='*60}\n")
        
        # Create provider for this model
        provider = GitHubModelsProvider(
            model_name=model_name,
            call_budget=call_budget,
            inter_call_sleep=inter_call_sleep
        )
        
        # Run panel (System-1 frozen across all conditions)
        # ui_pair is actually a list/tuple of all conditions
        model_responses = run_panel(
            personas=personas,
            tasks=task_list,
            ui_pair=tuple(ui_conditions),  # All 5 conditions
            providers=[provider],
            seeds=seeds,
            mode="static"
        )
        
        all_responses.extend(model_responses)
        
        # Collect stats
        stats = provider.get_stats()
        provider_stats[model_name] = stats
        print(f"\nModel {model_name} stats:")
        print(f"  API calls: {stats['api_calls']}")
        print(f"  Cache hits: {stats['cache_hits']}")
        print(f"  Total requests: {stats['total_requests']}")
    
    print(f"\n{'='*60}")
    print(f"All models complete. Total responses: {len(all_responses)}")
    print(f"{'='*60}\n")
    
    # Compute metrics
    print("Computing metrics...")
    
    # Load human over-dispersion from E1 decomposition (for axis-1 cross-condition correlation)
    e1_path = Path("results/e1_decomposition.json")
    if not e1_path.exists():
        print(f"WARNING: {e1_path} not found. Cannot compute cross-condition correlation.")
        print("Run E1 decomposition first to get human over-dispersion baseline.")
        human_overdispersion_by_condition = {}
    else:
        with open(e1_path, 'r') as f:
            e1_results = json.load(f)
        
        # Extract per-condition over-dispersion (rho) from E1
        human_overdispersion_by_condition = {}
        for cond, cond_data in e1_results.get('conditions', {}).items():
            split_half = cond_data.get('split_half_reliability', {})
            # Use Spearman-Brown reliability as proxy for over-dispersion
            # (E1 decomposition used different metric; adapt as needed)
            # For axis-1, we want betabinom rho, but E1 has split-half
            # Use placeholder for now; proper E1 should have betabinom rho
            rho = split_half.get('spearman_brown_reliability', 0.0)
            human_overdispersion_by_condition[cond] = rho
    
    # Per-condition metrics
    condition_metrics = {}
    panel_disagreement_by_condition = {}
    
    for cond in ui_conditions:
        cond_responses = [r for r in all_responses if r.ui_condition == cond]
        
        # Conflict-conditioned reliance
        conflict_result = conflict_conditioned_reliance(cond_responses)
        
        # Panel disagreement (across full panel: personas × models)
        disagreement_result = compute_panel_disagreement_across_personas_models(
            all_responses,
            cond
        )
        
        panel_disagreement_by_condition[cond] = disagreement_result['disagreement']
        
        condition_metrics[cond] = {
            'conflict_conditioned_reliance': {
                'reliance_rate': conflict_result.reliance_rate,
                'unconditional_reliance': conflict_result.unconditional_reliance,
                'n_conflict': conflict_result.n_conflict,
                'n_total': conflict_result.n_total,
                'conflict_fraction': conflict_result.conflict_fraction
            },
            'panel_disagreement': disagreement_result
        }
    
    # Per-model, per-condition metrics
    model_condition_metrics = {}
    disagreement_by_model_condition = {}
    
    for model in models:
        model_metrics = {}
        for cond in ui_conditions:
            model_cond_responses = [
                r for r in all_responses
                if r.model == model and r.ui_condition == cond
            ]
            
            if not model_cond_responses:
                continue
            
            # Conflict-conditioned reliance
            conflict_result = conflict_conditioned_reliance(model_cond_responses)
            
            # Panel disagreement (across personas for this model)
            # Compute per-persona reliance
            persona_reliance = {}
            for resp in model_cond_responses:
                if resp.persona_id not in persona_reliance:
                    persona_reliance[resp.persona_id] = []
                persona_reliance[resp.persona_id].append(float(resp.relied))
            
            persona_means = [np.mean(v) for v in persona_reliance.values()]
            disagreement = float(np.var(persona_means, ddof=1)) if len(persona_means) > 1 else 0.0
            
            disagreement_by_model_condition[(model, cond)] = disagreement
            
            model_metrics[cond] = {
                'conflict_conditioned_reliance': conflict_result.reliance_rate,
                'panel_disagreement': disagreement,
                'n_responses': len(model_cond_responses)
            }
        
        model_condition_metrics[model] = model_metrics
    
    # Cross-condition correlation (axis-1 main test)
    if human_overdispersion_by_condition and panel_disagreement_by_condition:
        # Align conditions
        shared_conditions = sorted(
            set(human_overdispersion_by_condition.keys()) & set(panel_disagreement_by_condition.keys())
        )
        
        if len(shared_conditions) >= 3:
            correlation_result = condition_correlation(
                disagreement_by_condition=panel_disagreement_by_condition,
                overdispersion_by_condition=human_overdispersion_by_condition
            )
            
            axis1_correlation = {
                'spearman_rho': correlation_result.spearman_rho,
                'spearman_pvalue': correlation_result.spearman_pvalue,
                'permutation_pvalue': correlation_result.permutation_pvalue,
                'bootstrap_ci': [
                    correlation_result.bootstrap_ci_lower,
                    correlation_result.bootstrap_ci_upper
                ],
                'n_conditions': correlation_result.n_conditions,
                'degenerate': correlation_result.degenerate,
                'note': correlation_result.note
            }
        else:
            axis1_correlation = {
                'note': f"Only {len(shared_conditions)} shared conditions. Need ≥3 for non-degenerate correlation."
            }
    else:
        axis1_correlation = {
            'note': "Human over-dispersion data not available. Run E1 decomposition first."
        }
    
    # Cross-family agreement
    cross_family = compute_cross_family_agreement(
        disagreement_by_model_condition=disagreement_by_model_condition,
        models=models,
        conditions=ui_conditions
    )
    
    # Power analysis readout
    # Effect size estimate: Spearman rho from axis-1 correlation
    # Variance components: between-persona, between-model, between-condition
    power_analysis = {
        'observed_effect_size': {
            'spearman_rho': axis1_correlation.get('spearman_rho', 0.0),
            'bootstrap_ci_width': (
                axis1_correlation['bootstrap_ci'][1] - axis1_correlation['bootstrap_ci'][0]
                if 'bootstrap_ci' in axis1_correlation else 0.0
            )
        },
        'variance_components': {
            'between_condition_disagreement': float(np.var(list(panel_disagreement_by_condition.values()), ddof=1))
                if len(panel_disagreement_by_condition) > 1 else 0.0,
            'mean_within_model_disagreement': float(np.mean([
                m['panel_disagreement']
                for model_metrics in model_condition_metrics.values()
                for m in model_metrics.values()
            ])) if model_condition_metrics else 0.0
        },
        'note': (
            "This is EXPLORATORY power-analysis input ONLY. "
            "Use these estimates to size a CONFIRMATORY run with adequate power. "
            "DO NOT tune conditions/τ/model-set based on these results."
        )
    }
    
    # Build results
    results = {
        'experiment_name': config['experiment_name'],
        'description': config['description'],
        'exploratory_status': '⚠️ EXPLORATORY ONLY — NOT CONFIRMATORY ⚠️',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'config_hash': config_hash,
        'run_manifest': {
            'models': models,
            'n_personas': len(personas),
            'n_items': len(task_list),
            'ui_conditions': ui_conditions,
            'seeds': seeds,
            'config': config
        },
        'provider_stats': provider_stats,
        'total_responses': len(all_responses),
        'condition_metrics': condition_metrics,
        'model_condition_metrics': model_condition_metrics,
        'axis1_cross_condition_correlation': axis1_correlation,
        'cross_family_agreement': cross_family,
        'power_analysis_input': power_analysis,
        'all_responses': [
            {
                'persona_id': r.persona_id,
                'model': r.model,
                'task_id': r.task_id,
                'ui_condition': r.ui_condition,
                'seed': r.seed,
                'system1_decision': r.system1_decision,
                'final_decision': r.final_decision,
                'relied': r.relied,
                'confidence': r.confidence,
                'trace': r.trace,
                'trust_state': r.trust_state
            }
            for r in all_responses
        ]
    }
    
    # Write results
    output_path = Path("results/axis1_pilot.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults written to: {output_path}")
    print()
    print("=== SUMMARY ===")
    print(f"⚠️  EXPLORATORY ONLY — NOT CONFIRMATORY ⚠️")
    print(f"Total responses: {len(all_responses)}")
    print(f"Models: {len(models)}")
    print(f"Conditions: {len(ui_conditions)}")
    print()
    print("Axis-1 cross-condition correlation:")
    if 'spearman_rho' in axis1_correlation:
        print(f"  Spearman ρ = {axis1_correlation['spearman_rho']:.4f}")
        print(f"  Permutation p = {axis1_correlation['permutation_pvalue']:.4f}")
        print(f"  Bootstrap CI = [{axis1_correlation['bootstrap_ci'][0]:.4f}, {axis1_correlation['bootstrap_ci'][1]:.4f}]")
        if axis1_correlation['degenerate']:
            print(f"  ⚠️  DEGENERATE (n < 3 conditions)")
    else:
        print(f"  {axis1_correlation.get('note', 'N/A')}")
    print()
    print("Cross-family agreement:")
    print(f"  Mean pairwise rank correlation = {cross_family['mean_pairwise_correlation']:.4f}")
    print()
    print("Power analysis input:")
    print(f"  Observed effect size (ρ) = {power_analysis['observed_effect_size']['spearman_rho']:.4f}")
    print(f"  Bootstrap CI width = {power_analysis['observed_effect_size']['bootstrap_ci_width']:.4f}")
    print()
    print(f"{power_analysis['note']}")
    print()
    print("✅ Experiment complete")


if __name__ == "__main__":
    main()
