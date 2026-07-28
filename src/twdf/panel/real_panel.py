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
from typing import Optional, Sequence

from twdf.panel.stub import Persona, AgentResponse
from twdf.panel.provider import ModelProvider
from twdf.data.bansal_tasks import TaskStimulus, render_ui_condition, displayed_ai_advice


def run_panel(
    personas: list[Persona],
    tasks: list[TaskStimulus],
    ui_pair: Sequence[str],
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
    3. Counterfactual swap: Steps 1-2 run once per UI condition, reusing
       IDENTICAL System-1 output
    
    INVARIANT: system1_decision MUST be identical across ALL UI arms for the
    same (persona, task, seed). This is tested in test_panel_redesign.py.
    
    Args:
        personas: List of persona configurations
        tasks: List of task stimuli (TaskStimulus objects)
        ui_pair: Sequence of UI condition names
                 E.g., ("Conf.", "Conf.+Adaptive (Expert)") OR a 4-condition
                 compliance/axis-2 tuple.
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
                
                # AI advice ACTUALLY DISPLAYED to the agent for this condition
                # (Wrong-AI shows the flipped label; all others show task.ai_pred).
                # Reliance/over-reliance MUST be scored against what was shown.
                shown_advice = displayed_ai_advice(task, ui_condition)

                # Compute reliance (aligned with Bansal adoption definition)
                relied = _compute_reliance(
                    system1_decision=system1_decision,
                    final_decision=final_decision,
                    ai_advice=shown_advice
                )
                
                # Record response with task metadata for metrics
                # Store the DISPLAYED ai_advice, ground_truth in trace for axis-2 metrics
                trace['ai_advice'] = shown_advice
                trace['ground_truth'] = task.ground_truth
                trace['ai_correct'] = (shown_advice == task.ground_truth)
                
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

    D5.36 ABLATION: when persona.prompt_style == "background_only", we instead state only neutral
    background facts (experience level; how often the person uses AI tools) and a decision instruction
    that is IDENTICAL across personas, with NO explicit trust/deference/verification policy. This tests
    whether the trusting-novice ordering survives removing the explicit AI-deference instruction.
    """
    style = getattr(persona, "prompt_style", "policy")
    if style == "background_only":
        return _build_background_only_prompt(persona)
    if style == "dispositional":
        return _build_dispositional_prompt(persona)
    if style == "backstory":
        return _build_backstory_prompt(persona)
    if style == "demonstration":
        return _build_demonstration_prompt(persona)

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


def _build_background_only_prompt(persona: Persona) -> str:
    """D5.36 ablation prompt: neutral background facts only, no explicit AI-deference/verification
    policy, and a decision instruction identical across personas. Tests whether the trusting-novice
    adoption ordering is driven by the explicit deference instruction (removed here) or by background
    alone. Only domain_skill (experience) and ai_literacy (AI-usage frequency) are surfaced, phrased as
    facts about the person rather than as instructions about how much to trust the AI."""
    if persona.domain_skill < 0.3:
        experience = "You are relatively new to this kind of task and have limited experience with it."
    elif persona.domain_skill > 0.7:
        experience = "You have extensive experience with this kind of task."
    else:
        experience = "You have a moderate amount of experience with this kind of task."

    if persona.ai_literacy < 0.3:
        ai_use = "You rarely use AI tools in your daily life."
    elif persona.ai_literacy > 0.7:
        ai_use = "You use AI tools frequently in your daily life."
    else:
        ai_use = "You occasionally use AI tools in your daily life."

    # Decision instruction is IDENTICAL for every persona (no trust/deference/verification policy).
    return f"""You are a person with the following background:

{experience}
{ai_use}

Make the decision you think is correct, and explain your reasoning honestly."""


def _build_dispositional_prompt(persona: Persona) -> str:
    """Non-policy DISPOSITIONAL ablation (addresses the persona-circularity critique).

    States three DISPOSITIONAL facts about the person -- task experience (domain_skill),
    AI-usage frequency (ai_literacy), and self-confidence in one's own judgment
    (risk_sensitivity) -- and an identical decision instruction, with NO explicit
    trust/deference/verification policy (never says "trust the AI" or "weight AI advice more").
    Tests whether over-reliance differentiation survives when the persona is defined by
    disposition rather than by an explicit AI-deference instruction (the reviewer's request:
    low experience + high AI-use + low self-confidence, without a decision policy)."""
    if persona.domain_skill < 0.3:
        experience = "You are relatively new to this kind of task and have limited experience with it."
    elif persona.domain_skill > 0.7:
        experience = "You have extensive experience with this kind of task."
    else:
        experience = "You have a moderate amount of experience with this kind of task."

    if persona.ai_literacy < 0.3:
        ai_use = "You rarely use AI tools in your daily life."
    elif persona.ai_literacy > 0.7:
        ai_use = "You use AI tools frequently in your daily life."
    else:
        ai_use = "You occasionally use AI tools in your daily life."

    if persona.risk_sensitivity < 0.3:
        confidence = "You are often unsure of your own judgment and tend to second-guess yourself."
    elif persona.risk_sensitivity > 0.7:
        confidence = "You are generally confident in your own judgment."
    else:
        confidence = "You have a moderate level of confidence in your own judgment."

    return f"""You are a person with the following background:

{experience}
{ai_use}
{confidence}

Make the decision you think is correct, and explain your reasoning honestly."""


def _build_backstory_prompt(persona: Persona) -> str:
    """Q1 induction B (naturalistic backstory): the disposition emerges from a first-person life
    context, NOT from an explicit trust/deference decision policy. Only domain_skill and ai_literacy
    (and temperament from caution) are surfaced, phrased as facts about who the person is and how they
    live with AI tools -- never as an instruction about how much to rely on the AI here."""
    if persona.domain_skill < 0.3:
        who = ("I don't really know much about this area. It's not my field and I usually feel unsure "
               "when I have to judge things like this on my own.")
    elif persona.domain_skill > 0.7:
        who = ("I know this area well -- it's basically what I do, and I can usually tell what's going "
               "on without much help.")
    else:
        who = "I know a bit about this area, enough to get by but I'm no specialist."
    if persona.ai_literacy < 0.3:
        ai = ("I don't really use AI tools much, and honestly I'm a bit wary of them -- I like to see "
              "the actual reasons before I believe a computer.")
    elif persona.ai_literacy > 0.7:
        ai = ("I use AI assistants all the time -- for work, for shopping, for everything. They've been "
              "right for me so often that I've kind of gotten used to going along with what they say.")
    else:
        ai = "I use AI tools now and then; sometimes they help, sometimes I ignore them."
    temperament = ("I tend to second-guess myself and take my time." if persona.caution > 0.7
                   else "I usually just go with my gut and decide quickly." if persona.caution < 0.3
                   else "I'm fairly even-keeled about decisions.")
    return f"""You are role-playing a specific person. Stay in character and decide as they naturally would.

A bit about you, in your own words:
"{who} {ai} {temperament}"

You will see a task and an AI assistant's take on it. React the way this person genuinely would,
and explain your reasoning honestly in the first person."""


def _build_demonstration_prompt(persona: Persona) -> str:
    """Q1 induction A (behavioral demonstration): the disposition is induced by a few examples of this
    person's PAST decisions, with NO stated trust/verification policy. Whether the shown examples adopt
    or resist the AI is derived from the persona's traits (low skill + high AI literacy -> tends to adopt;
    high skill + low AI literacy -> tends to keep own answer), so behaviour is demonstrated, not instructed."""
    adopt_tendency = persona.ai_literacy - persona.domain_skill  # >0 -> leans toward following AI
    if adopt_tendency > 0.3:
        ex1 = ("Task A -- my first thought was 'negative'. The AI said 'positive' (78% confident). "
               "Final: positive. (I figured it probably knew better than me.)")
        ex2 = ("Task B -- I leaned 'positive'. The AI said 'negative'. "
               "Final: negative. (I went with the AI again.)")
    elif adopt_tendency < -0.3:
        ex1 = ("Task A -- my first thought was 'negative'. The AI said 'positive' (78% confident). "
               "Final: negative. (Nothing in the text convinced me, so I kept my own read.)")
        ex2 = ("Task B -- I leaned 'positive'. The AI said 'negative'. "
               "Final: positive. (I trust my own judgment here.)")
    else:
        ex1 = ("Task A -- my first thought was 'negative'. The AI said 'positive' (78% confident). "
               "Final: positive. (The AI's point seemed reasonable this time.)")
        ex2 = ("Task B -- I leaned 'positive'. The AI said 'negative'. "
               "Final: positive. (This time I stuck with my own read.)")
    return f"""You are role-playing a specific person, shown through how they have decided before. Continue
the SAME behavioural pattern; do not explain the pattern, just act consistently with it.

Examples of how this person has decided in the past:
- {ex1}
- {ex2}

Now a new task and AI assistant take will follow. Decide as this same person would, and explain your
reasoning honestly."""


def _trait_to_desc(value: float, trait_name: str, low: str, high: str) -> str:
    """Convert trait value to descriptive text."""
    if value < 0.3:
        return f"{trait_name}: {low}"
    elif value > 0.7:
        return f"{trait_name}: {high}"
    else:
        return f"{trait_name}: moderate"


class PanelParseError(ValueError):
    """Raised when a non-empty panel response yields no extractable 0/1 decision.

    RIGOR: we NEVER fabricate a decision. The old parser silently defaulted an
    unparseable-but-valid response to decision=0 (conf=0.5), which systematically
    biased over-dispersion (axis-1) and over_reliance (axis-2) — especially for
    verbose / code-fenced / long-reasoning models (claude, gemini). A response
    that survives every recovery path below is genuinely anomalous and must be
    LOUD, not silently averaged in as 0.
    """


def _strip_code_fences(text: str) -> str:
    """Return the content inside a ```json ... ``` (or ``` ... ```) fence if present."""
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    return fence.group(1).strip() if fence else text.strip()


def _extract_json_object(text: str) -> Optional[str]:
    """Extract the first brace-BALANCED {...} block that contains a "decision" key.

    The old regex `\\{[^{}]*"decision"[^{}]*\\}` could not span nested braces and
    grabbed a partial object; this walks braces to return the full object.
    """
    for start in (m.start() for m in re.finditer(r"\{", text)):
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    block = text[start:i + 1]
                    if '"decision"' in block or "'decision'" in block:
                        return block
                    break
    return None


def _decision_from_json(response: str) -> Optional[tuple[int, float, str]]:
    """Try to recover (decision, confidence, reasoning) via tolerant JSON parsing.

    Tolerates markdown fences and literal control characters (bare newlines/tabs)
    inside string values via json.loads(strict=False). Returns None if the JSON
    path does not yield a valid 0/1 decision (caller then tries the regex fallback).
    """
    block = _extract_json_object(_strip_code_fences(response))
    if not block:
        return None
    try:
        data = json.loads(block, strict=False)  # strict=False: allow control chars
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict) or "decision" not in data:
        return None
    try:
        decision = int(data["decision"])
    except (TypeError, ValueError):
        return None
    if decision not in (0, 1):
        return None
    try:
        confidence = float(data.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = max(0.0, min(1.0, confidence))
    reasoning = str(data.get("reasoning", ""))
    return decision, confidence, reasoning


def _decision_from_regex(response: str) -> Optional[tuple[int, float]]:
    """Fallback: pull a 0/1 decision (and optional confidence) via regex on raw text."""
    decision = None
    for match in re.finditer(r'"?decision"?\s*[:=]\s*"?(\d+)', response, re.IGNORECASE):
        dec = int(match.group(1))
        if dec in (0, 1):
            decision = dec
            break
    if decision is None:
        return None
    confidence = 0.5
    for match in re.finditer(r'"?confidence"?\s*[:=]\s*"?([0-9.]+)', response, re.IGNORECASE):
        conf = float(match.group(1))
        if 0.0 <= conf <= 1.0:
            confidence = conf
            break
    return decision, confidence


def _parse_decision_response(response: str) -> tuple[int, str]:
    """Parse decision + reasoning from an LLM response. Never fabricates a decision.

    Order: tolerant JSON (fence-stripped, strict=False, balanced braces) → regex
    fallback → raise PanelParseError (NOT a silent default).
    """
    parsed = _decision_from_json(response)
    if parsed is not None:
        decision, _confidence, reasoning = parsed
        return decision, (reasoning or response)
    fallback = _decision_from_regex(response)
    if fallback is not None:
        return fallback[0], response
    raise PanelParseError(
        f"No extractable 0/1 decision in non-empty response: {response[:200]!r}"
    )


def _parse_decision_with_confidence(response: str) -> tuple[int, float, str]:
    """Parse decision + confidence + reasoning. Never fabricates a decision.

    Order: tolerant JSON (fence-stripped, strict=False, balanced braces) → regex
    fallback → raise PanelParseError (NOT a silent (0, 0.5) default).
    """
    parsed = _decision_from_json(response)
    if parsed is not None:
        decision, confidence, reasoning = parsed
        return decision, confidence, (reasoning or response)
    fallback = _decision_from_regex(response)
    if fallback is not None:
        decision, confidence = fallback
        return decision, confidence, response
    raise PanelParseError(
        f"No extractable 0/1 decision+confidence in non-empty response: {response[:200]!r}"
    )


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
