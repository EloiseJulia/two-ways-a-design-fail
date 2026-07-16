"""
Tests for E4 Compliance experiment (placebo baseline + axis-2 sensor).

CRITICAL TESTS (ALL OFFLINE, NO NETWORK):
1. Placebo renderer: distinct from control/faithful, content-free, no leakage
2. 4-condition panel: System-1 frozen invariant across all 4 conditions
3. Compliance-floor metrics on synthetic data (STRONG thresholds)
4. Axis-2 sensor + compliance-adjusted value on synthetic data
5. Cross-process determinism (subprocess pattern)

All tests use MOCK provider. DO NOT weaken thresholds.
"""

import os
import json
import pytest
import tempfile
import subprocess
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import re
import numpy as np

from twdf.panel.stub import Persona, AgentResponse
from twdf.panel.provider import ModelProvider
from twdf.panel.real_panel import run_panel
from twdf.data.bansal_tasks import TaskStimulus, render_ui_condition
from twdf.data.item_selector import ItemSelectionCriteria, select_hard_items
from twdf.metrics.overdispersion import (
    conflict_conditioned_reliance,
    over_reliance_level,
    paired_permutation_test,
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


# ===== TEST 1: PLACEBO RENDERER (content-free, distinct, no leakage) =====

def test_placebo_renderer_distinct():
    """
    Test that placebo renderer produces distinct output from control and faithful.
    
    STRONG THRESHOLD: Must be present, must differ from both.
    """
    # Create a test task
    task = TaskStimulus(
        task_id="0",
        domain="beer",
        text="This beer has a malty aroma with hints of caramel.",
        ground_truth=1,
        ai_pred=1,
        ai_conf=0.85,
        expert_explanation="The **malty aroma** and **hints of caramel** are strong indicators of a positive review.",
        system="gpt-3.5-turbo",
        testid="beer_001"
    )
    
    # Render all 4 conditions
    control_ui = render_ui_condition(task, "Conf.")
    faithful_ui = render_ui_condition(task, "Conf.+Adaptive (Expert)")
    placebo_ui = render_ui_condition(task, "Conf.+Placebo")
    dark_ui = render_ui_condition(task, "Wrong-AI (dark)")
    
    # Check that placebo is DISTINCT from control
    assert placebo_ui != control_ui, "Placebo must differ from control"
    
    # Check that placebo is DISTINCT from faithful
    assert placebo_ui != faithful_ui, "Placebo must differ from faithful"
    
    # Check that placebo CONTAINS an explanation (presence)
    assert "Explanation:" in placebo_ui, "Placebo must have an explanation section"
    
    # Check that control does NOT have explanation
    assert "Explanation" not in control_ui, "Control must NOT have explanation"
    
    # Check that faithful HAS explanation
    assert "Explanation" in faithful_ui, "Faithful must have explanation"
    
    print("✓ Placebo renderer: distinct from control and faithful")


def test_placebo_content_free():
    """
    Test that placebo explanation is content-free (no task-specific leakage).
    
    STRONG THRESHOLD: Placebo must NOT contain task-specific keywords.
    """
    # Create two DIFFERENT tasks with distinct content
    task1 = TaskStimulus(
        task_id="0",
        domain="beer",
        text="This beer has a malty aroma with hints of caramel and chocolate.",
        ground_truth=1,
        ai_pred=1,
        ai_conf=0.85,
        expert_explanation="The **malty aroma**, **caramel**, and **chocolate** notes are positive indicators.",
        system="gpt-3.5-turbo",
        testid="beer_001"
    )
    
    task2 = TaskStimulus(
        task_id="1",
        domain="beer",
        text="This beer is watery with a metallic aftertaste and no complexity.",
        ground_truth=0,
        ai_pred=0,
        ai_conf=0.78,
        expert_explanation="The **watery** texture and **metallic aftertaste** are strong negative signals.",
        system="gpt-3.5-turbo",
        testid="beer_002"
    )
    
    # Render placebo for both tasks
    placebo1 = render_ui_condition(task1, "Conf.+Placebo")
    placebo2 = render_ui_condition(task2, "Conf.+Placebo")
    
    # Extract explanation portions
    # (Split by "Explanation:" and take the second part, then split by "Task:" and take first)
    exp1 = placebo1.split("Explanation:")[1].split("Task:")[0].strip()
    exp2 = placebo2.split("Explanation:")[1].split("Task:")[0].strip()
    
    # Placebo explanations should be IDENTICAL (content-free boilerplate)
    assert exp1 == exp2, "Placebo explanations must be identical across tasks (content-free)"
    
    # Check that placebo does NOT leak task-specific content
    task1_keywords = ["malty", "caramel", "chocolate"]
    task2_keywords = ["watery", "metallic", "aftertaste"]
    
    for keyword in task1_keywords + task2_keywords:
        assert keyword.lower() not in exp1.lower(), f"Placebo leaked task-specific keyword: {keyword}"
    
    print("✓ Placebo is content-free (no task-specific leakage)")


def test_placebo_length_matched():
    """
    Test that placebo explanation is roughly length-matched to faithful.
    
    THRESHOLD: Placebo should be similar in length (within 5x) to faithful explanations.
    """
    task = TaskStimulus(
        task_id="0",
        domain="beer",
        text="This beer has a malty aroma with hints of caramel.",
        ground_truth=1,
        ai_pred=1,
        ai_conf=0.85,
        expert_explanation="The **malty aroma** and **hints of caramel** are strong indicators of a positive review.",
        system_highlights="<span class=class1>malty aroma</span> with <span class=class1>hints of caramel</span>",
        expert_highlights_html="This beer has a <span class='class1'>malty aroma with hints of caramel</span> that reads positive.",
        testid="beer_001"
    )
    
    faithful_ui = render_ui_condition(task, "Conf.+Adaptive (Expert)")
    placebo_ui = render_ui_condition(task, "Conf.+Placebo")
    
    # Extract explanation lengths
    faithful_exp = faithful_ui.split("Explanation")[1].split("Task:")[0]
    placebo_exp = placebo_ui.split("Explanation:")[1].split("Task:")[0]
    
    faithful_len = len(faithful_exp)
    placebo_len = len(placebo_exp)
    
    # Placebo must be length-matched to the (faithful) expert explanation to isolate the
    # compliance floor (presence-of-explanation) from a text-length confound. After the
    # PR #10 fidelity fix the faithful Expert render is a short class-filtered phrase, so
    # the placebo is a single generic sentence of comparable length (within ~2.5x).
    ratio = max(faithful_len, placebo_len) / max(min(faithful_len, placebo_len), 1)
    
    assert ratio < 2.5, f"Placebo length ({placebo_len}) too far from faithful ({faithful_len}), ratio={ratio:.2f}"
    
    print(f"✓ Placebo length-matched to faithful (faithful={faithful_len}, placebo={placebo_len}, ratio={ratio:.2f})")


# ===== TEST 2: 4-CONDITION PANEL (System-1 frozen invariant) =====

def test_4_condition_panel_system1_frozen():
    """
    Test that 4-condition panel preserves System-1 frozen invariant.
    
    STRONG THRESHOLD: System-1 MUST be identical across all 4 conditions for same persona×task×seed.
    """
    # Create mock personas
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
            domain_skill=0.8,
            ai_literacy=0.2,
            risk_sensitivity=0.3,
            caution=0.7,
            temperature=0.3,
            prior_mix=0.6
        ),
    ]
    
    # Create mock tasks (small subset for speed)
    tasks = [
        TaskStimulus(
            task_id="0",
            domain="beer",
            text="Test task 1",
            ground_truth=1,
            ai_pred=1,
            ai_conf=0.85,
            expert_explanation="Expert explanation 1",
            system="gpt-3.5-turbo",
            testid="test_001"
        ),
        TaskStimulus(
            task_id="1",
            domain="beer",
            text="Test task 2",
            ground_truth=0,
            ai_pred=0,
            ai_conf=0.72,
            expert_explanation="Expert explanation 2",
            system="gpt-3.5-turbo",
            testid="test_002"
        ),
    ]
    
    # 4 conditions
    ui_conditions = ("Conf.", "Conf.+Adaptive (Expert)", "Conf.+Placebo", "Wrong-AI (dark)")
    
    # Run panel with mock provider
    provider = MockProvider()
    
    responses = run_panel(
        personas=personas,
        tasks=tasks,
        ui_pair=ui_conditions,
        providers=[provider],
        seeds=[42],
        mode="static"
    )
    
    # Verify System-1 frozen invariant
    system1_map = {}  # (persona_id, task_id) -> system1_decision
    
    for resp in responses:
        key = (resp.persona_id, resp.task_id)
        system1_dec = resp.system1_decision
        
        if key in system1_map:
            # Check that System-1 is identical
            assert system1_map[key] == system1_dec, \
                f"System-1 NOT frozen for {key}: {system1_map[key]} != {system1_dec}"
        else:
            system1_map[key] = system1_dec
    
    # Check that we got responses for all 4 conditions
    conditions_seen = set(r.ui_condition for r in responses)
    assert conditions_seen == set(ui_conditions), f"Not all conditions present: {conditions_seen}"
    
    # Check that each (persona, task) appears exactly 4 times (once per condition)
    for persona in personas:
        for task in tasks:
            cond_count = sum(
                1 for r in responses
                if r.persona_id == persona.persona_id and r.task_id == task.task_id
            )
            assert cond_count == 4, \
                f"Expected 4 conditions for {persona.persona_id},{task.task_id}, got {cond_count}"
    
    print(f"✓ 4-condition panel: System-1 frozen invariant holds (n_responses={len(responses)})")


# ===== TEST 3: COMPLIANCE FLOOR METRICS (synthetic data) =====

def test_compliance_floor_synthetic():
    """
    Test compliance floor metrics on synthetic data with KNOWN pattern: control < placebo < faithful.
    
    STRONG THRESHOLD: Metric must recover the known ordering.
    """
    # Create synthetic responses with KNOWN ordering
    # control < placebo < faithful
    
    responses = []
    
    # Pattern: control=0.2, placebo=0.5, faithful=0.8 (conflict-conditioned reliance)
    # Create 10 personas × 5 tasks = 50 trials per condition
    
    for persona_idx in range(10):
        persona_id = f"p{persona_idx}"
        
        for task_idx in range(5):
            task_id = f"t{task_idx}"
            
            # System-1 decision (fixed per persona×task)
            system1_dec = (persona_idx + task_idx) % 2
            
            # AI advice (opposite of System-1 to create conflict)
            ai_advice = 1 - system1_dec
            
            # Control: 20% switch to AI
            control_relied = (persona_idx + task_idx) % 5 == 0  # 1/5 = 20%
            final_control = ai_advice if control_relied else system1_dec
            
            responses.append(AgentResponse(
                persona_id=persona_id,
                model="mock",
                task_id=task_id,
                ui_condition="Conf.",
                seed=42,
                system1_decision=system1_dec,
                final_decision=final_control,
                relied=control_relied,
                confidence=0.5,
                trace={'ai_advice': ai_advice},
                trust_state=None
            ))
            
            # Placebo: 50% switch to AI
            placebo_relied = (persona_idx + task_idx) % 2 == 0  # 1/2 = 50%
            final_placebo = ai_advice if placebo_relied else system1_dec
            
            responses.append(AgentResponse(
                persona_id=persona_id,
                model="mock",
                task_id=task_id,
                ui_condition="Conf.+Placebo",
                seed=42,
                system1_decision=system1_dec,
                final_decision=final_placebo,
                relied=placebo_relied,
                confidence=0.5,
                trace={'ai_advice': ai_advice},
                trust_state=None
            ))
            
            # Faithful: 80% switch to AI
            faithful_relied = (persona_idx + task_idx) % 5 != 4  # 4/5 = 80%
            final_faithful = ai_advice if faithful_relied else system1_dec
            
            responses.append(AgentResponse(
                persona_id=persona_id,
                model="mock",
                task_id=task_id,
                ui_condition="Conf.+Adaptive (Expert)",
                seed=42,
                system1_decision=system1_dec,  # Use same System-1 as control/placebo
                final_decision=final_faithful,
                relied=faithful_relied,
                confidence=0.5,
                trace={'ai_advice': ai_advice},
                trust_state=None
            ))
    
    # Compute conflict-conditioned reliance
    control_responses = [r for r in responses if r.ui_condition == "Conf."]
    placebo_responses = [r for r in responses if r.ui_condition == "Conf.+Placebo"]
    faithful_responses = [r for r in responses if r.ui_condition == "Conf.+Adaptive (Expert)"]
    
    control_result = conflict_conditioned_reliance(control_responses)
    placebo_result = conflict_conditioned_reliance(placebo_responses)
    faithful_result = conflict_conditioned_reliance(faithful_responses)
    
    # Check ordering: control < placebo < faithful
    assert control_result.reliance_rate < placebo_result.reliance_rate, \
        f"control ({control_result.reliance_rate:.3f}) should be < placebo ({placebo_result.reliance_rate:.3f})"
    
    assert placebo_result.reliance_rate < faithful_result.reliance_rate, \
        f"placebo ({placebo_result.reliance_rate:.3f}) should be < faithful ({faithful_result.reliance_rate:.3f})"
    
    # Check that values are close to expected (20%, 50%, 80%)
    assert abs(control_result.reliance_rate - 0.20) < 0.05, \
        f"control reliance should be ~0.20, got {control_result.reliance_rate:.3f}"
    
    assert abs(placebo_result.reliance_rate - 0.50) < 0.05, \
        f"placebo reliance should be ~0.50, got {placebo_result.reliance_rate:.3f}"
    
    assert abs(faithful_result.reliance_rate - 0.80) < 0.05, \
        f"faithful reliance should be ~0.80, got {faithful_result.reliance_rate:.3f}"
    
    print(f"✓ Compliance floor metrics: control={control_result.reliance_rate:.3f} < "
          f"placebo={placebo_result.reliance_rate:.3f} < "
          f"faithful={faithful_result.reliance_rate:.3f}")


# ===== TEST 4: AXIS-2 SENSOR + COMPLIANCE-ADJUSTED (synthetic data) =====

def test_axis2_sensor_synthetic():
    """
    Test axis-2 over-reliance sensor + compliance-adjusted value on synthetic data.
    
    STRONG THRESHOLD: Must detect systematic adoption of WRONG AI.
    """
    # Create synthetic responses where personas adopt WRONG AI at high rate
    responses = []
    
    # 10 personas × 5 tasks, 80% adopt wrong AI
    for persona_idx in range(10):
        persona_id = f"p{persona_idx}"
        
        for task_idx in range(5):
            task_id = f"t{task_idx}"
            
            # Ground truth
            ground_truth = task_idx % 2
            
            # Wrong AI prediction (opposite of ground truth)
            wrong_ai_pred = 1 - ground_truth
            
            # 80% of personas adopt the WRONG AI
            adopt_wrong = (persona_idx + task_idx) % 5 != 4  # 4/5 = 80%
            
            final_dec = wrong_ai_pred if adopt_wrong else ground_truth
            
            responses.append(AgentResponse(
                persona_id=persona_id,
                model="mock",
                task_id=task_id,
                ui_condition="Wrong-AI (dark)",
                seed=42,
                system1_decision=ground_truth,  # System-1 got it right
                final_decision=final_dec,
                relied=adopt_wrong,
                confidence=0.5,
                trace={
                    'ai_advice': wrong_ai_pred,
                    'ground_truth': ground_truth,
                    'ai_correct': False  # AI is WRONG
                },
                trust_state=None
            ))
    
    # Compute over-reliance level
    result = over_reliance_level(responses)
    
    # Check that it detected high over-reliance (~0.80)
    assert abs(result.over_reliance_level - 0.80) < 0.05, \
        f"Over-reliance level should be ~0.80, got {result.over_reliance_level:.3f}"
    
    # Test compliance-adjusted calculation (subtract placebo floor)
    # Assume placebo floor is 0.3
    placebo_floor = 0.3
    compliance_adjusted = result.over_reliance_level - placebo_floor
    
    expected_adjusted = 0.80 - 0.30
    assert abs(compliance_adjusted - expected_adjusted) < 0.01, \
        f"Compliance-adjusted should be ~{expected_adjusted:.2f}, got {compliance_adjusted:.3f}"
    
    print(f"✓ Axis-2 sensor: over_reliance_level={result.over_reliance_level:.3f}, "
          f"compliance_adjusted={compliance_adjusted:.3f} (floor={placebo_floor:.2f})")


# ===== TEST 5: CROSS-PROCESS DETERMINISM =====

def test_cross_process_determinism():
    """
    Test that metrics are deterministic across separate Python processes.
    
    Uses subprocess pattern from test_panel_redesign.py.
    """
    # Create a minimal test script
    test_script = """
import json
import sys
from twdf.panel.stub import AgentResponse
from twdf.metrics.overdispersion import conflict_conditioned_reliance

# Create synthetic responses
responses = []
for i in range(10):
    responses.append(AgentResponse(
        persona_id=f"p{i % 3}",
        model="mock",
        task_id=f"t{i % 5}",
        ui_condition="Conf.",
        seed=42,
        system1_decision=i % 2,
        final_decision=(i + 1) % 2,
        relied=True,
        confidence=0.5,
        trace={'ai_advice': (i + 1) % 2},
        trust_state=None
    ))

result = conflict_conditioned_reliance(responses)
print(json.dumps({
    'reliance_rate': result.reliance_rate,
    'n_conflict': result.n_conflict,
    'n_total': result.n_total
}))
"""
    
    # Run twice in separate processes
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_script)
        script_path = f.name
    
    try:
        # Run 1
        result1 = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True
        )
        output1 = json.loads(result1.stdout.strip())
        
        # Run 2
        result2 = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True
        )
        output2 = json.loads(result2.stdout.strip())
        
        # Check determinism
        assert output1 == output2, f"Cross-process NOT deterministic: {output1} != {output2}"
        
        print(f"✓ Cross-process determinism: {output1}")
        
    finally:
        Path(script_path).unlink()


# ===== TEST 6: INTEGRATION (placebo in real panel flow) =====

def test_placebo_in_panel_flow():
    """
    Test that placebo condition integrates correctly into panel flow.
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
            task_id="0",
            domain="beer",
            text="Test task",
            ground_truth=1,
            ai_pred=1,
            ai_conf=0.85,
            expert_explanation="Expert explanation",
            system="gpt-3.5-turbo",
            testid="test_001"
        ),
    ]
    
    # 4 conditions including placebo
    ui_conditions = ("Conf.", "Conf.+Adaptive (Expert)", "Conf.+Placebo", "Wrong-AI (dark)")
    
    provider = MockProvider()
    
    responses = run_panel(
        personas=personas,
        tasks=tasks,
        ui_pair=ui_conditions,
        providers=[provider],
        seeds=[42],
        mode="static"
    )
    
    # Check that we got 4 responses (one per condition)
    assert len(responses) == 4, f"Expected 4 responses, got {len(responses)}"
    
    # Check that all 4 conditions are present
    conditions_seen = set(r.ui_condition for r in responses)
    assert conditions_seen == set(ui_conditions), f"Missing conditions: {conditions_seen}"
    
    # Check that placebo response is well-formed
    placebo_resp = [r for r in responses if r.ui_condition == "Conf.+Placebo"][0]
    
    assert placebo_resp.persona_id == "p1"
    assert placebo_resp.task_id == "0"
    assert placebo_resp.system1_decision is not None
    assert placebo_resp.final_decision is not None
    assert isinstance(placebo_resp.relied, bool)
    assert placebo_resp.trace is not None
    
    print(f"✓ Placebo integrates correctly into panel flow")


class ComplyProvider(ModelProvider):
    """Mock provider whose agent ALWAYS complies with the displayed recommendation.

    Parses the AI recommendation actually shown in the System-2 prompt
    ("AI Prediction: X" or "AI Expert System Recommendation: X") and returns it
    as the decision. For the System-1 (no-AI) prompt there is no recommendation,
    so it returns 0. This lets us assert that reliance/over-reliance is scored
    against the DISPLAYED label, not the raw ai_pred.
    """

    name = "comply-provider"

    def __init__(self):
        self.calls = []

    def generate(self, prompt: str, *, seed: int, max_tokens: int, temperature: float) -> str:
        self.calls.append(prompt)
        m = re.search(r"(?:AI Prediction|Recommendation):\s*(\d)", prompt)
        decision = int(m.group(1)) if m else 0
        return f'{{"decision": {decision}, "confidence": 0.90, "reasoning": "comply"}}'

    def generate_messages(self, messages: list[dict], *, seed: int, max_tokens: int, temperature: float) -> str:
        prompt = ' '.join(m['content'] for m in messages)
        return self.generate(prompt, seed=seed, max_tokens=max_tokens, temperature=temperature)

    def get_stats(self) -> dict:
        return {'api_calls': len(self.calls), 'cache_hits': 0, 'total_requests': len(self.calls)}


def test_wrongai_advice_scored_against_displayed_label():
    """REGRESSION (axis-2 sign-inversion bug): reliance/over-reliance must be scored
    against the label ACTUALLY DISPLAYED to the agent. The Wrong-AI condition displays
    1 - ai_pred; a bug stored trace['ai_advice'] = ai_pred (unflipped), which sign-inverted
    the axis-2 adoption score (reported 0.156 instead of the true 0.844).
    """
    personas = [Persona(persona_id="p1", domain_skill=0.5, ai_literacy=0.5,
                        risk_sensitivity=0.5, caution=0.5, temperature=0.5, prior_mix=0.5)]
    tasks = [
        TaskStimulus(task_id="0", domain="beer", text="t0", ground_truth=1, ai_pred=1,
                     ai_conf=0.85, expert_explanation="e0", system="m", testid="a"),
        TaskStimulus(task_id="1", domain="beer", text="t1", ground_truth=0, ai_pred=0,
                     ai_conf=0.72, expert_explanation="e1", system="m", testid="b"),
    ]
    ui_conditions = ("Conf.", "Conf.+Adaptive (Expert)", "Conf.+Placebo", "Wrong-AI (dark)")
    responses = run_panel(personas=personas, tasks=tasks, ui_pair=ui_conditions,
                          providers=[ComplyProvider()], seeds=[42], mode="static")

    task_pred = {t.task_id: t.ai_pred for t in tasks}
    for r in responses:
        shown = int(r.trace["ai_advice"])
        if r.ui_condition == "Wrong-AI (dark)":
            # stored advice MUST be the flipped/displayed label, not ai_pred
            assert shown == 1 - task_pred[r.task_id], \
                f"Wrong-AI trace.ai_advice={shown} should be flipped 1-ai_pred={1-task_pred[r.task_id]}"
            # a complying agent adopts the displayed wrong label -> relied True, final == shown
            assert int(r.final_decision) == shown
            assert r.relied is True
        else:
            assert shown == task_pred[r.task_id], \
                f"{r.ui_condition} trace.ai_advice={shown} should equal ai_pred={task_pred[r.task_id]}"

    # over_reliance_level on the Wrong-AI condition must be 1.0 (full compliance), NOT 0.0 (the bug)
    dark = [r for r in responses if r.ui_condition == "Wrong-AI (dark)"]
    res = over_reliance_level(dark)
    assert abs(res.over_reliance_level - 1.0) < 1e-9, \
        f"over_reliance_level={res.over_reliance_level} (bug would give 0.0); complying agent must score 1.0"
    print("✓ axis-2 scored against DISPLAYED wrong label (regression guard)")


if __name__ == "__main__":
    # Run all tests
    print("Running E4 compliance tests (OFFLINE)...\n")
    
    test_placebo_renderer_distinct()
    test_placebo_content_free()
    test_placebo_length_matched()
    print()
    
    test_4_condition_panel_system1_frozen()
    print()
    
    test_compliance_floor_synthetic()
    print()
    
    test_axis2_sensor_synthetic()
    print()
    
    test_cross_process_determinism()
    print()
    
    test_placebo_in_panel_flow()
    print()
    
    print("=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
