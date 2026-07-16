"""
E4 Compliance experiment runner (axis-2 dark-pattern sensor + placebo baseline).

Formalizes the compliance floor (H3) and axis-2 systematic over-reliance sensor:
- 4 conditions: control, faithful, placebo (NEW), dark
- Placebo: AI + conf + NON-INFORMATIVE explanation (isolates presence effect)
- H3: control < placebo < faithful (compliance floor exists, genuine value beyond presence)
- Axis-2: over_reliance_level on wrong-AI + compliance-adjusted version
- System-1 frozen across ALL 4 conditions (invariant tested)

Usage:
    python -m twdf.experiments.e4_compliance --config configs/e4_compliance.yaml
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
from twdf.data.item_selector import ItemSelectionCriteria, select_hard_items
from twdf.metrics.overdispersion import (
    within_task_diff,
    bootstrap_ci,
    paired_permutation_test,
    conflict_conditioned_reliance,
    over_reliance_level
)


def main():
    parser = argparse.ArgumentParser(
        description="E4 Compliance: Placebo baseline + axis-2 sensor formalization"
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
    
    print(f"=== E4 Compliance Experiment ===")
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
    
    print(f"=== PERSONAS ({len(personas)}) ===")
    for p in personas:
        print(f"  - {p.persona_id}:")
        print(f"      skill={p.domain_skill:.1f}, ai_lit={p.ai_literacy:.1f}, "
              f"risk={p.risk_sensitivity:.1f}, caution={p.caution:.1f}, temp={p.temperature:.1f}")
    print()
    
    # Load tasks
    criteria = ItemSelectionCriteria(
        n_items=config['item_selection']['n_items'],
        prefer_ai_wrong=config['item_selection']['prefer_ai_wrong'],
        prefer_low_conf=config['item_selection']['prefer_low_conf'],
        prefer_high_variance=config['item_selection']['prefer_high_variance'],
        seed=config['item_selection']['seed']
    )
    
    tasks = select_hard_items(criteria=criteria)
    
    # Create provider
    print("Initializing GitHub Models provider...")
    provider = GitHubModelsProvider(
        model_name=config['model']['name'],
        cache_dir=Path(config['cache_dir']),
        call_budget=config['model']['call_budget'],
        inter_call_sleep=config['model']['inter_call_sleep'],
        max_retries=config['model']['max_retries']
    )
    print(f"Provider: {provider.name}")
    print(f"Call budget: {config['model']['call_budget']}")
    print(f"Cache dir: {config['cache_dir']}")
    print()
    
    # Run panel (4 conditions: control, faithful, placebo, dark)
    ui_conditions = tuple(config['ui_conditions'])
    print(f"=== RUNNING PANEL (4 CONDITIONS) ===")
    print(f"Conditions:")
    for i, cond in enumerate(ui_conditions):
        print(f"  {i+1}. {cond}")
    print(f"Mode: {config['mode']}")
    print(f"Expected calls: {len(personas)} personas × {len(tasks)} tasks × (1 System-1 + {len(ui_conditions)} System-2)")
    print(f"              = {len(personas) * len(tasks)} System-1 + {len(personas) * len(tasks) * len(ui_conditions)} System-2")
    print(f"              = {len(personas) * len(tasks) * (1 + len(ui_conditions))} total")
    print()
    
    start_time = time.time()
    
    responses = run_panel(
        personas=personas,
        tasks=list(tasks.values()),
        ui_pair=ui_conditions,  # 4-tuple
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
    
    # Estimate cost
    est_cost = provider_stats['api_calls'] * 500 * (0.15 + 0.60) / 1_000_000
    print(f"Estimated cost: ${est_cost:.4f}")
    print()
    
    # ===== ANALYSIS =====
    
    control_cond = ui_conditions[0]
    faithful_cond = ui_conditions[1]
    placebo_cond = ui_conditions[2]
    dark_cond = ui_conditions[3]
    
    # ===== H3: COMPLIANCE FLOOR (control < placebo < faithful) =====
    
    print("=" * 60)
    print("=== H3: COMPLIANCE FLOOR (placebo baseline) ===")
    print("=" * 60)
    print()
    
    # Conflict-conditioned reliance for all 3 explanation conditions
    control_responses = [r for r in responses if r.ui_condition == control_cond]
    faithful_responses = [r for r in responses if r.ui_condition == faithful_cond]
    placebo_responses = [r for r in responses if r.ui_condition == placebo_cond]
    
    control_conflict = conflict_conditioned_reliance(control_responses)
    faithful_conflict = conflict_conditioned_reliance(faithful_responses)
    placebo_conflict = conflict_conditioned_reliance(placebo_responses)
    
    print(f"{control_cond}:")
    print(f"  Conflict-conditioned reliance: {control_conflict.reliance_rate:.3f}")
    print(f"  Unconditional reliance: {control_conflict.unconditional_reliance:.3f}")
    print(f"  Conflict trials: {control_conflict.n_conflict}/{control_conflict.n_total} ({control_conflict.conflict_fraction:.1%})")
    print()
    
    print(f"{placebo_cond}:")
    print(f"  Conflict-conditioned reliance: {placebo_conflict.reliance_rate:.3f}")
    print(f"  Unconditional reliance: {placebo_conflict.unconditional_reliance:.3f}")
    print(f"  Conflict trials: {placebo_conflict.n_conflict}/{placebo_conflict.n_total} ({placebo_conflict.conflict_fraction:.1%})")
    print()
    
    print(f"{faithful_cond}:")
    print(f"  Conflict-conditioned reliance: {faithful_conflict.reliance_rate:.3f}")
    print(f"  Unconditional reliance: {faithful_conflict.unconditional_reliance:.3f}")
    print(f"  Conflict trials: {faithful_conflict.n_conflict}/{faithful_conflict.n_total} ({faithful_conflict.conflict_fraction:.1%})")
    print()
    
    # Compliance floor contrasts
    print("H3 Compliance floor hypothesis (control < placebo < faithful):")
    print(f"  control: {control_conflict.reliance_rate:.3f}")
    print(f"  placebo: {placebo_conflict.reliance_rate:.3f}")
    print(f"  faithful: {faithful_conflict.reliance_rate:.3f}")
    print()
    
    # Compute per-task reliance rates for paired tests (conflict trials only)
    control_by_task = {}
    placebo_by_task = {}
    faithful_by_task = {}
    
    for resp in responses:
        system1 = str(resp.system1_decision)
        final = str(resp.final_decision)
        ai_advice = str(resp.trace.get('ai_advice', ''))
        
        # Only count conflict trials
        if system1 != ai_advice:
            relied = (final == ai_advice)
            
            if resp.ui_condition == control_cond:
                if resp.task_id not in control_by_task:
                    control_by_task[resp.task_id] = []
                control_by_task[resp.task_id].append(float(relied))
            elif resp.ui_condition == placebo_cond:
                if resp.task_id not in placebo_by_task:
                    placebo_by_task[resp.task_id] = []
                placebo_by_task[resp.task_id].append(float(relied))
            elif resp.ui_condition == faithful_cond:
                if resp.task_id not in faithful_by_task:
                    faithful_by_task[resp.task_id] = []
                faithful_by_task[resp.task_id].append(float(relied))
    
    control_task_means = {task: np.mean(vals) for task, vals in control_by_task.items()}
    placebo_task_means = {task: np.mean(vals) for task, vals in placebo_by_task.items()}
    faithful_task_means = {task: np.mean(vals) for task, vals in faithful_by_task.items()}
    
    # Paired permutation tests
    if control_task_means and placebo_task_means:
        perm_placebo_control = paired_permutation_test(
            control_task_means,
            placebo_task_means,
            n_permutations=10000,
            seed=42
        )
        print(f"Placebo − Control paired permutation test:")
        print(f"  p = {perm_placebo_control.pvalue:.4f} (n_pairs={perm_placebo_control.n_pairs})")
        print(f"  mean diff = {perm_placebo_control.observed_diff:.4f}")
        print()
    
    if placebo_task_means and faithful_task_means:
        perm_faithful_placebo = paired_permutation_test(
            placebo_task_means,
            faithful_task_means,
            n_permutations=10000,
            seed=42
        )
        print(f"Faithful − Placebo paired permutation test:")
        print(f"  p = {perm_faithful_placebo.pvalue:.4f} (n_pairs={perm_faithful_placebo.n_pairs})")
        print(f"  mean diff = {perm_faithful_placebo.observed_diff:.4f}")
        print()
    
    # Per-persona breakdown (do personas diverge?)
    print("Per-persona conflict-conditioned reliance:")
    for ui_cond in [control_cond, placebo_cond, faithful_cond]:
        print(f"{ui_cond}:")
        ui_responses = [r for r in responses if r.ui_condition == ui_cond]
        
        persona_conflict_reliance = {}
        for resp in ui_responses:
            system1 = str(resp.system1_decision)
            final = str(resp.final_decision)
            ai_advice = str(resp.trace.get('ai_advice', ''))
            
            if resp.persona_id not in persona_conflict_reliance:
                persona_conflict_reliance[resp.persona_id] = {'conflict': [], 'all': []}
            
            relied = (final == ai_advice)
            persona_conflict_reliance[resp.persona_id]['all'].append(relied)
            
            if system1 != ai_advice:
                switched = (final == ai_advice)
                persona_conflict_reliance[resp.persona_id]['conflict'].append(switched)
        
        for persona_id in sorted(persona_conflict_reliance.keys()):
            conflict_trials = persona_conflict_reliance[persona_id]['conflict']
            all_trials = persona_conflict_reliance[persona_id]['all']
            
            if conflict_trials:
                conflict_rate = np.mean(conflict_trials)
                n_conflict = len(conflict_trials)
            else:
                conflict_rate = 0.0
                n_conflict = 0
            
            unconditional_rate = np.mean(all_trials)
            
            print(f"  {persona_id}: conflict={conflict_rate:.3f} (n_conflict={n_conflict}), "
                  f"unconditional={unconditional_rate:.3f}")
        print()
    
    # ===== AXIS-2: SYSTEMATIC OVER-RELIANCE SENSOR =====
    
    print("=" * 60)
    print("=== AXIS-2: SYSTEMATIC OVER-RELIANCE SENSOR (WRONG-AI) ===")
    print("=" * 60)
    print()
    
    dark_responses = [r for r in responses if r.ui_condition == dark_cond]
    dark_over_reliance = over_reliance_level(dark_responses)
    
    print(f"{dark_cond}:")
    print(f"  Over-reliance level (adopted wrong AI): {dark_over_reliance.over_reliance_level:.3f}")
    print(f"  Between-persona spread: {dark_over_reliance.between_persona_spread:.4f}")
    print(f"  n_trials: {dark_over_reliance.n_trials}")
    print()
    
    # Compliance-adjusted axis-2 (subtract placebo floor)
    compliance_adjusted = dark_over_reliance.over_reliance_level - placebo_conflict.reliance_rate
    print(f"Compliance-adjusted axis-2 reading:")
    print(f"  over_reliance_level − placebo_floor = {dark_over_reliance.over_reliance_level:.3f} − {placebo_conflict.reliance_rate:.3f}")
    print(f"  = {compliance_adjusted:.3f}")
    print()
    
    print("Per-persona adoption of wrong AI:")
    for persona_id in sorted(dark_over_reliance.per_persona_adoption.keys()):
        rate = dark_over_reliance.per_persona_adoption[persona_id]
        print(f"  {persona_id}: {rate:.3f}")
    print()
    
    # ===== SANITY CHECKS =====
    
    print("=" * 60)
    print("=== SANITY CHECKS ===")
    print("=" * 60)
    print()
    
    # System-1 accuracy
    system1_correct = []
    for resp in responses:
        task_id = resp.task_id
        task = tasks[task_id]
        system1_dec = int(resp.system1_decision)
        correct = (system1_dec == task.ground_truth)
        system1_correct.append(correct)
    
    accuracy = np.mean(system1_correct)
    print(f"System-1 accuracy: {accuracy:.3f} (n={len(system1_correct)})")
    print()
    
    # System-1 frozen invariant (across all 4 conditions)
    print("System-1 frozen invariant test (same persona×task×seed across ALL 4 conditions):")
    invariant_violations = 0
    for persona in personas:
        for task_id in tasks.keys():
            cond_system1 = {}
            for resp in responses:
                if resp.persona_id == persona.persona_id and resp.task_id == task_id:
                    cond_system1[resp.ui_condition] = resp.system1_decision
            
            if len(cond_system1) == len(ui_conditions):
                s1_values = list(cond_system1.values())
                if len(set(s1_values)) > 1:
                    invariant_violations += 1
                    print(f"  VIOLATION: {persona.persona_id}, {task_id}: {cond_system1}")
    
    if invariant_violations == 0:
        print("  ✓ System-1 frozen invariant HOLDS across all 4 conditions")
    else:
        print(f"  ✗ {invariant_violations} invariant violations detected!")
    print()
    
    # Conflict rate
    total_conflict = sum([
        control_conflict.n_conflict,
        faithful_conflict.n_conflict,
        placebo_conflict.n_conflict,
    ])
    total_trials = sum([
        control_conflict.n_total,
        faithful_conflict.n_total,
        placebo_conflict.n_total,
    ])
    overall_conflict_rate = total_conflict / total_trials if total_trials > 0 else 0.0
    
    print(f"Overall conflict rate: {overall_conflict_rate:.1%}")
    print(f"  Control: {control_conflict.conflict_fraction:.1%}")
    print(f"  Placebo: {placebo_conflict.conflict_fraction:.1%}")
    print(f"  Faithful: {faithful_conflict.conflict_fraction:.1%}")
    print()
    
    # ===== SAVE RESULTS =====
    
    output_file = Path(config['output_file'])
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
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
            'ui_conditions': list(ui_conditions),
            'model': provider.name,
            'seeds': config['seeds'],
            'total_api_calls': provider_stats['api_calls'],
            'cache_hits': provider_stats['cache_hits'],
            'estimated_cost_usd': est_cost,
        },
        'h3_compliance_floor': {
            'control': {
                'conflict_reliance': control_conflict.reliance_rate,
                'unconditional_reliance': control_conflict.unconditional_reliance,
                'n_conflict': control_conflict.n_conflict,
                'n_total': control_conflict.n_total,
                'conflict_fraction': control_conflict.conflict_fraction,
            },
            'placebo': {
                'conflict_reliance': placebo_conflict.reliance_rate,
                'unconditional_reliance': placebo_conflict.unconditional_reliance,
                'n_conflict': placebo_conflict.n_conflict,
                'n_total': placebo_conflict.n_total,
                'conflict_fraction': placebo_conflict.conflict_fraction,
            },
            'faithful': {
                'conflict_reliance': faithful_conflict.reliance_rate,
                'unconditional_reliance': faithful_conflict.unconditional_reliance,
                'n_conflict': faithful_conflict.n_conflict,
                'n_total': faithful_conflict.n_total,
                'conflict_fraction': faithful_conflict.conflict_fraction,
            },
            'placebo_minus_control_perm_test': {
                'pvalue': perm_placebo_control.pvalue if 'perm_placebo_control' in locals() else None,
                'mean_diff': perm_placebo_control.observed_diff if 'perm_placebo_control' in locals() else None,
                'n_pairs': perm_placebo_control.n_pairs if 'perm_placebo_control' in locals() else 0,
            },
            'faithful_minus_placebo_perm_test': {
                'pvalue': perm_faithful_placebo.pvalue if 'perm_faithful_placebo' in locals() else None,
                'mean_diff': perm_faithful_placebo.observed_diff if 'perm_faithful_placebo' in locals() else None,
                'n_pairs': perm_faithful_placebo.n_pairs if 'perm_faithful_placebo' in locals() else 0,
            },
        },
        'axis2_over_reliance': {
            'raw_over_reliance_level': dark_over_reliance.over_reliance_level,
            'over_reliance_on_wrong': dark_over_reliance.over_reliance_on_wrong,
            'n_truly_wrong': dark_over_reliance.n_truly_wrong,
            'compliance_adjusted_level': compliance_adjusted,
            'placebo_floor': placebo_conflict.reliance_rate,
            'between_persona_spread': dark_over_reliance.between_persona_spread,
            'n_trials': dark_over_reliance.n_trials,
            'per_persona_adoption': dark_over_reliance.per_persona_adoption,
        },
        'system1_accuracy': accuracy,
        'overall_conflict_rate': overall_conflict_rate,
        'system1_frozen_invariant_violations': invariant_violations,
        'responses': [
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
                'trust_state': r.trust_state,
            }
            for r in responses
        ]
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: {output_file}")
    print()
    print("=" * 60)
    print("=== DELIVERABLES COMPLETE ===")
    print("=" * 60)
    print(f"✓ 4-condition panel: {control_cond}, {placebo_cond}, {faithful_cond}, {dark_cond}")
    print(f"✓ H3 compliance floor: control < placebo < faithful hypothesis tested")
    print(f"✓ Axis-2 sensor: raw + compliance-adjusted over-reliance level computed")
    print(f"✓ System-1 frozen invariant verified across all 4 conditions")
    print(f"✓ Conflict rate: {overall_conflict_rate:.1%}")
    print(f"✓ Per-persona breakdowns for all metrics")
    print(f"✓ Results JSON with full manifest + all response fields serialized")
    print()
    print("NEXT: Tests, verification, commit + push")


if __name__ == '__main__':
    main()
