"""Few-cluster-robust re-estimation of the pooled coercive-framing effect (audit follow-up).

The headline dark-vs-neutral OR is estimated by a GEE with an exchangeable working correlation
clustered on ITEMS -- but there are only 8 matched-wrong item clusters per domain, the same
few-cluster regime the paper disowns for the dark x model interaction. GEE robust ("sandwich")
SEs are anti-conservative with <~40 clusters, so the reported CIs are likely too narrow.

This script re-estimates the SAME pooled effect (adopt ~ is_dark + is_placebo + C(model) on the
matched naturally-wrong items) with three few-cluster-valid alternatives and compares them to the
GEE point estimate:
  (A) Bayesian mixed logistic with an ITEM random intercept (partial pooling; VB posterior).
  (B) item-cluster bootstrap (resample the ~8 items with replacement; percentile CI).
  (C) item fixed-effects logistic (within-item dark effect) for a lower-bound sanity check.
Also reports the naive-independence GLM CI to show how much the clustering matters.

No new data; reads results/axis2_powered_*.json via load_all(). Run from repo root:
  python scripts/analysis/coercion_fewcluster.py
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
from statsmodels.tools.sm_exceptions import PerfectSeparationError

sys.path.insert(0, str(Path(__file__).resolve().parent))
from axis2_review_reanalysis import load_all, COND_NEUTRAL, COND_PLACEBO, COND_DARK

warnings.simplefilter("ignore")

FORMULA = "adopt ~ is_dark + is_placebo + C(model)"


def build_pooled(df, domain):
    """Reconstruct the matched-wrong-item pooled frame used by the GEE (identical construction)."""
    recs = []
    for (dom, model), g in df.groupby(["domain", "model"]):
        if dom != domain:
            continue
        neutral_wrong_items = set(g[(g.cond == COND_NEUTRAL) & (g.adv_wrong == 1)].item)
        sub = g[g.cond.isin([COND_NEUTRAL, COND_PLACEBO, COND_DARK]) &
                g.item.isin(neutral_wrong_items)].copy()
        sub = sub[sub.adv == (1 - sub.truth)]
        sub["adopt"] = (sub.final == (1 - sub.truth)).astype(int)
        sub["is_dark"] = (sub.cond == COND_DARK).astype(int)
        sub["is_placebo"] = (sub.cond == COND_PLACEBO).astype(int)
        sub["model"] = model
        recs.append(sub[["adopt", "is_dark", "is_placebo", "model", "item"]])
    return pd.concat(recs, ignore_index=True)


def gee_or(dd):
    from statsmodels.genmod.cov_struct import Exchangeable
    res = sm.GEE.from_formula(FORMULA, groups="item", data=dd,
                              family=sm.families.Binomial(), cov_struct=Exchangeable()).fit()
    ci = res.conf_int().loc["is_dark"]
    return dict(OR=float(np.exp(res.params["is_dark"])),
                CI=[float(np.exp(ci[0])), float(np.exp(ci[1]))], p=float(res.pvalues["is_dark"]))


def naive_or(dd):
    res = smf.logit(FORMULA, data=dd).fit(disp=0)
    ci = res.conf_int().loc["is_dark"]
    return dict(OR=float(np.exp(res.params["is_dark"])),
                CI=[float(np.exp(ci[0])), float(np.exp(ci[1]))], p=float(res.pvalues["is_dark"]))


def bayes_mixed_or(dd):
    """Item random intercept (partial pooling). VB posterior mean/sd on the logit scale."""
    vc = {"item": "0 + C(item)"}
    m = BinomialBayesMixedGLM.from_formula(FORMULA, vc, dd)
    r = m.fit_vb(verbose=False)
    names = list(r.model.exog_names)
    i = names.index("is_dark")
    mean, sd = float(r.fe_mean[i]), float(r.fe_sd[i])
    return dict(OR=float(np.exp(mean)),
                CI=[float(np.exp(mean - 1.96 * sd)), float(np.exp(mean + 1.96 * sd))],
                logit_mean=mean, logit_sd=sd)


def item_fe_or(dd):
    res = smf.logit("adopt ~ is_dark + is_placebo + C(item)", data=dd).fit(disp=0)
    ci = res.conf_int().loc["is_dark"]
    return dict(OR=float(np.exp(res.params["is_dark"])),
                CI=[float(np.exp(ci[0])), float(np.exp(ci[1]))], p=float(res.pvalues["is_dark"]))


def item_cluster_bootstrap(dd, n=3000, seed=42):
    rng = np.random.default_rng(seed)
    items = sorted(dd.item.unique())
    ors, fails = [], 0
    for _ in range(n):
        samp = rng.choice(items, size=len(items), replace=True)
        parts = []
        for k, it in enumerate(samp):
            b = dd[dd.item == it].copy()
            b["item"] = f"{it}__{k}"  # keep resampled clusters distinct
            parts.append(b)
        bd = pd.concat(parts, ignore_index=True)
        try:
            res = smf.logit(FORMULA, data=bd).fit(disp=0)
            ors.append(float(np.exp(res.params["is_dark"])))
        except (PerfectSeparationError, np.linalg.LinAlgError, ValueError):
            fails += 1
    ors = np.array(ors)
    return dict(OR_median=float(np.median(ors)),
                CI=[float(np.percentile(ors, 2.5)), float(np.percentile(ors, 97.5))],
                n_ok=int(len(ors)), n_fail=int(fails))


def main():
    df = load_all()
    out = {}
    for domain in ["beer", "amzbook"]:
        dd = build_pooled(df, domain)
        n_items = dd.item.nunique()
        res = dict(n_obs=int(len(dd)), n_item_clusters=int(n_items))
        res["gee_reported"] = gee_or(dd)
        res["naive_independence"] = naive_or(dd)
        res["item_random_intercept_vb"] = bayes_mixed_or(dd)
        res["item_fixed_effects"] = item_fe_or(dd)
        res["item_cluster_bootstrap"] = item_cluster_bootstrap(dd)
        out[domain] = res
        print("=" * 78)
        print(f"[{domain}]  n_obs={res['n_obs']}  item clusters={n_items}")
        for k in ["gee_reported", "naive_independence", "item_random_intercept_vb",
                  "item_fixed_effects", "item_cluster_bootstrap"]:
            v = res[k]
            orv = v.get("OR", v.get("OR_median"))
            extra = f" p={v['p']:.3g}" if "p" in v else (f" n_ok={v['n_ok']}/{v['n_ok']+v['n_fail']}" if "n_ok" in v else "")
            print(f"  {k:26s} OR={orv:.2f}  CI[{v['CI'][0]:.2f},{v['CI'][1]:.2f}]{extra}")
    Path("results").mkdir(exist_ok=True)
    json.dump(out, open("results/coercion_fewcluster.json", "w"), indent=2)
    print("\n-> results/coercion_fewcluster.json")


if __name__ == "__main__":
    main()
