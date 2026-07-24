"""Q1 persona-induction comparison: does the trusting-novice (p5) over-reliance survive NON-instructional
induction? Compares p5 dark adoption across four ways of inducing the same persona:

  policy        = explicit AI-deference decision policy   (results/axis2_powered_capladder.json, p1..p6)
  background    = neutral background facts, no policy      (results/persona_ablation.json, p1-bg..p6-bg)
  backstory     = naturalistic first-person life context  (results/persona_induction_AB.json, p*-bs)
  demonstration = few-shot past-decision examples         (results/persona_induction_AB.json, p*-dm)

All matched: dark condition, beer, seed 2024, gen 42, models {gpt-4.1, gpt-5.5}. If p5 stays the top (or
near-top) adopter WITHOUT the explicit deference instruction, the effect is not merely a prompt-compliance
artifact of that instruction -> answers the "persona is circular" critique.
"""
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

DARK = 'Wrong-AI-GT (dark)'
MODELS = ['gpt-4.1', 'gpt-5.5']
NUMBER = {  # persona_id -> persona number 1..6 (p5 = trusting-novice)
    **{f'p{i}-{sfx}': i for i in range(1, 7) for sfx in ('bs', 'dm', 'bg')},
    'p1-novice-skeptical': 1, 'p2-expert-trusting': 2, 'p3-moderate-balanced': 3,
    'p4-skilled-skeptical': 4, 'p5-novice-trusting': 5, 'p6-expert-moderate': 6}
TARGET = 5
ARMS = {
    'policy': ('results/axis2_powered_capladder.json',
               {'p1-novice-skeptical', 'p2-expert-trusting', 'p3-moderate-balanced',
                'p4-skilled-skeptical', 'p5-novice-trusting', 'p6-expert-moderate'}),
    'background': ('results/persona_ablation.json', {f'p{i}-bg' for i in range(1, 7)}),
    'backstory': ('results/persona_induction_AB.json', {f'p{i}-bs' for i in range(1, 7)}),
    'demonstration': ('results/persona_induction_AB.json', {f'p{i}-dm' for i in range(1, 7)}),
}


def load_arm(path, ids):
    d = json.load(open(path))
    rows = []
    for r in d['responses']:
        if r['ui_condition'] != DARK or r['model'] not in MODELS or r['persona_id'] not in ids:
            continue
        truth = int(r['trace']['ground_truth'])
        rows.append(dict(model=r['model'], pnum=NUMBER[r['persona_id']], item=str(r['task_id']),
                         adopt=int(int(r['final_decision']) == 1 - truth),
                         s1_correct=int(int(r['system1_decision']) == truth)))
    return pd.DataFrame(rows)


def main():
    out = {'by_model': {}, 'pooled': {}}
    arms = {name: load_arm(p, ids) for name, (p, ids) in ARMS.items()}

    for m in MODELS:
        md = {}
        for name, df in arms.items():
            sub = df[df.model == m]
            per = sub.groupby('pnum').adopt.mean()
            p5 = float(per.get(TARGET, np.nan))
            rank = int(per.rank(ascending=False).get(TARGET, -1)) if len(per) else -1
            md[name] = dict(p5_adopt=round(p5, 3),
                            p5_rank=rank, is_top=bool(per.idxmax() == TARGET) if len(per) else None,
                            per_persona={int(k): round(float(v), 3) for k, v in per.items()})
        out['by_model'][m] = md

    # pooled across models
    for name, df in arms.items():
        per = df.groupby('pnum').adopt.mean()
        p5 = float(per.get(TARGET, np.nan))
        out['pooled'][name] = dict(p5_adopt=round(p5, 3),
                                   p5_rank=int(per.rank(ascending=False).get(TARGET, -1)),
                                   is_top=bool(per.idxmax() == TARGET),
                                   per_persona={int(k): round(float(v), 3) for k, v in per.items()})

    # ordering agreement (Spearman) of each non-policy arm vs policy, pooled
    pol = out['pooled']['policy']['per_persona']
    out['ordering_vs_policy'] = {}
    for name in ['background', 'backstory', 'demonstration']:
        pp = out['pooled'][name]['per_persona']
        common = sorted(set(pol) & set(pp))
        rho, p = spearmanr([pol[k] for k in common], [pp[k] for k in common])
        out['ordering_vs_policy'][name] = dict(spearman=round(float(rho), 3), p=round(float(p), 4), n=len(common))

    json.dump(out, open('results/persona_induction_analysis.json', 'w'), indent=2)
    printout(out)


def printout(out):
    print('=' * 76)
    print('p5 (trusting-novice) DARK adoption across induction styles')
    print('  %-14s %-18s %-18s' % ('arm', 'pooled p5 (rank,top)', 'gpt-4.1 / gpt-5.5 p5'))
    for name in ['policy', 'background', 'backstory', 'demonstration']:
        pl = out['pooled'][name]
        m1 = out['by_model']['gpt-4.1'][name]; m2 = out['by_model']['gpt-5.5'][name]
        print('  %-14s %.2f (rank %d, top=%s)   %.2f / %.2f'
              % (name, pl['p5_adopt'], pl['p5_rank'], pl['is_top'], m1['p5_adopt'], m2['p5_adopt']))
    print('  --- ordering agreement vs policy (Spearman, pooled) ---')
    for name, v in out['ordering_vs_policy'].items():
        print('   %-14s rho=%.2f (p=%.3f, n=%d)' % (name, v['spearman'], v['p'], v['n']))
    print('-> results/persona_induction_analysis.json')


if __name__ == '__main__':
    main()
