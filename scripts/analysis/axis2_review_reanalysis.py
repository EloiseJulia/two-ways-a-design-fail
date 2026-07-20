"""Review-response reanalyses (compute-free; reads results/axis2_powered_*.json).

Addresses external CHI reviewer comments 3.2/3.4/3.5 with the EXISTING raw data:

(A) COERCION-FRAMING CONTRAST (3.2, 3.5): on the matched subset of items where the shown AI advice is
    WRONG in the neutral conditions, compare wrong-advice adoption under neutral (Conf.) vs placebo vs
    coercive (dark) framing, holding item + wrong-label constant. Isolates the coercive high-confidence
    framing from ordinary wrong-advice following, and gives a NON-arbitrary baseline for "resists"
    (dark vs neutral, not dark vs 0.5). Also a conflict-conditioned variant using system1_decision.

(B) PERSONA-P5 ROBUSTNESS UNDER ITEM-CLUSTERED INFERENCE (3.4): re-estimate the p5>others effect with
    item-clustered GEE (items are the pseudo-replication unit) and an item-level bootstrap CI of the
    p5-minus-others adoption gap, instead of treating 120 trials/cell as independent. The 1/6 sign-test
    is reported as DESCRIPTIVE only (personas are not exchangeable).

Dark condition adoption = final_decision == 1 - ground_truth. gpt-5.5 de-duplicated (kept from capladder).
"""
import json
import itertools
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact
import statsmodels.api as sm
from statsmodels.genmod.cov_struct import Exchangeable

PERSONAS = ['p1-novice-skeptical', 'p2-expert-trusting', 'p3-moderate-balanced',
            'p4-skilled-skeptical', 'p5-novice-trusting', 'p6-expert-moderate']
TARGET = 'p5-novice-trusting'
COND_NEUTRAL, COND_PLACEBO, COND_DARK = 'Conf.', 'Conf.+Placebo', 'Wrong-AI-GT (dark)'
FILES = {
    ('beer', 'capladder'): 'results/axis2_powered_capladder.json',
    ('beer', 'crossvendor'): 'results/axis2_powered_crossvendor.json',
    ('amzbook', 'capladder'): 'results/axis2_powered_capladder_amzbook.json',
    ('amzbook', 'crossvendor'): 'results/axis2_powered_crossvendor_amzbook.json',
}


def load_all():
    rows = []
    for (domain, arm), path in FILES.items():
        d = json.load(open(path))
        for r in d['responses']:
            model = r['model']
            if model == 'gpt-5.5' and arm != 'capladder':
                continue  # de-dup shared anchor
            gt = int(r['trace']['ground_truth'])
            adv = int(r['trace']['ai_advice'])
            rows.append(dict(domain=domain, model=model, persona=r['persona_id'],
                             item=str(r['task_id']), cond=r['ui_condition'],
                             truth=gt, adv=adv, adv_wrong=int(adv == 1 - gt),
                             s1=int(r['system1_decision']), final=int(r['final_decision'])))
    return pd.DataFrame(rows)


def bootstrap_ci(values, statfn, n=5000, seed=42):
    rng = np.random.default_rng(seed)
    arr = np.asarray(values)
    stats = [statfn(arr[rng.integers(0, len(arr), len(arr))]) for _ in range(n)]
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


# ============================ (A) COERCION CONTRAST ============================
def coercion_contrast(df):
    out = {'per_cell': [], 'pooled': {}}
    # matched wrong-item set per cell = items where neutral (Conf.) shows wrong advice
    per_cell_rows = []
    for (domain, model), g in df.groupby(['domain', 'model']):
        neutral_wrong_items = set(g[(g.cond == COND_NEUTRAL) & (g.adv_wrong == 1)].item)
        rec = dict(domain=domain, model=model, n_matched_items=len(neutral_wrong_items))
        for cond, key in [(COND_NEUTRAL, 'neutral'), (COND_PLACEBO, 'placebo'), (COND_DARK, 'dark')]:
            sub = g[(g.cond == cond) & (g.item.isin(neutral_wrong_items))].copy()
            # on these items the shown advice is the wrong label (1-gt) in every condition
            sub = sub[sub.adv == (1 - sub.truth)]
            adopt = (sub.final == (1 - sub.truth)).mean() if len(sub) else np.nan
            rec[f'adopt_{key}'] = float(adopt)
            rec[f'n_{key}'] = int(len(sub))
            # conflict-conditioned: among s1 != wrong label, fraction switching TO wrong
            cc = sub[sub.s1 != (1 - sub.truth)]
            rec[f'switch_{key}'] = float((cc.final == (1 - cc.truth)).mean()) if len(cc) else np.nan
            rec[f'n_conflict_{key}'] = int(len(cc))
        rec['delta_dark_minus_neutral'] = rec['adopt_dark'] - rec['adopt_neutral']
        rec['delta_dark_minus_placebo'] = rec['adopt_dark'] - rec['adopt_placebo']
        per_cell_rows.append(rec)
    out['per_cell'] = per_cell_rows

    # pooled stratified logistic: adopt ~ C(cond) on matched wrong items, item-clustered, per domain,
    # model as fixed effect. condition coded neutral(ref)/placebo/dark.
    for domain in ['beer', 'amzbook']:
        recs = []
        for (dom, model), g in df.groupby(['domain', 'model']):
            if dom != domain:
                continue
            neutral_wrong_items = set(g[(g.cond == COND_NEUTRAL) & (g.adv_wrong == 1)].item)
            sub = g[g.cond.isin([COND_NEUTRAL, COND_PLACEBO, COND_DARK]) &
                    g.item.isin(neutral_wrong_items)].copy()
            sub = sub[sub.adv == (1 - sub.truth)]
            sub['adopt'] = (sub.final == (1 - sub.truth)).astype(int)
            sub['is_dark'] = (sub.cond == COND_DARK).astype(int)
            sub['is_placebo'] = (sub.cond == COND_PLACEBO).astype(int)
            sub['model'] = model
            recs.append(sub[['adopt', 'is_dark', 'is_placebo', 'model', 'item']])
        dd = pd.concat(recs, ignore_index=True)
        try:
            res = sm.GEE.from_formula('adopt ~ is_dark + is_placebo + C(model)', groups='item',
                                      data=dd, family=sm.families.Binomial(),
                                      cov_struct=Exchangeable()).fit()
            out['pooled'][domain] = dict(
                dark_OR=float(np.exp(res.params['is_dark'])),
                dark_OR_ci=[float(np.exp(res.conf_int().loc['is_dark'][0])),
                            float(np.exp(res.conf_int().loc['is_dark'][1]))],
                dark_p=float(res.pvalues['is_dark']),
                placebo_OR=float(np.exp(res.params['is_placebo'])),
                placebo_p=float(res.pvalues['is_placebo']),
                n_obs=int(len(dd)))
        except Exception as e:
            out['pooled'][domain] = f'NA ({e})'
    return out


# ============ (B) PERSONA-P5 UNDER ITEM-CLUSTERED INFERENCE (dark only) ============
def persona_itemclustered(df):
    dark = df[df.cond == COND_DARK].copy()
    dark['adopt'] = (dark.final == (1 - dark.truth)).astype(int)
    dark['is_p5'] = (dark.persona == TARGET).astype(int)
    dark['cell'] = dark.domain + '|' + dark.model
    out = {}
    # GEE clustered by ITEM (pseudo-replication unit), pooled across all cells
    try:
        res_item = sm.GEE.from_formula('adopt ~ is_p5', groups='item', data=dark,
                                       family=sm.families.Binomial(), cov_struct=Exchangeable()).fit()
        out['gee_item_clustered'] = dict(
            OR=float(np.exp(res_item.params['is_p5'])),
            OR_ci=[float(np.exp(res_item.conf_int().loc['is_p5'][0])),
                   float(np.exp(res_item.conf_int().loc['is_p5'][1]))],
            p=float(res_item.pvalues['is_p5']))
    except Exception as e:
        out['gee_item_clustered'] = f'NA ({e})'
    # GEE clustered by CELL (as before, for comparison)
    try:
        res_cell = sm.GEE.from_formula('adopt ~ is_p5', groups='cell', data=dark,
                                       family=sm.families.Binomial(), cov_struct=Exchangeable()).fit()
        out['gee_cell_clustered'] = dict(OR=float(np.exp(res_cell.params['is_p5'])),
                                         p=float(res_cell.pvalues['is_p5']))
    except Exception as e:
        out['gee_cell_clustered'] = f'NA ({e})'
    # item-level bootstrap of the mean per-cell (p5 - others) gap: resample ITEMS with replacement
    items = sorted(dark.item.unique())
    cells = sorted(dark.cell.unique())
    # precompute per (cell, item, persona-group) adoption
    def gap_from_items(sampled_items):
        gaps = []
        for c in cells:
            sub = dark[(dark.cell == c) & (dark.item.isin(sampled_items))]
            if len(sub) == 0:
                continue
            p5 = sub[sub.is_p5 == 1].adopt.mean()
            oth = sub[sub.is_p5 == 0].adopt.mean()
            gaps.append(p5 - oth)
        return np.mean(gaps)
    rng = np.random.default_rng(42)
    boot = []
    for _ in range(3000):
        samp = rng.choice(items, size=len(items), replace=True)
        boot.append(gap_from_items(samp))
    out['gap_item_bootstrap'] = dict(mean=float(np.mean(boot)),
                                     ci=[float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))])
    # descriptive 12/12 (report as descriptive, NOT vs 1/6 exchangeable null)
    strict = 0
    for c in cells:
        sub = dark[dark.cell == c]
        rates = sub.groupby('persona').adopt.mean()
        strict += int(rates.idxmax() == TARGET and (rates == rates.max()).sum() == 1)
    out['p5_strict_top_cells'] = f'{strict}/{len(cells)}'
    return out


def main():
    df = load_all()
    result = {'coercion_contrast': coercion_contrast(df),
              'persona_itemclustered': persona_itemclustered(df)}
    json.dump(result, open('results/axis2_review_reanalysis.json', 'w'), indent=2)
    printout(result)


def printout(result):
    cc = result['coercion_contrast']
    print('=' * 78)
    print('(A) COERCION-FRAMING CONTRAST (matched naturally-wrong items; adopt = final==1-gt)')
    print('  %-8s %-18s items  neutral placebo dark   d(dark-neut) d(dark-plac)  |switch: neut/plac/dark'
          % ('domain', 'model'))
    for r in cc['per_cell']:
        print('  %-8s %-18s %4d   %.2f    %.2f    %.2f   %+.2f       %+.2f        %.2f/%.2f/%.2f'
              % (r['domain'], r['model'], r['n_matched_items'], r['adopt_neutral'], r['adopt_placebo'],
                 r['adopt_dark'], r['delta_dark_minus_neutral'], r['delta_dark_minus_placebo'],
                 r['switch_neutral'], r['switch_placebo'], r['switch_dark']))
    print('  POOLED stratified logistic (item-clustered, model FE), dark vs neutral:')
    for dom, v in cc['pooled'].items():
        if isinstance(v, dict):
            print('     [%s] dark OR=%.2f CI[%.2f,%.2f] p=%.3g | placebo OR=%.2f p=%.3g | n=%d'
                  % (dom, v['dark_OR'], v['dark_OR_ci'][0], v['dark_OR_ci'][1], v['dark_p'],
                     v['placebo_OR'], v['placebo_p'], v['n_obs']))
        else:
            print('     [%s] %s' % (dom, v))
    print('=' * 78)
    pi = result['persona_itemclustered']
    print('(B) PERSONA-P5 UNDER ITEM-CLUSTERED INFERENCE (dark)')
    print('  descriptive strict-top:', pi['p5_strict_top_cells'])
    print('  GEE cell-clustered :', pi['gee_cell_clustered'])
    print('  GEE ITEM-clustered :', pi['gee_item_clustered'])
    print('  p5-minus-others gap, ITEM bootstrap:', pi['gap_item_bootstrap'])
    print('  -> results/axis2_review_reanalysis.json')


if __name__ == '__main__':
    main()

