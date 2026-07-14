"""
CRITICAL TESTS for beta-binomial over-dispersion metric.

These tests verify the core methodological requirement (SPEC §8):
- betabinom_overdispersion MUST separate true over-dispersion from binomial noise
- NOT just raw variance (that would collapse hypothesis H1a)
- Mean-predictor baseline MUST be beaten on truly over-dispersed data
"""

import pytest
import numpy as np

from twdf.metrics.overdispersion import (
    betabinom_overdispersion,
    baseline_mean_predictor,
    bootstrap_ci,
    within_task_diff
)


def test_pure_binomial_returns_near_zero_rho():
    """
    CRITICAL TEST (a): Pure binomial data -> rho ≈ 0
    
    If all users have SAME reliance probability, there is NO between-user
    heterogeneity, only binomial sampling noise. The metric MUST return
    rho ≈ 0 (not confuse sampling noise with over-dispersion).
    """
    # Simulate: all users have p=0.5, each does 20 trials
    # Observed reliances will vary due to binomial noise, but rho should be ~0
    np.random.seed(42)
    
    n_users = 50
    n_trials = 20
    true_p = 0.5
    
    relied_by_user = {}
    for i in range(n_users):
        n_relied = np.random.binomial(n_trials, true_p)
        relied_by_user[f"user_{i}"] = (n_relied, n_trials)
    
    result = betabinom_overdispersion(relied_by_user)
    
    print(f"\nPure binomial test: rho = {result.rho:.4f}")
    print(f"  Mean p: {result.mean_p:.3f} (expected ~0.5)")
    print(f"  Empirical var: {result.empirical_variance:.4f}")
    print(f"  Binomial var: {result.binomial_variance:.4f}")
    
    # Should be near zero (we allow some estimation error)
    assert result.rho < 0.1, f"Pure binomial should give rho ≈ 0, got {result.rho:.4f}"
    
    # Mean should be close to true p
    assert abs(result.mean_p - true_p) < 0.1, f"Mean should be ~{true_p}, got {result.mean_p:.3f}"


def test_high_low_split_returns_positive_rho():
    """
    CRITICAL TEST (b): Deliberately over-dispersed data -> rho > 0
    
    If users split into high and low reliance groups, there IS true
    between-user heterogeneity beyond binomial noise. The metric MUST
    detect this and return rho > 0.
    """
    np.random.seed(43)
    
    n_trials = 20
    
    # Group 1: 25 users with p=0.3 (low reliance)
    # Group 2: 25 users with p=0.7 (high reliance)
    relied_by_user = {}
    
    for i in range(25):
        n_relied = np.random.binomial(n_trials, 0.3)
        relied_by_user[f"low_{i}"] = (n_relied, n_trials)
    
    for i in range(25):
        n_relied = np.random.binomial(n_trials, 0.7)
        relied_by_user[f"high_{i}"] = (n_relied, n_trials)
    
    result = betabinom_overdispersion(relied_by_user)
    
    print(f"\nHigh/low split test: rho = {result.rho:.4f}")
    print(f"  Mean p: {result.mean_p:.3f} (expected ~0.5)")
    print(f"  Empirical var: {result.empirical_variance:.4f}")
    print(f"  Binomial var: {result.binomial_variance:.4f}")
    print(f"  Excess var: {result.excess_variance:.4f}")
    
    # Should detect over-dispersion
    assert result.rho > 0.1, f"High/low split should give rho > 0.1, got {result.rho:.4f}"
    
    # Should have excess variance beyond binomial
    assert result.excess_variance > 0, f"Should have excess variance, got {result.excess_variance:.4f}"


def test_overdispersed_beats_mean_predictor():
    """
    CRITICAL TEST: Over-dispersed data BEATS mean-predictor baseline.
    
    The mean-predictor baseline outputs rho=0 by construction (no over-dispersion).
    On truly over-dispersed data, betabinom_overdispersion MUST beat this baseline
    (i.e., rho > 0 > baseline.rho).
    """
    np.random.seed(44)
    
    n_trials = 20
    
    # Create over-dispersed data (high/low split)
    relied_by_user = {}
    for i in range(25):
        n_relied = np.random.binomial(n_trials, 0.3)
        relied_by_user[f"low_{i}"] = (n_relied, n_trials)
    
    for i in range(25):
        n_relied = np.random.binomial(n_trials, 0.7)
        relied_by_user[f"high_{i}"] = (n_relied, n_trials)
    
    # Compute over-dispersion
    result = betabinom_overdispersion(relied_by_user)
    
    # Compute mean-predictor baseline
    baseline = baseline_mean_predictor(relied_by_user)
    
    print(f"\nBaseline comparison:")
    print(f"  Beta-binomial rho: {result.rho:.4f}")
    print(f"  Mean-predictor rho: {baseline.rho:.4f}")
    print(f"  Beta-binomial BEATS baseline: {result.rho > baseline.rho}")
    
    # Baseline should be exactly 0 (by construction)
    assert baseline.rho == 0.0, f"Mean-predictor baseline should have rho=0, got {baseline.rho:.4f}"
    
    # Over-dispersed data should beat baseline
    assert result.rho > baseline.rho, f"Over-dispersed data should beat baseline: {result.rho:.4f} > {baseline.rho:.4f}"


def test_bootstrap_ci():
    """Test bootstrap confidence interval computation."""
    np.random.seed(45)
    
    # Create simple data
    relied_by_user = {
        f"user_{i}": (np.random.binomial(20, 0.5), 20)
        for i in range(30)
    }
    
    # Compute bootstrap CI for rho
    ci = bootstrap_ci(
        stat_fn=lambda data: betabinom_overdispersion(data).rho,
        data=relied_by_user,
        n=100,  # small n for speed
        seed=42
    )
    
    print(f"\nBootstrap CI test:")
    print(f"  Estimate: {ci.estimate:.4f}")
    print(f"  95% CI: [{ci.ci_lower:.4f}, {ci.ci_upper:.4f}]")
    print(f"  SE: {ci.se:.4f}")
    
    # Sanity checks
    assert ci.ci_lower <= ci.estimate <= ci.ci_upper, "Estimate should be within CI"
    assert ci.se > 0, "SE should be positive"


def test_within_task_diff():
    """Test difficulty-controlled within-task difference."""
    # Control condition: tasks have varying difficulty but low reliance
    control_reliance = {
        'task_1': 0.3,  # easy task (low reliance in control)
        'task_2': 0.5,  # medium task
        'task_3': 0.7,  # hard task (high reliance in control)
    }
    
    # Treatment condition: same tasks, but intervention increases reliance uniformly
    treatment_reliance = {
        'task_1': 0.5,  # +0.2 effect
        'task_2': 0.7,  # +0.2 effect
        'task_3': 0.9,  # +0.2 effect
    }
    
    diff = within_task_diff(control_reliance, treatment_reliance)
    
    print(f"\nWithin-task diff test:")
    print(f"  Control: {list(control_reliance.values())}")
    print(f"  Treatment: {list(treatment_reliance.values())}")
    print(f"  Mean diff: {diff:.3f} (expected ~0.2)")
    
    # Should recover the uniform +0.2 effect (difficulty cancels out)
    assert abs(diff - 0.2) < 0.01, f"Expected diff ≈ 0.2, got {diff:.3f}"


def test_schema_mapping():
    """Test that Bansal data maps correctly to canonical schema."""
    # This is tested implicitly when we load data, but we verify key fields exist
    from twdf.data.bansal import EXPECTED_COLS
    
    required = ['assignmentId', 'questionId', 'condition', 'choice', 'y', 'pred', 'conf']
    
    for col in required:
        assert col in EXPECTED_COLS, f"Missing required column: {col}"
    
    print("\nSchema mapping test: PASSED")
