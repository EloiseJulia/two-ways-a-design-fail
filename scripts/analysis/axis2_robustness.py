"""Axis-2 robustness hardening analyses (compute-free; reads results/axis2_powered_*.json).

Produces, for the paper:
  (1) persona-p5 (novice-trusting) robustness: is it significantly the most-susceptible persona,
      across model x domain cells? (rank sign-test + Wilcoxon magnitude + per-cell Fisher(BH) + GEE)
  (2) ordering agreement: aggregate wrong-AI over-reliance RATE is model-idiosyncratic, while the
      6-persona RISK ORDERING is cross-vendor robust (pairwise rank correlations).
  (3) stats hygiene: Wilson CIs + binomial vs chance (BH) for every cell; between-model contrasts.

Dark condition = 'Wrong-AI-GT (dark)'. Over-reliance (adopt) = final_decision == 1 - ground_truth
(recomputed from ground_truth; E4 sign firewall). gpt-5.5 is shared between the capladder and
crossvendor files (byte-identical) and is de-duplicated (kept from capladder).
"""
import json
import itertools
import numpy as np
import pandas as pd
from scipy.stats import binomtest, fisher_exact, spearmanr, wilcoxon
import statsmodels.api as sm
from statsmodels.genmod.cov_struct import Exchangeable

DARK = 'Wrong-AI-GT (dark)'
PERSONAS = ['p1-novice-skeptical', 'p2-expert-trusting', 'p3-moderate-balanced',
            'p4-skilled-skeptical', 'p5-novice-trusting', 'p6-expert-moderate']
TARGET = 'p5-novice-trusting'

FILES = {
    ('beer', 'capladder'): 'results/axis2_powered_capladder_n50.json',
    ('beer', 'crossvendor'): 'results/axis2_powered_crossvendor_n50.json',
    ('amzbook', 'capladder'): 'results/axis2_powered_capladder_amzbook_n50.json',
    ('amzbook', 'crossvendor'): 'results/axis2_powered_crossvendor_amzbook_n50.json',
}


def load_dark_records():
    """Return long-form DataFrame of dark-condition trials, gpt-5.5 de-duplicated."""
    rows = []
    for (domain, arm), path in FILES.items():
        d = json.load(open(path))
        for r in d['responses']:
            if r['ui_condition'] != DARK:
                continue
            model = r['model']
            # de-dup gpt-5.5: keep the capladder copy only
            if model == 'gpt-5.5' and arm != 'capladder':
                continue
            gt = int(r['trace']['ground_truth'])
            disp = 1 - gt  # displayed (guaranteed-wrong) AI advice
            # sign firewall: the stored ai_advice must equal 1-gt in the dark arm
            assert int(r['trace']['ai_advice']) == disp, 'sign check failed in dark arm!'
            adopt = 1 if int(r['final_decision']) == disp else 0
            rows.append(dict(domain=domain, model=model, persona=r['persona_id'],
                             item=str(r['task_id']), adopt=adopt))
    return pd.DataFrame(rows)


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (float('nan'), float('nan'))
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = (z * ((p * (1 - p) / n + z**2 / (4 * n**2)) ** 0.5)) / denom
    return (center - half, center + half)


def bh(pvals):
    p = np.asarray(pvals, float)
    n = len(p)
    order = np.argsort(p)
    adj = np.empty(n)
    prev = 1.0
    for rank in range(n - 1, -1, -1):
        i = order[rank]
        val = p[i] * n / (rank + 1)
        prev = min(prev, val)
        adj[i] = prev
    return adj


def main():
    df = load_dark_records()
    cells = sorted(df.groupby(['domain', 'model']).groups.keys())
    out = {'n_cells': len(cells), 'cells': [], 'analysis1_persona_p5': {},
           'analysis2_ordering': {}, 'analysis3_hygiene': {}}

    # ---- per-cell persona adoption table ----
    cell_persona = {}  # (domain,model) -> {persona: (k, n, rate)}
    for (domain, model), g in df.groupby(['domain', 'model']):
        pt = {}
        for p in PERSONAS:
            gp = g[g.persona == p]
            k, n = int(gp.adopt.sum()), len(gp)
            pt[p] = (k, n, k / n if n else float('nan'))
        cell_persona[(domain, model)] = pt

    # ============ ANALYSIS 1: persona-p5 robustness ============
    a1 = out['analysis1_persona_p5']
    strict_top = 0
    tie_top = 0
    per_cell = []
    p5_minus_others = []
    per_cell_fisher_p = []
    for (domain, model) in cells:
        pt = cell_persona[(domain, model)]
        rates = {p: pt[p][2] for p in PERSONAS}
        mx = max(rates.values())
        top = [p for p, v in rates.items() if v == mx]
        is_strict = (top == [TARGET])
        is_tie_incl = (TARGET in top)
        strict_top += int(is_strict)
        tie_top += int(is_tie_incl)
        others_rate = np.mean([rates[p] for p in PERSONAS if p != TARGET])
        gap = rates[TARGET] - others_rate
        p5_minus_others.append(gap)
        k5, n5, _ = pt[TARGET]
        ko = sum(pt[p][0] for p in PERSONAS if p != TARGET)
        no = sum(pt[p][1] for p in PERSONAS if p != TARGET)
        _, fp = fisher_exact([[k5, n5 - k5], [ko, no - ko]], alternative='greater')
        per_cell_fisher_p.append(fp)
        per_cell.append(dict(domain=domain, model=model, p5_rate=rates[TARGET],
                             others_mean=others_rate, gap=gap, p5_is_strict_top=is_strict,
                             p5_in_top=is_tie_incl, fisher_p_greater=fp))
    fisher_bh = bh(per_cell_fisher_p)
    for row, adj in zip(per_cell, fisher_bh):
        row['fisher_bh'] = float(adj)
    a1['per_cell'] = per_cell
    a1['strict_top_count'] = f'{strict_top}/{len(cells)}'
    a1['in_top_count'] = f'{tie_top}/{len(cells)}'
    a1['signtest_strict_vs_1_6'] = binomtest(strict_top, len(cells), 1/6, alternative='greater').pvalue
    a1['signtest_intop_vs_1_6'] = binomtest(tie_top, len(cells), 1/6, alternative='greater').pvalue
    gaps = np.array(p5_minus_others)
    a1['gap_mean'] = float(gaps.mean())
    a1['gap_min'] = float(gaps.min())
    try:
        w = wilcoxon(gaps, alternative='greater')
        a1['wilcoxon_gap_gt0_p'] = float(w.pvalue)
    except Exception as e:
        a1['wilcoxon_gap_gt0_p'] = f'NA ({e})'
    df2 = df.copy()
    df2['is_p5'] = (df2.persona == TARGET).astype(int)
    df2['cell'] = df2.domain + '|' + df2.model
    try:
        model_gee = sm.GEE.from_formula('adopt ~ is_p5', groups='cell', data=df2,
                                        family=sm.families.Binomial(), cov_struct=Exchangeable())
        res = model_gee.fit()
        coef = res.params['is_p5']
        ci = res.conf_int().loc['is_p5'].tolist()
        a1['gee_is_p5'] = dict(odds_ratio=float(np.exp(coef)),
                               or_ci=[float(np.exp(ci[0])), float(np.exp(ci[1]))],
                               p=float(res.pvalues['is_p5']))
    except Exception as e:
        a1['gee_is_p5'] = f'NA ({e})'

    # ============ ANALYSIS 2: ordering agreement vs rate idiosyncrasy ============
    a2 = out['analysis2_ordering']
    agg = {}
    for (domain, model) in cells:
        pt = cell_persona[(domain, model)]
        k = sum(pt[p][0] for p in PERSONAS)
        n = sum(pt[p][1] for p in PERSONAS)
        agg[(domain, model)] = k / n
    a2['aggregate_rate'] = {f'{d}|{m}': agg[(d, m)] for (d, m) in cells}
    for domain in ['beer', 'amzbook']:
        vals = [agg[(d, m)] for (d, m) in cells if d == domain]
        a2[f'aggregate_rate_spread_{domain}'] = dict(min=min(vals), max=max(vals),
                                                     range=max(vals) - min(vals), sd=float(np.std(vals)))
    rankvecs = {}
    for (domain, model) in cells:
        pt = cell_persona[(domain, model)]
        rankvecs[(domain, model)] = [pt[p][2] for p in PERSONAS]

    def mean_pairwise(keys):
        rs = []
        for a, b in itertools.combinations(keys, 2):
            rho, _ = spearmanr(rankvecs[a], rankvecs[b])
            rs.append(rho)
        return rs
    for domain in ['beer', 'amzbook']:
        keys = [(d, m) for (d, m) in cells if d == domain]
        rs = mean_pairwise(keys)
        a2[f'ordering_spearman_within_{domain}'] = dict(mean=float(np.mean(rs)),
                                                        min=float(np.min(rs)), n_pairs=len(rs))
    vendors = ['gpt-5.5', 'claude-sonnet-4.5', 'gemini-2.5-pro']
    for domain in ['beer', 'amzbook']:
        keys = [(domain, m) for m in vendors]
        rs = mean_pairwise(keys)
        a2[f'ordering_spearman_indepvendor_{domain}'] = dict(mean=float(np.mean(rs)),
                                                            min=float(np.min(rs)), n_pairs=len(rs))
    cd = {}
    for m in sorted(set(m for (_, m) in cells)):
        if (('beer', m) in rankvecs) and (('amzbook', m) in rankvecs):
            rho, _ = spearmanr(rankvecs[('beer', m)], rankvecs[('amzbook', m)])
            cd[m] = float(rho)
    a2['ordering_spearman_crossdomain_by_model'] = cd

    # ============ ANALYSIS 3: stats hygiene ============
    a3 = out['analysis3_hygiene']
    rows = []
    pvals = []
    for (domain, model) in cells:
        pt = cell_persona[(domain, model)]
        k = sum(pt[p][0] for p in PERSONAS)
        n = sum(pt[p][1] for p in PERSONAS)
        lo, hi = wilson_ci(k, n)
        bt = binomtest(k, n, 0.5)
        rows.append(dict(domain=domain, model=model, k=k, n=n, rate=k / n,
                         wilson_lo=lo, wilson_hi=hi, binom_p_two=bt.pvalue))
        pvals.append(bt.pvalue)
    adj = bh(pvals)
    for row, a in zip(rows, adj):
        row['binom_bh'] = float(a)
        row['sig_after_bh'] = bool(a < 0.05)
    a3['per_cell'] = rows
    contrasts = [('gpt-4.1', 'gpt-4o'), ('gpt-4.1', 'gpt-4o-mini'), ('gpt-5.5', 'gpt-4.1'),
                 ('claude-sonnet-4.5', 'gpt-5.5'), ('gemini-2.5-pro', 'gpt-5.5')]
    cres = []
    for domain in ['beer', 'amzbook']:
        for m1, m2 in contrasts:
            if (domain, m1) not in cell_persona or (domain, m2) not in cell_persona:
                continue
            pt1, pt2 = cell_persona[(domain, m1)], cell_persona[(domain, m2)]
            k1 = sum(pt1[p][0] for p in PERSONAS); n1 = sum(pt1[p][1] for p in PERSONAS)
            k2 = sum(pt2[p][0] for p in PERSONAS); n2 = sum(pt2[p][1] for p in PERSONAS)
            _, fp = fisher_exact([[k1, n1 - k1], [k2, n2 - k2]])
            cres.append(dict(domain=domain, m1=m1, m2=m2, rate1=k1 / n1, rate2=k2 / n2,
                             fisher_p_two=fp))
    a3['between_model_contrasts'] = cres

    json.dump(out, open('results/axis2_robustness.json', 'w'), indent=2)
    print_summary(out)


def print_summary(out):
    a1, a2, a3 = out['analysis1_persona_p5'], out['analysis2_ordering'], out['analysis3_hygiene']
    print('=' * 70)
    print('ANALYSIS 1 - persona-p5 robustness (', out['n_cells'], 'domain x model cells)')
    print('  p5 strict top persona in', a1['strict_top_count'],
          '| in top (incl ties)', a1['in_top_count'])
    print('  sign-test strict vs chance(1/6): p =', f"{a1['signtest_strict_vs_1_6']:.2e}")
    print('  p5-minus-others gap: mean=%.3f min=%.3f | Wilcoxon>0 p=%s'
          % (a1['gap_mean'], a1['gap_min'], a1['wilcoxon_gap_gt0_p']))
    print('  GEE adopt~is_p5:', a1['gee_is_p5'])
    print('  per-cell Fisher(BH) p5>others:')
    for r in a1['per_cell']:
        print('     %-8s %-18s p5=%.2f others=%.2f gap=%+.2f fisherBH=%.3g strictTop=%s'
              % (r['domain'], r['model'], r['p5_rate'], r['others_mean'], r['gap'],
                 r['fisher_bh'], r['p5_is_strict_top']))
    print('=' * 70)
    print('ANALYSIS 2 - ordering agreement vs rate idiosyncrasy')
    for domain in ['beer', 'amzbook']:
        s = a2[f'aggregate_rate_spread_{domain}']
        print('  [%s] aggregate RATE spread: min=%.3f max=%.3f range=%.3f sd=%.3f'
              % (domain, s['min'], s['max'], s['range'], s['sd']))
        ow = a2[f'ordering_spearman_within_{domain}']
        iv = a2[f'ordering_spearman_indepvendor_{domain}']
        print('     persona ORDERING agreement: within-domain mean rho=%.3f (min %.3f, %d pairs)'
              % (ow['mean'], ow['min'], ow['n_pairs']))
        print('        independent-vendor (gpt5.5/claude/gemini) mean rho=%.3f (min %.3f)'
              % (iv['mean'], iv['min']))
    print('  cross-domain ordering by model:',
          {k: round(v, 3) for k, v in a2['ordering_spearman_crossdomain_by_model'].items()})
    print('=' * 70)
    print('ANALYSIS 3 - stats hygiene (Wilson CI + binom vs 0.5, BH-adjusted)')
    for r in a3['per_cell']:
        print('  %-8s %-18s rate=%.3f [%.3f,%.3f] binomBH=%.3g sig=%s'
              % (r['domain'], r['model'], r['rate'], r['wilson_lo'], r['wilson_hi'],
                 r['binom_bh'], r['sig_after_bh']))
    print('  between-model contrasts (Fisher two-sided):')
    for c in a3['between_model_contrasts']:
        print('     [%s] %-18s vs %-12s %.3f vs %.3f  p=%.3g'
              % (c['domain'], c['m1'], c['m2'], c['rate1'], c['rate2'], c['fisher_p_two']))
    print('  -> results/axis2_robustness.json written')


if __name__ == '__main__':
    main()
