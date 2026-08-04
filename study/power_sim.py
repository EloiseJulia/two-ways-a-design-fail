"""Monte-Carlo power for the PRIMARY confirmatory contrast (dark vs neutral wrong-advice adoption).

Within-subject design: N participants x 12 items x 3 framings (neutral/placebo/dark), Latin-square so
each participant sees ~4 items per framing; the AI advice is guaranteed-wrong in every trial. We simulate
a mixed logistic with participant + item random intercepts and fit a subject-cluster-robust logistic
regression (condition dummies), testing the one-sided dark>neutral coefficient at alpha=.05.

Run: python study/power_sim.py
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

RNG = np.random.default_rng(20260803)
N = 80            # participants
K = 12            # items (per participant; one domain each)
CONDS = ["neutral", "placebo", "dark"]
SUBJ_SD = 1.0     # participant random-intercept SD (logit)
ITEM_SD = 0.5     # item random-intercept SD (logit)
N_SIM = 400


def logit(p):
    return np.log(p / (1 - p))


def simulate_power(p_neutral, p_dark, p_placebo=None, n=N, n_sim=N_SIM):
    if p_placebo is None:
        p_placebo = p_neutral  # placebo == neutral floor (paper's finding)
    b0 = logit(p_neutral)
    b_dark = logit(p_dark) - b0
    b_plac = logit(p_placebo) - b0
    hits = 0
    for _ in range(n_sim):
        subj_re = RNG.normal(0, SUBJ_SD, n)
        item_re = RNG.normal(0, ITEM_SD, K)
        rows = []
        for s in range(n):
            # Latin-square style: assign each item a condition, balanced ~4/cond
            order = RNG.permutation(K)
            for j, it in enumerate(order):
                cond = CONDS[j % 3]
                eff = b_dark if cond == "dark" else (b_plac if cond == "placebo" else 0.0)
                eta = b0 + eff + subj_re[s] + item_re[it]
                p = 1 / (1 + np.exp(-eta))
                rows.append((s, it, cond, RNG.binomial(1, p)))
        df = pd.DataFrame(rows, columns=["subj", "item", "cond", "adopt"])
        df["cond"] = pd.Categorical(df["cond"], categories=CONDS)
        try:
            m = smf.logit("adopt ~ C(cond)", data=df).fit(disp=0)
            cov = m.cov_params()  # cluster-robust would need groups; use model SE (approx, slightly liberal)
            # subject-cluster-robust:
            m = smf.logit("adopt ~ C(cond)", data=df).fit(
                disp=0, cov_type="cluster", cov_kwds={"groups": df["subj"]})
            coef = m.params["C(cond)[T.dark]"]
            se = m.bse["C(cond)[T.dark]"]
            z = coef / se
            # one-sided dark>neutral
            from scipy.stats import norm
            p_one = 1 - norm.cdf(z)
            if p_one < 0.05 and coef > 0:
                hits += 1
        except Exception:
            continue
    return hits / n_sim


if __name__ == "__main__":
    scenarios = [
        ("OR~1.9 (synthetic beer): 0.32 -> 0.47", 0.32, 0.47),
        ("OR~1.5 (conservative):   0.35 -> 0.45", 0.35, 0.45),
        ("OR~1.3 (weak):           0.38 -> 0.44", 0.38, 0.44),
    ]
    print(f"N={N} participants, {K} items, ~{K//3}/condition, {N_SIM} sims, subjSD={SUBJ_SD} itemSD={ITEM_SD}")
    for label, p0, p1 in scenarios:
        pw = simulate_power(p0, p1)
        print(f"  {label:42s} power(dark>neutral, 1-sided .05) = {pw:.2f}")
