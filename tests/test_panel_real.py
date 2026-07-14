"""
Tests for real LLM panel (Module B).

CRITICAL TESTS:
1. Provider contract test (mock provider, no network)
2. Counterfactual invariant test (System-1 identical across UI arms)
3. Cache determinism test (CROSS-PROCESS - subprocess pattern)
4. Elasticity/permutation test on synthetic paired data
5. ONE real-API end-to-end test (marked live, skipped if no token)

Cross-process determinism is ESSENTIAL - single-process tests don't catch
hash-seed nondeterminism (the bug that bit this project twice).
"""

import os
import json
import pytest
import tempfile
import subprocess
import sys
from pathlib import Path
from typing import Optional

import numpy as np

from twdf.panel.stub import Persona, AgentResponse
from twdf.panel.provider import ModelProvider, GitHubModelsProvider
from twdf.panel.real_panel import run_panel, _compute_reliance
from twdf.data.bansal_tasks import TaskStimulus
from twdf.metrics.overdispersion import (
    within_task_diff,
    paired_permutation_test,
    bootstrap_ci
)


# ===== MOCK PROVIDER (NO NETWORK) =====

class MockProvider(ModelProvider):
    """Mock provider for testing without network calls."""
    
    name = "mock-provider"
    
    def __init__(self, deterministic_responses: Optional[dict] = None):
        """
        Args:
            deterministic_responses: Optional dict mapping prompt hash -> response
        """
        self.calls = []
        self.deterministic_responses = deterministic_responses or {}
    
    def generate(self, prompt: str, *, seed: int, max_tokens: int,
                 temperature: float) -> str:
        """Generate mock response."""
        self.calls.append({
            'prompt': prompt,
            'seed': seed,
            'max_tokens': max_tokens,
            'temperature': temperature
        })
        
        # Use seed to determine decision (deterministic)
        decision = seed % 2
        confidence = (seed % 100) / 100.0
        
        return f"""{{
  "decision": {decision},
  "confidence": {confidence:.2f},
  "reasoning": "Mock reasoning for seed {seed}"
}}"""
    
    def generate_messages(self, messages: list[dict], *, seed: int,
                         max_tokens: int, temperature: float) -> str:
        """Generate from messages."""
        # Extract prompt from messages
        prompt = ' '.join(m['content'] for m in messages)
        return self.generate(prompt, seed=seed, max_tokens=max_tokens, temperature=temperature)
    
    def get_stats(self) -> dict:
        return {
            'api_calls': len(self.calls),
            'cache_hits': 0,
            'total_requests': len(self.calls),
        }


# ===== TEST 1: Provider contract test =====

def test_provider_contract():
    """Test that run_panel returns well-formed AgentResponse with mock provider."""
    
    # Create simple personas
    personas = [
        Persona(
            persona_id="p1",
            domain_skill=0.5,
            ai_literacy=0.5,
            risk_sensitivity=0.5,
            caution=0.5,
            temperature=0.5,
            prior_mix=0.5
        ),
        Persona(
            persona_id="p2",
            domain_skill=0.7,
            ai_literacy=0.3,
            risk_sensitivity=0.2,
            caution=0.8,
            temperature=0.3,
            prior_mix=0.7
        ),
    ]
    
    # Create simple tasks
    tasks = [
        TaskStimulus(
            task_id="t1",
            domain="beer",
            text="This beer is excellent.",
            ground_truth=1,
            ai_pred=1,
            ai_conf=0.9,
            expert_explanation="The review is positive with words like **excellent**.",
            system="mock",
            testid="t1"
        ),
        TaskStimulus(
            task_id="t2",
            domain="beer",
            text="This beer is terrible.",
            ground_truth=0,
            ai_pred=0,
            ai_conf=0.8,
            expert_explanation="The review is negative with words like **terrible**.",
            system="mock",
            testid="t2"
        ),
    ]
    
    # UI pair
    ui_pair = ("Conf.", "Conf.+Adaptive (Expert)")
    
    # Mock provider
    provider = MockProvider()
    
    # Run panel
    responses = run_panel(
        personas=personas,
        tasks=tasks,
        ui_pair=ui_pair,
        providers=[provider],
        seeds=[42],
        mode="static"
    )
    
    # Verify structure
    assert len(responses) == len(personas) * len(tasks) * 2  # 2 UI conditions
    
    for resp in responses:
        # Check required fields
        assert isinstance(resp, AgentResponse)
        assert resp.persona_id in ['p1', 'p2']
        assert resp.task_id in ['t1', 't2']
        assert resp.ui_condition in ui_pair
        assert resp.model == "mock-provider"
        assert isinstance(resp.seed, int)
        assert resp.system1_decision in ['0', '1']
        assert resp.final_decision in ['0', '1']
        assert isinstance(resp.relied, bool)
        assert 0.0 <= resp.confidence <= 1.0
        assert isinstance(resp.trace, dict)


# ===== TEST 2: Counterfactual invariant test =====

def test_counterfactual_invariant():
    """
    Test that System-1 decision is IDENTICAL across UI arms for same (persona, task, seed).
    
    This is the CRITICAL INVARIANT for counterfactual pairing.
    If this fails, the difficulty control is broken.
    """
    
    personas = [
        Persona(
            persona_id="p1",
            domain_skill=0.5,
            ai_literacy=0.5,
            risk_sensitivity=0.5,
            caution=0.5,
            temperature=0.5,
            prior_mix=0.5
        ),
    ]
    
    tasks = [
        TaskStimulus(
            task_id="t1",
            domain="beer",
            text="This beer is good.",
            ground_truth=1,
            ai_pred=1,
            ai_conf=0.9,
            expert_explanation="Positive sentiment.",
            system="mock",
            testid="t1"
        ),
    ]
    
    ui_pair = ("Conf.", "Conf.+Adaptive (Expert)")
    provider = MockProvider()
    
    # Run panel
    responses = run_panel(
        personas=personas,
        tasks=tasks,
        ui_pair=ui_pair,
        providers=[provider],
        seeds=[42],
        mode="static"
    )
    
    # Extract System-1 decisions for each UI condition
    control_system1 = None
    treatment_system1 = None
    
    for resp in responses:
        if resp.ui_condition == ui_pair[0]:
            control_system1 = resp.system1_decision
        else:
            treatment_system1 = resp.system1_decision
    
    # CRITICAL INVARIANT: System-1 must be identical
    assert control_system1 is not None
    assert treatment_system1 is not None
    assert control_system1 == treatment_system1, \
        f"System-1 decision differs across UI arms! Control: {control_system1}, Treatment: {treatment_system1}"


# ===== TEST 3: Cache determinism test (CROSS-PROCESS) =====

def test_cache_determinism_cross_process(tmp_path):
    """
    Test that cached responses are byte-identical across SEPARATE PROCESSES.
    
    CRITICAL: Single-process tests don't catch hash-seed nondeterminism.
    This test spawns subprocesses to verify true determinism.
    
    NOTE: This test requires GH_MODELS_TOKEN to be set (even if not making real calls,
    provider init checks for the token). We'll skip if token is missing.
    """
    
    if "GH_MODELS_TOKEN" not in os.environ:
        pytest.skip("GH_MODELS_TOKEN not set - skipping cache determinism test")
    
    # Create test script that will run in subprocess
    test_script = tmp_path / "test_cache.py"
    cache_dir = tmp_path / "cache"
    output_file = tmp_path / "output.json"
    
    script_content = f'''
import sys
sys.path.insert(0, r"{Path(__file__).parent.parent.parent}")

from pathlib import Path
from twdf.panel.provider import GitHubModelsProvider

# Create provider with cache
provider = GitHubModelsProvider(
    cache_dir=Path(r"{cache_dir}"),
    call_budget=10
)

# Make a test call (will be cached if first run, retrieved if second)
# Use a simple prompt that should give consistent results
response = provider.generate(
    prompt="Say hello",
    seed=42,
    max_tokens=50,
    temperature=0.0
)

# Save response
import json
with open(r"{output_file}", 'w') as f:
    json.dump({{"response": response, "stats": provider.get_stats()}}, f)
'''
    
    test_script.write_text(script_content)
    
    # Run first process
    result1 = subprocess.run(
        [sys.executable, str(test_script)],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    
    if result1.returncode != 0:
        pytest.fail(f"First subprocess failed:\nstdout: {result1.stdout}\nstderr: {result1.stderr}")
    
    # Load first output
    with open(output_file, 'r') as f:
        output1 = json.load(f)
    
    # Run second process (should hit cache)
    result2 = subprocess.run(
        [sys.executable, str(test_script)],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    
    if result2.returncode != 0:
        pytest.fail(f"Second subprocess failed:\nstdout: {result2.stdout}\nstderr: {result2.stderr}")
    
    # Load second output
    with open(output_file, 'r') as f:
        output2 = json.load(f)
    
    # Verify byte-identical
    assert output1['response'] == output2['response'], \
        "Cache responses differ across processes!"
    
    # Verify second run used cache
    assert output2['stats']['cache_hits'] > 0, \
        "Second run should have hit cache!"


# ===== TEST 4: Elasticity/permutation test on synthetic data =====

def test_paired_permutation_with_known_effect():
    """Test paired permutation test on synthetic data with known positive effect."""
    
    # Synthetic data with known effect
    np.random.seed(42)
    n_tasks = 15
    
    # Control: mean reliance ~0.5
    control = {f"task_{i}": np.random.beta(5, 5) for i in range(n_tasks)}
    
    # Treatment: mean reliance ~0.7 (positive effect)
    treatment = {f"task_{i}": control[f"task_{i}"] + 0.2 + np.random.normal(0, 0.05) 
                 for i in range(n_tasks)}
    
    # Clamp to [0, 1]
    treatment = {k: min(1.0, max(0.0, v)) for k, v in treatment.items()}
    
    # Test within_task_diff
    diff = within_task_diff(control, treatment)
    assert diff > 0, "Expected positive diff for treatment > control"
    assert 0.15 < diff < 0.25, f"Expected diff ~0.2, got {diff}"
    
    # Test paired permutation
    result = paired_permutation_test(control, treatment, n_permutations=1000, seed=42)
    
    assert result.n_pairs == n_tasks
    assert result.observed_diff == pytest.approx(diff, abs=1e-6)
    assert result.pvalue < 0.05, "Expected significant result for strong effect"


def test_paired_permutation_null():
    """Test paired permutation test on null data (no difference)."""
    
    # Synthetic data with NO effect
    np.random.seed(43)
    n_tasks = 10
    
    # Control and treatment identical
    control = {f"task_{i}": np.random.beta(5, 5) for i in range(n_tasks)}
    treatment = {f"task_{i}": control[f"task_{i}"] + np.random.normal(0, 0.01) 
                 for i in range(n_tasks)}
    
    # Test
    diff = within_task_diff(control, treatment)
    assert abs(diff) < 0.05, "Expected near-zero diff for null data"
    
    result = paired_permutation_test(control, treatment, n_permutations=1000, seed=42)
    
    # p-value should be high for null
    assert result.pvalue > 0.1, f"Expected non-significant result for null data, got p={result.pvalue}"


# ===== TEST 5: Reliance computation =====

def test_reliance_computation():
    """Test reliance definition is correct."""
    
    # Case 1: final == AI, changed from system1 → relied
    assert _compute_reliance(system1_decision=0, final_decision=1, ai_advice=1) == True
    
    # Case 2: final == AI, system1 already matched AI → relied
    assert _compute_reliance(system1_decision=1, final_decision=1, ai_advice=1) == True
    
    # Case 3: final != AI → NOT relied
    assert _compute_reliance(system1_decision=0, final_decision=0, ai_advice=1) == False
    
    # Case 4: final != AI, even if changed from system1 → NOT relied
    assert _compute_reliance(system1_decision=1, final_decision=0, ai_advice=1) == False


# ===== TEST 6: LIVE end-to-end with real API (marked, skipped if no token) =====

@pytest.mark.live
def test_real_api_end_to_end():
    """
    Real API end-to-end test (ONE small run).
    
    Marked as 'live' - skipped in default pytest run.
    Run with: pytest -m live
    
    Requires GH_MODELS_TOKEN environment variable.
    """
    
    if "GH_MODELS_TOKEN" not in os.environ:
        pytest.skip("GH_MODELS_TOKEN not set - skipping live API test")
    
    # Tiny run (1 persona, 2 tasks)
    personas = [
        Persona(
            persona_id="test_p1",
            domain_skill=0.5,
            ai_literacy=0.5,
            risk_sensitivity=0.5,
            caution=0.5,
            temperature=0.5,
            prior_mix=0.5
        ),
    ]
    
    tasks = [
        TaskStimulus(
            task_id="test_t1",
            domain="beer",
            text="This beer is excellent with a smooth finish.",
            ground_truth=1,
            ai_pred=1,
            ai_conf=0.9,
            expert_explanation="Positive sentiment with words like **excellent** and **smooth**.",
            system="test",
            testid="test_t1"
        ),
        TaskStimulus(
            task_id="test_t2",
            domain="beer",
            text="This beer is terrible and tastes bad.",
            ground_truth=0,
            ai_pred=0,
            ai_conf=0.85,
            expert_explanation="Negative sentiment with words like **terrible** and **bad**.",
            system="test",
            testid="test_t2"
        ),
    ]
    
    ui_pair = ("Conf.", "Conf.+Adaptive (Expert)")
    
    # Real provider with temp cache
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = GitHubModelsProvider(
            cache_dir=Path(tmpdir) / "cache",
            call_budget=20
        )
        
        # Run panel
        responses = run_panel(
            personas=personas,
            tasks=tasks,
            ui_pair=ui_pair,
            providers=[provider],
            seeds=[42],
            mode="static"
        )
        
        # Verify
        assert len(responses) == len(personas) * len(tasks) * 2
        
        # Check all responses have valid decisions
        for resp in responses:
            assert resp.system1_decision in ['0', '1']
            assert resp.final_decision in ['0', '1']
            assert isinstance(resp.relied, bool)
            assert 0.0 <= resp.confidence <= 1.0
        
        # Check counterfactual invariant
        for persona in personas:
            for task in tasks:
                control_resp = [r for r in responses 
                               if r.persona_id == persona.persona_id 
                               and r.task_id == task.task_id 
                               and r.ui_condition == ui_pair[0]][0]
                treatment_resp = [r for r in responses 
                                 if r.persona_id == persona.persona_id 
                                 and r.task_id == task.task_id 
                                 and r.ui_condition == ui_pair[1]][0]
                
                assert control_resp.system1_decision == treatment_resp.system1_decision, \
                    f"System-1 invariant violated for {persona.persona_id}, {task.task_id}"
        
        # Check provider stats
        stats = provider.get_stats()
        print(f"\nLive API test stats: {stats}")
        assert stats['api_calls'] >= 0  # May be 0 if fully cached
        assert stats['total_requests'] == len(personas) * len(tasks) * 2 * 2  # 2 UI × 2 systems
