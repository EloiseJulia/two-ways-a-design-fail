"""
E1 robustness analysis: Task selection sensitivity check.

BLOCKER-1 FIX: The audit found that over-dispersion signal is fragile to task 
selection. This script computes Human condition over-dispersion (and ideally all 
conditions) under 3 different task-selection schemes to assess robustness.

This addresses audit requirement: "Make per-condition over-dispersion use the 
MAXIMUM principled data, and add ROBUSTNESS analysis with >=3 task-selection 
schemes to SHOW whether the signal is robust or fragile."

Runnable via: python -m twdf.experiments.e1_robustness --config configs/e1_multicond.yaml
"""

import argparse
import json
from pathlib import Path
import sys

import yaml

from twdf import __version__
from twdf.data.bansal import load_bansal
from twdf.metrics.overdispersion import betabinom_overdispersion_within_domain


def run_robustness_analysis(config: dict) -> dict:
    """
    Run robustness analysis across 3 task-selection schemes.
    
    Schemes:
    1. 'all': ALL shared tasks across conditions (maximum data, default)
    2. 'min_per_domain': Min 3 tasks per domain (early dev mode, fragile)
    3. 'first_10_shared': First 10 shared tasks (v0 mode, fragile)
    
    For each scheme, compute Human condition over-dispersion (primary) and
    all other conditions (if feasible within reasonable runtime).
    
    Returns:
        Results dict with per-scheme over-dispersion estimates and summary
    """
    print("=" * 80)
    print("E1 ROBUSTNESS ANALYSIS: Task selection sensitivity")
    print(f"Package version: {__version__}")
    print("=" * 80)
    
    data_config = config.get('data', {})
    schemes = ['all', 'min_per_domain', 'first_10_shared']
    
    results = {
        'schemes': {},
        'summary': {}
    }
    
    # For each scheme, load data and compute over-dispersion
    for scheme in schemes:
        print(f"\n{'=' * 80}")
        print(f"SCHEME: {scheme}")
        print(f"{'=' * 80}")
        
        # Load data with this task selection scheme
        df = load_bansal(
            data_dir=Path(data_config.get('raw_dir', 'data/raw')),
            task_sample=None,
            ui_conditions=data_config.get('ui_conditions'),  # None = all 6
            task_selection=scheme
        )
        
        ui_conditions = sorted(df['ui_condition'].unique())
        n_tasks = df['task_id'].nunique()
        n_trials_total = len(df)
        
        print(f"\nDataset summary for scheme '{scheme}':")
        print(f"  UI conditions: {len(ui_conditions)}")
        print(f"  Tasks: {n_tasks}")
        print(f"  Total trials: {n_trials_total}")
        
        # Compute over-dispersion for each condition
        scheme_results = {}
        for ui_cond in ui_conditions:
            od_result = betabinom_overdispersion_within_domain(
                df=df,
                condition=ui_cond,
                difficulty_col='task_difficulty'
            )
            
            scheme_results[ui_cond] = {
                'rho': float(od_result.rho),
                'mean_p': float(od_result.mean_p),
                'n_users': int(od_result.n_users),
                'n_trials': int(od_result.total_trials)
            }
            
            print(f"\n  {ui_cond}:")
            print(f"    rho: {od_result.rho:.4f}")
            print(f"    mean_p: {od_result.mean_p:.3f}")
            print(f"    n_users: {od_result.n_users}")
            print(f"    n_trials: {od_result.total_trials}")
        
        results['schemes'][scheme] = {
            'n_tasks': n_tasks,
            'n_trials_total': n_trials_total,
            'conditions': scheme_results
        }
    
    # Summary: compare Human condition across schemes
    print(f"\n{'=' * 80}")
    print("ROBUSTNESS SUMMARY")
    print(f"{'=' * 80}")
    print("\nHuman condition over-dispersion (rho) across task selection schemes:")
    
    human_rhos = []
    for scheme in schemes:
        if 'Human' in results['schemes'][scheme]['conditions']:
            rho = results['schemes'][scheme]['conditions']['Human']['rho']
            n_trials = results['schemes'][scheme]['conditions']['Human']['n_trials']
            human_rhos.append(rho)
            print(f"  {scheme:20s}: rho = {rho:.4f} (n_trials = {n_trials})")
        else:
            print(f"  {scheme:20s}: Human condition not found")
    
    # Compute range and verdict
    if len(human_rhos) >= 2:
        rho_min = min(human_rhos)
        rho_max = max(human_rhos)
        rho_range = rho_max - rho_min
        
        # Heuristic: if range > 50% of mean, signal is fragile
        rho_mean = sum(human_rhos) / len(human_rhos)
        is_fragile = (rho_range > 0.5 * rho_mean) if rho_mean > 0 else False
        
        results['summary']['human_rho_range'] = {
            'min': float(rho_min),
            'max': float(rho_max),
            'range': float(rho_range),
            'mean': float(rho_mean),
            'fragile': is_fragile
        }
        
        print(f"\n  Range: {rho_range:.4f} (min={rho_min:.4f}, max={rho_max:.4f})")
        print(f"  Mean: {rho_mean:.4f}")
        
        if is_fragile:
            print(f"\n  ⚠️  VERDICT: FRAGILE - Range > 50% of mean")
            print(f"     The over-dispersion signal is SENSITIVE to task selection.")
            print(f"     Report this as a known limitation. Do NOT overclaim robustness.")
        else:
            print(f"\n  ✓ VERDICT: ROBUST - Range ≤ 50% of mean")
            print(f"     The over-dispersion signal is reasonably stable across schemes.")
    else:
        results['summary']['human_rho_range'] = None
        print("\n  Insufficient data for robustness verdict")
    
    # All conditions summary table
    print(f"\n{'=' * 80}")
    print("ALL CONDITIONS ACROSS SCHEMES")
    print(f"{'=' * 80}")
    
    all_conditions = set()
    for scheme_data in results['schemes'].values():
        all_conditions.update(scheme_data['conditions'].keys())
    
    for cond in sorted(all_conditions):
        print(f"\n{cond}:")
        for scheme in schemes:
            if cond in results['schemes'][scheme]['conditions']:
                cond_data = results['schemes'][scheme]['conditions'][cond]
                print(f"  {scheme:20s}: rho = {cond_data['rho']:.4f}, "
                      f"n_trials = {cond_data['n_trials']}")
            else:
                print(f"  {scheme:20s}: not available")
    
    return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run E1 robustness analysis")
    parser.add_argument('--config', required=True, help="Path to YAML config file")
    parser.add_argument('--output', default='results/e1_multicond_robustness.json',
                       help="Output JSON path")
    
    args = parser.parse_args()
    
    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Run robustness analysis
    results = run_robustness_analysis(config)
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'=' * 80}")
    print(f"Robustness results saved to: {output_path}")
    print(f"{'=' * 80}")


if __name__ == '__main__':
    main()
