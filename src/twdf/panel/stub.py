"""
Synthetic panel stub (Module B placeholder for v0).

⚠️ THIS IS A STUB: NOT a real LLM panel, just a deterministic generator.

The full panel engine (LLM-based personas with counterfactual pairing) is 
deferred. This stub allows the v0 pipeline to run end-to-end offline by 
generating synthetic AgentResponse-shaped records with tunable disagreement.

Purpose: Prove the chain works (data -> panel -> metrics -> correlation).
Real panel implementation is a separate work stream.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class Persona:
    """Persona configuration (INTERFACES.md §3)."""
    persona_id: str
    domain_skill: float
    ai_literacy: float
    risk_sensitivity: float
    caution: float
    temperature: float
    prior_mix: float


@dataclass(frozen=True)
class AgentResponse:
    """
    Agent decision response (INTERFACES.md §3).
    
    For v0 stub: generated synthetically, not from real LLM.
    """
    persona_id: str
    model: str
    task_id: str
    ui_condition: str
    seed: int
    system1_decision: str
    final_decision: str
    relied: bool
    confidence: float
    trace: dict
    trust_state: Optional[float] = None


def generate_synthetic_panel(
    personas: list[Persona],
    tasks: list[str],
    ui_conditions: list[str],  # Changed from ui_pair tuple to list
    *,
    base_reliance: dict[str, float],  # ui_condition -> base reliance rate
    persona_spread: float = 0.2,      # how much personas differ
    seed: int = 42
) -> list[AgentResponse]:
    """
    ⚠️ STUB: Generate synthetic panel responses with tunable disagreement.
    
    This is NOT a real model panel. It's a deterministic generator that produces
    AgentResponse-shaped records to let the pipeline run without waiting for
    the full LLM panel implementation.
    
    Disagreement mechanism:
    - Each persona has a base reliance probability that varies by UI condition
    - Personas differ from each other (controlled by persona_spread)
    - Higher persona_spread -> more between-persona disagreement -> higher over-dispersion
    - Different conditions can have different base reliance rates and spreads
    
    Args:
        personas: List of persona configs
        tasks: List of task IDs to generate responses for
        ui_conditions: List of UI condition names (multi-condition support)
        base_reliance: Mapping from ui_condition to base reliance rate (0-1)
        persona_spread: How much personas differ (0 = identical, 1 = very diverse)
        seed: Random seed for reproducibility
    
    Returns:
        List of synthetic AgentResponse records
    """
    rng = np.random.RandomState(seed)
    
    responses = []
    
    for ui_cond in ui_conditions:  # Changed from ui_pair to ui_conditions
        base_p = base_reliance.get(ui_cond, 0.5)
        
        for persona in personas:
            # Each persona gets an offset from base, controlled by spread
            # Use deterministic hash of persona_id for reproducibility
            # Note: Python's hash() is NOT deterministic across runs, so use a stable hash
            import hashlib
            persona_hash = int(hashlib.md5(persona.persona_id.encode()).hexdigest()[:8], 16) % 1000 / 1000.0
            offset = (persona_hash - 0.5) * 2 * persona_spread  # range [-spread, +spread]
            persona_p = np.clip(base_p + offset, 0.01, 0.99)
            
            for task_id in tasks:
                # Deterministic but pseudo-random decision per (persona, task, ui)
                # Use stable hash instead of Python's non-deterministic hash()
                import hashlib
                hash_input = f"{persona.persona_id}|{task_id}|{ui_cond}"
                decision_seed = seed + int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16) % 10000
                task_rng = np.random.RandomState(decision_seed)
                
                # Simple model: rely on AI with probability persona_p
                relied = task_rng.rand() < persona_p
                
                # Dummy decisions (in real panel, these would be actual answers)
                system1_decision = task_rng.choice(['A', 'B', 'C', 'D'])
                ai_advice = task_rng.choice(['A', 'B', 'C', 'D'])
                final_decision = ai_advice if relied else system1_decision
                
                responses.append(AgentResponse(
                    persona_id=persona.persona_id,
                    model="stub-synthetic",
                    task_id=task_id,
                    ui_condition=ui_cond,
                    seed=decision_seed,
                    system1_decision=system1_decision,
                    final_decision=final_decision,
                    relied=relied,
                    confidence=persona_p,  # using reliance prob as confidence proxy
                    trace={'stub': True, 'persona_p': persona_p}
                ))
    
    return responses


def compute_panel_disagreement(responses: list[AgentResponse], ui_condition: str) -> float:
    """
    Compute panel disagreement (variance in reliance) for a given UI condition.
    
    This is the panel-side signal that should correlate with human over-dispersion.
    
    Args:
        responses: List of agent responses
        ui_condition: Which UI condition to analyze
    
    Returns:
        Disagreement metric (variance in per-persona reliance rates)
    """
    # Filter to this UI condition
    ui_responses = [r for r in responses if r.ui_condition == ui_condition]
    
    if not ui_responses:
        return 0.0
    
    # Compute per-persona reliance rate
    persona_reliance = {}
    for resp in ui_responses:
        if resp.persona_id not in persona_reliance:
            persona_reliance[resp.persona_id] = []
        persona_reliance[resp.persona_id].append(float(resp.relied))
    
    # Average reliance per persona
    persona_means = [np.mean(rates) for rates in persona_reliance.values()]
    
    # Disagreement = variance across personas
    return float(np.var(persona_means, ddof=1) if len(persona_means) > 1 else 0.0)
