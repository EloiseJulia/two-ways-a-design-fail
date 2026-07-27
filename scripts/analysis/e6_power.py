"""A-priori power analysis for E6-stripped (H1 within-subject coercion; H2 between-subject
index moderation). Monte Carlo under EXPLICIT, clearly-labelled assumptions -- this estimates
SENSITIVITY to a real effect, it does not assume the effect exists.

Run: python scripts/analysis/e6_power.py
"""
import numpy as np

RNG = np.random.default_rng(20260728)
def sig(x): return 1/(1+np.exp(-x))
def logit(p): return np.log(p/(1-p))

def power_H1(N, p_floor, p_dark, n_trials=10, sd_u=1.0, nsim=2000, alpha=0.05):
    """Within-subject: per-participant (Dark - Placebo) wrong-adoption gap; one-sided sign-flip perm test."""
    rej = 0
    for _ in range(nsim):
        u = RNG.normal(0, sd_u, N)
        p_f = sig(logit(p_floor) + u); p_d = sig(logit(p_dark) + u)
        kf = RNG.binomial(n_trials, p_f); kd = RNG.binomial(n_trials, p_d)
        diff = kd/n_trials - kf/n_trials
        obs = diff.mean()
        # sign-flip permutation null
        signs = RNG.choice([-1,1], size=(500, N))
        perm = (signs * diff).mean(axis=1)
        p = (1 + np.sum(perm >= obs)) / (1 + len(perm))
        rej += p < alpha
    return rej / nsim

def power_H2(N, p_low, p_high, frac_high=0.5, n_trials=10, sd_u=1.0, nsim=2000, alpha=0.05):
    """Between-subject: high- vs low-index Dark adoption; two-sided Mann-Whitney on per-participant rates."""
    from scipy.stats import mannwhitneyu
    rej = 0
    for _ in range(nsim):
        is_high = RNG.random(N) < frac_high
        nh, nl = int(is_high.sum()), int((~is_high).sum())
        if nh < 3 or nl < 3:
            continue
        u = RNG.normal(0, sd_u, N)
        p = np.where(is_high, sig(logit(p_high)+u), sig(logit(p_low)+u))
        k = RNG.binomial(n_trials, p) / n_trials
        try:
            _, pv = mannwhitneyu(k[is_high], k[~is_high], alternative="two-sided")
        except ValueError:
            continue
        rej += pv < alpha
    return rej / nsim

if __name__ == "__main__":
    print("="*72)
    print("H1  within-subject coercion: Dark vs Placebo floor (per-participant gap)")
    print("    assume placebo floor p0=0.20, n_trials=10, participant SD(logit)=1.0")
    print(f"{'N':>4} | {'p_dark=0.35':>12} {'p_dark=0.45':>12} {'p_dark=0.55':>12}")
    for N in (20,30,40,50,60):
        row = [power_H1(N, 0.20, pd) for pd in (0.35,0.45,0.55)]
        print(f"{N:>4} | {row[0]:>12.2f} {row[1]:>12.2f} {row[2]:>12.2f}")

    print("\n"+"="*72)
    print("H2  between-subject index moderation on Dark (high- vs low-index adoption)")
    print("    n_trials=10, SD(logit)=1.0, BALANCED split (frac_high=0.50)")
    print(f"{'N':>4} | {'gap .15 (.30/.45)':>18} {'gap .25 (.30/.55)':>18}")
    for N in (20,30,40,50,60,80):
        a = power_H2(N, 0.30, 0.45, 0.50); b = power_H2(N, 0.30, 0.55, 0.50)
        print(f"{N:>4} | {a:>18.2f} {b:>18.2f}")

    print("\n"+"="*72)
    print("H2 under ACADEMIC SKEW (few trusting-novices, frac_high=0.30) -- why purposive recruiting matters")
    print(f"{'N':>4} | {'gap .15':>10} {'gap .25':>10}")
    for N in (40,60,80):
        a = power_H2(N, 0.30, 0.45, 0.30); b = power_H2(N, 0.30, 0.55, 0.30)
        print(f"{N:>4} | {a:>10.2f} {b:>10.2f}")
