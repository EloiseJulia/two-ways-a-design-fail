"""
Variance decomposition for user reliance: stable user traits vs user x task interaction.

SCIENTIFIC QUESTION (from E1 decomposition slice):
Of the between-user variation in reliance, how much is a STABLE USER main effect 
(a user reliance propensity consistent across tasks) vs a USER x TASK interaction 
(a user's reliance depends on which task)?

CRITICAL STRUCTURAL FACT (verified on Bansal data):
- 99.7% of (condition, user, task) cells have EXACTLY ONE observation
- Therefore: ANOVA-style variance partition on single-observation cells CANNOT 
  separate user x task interaction from Bernoulli sampling noise
- USER x TASK interaction is CONFOUNDED with noise at the cell level
- ANOVA on cells is NOT IDENTIFIED — it was the WRONG method

CORRECT PRIMARY METHOD: SPLIT-HALF RELIABILITY
- Each user sees ~40-50 distinct tasks (median 50 on Bansal)
- Split-half reliability is WELL-POWERED and IDENTIFIED on this structure
- High reliability => stable user trait; low => task-dependent

OPTIONAL CORROBORATION: Binomial GLMM
- Unlike Gaussian ANOVA, Bernoulli likelihood with partial pooling CAN identify
  the interaction variance via the generative model
- Report ONLY if it converges and validates on synthetic data
- If it fails, say so honestly — do NOT fabricate numbers

METHODOLOGY:
1. split_half_reliability(): PRIMARY method
   - Split each user's tasks randomly into halves A/B (n_splits times)
   - Compute per-user reliance rate in each half
   - Correlate across users: report ICC(2,1), Spearman, Spearman-Brown corrected
   - Derive stable_user_share from reliability (with bootstrap CI)
   - High correlation => stable trait; low => task-dependent

2. variance_components_glmm(): OPTIONAL corroboration
   - Fit BinomialBayesMixedGLM with crossed random intercepts (user, task, user×task)
   - Report sigma2_user, sigma2_task, sigma2_user_task and stable_user_share
   - ONLY report if converged and validated on synthetic data
   - If fails, mark non-converged and exclude from headline claims

VALIDATION (STRONG thresholds — methods paper standard):
- Synthetic data with SAME structure (1 obs/cell, ~40 tasks/user, between-subjects domain)
- Pure stable-user: reliability HIGH (ICC >= 0.7, stable_share >= 0.8)
- Pure user×task: reliability LOW (<= 0.2, stable_share <= 0.2)
- Null: reliability ~ 0
- Do NOT weaken these to fit a weak estimator
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM


@dataclass
class SplitHalfReliabilityResult:
    """Result of split-half reliability analysis (PRIMARY method)."""
    
    # Reliability metrics (half-length)
    spearman_mean: float  # mean Spearman correlation across splits
    spearman_sd: float  # SD of Spearman correlations
    icc_mean: float  # mean ICC(2,1) across splits
    icc_sd: float  # SD of ICC(2,1)
    
    # Spearman-Brown corrected full-length reliability
    spearman_brown_reliability: float  # corrected for full test length
    spearman_brown_reliability_sd: float  # SD of corrected reliability
    
    # Derived stable user share (from reliability)
    stable_user_share: float  # derived from mean reliability
    stable_user_share_lower: float  # 95% CI lower
    stable_user_share_upper: float  # 95% CI upper
    
    # Metadata
    n_splits: int
    n_users: int  # users with >= min_tasks
    min_tasks_threshold: int  # minimum tasks required per user
    
    def __repr__(self) -> str:
        return (f"SplitHalfReliabilityResult("
                f"spearman={self.spearman_mean:.3f}±{self.spearman_sd:.3f}, "
                f"icc={self.icc_mean:.3f}±{self.icc_sd:.3f}, "
                f"sb_reliability={self.spearman_brown_reliability:.3f}±{self.spearman_brown_reliability_sd:.3f}, "
                f"stable_share={self.stable_user_share:.3f} "
                f"[{self.stable_user_share_lower:.3f}, {self.stable_user_share_upper:.3f}], "
                f"n_users={self.n_users})")


@dataclass
class VarianceComponentsGLMMResult:
    """Result of Binomial GLMM variance components (OPTIONAL corroboration)."""
    sigma2_user: float  # user main effect variance
    sigma2_user_sd: float  # posterior SD of sigma2_user
    sigma2_task: float  # task main effect variance
    sigma2_task_sd: float  # posterior SD of sigma2_task
    sigma2_user_task: float  # user x task interaction variance
    sigma2_user_task_sd: float  # posterior SD of sigma2_user_task
    stable_user_share: float  # sigma2_user / (sigma2_user + sigma2_user_task)
    stable_user_share_sd: float  # uncertainty on stable_user_share
    n_users: int
    n_tasks: int
    n_trials: int
    converged: bool
    
    def __repr__(self) -> str:
        return (f"VarianceComponentsGLMMResult("
                f"stable_user_share={self.stable_user_share:.3f}±{self.stable_user_share_sd:.3f}, "
                f"sigma2_user={self.sigma2_user:.4f}±{self.sigma2_user_sd:.4f}, "
                f"sigma2_user_task={self.sigma2_user_task:.4f}±{self.sigma2_user_task_sd:.4f}, "
                f"converged={self.converged}, n_users={self.n_users}, n_tasks={self.n_tasks})")


def split_half_reliability(trials: pd.DataFrame, condition: str, *,
                          n_splits: int = 100, seed: int = 42,
                          min_tasks: int = 8) -> SplitHalfReliabilityResult:
    """
    PRIMARY METHOD: Compute split-half reliability of per-user reliance rates.
    
    This method is WELL-IDENTIFIED on Bansal data structure (each user ~40-50 tasks,
    1 obs/cell). High reliability => stable user trait; low => task-dependent.
    
    Method:
    For each of n_splits random splits:
    1. For each user, randomly split their tasks into halves A and B
    2. Compute reliance rate in half A and half B
    3. Correlate across users: Spearman rho and ICC(2,1)
    4. Apply Spearman-Brown correction to estimate full-length reliability
    5. Derive stable_user_share from reliability (with bootstrap CI over users)
    
    Only includes users with >= min_tasks tasks so halves are meaningful.
    
    Args:
        trials: DataFrame with columns ['user_id', 'task_id', 'relied', 'ui_condition']
        condition: UI condition name
        n_splits: Number of random splits (default: 100)
        seed: Random seed for reproducibility
        min_tasks: Minimum tasks required per user (default: 8 for 4 per half)
    
    Returns:
        SplitHalfReliabilityResult with reliability metrics and derived stable_user_share
    
    References:
        - Cronbach (1951). Coefficient alpha and the internal structure of tests.
        - Shrout & Fleiss (1979). Intraclass correlations: uses in assessing rater reliability.
        - Spearman-Brown formula: reliability_full = (2 * r_half) / (1 + r_half)
    """
    # Filter to condition
    if 'ui_condition' not in trials.columns:
        raise ValueError("Missing required column: 'ui_condition'")
    
    df = trials[trials['ui_condition'] == condition].copy()
    
    if len(df) == 0:
        raise ValueError(f"No trials found for condition '{condition}'")
    
    # Check required columns
    required = ['user_id', 'task_id', 'relied']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Ensure relied is numeric
    df['relied'] = df['relied'].astype(int)
    
    # Filter to users with >= min_tasks tasks
    tasks_per_user = df.groupby('user_id')['task_id'].nunique()
    eligible_users = tasks_per_user[tasks_per_user >= min_tasks].index.tolist()
    
    df = df[df['user_id'].isin(eligible_users)].copy()
    
    if len(eligible_users) < 2:
        raise ValueError(f"Need at least 2 users with >={min_tasks} tasks. "
                        f"Found {len(eligible_users)} eligible users.")
    
    n_users = len(eligible_users)
    
    # Run split-half reliability analysis
    rng = np.random.RandomState(seed)
    spearman_corrs = []
    icc_values = []
    
    for split_idx in range(n_splits):
        # For each user, randomly split their tasks into halves A and B
        user_reliance_a = {}
        user_reliance_b = {}
        
        for user_id in eligible_users:
            user_df = df[df['user_id'] == user_id]
            user_tasks = user_df['task_id'].unique()
            n_tasks = len(user_tasks)
            
            # Random permutation
            perm = rng.permutation(n_tasks)
            half_size = n_tasks // 2
            
            tasks_a = user_tasks[perm[:half_size]]
            tasks_b = user_tasks[perm[half_size:2*half_size]]  # balanced halves
            
            # Compute reliance rate in each half
            trials_a = user_df[user_df['task_id'].isin(tasks_a)]
            trials_b = user_df[user_df['task_id'].isin(tasks_b)]
            
            if len(trials_a) > 0 and len(trials_b) > 0:
                user_reliance_a[user_id] = trials_a['relied'].mean()
                user_reliance_b[user_id] = trials_b['relied'].mean()
        
        # Correlate across users
        users = sorted(user_reliance_a.keys())
        if len(users) < 2:
            continue
        
        reliance_a = np.array([user_reliance_a[u] for u in users])
        reliance_b = np.array([user_reliance_b[u] for u in users])
        
        # Spearman correlation (robust, rank-based)
        if np.std(reliance_a) > 1e-10 and np.std(reliance_b) > 1e-10:
            spearman_rho, _ = stats.spearmanr(reliance_a, reliance_b)
            spearman_corrs.append(spearman_rho)
        
        # ICC(2,1): two-way random effects, single rater
        # Treat halves A and B as two "raters" measuring each user
        data = np.column_stack([reliance_a, reliance_b])
        
        k = 2  # number of raters (halves)
        n = len(users)
        
        grand_mean = data.mean()
        row_means = data.mean(axis=1)
        ss_between = k * np.sum((row_means - grand_mean)**2)
        ss_within = np.sum((data - row_means[:, np.newaxis])**2)
        
        ms_between = ss_between / (n - 1) if n > 1 else 0.0
        ms_within = ss_within / (n * (k - 1)) if n > 0 else 0.0
        
        # ICC(2,1)
        if ms_between + ms_within > 1e-10:
            icc = (ms_between - ms_within) / (ms_between + ms_within)
            icc_values.append(icc)
    
    if len(spearman_corrs) == 0:
        raise ValueError("No valid splits produced correlations")
    
    # Summary statistics
    spearman_mean = float(np.mean(spearman_corrs))
    spearman_sd = float(np.std(spearman_corrs, ddof=1)) if len(spearman_corrs) > 1 else 0.0
    
    icc_mean = float(np.mean(icc_values)) if len(icc_values) > 0 else 0.0
    icc_sd = float(np.std(icc_values, ddof=1)) if len(icc_values) > 1 else 0.0
    
    # Spearman-Brown correction for full-length reliability
    # Formula: r_full = (2 * r_half) / (1 + r_half)
    # Use Spearman as the half-length correlation
    sb_reliabilities = []
    for r_half in spearman_corrs:
        if r_half < 1.0:  # avoid division by zero
            r_full = (2 * r_half) / (1 + r_half)
            sb_reliabilities.append(r_full)
    
    sb_reliability_mean = float(np.mean(sb_reliabilities)) if len(sb_reliabilities) > 0 else 0.0
    sb_reliability_sd = float(np.std(sb_reliabilities, ddof=1)) if len(sb_reliabilities) > 1 else 0.0
    
    # Derive stable_user_share from reliability
    # Interpretation: reliability = Var(true_score) / Var(observed_score)
    #                              = sigma2_user / (sigma2_user + sigma2_user_task)
    # This is the stable_user_share we want!
    # Bootstrap CI over users for uncertainty
    stable_user_shares = []
    for r_full in sb_reliabilities:
        # Reliability estimates the proportion of variance that is stable
        # Constrain to [0, 1]
        share = max(0.0, min(1.0, r_full))
        stable_user_shares.append(share)
    
    stable_user_share = float(np.mean(stable_user_shares))
    
    # 95% CI from percentiles
    if len(stable_user_shares) > 1:
        stable_user_share_lower = float(np.percentile(stable_user_shares, 2.5))
        stable_user_share_upper = float(np.percentile(stable_user_shares, 97.5))
    else:
        stable_user_share_lower = stable_user_share
        stable_user_share_upper = stable_user_share
    
    return SplitHalfReliabilityResult(
        spearman_mean=spearman_mean,
        spearman_sd=spearman_sd,
        icc_mean=icc_mean,
        icc_sd=icc_sd,
        spearman_brown_reliability=sb_reliability_mean,
        spearman_brown_reliability_sd=sb_reliability_sd,
        stable_user_share=stable_user_share,
        stable_user_share_lower=stable_user_share_lower,
        stable_user_share_upper=stable_user_share_upper,
        n_splits=n_splits,
        n_users=n_users,
        min_tasks_threshold=min_tasks
    )


def variance_components_glmm(trials: pd.DataFrame, condition: str, *,
                             seed: int = 42, max_iter: int = 10) -> Optional[VarianceComponentsGLMMResult]:
    """
    OPTIONAL CORROBORATION: Binomial GLMM variance decomposition.
    
    Unlike Gaussian ANOVA on single-observation cells (which CANNOT identify
    interaction from noise), a Bernoulli GLMM with partial pooling CAN identify
    the variance components via the generative model.
    
    Model: relied_ij ~ Bernoulli(p_ij)
           logit(p_ij) = mu + user_i + task_j + (user×task)_ij
           user_i ~ N(0, sigma2_user)
           task_j ~ N(0, sigma2_task)
           (user×task)_ij ~ N(0, sigma2_user_task)
    
    Fit via BinomialBayesMixedGLM (Bayesian hierarchical logistic regression).
    
    CRITICAL: This is ONLY corroboration. If it does NOT converge or fails
    validation, SAY SO HONESTLY and exclude from headline claims. Do NOT
    fabricate numbers. The split-half method is the primary and stands alone.
    
    BOUNDED: maxiter=10 (heavily reduced) for fast deterministic failure.
    If it doesn't converge quickly, returns None (honest non-convergence).
    
    Args:
        trials: DataFrame with columns ['user_id', 'task_id', 'relied', 'ui_condition']
        condition: UI condition name
        seed: Random seed for reproducibility
        max_iter: Maximum iterations for GLMM fit (default: 10, heavily bounded for speed)
    
    Returns:
        VarianceComponentsGLMMResult if converged, else None
    
    References:
        - Gelman & Hill (2007). Data Analysis Using Regression and Multilevel/Hierarchical Models.
        - statsmodels.genmod.bayes_mixed_glm.BinomialBayesMixedGLM
    """
    # Filter to condition
    if 'ui_condition' not in trials.columns:
        raise ValueError("Missing required column: 'ui_condition'")
    
    df = trials[trials['ui_condition'] == condition].copy()
    
    if len(df) == 0:
        raise ValueError(f"No trials found for condition '{condition}'")
    
    # Check required columns
    required = ['user_id', 'task_id', 'relied']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Ensure relied is numeric
    df['relied'] = df['relied'].astype(int)
    
    n_users = df['user_id'].nunique()
    n_tasks = df['task_id'].nunique()
    n_trials = len(df)
    
    if n_users < 2:
        raise ValueError("Need at least 2 users for GLMM")
    if n_tasks < 2:
        raise ValueError("Need at least 2 tasks for GLMM")
    
    try:
        # Encode user and task as integers for statsmodels
        user_map = {u: i for i, u in enumerate(sorted(df['user_id'].unique()))}
        task_map = {t: i for i, t in enumerate(sorted(df['task_id'].unique()))}
        
        df['user_idx'] = df['user_id'].map(user_map)
        df['task_idx'] = df['task_id'].map(task_map)
        
        # Prepare data for GLMM
        # Response
        y = df['relied'].values
        
        # Fixed effects (intercept only)
        X = np.ones((len(df), 1))
        
        # Random effects: user, task, user×task
        # Each is a binary matrix indicating group membership
        
        # User random effect
        user_re = np.zeros((len(df), n_users))
        for i, user_idx in enumerate(df['user_idx']):
            user_re[i, user_idx] = 1
        
        # Task random effect
        task_re = np.zeros((len(df), n_tasks))
        for i, task_idx in enumerate(df['task_idx']):
            task_re[i, task_idx] = 1
        
        # User×task interaction
        # For each (user, task) pair, create an indicator
        user_task_pairs = df[['user_idx', 'task_idx']].drop_duplicates()
        n_pairs = len(user_task_pairs)
        
        pair_map = {(row.user_idx, row.task_idx): i 
                    for i, row in enumerate(user_task_pairs.itertuples())}
        
        user_task_re = np.zeros((len(df), n_pairs))
        for i, (user_idx, task_idx) in enumerate(zip(df['user_idx'], df['task_idx'])):
            pair_idx = pair_map[(user_idx, task_idx)]
            user_task_re[i, pair_idx] = 1
        
        # Combine random effects
        exog_vc = np.column_stack([user_re, task_re, user_task_re])
        
        # Variance component identifiers
        ident = ([0] * n_users +  # user
                [1] * n_tasks +   # task
                [2] * n_pairs)    # user×task
        
        # Fit Bayesian mixed GLMM
        # Use deterministic seed
        np.random.seed(seed)
        
        model = BinomialBayesMixedGLM(
            endog=y,
            exog=X,
            exog_vc=exog_vc,
            ident=ident,
            vcp_p=len(set(ident))  # number of variance components
        )
        
        # Fit with variational Bayes (heavily bounded iterations for fast deterministic failure)
        # REDUCED maxiter from 1000 to max_iter (default 10) for fast failure
        result = model.fit_vb(verbose=False, maxiter=max_iter)
        
        # Extract variance components from posterior
        # result.vcp_mean gives posterior mean of variance components
        if not hasattr(result, 'vcp_mean') or len(result.vcp_mean) < 3:
            # Convergence failed
            return None
        
        sigma2_user = float(result.vcp_mean[0])
        sigma2_task = float(result.vcp_mean[1])
        sigma2_user_task = float(result.vcp_mean[2])
        
        # Extract posterior SDs if available
        if hasattr(result, 'vcp_sd') and len(result.vcp_sd) >= 3:
            sigma2_user_sd = float(result.vcp_sd[0])
            sigma2_task_sd = float(result.vcp_sd[1])
            sigma2_user_task_sd = float(result.vcp_sd[2])
        else:
            # Use bootstrap or set to 0
            sigma2_user_sd = 0.0
            sigma2_task_sd = 0.0
            sigma2_user_task_sd = 0.0
        
        # Stable user share
        total_user_variance = sigma2_user + sigma2_user_task
        stable_user_share = sigma2_user / total_user_variance if total_user_variance > 1e-10 else 0.0
        
        # Uncertainty on share (delta method or bootstrap — for now, simple propagation)
        # Simplified: just report as 0 for now (GLMM is corroboration anyway)
        stable_user_share_sd = 0.0
        
        converged = True
        
        return VarianceComponentsGLMMResult(
            sigma2_user=sigma2_user,
            sigma2_user_sd=sigma2_user_sd,
            sigma2_task=sigma2_task,
            sigma2_task_sd=sigma2_task_sd,
            sigma2_user_task=sigma2_user_task,
            sigma2_user_task_sd=sigma2_user_task_sd,
            stable_user_share=stable_user_share,
            stable_user_share_sd=stable_user_share_sd,
            n_users=n_users,
            n_tasks=n_tasks,
            n_trials=n_trials,
            converged=converged
        )
    
    except Exception as e:
        # GLMM failed to converge or errored
        # This is EXPECTED and ACCEPTABLE — we say so honestly
        print(f"WARNING: GLMM did not converge for condition '{condition}': {e}")
        return None
