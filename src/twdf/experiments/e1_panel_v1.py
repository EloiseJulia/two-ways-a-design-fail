"""
E1 Panel V1 experiment runner (Module B thin vertical slice).

Real LLM panel with counterfactual pairing via GitHub Models.

Usage:
    python -m twdf.experiments.e1_panel_v1 --config configs/e1_panel_v1.yaml
"""

import argparse
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime

import yaml
import numpy as np

from twdf.panel.stub import Persona
from twdf.panel.provider import GitHubModelsProvider
from twdf.panel.real_panel import run_panel
from twdf.data.bansal_tasks import load_beer_tasks
from twdf.metrics.overdispersion import (
    within_task_diff,
    bootstrap_ci,
    paired_permutation_test
)


def compute_panel_disagreement(responses: list, ui_condition: str) -> float:
    """
    Compute panel disagreement (variance in reliance) for a given UI condition.
    
    This is the panel-side signal that should correlate with human over-dispersion.
    
    Args:
        responses: List of agent responses
        ui_condition: Which UI condition to analyze
    
    Returns:
        Disagreement metric (variance in per-persona reliance rates)
    """
    # Filter to this UI condition
    ui_responses = [r for r in responses if r.ui_condition == ui_condition]
    
    if not ui_responses:
        return 0.0
    
    # Compute per-persona reliance rate
    persona_reliance = {}
    for resp in ui_responses:
        if resp.persona_id not in persona_reliance:
            persona_reliance[resp.persona_id] = []
        persona_reliance[resp.persona_id].append(float(resp.relied))
    
    # Average reliance per persona
    persona_means = [np.mean(rates) for rates in persona_reliance.values()]
    
    # Disagreement = variance across personas
    return float(np.var(persona_means, ddof=1) if len(persona_means) > 1 else 0.0)


def main():
    parser = argparse.ArgumentParser(
        description="E1 Panel V1: Real LLM panel with counterfactual pairing"
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to config YAML file"
    )
    args = parser.parse_args()
    
    # Load config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"=== E1 Panel V1 Experiment ===")
    print(f"Config: {args.config}")
    print(f"Experiment: {config['experiment_name']}")
    print(f"Description: {config['description']}")
    print()
    
    # Compute config hash (for reproducibility)
    config_str = json.dumps(config, sort_keys=True)
    config_hash = hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    # Create personas
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
        for p in config['personas']
    ]
    
    print(f"Personas: {len(personas)}")
    for p in personas:
        print(f"  - {p.persona_id}: skill={p.domain_skill:.1f}, ai_lit={p.ai_literacy:.1f}, "
              f"risk={p.risk_sensitivity:.1f}, caution={p.caution:.1f}, temp={p.temperature:.1f}")
    print()
    
    # Load tasks
    print(f"Loading {config['domain']} tasks (n={config['n_tasks']}, seed={config['task_seed']})...")
    tasks = load_beer_tasks(
        seed=config['task_seed'],
        n_tasks=config['n_tasks']
    )
    
    print(f"Loaded {len(tasks)} tasks")
    print()
    
    # Create provider
    print("Initializing GitHub Models provider...")
    provider = GitHubModelsProvider(
        cache_dir=Path(config['cache_dir']),
        call_budget=config['model']['call_budget'],
        inter_call_sleep=config['model']['inter_call_sleep'],
        max_retries=config['model']['max_retries']
    )
    print(f"Provider: {provider.name}")
    print(f"Call budget: {config['model']['call_budget']}")
    print(f"Cache dir: {config['cache_dir']}")
    print()
    
    # Run panel
    ui_pair = tuple(config['ui_pair'])
    print(f"Running panel with UI pair: {ui_pair[0]} vs {ui_pair[1]}")
    print(f"Mode: {config['mode']}")
    print(f"Expected calls: {len(personas)} personas × {len(tasks)} tasks × 2 UI × 2 systems = {len(personas) * len(tasks) * 2 * 2}")
    print()
    
    start_time = time.time()
    
    responses = run_panel(
        personas=personas,
        tasks=list(tasks.values()),
        ui_pair=ui_pair,
        providers=[provider],
        seeds=config['seeds'],
        mode=config['mode']
    )
    
    wall_time = time.time() - start_time
    
    print(f"Panel completed in {wall_time:.1f}s")
    print(f"Total responses: {len(responses)}")
    print()
    
    # Get provider stats
    provider_stats = provider.get_stats()
    print(f"Provider stats:")
    print(f"  API calls: {provider_stats['api_calls']}")
    print(f"  Cache hits: {provider_stats['cache_hits']}")
    print(f"  Total requests: {provider_stats['total_requests']}")
    print()
    
    # Estimate cost (gpt-4o-mini pricing: ~$0.15/1M input tokens, ~$0.60/1M output tokens)
    # Rough estimate: ~500 tokens/call avg
    est_cost = provider_stats['api_calls'] * 500 * (0.15 + 0.60) / 1_000_000
    print(f"Estimated cost: ${est_cost:.4f}")
    print()
    
    # ===== ANALYSIS =====
    
    control_cond, treatment_cond = ui_pair
    
    # Per-condition panel disagreement
    control_disagreement = compute_panel_disagreement(responses, control_cond)
    treatment_disagreement = compute_panel_disagreement(responses, treatment_cond)
    
    print("=== PANEL DISAGREEMENT (variance in per-persona reliance) ===")
    print(f"{control_cond}: {control_disagreement:.4f}")
    print(f"{treatment_cond}: {treatment_disagreement:.4f}")
    print()
    
    # Per-persona reliance rates
    print("=== PER-PERSONA RELIANCE RATES ===")
    for ui_cond in [control_cond, treatment_cond]:
        print(f"{ui_cond}:")
        ui_responses = [r for r in responses if r.ui_condition == ui_cond]
        persona_reliance = {}
        for resp in ui_responses:
            if resp.persona_id not in persona_reliance:
                persona_reliance[resp.persona_id] = []
            persona_reliance[resp.persona_id].append(float(resp.relied))
        
        for persona_id in sorted(persona_reliance.keys()):
            rate = np.mean(persona_reliance[persona_id])
            n = len(persona_reliance[persona_id])
            print(f"  {persona_id}: {rate:.3f} (n={n})")
        print()
    
    # Within-task elasticity (E2 / C2)
    print("=== WITHIN-TASK RELIANCE ELASTICITY (C2) ===")
    
    # Compute per-task reliance rates
    control_by_task = {}
    treatment_by_task = {}
    
    for resp in responses:
        if resp.ui_condition == control_cond:
            if resp.task_id not in control_by_task:
                control_by_task[resp.task_id] = []
            control_by_task[resp.task_id].append(float(resp.relied))
        else:
            if resp.task_id not in treatment_by_task:
                treatment_by_task[resp.task_id] = []
            treatment_by_task[resp.task_id].append(float(resp.relied))
    
    # Mean per task
    control_task_means = {task: np.mean(vals) for task, vals in control_by_task.items()}
    treatment_task_means = {task: np.mean(vals) for task, vals in treatment_by_task.items()}
    
    # Within-task diff
    elasticity = within_task_diff(control_task_means, treatment_task_means)
    print(f"Mean elasticity (treatment - control): {elasticity:.4f}")
    
    # Paired permutation test
    perm_result = paired_permutation_test(
        control_task_means,
        treatment_task_means,
        n_permutations=10000,
        seed=42
    )
    print(f"Paired permutation test: p = {perm_result.pvalue:.4f} (n_pairs={perm_result.n_pairs})")
    
    # Bootstrap CI over personas
    # We need to resample personas, not tasks
    def elasticity_stat(persona_sample):
        # Compute elasticity for a bootstrap sample of personas
        control_means = {}
        treatment_means = {}
        
        for resp in responses:
            if resp.persona_id not in persona_sample:
                continue
            
            task = resp.task_id
            
            if resp.ui_condition == control_cond:
                if task not in control_means:
                    control_means[task] = []
                control_means[task].append(float(resp.relied))
            else:
                if task not in treatment_means:
                    treatment_means[task] = []
                treatment_means[task].append(float(resp.relied))
        
        control_task_means = {t: np.mean(v) for t, v in control_means.items()}
        treatment_task_means = {t: np.mean(v) for t, v in treatment_means.items()}
        
        return within_task_diff(control_task_means, treatment_task_means)
    
    # Create persona dict for bootstrap
    persona_ids = {p.persona_id: p.persona_id for p in personas}
    
    bootstrap_result = bootstrap_ci(
        stat_fn=elasticity_stat,
        data=persona_ids,
        n=10000,
        seed=43,
        alpha=0.05
    )
    
    print(f"Bootstrap 95% CI: [{bootstrap_result.ci_lower:.4f}, {bootstrap_result.ci_upper:.4f}]")
    print()
    
    # System-1 accuracy (sanity check: agents attempt the task)
    print("=== SYSTEM-1 ACCURACY (no AI) ===")
    system1_correct = []
    for resp in responses:
        task = tasks[resp.task_id]
        system1_dec = int(resp.system1_decision)
        correct = (system1_dec == task.ground_truth)
        system1_correct.append(correct)
    
    accuracy = np.mean(system1_correct)
    print(f"System-1 accuracy: {accuracy:.3f} (n={len(system1_correct)})")
    print("(Sanity check: agents are actually attempting the task)")
    print()
    
    # ===== SAVE RESULTS =====
    
    output_file = Path(config['output_file'])
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare results
    results = {
        'run_manifest': {
            'experiment_name': config['experiment_name'],
            'config_hash': config_hash,
            'config_file': args.config,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'wall_time_seconds': wall_time,
            'n_personas': len(personas),
            'n_tasks': len(tasks),
            'n_responses': len(responses),
            'ui_pair': list(ui_pair),
            'model': provider.name,
            'seeds': config['seeds'],
            'total_api_calls': provider_stats['api_calls'],
            'cache_hits': provider_stats['cache_hits'],
            'estimated_cost_usd': est_cost,
        },
        'panel_disagreement': {
            control_cond: control_disagreement,
            treatment_cond: treatment_disagreement,
        },
        'elasticity': {
            'mean_diff': elasticity,
            'permutation_pvalue': perm_result.pvalue,
            'bootstrap_ci_lower': bootstrap_result.ci_lower,
            'bootstrap_ci_upper': bootstrap_result.ci_upper,
            'n_pairs': perm_result.n_pairs,
        },
        'system1_accuracy': accuracy,
        'responses': [
            {
                'persona_id': r.persona_id,
                'task_id': r.task_id,
                'ui_condition': r.ui_condition,
                'system1_decision': r.system1_decision,
                'final_decision': r.final_decision,
                'relied': r.relied,
                'confidence': r.confidence,
                'seed': r.seed,
            }
            for r in responses
        ]
    }
    
    # Save JSON
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: {output_file}")
    print()
    print("=== DELIVERABLES ===")
    print(f"✓ Real panel implemented with GitHub Models")
    print(f"✓ Counterfactual pairing (System-1 frozen across UI arms)")
    print(f"✓ {len(personas)} diverse personas × {len(tasks)} diverse tasks")
    print(f"✓ Elasticity + paired permutation test + bootstrap CI")
    print(f"✓ Panel disagreement per arm")
    print(f"✓ System-1 accuracy sanity check")
    print(f"✓ Results JSON with run_manifest")
    print()
    print("NEXT: Run tests, verify cross-process determinism, commit results")


if __name__ == '__main__':
    main()
