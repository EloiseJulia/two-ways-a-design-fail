"""
Tests for Lu&Yin dataset loader.

VALIDATION:
- Loader produces canonical schema (INTERFACES §1)
- Structure matches expected (301 users × 30 tasks each)
- Reliance defined correctly (finalPrediction == prediction)
- Deterministic loading (same input → same output)
- Dtype coercion works (boolean strings → bool)
"""

import pandas as pd
import pytest
from pathlib import Path

from twdf.data.luyin import load_luyin, EXPECTED_COLS


def test_luyin_loader_structure():
    """Test that Lu&Yin loader produces expected structure."""
    df = load_luyin()
    
    # Canonical schema columns (INTERFACES §1)
    required_cols = ['trial_id', 'dataset', 'user_id', 'task_id', 'ui_condition',
                    'ai_advice', 'ai_correct', 'human_initial', 'human_final',
                    'ground_truth', 'relied', 'task_difficulty', 'confidence',
                    'rt_ms', 'extra']
    
    for col in required_cols:
        assert col in df.columns, f"Missing canonical column: {col}"
    
    # Dataset identifier
    assert (df['dataset'] == 'luyin21').all(), "Dataset should be 'luyin21'"
    
    # Structure: 301 users × 30 tasks each = 9030 trials (actual: 31 unique tasks, 30/user)
    assert df['user_id'].nunique() == 301, f"Expected 301 users, got {df['user_id'].nunique()}"
    assert df['task_id'].nunique() == 31, f"Expected 31 tasks, got {df['task_id'].nunique()}"
    
    # Each user should have exactly 30 tasks (not all 31 - each user sees a subset)
    tasks_per_user = df.groupby('user_id')['task_id'].nunique()
    assert (tasks_per_user == 30).all(), "Each user should have exactly 30 tasks"
    
    print(f"✓ Structure correct: {df['user_id'].nunique()} users × {df['task_id'].nunique()} tasks = {len(df)} trials")


def test_luyin_loader_reliance_definition():
    """Test that reliance is defined correctly: finalPrediction == prediction."""
    df = load_luyin()
    
    # Reliance should be boolean
    assert df['relied'].dtype == bool, "relied should be boolean type"
    
    # Check consistency with raw columns in extra
    for idx, row in df.iterrows():
        final_pred = row['human_final']
        ai_pred = row['ai_advice']
        relied = row['relied']
        
        # relied should be True iff finalPrediction == prediction
        expected_relied = (final_pred == ai_pred)
        assert relied == expected_relied, (
            f"Row {idx}: relied={relied} but finalPrediction={final_pred}, AI={ai_pred}"
        )
    
    print(f"✓ Reliance definition correct: relied = (finalPrediction == prediction)")
    print(f"  Overall reliance rate: {df['relied'].mean():.3f}")


def test_luyin_loader_dtype_coercion():
    """Test that boolean and numeric columns are coerced correctly."""
    df = load_luyin()
    
    # Boolean columns in extra should be actual booleans
    for idx, row in df.iterrows():
        extra = row['extra']
        
        # Check boolean types
        assert isinstance(extra['switch'], bool), f"Row {idx}: switch should be bool"
        assert isinstance(extra['selfCorrect'], bool), f"Row {idx}: selfCorrect should be bool"
        assert isinstance(extra['finalCorrect'], bool), f"Row {idx}: finalCorrect should be bool"
        
        # ai_correct should be boolean
        assert isinstance(row['ai_correct'], bool), f"Row {idx}: ai_correct should be bool"
    
    # Numeric columns
    assert pd.api.types.is_integer_dtype(df['ai_advice']), "ai_advice should be int"
    assert pd.api.types.is_integer_dtype(df['human_initial']), "human_initial should be int"
    assert pd.api.types.is_integer_dtype(df['human_final']), "human_final should be int"
    assert pd.api.types.is_integer_dtype(df['ground_truth']), "ground_truth should be int"
    
    print(f"✓ Dtype coercion correct: booleans are bool, predictions are int")


def test_luyin_loader_ground_truth_derivation():
    """Test that ground_truth is derived correctly from finalCorrect + finalPrediction."""
    df = load_luyin()
    
    for idx, row in df.iterrows():
        final_pred = row['human_final']
        final_correct = row['extra']['finalCorrect']
        ground_truth = row['ground_truth']
        
        # If finalCorrect==True, ground_truth should equal finalPrediction
        # If finalCorrect==False, ground_truth should be opposite (1 - finalPrediction)
        if final_correct:
            expected_gt = final_pred
        else:
            expected_gt = 1 - final_pred
        
        assert ground_truth == expected_gt, (
            f"Row {idx}: ground_truth={ground_truth} but expected {expected_gt} "
            f"(finalPrediction={final_pred}, finalCorrect={final_correct})"
        )
    
    print(f"✓ Ground truth derivation correct")


def test_luyin_loader_determinism():
    """Test that loading is deterministic (same call → same result)."""
    df1 = load_luyin()
    df2 = load_luyin()
    
    # Should be identical
    pd.testing.assert_frame_equal(df1, df2)
    
    print(f"✓ Loader is deterministic")


def test_luyin_loader_conflict_trials():
    """Test that conflict trials (selfPrediction ≠ AI) are identified correctly."""
    df = load_luyin()
    
    # Conflict trials
    conflict = df[df['human_initial'] != df['ai_advice']]
    
    # Should have substantial conflict (not trivial)
    conflict_rate = len(conflict) / len(df)
    assert conflict_rate > 0.01, f"Expected >1% conflict trials, got {conflict_rate:.1%}"
    
    # Conflict per user distribution (should have enough for split-half)
    conflict_per_user = conflict.groupby('user_id')['task_id'].count()
    assert conflict_per_user.min() >= 1, "Each user should have at least 1 conflict trial"
    
    print(f"✓ Conflict trials identified: {len(conflict)} ({conflict_rate:.1%})")
    print(f"  Conflict per user: min={conflict_per_user.min()}, max={conflict_per_user.max()}, "
          f"median={conflict_per_user.median():.0f}, mean={conflict_per_user.mean():.1f}")


def test_luyin_decomposition_determinism_subprocess():
    """
    Test that luyin_decomposition experiment is deterministic across subprocess runs.
    
    CRITICAL: This is the gold-standard reproducibility test.
    If this fails, the result is not scientifically valid.
    """
    import subprocess
    import json
    from pathlib import Path
    import tempfile
    
    # Create temp output files
    with tempfile.TemporaryDirectory() as tmpdir:
        output1 = Path(tmpdir) / "luyin_decomp_run1.json"
        output2 = Path(tmpdir) / "luyin_decomp_run2.json"
        
        # Run 1
        result1 = subprocess.run(
            ['python', '-m', 'twdf.experiments.luyin_decomposition',
             '--config', 'configs/luyin_decomposition.yaml',
             '--output', str(output1)],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        assert result1.returncode == 0, f"Run 1 failed: {result1.stderr}"
        
        # Run 2
        result2 = subprocess.run(
            ['python', '-m', 'twdf.experiments.luyin_decomposition',
             '--config', 'configs/luyin_decomposition.yaml',
             '--output', str(output2)],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        assert result2.returncode == 0, f"Run 2 failed: {result2.stderr}"
        
        # Load results
        with open(output1) as f:
            res1 = json.load(f)
        with open(output2) as f:
            res2 = json.load(f)
        
        # Compare split-half results (excluding timestamp)
        uncond1 = res1.get('unconditional_reliance', {}).get('split_half_reliability', {})
        uncond2 = res2.get('unconditional_reliance', {}).get('split_half_reliability', {})
        
        # Key metrics should be EXACTLY equal (same seed)
        for key in ['stable_user_share', 'stable_user_share_lower', 'stable_user_share_upper',
                   'spearman_mean', 'icc_mean', 'n_users']:
            assert uncond1[key] == uncond2[key], (
                f"Determinism FAIL: {key} differs between runs "
                f"({uncond1[key]} vs {uncond2[key]})"
            )
        
        print(f"✓ Decomposition experiment is deterministic across subprocess runs")
        print(f"  stable_user_share: {uncond1['stable_user_share']:.3f} "
              f"[{uncond1['stable_user_share_lower']:.3f}, {uncond1['stable_user_share_upper']:.3f}]")
