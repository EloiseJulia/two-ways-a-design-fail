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
