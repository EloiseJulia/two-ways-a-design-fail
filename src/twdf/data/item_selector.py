"""
Data-driven hard/ambiguous item selection (Fix B).

SCIENTIFIC RATIONALE:
PR #3's compliance-collapse (97% no-movement, 3% conflict) was partly because
items were too easy (agent never uncertain). Fix B selects items that concentrate
CONFLICT/ambiguity by these DATA-DRIVEN criteria:

1. Items where AI is WRONG (pred != Y) and/or LOW confidence
2. Items where HUMAN reliance actually VARIES across users (high variance)

This calibrates WHERE we look to the loci of real human heterogeneity.

LEAKAGE GUARD:
- Using human reliance to SELECT items is allowed and MUST be disclosed
- Panel agents MUST NOT see human outcomes/reliance in any prompt
- Human reliance MUST NOT be fed as a predictor
- Item selection ≠ label leakage

Determinism: Sort + fixed seed for reproducible selection.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json

import numpy as np
import pandas as pd

from twdf.data.bansal_tasks import TaskStimulus, load_domain_tasks
from twdf.data.bansal import load_bansal


@dataclass
class ItemSelectionCriteria:
    """Criteria for data-driven item selection."""
    n_items: int  # Target number of items to select
    prefer_ai_wrong: float = 0.5  # Weight for AI-incorrect items (0-1)
    prefer_low_conf: float = 0.3  # Weight for low-confidence items (0-1)
    prefer_high_variance: float = 0.2  # Weight for high human variance items (0-1)
    seed: int = 42  # Random seed for deterministic selection
    
    def __post_init__(self):
        total = self.prefer_ai_wrong + self.prefer_low_conf + self.prefer_high_variance
        if not np.isclose(total, 1.0):
            raise ValueError(f"Selection weights must sum to 1.0, got {total}")


def compute_human_reliance_variance(
    task_stimuli: dict[str, TaskStimulus],
    data_dir: Optional[Path] = None,
    domain: str = "beer"
) -> dict[str, float]:
    """
    Compute per-item human reliance variance from Bansal data.
    
    Higher variance = humans disagree more on whether to rely on AI for this item.
    We SELECT items with high variance (loci of heterogeneity), but we do NOT
    leak human outcomes to the panel agents.
    
    Args:
        task_stimuli: Dict of task_id -> TaskStimulus
        data_dir: Directory for Bansal CSV (default: data/raw/)
        domain: Task domain to select from (default: beer)
    
    Returns:
        Dict mapping task_id -> reliance variance across humans
    """
    # Load Bansal human data
    df = load_bansal(
        data_dir=data_dir,
        task_sample=None,  # Load all tasks
        ui_conditions=None,  # All conditions
        task_selection='all'
    )
    
    # Filter to requested domain
    df_domain = df[df['extra'].apply(lambda x: x.get('task') == domain)].copy()
    
    # Compute per-item reliance variance
    variance_by_task = {}
    
    for task_id in task_stimuli.keys():
        # Get all human trials for this task (across all conditions)
        task_trials = df_domain[df_domain['task_id'] == task_id]
        
        if len(task_trials) == 0:
            variance_by_task[task_id] = 0.0
            continue
        
        # Reliance rate per user (if user saw this task multiple times)
        user_reliance = task_trials.groupby('user_id')['relied'].mean()
        
        # Variance across users
        if len(user_reliance) > 1:
            variance = float(user_reliance.var(ddof=1))
        else:
            variance = 0.0
        
        variance_by_task[task_id] = variance
    
    return variance_by_task


def select_hard_items(
    criteria: ItemSelectionCriteria | None = None,
    data_dir: Optional[Path] = None,
    *,
    domain: str = "beer",
    seed: int | None = None,
    n_items: int | None = None,
) -> dict[str, TaskStimulus]:
    """
    Select hard/ambiguous items using data-driven criteria (Fix B).

    DETERMINISTIC SELECTION (sorted + fixed seed):
    1. Load all tasks for the requested Bansal domain
    2. Compute human reliance variance per item (from CSV)
    3. Score items by weighted criteria:
       - AI-wrong items (pred != Y): higher score
       - Low AI confidence: higher score
       - High human reliance variance: higher score
    4. Sort by composite score (descending), select top n_items
    5. Deterministic shuffle with seed, then re-sort for final determinism
    """
    if criteria is None:
        criteria = ItemSelectionCriteria(n_items=n_items or 20, seed=seed if seed is not None else 42)
    elif seed is not None or n_items is not None:
        criteria = ItemSelectionCriteria(
            n_items=n_items if n_items is not None else criteria.n_items,
            prefer_ai_wrong=criteria.prefer_ai_wrong,
            prefer_low_conf=criteria.prefer_low_conf,
            prefer_high_variance=criteria.prefer_high_variance,
            seed=seed if seed is not None else criteria.seed,
        )

    domain = domain.lower()

    if data_dir is None:
        data_dir = Path("data/raw")

    print(f"=== FIX B: Data-driven hard/ambiguous item selection ({domain}) ===")
    print(f"Target: {criteria.n_items} items")
    print(f"Weights: AI-wrong={criteria.prefer_ai_wrong:.1%}, "
          f"low-conf={criteria.prefer_low_conf:.1%}, "
          f"high-variance={criteria.prefer_high_variance:.1%}")
    print(f"Seed: {criteria.seed}")
    print()

    all_tasks = load_domain_tasks(
        domain,
        data_dir=data_dir,
        seed=criteria.seed,
        n_tasks=1000  # Load all available
    )

    print(f"Total {domain} tasks available: {len(all_tasks)}")

    print("Computing human reliance variance per item...")
    variance_by_task = compute_human_reliance_variance(all_tasks, data_dir=data_dir, domain=domain)

    item_scores = []

    max_variance = max(variance_by_task.values()) if variance_by_task else 1.0
    for task_id, task in all_tasks.items():
        ai_wrong = 1.0 if task.ai_pred != task.ground_truth else 0.0
        low_conf = 1.0 - task.ai_conf
        high_variance = variance_by_task.get(task_id, 0.0) / max_variance if max_variance > 0 else 0.0

        score = (
            criteria.prefer_ai_wrong * ai_wrong +
            criteria.prefer_low_conf * low_conf +
            criteria.prefer_high_variance * high_variance
        )

        item_scores.append((task_id, task, score, ai_wrong, low_conf, high_variance))

    item_scores.sort(key=lambda x: (-x[2], x[0]))
    selected = item_scores[:criteria.n_items]

    rng = np.random.RandomState(criteria.seed)
    selected_ids = [item[0] for item in selected]
    rng.shuffle(selected_ids)
    selected_ids = sorted(selected_ids)

    selected_tasks = {task_id: all_tasks[task_id] for task_id in selected_ids}

    ai_wrong_count = sum(1 for tid in selected_ids if all_tasks[tid].ai_pred != all_tasks[tid].ground_truth)
    ai_correct_count = len(selected_ids) - ai_wrong_count

    conf_values = [all_tasks[tid].ai_conf for tid in selected_ids]
    low_conf_count = sum(1 for c in conf_values if c < 0.7)
    high_conf_count = len(conf_values) - low_conf_count

    variance_values = [variance_by_task.get(tid, 0.0) for tid in selected_ids]
    high_var_count = sum(1 for v in variance_values if v > np.median(variance_values))

    print(f"\n=== SELECTED {len(selected_tasks)} HARD ITEMS ===")
    print(f"AI correctness:")
    print(f"  - AI WRONG: {ai_wrong_count}/{len(selected_ids)} ({ai_wrong_count/len(selected_ids)*100:.1f}%)")
    print(f"  - AI correct: {ai_correct_count}/{len(selected_ids)} ({ai_correct_count/len(selected_ids)*100:.1f}%)")
    print()
    print(f"AI confidence distribution:")
    print(f"  - Low conf (<0.7): {low_conf_count}/{len(selected_ids)} ({low_conf_count/len(selected_ids)*100:.1f}%)")
    print(f"  - High conf (≥0.7): {high_conf_count}/{len(selected_ids)} ({high_conf_count/len(selected_ids)*100:.1f}%)")
    print(f"  - Min: {min(conf_values):.3f}, Max: {max(conf_values):.3f}, Mean: {np.mean(conf_values):.3f}")
    print()
    print(f"Human reliance variance (selection criterion only, NOT leaked to agents):")
    print(f"  - High variance (above median): {high_var_count}/{len(selected_ids)}")
    print(f"  - Median variance: {np.median(variance_values):.4f}")
    print(f"  - Mean variance: {np.mean(variance_values):.4f}")
    print()
    print(f"Selected task IDs: {selected_ids}")
    print()
    print("DISCLOSURE: Human reliance variance was used to SELECT items (concentrating")
    print("on loci of heterogeneity), but human outcomes/reliance are NOT leaked to")
    print("panel agents in prompts or as predictors. Item selection ≠ label leakage.")
    print()

    return selected_tasks


__all__ = ['ItemSelectionCriteria', 'select_hard_items', 'compute_human_reliance_variance']
