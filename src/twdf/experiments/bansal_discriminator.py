"""
Bansal Discriminator: C0 Mechanism Test

SCIENTIFIC QUESTION (DECISIVE test for C0 co-anchor):
Does Bansal's low AI-assisted stable_user_share (~0.32-0.41, user×task dominant)
PERSIST under Lu&Yin-matched homogeneity (single domain, matched AI-accuracy regime,
comparable tasks/user), or does it COLLAPSE to trait-stable (~0.80)?

DECISION RULE (PI-directed):
- PERSISTS (share stays low ~0.3-0.5 under matched homogeneity) → controllable
  regime confounds NOT the driver → residual gap is likely the UNCONTROLLABLE
  sequential-feedback difference → **recommend DEMOTE C0** to single-dataset finding;
  lean on C1 (panel).
- COLLAPSES (share rises toward ~0.7-0.8 under matched homogeneity) → task/
  difficulty/accuracy homogeneity DOES drive the share → **recommend reframe C0
  as design-dependent** on identified ground.

HONEST CAVEAT: Sequential-feedback is an UNCONTROLLABLE confound here (Bansal is
static). A persisting low share does NOT prove "regime doesn't matter" in general;
it only rules out the controllable confounds tested here.

METHODOLOGY:
- Reuse EXISTING split_half_reliability() (PRIMARY method, seed=43, n_splits=100,
  min_tasks=8)
- Matched-subset decompositions:
  1. By domain (difficulty homogeneity): beer, amzbook, **lsat** (Lu&Yin-matched)
  2. By AI-accuracy band: tasks with AI-acc ~0.60-0.75 (Lu&Yin's ~0.70)
  3. By tasks/user: subsample to ~30 (Lu&Yin's count, robustness check)
  4. Heterogeneity gradient: full → domain → accuracy-band → joint-matched
- Report ALL subsets with full structure (n_users, tasks/user, reliance, AI-acc,
  stable_user_share + 95% CI)

PRE-SPECIFICATION: All subsets defined in config BEFORE seeing results. Report ALL.

Runnable via: python -m twdf.experiments.bansal_discriminator --config configs/bansal_discriminator.yaml
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
from typing import Optional

import yaml
import pandas as pd
import numpy as np

from twdf import __version__
from twdf.data.bansal import load_bansal
from twdf.metrics.variance_decomposition import split_half_reliability


def filter_subset(df: pd.DataFrame, subset_config: dict) -> pd.DataFrame:
    """
    Filter dataframe to subset based on config.
    
    Args:
        df: Full canonical dataframe
        subset_config: Subset configuration dict
    
    Returns:
        Filtered dataframe for this subset
    """
    filter_type = subset_config.get('filter_type', 'none')
    
    if filter_type == 'none':
        # Full data (no filter)
        return df.copy()
    
    elif filter_type == 'domain':
        # Filter to specific domain (beer/amzbook/lsat)
        domain = subset_config['domain']
        # Domain is stored in extra['task']
        filtered = df[df['extra'].apply(lambda x: x['task'] == domain)].copy()
        return filtered
    
    elif filter_type == 'ai_accuracy_band':
        # Filter to tasks with AI accuracy in specified band
        ai_acc_min = subset_config['ai_acc_min']
        ai_acc_max = subset_config['ai_acc_max']
        
        # Compute per-task AI accuracy
        task_ai_acc = df.groupby('task_id')['ai_correct'].mean()
        valid_tasks = task_ai_acc[(task_ai_acc >= ai_acc_min) & (task_ai_acc <= ai_acc_max)].index
        
        filtered = df[df['task_id'].isin(valid_tasks)].copy()
        return filtered
    
    elif filter_type == 'subsample_tasks_per_user':
        # Subsample each user's tasks to target_tasks (robustness check)
        target_tasks = subset_config['target_tasks']
        seed = subset_config.get('seed', 43)  # deterministic
        
        rng = np.random.RandomState(seed)
        sampled_rows = []
        
        for user_id in df['user_id'].unique():
            user_df = df[df['user_id'] == user_id]
            user_tasks = user_df['task_id'].unique()
            
            if len(user_tasks) <= target_tasks:
                # Keep all tasks if user has <= target
                sampled_rows.append(user_df)
            else:
                # Random sample target_tasks tasks
                sampled_tasks = rng.choice(user_tasks, size=target_tasks, replace=False)
                sampled_rows.append(user_df[user_df['task_id'].isin(sampled_tasks)])
        
        filtered = pd.concat(sampled_rows, ignore_index=True)
        return filtered
    
    elif filter_type == 'domain_and_accuracy':
        # Joint filter: domain + AI-accuracy band (strictest Lu&Yin match)
        domain = subset_config['domain']
        ai_acc_min = subset_config['ai_acc_min']
        ai_acc_max = subset_config['ai_acc_max']
        
        # Filter to domain
        filtered = df[df['extra'].apply(lambda x: x['task'] == domain)].copy()
        
        # Then filter to AI-accuracy band
        task_ai_acc = filtered.groupby('task_id')['ai_correct'].mean()
        valid_tasks = task_ai_acc[(task_ai_acc >= ai_acc_min) & (task_ai_acc <= ai_acc_max)].index
        
        filtered = filtered[filtered['task_id'].isin(valid_tasks)].copy()
        return filtered
    
    else:
        raise ValueError(f"Unknown filter_type: {filter_type}")


def compute_subset_structure(df: pd.DataFrame) -> dict:
    """
    Compute structural statistics for a subset.
    
    Returns:
        Dict with n_users, n_tasks, n_trials, tasks_per_user_median, 
        tasks_per_user_mean, reliance_rate, ai_accuracy
    """
    tasks_per_user = df.groupby('user_id')['task_id'].nunique()
    
    return {
        'n_users': int(df['user_id'].nunique()),
        'n_tasks': int(df['task_id'].nunique()),
        'n_trials': int(len(df)),
        'tasks_per_user_median': float(tasks_per_user.median()),
        'tasks_per_user_mean': float(tasks_per_user.mean()),
        'tasks_per_user_min': int(tasks_per_user.min()),
        'tasks_per_user_max': int(tasks_per_user.max()),
        'reliance_rate': float(df['relied'].mean()),
        'ai_accuracy': float(df['ai_correct'].mean()),
    }


def run_discriminator_analysis(config: dict) -> dict:
    """
    Run Bansal discriminator analysis: matched-subset decompositions.
    
    For each pre-specified subset, compute split_half_reliability and report
    full structure alongside Lu&Yin (0.80) and Bansal-full (0.32-0.41) benchmarks.
    
    Returns:
        Results dict with per-subset stable_user_share + structure + verdict
    """
    print("=" * 80)
    print("BANSAL DISCRIMINATOR: C0 Mechanism Test")
    print("=" * 80)
    print("QUESTION: Does Bansal's low AI-assisted stable_user_share PERSIST or")
    print("          COLLAPSE under Lu&Yin-matched homogeneity?")
    print(f"Package version: {__version__}")
    print(f"Run timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)
    
    data_config = config.get('data', {})
    analysis_config = config.get('analysis', {})
    
    # Seeds and params
    seed_split = analysis_config.get('seed_split_half', 43)
    n_splits = analysis_config.get('n_splits', 100)
    min_tasks = analysis_config.get('min_tasks_per_user', 8)
    
    # Load full Bansal data (AI-assisted conditions)
    # Use Conf.+Adaptive as the representative AI condition (same as e1_decomposition focus)
    # This avoids pooling 1338 users which makes split-half very slow
    print("\nLoading Bansal data (representative AI condition: Conf.+Adaptive)...")
    ai_condition_focus = 'Conf.+Adaptive'  # Representative condition, same as original pair
    
    df = load_bansal(
        data_dir=Path(data_config.get('raw_dir', 'data/raw')),
        task_sample=None,
        ui_conditions=[ai_condition_focus],
        task_selection='all'  # maximum data
    )
    
    print(f"\nFull AI-assisted dataset (Conf.+Adaptive):")
    print(f"  Condition: {ai_condition_focus}")
    print(f"  Users: {df['user_id'].nunique()}")
    print(f"  Tasks: {df['task_id'].nunique()}")
    print(f"  Trials: {len(df)}")
    print(f"  Note: Using Conf.+Adaptive as representative AI condition (avoids pooling 1338 users)")
    
    # Also load Human (no-AI) baseline for reference
    print("\nLoading Human (no-AI) baseline for reference...")
    df_human = load_bansal(
        data_dir=Path(data_config.get('raw_dir', 'data/raw')),
        task_sample=None,
        ui_conditions=['Human'],
        task_selection='all'
    )
    
    # Get benchmarks from config
    benchmarks = analysis_config.get('benchmarks', {})
    
    # Run analyses on each pre-specified subset
    subsets_config = analysis_config.get('subsets', {})
    
    results = {
        'subsets': {},
        'benchmarks': benchmarks,
        'run_manifest': {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'package_version': __version__,
            'config_hash': hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16],
            'seed_split_half': seed_split,
            'n_splits': n_splits,
            'min_tasks_per_user': min_tasks,
            'ai_condition_focus': ai_condition_focus,
            'n_subsets': len(subsets_config),
            'note': 'C0 mechanism test: matched-subset decompositions to test PERSIST vs COLLAPSE (using Conf.+Adaptive as representative AI condition)'
        }
    }
    
    # Process each subset
    for subset_name, subset_config in subsets_config.items():
        print(f"\n{'=' * 80}")
        print(f"SUBSET: {subset_name}")
        print(f"Description: {subset_config['description']}")
        print(f"{'=' * 80}")
        
        try:
            # Filter to subset
            df_subset = filter_subset(df, subset_config)
            
            if len(df_subset) == 0:
                print(f"  ERROR: No data after filtering")
                results['subsets'][subset_name] = {
                    'description': subset_config['description'],
                    'filter_config': subset_config,
                    'error': 'No data after filtering'
                }
                continue
            
            # Compute structure
            structure = compute_subset_structure(df_subset)
            
            print(f"\n  Subset structure:")
            print(f"    Users: {structure['n_users']}")
            print(f"    Tasks: {structure['n_tasks']}")
            print(f"    Trials: {structure['n_trials']}")
            print(f"    Tasks/user: median={structure['tasks_per_user_median']:.1f}, "
                  f"mean={structure['tasks_per_user_mean']:.1f}, "
                  f"range=[{structure['tasks_per_user_min']}, {structure['tasks_per_user_max']}]")
            print(f"    Reliance rate: {structure['reliance_rate']:.3f}")
            print(f"    AI accuracy: {structure['ai_accuracy']:.3f}")
            
            # Check if enough users with min_tasks
            tasks_per_user = df_subset.groupby('user_id')['task_id'].nunique()
            eligible_users = (tasks_per_user >= min_tasks).sum()
            
            if eligible_users < 2:
                print(f"  ERROR: Only {eligible_users} users with >={min_tasks} tasks (need >=2)")
                results['subsets'][subset_name] = {
                    'description': subset_config['description'],
                    'filter_config': subset_config,
                    'structure': structure,
                    'error': f'Only {eligible_users} users with >={min_tasks} tasks'
                }
                continue
            
            # Compute split-half reliability on representative AI condition (Conf.+Adaptive)
            print(f"\n  Computing split-half reliability (condition: {ai_condition_focus})...")
            
            split_result = split_half_reliability(
                trials=df_subset,
                condition=ai_condition_focus,
                n_splits=n_splits,
                seed=seed_split,
                min_tasks=min_tasks
            )
            
            print(f"\n  Split-half reliability results:")
            print(f"    Spearman (half):     {split_result.spearman_mean:.3f} ± {split_result.spearman_sd:.3f}")
            print(f"    ICC(2,1):            {split_result.icc_mean:.3f} ± {split_result.icc_sd:.3f}")
            print(f"    Spearman-Brown (full): {split_result.spearman_brown_reliability:.3f} ± {split_result.spearman_brown_reliability_sd:.3f}")
            print(f"    STABLE USER SHARE:   {split_result.stable_user_share:.3f} "
                  f"[{split_result.stable_user_share_lower:.3f}, {split_result.stable_user_share_upper:.3f}]")
            print(f"    n_splits: {split_result.n_splits}")
            print(f"    n_users (>={min_tasks} tasks): {split_result.n_users}")
            
            # Compare to benchmarks
            print(f"\n  Comparison to benchmarks:")
            print(f"    Lu&Yin AI-assisted:     {benchmarks.get('luyin_ai_assisted', 'N/A')} "
                  f"[{benchmarks.get('luyin_ci_lower', 'N/A')}, {benchmarks.get('luyin_ci_upper', 'N/A')}]")
            print(f"    Bansal Human (no-AI):   {benchmarks.get('bansal_human_no_ai', 'N/A')} "
                  f"[{benchmarks.get('bansal_human_ci_lower', 'N/A')}, {benchmarks.get('bansal_human_ci_upper', 'N/A')}]")
            print(f"    Bansal AI-assisted range: {benchmarks.get('bansal_ai_assisted_min', 'N/A')} - "
                  f"{benchmarks.get('bansal_ai_assisted_max', 'N/A')}")
            print(f"    THIS SUBSET:            {split_result.stable_user_share:.3f} "
                  f"[{split_result.stable_user_share_lower:.3f}, {split_result.stable_user_share_upper:.3f}]")
            
            # Save results
            results['subsets'][subset_name] = {
                'description': subset_config['description'],
                'filter_config': subset_config,
                'structure': structure,
                'split_half_reliability': {
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
            }
            
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            results['subsets'][subset_name] = {
                'description': subset_config['description'],
                'filter_config': subset_config,
                'error': str(e)
            }
    
    # Compute verdict based on results
    print(f"\n{'=' * 80}")
    print("VERDICT COMPUTATION")
    print(f"{'=' * 80}")
    
    # Look at key subsets for verdict
    lsat_share = results['subsets'].get('domain_lsat', {}).get('split_half_reliability', {}).get('stable_user_share')
    lsat_matched_share = results['subsets'].get('lsat_matched', {}).get('split_half_reliability', {}).get('stable_user_share')
    full_ai_share = results['subsets'].get('full_ai', {}).get('split_half_reliability', {}).get('stable_user_share')
    
    # Decision rule thresholds
    PERSIST_THRESHOLD_UPPER = 0.50  # If share stays below this, it's still user×task dominant
    COLLAPSE_THRESHOLD_LOWER = 0.70  # If share rises above this, it's approaching trait-stable
    
    verdict_parts = []
    
    if lsat_share is not None:
        print(f"\nLSAT domain (Lu&Yin-matched regime):")
        print(f"  stable_user_share = {lsat_share:.3f}")
        
        if lsat_share <= PERSIST_THRESHOLD_UPPER:
            verdict_parts.append("LSAT domain (Lu&Yin-matched regime) shows PERSISTENT low share "
                                f"({lsat_share:.3f} ≤ {PERSIST_THRESHOLD_UPPER})")
        elif lsat_share >= COLLAPSE_THRESHOLD_LOWER:
            verdict_parts.append("LSAT domain (Lu&Yin-matched regime) shows COLLAPSE to trait-stable "
                                f"({lsat_share:.3f} ≥ {COLLAPSE_THRESHOLD_LOWER})")
        else:
            verdict_parts.append("LSAT domain (Lu&Yin-matched regime) shows INTERMEDIATE share "
                                f"({lsat_share:.3f}, between {PERSIST_THRESHOLD_UPPER} and {COLLAPSE_THRESHOLD_LOWER})")
    
    if lsat_matched_share is not None:
        print(f"\nLSAT + AI-accuracy matched (strictest Lu&Yin match):")
        print(f"  stable_user_share = {lsat_matched_share:.3f}")
        
        if lsat_matched_share <= PERSIST_THRESHOLD_UPPER:
            verdict_parts.append("LSAT+AI-acc matched (strictest) shows PERSISTENT low share "
                                f"({lsat_matched_share:.3f} ≤ {PERSIST_THRESHOLD_UPPER})")
        elif lsat_matched_share >= COLLAPSE_THRESHOLD_LOWER:
            verdict_parts.append("LSAT+AI-acc matched (strictest) shows COLLAPSE to trait-stable "
                                f"({lsat_matched_share:.3f} ≥ {COLLAPSE_THRESHOLD_LOWER})")
        else:
            verdict_parts.append("LSAT+AI-acc matched (strictest) shows INTERMEDIATE share "
                                f"({lsat_matched_share:.3f}, between {PERSIST_THRESHOLD_UPPER} and {COLLAPSE_THRESHOLD_LOWER})")
    
    # Overall verdict
    if any('PERSISTENT' in v for v in verdict_parts):
        verdict_summary = "PERSISTS"
        recommendation = ("User×task dominance PERSISTS under Lu&Yin-matched homogeneity. "
                         "The controllable regime confounds (task/difficulty/accuracy homogeneity) "
                         "are NOT the primary driver of the low share. The residual gap is likely "
                         "the UNCONTROLLABLE sequential-feedback difference (Bansal is static, "
                         "Lu&Yin is sequential). RECOMMENDATION: **DEMOTE C0** to a single-dataset "
                         "finding (Bansal only); lean on C1 (panel two-axis) as the primary contribution.")
    elif any('COLLAPSE' in v for v in verdict_parts):
        verdict_summary = "COLLAPSES"
        recommendation = ("User×task dominance COLLAPSES to trait-stable under Lu&Yin-matched homogeneity. "
                         "Task/difficulty/accuracy homogeneity DOES drive the stable_user_share. "
                         "RECOMMENDATION: **Reframe C0 as design-dependent** on identified controllable "
                         "ground (task heterogeneity, difficulty spread, AI-accuracy regime).")
    else:
        verdict_summary = "INTERMEDIATE"
        recommendation = ("Results are INTERMEDIATE — share rises modestly but does not fully collapse. "
                         "This suggests partial regime effects but not a complete collapse. "
                         "RECOMMENDATION: Exercise caution; consider a nuanced framing that acknowledges "
                         "both within-dataset (Bansal) and regime-dependent (homogeneity) effects. "
                         "May need additional data or replication to resolve decisively.")
    
    results['verdict'] = {
        'summary': verdict_summary,
        'details': verdict_parts,
        'recommendation': recommendation,
        'decision_rule': {
            'persist_threshold_upper': PERSIST_THRESHOLD_UPPER,
            'collapse_threshold_lower': COLLAPSE_THRESHOLD_LOWER,
            'note': 'Thresholds defined by PI-directed decision rule (see config comments)'
        }
    }
    
    print(f"\nVERDICT: {verdict_summary}")
    print(f"\nRECOMMENDATION:")
    print(f"  {recommendation}")
    
    print(f"\n{'=' * 80}")
    print("HONEST CAVEATS:")
    print("  - Sequential-feedback is an UNCONTROLLABLE confound (Bansal is static).")
    print("  - A PERSIST verdict does NOT prove 'regime doesn't matter' in general;")
    print("    it only rules out the controllable confounds tested here.")
    print("  - A COLLAPSE verdict isolates controllable regime effects but cannot")
    print("    speak to sequential-feedback effects without additional data.")
    print(f"{'=' * 80}")
    
    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Bansal discriminator: C0 mechanism test (matched-subset decompositions)'
    )
    parser.add_argument('--config', type=str, required=True,
                       help='Path to config YAML file (e.g., configs/bansal_discriminator.yaml)')
    
    args = parser.parse_args()
    
    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Run analysis
    results = run_discriminator_analysis(config)
    
    # Save results
    output_file = Path(config.get('output', {}).get('results_file', 'results/bansal_discriminator.json'))
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print("\nDONE.")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
