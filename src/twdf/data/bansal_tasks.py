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
    expert_explanation: str  # Expert-highlighted explanation HTML
    system: str  # AI system name
    
    # Original fields for reference
    testid: str  # Original test ID from task JSON


# Task stimulus URLs (verified 2026-07-15)
TASK_URLS = {
    'beer': 'https://raw.githubusercontent.com/uw-hai/Complementary-Performance/main/task-examples/task-sentiment-beer.json',
    'amzbook': 'https://raw.githubusercontent.com/uw-hai/Complementary-Performance/main/task-examples/task-sentiment-amzbook.json',
    'lsat': 'https://raw.githubusercontent.com/uw-hai/Complementary-Performance/main/task-examples/task-lsat.json',
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
            system=item['system'],
            testid=testid,
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


def render_ui_condition(task: TaskStimulus, ui_condition: str) -> str:
    """
    Render task stimulus for a specific UI condition.
    
    UI Conditions (Bansal exact strings):
    - "Conf.": AI prediction + confidence, NO explanation
    - "Conf.+Adaptive (Expert)": AI prediction + confidence + expert explanation
    
    Args:
        task: Task stimulus
        ui_condition: UI condition name
    
    Returns:
        Rendered UI content string
    """
    if ui_condition == "Conf.":
        # Control: prediction + confidence only
        return f"""AI Prediction: {task.ai_pred}
AI Confidence: {task.ai_conf:.2%}

Task:
{task.text}"""
    
    elif ui_condition == "Conf.+Adaptive (Expert)":
        # Treatment: prediction + confidence + expert explanation
        return f"""AI Prediction: {task.ai_pred}
AI Confidence: {task.ai_conf:.2%}

Explanation (Expert highlights):
{task.expert_explanation}

Task:
{task.text}"""
    
    else:
        raise ValueError(f"Unknown UI condition: {ui_condition}. "
                        f"Valid: 'Conf.', 'Conf.+Adaptive (Expert)'")
