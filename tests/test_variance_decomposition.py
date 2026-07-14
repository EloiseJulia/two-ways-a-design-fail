"""
Tests for variance decomposition analysis.

VALIDATION REQUIREMENT (methods paper standard):
All estimators MUST be validated on synthetic data with known ground truth:
1. Stable-user-only: split-half reliability HIGH (ICC/Spearman-Brown >= 0.7),
   stable_user_share >= 0.8
2. User x task-only: split-half reliability LOW (<= 0.2), stable_user_share <= 0.2
3. Null (no variance): reliability ~ 0

These are STRONG thresholds. Do NOT weaken them to fit a weak estimator.
If a method cannot meet these, it is NOT valid for this data structure.

CRITICAL: Synthetic data MUST match Bansal structure:
- Each user ~40 tasks (not 20)
- 1 observation per (user, task) cell
- Between-subjects domain design
"""

import numpy as np
import pandas as pd
import pytest

from twdf.metrics.variance_decomposition import (
    split_half_reliability,
    variance_components_glmm,
    SplitHalfReliabilityResult,
    VarianceComponentsGLMMResult
)


def generate_synthetic_trials(n_users: int = 50, n_tasks_per_user: int = 40,
                              n_trials_per_cell: int = 1,
                              user_effect_sd: float = 0.0,
                              task_effect_sd: float = 0.0,
                              user_task_effect_sd: float = 0.0,
                              baseline_prob: float = 0.5,
                              seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic reliance trial data with BANSAL STRUCTURE.
    
    CRITICAL: Must match Bansal data structure:
    - Each user sees ~40-50 tasks (median 50), NOT 20
    - 1 observation per (user, task) cell
    - Between-subjects domain (each user in ONE domain)
    
    Model: logit(p_ij) = baseline + user_effect_i + task_effect_j + user_task_effect_ij
    
    Args:
        n_users: Number of users
        n_tasks_per_user: Tasks per user (default: 40, matching Bansal)
        n_trials_per_cell: Observations per (user, task) cell (default: 1, matching Bansal)
        user_effect_sd: SD of user main effect (stable trait)
        task_effect_sd: SD of task main effect
        user_task_effect_sd: SD of user x task interaction
        baseline_prob: Baseline probability
        seed: Random seed
    
    Returns:
        DataFrame with columns ['user_id', 'task_id', 'relied', 'ui_condition']
    """
    rng = np.random.RandomState(seed)
    
    # Total tasks needed (3 domains, roughly equal)
    n_domains = 3
    n_tasks_total = n_tasks_per_user * n_domains  # each domain has n_tasks_per_user tasks
    
    # Generate effects
    user_effects = rng.normal(0, user_effect_sd, n_users) if user_effect_sd > 0 else np.zeros(n_users)
    task_effects = rng.normal(0, task_effect_sd, n_tasks_total) if task_effect_sd > 0 else np.zeros(n_tasks_total)
    
    # Assign tasks to domains
    tasks_per_domain = n_tasks_per_user
    task_domains = np.array([1] * tasks_per_domain + 
                           [2] * tasks_per_domain + 
                           [3] * tasks_per_domain)
    
    trials = []
    for user_idx in range(n_users):
        # Each user sees tasks from ONE domain (between-subjects)
        domain = (user_idx % n_domains) + 1
        domain_tasks = np.where(task_domains == domain)[0]
        
        for task_idx in domain_tasks:
            # User x task interaction (unique to each cell)
            user_task_effect = rng.normal(0, user_task_effect_sd) if user_task_effect_sd > 0 else 0.0
            
            # Combine effects on logit scale
            logit_p = (np.log(baseline_prob / (1 - baseline_prob)) +
                      user_effects[user_idx] +
                      task_effects[task_idx] +
                      user_task_effect)
            
            p = 1 / (1 + np.exp(-logit_p))
            
            # Generate trials (typically 1 per cell for Bansal structure)
            for _ in range(n_trials_per_cell):
                relied = rng.random() < p
                trials.append({
                    'user_id': f'user_{user_idx}',
                    'task_id': f'task_{task_idx}',
                    'relied': int(relied),
                    'ui_condition': 'synthetic'
                })
    
    return pd.DataFrame(trials)


def test_split_half_stable_user_only():
    """
    Test 1: STABLE USER TRAIT ONLY (no user x task interaction).
    
    Generate synthetic data where each user has a fixed reliance probability
    (consistent across tasks). No user x task interaction.
    
    STRONG threshold: Spearman-Brown reliability >= 0.7, stable_user_share >= 0.8
    """
    # Large user effect, zero user x task interaction
    # CRITICAL: Use ~40 tasks per user to match Bansal structure
    df = generate_synthetic_trials(
        n_users=50,
        n_tasks_per_user=40,  # Bansal structure
        n_trials_per_cell=1,  # Bansal structure
        user_effect_sd=1.5,  # strong stable user effect
        task_effect_sd=0.3,  # some task difficulty variance
        user_task_effect_sd=0.0,  # NO user x task interaction
        seed=42
    )
    
    result = split_half_reliability(df, 'synthetic', n_splits=100, seed=42, min_tasks=8)
    
    # STRONG threshold: Spearman-Brown reliability >= 0.7
    assert result.spearman_brown_reliability >= 0.7, \
        f"Expected Spearman-Brown reliability >= 0.7 for stable-user-only, got {result.spearman_brown_reliability:.3f}"
    
    # STRONG threshold: stable_user_share >= 0.8
    assert result.stable_user_share >= 0.8, \
        f"Expected stable_user_share >= 0.8 for stable-user-only, got {result.stable_user_share:.3f}"
    
    # ICC should also be high
    assert result.icc_mean >= 0.7, \
        f"Expected ICC >= 0.7 for stable-user-only, got {result.icc_mean:.3f}"
    
    print(f"✓ Stable user only: Spearman-Brown = {result.spearman_brown_reliability:.3f}, "
          f"stable_share = {result.stable_user_share:.3f} [{result.stable_user_share_lower:.3f}, {result.stable_user_share_upper:.3f}]")


def test_split_half_user_task_only():
    """
    Test 2: USER x TASK INTERACTION ONLY (no stable user trait).
    
    Generate synthetic data where each user's reliance varies randomly across
    tasks (no consistent user trait). All variance is user x task interaction.
    
    STRONG threshold: Spearman-Brown reliability <= 0.2, stable_user_share <= 0.2
    """
    # Zero user effect, large user x task interaction
    df = generate_synthetic_trials(
        n_users=50,
        n_tasks_per_user=40,  # Bansal structure
        n_trials_per_cell=1,  # Bansal structure
        user_effect_sd=0.0,  # NO stable user effect
        task_effect_sd=0.3,  # some task difficulty variance
        user_task_effect_sd=1.5,  # strong user x task interaction
        seed=42
    )
    
    result = split_half_reliability(df, 'synthetic', n_splits=100, seed=42, min_tasks=8)
    
    # STRONG threshold: Spearman-Brown reliability <= 0.2
    assert result.spearman_brown_reliability <= 0.2, \
        f"Expected Spearman-Brown reliability <= 0.2 for user-x-task-only, got {result.spearman_brown_reliability:.3f}"
    
    # STRONG threshold: stable_user_share <= 0.2
    assert result.stable_user_share <= 0.2, \
        f"Expected stable_user_share <= 0.2 for user-x-task-only, got {result.stable_user_share:.3f}"
    
    print(f"✓ User x task only: Spearman-Brown = {result.spearman_brown_reliability:.3f}, "
          f"stable_share = {result.stable_user_share:.3f} [{result.stable_user_share_lower:.3f}, {result.stable_user_share_upper:.3f}]")


def test_split_half_null():
    """
    Test 3: NULL (all users same probability, no variance).
    
    Generate synthetic data where all users have the same reliance probability.
    No user variance, no task variance, no interaction.
    
    Expected: reliability ~ 0, stable_user_share ~ 0
    """
    # Zero all effects
    df = generate_synthetic_trials(
        n_users=50,
        n_tasks_per_user=40,  # Bansal structure
        n_trials_per_cell=1,  # Bansal structure
        user_effect_sd=0.0,
        task_effect_sd=0.0,
        user_task_effect_sd=0.0,
        baseline_prob=0.5,
        seed=42
    )
    
    result = split_half_reliability(df, 'synthetic', n_splits=100, seed=42, min_tasks=8)
    
    # Reliability should be close to 0 (sampling noise only)
    # Allow some slack for sampling variability
    assert abs(result.spearman_brown_reliability) < 0.3, \
        f"Expected Spearman-Brown reliability ~ 0 for null, got {result.spearman_brown_reliability:.3f}"
    
    assert abs(result.stable_user_share) < 0.3, \
        f"Expected stable_user_share ~ 0 for null, got {result.stable_user_share:.3f}"
    
    print(f"✓ Null: Spearman-Brown = {result.spearman_brown_reliability:.3f}, "
          f"stable_share = {result.stable_user_share:.3f}")


def test_split_half_determinism():
    """
    Test 4: Split-half reliability is deterministic under fixed seed.
    """
    df = generate_synthetic_trials(
        n_users=50,
        n_tasks_per_user=40,
        n_trials_per_cell=1,
        user_effect_sd=1.0,
        task_effect_sd=0.5,
        user_task_effect_sd=0.5,
        seed=42
    )
    
    result1 = split_half_reliability(df, 'synthetic', n_splits=100, seed=99, min_tasks=8)
    result2 = split_half_reliability(df, 'synthetic', n_splits=100, seed=99, min_tasks=8)
    
    assert abs(result1.spearman_mean - result2.spearman_mean) < 1e-10, \
        "Split-half Spearman should be deterministic under same seed"
    assert abs(result1.stable_user_share - result2.stable_user_share) < 1e-10, \
        "Stable user share should be deterministic under same seed"
    
    print(f"✓ Split-half determinism: stable_share = {result1.stable_user_share:.4f} (identical across runs)")


def test_split_half_insufficient_users():
    """
    Test 5: Split-half raises error if too few users have enough tasks.
    """
    # Only 1 user with enough tasks
    df = pd.DataFrame({
        'user_id': ['u1'] * 10 + ['u2'] * 2,
        'task_id': [f't{i}' for i in range(10)] + ['t1', 't2'],
        'relied': [1] * 12,
        'ui_condition': ['test'] * 12
    })
    
    with pytest.raises(ValueError, match="Need at least 2 users"):
        split_half_reliability(df, 'test', n_splits=10, seed=42, min_tasks=8)


def test_split_half_missing_columns():
    """
    Test 6: Split-half raises error on missing columns.
    """
    df = pd.DataFrame({
        'user_id': ['u1', 'u2'],
        'task_id': ['t1', 't1'],
        'relied': [1, 0]
        # missing 'ui_condition'
    })
    
    with pytest.raises(ValueError, match="Missing required column"):
        split_half_reliability(df, 'test', seed=42)


def test_glmm_stable_user_only():
    """
    Test 7: GLMM for STABLE USER TRAIT ONLY (optional corroboration).
    
    If GLMM converges, it should recover stable_user_share ~1.0.
    If it doesn't converge, that's OK — we mark it non-validated.
    """
    df = generate_synthetic_trials(
        n_users=30,  # smaller for GLMM speed
        n_tasks_per_user=20,  # smaller for GLMM speed
        n_trials_per_cell=1,
        user_effect_sd=1.5,
        task_effect_sd=0.3,
        user_task_effect_sd=0.0,
        seed=42
    )
    
    result = variance_components_glmm(df, 'synthetic', seed=42)
    
    if result is not None and result.converged:
        # If GLMM converged, check it recovers the right pattern
        # Allow slack since GLMM may be noisy
        assert result.stable_user_share > 0.5, \
            f"Expected GLMM stable_user_share > 0.5 for stable-user-only if converged, got {result.stable_user_share:.3f}"
        print(f"✓ GLMM stable user only: stable_share = {result.stable_user_share:.3f} (converged)")
    else:
        # GLMM didn't converge — that's acceptable, we mark it
        print("✓ GLMM stable user only: did not converge (acceptable for optional corroboration)")


def test_glmm_user_task_only():
    """
    Test 8: GLMM for USER x TASK INTERACTION ONLY (optional corroboration).
    
    If GLMM converges, it should recover stable_user_share ~0.0.
    If it doesn't converge, that's OK — we mark it non-validated.
    """
    df = generate_synthetic_trials(
        n_users=30,
        n_tasks_per_user=20,
        n_trials_per_cell=1,
        user_effect_sd=0.0,
        task_effect_sd=0.3,
        user_task_effect_sd=1.5,
        seed=42
    )
    
    result = variance_components_glmm(df, 'synthetic', seed=42)
    
    if result is not None and result.converged:
        # If GLMM converged, check it recovers the right pattern
        assert result.stable_user_share < 0.5, \
            f"Expected GLMM stable_user_share < 0.5 for user-x-task-only if converged, got {result.stable_user_share:.3f}"
        print(f"✓ GLMM user x task only: stable_share = {result.stable_user_share:.3f} (converged)")
    else:
        print("✓ GLMM user x task only: did not converge (acceptable for optional corroboration)")


def test_spearman_brown_correction():
    """
    Test 9: Spearman-Brown correction increases reliability estimate.
    
    Spearman-Brown formula: r_full = (2 * r_half) / (1 + r_half)
    Should be >= r_half for r_half > 0.
    """
    df = generate_synthetic_trials(
        n_users=50,
        n_tasks_per_user=40,
        n_trials_per_cell=1,
        user_effect_sd=1.0,
        task_effect_sd=0.5,
        user_task_effect_sd=0.3,
        seed=42
    )
    
    result = split_half_reliability(df, 'synthetic', n_splits=100, seed=42, min_tasks=8)
    
    # Spearman-Brown corrected should be >= half-length correlation (Spearman)
    # (unless half-length is negative, which can happen with noise)
    if result.spearman_mean > 0:
        assert result.spearman_brown_reliability >= result.spearman_mean, \
            f"Spearman-Brown corrected ({result.spearman_brown_reliability:.3f}) should be >= half-length ({result.spearman_mean:.3f})"
    
    print(f"✓ Spearman-Brown correction: half={result.spearman_mean:.3f}, full={result.spearman_brown_reliability:.3f}")


def test_stable_user_share_bounds():
    """
    Test 10: stable_user_share is bounded in [0, 1].
    """
    # Test with various data patterns
    for user_sd, interaction_sd in [(1.5, 0.0), (0.0, 1.5), (0.0, 0.0), (1.0, 1.0)]:
        df = generate_synthetic_trials(
            n_users=50,
            n_tasks_per_user=40,
            n_trials_per_cell=1,
            user_effect_sd=user_sd,
            task_effect_sd=0.3,
            user_task_effect_sd=interaction_sd,
            seed=42
        )
        
        result = split_half_reliability(df, 'synthetic', n_splits=100, seed=42, min_tasks=8)
        
        assert 0.0 <= result.stable_user_share <= 1.0, \
            f"stable_user_share should be in [0, 1], got {result.stable_user_share:.3f}"
        assert 0.0 <= result.stable_user_share_lower <= 1.0, \
            f"stable_user_share_lower should be in [0, 1], got {result.stable_user_share_lower:.3f}"
        assert 0.0 <= result.stable_user_share_upper <= 1.0, \
            f"stable_user_share_upper should be in [0, 1], got {result.stable_user_share_upper:.3f}"
    
    print("✓ Stable user share bounds: all values in [0, 1]")


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '-s'])
