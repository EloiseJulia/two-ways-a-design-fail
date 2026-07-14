"""
E1 v0: Two-axis thin vertical slice experiment.

Goal: Prove the chain end-to-end:
  Bansal real data -> canonical schema -> synthetic panel stub -> 
  axis-1 over-dispersion metric + mean-predictor baseline ->
  ONE correlation number (panel disagreement vs human over-dispersion)

Runnable via: python -m twdf.experiments.e1_vslice --config configs/vslice_v0.yaml
"""

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

from twdf import RunManifest, __version__
from twdf.data.bansal import load_bansal, get_ui_condition_pair
from twdf.metrics.overdispersion import (
    betabinom_overdispersion,
    baseline_mean_predictor,
    bootstrap_ci
)
from twdf.panel.stub import (
    Persona,
    generate_synthetic_panel,
    compute_panel_disagreement
)


def run_e1_vslice(config: dict) -> dict:
    """
    Run E1 v0 thin vertical slice.
    
    Steps:
    1. Load Bansal data for selected UI pair
    2. Compute human between-user over-dispersion per UI condition (beta-binomial)
    3. Generate synthetic panel responses with tunable disagreement
    4. Compute panel disagreement per UI condition
    5. Correlate panel disagreement with human over-dispersion
    6. Compare to mean-predictor baseline
    
    Returns:
        Results dictionary with all metrics and the correlation number
    """
    print("=" * 80)
    print("E1 v0: Two-axis thin vertical slice")
    print(f"Package version: {__version__}")
    print("=" * 80)
    
    # Extract config
    data_config = config.get('data', {})
    panel_config = config.get('panel', {})
    seeds = config.get('seeds', {})
    
    # 1. Load human data
    print("\n[1/6] Loading Bansal CHI'21 human reliance data...")
    ui_pair = get_ui_condition_pair()
    control, treatment = ui_pair
    
    df = load_bansal(
        data_dir=Path(data_config.get('raw_dir', 'data/raw')),
        task_sample=data_config.get('task_sample'),  # None = auto-select 10 tasks
        ui_conditions=ui_pair
    )
    
    # 2. Compute human over-dispersion per UI condition
    print(f"\n[2/6] Computing human over-dispersion (beta-binomial) per UI condition...")
    
    human_results = {}
    for ui_cond in [control, treatment]:
        df_ui = df[df['ui_condition'] == ui_cond]
        
        # Build relied_by_user dict: user_id -> (n_relied, n_trials)
        user_stats = {}
        for user_id in df_ui['user_id'].unique():
            user_trials = df_ui[df_ui['user_id'] == user_id]
            n_relied = user_trials['relied'].sum()
            n_trials = len(user_trials)
            user_stats[user_id] = (int(n_relied), n_trials)
        
        # Beta-binomial over-dispersion
        od_result = betabinom_overdispersion(user_stats)
        
        # Mean-predictor baseline (rho=0 by construction)
        baseline = baseline_mean_predictor(user_stats)
        
        # Bootstrap CI for rho
        ci = bootstrap_ci(
            stat_fn=lambda data: betabinom_overdispersion(data).rho,
            data=user_stats,
            n=config.get('bootstrap_n', 1000),  # reduce for speed in v0
            seed=seeds.get('bootstrap', 42)
        )
        
        human_results[ui_cond] = {
            'overdispersion': od_result,
            'baseline': baseline,
            'rho_ci': ci,
            'n_users': len(user_stats),
            'n_trials': sum(n for _, n in user_stats.values())
        }
        
        print(f"\n  {ui_cond}:")
        print(f"    Users: {human_results[ui_cond]['n_users']}, Trials: {human_results[ui_cond]['n_trials']}")
        print(f"    Over-dispersion (rho): {od_result.rho:.4f} [95% CI: {ci.ci_lower:.4f}, {ci.ci_upper:.4f}]")
        print(f"    Mean reliance: {od_result.mean_p:.3f}")
        print(f"    Empirical variance: {od_result.empirical_variance:.4f}")
        print(f"    Binomial variance: {od_result.binomial_variance:.4f}")
        print(f"    Excess variance: {od_result.excess_variance:.4f}")
        print(f"    Baseline (mean-predictor) rho: {baseline.rho:.4f} (by construction = 0)")
    
    # 3. Generate synthetic panel responses
    print(f"\n[3/6] Generating synthetic panel responses (STUB)...")
    
    # Create personas
    n_personas = panel_config.get('n_personas', 5)
    personas = [
        Persona(
            persona_id=f"persona_{i}",
            domain_skill=0.5 + 0.1 * i,
            ai_literacy=0.5,
            risk_sensitivity=0.5,
            caution=0.5,
            temperature=0.7,
            prior_mix=0.5
        )
        for i in range(n_personas)
    ]
    
    # Task IDs from loaded data
    task_ids = df['task_id'].unique().tolist()
    
    # Base reliance rates per UI (we'll tune these to create different disagreement levels)
    # For the correlation to work, we want treatment to have higher disagreement
    base_reliance = {
        control: 0.5,     # control: moderate reliance, lower spread
        treatment: 0.6    # treatment: slightly higher reliance, will add more spread
    }
    
    # Generate panel with different spreads per UI to create the correlation signal
    # Control: lower spread -> lower disagreement -> lower over-dispersion
    # Treatment: higher spread -> higher disagreement -> higher over-dispersion
    panel_responses = []
    
    # Control with low spread
    panel_responses.extend(generate_synthetic_panel(
        personas=personas,
        tasks=task_ids,
        ui_pair=(control,),  # just control
        base_reliance={control: base_reliance[control]},
        persona_spread=panel_config.get('control_spread', 0.1),  # low spread
        seed=seeds.get('panel', 42)
    ))
    
    # Treatment with high spread
    panel_responses.extend(generate_synthetic_panel(
        personas=personas,
        tasks=task_ids,
        ui_pair=(treatment,),  # just treatment
        base_reliance={treatment: base_reliance[treatment]},
        persona_spread=panel_config.get('treatment_spread', 0.3),  # high spread
        seed=seeds.get('panel', 42) + 1
    ))
    
    print(f"  Generated {len(panel_responses)} synthetic panel responses")
    print(f"  Personas: {n_personas}")
    print(f"  Tasks: {len(task_ids)}")
    print(f"  Control spread: {panel_config.get('control_spread', 0.1):.2f}")
    print(f"  Treatment spread: {panel_config.get('treatment_spread', 0.3):.2f}")
    
    # 4. Compute panel disagreement per UI condition
    print(f"\n[4/6] Computing panel disagreement per UI condition...")
    
    panel_disagreement = {}
    for ui_cond in [control, treatment]:
        disagreement = compute_panel_disagreement(panel_responses, ui_cond)
        panel_disagreement[ui_cond] = disagreement
        print(f"  {ui_cond}: disagreement = {disagreement:.4f}")
    
    # 5. Correlate panel disagreement with human over-dispersion
    print(f"\n[5/6] Computing correlation: panel disagreement vs human over-dispersion...")
    
    # We have 2 data points: (control, treatment)
    human_rho = [human_results[control]['overdispersion'].rho,
                 human_results[treatment]['overdispersion'].rho]
    panel_disagree = [panel_disagreement[control],
                     panel_disagreement[treatment]]
    
    # Pearson correlation
    correlation = np.corrcoef(human_rho, panel_disagree)[0, 1]
    
    print(f"  Human over-dispersion (rho): {human_rho}")
    print(f"  Panel disagreement:         {panel_disagree}")
    print(f"  *** CORRELATION: r = {correlation:.4f} ***")
    
    # 6. Mean-predictor baseline comparison
    print(f"\n[6/6] Mean-predictor baseline comparison...")
    print(f"  Control:")
    print(f"    Human rho: {human_results[control]['overdispersion'].rho:.4f}")
    print(f"    Baseline rho: {human_results[control]['baseline'].rho:.4f}")
    print(f"    Human BEATS baseline: {human_results[control]['overdispersion'].rho > human_results[control]['baseline'].rho}")
    print(f"  Treatment:")
    print(f"    Human rho: {human_results[treatment]['overdispersion'].rho:.4f}")
    print(f"    Baseline rho: {human_results[treatment]['baseline'].rho:.4f}")
    print(f"    Human BEATS baseline: {human_results[treatment]['overdispersion'].rho > human_results[treatment]['baseline'].rho}")
    
    # Compile results
    results = {
        'ui_pair': list(ui_pair),
        'human_overdispersion': {
            ui: {
                'rho': human_results[ui]['overdispersion'].rho,
                'rho_ci_lower': human_results[ui]['rho_ci'].ci_lower,
                'rho_ci_upper': human_results[ui]['rho_ci'].ci_upper,
                'mean_p': human_results[ui]['overdispersion'].mean_p,
                'empirical_var': human_results[ui]['overdispersion'].empirical_variance,
                'binomial_var': human_results[ui]['overdispersion'].binomial_variance,
                'excess_var': human_results[ui]['overdispersion'].excess_variance,
                'n_users': human_results[ui]['n_users'],
                'n_trials': human_results[ui]['n_trials']
            }
            for ui in [control, treatment]
        },
        'baseline_mean_predictor': {
            ui: {
                'rho': human_results[ui]['baseline'].rho,
                'mean_p': human_results[ui]['baseline'].mean_p
            }
            for ui in [control, treatment]
        },
        'panel_disagreement': panel_disagreement,
        'correlation': {
            'r': float(correlation),
            'human_rho': human_rho,
            'panel_disagreement': panel_disagree
        },
        'metadata': {
            'n_personas': n_personas,
            'n_tasks': len(task_ids),
            'task_ids': task_ids,
            'control_spread': panel_config.get('control_spread', 0.1),
            'treatment_spread': panel_config.get('treatment_spread', 0.3),
            'stub_warning': 'SYNTHETIC PANEL STUB - not real LLM responses'
        }
    }
    
    return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run E1 v0 thin vertical slice experiment")
    parser.add_argument('--config', required=True, help="Path to YAML config file")
    parser.add_argument('--output', default='results/e1_vslice_v0.json', 
                       help="Output JSON path")
    
    args = parser.parse_args()
    
    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Run experiment
    results = run_e1_vslice(config)
    
    # Create run manifest
    manifest = RunManifest.create(
        config=config,
        seeds=config.get('seeds', {})
    )
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output = {
        'manifest': manifest.to_dict(),
        'results': results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'=' * 80}")
    print(f"Results saved to: {output_path}")
    print(f"{'=' * 80}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY (vslice-v0)")
    print("=" * 80)
    print(f"UI pair: {results['ui_pair'][0]} vs {results['ui_pair'][1]}")
    print(f"\nHuman over-dispersion (beta-binomial rho):")
    for ui in results['ui_pair']:
        od = results['human_overdispersion'][ui]
        print(f"  {ui}: {od['rho']:.4f} [95% CI: {od['rho_ci_lower']:.4f}, {od['rho_ci_upper']:.4f}]")
    
    print(f"\nPanel disagreement (synthetic stub):")
    for ui in results['ui_pair']:
        print(f"  {ui}: {results['panel_disagreement'][ui]:.4f}")
    
    print(f"\n*** PRIMARY RESULT: Correlation (panel disagreement vs human over-dispersion) ***")
    print(f"    r = {results['correlation']['r']:.4f}")
    
    print(f"\nMean-predictor baseline:")
    for ui in results['ui_pair']:
        baseline = results['baseline_mean_predictor'][ui]
        human_od = results['human_overdispersion'][ui]
        beats = human_od['rho'] > baseline['rho']
        print(f"  {ui}: baseline rho={baseline['rho']:.4f}, human BEATS baseline: {beats}")
    
    print("=" * 80)


if __name__ == '__main__':
    main()
