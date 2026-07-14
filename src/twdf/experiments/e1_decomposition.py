"""
E1 decomposition analysis: User trait vs user x task variance in reliance.

SCIENTIFIC QUESTION:
Of the between-user variation in reliance, how much is a STABLE USER main effect 
(consistent reliance propensity across tasks) vs a USER x TASK interaction 
(task-dependent reliance)?

CRITICAL STRUCTURAL FACT (verified on Bansal data):
- 99.7% of (condition, user, task) cells have EXACTLY ONE observation
- Therefore: ANOVA-style variance partition on single-observation cells CANNOT 
  separate user x task interaction from Bernoulli sampling noise
- USER x TASK interaction is CONFOUNDED with noise at the cell level

CORRECT PRIMARY METHOD: SPLIT-HALF RELIABILITY
- Each user sees ~40-50 distinct tasks (median 50 on Bansal)
- Split-half reliability is WELL-POWERED and IDENTIFIED on this structure
- High reliability => stable user trait; low => task-dependent

OPTIONAL CORROBORATION: Binomial GLMM
- Unlike Gaussian ANOVA, Bernoulli likelihood with partial pooling CAN identify
  the interaction variance via the generative model
- Report ONLY if it converges and validates on synthetic data
- If it fails, say so honestly — do NOT fabricate numbers

Runs on all 6 Bansal conditions (focus reporting on Human; report all for completeness).

Runnable via: python -m twdf.experiments.e1_decomposition --config configs/e1_decomposition.yaml
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

import yaml

from twdf import __version__
from twdf.data.bansal import load_bansal
from twdf.metrics.variance_decomposition import split_half_reliability, variance_components_glmm


def run_decomposition_analysis(config: dict) -> dict:
    """
    Run variance decomposition analysis on all conditions.
    
    PRIMARY: Split-half reliability (well-identified on Bansal structure)
    OPTIONAL: GLMM variance components (corroboration if it converges)
    
    Returns:
        Results dict with split-half reliability (primary) and GLMM (if converged) per condition
    """
    print("=" * 80)
    print("E1 DECOMPOSITION ANALYSIS: Stable user trait vs user x task interaction")
    print("PRIMARY METHOD: Split-half reliability (well-identified)")
    print("OPTIONAL CORROBORATION: GLMM (if converges)")
    print(f"Package version: {__version__}")
    print(f"Run timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)
    
    data_config = config.get('data', {})
    analysis_config = config.get('analysis', {})
    
    # Seeds
    seed_glmm = analysis_config.get('seed_variance_components', 42)
    seed_split = analysis_config.get('seed_split_half', 43)
    n_splits = analysis_config.get('n_splits', 100)
    min_tasks = analysis_config.get('min_tasks_per_user', 8)
    
    # Load data (use 'all' task selection for maximum power)
    print("\nLoading Bansal data...")
    df = load_bansal(
        data_dir=Path(data_config.get('raw_dir', 'data/raw')),
        task_sample=None,
        ui_conditions=data_config.get('ui_conditions'),  # None = all 6
        task_selection='all'  # maximum data
    )
    
    ui_conditions = sorted(df['ui_condition'].unique())
    n_tasks = df['task_id'].nunique()
    n_trials_total = len(df)
    
    print(f"\nDataset summary:")
    print(f"  UI conditions: {len(ui_conditions)} ({', '.join(ui_conditions)})")
    print(f"  Tasks: {n_tasks}")
    print(f"  Total trials: {n_trials_total}")
    print(f"  Task selection: 'all' (maximum data)")
    
    # Run analyses for each condition
    # Run analyses for each condition
    results = {
        'conditions': {},
        'run_manifest': {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'package_version': __version__,
            'config_hash': hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16],
            'seed_glmm': seed_glmm,
            'seed_split_half': seed_split,
            'n_splits': n_splits,
            'min_tasks': min_tasks,
            'n_conditions': len(ui_conditions),
            'n_tasks_total': n_tasks,
            'n_trials_total': n_trials_total,
            'note': 'PRIMARY method: split-half reliability; GLMM is optional corroboration'
        }
    }
    
    for ui_cond in ui_conditions:
        print(f"\n{'=' * 80}")
        print(f"CONDITION: {ui_cond}")
        print(f"{'=' * 80}")
        
        # PRIMARY: Split-half reliability analysis
        print("\n1. PRIMARY: Split-half reliability...")
        try:
            split_result = split_half_reliability(
                trials=df,
                condition=ui_cond,
                n_splits=n_splits,
                seed=seed_split,
                min_tasks=min_tasks
            )
            
            print(f"   Spearman (half):     {split_result.spearman_mean:.3f} ± {split_result.spearman_sd:.3f}")
            print(f"   ICC(2,1):            {split_result.icc_mean:.3f} ± {split_result.icc_sd:.3f}")
            print(f"   Spearman-Brown (full): {split_result.spearman_brown_reliability:.3f} ± {split_result.spearman_brown_reliability_sd:.3f}")
            print(f"   STABLE USER SHARE:   {split_result.stable_user_share:.3f} [{split_result.stable_user_share_lower:.3f}, {split_result.stable_user_share_upper:.3f}]")
            print(f"   n_splits: {split_result.n_splits}")
            print(f"   n_users (>={min_tasks} tasks): {split_result.n_users}")
            
            split_data = {
                'spearman_mean': float(split_result.spearman_mean),
                'spearman_sd': float(split_result.spearman_sd),
                'icc_mean': float(split_result.icc_mean),
                'icc_sd': float(split_result.icc_sd),
                'spearman_brown_reliability': float(split_result.spearman_brown_reliability),
                'spearman_brown_reliability_sd': float(split_result.spearman_brown_reliability_sd),
                'stable_user_share': float(split_result.stable_user_share),
                'stable_user_share_lower': float(split_result.stable_user_share_lower),
                'stable_user_share_upper': float(split_result.stable_user_share_upper),
                'n_splits': int(split_result.n_splits),
                'n_users': int(split_result.n_users),
                'min_tasks_threshold': int(split_result.min_tasks_threshold)
            }
        except Exception as e:
            print(f"   ERROR: Split-half reliability failed: {e}")
            split_data = {'error': str(e)}
        
        # OPTIONAL CORROBORATION: GLMM variance components
        print("\n2. OPTIONAL CORROBORATION: GLMM variance components (bounded: maxiter=10)...")
        glmm_result = None
        try:
            glmm_result = variance_components_glmm(
                trials=df,
                condition=ui_cond,
                seed=seed_glmm,
                max_iter=10  # Heavily bounded for fast deterministic failure
            )
            
            if glmm_result is not None and glmm_result.converged:
                print(f"   sigma2_user:      {glmm_result.sigma2_user:.4f} ± {glmm_result.sigma2_user_sd:.4f}")
                print(f"   sigma2_task:      {glmm_result.sigma2_task:.4f} ± {glmm_result.sigma2_task_sd:.4f}")
                print(f"   sigma2_user_task: {glmm_result.sigma2_user_task:.4f} ± {glmm_result.sigma2_user_task_sd:.4f}")
                print(f"   stable_user_share: {glmm_result.stable_user_share:.3f} ± {glmm_result.stable_user_share_sd:.3f}")
                print(f"   n_users: {glmm_result.n_users}, n_tasks: {glmm_result.n_tasks}, n_trials: {glmm_result.n_trials}")
                print(f"   converged: {glmm_result.converged}")
                
                glmm_data = {
                    'sigma2_user': float(glmm_result.sigma2_user),
                    'sigma2_user_sd': float(glmm_result.sigma2_user_sd),
                    'sigma2_task': float(glmm_result.sigma2_task),
                    'sigma2_task_sd': float(glmm_result.sigma2_task_sd),
                    'sigma2_user_task': float(glmm_result.sigma2_user_task),
                    'sigma2_user_task_sd': float(glmm_result.sigma2_user_task_sd),
                    'stable_user_share': float(glmm_result.stable_user_share),
                    'stable_user_share_sd': float(glmm_result.stable_user_share_sd),
                    'n_users': int(glmm_result.n_users),
                    'n_tasks': int(glmm_result.n_tasks),
                    'n_trials': int(glmm_result.n_trials),
                    'converged': bool(glmm_result.converged)
                }
            else:
                print("   GLMM did not converge (acceptable; split-half is primary)")
                glmm_data = {'converged': False, 'note': 'Did not converge'}
        except Exception as e:
            print(f"   GLMM error (acceptable; split-half is primary): {e}")
            glmm_data = {'converged': False, 'error': str(e)}
        
        # Store results for this condition
        results['conditions'][ui_cond] = {
            'split_half_reliability': split_data,  # PRIMARY
            'glmm_variance_components': glmm_data  # OPTIONAL
        }
    
    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY ACROSS CONDITIONS (PRIMARY: Split-half reliability)")
    print(f"{'=' * 80}")
    
    print("\nPRIMARY RESULT: Stable user share from split-half reliability:")
    for cond in sorted(results['conditions'].keys()):
        split = results['conditions'][cond].get('split_half_reliability', {})
        if 'stable_user_share' in split:
            share = split['stable_user_share']
            lower = split['stable_user_share_lower']
            upper = split['stable_user_share_upper']
            print(f"  {cond:25s}: {share:.3f} [{lower:.3f}, {upper:.3f}]")
        else:
            print(f"  {cond:25s}: ERROR")
    
    print("\nSplit-half Spearman-Brown reliability (full-length):")
    for cond in sorted(results['conditions'].keys()):
        split = results['conditions'][cond].get('split_half_reliability', {})
        if 'spearman_brown_reliability' in split:
            rel = split['spearman_brown_reliability']
            rel_sd = split['spearman_brown_reliability_sd']
            print(f"  {cond:25s}: {rel:.3f} ± {rel_sd:.3f}")
        else:
            print(f"  {cond:25s}: ERROR")
    
    print("\nOPTIONAL: GLMM stable user share (if converged):")
    for cond in sorted(results['conditions'].keys()):
        glmm = results['conditions'][cond].get('glmm_variance_components', {})
        if glmm.get('converged'):
            share = glmm['stable_user_share']
            share_sd = glmm.get('stable_user_share_sd', 0.0)
            print(f"  {cond:25s}: {share:.3f} ± {share_sd:.3f}")
        else:
            print(f"  {cond:25s}: not converged")
    
    return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run E1 decomposition analysis")
    parser.add_argument('--config', required=True, help="Path to YAML config file")
    parser.add_argument('--output', default='results/e1_decomposition.json',
                       help="Output JSON path")
    
    args = parser.parse_args()
    
    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Run decomposition analysis
    results = run_decomposition_analysis(config)
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'=' * 80}")
    print(f"Decomposition results saved to: {output_path}")
    print(f"{'=' * 80}")


if __name__ == '__main__':
    main()
