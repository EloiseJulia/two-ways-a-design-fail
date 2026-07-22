"""Persona-deference ablation analysis (fills the sec persona manipulation-check [ablation results pending]).

Question: is the trusting-novice persona (p5) the top wrong-AI adopter because of the EXPLICIT AI-deference/
verification policy written into its prompt, or does the ranking survive when that policy is removed?

Compares, on the dark condition (beer, seed 2024, gen 42, models gpt-4.1 & gpt-5.5), matched personas:
  POLICY arm     = existing axis2_powered_capladder.json (p1..p6 with explicit decision/deference policy)
  BACKGROUND arm = results/persona_ablation.json (p1-bg..p6-bg: same traits, neutral background facts,
                   NO explicit AI-deference/verification policy; prompt_style=background_only)
Reports per-persona dark adoption in each arm, p5's rank, and the Spearman agreement of the persona
ordering between arms (per model). If p5 stays top and the ordering correlates, the effect is carried by
the persona's background traits, not only by the explicit policy sentence.
"""
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

DARK = 'Wrong-AI-GT (dark)'
MODELS = ['gpt-4.1', 'gpt-5.5']
# policy persona (capladder) -> its number; background persona has the same number with -bg
POLICY = ['p1-novice-skeptical', 'p2-expert-trusting', 'p3-moderate-balanced',
          'p4-skilled-skeptical', 'p5-novice-trusting', 'p6-expert-moderate']
BG = ['p1-bg', 'p2-bg', 'p3-bg', 'p4-bg', 'p5-bg', 'p6-bg']
NUM = {p: i + 1 for i, p in enumerate(POLICY)}
NUM.update({p: i + 1 for i, p in enumerate(BG)})
TARGET_NUM = 5  # p5 = trusting-novice


def load(path, personas):
    d = json.load(open(path))
    rows = []
    for r in d['responses']:
        if r['ui_condition'] != DARK or r['model'] not in MODELS or r['persona_id'] not in personas:
            continue
        truth = int(r['trace']['ground_truth'])
        rows.append(dict(model=r['model'], pnum=NUM[r['persona_id']], item=str(r['task_id']),
                         adopt=int(int(r['final_decision']) == 1 - truth),
                         s1_correct=int(int(r['system1_decision']) == truth)))
    return pd.DataFrame(rows)


def per_persona(df):
    a = df.groupby('pnum').adopt.mean()
    fl = df[df.s1_correct == 1].groupby('pnum').adopt.mean()  # AI-induced flip
    return a, fl


def main():
    policy = load('results/axis2_powered_capladder.json', POLICY)
    bg = load('results/persona_ablation.json', BG)
    out = {'by_model': {}, 'items_note': {}}

    for m in MODELS:
        pa, pf = per_persona(policy[policy.model == m])
        ba, bf = per_persona(bg[bg.model == m])
        nums = sorted(set(pa.index) & set(ba.index))
        rho, p = spearmanr([pa[n] for n in nums], [ba[n] for n in nums])
        out['by_model'][m] = dict(
            policy_adopt={int(n): round(float(pa[n]), 3) for n in nums},
            background_adopt={int(n): round(float(ba[n]), 3) for n in nums},
            policy_flip={int(n): round(float(pf.get(n, np.nan)), 3) for n in nums},
            background_flip={int(n): round(float(bf.get(n, np.nan)), 3) for n in nums},
            p5_policy_adopt=round(float(pa[TARGET_NUM]), 3),
            p5_background_adopt=round(float(ba[TARGET_NUM]), 3),
            p5_rank_policy=int((pa.rank(ascending=False)[TARGET_NUM])),
            p5_rank_background=int((ba.rank(ascending=False)[TARGET_NUM])),
            p5_is_top_policy=bool(pa.idxmax() == TARGET_NUM),
            p5_is_top_background=bool(ba.idxmax() == TARGET_NUM),
            ordering_spearman=round(float(rho), 3), ordering_spearman_p=round(float(p), 4))
        out['items_note'][m] = dict(policy_items=int(policy[policy.model == m].item.nunique()),
                                    background_items=int(bg[bg.model == m].item.nunique()),
                                    shared_items=int(len(set(policy[policy.model == m].item) &
                                                         set(bg[bg.model == m].item))))

    json.dump(out, open('results/persona_ablation_analysis.json', 'w'), indent=2)
    for m in MODELS:
        o = out['by_model'][m]
        print('=' * 70)
        print('%s  (shared items: %d)' % (m, out['items_note'][m]['shared_items']))
        print('  persona#:      ', ' '.join('%5d' % n for n in sorted(o['policy_adopt'])))
        print('  policy adopt:  ', ' '.join('%5.2f' % o['policy_adopt'][n] for n in sorted(o['policy_adopt'])))
        print('  bg     adopt:  ', ' '.join('%5.2f' % o['background_adopt'][n] for n in sorted(o['background_adopt'])))
        print('  p5 adopt: policy %.2f (rank %d, top=%s) | background %.2f (rank %d, top=%s)'
              % (o['p5_policy_adopt'], o['p5_rank_policy'], o['p5_is_top_policy'],
                 o['p5_background_adopt'], o['p5_rank_background'], o['p5_is_top_background']))
        print('  ordering Spearman(policy, background) = %.2f (p=%.3f)'
              % (o['ordering_spearman'], o['ordering_spearman_p']))
    print('-> results/persona_ablation_analysis.json')


if __name__ == '__main__':
    main()
