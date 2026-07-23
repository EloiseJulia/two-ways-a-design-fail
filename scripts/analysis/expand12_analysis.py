"""n=12 backend-expansion analysis (D5.51). Reads result files only; zero proxy.

Merges the existing 6 backends (axis2_powered_{capladder,crossvendor}{,_amzbook}.json) with the 6 NEW
backends (axis2_expand12_{beer,amzbook}.json) and recomputes, at n=12 and reporting ALL 12:
  1. capability (mean System-1 accuracy) per backend
  2. capability vs vulnerability (p5 dark adoption, AI-induced flip) Spearman + BH  -- now powered at n=12
  3. vulnerability-coverage set-cover (single frontier vs coverage-greedy vs capability-first) at n=12
  4. RAIR / RSR appropriate reliance across all 12

Runs on whatever domains are present (beer first; amzbook when Phase 2 lands). Missing new-backend files
are skipped with a warning so this can be run as soon as beer completes.
"""
import json
import os
import itertools
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

PERSONAS = ['p1-novice-skeptical', 'p2-expert-trusting', 'p3-moderate-balanced',
            'p4-skilled-skeptical', 'p5-novice-trusting', 'p6-expert-moderate']
TARGET = 'p5-novice-trusting'
DARK = 'Wrong-AI-GT (dark)'
CONF = 'Conf.'
EXISTING = ['gpt-4o-mini', 'gpt-4.1', 'gpt-4o', 'gpt-5.5', 'claude-sonnet-4.5', 'gemini-2.5-pro']
NEW = ['gpt-3.5-turbo', 'gpt-4', 'gpt-5.4', 'claude-haiku-4.5', 'claude-opus-4.6', 'gemini-3.1-pro-preview']
ALL12 = EXISTING + NEW

# existing-6 sources (dark + Conf.); gpt-5.5 de-duped to capladder
EXISTING_FILES = {('beer', 'capladder'): 'results/axis2_powered_capladder.json',
                  ('beer', 'crossvendor'): 'results/axis2_powered_crossvendor.json',
                  ('amzbook', 'capladder'): 'results/axis2_powered_capladder_amzbook.json',
                  ('amzbook', 'crossvendor'): 'results/axis2_powered_crossvendor_amzbook.json'}
NEW_FILES = {'beer': 'results/axis2_expand12_beer.json', 'amzbook': 'results/axis2_expand12_amzbook.json'}


def _rows(responses, dom, arm=None):
    out = []
    for r in responses:
        cond = r['ui_condition']
        if cond not in (DARK, CONF):
            continue
        m = r['model']
        if arm is not None:  # existing files: filter to existing-6 + de-dup gpt-5.5
            if m not in EXISTING:
                continue
            if m == 'gpt-5.5' and arm != 'capladder':
                continue
        else:
            if m not in NEW:
                continue
        truth = int(r['trace']['ground_truth'])
        s1 = int(r['system1_decision']); final = int(r['final_decision'])
        ai = int(r['trace']['ai_advice'])
        out.append(dict(dom=dom, model=m, persona=r['persona_id'], item=str(r['task_id']), cond=cond,
                        truth=truth, s1=s1, final=final, ai_advice=ai,
                        adopt=int(final == 1 - truth), s1_correct=int(s1 == truth),
                        final_correct=int(final == truth), ai_correct=int(ai == truth)))
    return out


def load():
    rows = []
    present = set()
    for (dom, arm), path in EXISTING_FILES.items():
        if os.path.exists(path):
            rows += _rows(json.load(open(path))['responses'], dom, arm=arm); present.add(dom)
    for dom, path in NEW_FILES.items():
        if os.path.exists(path):
            rows += _rows(json.load(open(path))['responses'], dom); present.add(('new', dom))
        else:
            print(f'[warn] new-backend file missing (skipped): {path}')
    return pd.DataFrame(rows)


def reliance(sub):
    opp_rair = sub[(sub.s1_correct == 0) & (sub.ai_correct == 1) & (sub.cond == CONF)]
    rair = float((opp_rair.final_correct == 1).mean()) if len(opp_rair) else float('nan')
    opp_rsr = sub[(sub.s1_correct == 1) & (sub.ai_correct == 0) & (sub.cond == CONF)]
    rsr = float((opp_rsr.final_correct == 1).mean()) if len(opp_rsr) else float('nan')
    return rair, rsr, int(len(opp_rair)), int(len(opp_rsr))


def bh(pvals):
    p = np.array(pvals, float); n = len(p); order = np.argsort(p)
    adj = np.empty(n); prev = 1.0
    for rank, idx in enumerate(reversed(order)):
        k = n - rank
        prev = min(prev, p[idx] * n / k); adj[idx] = prev
    return adj


def coverage(df, metric, tau, cap_order):
    models = [m for m in ALL12 if m in set(df.model)]
    def cellval(m, dom, p):
        s = df[(df.model == m) & (df.dom == dom) & (df.persona == p) & (df.cond == DARK)]
        if metric == 'flip':
            s = s[s.s1_correct == 1]
        return float(s.adopt.mean()) if len(s) else 0.0
    doms = sorted(df[df.cond == DARK].dom.unique())
    cells = [(d, p) for d in doms for p in PERSONAS]
    covers = {m: {c for c in cells if cellval(m, c[0], c[1]) >= tau} for m in models}
    universe = set().union(*covers.values()) if covers else set()
    def greedy():
        chosen, cov, curve = [], set(), []
        rem = list(models)
        while rem:
            b = max(rem, key=lambda m: len(covers[m] - cov))
            chosen.append(b); cov |= covers[b]; rem.remove(b); curve.append(len(cov))
        return chosen, curve
    capord = [m for m in cap_order if m in models]
    def fixed(order):
        cov, curve = set(), []
        for m in order:
            cov |= covers[m]; curve.append(len(cov))
        return curve
    g_order, g_curve = greedy()
    U = max(len(universe), 1)
    return dict(metric=metric, tau=tau, universe=len(universe), n_backends=len(models),
                single_best=max((len(covers[m]) for m in models), default=0),
                single_best_backend=max(models, key=lambda m: len(covers[m])) if models else None,
                single_frontier=len(covers.get(capord[0], set())) if capord else 0,
                frontier_backend=capord[0] if capord else None,
                greedy_order=g_order, greedy_curve=g_curve,
                greedy_k_full=next((i + 1 for i, v in enumerate(g_curve) if v == len(universe)), None),
                capability_curve=fixed(capord),
                capability_k_full=next((i + 1 for i, v in enumerate(fixed(capord)) if v == len(universe)), None))


def main():
    df = load()
    models = [m for m in ALL12 if m in set(df.model)]
    out = {'n_backends': len(models), 'backends_present': models}
    print(f'backends present: {len(models)}/12 -> {models}')

    cap = {m: float(df[df.model == m].s1_correct.mean()) for m in models}
    cap_order = sorted(models, key=lambda m: cap[m], reverse=True)
    out['capability_s1acc'] = {m: round(cap[m], 3) for m in models}
    out['capability_order_strong_to_weak'] = cap_order

    # per-backend vulnerability metrics (pooled over present domains)
    pb = {}
    for m in models:
        d = df[(df.model == m) & (df.cond == DARK)]
        p5 = d[d.persona == TARGET]
        flip = d[d.s1_correct == 1]
        rair, rsr, nr, ns = reliance(df[df.model == m])
        pb[m] = dict(p5_adopt=round(float(p5.adopt.mean()), 3) if len(p5) else None,
                     agg_adopt=round(float(d.adopt.mean()), 3) if len(d) else None,
                     flip=round(float(flip.adopt.mean()), 3) if len(flip) else None,
                     RAIR=round(rair, 3), RSR=round(rsr, 3), n_rair=nr, n_rsr=ns)
    out['per_backend'] = pb

    # correlations capability vs vulnerability across all present backends
    out['correlations'] = {}
    capv = np.array([cap[m] for m in models])
    for key in ['p5_adopt', 'agg_adopt', 'flip']:
        y = np.array([pb[m][key] if pb[m][key] is not None else np.nan for m in models])
        ok = ~np.isnan(y)
        if ok.sum() >= 3:
            rho, p = spearmanr(capv[ok], y[ok])
            out['correlations'][key] = dict(spearman=round(float(rho), 3), p=round(float(p), 4), n=int(ok.sum()))

    # coverage at n=12
    out['coverage'] = {'adopt_tau0.5': coverage(df, 'adopt', 0.5, cap_order),
                       'flip_tau0.5': coverage(df, 'flip', 0.5, cap_order)}

    json.dump(out, open('results/expand12_analysis.json', 'w'), indent=2)
    printout(out)


def printout(out):
    print('=' * 78)
    print('CAPABILITY (S1 acc) vs VULNERABILITY, n=%d backends' % out['n_backends'])
    print('  %-22s cap   p5adopt aggAdopt flip  RAIR  RSR' % 'backend')
    for m in out['capability_order_strong_to_weak']:
        d = out['per_backend'][m]
        print('  %-22s %.3f %s   %s   %s %s %s'
              % (m, out['capability_s1acc'][m], d['p5_adopt'], d['agg_adopt'], d['flip'], d['RAIR'], d['RSR']))
    print('  --- correlations (Spearman, capability vs) ---')
    for k, v in out['correlations'].items():
        print('   %-10s rho=%.2f p=%.3f (n=%d)' % (k, v['spearman'], v['p'], v['n']))
    for key, c in out['coverage'].items():
        print(' COVERAGE[%s] universe=%d single-best=%d(%s) single-frontier=%d(%s) greedy_k=%s cap_k=%s'
              % (key, c['universe'], c['single_best'], c['single_best_backend'], c['single_frontier'],
                 c['frontier_backend'], c['greedy_k_full'], c['capability_k_full']))
    print('-> results/expand12_analysis.json')


if __name__ == '__main__':
    main()
