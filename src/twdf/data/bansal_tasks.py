"""
Bansal et al. task stimuli loader for panel experiments.

Source: https://github.com/uw-hai/Complementary-Performance/main/task-examples/
Domains: beer (sentiment), amzbook (review sentiment), lsat (logical reasoning)

Loads task stimuli with AI predictions + explanations for panel experiments.
Verifies testid→questionId join with Bansal decision CSV.
"""

import json
import re
import urllib.request
from html import unescape
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import pandas as pd


@dataclass
class TaskStimulus:
    """Task stimulus for panel experiment."""
    task_id: str  # Maps to Bansal questionId
    domain: str  # 'beer', 'amzbook', or 'lsat'
    text: str  # Raw task content (X)
    ground_truth: int  # Correct answer (Y)
    ai_pred: int  # AI prediction
    ai_conf: float  # AI confidence
    expert_explanation: str  # Expert-highlighted explanation (clean text with **bold**)
    system_highlights: str = ""  # LIME system highlights HTML (raw, for rendering)
    
    # Original fields for reference
    testid: str = ""  # Original test ID from task JSON
    expert_highlights_html: str = ""  # Expert highlights HTML (raw, preserves class tags)
    system: str = ""  # Backward-compatible alias for old test fixtures

    def __post_init__(self) -> None:
        if self.system and not self.system_highlights:
            self.system_highlights = self.system


# Task stimulus URLs (verified 2026-07-15)
TASK_URLS = {
    'beer': 'https://raw.githubusercontent.com/uw-hai/Complementary-Performance/main/task-examples/task-sentiment-beer.json',
    'amzbook': 'https://raw.githubusercontent.com/uw-hai/Complementary-Performance/main/task-examples/task-sentiment-amzbook.json',
    'lsat': 'https://raw.githubusercontent.com/uw-hai/Complementary-Performance/main/task-examples/task-lsat.json',
}


ADAPTIVE_CONF_THRESHOLD = {
    "beer": 0.892,
    "amzbook": 0.889,
}


def _download_if_missing(url: str, local_path: Path) -> Path:
    """Download task JSON if not already cached."""
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    if local_path.exists():
        print(f"Task file already exists: {local_path}")
        return local_path
    
    print(f"Downloading task stimuli from {url}...")
    urllib.request.urlretrieve(url, local_path)
    print(f"Downloaded to {local_path}")
    
    return local_path


def _extract_text_from_html(html: str) -> str:
    """
    Extract plain text from HTML explanation.
    
    For expert explanations with highlights, we render them as **bold**.
    This preserves the cognitive-semantic intervention (emphasis on key phrases).
    """
    # Remove <p> tags
    text = re.sub(r'<p>', '', html)
    text = re.sub(r'</p>', '\n', text)
    
    # Convert <b> to **bold** (markdown emphasis)
    text = re.sub(r'<b>', '**', text)
    text = re.sub(r'</b>', '**', text)
    
    # Remove other HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up whitespace
    text = re.sub(r'\n+', '\n', text)
    text = text.strip()
    
    return text


def adaptive_conf_threshold(domain: str) -> float:
    """Return the fixed Bansal median-confidence threshold for a task domain."""
    try:
        return ADAPTIVE_CONF_THRESHOLD[domain]
    except KeyError as exc:
        raise ValueError(
            f"No adaptive confidence threshold configured for domain '{domain}'. "
            f"Known domains: {sorted(ADAPTIVE_CONF_THRESHOLD)}"
        ) from exc


def _format_highlights(matches: list[tuple[str, str]], unavailable: str) -> str:
    if not matches:
        return unavailable

    highlight_texts = []
    for cls, text in matches:
        direction = "supporting positive" if cls == "class1" else "supporting negative"
        clean_text = re.sub(r"\s+", " ", unescape(text)).strip()
        highlight_texts.append(f'  - "{clean_text}" ({direction})')

    return "Key phrases identified by the AI model:\n" + "\n".join(highlight_texts)


def _extract_lime_highlights(system_html: str, target_classes: set[str]) -> str:
    """
    Extract all LIME system highlights for the requested label classes.
    
    LIME highlights are token-level: `<span class=class0>` (negative) or `<span class=class1>` (positive).
    Selection is by class label, not by token count: Single shows all predicted-class
    spans; Double shows all class0 and class1 spans, preserving document order.
    """
    if not system_html:
        return "(No explanation available)"
    
    highlight_pattern = r"<span class=(class[01])>([^<]+)</span>"
    matches = [
        (cls, text)
        for cls, text in re.findall(highlight_pattern, system_html)
        if cls in target_classes
    ]
    
    return _format_highlights(matches, "(No matching LIME highlights available)")


def _extract_expert_highlights(expert_html: str, target_classes: set[str]) -> str:
    """
    Extract expert phrase spans for the requested classes from raw expert HTML.

    Expert highlights use single-quoted class attributes, e.g.
    `<span class='class0'>phrase</span>`.
    """
    if not expert_html:
        return "(No expert explanation available)"

    highlight_pattern = r"<span class='(class[01])'>([^<]+)</span>"
    matches = [
        (cls, text)
        for cls, text in re.findall(highlight_pattern, expert_html)
        if cls in target_classes
    ]

    return _format_highlights(matches, "(No matching expert highlights available)")


def load_beer_tasks(data_dir: Optional[Path] = None,
                   seed: int = 42,
                   n_tasks: int = 20) -> dict[str, TaskStimulus]:
    """
    Load beer sentiment task stimuli.
    
    CRITICAL: Sampling must be DIVERSE (span both AI-correct and AI-incorrect,
    range of confidence levels) for the decomposition finding to hold.
    
    Args:
        data_dir: Directory for raw data (default: data/raw/)
        seed: Random seed for deterministic task selection
        n_tasks: Number of tasks to select (default: 20)
    
    Returns:
        Dict mapping task_id (str) -> TaskStimulus
    """
    if data_dir is None:
        data_dir = Path("data/raw")
    
    # Download beer tasks
    local_path = data_dir / "task-sentiment-beer.json"
    _download_if_missing(TASK_URLS['beer'], local_path)
    
    # Load JSON
    with open(local_path, 'r', encoding='utf-8') as f:
        raw_tasks = json.load(f)
    
    print(f"Loaded {len(raw_tasks)} beer tasks from {local_path}")
    
    # Parse tasks
    tasks = {}
    for idx, item in enumerate(raw_tasks):
        # Map fields
        # Use array index as task_id to match Bansal questionId (0-49)
        task_id = str(idx)
        testid = str(item['testid'])
        
        task = TaskStimulus(
            task_id=task_id,
            domain='beer',
            text=item['X'],
            ground_truth=int(item['Y']),
            ai_pred=int(item['pred']),
            ai_conf=float(item['conf']),
            expert_explanation=_extract_text_from_html(item['expert']),
            system_highlights=item['system'],  # Raw LIME HTML
            testid=testid,
            expert_highlights_html=item['expert'],
        )
        
        tasks[task_id] = task
    
    # Verify testid→questionId join with Bansal decision CSV
    print("\nVerifying testid→questionId join with Bansal decision data...")
    from twdf.data.bansal import load_bansal
    
    # Load Bansal data (all conditions, all tasks)
    bansal_df = load_bansal(
        data_dir=data_dir,
        task_sample=None,
        ui_conditions=None,
        task_selection='all'
    )
    
    # Filter to beer domain
    beer_trials = bansal_df[bansal_df['extra'].apply(lambda x: x.get('task') == 'beer')]
    beer_questionIds = set(beer_trials['task_id'].astype(str).unique())
    
    # Check overlap
    task_ids_set = set(tasks.keys())
    overlap = task_ids_set & beer_questionIds
    
    print(f"Task stimuli testids: {len(task_ids_set)}")
    print(f"Bansal beer questionIds: {len(beer_questionIds)}")
    print(f"Overlap (join): {len(overlap)}")
    
    if len(overlap) == 0:
        raise RuntimeError(
            "ZERO overlap between task stimuli testids and Bansal beer questionIds! "
            "The join is broken. Cannot proceed with panel experiment."
        )
    
    if len(overlap) < n_tasks:
        print(f"WARNING: Only {len(overlap)} overlapping tasks, but requested n_tasks={n_tasks}")
        print(f"Reducing to {len(overlap)} tasks")
        n_tasks = len(overlap)
    
    # Select diverse subset (deterministic)
    # Sort by task_id for determinism, then select to span diversity
    overlapping_tasks = sorted(overlap)
    
    # Compute diversity metrics for selection
    import numpy as np
    diversity_scores = []
    for tid in overlapping_tasks:
        task = tasks[tid]
        # Diversity = span of AI correctness + confidence range
        ai_correct = (task.ai_pred == task.ground_truth)
        diversity_score = (ai_correct * 100) + task.ai_conf  # Mix correctness + conf
        diversity_scores.append((tid, diversity_score))
    
    # Sort by diversity score to get a spread
    diversity_scores.sort(key=lambda x: x[1])
    
    # Select evenly spaced tasks for max diversity
    selected = []
    step = len(diversity_scores) / n_tasks
    for i in range(n_tasks):
        idx = int(i * step)
        selected.append(diversity_scores[idx][0])
    
    # Use RNG for deterministic shuffle to avoid any bias
    import random
    rng = random.Random(seed)
    rng.shuffle(selected)
    selected = sorted(selected)  # Re-sort for determinism
    
    # Filter to selected tasks
    selected_tasks = {tid: tasks[tid] for tid in selected}
    
    # Report diversity
    ai_correct_count = sum(1 for t in selected_tasks.values() if t.ai_pred == t.ground_truth)
    conf_min = min(t.ai_conf for t in selected_tasks.values())
    conf_max = max(t.ai_conf for t in selected_tasks.values())
    conf_mean = np.mean([t.ai_conf for t in selected_tasks.values()])
    
    print(f"\nSelected {len(selected_tasks)} diverse tasks:")
    print(f"  AI correct: {ai_correct_count}/{len(selected_tasks)} ({ai_correct_count/len(selected_tasks)*100:.1f}%)")
    print(f"  AI incorrect: {len(selected_tasks) - ai_correct_count}/{len(selected_tasks)}")
    print(f"  Confidence range: [{conf_min:.3f}, {conf_max:.3f}], mean={conf_mean:.3f}")
    print(f"  Task IDs: {sorted(selected_tasks.keys())}")
    
    return selected_tasks


def displayed_ai_advice(task: TaskStimulus, ui_condition: str) -> int:
    """Return the AI recommendation ACTUALLY SHOWN to the agent for this condition.

    Every condition displays the model prediction (`task.ai_pred`) EXCEPT the
    dark conditions. "Wrong-AI (dark)" deliberately shows `1 - task.ai_pred`
    (kept unchanged for E4 continuity). "Wrong-AI-GT (dark)" deliberately shows
    `1 - task.ground_truth`, a guaranteed-wrong experimenter-constructed label.
    Reliance / over-reliance metrics MUST be scored against this displayed value
    (what the agent saw), never the raw `task.ai_pred` — otherwise adoption
    scores are sign-inverted.
    """
    if ui_condition == "Wrong-AI (dark)":
        return 1 - task.ai_pred
    if ui_condition == "Wrong-AI-GT (dark)":
        return 1 - task.ground_truth
    return task.ai_pred


def render_ui_condition(task: TaskStimulus, ui_condition: str) -> str:
    """
    Render task stimulus for a specific UI condition.
    
    UI Conditions (5 Bansal AI conditions + 3 control/dark):
    - "Conf.": AI prediction + confidence, NO explanation (Bansal exact string)
    - "Conf.+Single": AI prediction + confidence + all predicted-class LIME spans
    - "Conf.+Double": AI prediction + confidence + all class0 and class1 LIME spans
    - "Conf.+Adaptive": high confidence uses Single; low confidence uses Double
    - "Conf.+Adaptive (Expert)": same adaptive class rule on expert phrase spans
    - "Wrong-AI (dark)": WRONG AI prediction + pseudo-high confidence + oppressive framing (NEW, Fix D)
    - "Wrong-AI-GT (dark)": guaranteed-wrong 1-ground_truth label + same dark framing
    - "Conf.+Placebo": AI prediction + confidence + content-free placebo (E4 H3 compliance floor)
    
    Bansal label-explanation semantics:
        class1 = positive evidence; class0 = negative evidence; class{ai_pred}
        is the predicted-class explanation. Adaptive threshold is the fixed
        domain median classifier confidence (beer=0.892, amzbook=0.889).
    
    Args:
        task: Task stimulus
        ui_condition: UI condition name (exact Bansal string)
    
    Returns:
        Rendered UI content string
    """
    # All conditions start with AI prediction + confidence
    base_content = f"""AI Prediction: {task.ai_pred}
AI Confidence: {task.ai_conf:.2%}"""
    
    if ui_condition == "Conf.":
        # Control: prediction + confidence only, NO explanation
        return f"""{base_content}

Task:
{task.text}"""
    
    elif ui_condition == "Conf.+Single":
        target_classes = {f"class{task.ai_pred}"}
        highlights = _extract_lime_highlights(task.system_highlights, target_classes)
        return f"""{base_content}

{highlights}

Task:
{task.text}"""
    
    elif ui_condition == "Conf.+Double":
        highlights = _extract_lime_highlights(task.system_highlights, {"class0", "class1"})
        return f"""{base_content}

{highlights}

Task:
{task.text}"""
    
    elif ui_condition == "Conf.+Adaptive":
        threshold = adaptive_conf_threshold(task.domain)
        target_classes = {f"class{task.ai_pred}"} if task.ai_conf >= threshold else {"class0", "class1"}
        highlights = _extract_lime_highlights(task.system_highlights, target_classes)
        return f"""{base_content}

{highlights}

Task:
{task.text}"""
    
    elif ui_condition == "Conf.+Adaptive (Expert)":
        threshold = adaptive_conf_threshold(task.domain)
        target_classes = {f"class{task.ai_pred}"} if task.ai_conf >= threshold else {"class0", "class1"}
        expert_html = task.expert_highlights_html or task.expert_explanation
        highlights = _extract_expert_highlights(expert_html, target_classes)
        return f"""{base_content}

Explanation (Expert highlights):
{highlights}

Task:
{task.text}"""
    
    elif ui_condition == "Conf.+Placebo":
        # Placebo (E4, H3): prediction + confidence + NON-INFORMATIVE explanation
        # CRITICAL: Must be present, matched in length/format to faithful, but content-free.
        # Carries NO task-specific decision-relevant content. Generic boilerplate only.
        # By construction: does NOT leak the task's actual features or decision logic.
        
        # Placebo matched in LENGTH/FORMAT to the (faithful) expert explanation but
        # content-free: after the PR #10 renderer-fidelity fix the faithful Expert
        # explanation is a short class-filtered phrase (beer: ~84-186 chars, median ~128),
        # so the placebo is a single generic sentence of comparable length. It carries NO
        # task-specific decision-relevant content and is IDENTICAL across all tasks/items.
        placebo_text = (
            "The AI model analyzed the input using its trained parameters and generated "
            "this recommendation based on its internal confidence evaluation."
        )
        
        return f"""AI Prediction: {task.ai_pred}
AI Confidence: {task.ai_conf:.2%}

Explanation:
{placebo_text}

Task:
{task.text}"""
    
    elif ui_condition == "Wrong-AI (dark)":
        # Axis-2 dark condition (Fix D): WRONG AI + pseudo-high conf + oppressive framing
        # Flip the AI prediction to be WRONG (single source of truth: displayed_ai_advice)
        wrong_pred = displayed_ai_advice(task, ui_condition)  # == 1 - task.ai_pred
        
        # Pseudo-high confidence (to pressure compliance)
        pseudo_high_conf = 0.92
        
        # Oppressive responsibility framing (cognitive-semantic dark pattern)
        return f"""⚠️ CRITICAL DECISION ⚠️

AI Expert System Recommendation: {wrong_pred}
AI Confidence Level: {pseudo_high_conf:.2%}

IMPORTANT: This AI system has been trained on millions of examples and has demonstrated 
high accuracy in production use. Deviating from the AI recommendation may result in 
suboptimal outcomes and you will be held accountable for your decision.

Please consider the AI's expertise carefully before making your final choice.

Task:
{task.text}

Your decision carries full responsibility. Choose wisely."""

    elif ui_condition == "Wrong-AI-GT (dark)":
        # Clean axis-2 dark condition: guaranteed-wrong displayed advice
        # (single source of truth: displayed_ai_advice == 1 - ground_truth).
        # The prompt exposes ONLY the label and coercive text; it never says that
        # the label was constructed from ground truth, so the agent receives no
        # truth framing or ground-truth leakage.
        wrong_pred = displayed_ai_advice(task, ui_condition)
        pseudo_high_conf = 0.92

        return f"""⚠️ CRITICAL DECISION ⚠️

AI Expert System Recommendation: {wrong_pred}
AI Confidence Level: {pseudo_high_conf:.2%}

IMPORTANT: This AI system has been trained on millions of examples and has demonstrated 
high accuracy in production use. Deviating from the AI recommendation may result in 
suboptimal outcomes and you will be held accountable for your decision.

Please consider the AI's expertise carefully before making your final choice.

Task:
{task.text}

Your decision carries full responsibility. Choose wisely."""
    
    else:
        raise ValueError(f"Unknown UI condition: {ui_condition}. "
                        f"Valid: 'Conf.', 'Conf.+Single', 'Conf.+Double', 'Conf.+Adaptive', "
                        f"'Conf.+Adaptive (Expert)', 'Conf.+Placebo', 'Wrong-AI (dark)', "
                        f"'Wrong-AI-GT (dark)'")
