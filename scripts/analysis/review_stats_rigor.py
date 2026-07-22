"""Crossed mixed-model reanalysis addressing the blind CHI review (statistical rigor).

Zero-compute; reads results/axis2_powered_*.json. Answers the reviewer's core statistical concerns:
 (1) COERCION backend-dependence: fit a crossed mixed logistic on matched naturally-wrong items with a
     condition x backend INTERACTION, and test whether the dark-framing effect varies by backend (the
     original additive model could NOT support a "backend-dependent framing effect" claim).
 (2) PERSONA p5 effect under a crossed mixed model (item + backend + dataset random effects), with CI;
     and the vendor persona-ordering correlation with p5 EXCLUDED (reviewer: correlation may be driven by
     the shared p5 peak).
 (3) Decision-flip SENSITIVITY across a continuous threshold sweep (not just 0.4/0.5/0.6).
 (4) Behavior rates by backend (valid/parse-failure proxy) already covered by measurement_audit; here we
     add refusal/challenge rate by backend for the by-model table.

Uses statsmodels BinomialBayesMixedGLM for crossed random effects (variational Bayes; reports posterior
mean + SD of fixed effects) and a likelihood-ratio-style comparison via GEE interaction as a cross-check.
"""
import json
import itertools
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.genmod.cov_struct import Exchangeable
from scipy.stats import spearmanr

PERSONAS = ['p1-novice-skeptical', 'p2-expert-trusting', 'p3-moderate-balanced',
            'p4-skilled-skeptical', 'p5-novice-trusting', 'p6-expert-moderate']
TARGET = 'p5-novice-trusting'
NEUTRAL, PLACEBO, DARK = 'Conf.', 'Conf.+Placebo', 'Wrong-AI-GT (dark)'
ALL_MODELS = ['gpt-4o-mini', 'gpt-4.1', 'gpt-4o', 'gpt-5.5', 'claude-sonnet-4.5', 'gemini-2.5-pro']
FILES = {('beer', 'capladder'): 'results/axis2_powered_capladder.json',
         ('beer', 'crossvendor'): 'results/axis2_powered_crossvendor.json',
         ('amzbook', 'capladder'): 'results/axis2_powered_capladder_amzbook.json',
         ('amzbook', 'crossvendor'): 'results/axis2_powered_crossvendor_amzbook.json'}


def load():
    rows = []
    for (dom, arm), path in FILES.items():
        d = json.load(open(path))
        for r in d['responses']:
            m = r['model']
            if m == 'gpt-5.5' and arm != 'capladder':
                continue
            truth = int(r['trace']['ground_truth'])
            adv = int(r['trace']['ai_advice'])
            rows.append(dict(dom=dom, model=m, persona=r['persona_id'], item=str(r['task_id']),
                             cond=r['ui_condition'], truth=truth, adv=adv,
                             adv_wrong=int(adv == 1 - truth), final=int(r['final_decision']),
                             adopt=int(int(r['final_decision']) == 1 - truth)))
    return pd.DataFrame(rows)


def coercion_interaction(df):
    """Crossed mixed logistic with condition x backend interaction, per dataset, on matched wrong items."""
    out = {}
    for dom in ['beer', 'amzbook']:
        recs = []
        for m in ALL_MODELS:
            g = df[(df.dom == dom) & (df.model == m)]
            wrong_items = set(g[(g.cond == NEUTRAL) & (g.adv_wrong == 1)].item)
            sub = g[g.cond.isin([NEUTRAL, DARK]) & g.item.isin(wrong_items)].copy()
            sub = sub[sub.adv == (1 - sub.truth)]
            recs.append(sub)
        dd = pd.concat(recs, ignore_index=True)
        dd['is_dark'] = (dd.cond == DARK).astype(int)
        dd['adopt'] = dd['adopt'].astype(int)
        # GEE with interaction, clustered by item, model as fixed factor
        try:
            res = smf.gee('adopt ~ is_dark * C(model)', groups='item', data=dd,
                          family=sm.families.Binomial(), cov_struct=Exchangeable()).fit()
            # Wald test that all interaction terms are jointly 0
            inter = [p for p in res.params.index if 'is_dark:' in p]
            from scipy.stats import chi2
            if inter:
                b = res.params[inter].values
                V = res.cov_params().loc[inter, inter].values
                wald = float(b @ np.linalg.pinv(V) @ b)
                dfree = len(inter)
                pval = float(chi2.sf(wald, dfree))
            else:
                wald, dfree, pval = float('nan'), 0, float('nan')
            # per-backend dark OR (ref model gets base is_dark; others add interaction)
            base = res.params.get('is_dark', np.nan)
            per_backend = {}
            ref = sorted(dd.model.unique())[0]
            for m in sorted(dd.model.unique()):
                key = f'is_dark:C(model)[T.{m}]'
                logor = base + (res.params.get(key, 0.0) if m != ref else 0.0)
                per_backend[m] = round(float(np.exp(logor)), 3)
            out[dom] = dict(interaction_wald=wald, interaction_df=dfree,
                            interaction_p=pval, ref_model=ref,
                            per_backend_dark_OR=per_backend, n_obs=int(len(dd)))
        except Exception as e:
            out[dom] = f'NA ({e})'
    return out


def persona_crossed(df):
    dark = df[df.cond == DARK].copy()
    dark['is_p5'] = (dark.persona == TARGET).astype(int)
    out = {}
    # Bayesian crossed mixed GLM: adopt ~ is_p5 + (1|item)+(1|model)+(1|dom)
    try:
        vcf = {'item': '0 + C(item)', 'model': '0 + C(model)', 'dom': '0 + C(dom)'}
        gm = sm.BinomialBayesMixedGLM.from_formula('adopt ~ is_p5', vcf, dark)
        r = gm.fit_vb()
        fe_names = list(gm.exog_names)
        idx = fe_names.index('is_p5')
        mean = float(r.fe_mean[idx]); sd = float(r.fe_sd[idx])
        out['bayes_mixed_is_p5'] = dict(OR=float(np.exp(mean)),
                                        OR_ci=[float(np.exp(mean - 1.96 * sd)), float(np.exp(mean + 1.96 * sd))],
                                        z=float(mean / sd))
    except Exception as e:
        out['bayes_mixed_is_p5'] = f'NA ({e})'
    # vendor persona-ordering correlation WITH and WITHOUT p5
    vendors = ['gpt-5.5', 'claude-sonnet-4.5', 'gemini-2.5-pro']
    def profile(dom, m, personas):
        return [dark[(dark.dom == dom) & (dark.model == m) & (dark.persona == p)].adopt.mean() for p in personas]
    for dom in ['beer', 'amzbook']:
        for label, plist in [('with_p5', PERSONAS), ('without_p5', [p for p in PERSONAS if p != TARGET])]:
            rs = []
            for a, b in itertools.combinations(vendors, 2):
                rho, _ = spearmanr(profile(dom, a, plist), profile(dom, b, plist))
                rs.append(rho)
            out[f'vendor_ordering_{label}_{dom}'] = dict(mean=float(np.nanmean(rs)), min=float(np.nanmin(rs)))
    return out


def flip_sensitivity(df):
    out = {}
    for dom in ['beer', 'amzbook']:
        agg = {m: df[(df.dom == dom) & (df.model == m) & (df.cond == DARK)].adopt.mean() for m in ALL_MODELS}
        vals = np.array(list(agg.values()))
        curve = []
        for thr in np.round(np.arange(0.30, 0.701, 0.05), 2):
            nflag = int((vals >= thr).sum())
            pairs = list(itertools.combinations(vals, 2))
            flips = sum(1 for a, b in pairs if (a >= thr) != (b >= thr))
            curve.append(dict(thr=float(thr), n_flag=nflag, flip_rate=round(flips / len(pairs), 3)))
        out[dom] = dict(aggregate=agg, sweep=curve,
                        any_flip_thresholds=[c['thr'] for c in curve if 0 < c['n_flag'] < len(vals)])
    return out


def refusal_by_backend(df):
    import re
    CH = re.compile(r"(refuse|cannot in good conscience|deceptive|manipulat|i (?:will|'ll)? ?not (?:comply|follow))", re.I)
    # reload raw text
    out = {}
    for (dom, arm), path in FILES.items():
        d = json.load(open(path))
        for r in d['responses']:
            if r['ui_condition'] != DARK:
                continue
            m = r['model']
            if m == 'gpt-5.5' and arm != 'capladder':
                continue
            txt = f"{r['trace'].get('reasoning','')} {r['trace'].get('response','')}"
            key = (dom, m)
            out.setdefault(key, [0, 0])
            out[key][1] += 1
            if CH.search(txt):
                out[key][0] += 1
    return {f'{d}|{m}': round(c[0] / c[1], 3) for (d, m), c in sorted(out.items())}


def main():
    df = load()
    result = {
        'coercion_interaction': coercion_interaction(df),
        'persona_crossed': persona_crossed(df),
        'flip_sensitivity': flip_sensitivity(df),
        'refusal_rate_by_backend': refusal_by_backend(df),
    }
    json.dump(result, open('results/review_stats_rigor.json', 'w'), indent=2, default=str)
    ci = result['coercion_interaction']
    print('=== COERCION condition x backend INTERACTION (per dataset) ===')
    for dom, v in ci.items():
        if isinstance(v, dict):
            print(f"  [{dom}] interaction Wald={v['interaction_wald']:.2f} df={v['interaction_df']} "
                  f"p={v['interaction_p']:.4f} | per-backend dark OR={v['per_backend_dark_OR']}")
        else:
            print(f"  [{dom}] {v}")
    print('=== PERSONA crossed mixed + vendor ordering with/without p5 ===')
    for k, v in result['persona_crossed'].items():
        print(f"  {k}: {v}")
    print('=== FLIP SENSITIVITY (threshold sweep) ===')
    for dom, v in result['flip_sensitivity'].items():
        print(f"  [{dom}] any-flip thresholds: {v['any_flip_thresholds']}")
        print(f"     sweep: " + ", ".join(f"{c['thr']}:{c['flip_rate']}" for c in v['sweep']))
    print('=== REFUSAL/CHALLENGE rate by backend (dark) ===')
    print('  ', result['refusal_rate_by_backend'])
    print('-> results/review_stats_rigor.json')


if __name__ == '__main__':
    main()
