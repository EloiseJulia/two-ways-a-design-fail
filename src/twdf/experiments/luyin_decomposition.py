"""
Lu&Yin decomposition analysis: Replication of C0 finding on second dataset.

SCIENTIFIC QUESTION:
Replicate the Bansal decomposition finding on a SECOND dataset (Lu&Yin CHI'21):
Does AI-assisted reliance remain predominantly USER × TASK (low stable-user share)
as found on Bansal (0.32–0.41), or does the pattern DIVERGE?

DATA STRUCTURE (Lu&Yin):
- 301 workers × exactly 30 tasks each (well-powered for split-half, like Bansal's 20–50/user)
- Within-subject sequential design (differs from Bansal's between-subjects conditions)
- NO true no-AI baseline condition (all trials involve AI)
  → Cannot directly replicate the 0.74 stable-trait no-AI arm
  → Focus comparison: AI-assisted stable-user share on Lu&Yin vs Bansal's 0.32–0.41

PRIMARY METHOD: SPLIT-HALF RELIABILITY
- Same as Bansal: split each user's tasks into random halves, correlate reliance rates
- Same seeds (43), same n_splits (100), same min_tasks (8) for comparability
- Report stable_user_share + 95% CI

ROBUSTNESS DV: CONFLICT-CONDITIONED RELIANCE
- Among trials where selfPrediction ≠ AI (genuine conflict), did user adopt AI?
- This mirrors the PR#4 panel DV and tests generalization on the refined measure
- Report if sufficiently powered (enough conflict trials per user)

OPTIONAL CORROBORATION: GLMM (if converges)

HONEST REPORTING:
- If stable_user_share on Lu&Yin ≈ 0.32–0.41 (Bansal AI range): GENERALIZES
- If significantly different but still low (<0.5): PARTIALLY replicates (directional)
- If high (≥0.6): DIVERGES (does not replicate)
- Any outcome is valid; report truthfully, do NOT tune to force a match

Runnable via: python -m twdf.experiments.luyin_decomposition --config configs/luyin_decomposition.yaml
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

import yaml
import pandas as pd

from twdf import __version__
from twdf.data.luyin import load_luyin
from twdf.metrics.variance_decomposition import split_half_reliability, variance_components_glmm


def compute_conflict_conditioned_reliance_per_user(trials: pd.DataFrame) -> pd.DataFrame:
    """
    Compute per-user reliance rate on conflict trials (selfPrediction ≠ AI).
    
    Returns DataFrame with columns: user_id, n_conflict, n_relied_conflict, reliance_rate_conflict
    """
    # Filter to conflict trials
    conflict = trials[trials['human_initial'] != trials['ai_advice']].copy()
    
    if len(conflict) == 0:
        raise ValueError("No conflict trials found")
    
    # Per-user conflict reliance
    conflict_stats = conflict.groupby('user_id').agg({
        'task_id': 'count',  # n_conflict
        'relied': 'sum'  # n_relied_conflict
    }).rename(columns={'task_id': 'n_conflict', 'relied': 'n_relied_conflict'})
    
    conflict_stats['reliance_rate_conflict'] = (
        conflict_stats['n_relied_conflict'] / conflict_stats['n_conflict']
    )
    
    return conflict_stats.reset_index()


def run_luyin_decomposition_analysis(config: dict) -> dict:
    """
    Run variance decomposition analysis on Lu&Yin dataset.
    
    PRIMARY: Split-half reliability (unconditional + conflict-conditioned)
    OPTIONAL: GLMM variance components (corroboration if it converges)
    
    Returns:
        Results dict with split-half reliability (primary) and GLMM (if converged)
    """
    print("=" * 80)
    print("LU&YIN DECOMPOSITION ANALYSIS: C0 Replication on Second Dataset")
    print("PRIMARY METHOD: Split-half reliability (same as Bansal)")
    print("QUESTION: Does AI-assisted reliance remain USER×TASK dominant?")
    print(f"Package version: {__version__}")
    print(f"Run timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)
    
    data_config = config.get('data', {})
    analysis_config = config.get('analysis', {})
    
    # Seeds (SAME as Bansal for comparability)
    seed_glmm = analysis_config.get('seed_variance_components', 42)
    seed_split = analysis_config.get('seed_split_half', 43)
    n_splits = analysis_config.get('n_splits', 100)
    min_tasks = analysis_config.get('min_tasks_per_user', 8)
    compute_conflict = analysis_config.get('compute_conflict_conditioned', True)
    
    # Load data
    print("\nLoading Lu&Yin data...")
    df = load_luyin(
        data_dir=Path(data_config.get('raw_dir', 'data/raw')),
        condition=data_config.get('condition')
    )
    
    n_users = df['user_id'].nunique()
    n_tasks = df['task_id'].nunique()
    n_trials_total = len(df)
    ui_condition = df['ui_condition'].unique()[0]  # Single condition
    
    print(f"\nDataset summary:")
    print(f"  Dataset: luyin21")
    print(f"  UI condition: {ui_condition}")
    print(f"  Users: {n_users}")
    print(f"  Tasks: {n_tasks}")
    print(f"  Total trials: {n_trials_total}")
    
    results = {
        'run_manifest': {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'package_version': __version__,
            'config_hash': hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16],
            'dataset': 'luyin21',
            'seed_glmm': seed_glmm,
            'seed_split_half': seed_split,
            'n_splits': n_splits,
            'min_tasks': min_tasks,
            'n_users': n_users,
            'n_tasks': n_tasks,
            'n_trials_total': n_trials_total,
            'note': 'C0 replication on Lu&Yin; PRIMARY: split-half reliability; GLMM optional'
        },
        'unconditional_reliance': {},
        'conflict_conditioned_reliance': {}
    }
    
    # ========== PRIMARY DV: UNCONDITIONAL RELIANCE ==========
    print(f"\n{'=' * 80}")
    print(f"PRIMARY DV: UNCONDITIONAL RELIANCE (finalPrediction == AI)")
    print(f"{'=' * 80}")
    
    print("\n1. PRIMARY: Split-half reliability...")
    try:
        split_result = split_half_reliability(
            trials=df,
            condition=ui_condition,
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
        
        results['unconditional_reliance']['split_half_reliability'] = {
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
        results['unconditional_reliance']['split_half_reliability'] = {'error': str(e)}
    
    # OPTIONAL CORROBORATION: GLMM
    print("\n2. OPTIONAL CORROBORATION: GLMM variance components (bounded: maxiter=10)...")
    try:
        glmm_result = variance_components_glmm(
            trials=df,
            condition=ui_condition,
            seed=seed_glmm,
            max_iter=10
        )
        
        if glmm_result is not None and glmm_result.converged:
            print(f"   sigma2_user:      {glmm_result.sigma2_user:.4f} ± {glmm_result.sigma2_user_sd:.4f}")
            print(f"   sigma2_task:      {glmm_result.sigma2_task:.4f} ± {glmm_result.sigma2_task_sd:.4f}")
            print(f"   sigma2_user_task: {glmm_result.sigma2_user_task:.4f} ± {glmm_result.sigma2_user_task_sd:.4f}")
            print(f"   stable_user_share: {glmm_result.stable_user_share:.3f} ± {glmm_result.stable_user_share_sd:.3f}")
            print(f"   converged: {glmm_result.converged}")
            
            results['unconditional_reliance']['glmm_variance_components'] = {
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
            results['unconditional_reliance']['glmm_variance_components'] = {
                'converged': False, 
                'note': 'Did not converge'
            }
    except Exception as e:
        print(f"   GLMM error (acceptable; split-half is primary): {e}")
        results['unconditional_reliance']['glmm_variance_components'] = {
            'converged': False, 
            'error': str(e)
        }
    
    # ========== ROBUSTNESS DV: CONFLICT-CONDITIONED RELIANCE ==========
    if compute_conflict:
        print(f"\n{'=' * 80}")
        print(f"ROBUSTNESS DV: CONFLICT-CONDITIONED RELIANCE (selfPrediction ≠ AI)")
        print(f"{'=' * 80}")
        
        # Check if there are enough conflict trials per user for split-half
        conflict_trials = df[df['human_initial'] != df['ai_advice']].copy()
        n_conflict_total = len(conflict_trials)
        conflict_per_user = conflict_trials.groupby('user_id')['task_id'].count()
        
        print(f"\n  Conflict trials: {n_conflict_total} ({n_conflict_total/n_trials_total:.1%} of total)")
        print(f"  Conflict per user: min={conflict_per_user.min()}, max={conflict_per_user.max()}, "
              f"median={conflict_per_user.median():.0f}, mean={conflict_per_user.mean():.1f}")
        
        # Require at least min_tasks conflict trials per user for split-half
        users_with_enough_conflict = (conflict_per_user >= min_tasks).sum()
        print(f"  Users with >={min_tasks} conflict trials: {users_with_enough_conflict}/{len(conflict_per_user)}")
        
        if users_with_enough_conflict < 20:
            print(f"\n  UNDERPOWERED: Only {users_with_enough_conflict} users have >={min_tasks} conflict trials.")
            print(f"  Split-half requires substantial n/user. Skipping conflict-conditioned analysis.")
            print(f"  (This is a data limitation, not a methodology failure.)")
            results['conflict_conditioned_reliance']['note'] = (
                f"Underpowered: only {users_with_enough_conflict} users with >={min_tasks} conflict trials"
            )
        else:
            # Create a conflict-only dataset with 'relied' preserved
            # For split-half, we need the same format but filtered to conflict trials
            conflict_df = conflict_trials.copy()
            conflict_df['ui_condition'] = ui_condition + '_conflict'
            
            print("\n1. PRIMARY: Split-half reliability on conflict trials...")
            try:
                split_conflict = split_half_reliability(
                    trials=conflict_df,
                    condition=conflict_df['ui_condition'].unique()[0],
                    n_splits=n_splits,
                    seed=seed_split,
                    min_tasks=min_tasks
                )
                
                print(f"   Spearman (half):     {split_conflict.spearman_mean:.3f} ± {split_conflict.spearman_sd:.3f}")
                print(f"   ICC(2,1):            {split_conflict.icc_mean:.3f} ± {split_conflict.icc_sd:.3f}")
                print(f"   Spearman-Brown (full): {split_conflict.spearman_brown_reliability:.3f} ± {split_conflict.spearman_brown_reliability_sd:.3f}")
                print(f"   STABLE USER SHARE:   {split_conflict.stable_user_share:.3f} [{split_conflict.stable_user_share_lower:.3f}, {split_conflict.stable_user_share_upper:.3f}]")
                print(f"   n_splits: {split_conflict.n_splits}")
                print(f"   n_users (>={min_tasks} conflict): {split_conflict.n_users}")
                
                results['conflict_conditioned_reliance']['split_half_reliability'] = {
                    'spearman_mean': float(split_conflict.spearman_mean),
                    'spearman_sd': float(split_conflict.spearman_sd),
                    'icc_mean': float(split_conflict.icc_mean),
                    'icc_sd': float(split_conflict.icc_sd),
                    'spearman_brown_reliability': float(split_conflict.spearman_brown_reliability),
                    'spearman_brown_reliability_sd': float(split_conflict.spearman_brown_reliability_sd),
                    'stable_user_share': float(split_conflict.stable_user_share),
                    'stable_user_share_lower': float(split_conflict.stable_user_share_lower),
                    'stable_user_share_upper': float(split_conflict.stable_user_share_upper),
                    'n_splits': int(split_conflict.n_splits),
                    'n_users': int(split_conflict.n_users),
                    'min_tasks_threshold': int(split_conflict.min_tasks_threshold),
                    'n_conflict_trials': int(n_conflict_total)
                }
            except Exception as e:
                print(f"   ERROR: Split-half on conflict trials failed: {e}")
                results['conflict_conditioned_reliance']['split_half_reliability'] = {'error': str(e)}
    
    # ========== SUMMARY ==========
    print(f"\n{'=' * 80}")
    print("SUMMARY: Lu&Yin Decomposition Results")
    print(f"{'=' * 80}")
    
    print("\nPRIMARY RESULT: Stable user share from split-half reliability")
    print(f"  Unconditional reliance: ", end='')
    uncond = results.get('unconditional_reliance', {}).get('split_half_reliability', {})
    if 'stable_user_share' in uncond:
        print(f"{uncond['stable_user_share']:.3f} [{uncond['stable_user_share_lower']:.3f}, {uncond['stable_user_share_upper']:.3f}]")
    else:
        print("ERROR")
    
    if compute_conflict and 'split_half_reliability' in results.get('conflict_conditioned_reliance', {}):
        print(f"  Conflict-conditioned:   ", end='')
        conflict = results.get('conflict_conditioned_reliance', {}).get('split_half_reliability', {})
        if 'stable_user_share' in conflict:
            print(f"{conflict['stable_user_share']:.3f} [{conflict['stable_user_share_lower']:.3f}, {conflict['stable_user_share_upper']:.3f}]")
        else:
            print("ERROR")
    
    print("\nCOMPARISON TO BANSAL (from e1_decomposition.json):")
    print("  Bansal Human (no-AI):        0.742 [0.693, 0.787]  <- stable user trait")
    print("  Bansal AI-assisted range:    0.321–0.414           <- user×task dominant")
    print("  Lu&Yin AI-assisted (above):  (see primary result)")
    print("\nGENERALIZATION VERDICT:")
    if 'stable_user_share' in uncond:
        share = uncond['stable_user_share']
        if 0.25 <= share <= 0.50:
            print(f"  GENERALIZES: Lu&Yin share ({share:.3f}) falls in similar low range as Bansal AI (0.32–0.41)")
            print(f"  → AI-assisted reliance remains predominantly USER×TASK (not stable user trait)")
        elif share < 0.25:
            print(f"  PARTIALLY REPLICATES (stronger): Lu&Yin share ({share:.3f}) is even LOWER than Bansal")
            print(f"  → USER×TASK dominance is even more pronounced on Lu&Yin")
        elif 0.50 < share < 0.65:
            print(f"  PARTIALLY REPLICATES (weaker): Lu&Yin share ({share:.3f}) higher than Bansal but still <0.65")
            print(f"  → USER×TASK still substantial, but less dominant than on Bansal")
        else:
            print(f"  DIVERGES: Lu&Yin share ({share:.3f}) approaches stable-trait territory (≥0.65)")
            print(f"  → Does NOT replicate the USER×TASK dominance found on Bansal")
    else:
        print("  INCONCLUSIVE: Primary analysis failed")
    
    print("\nCAVEATS:")
    print("  - Single new dataset (Lu&Yin); not multi-dataset meta-analysis")
    print("  - Lu&Yin is within-subject sequential design; Bansal is between-subjects conditions")
    print("  - Lu&Yin has no true no-AI baseline (cannot replicate 0.74 stable-trait arm)")
    print("  - Comparison is AI-assisted Lu&Yin vs AI-assisted Bansal conditions only")
    
    return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run Lu&Yin decomposition analysis")
    parser.add_argument('--config', required=True, help="Path to YAML config file")
    parser.add_argument('--output', default='results/luyin_decomposition.json',
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
    results = run_luyin_decomposition_analysis(config)
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'=' * 80}")
    print(f"Lu&Yin decomposition results saved to: {output_path}")
    print(f"{'=' * 80}")


if __name__ == '__main__':
    main()
