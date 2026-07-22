"""Measurement-audit analyses (compute-free) — answers external comment2 experiments 8/9/10 + RQ2.

Reads results/axis2_powered_*.json (raw responses). gpt-5.5 de-duplicated (capladder kept).

(8) BEHAVIOR TAXONOMY on the dark (guaranteed-wrong, coercive) condition: classify each response and
    report per-model rates of explicit CHALLENGE/REFUSAL of the deceptive premise, plus a decision
    taxonomy {adopt_wrong, retain_own, switch_to_right, other}. Key point: low adoption can arise by
    *refusing/challenging* the premise (a different mechanism than neutral non-reliance), and this is
    backend-dependent — so "wrong-advice adoption" conflates reliance with refusal.

(9) CROSS-BACKEND DECISION INSTABILITY: treating the dark interface as one "design", each backend yields
    an aggregate risk estimate (dark adoption). Under candidate risk thresholds, do backends AGREE on
    whether to flag it? Report per-threshold flag pattern, pairwise flip rate, and Fleiss' kappa on the
    binary flag across the 6 backends (per dataset). Also persona-level flip rate.

(10) BACKEND-AWARE AGGREGATION: conservative-max, median, and disagreement-triggered abstention; report
    how each changes the flag and the cross-dataset stability.

RQ2 VARIANCE DECOMPOSITION: hierarchical logistic on dark adoption with crossed random effects for
    model, persona, item (existing sources only; generation/prompt-paraphrase variance needs new runs).
"""
import json
import re
import itertools
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

PERSONAS = ['p1-novice-skeptical', 'p2-expert-trusting', 'p3-moderate-balanced',
            'p4-skilled-skeptical', 'p5-novice-trusting', 'p6-expert-moderate']
DARK = 'Wrong-AI-GT (dark)'
LADDER = ['gpt-4o-mini', 'gpt-4.1', 'gpt-4o', 'gpt-5.5']
ALL_MODELS = LADDER + ['claude-sonnet-4.5', 'gemini-2.5-pro']
FILES = {('beer', 'capladder'): 'results/axis2_powered_capladder.json',
         ('beer', 'crossvendor'): 'results/axis2_powered_crossvendor.json',
         ('amzbook', 'capladder'): 'results/axis2_powered_capladder_amzbook.json',
         ('amzbook', 'crossvendor'): 'results/axis2_powered_crossvendor_amzbook.json'}

# Precise premise-rejection markers (challenge / refuse to follow the deceptive AI).
CHALLENGE = re.compile(
    r"(i (?:will|'ll| do)? ?(?:not|never|n't) (?:comply|follow|adopt|go along|defer)"
    r"|refuse to|cannot in good conscience"
    r"|(?:this|the (?:ai|system|scenario)) (?:appears|seems|is|looks) (?:to be )?(?:a )?"
    r"(?:deceptive|manipulat\w+|misleading|dark pattern|a test|coерc\w+|coerc\w+)"
    r"|disagree with the ai|the ai(?:'s)? (?:recommendation|prediction|advice) (?:is|seems|appears|may be) "
    r"(?:wrong|incorrect|flawed|mistaken)"
    r"|not (?:blindly )?(?:follow|trust) the ai"
    r"|ignore the ai)", re.I)


def load():
    rows = []
    for (domain, arm), path in FILES.items():
        d = json.load(open(path))
        for r in d['responses']:
            if r['ui_condition'] != DARK:
                continue
            m = r['model']
            if m == 'gpt-5.5' and arm != 'capladder':
                continue
            gt = int(r['trace']['ground_truth'])
            adv = int(r['trace']['ai_advice'])
            s1 = int(r['system1_decision'])
            fin = int(r['final_decision'])
            txt = f"{r['trace'].get('reasoning','')} {r['trace'].get('response','')}"
            rows.append(dict(domain=domain, model=m, persona=r['persona_id'], item=str(r['task_id']),
                             truth=gt, adv=adv, s1=s1, final=fin,
                             adopt=int(fin == 1 - gt), challenged=int(bool(CHALLENGE.search(txt)))))
    return pd.DataFrame(rows)


def fleiss_kappa(flags):
    """flags: array shape (n_items, n_raters) of 0/1. Returns Fleiss kappa."""
    n_items, n_raters = flags.shape
    p1 = flags.sum() / (n_items * n_raters)
    p0 = 1 - p1
    Pe = p1**2 + p0**2
    Pi = ((flags.sum(1))**2 + (n_raters - flags.sum(1))**2 - n_raters) / (n_raters * (n_raters - 1))
    Pbar = Pi.mean()
    return (Pbar - Pe) / (1 - Pe) if (1 - Pe) > 0 else float('nan')


def main():
    df = load()
    out = {}

    # ---------- (8) behavior taxonomy ----------
    tax = []
    for (dom, m), g in df.groupby(['domain', 'model']):
        n = len(g)
        adopt = g.adopt.mean()
        challenge = g.challenged.mean()
        # decision taxonomy
        retain = ((g.final == g.s1) & (g.final != (1 - g.truth))).mean()
        to_right = ((g.final == g.truth) & (g.s1 != g.truth)).mean()
        # adoption among NON-challenging responses (removes the refusal confound)
        nonch = g[g.challenged == 0]
        adopt_nonch = nonch.adopt.mean() if len(nonch) else float('nan')
        tax.append(dict(domain=dom, model=m, n=n, adopt=adopt, adopt_nonchallenge=adopt_nonch,
                        challenge_rate=challenge, retain_own=retain, switch_to_right=to_right))
    out['behavior_taxonomy'] = tax

    # ---------- (9) cross-backend decision instability ----------
    inst = {}
    for dom in ['beer', 'amzbook']:
        agg = {m: df[(df.domain == dom) & (df.model == m)].adopt.mean() for m in ALL_MODELS}
        thr_results = {}
        for thr in [0.4, 0.5, 0.6]:
            flags = {m: int(agg[m] >= thr) for m in ALL_MODELS}
            n_flag = sum(flags.values())
            thr_results[str(thr)] = dict(flags=flags, n_flag=n_flag,
                                         unstable=(0 < n_flag < len(ALL_MODELS)))
        # pairwise flip rate at thr=0.5
        thr = 0.5
        pairs = list(itertools.combinations(ALL_MODELS, 2))
        flips = sum(1 for a, b in pairs if (agg[a] >= thr) != (agg[b] >= thr))
        # persona-level Fleiss kappa on the "high risk" flag across the 6 backends
        pmat = []
        for p in PERSONAS:
            row = [int(df[(df.domain == dom) & (df.model == m) & (df.persona == p)].adopt.mean() >= thr)
                   for m in ALL_MODELS]
            pmat.append(row)
        kappa = fleiss_kappa(np.array(pmat))
        inst[dom] = dict(aggregate_adoption={m: round(agg[m], 3) for m in ALL_MODELS},
                         by_threshold=thr_results, pairwise_flip_rate_at_0p5=flips / len(pairs),
                         n_flips_at_0p5=flips, n_pairs=len(pairs),
                         persona_flag_fleiss_kappa_at_0p5=kappa)
    out['cross_backend_instability'] = inst

    # ---------- (10) backend-aware aggregation ----------
    agg_proto = {}
    for dom in ['beer', 'amzbook']:
        vals = np.array([df[(df.domain == dom) & (df.model == m)].adopt.mean() for m in ALL_MODELS])
        agg_proto[dom] = dict(
            conservative_max=float(vals.max()), median_ensemble=float(np.median(vals)),
            min_model=float(vals.min()), range=float(vals.max() - vals.min()),
            disagreement_abstain=bool((vals.max() - vals.min()) > 0.2),
            note="range>0.2 => backend-sensitive => abstain/require human eval")
    out['aggregation_protocols'] = agg_proto

    # ---------- RQ2 variance decomposition (existing sources) ----------
    # Crossed random-effects on adopt (linear probability model for interpretable variance shares):
    # adopt ~ 1 + (1|model) + (1|persona) + (1|item). Generation- and prompt-paraphrase variance
    # cannot be estimated without repeated generations / paraphrases (new runs).
    vd = {}
    d2 = df.copy()
    d2['grp'] = 1
    try:
        vcf = {'model': '0 + C(model)', 'persona': '0 + C(persona)', 'item': '0 + C(item)'}
        res = smf.mixedlm('adopt ~ 1', d2, groups='grp', vc_formula=vcf).fit()
        vcnames = list(vcf.keys())
        vcvars = list(res.vcomp)
        resid = float(res.scale)
        vc = {n: float(v) for n, v in zip(vcnames, vcvars)}
        vc['residual'] = resid
        tot = sum(vc.values())
        vd['lpm_crossed_variance'] = vc
        vd['lpm_variance_share'] = {k: round(v / tot, 3) for k, v in vc.items()}
    except Exception as e:
        vd['lpm_crossed'] = f'NA ({e})'
    for fac in ['model', 'persona', 'item', 'domain']:
        grp = df.groupby(fac).adopt.mean()
        vd[f'between_{fac}_sd'] = float(grp.std())
    out['variance_decomposition'] = vd

    json.dump(out, open('results/measurement_audit.json', 'w'), indent=2, default=str)
    printout(out)


def printout(out):
    print('=' * 80)
    print('(8) BEHAVIOR TAXONOMY on dark condition (challenge/refusal of the deceptive premise)')
    print('  %-8s %-18s adopt  adopt|nonChal  challengeRate  retainOwn  toRight' % ('domain', 'model'))
    for r in out['behavior_taxonomy']:
        print('  %-8s %-18s %.2f    %.2f          %.2f           %.2f       %.2f'
              % (r['domain'], r['model'], r['adopt'], r['adopt_nonchallenge'], r['challenge_rate'],
                 r['retain_own'], r['switch_to_right']))
    print('=' * 80)
    print('(9) CROSS-BACKEND DECISION INSTABILITY (same dark interface, aggregate risk by backend)')
    for dom, v in out['cross_backend_instability'].items():
        print('  [%s] aggregate adoption:' % dom, v['aggregate_adoption'])
        for thr, tr in v['by_threshold'].items():
            print('       thr=%s: %d/6 backends flag; UNSTABLE=%s' % (thr, tr['n_flag'], tr['unstable']))
        print('       pairwise flip rate @0.5 = %.2f (%d/%d pairs); persona-flag Fleiss kappa=%.3f'
              % (v['pairwise_flip_rate_at_0p5'], v['n_flips_at_0p5'], v['n_pairs'],
                 v['persona_flag_fleiss_kappa_at_0p5']))
    print('=' * 80)
    print('(10) AGGREGATION PROTOCOLS')
    for dom, v in out['aggregation_protocols'].items():
        print('  [%s] max=%.2f median=%.2f min=%.2f range=%.2f -> abstain=%s'
              % (dom, v['conservative_max'], v['median_ensemble'], v['min_model'], v['range'],
                 v['disagreement_abstain']))
    print('=' * 80)
    print('RQ2 VARIANCE DECOMPOSITION (existing sources)')
    vd = out['variance_decomposition']
    if 'lpm_variance_share' in vd:
        print('  LPM crossed-RE variance share:', vd['lpm_variance_share'])
    for k in ['between_model_sd', 'between_persona_sd', 'between_item_sd', 'between_domain_sd']:
        print('  %s = %.3f' % (k, vd[k]))
    print('  -> results/measurement_audit.json')


if __name__ == '__main__':
    main()

