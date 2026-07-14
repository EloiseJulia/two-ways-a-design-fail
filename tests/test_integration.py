"""Integration test: run minimal E1 v0 pipeline on fixture data."""

import tempfile
import json
from pathlib import Path

import pytest

from twdf.experiments.e1_vslice import run_e1_vslice


@pytest.mark.integration
def test_e1_pipeline_runs():
    """
    Integration test: verify the full E1 v0 pipeline runs without errors.
    
    This doesn't verify correctness of results (that's in unit tests),
    just that the pipeline executes end-to-end.
    """
    # Minimal config for integration test
    config = {
        'data': {
            'raw_dir': 'data/raw',
            'task_sample': None  # auto-select
        },
        'panel': {
            'n_personas': 3,  # reduced for speed
            'control_spread': 0.1,
            'treatment_spread': 0.3
        },
        'seeds': {
            'bootstrap': 42,
            'panel': 123
        },
        'bootstrap_n': 100  # very small for speed
    }
    
    # Run pipeline
    # Note: This will download Bansal data if not already cached
    results = run_e1_vslice(config)
    
    # Verify structure of results
    assert 'ui_pair' in results
    assert 'human_overdispersion' in results
    assert 'panel_disagreement' in results
    assert 'correlation' in results
    assert 'baseline_mean_predictor' in results
    
    # Verify correlation structure
    corr = results['correlation']
    assert 'r' in corr
    assert isinstance(corr['r'], float)
    assert not np.isnan(corr['r'])
    
    print(f"\nIntegration test results:")
    print(f"  UI pair: {results['ui_pair']}")
    print(f"  Correlation: r = {corr['r']:.4f}")
    print(f"  Human over-dispersion (rho): {corr['human_rho']}")
    print(f"  Panel disagreement: {corr['panel_disagreement']}")
    
    # Sanity check: correlation should be a valid number
    assert -1 <= corr['r'] <= 1, f"Correlation must be in [-1, 1], got {corr['r']}"


if __name__ == '__main__':
    # Allow running directly for manual testing
    import numpy as np
    test_e1_pipeline_runs()
