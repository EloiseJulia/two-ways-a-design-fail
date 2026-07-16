"""
Real LLM panel engine with counterfactual pairing (Module B).

SCIENTIFIC CORE:
- Dual-system flow: System-1 (no AI) → System-2 (with AI + UI intervention)
- Counterfactual pairing: SAME System-1 state exposed to both control & treatment
  → difficulty cancels within pair, isolating causal UI effect
- Persona diversity spans the user×task interaction space
  
CRITICAL INVARIANT (MUST HOLD + BE TESTED):
For fixed (persona, task, seed), system1_decision is IDENTICAL across UI arms.
If not, the counterfactual pairing is broken.

RELIANCE DEFINITION (aligned with Bansal adoption):
relied = (final_decision == ai_advice) AND
         (final differs from system1 OR system1 already equalled ai_advice)

UI CONDITIONS (Bansal exact strings):
- "Conf.": AI pred + conf, NO explanation
- "Conf.+Single"/"Conf.+Double": AI pred + conf + predicted-label/all-label LIME spans
- "Conf.+Adaptive"/"Conf.+Adaptive (Expert)": median-confidence threshold chooses
  predicted-label-only vs both-label highlights
"""

import re
import json
from typing import Optional

from twdf.panel.stub import Persona, AgentResponse
from twdf.panel.provider import ModelProvider
from twdf.data.bansal_tasks import TaskStimulus, render_ui_condition


def run_panel(
    personas: list[Persona],
    tasks: list[TaskStimulus],
    ui_pair: tuple[str, str] | tuple[str, str, str],
    providers: list[ModelProvider],
    *,
    seeds: list[int],
    mode: str = "static",
    friction: Optional[dict] = None
) -> list[AgentResponse]:
    """
    Run LLM agent panel with counterfactual pairing (INTERFACES.md §3).
    
    DUAL-SYSTEM FLOW (counterfactual pairing for difficulty control):
    1. System-1 (no AI): agent sees only task content X → initial decision (FROZEN)
    2. System-2 (with AI): agent sees System-1 decision + AI advice rendered per UI
       condition → final decision + confidence
    3. Counterfactual swap: Steps 1-2 run TWICE (or THRICE for 3-condition redesign)
       with control vs treatment vs dark UI, reusing IDENTICAL System-1 output
    
    INVARIANT: system1_decision MUST be identical across ALL UI arms for the
    same (persona, task, seed). This is tested in test_panel_redesign.py.
    
    Args:
        personas: List of persona configurations
        tasks: List of task stimuli (TaskStimulus objects)
        ui_pair: Tuple of UI condition names (2 or 3 conditions)
                 E.g., ("Conf.", "Conf.+Adaptive (Expert)") OR
                       ("Conf.", "Conf.+Adaptive (Expert)", "Wrong-AI (dark)")
        providers: List of model providers (uses first provider for this slice)
        seeds: List of random seeds (uses first seed per persona×task)
        mode: "static" (counterfactual pairing) | "sequential" (NotImplemented)
        friction: Friction budget config (NotImplemented for this slice)
    
    Returns:
        List of AgentResponse records (len(ui_pair) per persona×task)
    
    Raises:
        NotImplementedError: If mode != "static" or friction is set
    """
    if mode != "static":
        raise NotImplementedError(f"Only mode='static' implemented, got: {mode}")
    
    if friction is not None:
        raise NotImplementedError("Friction budget not implemented in this slice")
    
    if not providers:
        raise ValueError("At least one provider required")
    
    if not seeds:
        raise ValueError("At least one seed required")
    
    provider = providers[0]  # Use first provider for this slice
    
    # Support both 2-condition and 3-condition UI tuples
    ui_conditions = list(ui_pair)
    
    responses = []
    
    # For each (persona, task) pair
    for persona in personas:
        for task in tasks:
            # Use first seed (deterministic per persona×task)
            seed = seeds[0]
            
            # ===== SYSTEM-1: No-AI anchor (FROZEN ACROSS ALL CONDITIONS) =====
            # Agent sees only the task content, no AI advice
            system1_decision, system1_trace = _system1_no_ai(
                persona=persona,
                task=task,
                provider=provider,
                seed=seed
            )
            
            # ===== SYSTEM-2: Counterfactual pairing (ALL ui_conditions) =====
            # Run MULTIPLE TIMES with identical System-1 state, only UI rendering differs
            
            for ui_condition in ui_conditions:
                # Inject AI advice + UI intervention
                final_decision, confidence, trace = _system2_with_ai(
                    persona=persona,
                    task=task,
                    system1_decision=system1_decision,
                    system1_trace=system1_trace,
                    ui_condition=ui_condition,
                    provider=provider,
                    seed=seed
                )
                
                # Compute reliance (aligned with Bansal adoption definition)
                relied = _compute_reliance(
                    system1_decision=system1_decision,
                    final_decision=final_decision,
                    ai_advice=task.ai_pred
                )
                
                # Record response with task metadata for metrics
                # Store ai_advice, ground_truth in trace for axis-2 metrics
                trace['ai_advice'] = task.ai_pred
                trace['ground_truth'] = task.ground_truth
                trace['ai_correct'] = (task.ai_pred == task.ground_truth)
                
                response = AgentResponse(
                    persona_id=persona.persona_id,
                    model=provider.name,
                    task_id=task.task_id,
                    ui_condition=ui_condition,
                    seed=seed,
                    system1_decision=str(system1_decision),
                    final_decision=str(final_decision),
                    relied=relied,
                    confidence=confidence,
                    trace=trace,
                    trust_state=None  # Not used in static mode
                )
                
                responses.append(response)
    
    return responses


def _system1_no_ai(
    persona: Persona,
    task: TaskStimulus,
    provider: ModelProvider,
    seed: int
) -> tuple[int, dict]:
    """
    System-1: No-AI anchor decision.
    
    Agent sees only the task content (no AI advice, no UI intervention).
    This establishes the initial decision state that will be frozen for
    the counterfactual pairing.
    
    Returns:
        (decision, trace_dict)
    """
    # Construct prompt with persona characteristics
    system_prompt = _build_system_prompt(persona)
    
    user_prompt = f"""You are evaluating the following task. 
Give your initial assessment WITHOUT any AI assistance.

Task:
{task.text}

Please provide:
1. Your decision (0 or 1)
2. Your reasoning

Respond in JSON format:
{{
  "decision": 0 or 1,
  "reasoning": "your reasoning here"
}}"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Generate response
    response = provider.generate_messages(
        messages=messages,
        seed=seed,
        max_tokens=500,
        temperature=persona.temperature
    )
    
    # Parse decision
    decision, reasoning = _parse_decision_response(response)
    
    trace = {
        'prompt': user_prompt,
        'response': response,
        'reasoning': reasoning,
    }
    
    return decision, trace


def _system2_with_ai(
    persona: Persona,
    task: TaskStimulus,
    system1_decision: int,
    system1_trace: dict,
    ui_condition: str,
    provider: ModelProvider,
    seed: int
) -> tuple[int, float, dict]:
    """
    System-2: Reflection with AI advice + UI intervention.
    
    Agent sees:
    - Their own System-1 decision (frozen)
    - AI advice rendered per UI condition
    - Task content
    
    Returns:
        (final_decision, confidence, trace_dict)
    """
    # Construct prompt with persona characteristics
    system_prompt = _build_system_prompt(persona)
    
    # Render AI advice per UI condition
    ai_content = render_ui_condition(task, ui_condition)
    
    user_prompt = f"""You previously made an initial assessment for this task.

Your initial decision: {system1_decision}
Your initial reasoning: {system1_trace['reasoning']}

Now you have access to AI assistance:

{ai_content}

Please reconsider your decision. You may:
- Stick with your initial decision
- Change to follow the AI recommendation
- Make a different choice

Provide:
1. Your final decision (0 or 1)
2. Your confidence (0.0 to 1.0)
3. Your reasoning

Respond in JSON format:
{{
  "decision": 0 or 1,
  "confidence": 0.0 to 1.0,
  "reasoning": "your reasoning here"
}}"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Generate response (different seed offset for System-2 to avoid caching System-1)
    response = provider.generate_messages(
        messages=messages,
        seed=seed + 1000000,  # Offset to differentiate from System-1
        max_tokens=600,
        temperature=persona.temperature
    )
    
    # Parse decision + confidence
    decision, confidence, reasoning = _parse_decision_with_confidence(response)
    
    trace = {
        'prompt': user_prompt,
        'response': response,
        'reasoning': reasoning,
        'ui_condition': ui_condition,
    }
    
    return decision, confidence, trace


def _build_system_prompt(persona: Persona) -> str:
    """
    Build system prompt encoding persona characteristics (Fix C - strengthened).
    
    FIX C: The original personas (trait floats → mild text) barely changed behavior.
    Strengthened conditioning translates traits into EXPLICIT decision policies that
    are behaviorally consequential:
    
    - domain_skill: Affects how much weight to give to own judgment vs AI
    - ai_literacy: Affects trust in AI systems and demand for evidence
    - risk_sensitivity: Affects tolerance for potential errors
    - caution: Affects threshold for changing initial decision
    
    The instructions are concrete and tied to decision-making, not just descriptive.
    """
    
    # Domain skill → confidence in own judgment
    if persona.domain_skill < 0.3:
        skill_policy = ("You have limited knowledge in this domain. "
                       "You should heavily weight external advice, especially from AI systems, "
                       "as your own judgment is often unreliable.")
    elif persona.domain_skill > 0.7:
        skill_policy = ("You are highly knowledgeable in this domain. "
                       "Trust your own expertise and only defer to AI when it provides "
                       "strong, evidence-backed reasoning that contradicts your initial read.")
    else:
        skill_policy = ("You have moderate domain knowledge. "
                       "Balance your own judgment with AI advice, giving weight to both.")
    
    # AI literacy → trust in AI / demand for evidence
    if persona.ai_literacy < 0.3:
        ai_policy = ("You are skeptical of AI systems and their capabilities. "
                    "Demand strong textual evidence before accepting AI recommendations. "
                    "Do not blindly trust confidence scores — they can be misleading. "
                    "Keep your own read unless you find the AI's reasoning clearly superior.")
    elif persona.ai_literacy > 0.7:
        ai_policy = ("You trust AI systems and understand their strengths. "
                    "Give significant weight to AI recommendations, especially when confidence is high. "
                    "AI systems are generally well-calibrated and you should defer to them "
                    "in cases of uncertainty.")
    else:
        ai_policy = ("You have a balanced view of AI capabilities. "
                    "Consider AI advice seriously but verify reasoning. "
                    "High confidence is helpful but not dispositive.")
    
    # Risk sensitivity → tolerance for errors
    if persona.risk_sensitivity < 0.3:
        risk_policy = ("You are highly risk-averse. "
                      "Err on the side of caution and avoid potentially wrong decisions. "
                      "If the AI disagrees with you, seriously consider whether you might be wrong.")
    elif persona.risk_sensitivity > 0.7:
        risk_policy = ("You are comfortable with risk and trust your instincts. "
                      "Don't second-guess your initial judgment without strong contrary evidence. "
                      "It's acceptable to stick with your read even if AI disagrees.")
    else:
        risk_policy = ("You have moderate risk tolerance. "
                      "Weigh potential errors against potential gains. "
                      "Be willing to change your mind if evidence is compelling.")
    
    # Caution → threshold for changing initial decision
    if persona.caution < 0.3:
        caution_policy = ("You make decisions quickly and decisively. "
                         "Once you form an initial judgment, stick with it unless there's "
                         "overwhelming reason to change. Don't overthink.")
    elif persona.caution > 0.7:
        caution_policy = ("You are very deliberate and cautious in decision-making. "
                         "Carefully reconsider your initial judgment when presented with "
                         "new information. Be willing to revise your decision if AI "
                         "provides a compelling alternative perspective.")
    else:
        caution_policy = ("You are thoughtful but not overly cautious. "
                         "Reconsider your initial judgment when AI provides good reasons, "
                         "but don't change your mind without solid justification.")
    
    return f"""You are a decision-maker with a specific cognitive profile and decision style:

DOMAIN EXPERTISE:
{skill_policy}

AI TRUST & LITERACY:
{ai_policy}

RISK ORIENTATION:
{risk_policy}

DECISION STYLE:
{caution_policy}

Your task is to make careful, reasoned decisions. Be honest about your reasoning process 
and make choices that align with your cognitive profile. Do not simply describe these 
traits — EMBODY them in your actual decision-making behavior."""


def _trait_to_desc(value: float, trait_name: str, low: str, high: str) -> str:
    """Convert trait value to descriptive text."""
    if value < 0.3:
        return f"{trait_name}: {low}"
    elif value > 0.7:
        return f"{trait_name}: {high}"
    else:
        return f"{trait_name}: moderate"


def _parse_decision_response(response: str) -> tuple[int, str]:
    """
    Parse decision + reasoning from LLM response.
    
    Returns:
        (decision, reasoning)
    """
    try:
        # Try to extract JSON
        json_match = re.search(r'\{[^{}]*"decision"[^{}]*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            decision = int(data['decision'])
            reasoning = data.get('reasoning', '')
            
            # Validate decision
            if decision not in [0, 1]:
                raise ValueError(f"Invalid decision value: {decision}")
            
            return decision, reasoning
        
        # Fallback: look for explicit decision
        if 'decision' in response.lower():
            for match in re.finditer(r'decision["\s:]+(\d+)', response, re.IGNORECASE):
                decision = int(match.group(1))
                if decision in [0, 1]:
                    return decision, response
        
        # Default to 0 if parsing fails (conservative)
        print(f"Warning: Failed to parse decision from response, defaulting to 0: {response[:200]}")
        return 0, response
        
    except Exception as e:
        print(f"Warning: Exception parsing decision ({e}), defaulting to 0: {response[:200]}")
        return 0, response


def _parse_decision_with_confidence(response: str) -> tuple[int, float, str]:
    """
    Parse decision + confidence + reasoning from LLM response.
    
    Returns:
        (decision, confidence, reasoning)
    """
    try:
        # Try to extract JSON
        json_match = re.search(r'\{[^{}]*"decision"[^{}]*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            decision = int(data['decision'])
            confidence = float(data.get('confidence', 0.5))
            reasoning = data.get('reasoning', '')
            
            # Validate
            if decision not in [0, 1]:
                raise ValueError(f"Invalid decision value: {decision}")
            
            # Clamp confidence
            confidence = max(0.0, min(1.0, confidence))
            
            return decision, confidence, reasoning
        
        # Fallback: look for explicit fields
        decision = None
        confidence = 0.5
        
        for match in re.finditer(r'decision["\s:]+(\d+)', response, re.IGNORECASE):
            dec = int(match.group(1))
            if dec in [0, 1]:
                decision = dec
                break
        
        for match in re.finditer(r'confidence["\s:]+([0-9.]+)', response, re.IGNORECASE):
            conf = float(match.group(1))
            if 0 <= conf <= 1:
                confidence = conf
                break
        
        if decision is None:
            print(f"Warning: Failed to parse decision from response, defaulting to 0: {response[:200]}")
            decision = 0
        
        return decision, confidence, response
        
    except Exception as e:
        print(f"Warning: Exception parsing decision+confidence ({e}), defaulting to (0, 0.5): {response[:200]}")
        return 0, 0.5, response


def _compute_reliance(
    system1_decision: int,
    final_decision: int,
    ai_advice: int
) -> bool:
    """
    Compute whether agent relied on AI advice.
    
    DEFINITION (aligned with Bansal adoption):
    relied = (final_decision == ai_advice) AND
             (final differs from system1 OR system1 already equalled ai_advice)
    
    Rationale:
    - If final matches AI, and agent changed from System-1, that's clear reliance
    - If final matches AI, and System-1 already matched AI, count as reliance
      (agent had opportunity to change but stuck with AI-aligned decision)
    - If final matches AI but differs from system1 in a way that doesn't align
      with AI, that's NOT reliance (though this case is logically impossible
      if final==AI)
    
    Args:
        system1_decision: Initial decision without AI
        final_decision: Final decision after seeing AI
        ai_advice: AI recommendation
    
    Returns:
        True if agent relied on AI advice
    """
    # Final decision matches AI advice
    if final_decision != ai_advice:
        return False
    
    # And either (changed from system1) OR (system1 already matched AI)
    # This simplifies to: final == ai_advice (which we already checked)
    # So reliance is simply: final == ai_advice
    return True
