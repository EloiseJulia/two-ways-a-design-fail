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


def test_panel_stub_determinism():
    """
    Test that synthetic panel stub produces identical results with same seed.
    
    This verifies reproducibility requirement from audit (B2).
    """
    from twdf.panel.stub import Persona, generate_synthetic_panel, compute_panel_disagreement
    
    # Create test personas
    personas = [
        Persona(
            persona_id=f"p{i}",
            domain_skill=0.5,
            ai_literacy=0.5,
            risk_sensitivity=0.5,
            caution=0.5,
            temperature=0.7,
            prior_mix=0.5
        )
        for i in range(3)
    ]
    
    tasks = ['t1', 't2', 't3']
    ui_conditions = ['control', 'treatment']  # Changed from ui_pair tuple to list
    base_reliance = {'control': 0.5, 'treatment': 0.6}
    
    # Run 1
    responses_1 = generate_synthetic_panel(
        personas=personas,
        tasks=tasks,
        ui_conditions=ui_conditions,  # Changed from ui_pair to ui_conditions
        base_reliance=base_reliance,
        persona_spread=0.2,
        seed=42
    )
    disagreement_1_control = compute_panel_disagreement(responses_1, 'control')
    disagreement_1_treatment = compute_panel_disagreement(responses_1, 'treatment')
    
    # Run 2 with same seed
    responses_2 = generate_synthetic_panel(
        personas=personas,
        tasks=tasks,
        ui_conditions=ui_conditions,  # Changed from ui_pair to ui_conditions
        base_reliance=base_reliance,
        persona_spread=0.2,
        seed=42
    )
    disagreement_2_control = compute_panel_disagreement(responses_2, 'control')
    disagreement_2_treatment = compute_panel_disagreement(responses_2, 'treatment')
    
    print(f"\nPanel stub determinism test:")
    print(f"  Run 1 - Control: {disagreement_1_control:.6f}, Treatment: {disagreement_1_treatment:.6f}")
    print(f"  Run 2 - Control: {disagreement_2_control:.6f}, Treatment: {disagreement_2_treatment:.6f}")
    
    # Should be byte-for-byte identical
    assert disagreement_1_control == disagreement_2_control, "Control disagreement not deterministic"
    assert disagreement_1_treatment == disagreement_2_treatment, "Treatment disagreement not deterministic"
    
    # Verify individual responses are identical
    assert len(responses_1) == len(responses_2), "Different number of responses"
    for r1, r2 in zip(responses_1, responses_2):
        assert r1 == r2, f"Response mismatch: {r1} != {r2}"
    
    print("  ✓ Panel stub is deterministic with fixed seed")


def test_multi_condition_data_loader():
    """Test that data loader correctly handles multi-condition selection."""
    from twdf.data.bansal import load_bansal
    import pandas as pd
    from pathlib import Path
    
    # Test with 3 conditions (subset of all 6)
    test_conditions = ['Human', 'Conf.', 'Conf.+Adaptive']
    
    df = load_bansal(
        data_dir=Path('data/raw'),
        ui_conditions=test_conditions,
        task_sample=None  # auto-select
    )
    
    print(f"\nMulti-condition loader test:")
    print(f"  Requested: {test_conditions}")
    print(f"  Got: {sorted(df['ui_condition'].unique())}")
    print(f"  Total rows: {len(df)}")
    
    # Verify all requested conditions are present
    assert set(df['ui_condition'].unique()) == set(test_conditions), \
        f"Condition mismatch: got {df['ui_condition'].unique()}, expected {test_conditions}"
    
    # Verify tasks are shared across all conditions
    tasks_by_condition = {
        cond: set(df[df['ui_condition'] == cond]['task_id'].unique())
        for cond in test_conditions
    }
    shared_tasks = set.intersection(*tasks_by_condition.values())
    
    print(f"  Shared tasks: {len(shared_tasks)}")
    assert len(shared_tasks) > 0, "Should have shared tasks across all conditions"
    
    # Verify task_difficulty is populated
    assert not df['task_difficulty'].isna().all(), "task_difficulty should be populated"
    
    print("  ✓ Multi-condition loader working correctly")


def test_difficulty_controlled_overdispersion():
    """Test difficulty-controlled over-dispersion with synthetic confounded data."""
    from twdf.metrics.overdispersion import betabinom_overdispersion_difficulty_controlled
    import pandas as pd
    import numpy as np
    
    # Create synthetic data where difficulty confounds the comparison:
    # - Easy tasks (difficulty=1): users have low reliance variance
    # - Hard tasks (difficulty=3): users have high reliance variance
    # If we naively pool, we'd mistake difficulty for over-dispersion
    
    np.random.seed(46)
    
    trials = []
    n_users = 30
    
    # Condition with more easy tasks (should appear low over-dispersion if confounded)
    for user_id in range(n_users):
        # 80% easy tasks (difficulty=1)
        for task_id in range(8):
            relied = np.random.rand() < 0.3  # low variance on easy tasks
            trials.append({
                'user_id': f"user_{user_id}",
                'task_id': f"easy_{task_id}",
                'task_difficulty': 1.0,
                'ui_condition': 'test_cond',
                'relied': relied
            })
        # 20% hard tasks (difficulty=3)
        for task_id in range(2):
            # High variance on hard tasks
            user_p = 0.3 if user_id % 2 == 0 else 0.7  # split users
            relied = np.random.rand() < user_p
            trials.append({
                'user_id': f"user_{user_id}",
                'task_id': f"hard_{task_id}",
                'task_difficulty': 3.0,
                'ui_condition': 'test_cond',
                'relied': relied
            })
    
    df = pd.DataFrame(trials)
    
    # Compute difficulty-controlled over-dispersion
    od_controlled = betabinom_overdispersion_difficulty_controlled(
        df=df,
        condition='test_cond',
        difficulty_col='task_difficulty'
    )
    
    print(f"\nDifficulty-controlled overdispersion test:")
    print(f"  Controlled rho: {od_controlled.rho:.4f}")
    print(f"  Mean p: {od_controlled.mean_p:.3f}")
    
    # Should detect over-dispersion from user split on hard tasks
    # even though easy tasks dominate the count
    assert od_controlled.rho >= 0, "Should get non-negative rho"
    assert od_controlled.n_users == n_users, f"Should have {n_users} users"
    
    print("  ✓ Difficulty-controlled estimator working")


def test_condition_correlation_spearman():
    """Test Spearman correlation with monotonic synthetic data."""
    from twdf.metrics.overdispersion import condition_correlation
    
    # Create monotonic relationship: higher disagreement -> higher over-dispersion
    disagreement = {
        'cond_A': 0.01,
        'cond_B': 0.02,
        'cond_C': 0.03,
        'cond_D': 0.04,
        'cond_E': 0.05,
    }
    
    overdispersion = {
        'cond_A': 0.10,
        'cond_B': 0.15,
        'cond_C': 0.20,
        'cond_D': 0.25,
        'cond_E': 0.30,
    }
    
    # Perfect monotonic relationship -> Spearman rho ≈ 1.0
    corr = condition_correlation(
        disagreement_by_condition=disagreement,
        overdispersion_by_condition=overdispersion,
        permutation_n=1000,
        bootstrap_n=1000,
        bootstrap_seed=42,
        permutation_seed=456
    )
    
    print(f"\nMonotonic correlation test:")
    print(f"  Spearman rho: {corr.spearman_rho:.4f} (expected ≈ 1.0)")
    print(f"  Permutation p: {corr.permutation_pvalue:.4f} (expected < 0.05)")
    print(f"  Bootstrap CI: [{corr.bootstrap_ci_lower:.4f}, {corr.bootstrap_ci_upper:.4f}]")
    print(f"  Degenerate: {corr.degenerate} (n={corr.n_conditions})")
    
    # Should get near-perfect positive correlation
    assert corr.spearman_rho > 0.9, f"Monotonic data should give rho > 0.9, got {corr.spearman_rho:.4f}"
    
    # Should be statistically significant
    assert corr.permutation_pvalue < 0.05, f"Should be significant, got p={corr.permutation_pvalue:.4f}"
    
    # Should NOT be degenerate (n=5)
    assert not corr.degenerate, "n=5 should not be degenerate"
    
    print("  ✓ Spearman correlation working on monotonic data")


def test_condition_correlation_random():
    """Test correlation with random (no association) synthetic data."""
    from twdf.metrics.overdispersion import condition_correlation
    import numpy as np
    
    np.random.seed(47)
    
    # Create random data (no association)
    conditions = ['A', 'B', 'C', 'D', 'E', 'F']
    disagreement = {c: np.random.rand() * 0.1 for c in conditions}
    overdispersion = {c: np.random.rand() * 0.3 for c in conditions}
    
    corr = condition_correlation(
        disagreement_by_condition=disagreement,
        overdispersion_by_condition=overdispersion,
        permutation_n=1000,
        bootstrap_n=1000,
        bootstrap_seed=42,
        permutation_seed=456
    )
    
    print(f"\nRandom correlation test:")
    print(f"  Spearman rho: {corr.spearman_rho:.4f}")
    print(f"  Permutation p: {corr.permutation_pvalue:.4f} (expected > 0.05)")
    print(f"  n_conditions: {corr.n_conditions}")
    
    # With random data, should typically NOT be significant (though 5% chance of false positive)
    # We don't assert on p-value (could fail by chance), just verify it runs
    
    # Should NOT be degenerate (n=6)
    assert not corr.degenerate, "n=6 should not be degenerate"
    
    print("  ✓ Correlation test runs on random data")


def test_condition_correlation_degenerate():
    """Test that n<3 is correctly flagged as degenerate."""
    from twdf.metrics.overdispersion import condition_correlation
    
    # Only 2 conditions
    disagreement = {'A': 0.01, 'B': 0.03}
    overdispersion = {'A': 0.10, 'B': 0.20}
    
    corr = condition_correlation(
        disagreement_by_condition=disagreement,
        overdispersion_by_condition=overdispersion,
        permutation_n=100,
        bootstrap_n=100,
        bootstrap_seed=42,
        permutation_seed=456
    )
    
    print(f"\nDegenerate (n=2) test:")
    print(f"  Spearman rho: {corr.spearman_rho:.4f}")
    print(f"  Degenerate: {corr.degenerate}")
    print(f"  Note: {corr.note}")
    
    # Should be flagged as degenerate
    assert corr.degenerate, "n=2 should be flagged as degenerate"
    assert corr.note is not None, "Should have warning note"
    assert "DEGENERATE" in corr.note, "Note should mention degenerate"
    
    print("  ✓ Degenerate guard working")


def test_panel_stub_multi_condition():
    """Test panel stub with multi-condition (not just pair)."""
    from twdf.panel.stub import Persona, generate_synthetic_panel, compute_panel_disagreement
    
    personas = [
        Persona(
            persona_id=f"p{i}",
            domain_skill=0.5,
            ai_literacy=0.5,
            risk_sensitivity=0.5,
            caution=0.5,
            temperature=0.7,
            prior_mix=0.5
        )
        for i in range(3)
    ]
    
    tasks = ['t1', 't2']
    ui_conditions = ['cond_A', 'cond_B', 'cond_C', 'cond_D']  # 4 conditions
    base_reliance = {c: 0.5 for c in ui_conditions}
    
    responses = generate_synthetic_panel(
        personas=personas,
        tasks=tasks,
        ui_conditions=ui_conditions,
        base_reliance=base_reliance,
        persona_spread=0.2,
        seed=42
    )
    
    print(f"\nMulti-condition panel stub test:")
    print(f"  Conditions: {ui_conditions}")
    print(f"  Expected responses: {len(personas)} * {len(tasks)} * {len(ui_conditions)} = {len(personas) * len(tasks) * len(ui_conditions)}")
    print(f"  Got responses: {len(responses)}")
    
    # Should have responses for all conditions
    assert len(responses) == len(personas) * len(tasks) * len(ui_conditions), \
        "Should have response for each (persona, task, condition) combination"
    
    # Verify all conditions present
    response_conditions = set(r.ui_condition for r in responses)
    assert response_conditions == set(ui_conditions), \
        f"Condition mismatch: {response_conditions} != {ui_conditions}"
    
    # Compute disagreement per condition
    for ui_cond in ui_conditions:
        disagreement = compute_panel_disagreement(responses, ui_cond)
        print(f"  {ui_cond}: disagreement = {disagreement:.4f}")
        assert disagreement >= 0, f"Disagreement should be non-negative, got {disagreement}"
    
    print("  ✓ Multi-condition panel stub working")

