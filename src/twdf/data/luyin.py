"""
Lu & Yin CHI'21 dataset loader.

Paper: "Effects of Explainable AI and Trust in Approving Incorrect AI Recommendations"
DOI: 10.1145/3411764.3445740
Repo: https://github.com/ZhuoranLu/Trustworthy-ML

Loads raw per-trial data and converts to canonical schema (INTERFACES.md §1).
"""

import os
from pathlib import Path
from typing import Optional
import urllib.request

import pandas as pd
import numpy as np


# Verified download URL from Manager spec
LUYIN_URL = "https://raw.githubusercontent.com/ZhuoranLu/Trustworthy-ML/main/data/expOneFinalPredictionsValid1125.csv"

# Expected columns from real data
EXPECTED_COLS = ['workerId', 'taskId', 'globalId', 'selfPrediction', 
                'finalPrediction', 'prediction', 'mlCorrect', 'selfCorrect', 
                'finalCorrect', 'switch', 'agreement', 'finalAgreement', 
                'idpAgreement', 'decision']


def download_if_missing(data_dir: Path) -> Path:
    """
    Download Lu&Yin dataset to data/raw/ if not already present.
    
    Returns path to the downloaded CSV file.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_path = data_dir / "luyin_chi21_predictions.csv"
    
    if csv_path.exists():
        print(f"Dataset already exists: {csv_path}")
        return csv_path
    
    print(f"Downloading Lu&Yin dataset from {LUYIN_URL}...")
    urllib.request.urlretrieve(LUYIN_URL, csv_path)
    print(f"Downloaded to {csv_path}")
    
    return csv_path


def load_luyin(data_dir: Optional[Path] = None,
               condition: Optional[str] = None) -> pd.DataFrame:
    """
    Load Lu&Yin CHI'21 data and convert to canonical per-trial schema.
    
    Column mapping (verified real headers):
    - workerId -> user_id
    - taskId -> task_id
    - selfPrediction -> human_initial (pre-AI decision)
    - finalPrediction -> human_final (post-AI decision)
    - prediction -> ai_advice (AI recommendation shown)
    - mlCorrect -> ai_correct
    - selfCorrect, finalCorrect, switch preserved in extra
    
    Derived fields:
    - relied: finalPrediction == prediction (adopted AI advice)
    - ground_truth: derived from finalCorrect and finalPrediction
    - ui_condition: 'luyin21' (or condition-based if available)
    
    STRUCTURE (verified):
    - 9030 data rows
    - 301 workers × exactly 30 tasks each (well-powered for split-half)
    - Within-subject sequential design (unlike Bansal's between-subjects)
    
    Args:
        data_dir: Directory containing raw data (default: ./data/raw)
        condition: Optional condition filter (e.g., by idpAgreement/decision if needed).
                  None = all trials (unconditional analysis)
    
    Returns:
        DataFrame with canonical schema per INTERFACES.md §1
    """
    if data_dir is None:
        data_dir = Path("data/raw")
    
    csv_path = download_if_missing(data_dir)
    
    # Load raw data
    # First column is unnamed row index; index_col=0 to skip it
    # Specify dtype for mixed-type columns to avoid DtypeWarning
    df = pd.read_csv(csv_path, index_col=0, 
                    dtype={'selfPrediction': str, 'finalPrediction': str, 
                           'prediction': str, 'selfCorrect': str, 'finalCorrect': str,
                           'mlCorrect': str, 'switch': str})
    
    # Verify expected columns
    missing = set(EXPECTED_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")
    
    print(f"Loaded {len(df)} rows from Lu&Yin dataset")
    print(f"Available columns: {list(df.columns)}")
    
    # Check for condition columns (idpAgreement, decision)
    print(f"\nCondition variables:")
    if 'idpAgreement' in df.columns:
        print(f"  idpAgreement values: {sorted(df['idpAgreement'].unique())}")
    if 'decision' in df.columns:
        print(f"  decision values: {sorted(df['decision'].unique())}")
    
    # Coerce boolean columns explicitly (they're read as strings 'TRUE'/'FALSE')
    bool_cols = ['selfCorrect', 'finalCorrect', 'mlCorrect', 'switch']
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].map({'TRUE': True, 'FALSE': False, True: True, False: False})
    
    # Coerce numeric columns
    numeric_cols = ['workerId', 'taskId', 'globalId', 'selfPrediction', 
                   'finalPrediction', 'prediction', 'agreement', 'finalAgreement', 
                   'idpAgreement', 'decision']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Apply condition filter if specified
    if condition is not None:
        # Interpret condition as filter on idpAgreement or decision
        # For now, support simple equality filter like 'idpAgreement==70'
        if '==' in condition:
            col_name, col_value = condition.split('==')
            col_name = col_name.strip()
            col_value = col_value.strip()
            if col_name in df.columns:
                df = df[df[col_name] == int(col_value)].copy()
                print(f"Filtered to {col_name}=={col_value}: {len(df)} rows")
            else:
                raise ValueError(f"Unknown condition column: {col_name}")
        else:
            raise ValueError(f"Unsupported condition format: {condition}. Use 'column==value'")
    
    # Derive ground truth from finalCorrect and finalPrediction
    # If finalCorrect==True, ground_truth = finalPrediction
    # If finalCorrect==False, ground_truth = 1 - finalPrediction (opposite)
    df['ground_truth'] = df.apply(
        lambda row: row['finalPrediction'] if row['finalCorrect'] 
                    else (1 - row['finalPrediction']), 
        axis=1
    )
    
    # Convert to canonical schema
    canonical = pd.DataFrame({
        'trial_id': df['workerId'].astype(str) + "_" + df['taskId'].astype(str),
        'dataset': 'luyin21',
        'user_id': df['workerId'].astype(str),
        'task_id': df['taskId'].astype(str),
        'ui_condition': 'luyin21' if condition is None else condition,
        'ai_advice': df['prediction'].astype(int),
        'ai_correct': df['mlCorrect'],
        'human_initial': df['selfPrediction'].astype(int),
        'human_final': df['finalPrediction'].astype(int),
        'ground_truth': df['ground_truth'].astype(int),
        'relied': (df['finalPrediction'] == df['prediction']),
        'task_difficulty': pd.NA,  # not available in this dataset
        'confidence': pd.NA,  # not available
        'rt_ms': pd.NA,  # not available
        'extra': df[['switch', 'selfCorrect', 'finalCorrect', 'agreement', 
                    'finalAgreement', 'idpAgreement', 'decision', 'globalId']].to_dict('records'),
    })
    
    print(f"\nCanonical schema summary:")
    print(f"  Total trials: {len(canonical)}")
    print(f"  Users: {canonical['user_id'].nunique()}")
    print(f"  Tasks: {canonical['task_id'].nunique()}")
    print(f"  Conditions: {canonical['ui_condition'].unique()}")
    
    # Report structure
    tasks_per_user = canonical.groupby('user_id')['task_id'].nunique()
    print(f"  Tasks per user: min={tasks_per_user.min()}, max={tasks_per_user.max()}, "
          f"median={tasks_per_user.median():.0f}, mean={tasks_per_user.mean():.1f}")
    
    print(f"  Reliance rate (unconditional): {canonical['relied'].mean():.3f}")
    print(f"  AI accuracy: {canonical['ai_correct'].mean():.3f}")
    
    # Conflict-conditioned reliance (system1 ≠ AI)
    conflict_trials = canonical[canonical['human_initial'] != canonical['ai_advice']]
    if len(conflict_trials) > 0:
        conflict_reliance = conflict_trials['relied'].mean()
        print(f"  Conflict trials (selfPrediction ≠ AI): {len(conflict_trials)} ({len(conflict_trials)/len(canonical):.1%})")
        print(f"  Conflict-conditioned reliance: {conflict_reliance:.3f}")
        
        # Conflict per user distribution
        conflict_per_user = conflict_trials.groupby('user_id')['task_id'].count()
        print(f"  Conflict per user: min={conflict_per_user.min()}, max={conflict_per_user.max()}, "
              f"median={conflict_per_user.median():.0f}, mean={conflict_per_user.mean():.1f}")
    else:
        print(f"  No conflict trials found (selfPrediction always == AI)")
    
    return canonical
