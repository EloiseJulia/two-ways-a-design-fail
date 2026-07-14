"""
Bansal et al. CHI'21 dataset loader.

Paper: "Does the Whole Exceed its Parts? The Effect of AI Explanations on 
       Complementary Team Performance"
DOI: 10.1145/3411764.3445717
Repo: https://github.com/uw-hai/Complementary-Performance

Loads raw per-trial data and converts to canonical schema (INTERFACES.md §1).
"""

import os
from pathlib import Path
from typing import Optional
import urllib.request

import pandas as pd
import numpy as np


# Verified download URL from Gate 1 report
BANSAL_URL = "https://raw.githubusercontent.com/uw-hai/Complementary-Performance/main/experiment-data/decision-result-filter.csv"

# Expected columns from real data (verified 2026-07-14)
EXPECTED_COLS = ['assignmentId', 'questionId', 'task', 'condition', 'time', 
                 'choice', 'y', 'pred', 'conf', 'conf2', 'pred2']


def download_if_missing(data_dir: Path) -> Path:
    """
    Download Bansal dataset to data/raw/ if not already present.
    
    Returns path to the downloaded CSV file.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_path = data_dir / "bansal_chi21_decisions.csv"
    
    if csv_path.exists():
        print(f"Dataset already exists: {csv_path}")
        return csv_path
    
    print(f"Downloading Bansal dataset from {BANSAL_URL}...")
    urllib.request.urlretrieve(BANSAL_URL, csv_path)
    print(f"Downloaded to {csv_path}")
    
    return csv_path


def load_bansal(data_dir: Optional[Path] = None,
                task_sample: Optional[list[str]] = None,
                ui_conditions: Optional[list[str] | tuple[str, str]] = None,
                min_tasks_per_domain: Optional[int] = None) -> pd.DataFrame:
    """
    Load Bansal CHI'21 data and convert to canonical per-trial schema.
    
    Column mapping (verified real headers):
    - assignmentId -> user_id
    - questionId -> task_id
    - condition -> ui_condition
    - choice -> human_final
    - y -> ground_truth
    - pred -> ai_advice
    - conf -> confidence
    
    Derived fields:
    - relied: human_final == ai_advice
    - ai_correct: ai_advice == ground_truth
    - task_difficulty: derived from task domain (beer/amzbook/lsat in extra['task'])
    
    Args:
        data_dir: Directory containing raw data (default: ./data/raw)
        task_sample: List of questionIds to keep (default: auto-select shared tasks)
        ui_conditions: List or tuple of condition names to keep.
                      None = all 6 conditions ('Human', 'Conf.', 'Conf.+Single',
                      'Conf.+Double', 'Conf.+Adaptive', 'Conf.+Adaptive (Expert)')
                      Tuple of 2 = backward compatible with v0 (control, treatment)
                      List = multi-condition for E1 multicond
        min_tasks_per_domain: Minimum shared tasks per domain (beer/amzbook/lsat)
                             for difficulty control. None = no constraint.
    
    Returns:
        DataFrame with canonical schema per INTERFACES.md §1
    """
    if data_dir is None:
        data_dir = Path("data/raw")
    
    csv_path = download_if_missing(data_dir)
    
    # Load raw data
    # Specify dtype for mixed-type columns to avoid DtypeWarning
    df = pd.read_csv(csv_path, dtype={'choice': str, 'y': str, 'pred': str, 'pred2': str})
    
    # Verify expected columns
    missing = set(EXPECTED_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")
    
    print(f"Loaded {len(df)} rows from Bansal dataset")
    print(f"Available conditions: {sorted(df['condition'].unique())}")
    print(f"Available tasks (domains): {sorted(df['task'].unique())}")
    print(f"Question IDs range: {df['questionId'].min()} - {df['questionId'].max()}")
    
    # Select UI conditions (multi-condition support with backward compatibility)
    # Available conditions from the dataset:
    # 'Conf.', 'Conf.+Adaptive', 'Conf.+Adaptive (Expert)', 'Conf.+Double', 'Conf.+Single', 'Human'
    if ui_conditions is None:
        # Default: all 6 conditions for multi-condition E1
        ui_conditions = ['Human', 'Conf.', 'Conf.+Single', 'Conf.+Double', 
                        'Conf.+Adaptive', 'Conf.+Adaptive (Expert)']
        print(f"Selected all {len(ui_conditions)} UI conditions (default)")
    elif isinstance(ui_conditions, tuple) and len(ui_conditions) == 2:
        # Backward compatible with v0: tuple of (control, treatment)
        ui_conditions = list(ui_conditions)
        print(f"Selected UI pair (v0 mode): {ui_conditions[0]} vs {ui_conditions[1]}")
    else:
        # Multi-condition list
        print(f"Selected {len(ui_conditions)} UI conditions: {ui_conditions}")
    
    # Ensure sorted order for determinism
    ui_conditions = sorted(ui_conditions)
    
    # Filter to selected conditions
    df = df[df['condition'].isin(ui_conditions)].copy()
    print(f"After condition filter: {len(df)} rows")
    
    # Select task sample - tasks shared across ALL selected conditions
    if task_sample is None:
        # Find questionIds that appear in ALL selected conditions
        condition_tasks = [set(df[df['condition'] == cond]['questionId'].unique()) 
                          for cond in ui_conditions]
        shared_qs = set.intersection(*condition_tasks) if condition_tasks else set()
        
        # If min_tasks_per_domain specified, ensure representation across domains
        if min_tasks_per_domain is not None and min_tasks_per_domain > 0:
            # Group shared tasks by domain
            shared_df = df[df['questionId'].isin(shared_qs)]
            domain_tasks = {}
            for domain in shared_df['task'].unique():
                domain_qs = sorted(shared_df[shared_df['task'] == domain]['questionId'].unique())
                domain_tasks[domain] = domain_qs
            
            # Select min_tasks_per_domain from each domain
            selected = []
            for domain in sorted(domain_tasks.keys()):  # sorted for determinism
                selected.extend(domain_tasks[domain][:min_tasks_per_domain])
            task_sample = sorted(set(selected))
            print(f"Auto-selected {len(task_sample)} shared tasks ({min_tasks_per_domain}/domain):")
            for domain in sorted(domain_tasks.keys()):
                domain_selected = [q for q in task_sample if q in domain_tasks[domain]]
                print(f"  {domain}: {len(domain_selected)} tasks")
        else:
            # Just take first N shared tasks (sorted for determinism)
            task_sample = sorted(shared_qs)[:10] if len(shared_qs) >= 10 else sorted(shared_qs)
            print(f"Auto-selected {len(task_sample)} shared tasks: {task_sample}")
    
    df = df[df['questionId'].isin(task_sample)].copy()
    print(f"After task filter: {len(df)} rows")
    
    # Map task domain to difficulty proxy
    # beer/amzbook/lsat have different inherent difficulty
    # We'll use domain as a categorical difficulty indicator
    domain_difficulty = {
        'beer': 1.0,      # easiest (concrete, sensory)
        'amzbook': 2.0,   # medium (semantic, subjective)
        'lsat': 3.0       # hardest (abstract reasoning)
    }
    
    # Convert to canonical schema
    canonical = pd.DataFrame({
        'trial_id': df['assignmentId'].astype(str) + "_" + df['questionId'].astype(str) + "_" + df['condition'],
        'dataset': 'bansal21',
        'user_id': df['assignmentId'].astype(str),
        'task_id': df['questionId'].astype(str),
        'ui_condition': df['condition'],
        'ai_advice': df['pred'],
        'ai_correct': (df['pred'] == df['y']),
        'human_initial': pd.NA,  # not available in this dataset
        'human_final': df['choice'],
        'ground_truth': df['y'],
        'relied': (df['choice'] == df['pred']),
        'task_difficulty': df['task'].map(domain_difficulty),  # domain as difficulty proxy
        'confidence': df['conf'],
        'rt_ms': df['time'] * 1000,  # convert seconds to ms
        'extra': df[['task', 'conf2', 'pred2']].to_dict('records'),
    })
    
    print(f"\nCanonical schema summary:")
    print(f"  Total trials: {len(canonical)}")
    print(f"  Users: {canonical['user_id'].nunique()}")
    print(f"  Tasks: {canonical['task_id'].nunique()}")
    print(f"  Conditions: {canonical['ui_condition'].unique()}")
    print(f"  Reliance rate: {canonical['relied'].mean():.3f}")
    print(f"  AI accuracy: {canonical['ai_correct'].mean():.3f}")
    
    return canonical


def get_ui_condition_pair() -> tuple[str, str]:
    """
    Return the UI condition pair selected for v0.
    
    Rationale: Human vs Conf.+Adaptive represents the core manipulation
    in Bansal et al. - comparing pure human judgment (no AI) to the condition
    with both confidence display and adaptive explanation.
    This is a clean contrast for testing over-dispersion sensitivity.
    """
    return ('Human', 'Conf.+Adaptive')
