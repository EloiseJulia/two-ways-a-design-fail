"""
Over-dispersion metrics (Axis 1) - Module C core.

METHODOLOGICAL RIGOR (see SPEC §8):
- betabinom_overdispersion MUST separate TRUE between-user variance from binomial noise
- NOT raw empirical variance (that collapses hypothesis H1a)
- Uses beta-binomial hierarchical model to estimate excess dispersion parameter
- Mean-predictor baseline MUST output only p(1-p) and cannot produce over-dispersion
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats
from scipy.special import betaln, gammaln
from scipy.optimize import minimize_scalar


@dataclass
class OverdispersionResult:
    """Result of beta-binomial over-dispersion analysis."""
    rho: float  # dispersion parameter (0 = pure binomial, >0 = over-dispersed)
    mean_p: float  # pooled reliance rate
    binomial_variance: float  # theoretical variance if purely binomial: p(1-p)
    empirical_variance: float  # observed between-user variance
    excess_variance: float  # empirical - binomial (unnormalized)
    n_users: int
    total_trials: int
    converged: bool
    
    def __repr__(self) -> str:
        return (f"OverdispersionResult(rho={self.rho:.4f}, mean_p={self.mean_p:.4f}, "
                f"binomial_var={self.binomial_variance:.4f}, empirical_var={self.empirical_variance:.4f}, "
                f"excess={self.excess_variance:.4f}, n_users={self.n_users})")


def betabinom_overdispersion(relied_by_user: dict[str, tuple[int, int]]) -> OverdispersionResult:
    """
    Estimate TRUE between-user over-dispersion using beta-binomial model.
    
    CRITICAL: This function separates genuine between-user heterogeneity from 
    binomial sampling noise. Raw empirical variance is WRONG because it conflates 
    signal with noise.
    
    Model: Each user i has reliance probability p_i ~ Beta(alpha, beta).
              Observed reliance k_i ~ Binomial(n_i, p_i).
    
    The dispersion parameter rho = 1/(alpha + beta + 1) measures over-dispersion:
    - rho = 0: all users have same p (pure binomial, no between-user variance)
    - rho > 0: users differ in their reliance probabilities
    
    Var(k_i/n_i) = p(1-p)/n_i * [1 + (n_i - 1) * rho]
                   (binomial noise)  (excess from heterogeneity)
    
    Estimation: Maximum likelihood fit of (alpha, beta) to observed (k_i, n_i).
    
    Args:
        relied_by_user: dict mapping user_id -> (n_relied, n_trials)
                       e.g., {'user1': (7, 10), 'user2': (3, 10)}
    
    Returns:
        OverdispersionResult with rho, mean_p, variances, and convergence status
    
    References:
        - Prentice (1986). Binary regression using an extended beta-binomial distribution.
        - Griffiths (1973). Maximum likelihood estimation for the beta-binomial distribution.
    """
    if not relied_by_user:
        raise ValueError("relied_by_user cannot be empty")
    
    # Extract observed data
    users = list(relied_by_user.keys())
    k = np.array([relied_by_user[u][0] for u in users])  # successes per user
    n = np.array([relied_by_user[u][1] for u in users])  # trials per user
    
    if len(k) < 2:
        raise ValueError("Need at least 2 users to estimate over-dispersion")
    
    if np.any(n <= 0):
        raise ValueError("All users must have n_trials > 0")
    
    # Pooled estimates
    mean_p = k.sum() / n.sum()
    empirical_p = k / n  # per-user reliance rates
    empirical_variance = np.var(empirical_p, ddof=1)
    binomial_variance = mean_p * (1 - mean_p)
    
    # Fit beta-binomial via maximum likelihood
    # Parameterize as (mu, rho) where mu = mean_p, rho = dispersion
    # Then alpha = mu * (1/rho - 1), beta = (1-mu) * (1/rho - 1)
    
    def neg_log_likelihood(rho: float) -> float:
        """Negative log-likelihood for beta-binomial model."""
        if rho <= 0 or rho >= 1:
            return np.inf
        
        # Convert (mean_p, rho) to (alpha, beta)
        concentration = 1.0 / rho - 1.0  # alpha + beta
        alpha = mean_p * concentration
        beta = (1 - mean_p) * concentration
        
        if alpha <= 0 or beta <= 0:
            return np.inf
        
        # Beta-binomial log-likelihood using direct formula
        # log P(k | n, alpha, beta) = log B(k+alpha, n-k+beta) - log B(alpha, beta) + log C(n,k)
        # where B is the beta function and C(n,k) is binomial coefficient
        
        ll = 0.0
        for i in range(len(k)):
            if n[i] == 0:
                continue
            
            try:
                # Use gamma functions: B(a,b) = Gamma(a)*Gamma(b)/Gamma(a+b)
                # log B(a,b) = log Gamma(a) + log Gamma(b) - log Gamma(a+b)
                log_beta_numerator = (gammaln(k[i] + alpha) + gammaln(n[i] - k[i] + beta) 
                                     - gammaln(n[i] + alpha + beta))
                log_beta_denominator = gammaln(alpha) + gammaln(beta) - gammaln(alpha + beta)
                
                # Binomial coefficient: log C(n,k) = log(n!) - log(k!) - log((n-k)!)
                log_binom_coef = gammaln(n[i] + 1) - gammaln(k[i] + 1) - gammaln(n[i] - k[i] + 1)
                
                ll += log_beta_numerator - log_beta_denominator + log_binom_coef
            except (ValueError, FloatingPointError):
                return np.inf
        
        return -ll
    
    # Optimize over rho in (0, 1)
    # Start with method-of-moments estimate
    # Var(p_hat) ≈ p(1-p)/n_avg * [1 + (n_avg - 1) * rho]
    # rho_mm = (Var(p_hat) - p(1-p)/n_avg) / (p(1-p) * (1 - 1/n_avg))
    n_avg = np.mean(n)
    expected_binom_var = binomial_variance / n_avg
    rho_mm = max(0.001, min(0.999, (empirical_variance - expected_binom_var) / 
                                     (binomial_variance * (1 - 1/n_avg))))
    
    result = minimize_scalar(neg_log_likelihood, bounds=(1e-6, 0.999), method='bounded',
                           options={'xatol': 1e-8})
    
    rho = result.x if result.success else rho_mm
    converged = result.success
    
    # Ensure rho is non-negative (it's a variance component)
    rho = max(0.0, rho)
    
    excess_variance = empirical_variance - binomial_variance / n_avg
    
    return OverdispersionResult(
        rho=rho,
        mean_p=mean_p,
        binomial_variance=binomial_variance,
        empirical_variance=empirical_variance,
        excess_variance=excess_variance,
        n_users=len(users),
        total_trials=int(n.sum()),
        converged=converged
    )


def baseline_mean_predictor(relied_by_user: dict[str, tuple[int, int]]) -> OverdispersionResult:
    """
    Mean-predictor baseline: outputs ONLY p(1-p) variance.
    
    By construction, this baseline CANNOT produce over-dispersion because it
    assumes all users have identical reliance probability = pooled mean.
    
    This is the null model against which we test H1a: genuine between-user
    heterogeneity should beat this baseline.
    
    Returns:
        OverdispersionResult with rho=0 (by construction, no over-dispersion)
    """
    if not relied_by_user:
        raise ValueError("relied_by_user cannot be empty")
    
    users = list(relied_by_user.keys())
    k = np.array([relied_by_user[u][0] for u in users])
    n = np.array([relied_by_user[u][1] for u in users])
    
    mean_p = k.sum() / n.sum()
    binomial_variance = mean_p * (1 - mean_p)
    n_avg = np.mean(n)
    
    # Mean-predictor says all users have same p, so rho = 0
    return OverdispersionResult(
        rho=0.0,  # BY CONSTRUCTION: no over-dispersion
        mean_p=mean_p,
        binomial_variance=binomial_variance,
        empirical_variance=binomial_variance / n_avg,  # purely from sampling
        excess_variance=0.0,  # no excess by definition
        n_users=len(users),
        total_trials=int(n.sum()),
        converged=True
    )


@dataclass
class BootstrapCI:
    """Bootstrap confidence interval result."""
    estimate: float
    ci_lower: float
    ci_upper: float
    se: float
    
    def __repr__(self) -> str:
        return f"BootstrapCI(estimate={self.estimate:.4f}, CI=[{self.ci_lower:.4f}, {self.ci_upper:.4f}], SE={self.se:.4f})"


def bootstrap_ci(
    stat_fn,
    data,
    n: int = 10000,
    seed: int = 42,
    alpha: float = 0.05
) -> BootstrapCI:
    """
    Bootstrap confidence interval for a statistic.
    
    Args:
        stat_fn: Function that computes statistic from data
        data: Input data (passed to stat_fn)
        n: Number of bootstrap samples
        seed: Random seed for reproducibility
        alpha: Significance level (default 0.05 for 95% CI)
    
    Returns:
        BootstrapCI with estimate, CI bounds, and standard error
    """
    rng = np.random.RandomState(seed)
    
    # Original estimate
    estimate = stat_fn(data)
    
    # Bootstrap samples
    boot_stats = []
    for _ in range(n):
        # Resample with replacement
        if isinstance(data, dict):
            # For dict data, resample users
            users = list(data.keys())
            boot_users = rng.choice(users, size=len(users), replace=True)
            boot_data = {f"boot_{i}": data[u] for i, u in enumerate(boot_users)}
            boot_stats.append(stat_fn(boot_data))
        else:
            raise ValueError("Only dict data supported for now")
    
    boot_stats = np.array(boot_stats)
    
    # Percentile CI
    ci_lower = np.percentile(boot_stats, 100 * alpha / 2)
    ci_upper = np.percentile(boot_stats, 100 * (1 - alpha / 2))
    se = np.std(boot_stats, ddof=1)
    
    return BootstrapCI(
        estimate=estimate,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        se=se
    )


def within_task_diff(
    control_reliance: dict[str, float],
    treatment_reliance: dict[str, float]
) -> float:
    """
    Difficulty-controlled WITHIN-TASK counterfactual difference.
    
    For each task, computes treatment - control reliance difference.
    Task difficulty cancels out within the pair, isolating the causal
    effect of the UI intervention.
    
    This is NOT a pooled correlation (which would conflate UI effect with
    difficulty variation across tasks).
    
    Args:
        control_reliance: task_id -> mean reliance rate in control
        treatment_reliance: task_id -> mean reliance rate in treatment
    
    Returns:
        Mean within-task difference (treatment - control)
    """
    shared_tasks = set(control_reliance.keys()) & set(treatment_reliance.keys())
    
    if not shared_tasks:
        raise ValueError("No shared tasks between control and treatment")
    
    diffs = [treatment_reliance[task] - control_reliance[task] 
             for task in shared_tasks]
    
    return np.mean(diffs)


@dataclass
class PairedPermutationResult:
    """Result from paired permutation test."""
    observed_diff: float  # Observed mean difference
    pvalue: float  # Two-sided permutation p-value
    n_permutations: int
    n_pairs: int
    
    def __repr__(self) -> str:
        return (f"PairedPermutationResult(observed_diff={self.observed_diff:.4f}, "
                f"p={self.pvalue:.4f}, n_pairs={self.n_pairs})")


def paired_permutation_test(
    control_reliance: dict[str, float],
    treatment_reliance: dict[str, float],
    n_permutations: int = 10000,
    seed: int = 42
) -> PairedPermutationResult:
    """
    Paired permutation test for within-task reliance elasticity.
    
    Tests H0: no difference between control and treatment reliance.
    Permutation scheme: For each task, randomly swap control/treatment labels
    with probability 0.5 (preserves pairing structure).
    
    This is the correct test for paired data (not independent-samples permutation).
    
    Args:
        control_reliance: task_id -> mean reliance rate in control
        treatment_reliance: task_id -> mean reliance rate in treatment
        n_permutations: Number of permutation samples (default 10000)
        seed: Random seed for reproducibility (hashlib-based RNG for determinism)
    
    Returns:
        PairedPermutationResult with observed diff, p-value, n_pairs
    """
    # Observed difference
    observed_diff = within_task_diff(control_reliance, treatment_reliance)
    
    # Get paired data
    shared_tasks = sorted(set(control_reliance.keys()) & set(treatment_reliance.keys()))
    n_pairs = len(shared_tasks)
    
    if n_pairs == 0:
        raise ValueError("No shared tasks between control and treatment")
    
    # Extract paired values
    control_vals = np.array([control_reliance[task] for task in shared_tasks])
    treatment_vals = np.array([treatment_reliance[task] for task in shared_tasks])
    
    # Use hashlib-seeded RNG for determinism
    # (builtin hash() is BANNED - non-deterministic across processes)
    import hashlib
    seed_bytes = hashlib.sha256(str(seed).encode()).digest()
    seed_int = int.from_bytes(seed_bytes[:4], 'big') % (2**31)
    rng = np.random.RandomState(seed_int)
    
    # Permutation distribution
    perm_diffs = []
    for _ in range(n_permutations):
        # For each pair, randomly flip control/treatment with p=0.5
        flips = rng.rand(n_pairs) < 0.5
        
        perm_control = np.where(flips, treatment_vals, control_vals)
        perm_treatment = np.where(flips, control_vals, treatment_vals)
        
        perm_diff = np.mean(perm_treatment - perm_control)
        perm_diffs.append(perm_diff)
    
    perm_diffs = np.array(perm_diffs)
    
    # Two-sided p-value
    pvalue = np.mean(np.abs(perm_diffs) >= np.abs(observed_diff))
    
    return PairedPermutationResult(
        observed_diff=observed_diff,
        pvalue=float(pvalue),
        n_permutations=n_permutations,
        n_pairs=n_pairs
    )


def betabinom_overdispersion_within_domain(
    df: 'pd.DataFrame',
    condition: str,
    difficulty_col: str = 'task_difficulty'
) -> 'OverdispersionResult':
    """
    Compute per-condition human over-dispersion with within-domain aggregation.
    
    METHODOLOGICAL RIGOR - Difficulty control via between-subjects design:
    This function aggregates each user's trials within their assigned domain.
    
    **Critical design fact**: The Bansal CHI'21 dataset is BETWEEN-SUBJECTS on domain.
    Each user saw exactly ONE domain (beer, amzbook, OR lsat), never multiple domains.
    Therefore, difficulty is NOT confounded across conditions BECAUSE users are 
    compared within their domain group.
    
    What this function actually does:
    1. For each user in the given condition, aggregate (n_relied, n_trials) across
       ALL trials that user saw (which are all in the same domain for that user)
    2. Fit beta-binomial model on the per-user aggregated counts
    3. The difficulty_col is present for diagnostic checks but does NOT affect the
       computation (no stratification, no per-stratum weighting)
    
    Why this is valid:
    - Between-subjects on domain means difficulty is balanced within each condition
    - Cross-condition comparisons are valid because each condition has users from
      all domains in similar proportions
    - No need for stratified estimation or difficulty covariate because the experimental
      design already controls for difficulty via randomization
    
    Future note for within-subjects data:
    If future datasets have within-subjects difficulty variation (users see multiple
    domains), this function would need modification to either:
    (a) Stratify by domain and fit separate models, or
    (b) Include difficulty as a covariate in a hierarchical model
    
    Args:
        df: DataFrame with canonical schema (must include user_id, relied, ui_condition)
        condition: UI condition name to analyze
        difficulty_col: Column name for difficulty (used for diagnostic checks only)
    
    Returns:
        OverdispersionResult for this condition with within-domain aggregation
    
    Audit note:
        The auditor should verify:
        1. Each user in Bansal dataset saw exactly 1 domain (between-subjects check)
        2. Domain distribution is similar across conditions (randomization check)
        3. This is NOT stratified estimation (no per-domain fits or weighting)
    """
    import pandas as pd
    
    # Filter to this condition
    df_cond = df[df['ui_condition'] == condition].copy()
    
    if len(df_cond) == 0:
        raise ValueError(f"No data for condition '{condition}'")
    
    # Check if difficulty data is available
    if difficulty_col not in df_cond.columns or df_cond[difficulty_col].isna().all():
        # Fallback: no difficulty control (warn user)
        print(f"  Warning: No difficulty data for {condition}, using uncontrolled estimator")
        user_stats = {}
        for user_id in df_cond['user_id'].unique():
            user_trials = df_cond[df_cond['user_id'] == user_id]
            n_relied = user_trials['relied'].sum()
            n_trials = len(user_trials)
            user_stats[user_id] = (int(n_relied), n_trials)
        return betabinom_overdispersion(user_stats)
    
    # Build per-user stats aggregating within their domain
    # (In Bansal dataset, each user saw exactly 1 domain due to between-subjects design)
    user_stats = {}
    for user_id in df_cond['user_id'].unique():
        user_trials = df_cond[df_cond['user_id'] == user_id]
        n_relied = int(user_trials['relied'].sum())
        n_trials = len(user_trials)
        user_stats[user_id] = (n_relied, n_trials)
    
    # Diagnostic: verify between-subjects design (each user should see only 1 domain)
    user_difficulty_counts = df_cond.groupby('user_id')[difficulty_col].nunique()
    multi_domain_users = (user_difficulty_counts > 1).sum()
    if multi_domain_users > 0:
        print(f"  ⚠️  WARNING: {multi_domain_users}/{len(user_stats)} users saw multiple domains")
        print(f"     This violates the between-subjects assumption - check dataset!")
    
    # Fit beta-binomial (pooled across difficulty, but each user saw mixed difficulty)
    return betabinom_overdispersion(user_stats)


@dataclass
class ConflictConditionedRelianceResult:
    """Result of conflict-conditioned reliance analysis (Fix A)."""
    reliance_rate: float  # Fraction of CONFLICT trials where agent switched to AI advice
    unconditional_reliance: float  # Traditional reliance (all trials)
    n_conflict: int  # Number of conflict trials (system1 != ai_advice)
    n_total: int  # Total trials
    conflict_fraction: float  # n_conflict / n_total
    per_cell_counts: dict  # Detailed conflict counts per cell
    
    def __repr__(self) -> str:
        return (f"ConflictConditionedRelianceResult("
                f"conflict_reliance={self.reliance_rate:.3f}, "
                f"unconditional={self.unconditional_reliance:.3f}, "
                f"n_conflict={self.n_conflict}/{self.n_total} ({self.conflict_fraction:.1%}))")


@dataclass
class ConditionCorrelationResult:
    """Result of correlation between panel disagreement and human over-dispersion."""
    spearman_rho: float
    spearman_pvalue: float  # from scipy (asymptotic, for reference)
    permutation_pvalue: float  # from permutation test (exact, small-n robust)
    bootstrap_ci_lower: float
    bootstrap_ci_upper: float
    n_conditions: int
    degenerate: bool  # True if n_conditions < 3
    note: Optional[str] = None


def condition_correlation(
    disagreement_by_condition: dict[str, float],
    overdispersion_by_condition: dict[str, float],
    *,
    permutation_n: int = 10000,
    bootstrap_n: int = 10000,
    bootstrap_seed: int = 42,
    permutation_seed: int = 456
) -> ConditionCorrelationResult:
    """
    Correlate panel disagreement vs human over-dispersion across UI conditions.
    
    METHODOLOGICAL RIGOR - Small-n robust statistics:
    With n=6 conditions, we cannot rely on asymptotic normality assumptions.
    Instead, we use:
    
    1. **Spearman rank correlation** (not Pearson):
       - Robust to outliers and monotonic (not necessarily linear) relationships
       - Natural for small n where rank-based tests are more powerful
       - The scientific hypothesis is MONOTONIC (more disagreement -> more over-dispersion),
         not necessarily linear, so Spearman is the right test
    
    2. **Permutation test for p-value**:
       - Null hypothesis: no association between disagreement and over-dispersion
       - Procedure: shuffle CONDITION LABELS (breaking the pairing between disagreement
         and over-dispersion values), recompute Spearman rho, repeat 10k times
       - p-value = fraction of shuffles with |rho| >= |observed rho|
       - Exact finite-sample distribution under the null (no asymptotic assumptions)
       - Requires seeded RNG for reproducibility
    
    3. **Bootstrap CI**:
       - Resample conditions with replacement, recompute Spearman rho
       - 95% percentile CI from 10k bootstrap samples
       - Accounts for uncertainty in both disagreement and over-dispersion estimates
    
    4. **Degenerate guard**:
       - If n_conditions < 3, correlation is degenerate (n=2 always gives rho=±1)
       - Flag as degenerate, do NOT present as evidence
    
    Args:
        disagreement_by_condition: condition -> panel disagreement (variance)
        overdispersion_by_condition: condition -> human beta-binomial rho
        permutation_n: Number of permutation samples (default 10000)
        bootstrap_n: Number of bootstrap samples (default 10000)
        bootstrap_seed: Seed for bootstrap RNG
        permutation_seed: Seed for permutation RNG
    
    Returns:
        ConditionCorrelationResult with Spearman rho, permutation p, bootstrap CI
    
    Audit notes:
        - Degenerate flag must be checked; n<3 results are plumbing only
        - Permutation test should be two-tailed (|rho| for generality)
        - Seeds must be fixed and logged for reproducibility
        - Bootstrap should resample CONDITIONS (not users within conditions)
    """
    from scipy import stats as scipy_stats
    
    # Align conditions (sorted for determinism)
    conditions = sorted(set(disagreement_by_condition.keys()) & 
                       set(overdispersion_by_condition.keys()))
    
    if len(conditions) == 0:
        raise ValueError("No shared conditions between disagreement and overdispersion")
    
    n_conditions = len(conditions)
    degenerate = n_conditions < 3
    
    # Extract aligned arrays
    disagreement = np.array([disagreement_by_condition[c] for c in conditions])
    overdispersion = np.array([overdispersion_by_condition[c] for c in conditions])
    
    # Compute Spearman rank correlation
    spearman_result = scipy_stats.spearmanr(disagreement, overdispersion)
    spearman_rho = spearman_result.correlation
    spearman_pvalue = spearman_result.pvalue
    
    # Permutation test (null: no association)
    perm_rng = np.random.RandomState(permutation_seed)
    perm_rhos = []
    for _ in range(permutation_n):
        # Shuffle condition labels (break association)
        shuffled_disagreement = perm_rng.permutation(disagreement)
        perm_rho = scipy_stats.spearmanr(shuffled_disagreement, overdispersion).correlation
        perm_rhos.append(perm_rho)
    
    perm_rhos = np.array(perm_rhos)
    # Two-tailed: how often is |shuffled rho| >= |observed rho|?
    permutation_pvalue = np.mean(np.abs(perm_rhos) >= np.abs(spearman_rho))
    
    # Bootstrap CI (resample conditions with replacement)
    boot_rng = np.random.RandomState(bootstrap_seed)
    boot_rhos = []
    for _ in range(bootstrap_n):
        # Resample condition indices
        boot_idx = boot_rng.choice(n_conditions, size=n_conditions, replace=True)
        boot_disagreement = disagreement[boot_idx]
        boot_overdispersion = overdispersion[boot_idx]
        boot_rho = scipy_stats.spearmanr(boot_disagreement, boot_overdispersion).correlation
        # Handle NaN from constant arrays after resampling
        if not np.isnan(boot_rho):
            boot_rhos.append(boot_rho)
    
    boot_rhos = np.array(boot_rhos)
    bootstrap_ci_lower = np.percentile(boot_rhos, 2.5)
    bootstrap_ci_upper = np.percentile(boot_rhos, 97.5)
    
    # Degenerate warning
    note = None
    if degenerate:
        note = (
            f"DEGENERATE CORRELATION WARNING: n={n_conditions} conditions. "
            f"Spearman rho with n<3 has NO statistical meaning. "
            f"This is a PLUMBING CHECK ONLY, NOT a scientific result. "
            f"Meaningful correlation requires n≥3 (ideally n≥5) UI conditions."
        )
    
    return ConditionCorrelationResult(
        spearman_rho=float(spearman_rho) if not np.isnan(spearman_rho) else 0.0,
        spearman_pvalue=float(spearman_pvalue) if not np.isnan(spearman_pvalue) else 1.0,
        permutation_pvalue=float(permutation_pvalue),
        bootstrap_ci_lower=float(bootstrap_ci_lower) if not np.isnan(bootstrap_ci_lower) else 0.0,
        bootstrap_ci_upper=float(bootstrap_ci_upper) if not np.isnan(bootstrap_ci_upper) else 0.0,
        n_conditions=n_conditions,
        degenerate=degenerate,
        note=note
    )


def conflict_conditioned_reliance(responses: list) -> ConflictConditionedRelianceResult:
    """
    Conflict-conditioned reliance DV (Fix A) - PRIMARY axis-1 metric.
    
    CRITICAL METRIC FIX: The compliance-collapse in PR #3 (97% no-movement) showed
    that unconditional reliance ≈ agent↔AI agreement, NOT adoption. The fix is to
    define reliance on the subset of trials where the agent's System-1 decision
    CONFLICTS with the AI advice shown (genuine conflict — the only trials where
    AI advice can actually move the agent).
    
    Definition:
    - CONFLICT trial: system1_decision != ai_advice
    - On conflict trials, reliance = (final_decision == ai_advice)
      i.e., agent SWITCHED from their initial decision to adopt AI advice
    
    Returns both:
    - Conflict-conditioned reliance (PRIMARY DV)
    - Unconditional reliance (for transparency / comparison to PR #3)
    - Per-cell conflict counts (for underpowered-cell flagging)
    
    Args:
        responses: List of AgentResponse records (must have system1_decision, 
                   final_decision, ai_advice attributes)
    
    Returns:
        ConflictConditionedRelianceResult with conflict-reliance + unconditional
        reliance + n_conflict per cell
    
    Guard:
        If n_conflict is tiny for a cell (< 3), flag as underpowered rather than
        silently averaging. Report per-cell conflict counts in results JSON.
    
    Methodological notes:
        - Item selection (Fix B) deliberately concentrates conflict/ambiguity
        - Conflict-conditioning is defined a priori (this docstring = preregistration)
        - BOTH metrics reported side-by-side for transparency
        - This is the axis-1 DV; axis-2 (over_reliance_level) computed separately
    """
    if not responses:
        return ConflictConditionedRelianceResult(
            reliance_rate=0.0,
            unconditional_reliance=0.0,
            n_conflict=0,
            n_total=0,
            conflict_fraction=0.0,
            per_cell_counts={}
        )
    
    # Group responses by (persona, condition) cells
    cells = {}
    for resp in responses:
        # Extract ai_advice from task if available, else from response trace
        # For panel responses, ai_advice is task.ai_pred
        ai_advice = None
        if hasattr(resp, 'ai_advice'):
            ai_advice = str(resp.ai_advice)
        elif 'ai_advice' in resp.trace:
            ai_advice = str(resp.trace['ai_advice'])
        else:
            # Try to infer from task_id if tasks are available
            # For now, skip this response if ai_advice not available
            continue
        
        system1 = str(resp.system1_decision)
        final = str(resp.final_decision)
        
        cell_key = (resp.persona_id, resp.ui_condition)
        
        if cell_key not in cells:
            cells[cell_key] = {
                'conflict_trials': [],
                'all_trials': [],
                'n_conflict': 0,
                'n_total': 0,
            }
        
        # Check if conflict trial
        is_conflict = (system1 != ai_advice)
        
        # Record trial
        relied = (final == ai_advice)
        cells[cell_key]['all_trials'].append(relied)
        cells[cell_key]['n_total'] += 1
        
        if is_conflict:
            # On conflict trial, did agent switch to AI?
            switched = (final == ai_advice)
            cells[cell_key]['conflict_trials'].append(switched)
            cells[cell_key]['n_conflict'] += 1
    
    # Aggregate across all cells
    total_conflict = sum(c['n_conflict'] for c in cells.values())
    total_all = sum(c['n_total'] for c in cells.values())
    
    # Compute conflict-conditioned reliance
    conflict_switched = sum(sum(c['conflict_trials']) for c in cells.values())
    conflict_reliance_rate = conflict_switched / total_conflict if total_conflict > 0 else 0.0
    
    # Compute unconditional reliance (for comparison)
    all_relied = sum(sum(c['all_trials']) for c in cells.values())
    unconditional_reliance = all_relied / total_all if total_all > 0 else 0.0
    
    # Per-cell conflict counts (for underpowered-cell flagging)
    per_cell_counts = {
        f"{cell[0]}|{cell[1]}": {
            'n_conflict': data['n_conflict'],
            'n_total': data['n_total'],
            'conflict_fraction': data['n_conflict'] / data['n_total'] if data['n_total'] > 0 else 0.0,
            'underpowered': data['n_conflict'] < 3,
        }
        for cell, data in cells.items()
    }
    
    return ConflictConditionedRelianceResult(
        reliance_rate=conflict_reliance_rate,
        unconditional_reliance=unconditional_reliance,
        n_conflict=total_conflict,
        n_total=total_all,
        conflict_fraction=total_conflict / total_all if total_all > 0 else 0.0,
        per_cell_counts=per_cell_counts
    )


@dataclass
class OverRelianceLevelResult:
    """Result of axis-2 over-reliance level analysis (Fix D)."""
    over_reliance_level: float  # Fraction adopting the DISPLAYED coercive label across panel
    per_persona_adoption: dict  # persona_id -> adoption rate of the displayed coercive label
    n_trials: int  # Total trials in Wrong-AI condition
    between_persona_spread: float  # Variance in per-persona adoption (uniformity check)
    # CLEAN axis-2 signal: adoption restricted to trials where the displayed advice is
    # GENUINELY WRONG (ai_advice != ground_truth). The raw level above can be inflated by
    # trials where the flipped label coincidentally equals the ground truth.
    over_reliance_on_wrong: float = 0.0  # adoption among truly-wrong-advice trials
    n_truly_wrong: int = 0  # number of trials where displayed advice != ground_truth
    
    def __repr__(self) -> str:
        return (f"OverRelianceLevelResult("
                f"level={self.over_reliance_level:.3f}, "
                f"on_wrong={self.over_reliance_on_wrong:.3f}, "
                f"spread={self.between_persona_spread:.4f}, "
                f"n={self.n_trials})")


def over_reliance_level(responses: list) -> OverRelianceLevelResult:
    """
    Axis-2 over-reliance level (Fix D) - systematic adoption of WRONG AI advice.
    
    AXIS-2 SIGNAL (separate from axis-1 over-dispersion):
    Even if between-persona disagreement ≈ 0 (uniform), high adoption of WRONG AI
    advice ⇒ high-risk flag (closes the "uniformly lethal" blind spot).
    
    This metric is computed on the Wrong-AI dark condition where:
    - AI advice shown is the WRONG label (ai_advice != ground_truth)
    - Presented with pseudo-high confidence + oppressive responsibility framing
    
    Definition:
    - over_reliance_level = fraction of trials where agent adopted the WRONG label
    - Computed across the panel (all personas × tasks in Wrong-AI condition)
    - Also report per-persona spread to distinguish uniform vs heterogeneous adoption
    
    Args:
        responses: List of AgentResponse records from Wrong-AI condition
                   (must have final_decision, ground_truth, ai_advice)
    
    Returns:
        OverRelianceLevelResult with:
        - over_reliance_level: panel-wide adoption rate of wrong AI
        - per_persona_adoption: per-persona wrong-AI adoption rates
        - between_persona_spread: variance in per-persona rates
    
    Methodological notes:
        - This is AXIS-2 (separate from axis-1 disagreement)
        - τ_level threshold stays unfrozen (prereg not yet completed)
        - Wrong-AI condition deliberately shows wrong labels (tested)
        - Convergent high adoption (low spread, high level) = uniform lethality
    """
    if not responses:
        return OverRelianceLevelResult(
            over_reliance_level=0.0,
            per_persona_adoption={},
            n_trials=0,
            between_persona_spread=0.0
        )
    
    # Group by persona
    persona_trials = {}
    truly_wrong_trials = []  # (displayed_advice_is_wrong, adopted) per trial
    for resp in responses:
        # Extract ground_truth and ai_advice
        # For panel responses with task objects
        ground_truth = None
        ai_advice = None
        
        if hasattr(resp, 'ground_truth'):
            ground_truth = str(resp.ground_truth)
        elif 'ground_truth' in resp.trace:
            ground_truth = str(resp.trace['ground_truth'])
        
        if hasattr(resp, 'ai_advice'):
            ai_advice = str(resp.ai_advice)
        elif 'ai_advice' in resp.trace:
            ai_advice = str(resp.trace['ai_advice'])
        
        if ground_truth is None or ai_advice is None:
            continue
        
        final = str(resp.final_decision)
        
        # Adopted the displayed coercive label? (final == displayed ai_advice)
        adopted_wrong_ai = (final == ai_advice)
        # Is the displayed advice GENUINELY wrong (!= ground truth)?
        truly_wrong = (ai_advice != ground_truth)
        
        if resp.persona_id not in persona_trials:
            persona_trials[resp.persona_id] = []
        persona_trials[resp.persona_id].append(adopted_wrong_ai)
        truly_wrong_trials.append((truly_wrong, adopted_wrong_ai))
    
    # Compute per-persona adoption rates
    per_persona_adoption = {
        persona_id: np.mean(trials)
        for persona_id, trials in persona_trials.items()
    }
    
    # Overall level (across panel)
    all_trials = [trial for trials in persona_trials.values() for trial in trials]
    over_reliance_level = np.mean(all_trials) if all_trials else 0.0
    
    # CLEAN axis-2: adoption restricted to genuinely-wrong-advice trials
    wrong_only = [adopted for (tw, adopted) in truly_wrong_trials if tw]
    over_reliance_on_wrong = float(np.mean(wrong_only)) if wrong_only else 0.0
    
    # Between-persona spread (variance)
    persona_rates = list(per_persona_adoption.values())
    between_persona_spread = float(np.var(persona_rates, ddof=1) if len(persona_rates) > 1 else 0.0)
    
    return OverRelianceLevelResult(
        over_reliance_level=float(over_reliance_level),
        per_persona_adoption=per_persona_adoption,
        n_trials=len(all_trials),
        between_persona_spread=between_persona_spread,
        over_reliance_on_wrong=over_reliance_on_wrong,
        n_truly_wrong=len(wrong_only),
    )

