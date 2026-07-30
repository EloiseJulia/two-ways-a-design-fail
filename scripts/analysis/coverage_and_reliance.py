"""Increment B + C (zero-compute) for the capability-vulnerability section.

B. VULNERABILITY-COVERAGE PANEL SELECTION as a submodular set-cover problem, and its contrast with
   CAPABILITY-RANKED selection (what a quality-optimal router would do). Universe = the high-severity
   failure cells (dataset x persona) that ANY backend reproduces at adoption >= tau. Coverage f(S) =
   |union of cells a panel S reproduces| is monotone submodular, so greedy gives a (1-1/e) guarantee.
   We report the greedy coverage curve vs the capability-first curve and the panel size each needs to
   reach full coverage. Robustness: repeated with the AI-induced-flip metric (P(adopt | S1 correct)).

C. APPROPRIATE-RELIANCE VOCABULARY (Schemmer et al., IUI'23): RAIR (relative positive AI reliance) and
   RSR (relative self-reliance), computed on the faithful 'Conf.' condition where the AI is sometimes
   right and sometimes wrong. Restates the mismatch in the field's terms: the frontier backend is the
   MOST appropriately-reliant (high RAIR and high RSR) -- good user behaviour -- and its high RSR under
   the adversarial dark condition (= low over-reliance) is exactly why it is a poor vulnerability probe.
"""
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

PERSONAS = ['p1-novice-skeptical', 'p2-expert-trusting', 'p3-moderate-balanced',
            'p4-skilled-skeptical', 'p5-novice-trusting', 'p6-expert-moderate']
DARK = 'Wrong-AI-GT (dark)'
CONF = 'Conf.'
# capability order (strongest -> weakest) by System-1 accuracy from D5.40 (results/capability_vulnerability.json)
ALL_MODELS = ['gpt-4o-mini', 'gpt-4.1', 'gpt-4o', 'gpt-5.5', 'claude-sonnet-4.5', 'gemini-2.5-pro']
FILES = {('beer', 'capladder'): 'results/axis2_powered_capladder_n50.json',
         ('beer', 'crossvendor'): 'results/axis2_powered_crossvendor_n50.json',
         ('amzbook', 'capladder'): 'results/axis2_powered_capladder_amzbook_n50.json',
         ('amzbook', 'crossvendor'): 'results/axis2_powered_crossvendor_amzbook_n50.json'}


def load(conditions):
    rows = []
    for (dom, arm), path in FILES.items():
        d = json.load(open(path))
        for r in d['responses']:
            if r['ui_condition'] not in conditions:
                continue
            m = r['model']
            if m == 'gpt-5.5' and arm != 'capladder':
                continue  # de-dup gpt-5.5 (byte-identical across arms), keep capladder
            truth = int(r['trace']['ground_truth'])
            s1 = int(r['system1_decision'])
            final = int(r['final_decision'])
            ai = int(r['trace']['ai_advice'])
            rows.append(dict(dom=dom, model=m, persona=r['persona_id'], item=str(r['task_id']),
                             cond=r['ui_condition'], truth=truth, s1=s1, final=final, ai_advice=ai,
                             adopt=int(final == 1 - truth), s1_correct=int(s1 == truth),
                             final_correct=int(final == truth), ai_correct=int(ai == truth),
                             follow_ai=int(final == ai)))
    return pd.DataFrame(rows)


# ------------------------- B: submodular vulnerability coverage -------------------------
def coverage_analysis(df, metric='adopt', tau=0.5, cap_order=None):
    """Cells = (dom, persona). A backend covers a cell if its mean `metric` on that cell >= tau
    (for 'flip' the metric is adoption restricted to S1-correct trials). Universe = cells covered by
    any backend. Returns coverage-greedy vs capability-first cumulative coverage curves.
    `cap_order` must be the backends ordered strongest->weakest by the capability proxy."""
    def cell_val(m, dom, p):
        sub = df[(df.model == m) & (df.dom == dom) & (df.persona == p)]
        if metric == 'flip':
            sub = sub[sub.s1_correct == 1]
        return float(sub.adopt.mean()) if len(sub) else 0.0

    cells = [(dom, p) for dom in ['beer', 'amzbook'] for p in PERSONAS]
    covers = {m: {c for c in cells if cell_val(m, c[0], c[1]) >= tau} for m in ALL_MODELS}
    universe = set().union(*covers.values())

    def greedy_marginal():
        chosen, covered, curve = [], set(), []
        remaining = list(ALL_MODELS)
        while remaining:
            best = max(remaining, key=lambda m: len(covers[m] - covered))
            chosen.append(best); covered |= covers[best]; remaining.remove(best)
            curve.append(len(covered))
        return chosen, curve

    def fixed_order(order):
        chosen, covered, curve = [], set(), []
        for m in order:
            chosen.append(m); covered |= covers[m]
            curve.append(len(covered))
        return chosen, curve

    g_order, g_curve = greedy_marginal()
    c_order, c_curve = fixed_order(cap_order)  # capability-first = what a quality router picks
    U = max(len(universe), 1)
    return dict(
        metric=metric, tau=tau, universe_size=len(universe),
        per_backend_cover={m: sorted('%s/%s' % c for c in covers[m]) for m in ALL_MODELS},
        per_backend_cover_n={m: len(covers[m]) for m in ALL_MODELS},
        greedy_order=g_order, greedy_curve=g_curve,
        capability_order=c_order, capability_curve=c_curve,
        greedy_k_for_full=next((i + 1 for i, v in enumerate(g_curve) if v == len(universe)), None),
        capability_k_for_full=next((i + 1 for i, v in enumerate(c_curve) if v == len(universe)), None),
        greedy_auc=round(sum(g_curve) / (U * len(ALL_MODELS)), 3),
        capability_auc=round(sum(c_curve) / (U * len(ALL_MODELS)), 3),
        single_best_cover=max(len(covers[m]) for m in ALL_MODELS),
        single_best_backend=max(ALL_MODELS, key=lambda m: len(covers[m])),
        single_frontier_cover=len(covers[cap_order[0]]),
        frontier_backend=cap_order[0])


# ------------------------- C: appropriate-reliance (RAIR / RSR) -------------------------
def reliance_metrics(sub):
    """RAIR/RSR per Schemmer et al. (IUI'23). Opportunities restricted to conflict (s1 != ai_advice)."""
    # RAIR: of (S1 wrong & AI correct), fraction that switched to the correct AI answer.
    opp_rair = sub[(sub.s1_correct == 0) & (sub.ai_correct == 1)]
    rair = float((opp_rair.final_correct == 1).mean()) if len(opp_rair) else float('nan')
    # RSR: of (S1 correct & AI wrong), fraction that retained the correct own answer.
    opp_rsr = sub[(sub.s1_correct == 1) & (sub.ai_correct == 0)]
    rsr = float((opp_rsr.final_correct == 1).mean()) if len(opp_rsr) else float('nan')
    return dict(RAIR=rair, RSR=rsr, n_rair_opp=int(len(opp_rair)), n_rsr_opp=int(len(opp_rsr)))


def main():
    out = {'coverage': {}, 'reliance': {}}

    # ---- B: coverage (dark condition) ----
    dark = load([DARK])
    conf = load([CONF])
    # capability proxy = mean System-1 accuracy pooled over dark+conf; order strongest -> weakest.
    cap = {m: float(pd.concat([dark, conf])[lambda x: x.model == m].s1_correct.mean()) for m in ALL_MODELS}
    cap_order = sorted(ALL_MODELS, key=lambda m: cap[m], reverse=True)  # what a quality router picks first
    out['capability_s1acc'] = {m: round(cap[m], 3) for m in ALL_MODELS}
    out['capability_order_strong_to_weak'] = cap_order
    out['coverage']['adopt_tau0.5'] = coverage_analysis(dark, 'adopt', 0.5, cap_order)
    out['coverage']['flip_tau0.5'] = coverage_analysis(dark, 'flip', 0.5, cap_order)

    # ---- C: appropriate reliance on the faithful Conf. condition ----
    rel = {'faithful_Conf': {}, 'dark': {}}
    for m in ALL_MODELS:
        rel['faithful_Conf'][m] = reliance_metrics(conf[conf.model == m])
        # over-reliance under adversarial dark = 1 - RSR_dark (AI always wrong there)
        dsub = dark[dark.model == m]
        opp = dsub[dsub.s1_correct == 1]
        rsr_dark = float((opp.final_correct == 1).mean()) if len(opp) else float('nan')
        rel['dark'][m] = dict(RSR_dark=rsr_dark, over_reliance=1 - rsr_dark, n_opp=int(len(opp)))
    out['reliance'] = rel

    capv = np.array([cap[m] for m in ALL_MODELS])
    for name, getter in [('RAIR_conf', lambda m: rel['faithful_Conf'][m]['RAIR']),
                         ('RSR_conf', lambda m: rel['faithful_Conf'][m]['RSR']),
                         ('over_reliance_dark', lambda m: rel['dark'][m]['over_reliance'])]:
        y = np.array([getter(m) for m in ALL_MODELS])
        rho, p = spearmanr(capv, y)
        out.setdefault('correlations', {})[name] = dict(spearman=round(float(rho), 3),
                                                         spearman_p=round(float(p), 4))

    json.dump(out, open('results/coverage_and_reliance.json', 'w'), indent=2)
    printout(out)


def printout(out):
    print('=' * 80)
    print('B. VULNERABILITY-COVERAGE (submodular set-cover): greedy vs capability-first')
    for key in ['adopt_tau0.5', 'flip_tau0.5']:
        c = out['coverage'][key]
        print(' [%s] universe=%d cells | single-best=%d single-frontier(gpt5.5)=%d'
              % (key, c['universe_size'], c['single_best_cover'], c['single_frontier_cover']))
        print('   greedy  order=%s' % ' > '.join(m.replace('-sonnet-4.5', '').replace('gpt-', '') for m in c['greedy_order']))
        print('   greedy  curve=%s  k_for_full=%s  AUC=%.3f' % (c['greedy_curve'], c['greedy_k_for_full'], c['greedy_auc']))
        print('   cap1st  order=%s' % ' > '.join(m.replace('-sonnet-4.5', '').replace('gpt-', '') for m in c['capability_order']))
        print('   cap1st  curve=%s  k_for_full=%s  AUC=%.3f' % (c['capability_curve'], c['capability_k_for_full'], c['capability_auc']))
    print('=' * 80)
    print('C. APPROPRIATE RELIANCE (Schemmer IUI23): faithful Conf. RAIR/RSR + dark over-reliance')
    print('  %-18s cap(S1) RAIR  RSR   RSR_dark  overRel(dark)' % 'backend')
    for m in ALL_MODELS:
        f = out['reliance']['faithful_Conf'][m]; d = out['reliance']['dark'][m]
        print('  %-18s %.3f  %.3f %.3f  %.3f    %.3f'
              % (m, out['capability_s1acc'][m], f['RAIR'], f['RSR'], d['RSR_dark'], d['over_reliance']))
    print('  correlations (Spearman across 6 backends), capability vs:')
    for k, v in out['correlations'].items():
        print('    %-20s rho=%.2f (p=%.3f)' % (k, v['spearman'], v['spearman_p']))
    print('-> results/coverage_and_reliance.json')


if __name__ == '__main__':
    main()
