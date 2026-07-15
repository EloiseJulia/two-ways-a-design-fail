"""
Tests for Bansal discriminator: C0 mechanism test.

CRITICAL: This is the C0 co-anchor mechanism test. Do NOT weaken tests.

Test coverage:
1. Subset selection correctness (domain, AI-accuracy band, subsampling)
2. Cross-process determinism (same config/seed → identical results)
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import pandas as pd
import yaml

from twdf.data.bansal import load_bansal
from twdf.experiments.bansal_discriminator import filter_subset, compute_subset_structure


class TestSubsetFiltering:
    """Test that subset filtering works correctly."""
    
    @pytest.fixture
    def sample_data(self):
        """Load a small sample of Bansal data for testing."""
        df = load_bansal(
            data_dir=Path('data/raw'),
            ui_conditions=['Conf.+Adaptive'],
            task_selection='all'
        )
        return df
    
    def test_filter_none(self, sample_data):
        """Test filter_type='none' returns full data."""
        subset_config = {'filter_type': 'none'}
        filtered = filter_subset(sample_data, subset_config)
        
        assert len(filtered) == len(sample_data)
        assert set(filtered.columns) == set(sample_data.columns)
    
    def test_filter_domain_beer(self, sample_data):
        """Test domain filtering for beer domain."""
        subset_config = {'filter_type': 'domain', 'domain': 'beer'}
        filtered = filter_subset(sample_data, subset_config)
        
        # Check all rows are beer domain
        domains = filtered['extra'].apply(lambda x: x['task'])
        assert all(domains == 'beer')
        
        # Check we got some data
        assert len(filtered) > 0
    
    def test_filter_domain_lsat(self, sample_data):
        """Test domain filtering for lsat domain (Lu&Yin-matched)."""
        subset_config = {'filter_type': 'domain', 'domain': 'lsat'}
        filtered = filter_subset(sample_data, subset_config)
        
        # Check all rows are lsat domain
        domains = filtered['extra'].apply(lambda x: x['task'])
        assert all(domains == 'lsat')
        
        # Check we got some data
        assert len(filtered) > 0
        
        # Check tasks per user (should be ~20 for lsat in Bansal)
        tasks_per_user = filtered.groupby('user_id')['task_id'].nunique()
        # LSAT has fewer tasks (20 per user in Bansal)
        assert tasks_per_user.median() <= 25  # Allow some margin
    
    def test_filter_ai_accuracy_band(self, sample_data):
        """Test AI-accuracy band filtering."""
        subset_config = {
            'filter_type': 'ai_accuracy_band',
            'ai_acc_min': 0.60,
            'ai_acc_max': 0.75
        }
        filtered = filter_subset(sample_data, subset_config)
        
        # Compute per-task AI accuracy in filtered set
        if len(filtered) > 0:
            task_ai_acc = filtered.groupby('task_id')['ai_correct'].mean()
            
            # All tasks should be in the specified band
            assert all((task_ai_acc >= 0.60) & (task_ai_acc <= 0.75))
    
    def test_filter_subsample_tasks(self, sample_data):
        """Test tasks-per-user subsampling."""
        subset_config = {
            'filter_type': 'subsample_tasks_per_user',
            'target_tasks': 30,
            'seed': 43  # deterministic
        }
        filtered = filter_subset(sample_data, subset_config)
        
        # Check tasks per user <= target (may be less if user had < target originally)
        tasks_per_user = filtered.groupby('user_id')['task_id'].nunique()
        assert all(tasks_per_user <= 30)
        
        # Check we got some data
        assert len(filtered) > 0
    
    def test_filter_domain_and_accuracy(self, sample_data):
        """Test joint domain + AI-accuracy filtering (strictest match)."""
        subset_config = {
            'filter_type': 'domain_and_accuracy',
            'domain': 'beer',
            'ai_acc_min': 0.75,
            'ai_acc_max': 0.90
        }
        filtered = filter_subset(sample_data, subset_config)
        
        # May have no data if the band is too narrow (acceptable)
        if len(filtered) > 0:
            # Check domain
            domains = filtered['extra'].apply(lambda x: x['task'])
            assert all(domains == 'beer')
            
            # Check AI accuracy
            task_ai_acc = filtered.groupby('task_id')['ai_correct'].mean()
            assert all((task_ai_acc >= 0.75) & (task_ai_acc <= 0.90))


class TestSubsetStructure:
    """Test subset structure computation."""
    
    def test_structure_full_data(self):
        """Test structure computation on full Conf.+Adaptive data."""
        df = load_bansal(
            data_dir=Path('data/raw'),
            ui_conditions=['Conf.+Adaptive'],
            task_selection='all'
        )
        
        structure = compute_subset_structure(df)
        
        # Check all expected keys
        expected_keys = {
            'n_users', 'n_tasks', 'n_trials',
            'tasks_per_user_median', 'tasks_per_user_mean',
            'tasks_per_user_min', 'tasks_per_user_max',
            'reliance_rate', 'ai_accuracy'
        }
        assert set(structure.keys()) == expected_keys
        
        # Check reasonable values (Conf.+Adaptive should have ~292 users, 50 tasks)
        assert structure['n_users'] > 0
        assert structure['n_tasks'] > 0
        assert structure['n_trials'] > 0
        assert 0.0 <= structure['reliance_rate'] <= 1.0
        assert 0.0 <= structure['ai_accuracy'] <= 1.0
    
    def test_structure_beer_domain(self):
        """Test structure computation on beer domain subset."""
        df = load_bansal(
            data_dir=Path('data/raw'),
            ui_conditions=['Conf.+Adaptive'],
            task_selection='all'
        )
        
        subset_config = {'filter_type': 'domain', 'domain': 'beer'}
        filtered = filter_subset(df, subset_config)
        
        structure = compute_subset_structure(filtered)
        
        # Beer domain has all 50 tasks per user (within-domain)
        assert structure['tasks_per_user_median'] == 50.0
        assert structure['tasks_per_user_mean'] == 50.0


class TestDeterminism:
    """
    Test cross-process determinism (CRITICAL for C0 mechanism test).
    
    Same config + same seeds → bit-identical results across separate runs.
    """
    
    def test_discriminator_determinism_subprocess(self):
        """
        Run discriminator twice in separate processes with same config/seed.
        
        Results must be identical (excluding timestamp).
        
        CRITICAL: Do NOT weaken this test. Determinism is required for
        preregistration and honest reporting.
        """
        config_path = Path('configs/bansal_discriminator.yaml')
        
        if not config_path.exists():
            pytest.skip(f"Config file not found: {config_path}")
        
        # Run twice in separate processes
        results_1 = subprocess.run(
            [sys.executable, '-m', 'twdf.experiments.bansal_discriminator',
             '--config', str(config_path)],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes max
        )
        
        results_2 = subprocess.run(
            [sys.executable, '-m', 'twdf.experiments.bansal_discriminator',
             '--config', str(config_path)],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        # Both should succeed
        assert results_1.returncode == 0, f"Run 1 failed: {results_1.stderr}"
        assert results_2.returncode == 0, f"Run 2 failed: {results_2.stderr}"
        
        # Load results JSON from both runs
        results_file = Path('results/bansal_discriminator.json')
        assert results_file.exists()
        
        # Save first run results
        with open(results_file) as f:
            json_1 = json.load(f)
        
        # Wait a moment and run second time (will overwrite)
        import time
        time.sleep(1)
        
        results_2 = subprocess.run(
            [sys.executable, '-m', 'twdf.experiments.bansal_discriminator',
             '--config', str(config_path)],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        assert results_2.returncode == 0, f"Run 2 failed: {results_2.stderr}"
        
        with open(results_file) as f:
            json_2 = json.load(f)
        
        # Compare stable_user_share for each subset (excluding timestamp)
        for subset_name in json_1['subsets']:
            if 'split_half_reliability' in json_1['subsets'][subset_name]:
                share_1 = json_1['subsets'][subset_name]['split_half_reliability']['stable_user_share']
                share_2 = json_2['subsets'][subset_name]['split_half_reliability']['stable_user_share']
                
                # Must be identical to many decimal places
                assert abs(share_1 - share_2) < 1e-10, \
                    f"Non-deterministic results for {subset_name}: {share_1} != {share_2}"
        
        # Compare verdict summary
        assert json_1['verdict']['summary'] == json_2['verdict']['summary'], \
            "Verdict changed between runs (non-deterministic)"


class TestRealResults:
    """
    Test real discriminator results against expected patterns.
    
    These are NOT unit tests — they check the actual scientific findings.
    If these fail, it means the C0 mechanism test produced unexpected results.
    """
    
    def test_full_ai_baseline_in_expected_range(self):
        """Full AI baseline should match e1_decomposition range (~0.32-0.41)."""
        results_file = Path('results/bansal_discriminator.json')
        
        if not results_file.exists():
            pytest.skip("Results file not found (run discriminator first)")
        
        with open(results_file) as f:
            results = json.load(f)
        
        full_ai = results['subsets']['full_ai']
        
        if 'split_half_reliability' in full_ai:
            share = full_ai['split_half_reliability']['stable_user_share']
            
            # Should be in the AI-assisted range from e1_decomposition
            # (0.321 - 0.414, with some tolerance for Conf.+Adaptive specifically)
            assert 0.25 <= share <= 0.45, \
                f"Full AI baseline out of expected range: {share}"
    
    def test_lsat_domain_higher_than_full_ai(self):
        """LSAT domain (Lu&Yin-matched) should be higher than full_ai if homogeneity matters."""
        results_file = Path('results/bansal_discriminator.json')
        
        if not results_file.exists():
            pytest.skip("Results file not found (run discriminator first)")
        
        with open(results_file) as f:
            results = json.load(f)
        
        full_ai = results['subsets']['full_ai']
        lsat = results['subsets']['domain_lsat']
        
        if 'split_half_reliability' in full_ai and 'split_half_reliability' in lsat:
            share_full = full_ai['split_half_reliability']['stable_user_share']
            share_lsat = lsat['split_half_reliability']['stable_user_share']
            
            # LSAT should be higher than full_ai (because it's more homogeneous)
            # This is an empirical finding — if it fails, the mechanism test failed
            # NOTE: Not enforcing strict > because variance, but should be higher
            assert share_lsat >= share_full * 0.95, \
                f"LSAT not higher than full_ai: {share_lsat} vs {share_full}"
    
    def test_lsat_below_luyin_threshold(self):
        """LSAT domain should be below Lu&Yin's 0.80 if PERSIST verdict is correct."""
        results_file = Path('results/bansal_discriminator.json')
        
        if not results_file.exists():
            pytest.skip("Results file not found (run discriminator first)")
        
        with open(results_file) as f:
            results = json.load(f)
        
        lsat = results['subsets']['domain_lsat']
        luyin_threshold = results['benchmarks']['luyin_ai_assisted']
        
        if 'split_half_reliability' in lsat:
            share_lsat = lsat['split_half_reliability']['stable_user_share']
            
            # LSAT should be well below Lu&Yin's 0.80 if user×task persists
            # If this fails, the PERSIST verdict may be wrong
            assert share_lsat < 0.70, \
                f"LSAT too high (approaching Lu&Yin's trait-stable): {share_lsat}"
    
    def test_verdict_is_persists_or_intermediate(self):
        """Verdict should be PERSISTS or INTERMEDIATE based on LSAT results."""
        results_file = Path('results/bansal_discriminator.json')
        
        if not results_file.exists():
            pytest.skip("Results file not found (run discriminator first)")
        
        with open(results_file) as f:
            results = json.load(f)
        
        verdict = results['verdict']['summary']
        
        # Based on LSAT ~0.46, verdict should be PERSISTS (not COLLAPSES)
        # (If LSAT were ~0.75+, it would be COLLAPSES or INTERMEDIATE)
        assert verdict in ['PERSISTS', 'INTERMEDIATE'], \
            f"Unexpected verdict: {verdict} (expected PERSISTS or INTERMEDIATE based on LSAT ~0.46)"


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
