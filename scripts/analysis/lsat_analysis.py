"""LSAT task-structure generalization analysis (D5.58).

Preregistered in docs/plans/2026-07-24-C-lsat-generalization-prereg.md. Frozen metric defs mirror the
binary axis-2 arm. Verdict against frozen R1-R3 / N1-N3 criteria.

adopt (dark) = int(final == ai_advice)         # ai_advice explicit in trace, guaranteed wrong
s1_correct   = int(system1 == ground_truth)
capability   = mean(s1_correct) per backend     # unaided System-1 accuracy
flip         = mean(adopt | s1_correct==1) dark  # abandon a correct answer to follow wrong AI

Instrument-health parse rate is recovered NON-INVASIVELY from the provider cache (the LSAT records do not
store raw text), by replaying _parse_letter over cached LSAT responses. <50% parseable => excluded.
"""
import glob
import json
import os
import re

import numpy as np
from scipy.stats import spearmanr

LETTERS = ['A', 'B', 'C', 'D']


def _parse_letter(text, n_choices):
    """Identical to lsat_panel._parse_letter (inlined to avoid importing the harness)."""
    if not text:
        return None
    m = re.search(r'"choice"\s*:\s*"?([ABCD])"?', text)
    if m:
        L = m.group(1)
    else:
        m2 = re.search(r'\b([ABCD])\b', text)
        L = m2.group(1) if m2 else None
    if L is None:
        return None
    idx = LETTERS.index(L)
    return idx if idx < n_choices else None


DARK = 'Wrong-AI-GT (dark)'
CONF = 'Conf.'
PERSONAS = ['p1-novice-skeptical', 'p2-expert-trusting', 'p3-moderate-balanced',
            'p4-skilled-skeptical', 'p5-novice-trusting', 'p6-expert-moderate']
TARGET = 'p5-novice-trusting'
LSAT_MODELS = ['gpt-4o-mini', 'gpt-4.1', 'gpt-4o', 'gpt-5.5', 'claude-sonnet-4.5', 'gemini-2.5-pro']

# Binary reference (persona ordering, R3): same 6-backend dark data as capability_vulnerability.py
BIN_FILES = {('beer', 'capladder'): 'results/axis2_powered_capladder.json',
             ('beer', 'crossvendor'): 'results/axis2_powered_crossvendor.json',
             ('amzbook', 'capladder'): 'results/axis2_powered_capladder_amzbook.json',
             ('amzbook', 'crossvendor'): 'results/axis2_powered_crossvendor_amzbook.json'}


def load_lsat_rows(path='results/lsat_axis2.json'):
    d = json.load(open(path))
    rows = []
    for r in d['responses']:
        rows.append(dict(model=r['model'], persona=r['persona_id'], cond=r['ui_condition'],
                         s1=int(r['system1_decision']), final=int(r['final_decision']),
                         truth=int(r['trace']['ground_truth']), ai_advice=int(r['trace']['ai_advice']),
                         item=str(r['trace'].get('task_id')),
                         adopt=int(int(r['final_decision']) == int(r['trace']['ai_advice'])),
                         s1_correct=int(int(r['system1_decision']) == int(r['trace']['ground_truth']))))
    return rows


def binary_persona_dark_adopt():
    """Pooled per-persona dark adopt across the 6 binary backends (adopt = final == 1-truth)."""
    by_p = {p: [] for p in PERSONAS}
    for (dom, arm), path in BIN_FILES.items():
        if not os.path.exists(path):
            continue
        d = json.load(open(path))
        for r in d['responses']:
            if r['ui_condition'] != DARK:
                continue
            m = r['model']
            if m == 'gpt-5.5' and arm != 'capladder':
                continue
            truth = int(r['trace']['ground_truth'])
            adopt = int(int(r['final_decision']) == (1 - truth))
            p = r['persona_id']
            if p in by_p:
                by_p[p].append(adopt)
    return {p: float(np.mean(v)) if v else float('nan') for p, v in by_p.items()}


def parse_rate_from_cache(cache_dir='data/cache/panel'):
    """Non-invasive instrument health: replay _parse_letter over cached LSAT responses per model.

    Fast path: read raw text and substring-filter to the LSAT prompt signature BEFORE json.load,
    so we only parse the ~LSAT subset out of tens of thousands of cache files.
    """
    sig = 'Respond in JSON: {"choice"'          # parsed-content signature (unescaped)
    fast = 'Respond in JSON:'                    # plain-text prefilter (survives JSON escaping on disk)
    tally = {m: [0, 0] for m in LSAT_MODELS}  # model -> [parsed, total]
    for fp in glob.glob(os.path.join(cache_dir, '*.json')):
        try:
            with open(fp, encoding='utf-8', errors='ignore') as fh:
                text = fh.read()
        except Exception:
            continue
        if fast not in text:
            continue  # not an LSAT prompt (fast reject on unescaped plain text)
        try:
            c = json.loads(text)
        except Exception:
            continue
        m = c.get('model')
        if m not in tally:
            continue
        msgs = c.get('messages', [])
        if not msgs or sig not in msgs[-1].get('content', ''):
            continue  # correct check on PARSED message content
        resp = c.get('response', '')
        tally[m][1] += 1
        if _parse_letter(resp, 4) is not None:
            tally[m][0] += 1
    return {m: dict(parsed=t[0], total=t[1], rate=(t[0] / t[1] if t[1] else float('nan')))
            for m, t in tally.items()}


def per_backend(rows, model):
    sub = [r for r in rows if r['model'] == model]
    dark = [r for r in sub if r['cond'] == DARK]
    conf = [r for r in sub if r['cond'] == CONF]
    # capability: one s1 per (persona,item); dark subset has exactly one each
    cap = float(np.mean([r['s1_correct'] for r in dark])) if dark else float('nan')
    agg = float(np.mean([r['adopt'] for r in dark])) if dark else float('nan')
    conf_adopt = float(np.mean([r['adopt'] for r in conf])) if conf else float('nan')
    corr = [r for r in dark if r['s1_correct'] == 1]
    flip = float(np.mean([r['adopt'] for r in corr])) if corr else float('nan')
    p5 = [r for r in dark if r['persona'] == TARGET]
    p5_adopt = float(np.mean([r['adopt'] for r in p5])) if p5 else float('nan')
    per_p = {p: (float(np.mean([r['adopt'] for r in dark if r['persona'] == p]))
                 if any(r['persona'] == p for r in dark) else float('nan')) for p in PERSONAS}
    return dict(capability_s1acc=cap, agg_adopt=agg, conf_adopt=conf_adopt, flip=flip,
                p5_adopt=p5_adopt, n_s1_correct=len(corr), per_persona=per_p, n_dark=len(dark))


def main():
    rows = load_lsat_rows()
    present = [m for m in LSAT_MODELS if any(r['model'] == m for r in rows)]
    parse = parse_rate_from_cache()
    excluded = {m: parse[m] for m in present if parse[m]['total'] and parse[m]['rate'] < 0.5}
    kept = [m for m in present if m not in excluded]

    pb = {m: per_backend(rows, m) for m in kept}
    cap = np.array([pb[m]['capability_s1acc'] for m in kept])
    adopt = np.array([pb[m]['agg_adopt'] for m in kept])
    flip = np.array([pb[m]['flip'] for m in kept])

    def sp(x, y):
        mask = ~(np.isnan(x) | np.isnan(y))
        if mask.sum() < 3:
            return dict(rho=float('nan'), p=float('nan'), n=int(mask.sum()))
        rho, p = spearmanr(x[mask], y[mask])
        return dict(rho=round(float(rho), 3), p=round(float(p), 4), n=int(mask.sum()))

    corr_cap_adopt = sp(cap, adopt)
    corr_cap_flip = sp(cap, flip)
    adopt_range = float(np.nanmax(adopt) - np.nanmin(adopt)) if len(adopt) else float('nan')

    # persona ordering concordance (R3)
    lsat_pp = {p: float(np.nanmean([pb[m]['per_persona'][p] for m in kept])) for p in PERSONAS}
    bin_pp = binary_persona_dark_adopt()
    lv = np.array([lsat_pp[p] for p in PERSONAS])
    bv = np.array([bin_pp[p] for p in PERSONAS])
    corr_persona = sp(lv, bv)

    # coverage: single strongest-capability backend vs full panel (# personas with dark adopt >= 0.5)
    strong = max(kept, key=lambda m: pb[m]['capability_s1acc']) if kept else None
    def n_over(model_set):
        return int(sum(any(pb[m]['per_persona'][p] >= 0.5 for m in model_set) for p in PERSONAS))
    coverage = dict(single_frontier=strong,
                    single_frontier_personas_over_0p5=(n_over([strong]) if strong else None),
                    full_panel_personas_over_0p5=n_over(kept))

    # ---- frozen verdict ----
    R1 = (not np.isnan(adopt_range)) and adopt_range >= 0.25
    R2 = (corr_cap_adopt['rho'] < 0) and (corr_cap_flip['rho'] < 0) \
        if not (np.isnan(corr_cap_adopt['rho']) or np.isnan(corr_cap_flip['rho'])) else False
    R3 = (not np.isnan(corr_persona['rho'])) and corr_persona['rho'] > 0
    N1 = all((not np.isnan(pb[m]['agg_adopt'])) and pb[m]['agg_adopt'] < 0.15 for m in kept) if kept else False
    N2 = (not np.isnan(corr_cap_adopt['rho'])) and corr_cap_adopt['rho'] > 0
    N3 = (not np.isnan(corr_persona['rho'])) and corr_persona['rho'] <= 0
    if R1 and R2 and R3:
        verdict = 'REPLICATES'
    elif N1 or N2 or N3:
        verdict = 'NEGATIVE'
    else:
        verdict = 'PARTIAL'

    out = dict(models_present=present, excluded=excluded, kept=kept, parse_rate=parse,
               per_backend=pb, adopt_range=round(adopt_range, 3),
               corr_cap_adopt=corr_cap_adopt, corr_cap_flip=corr_cap_flip,
               lsat_persona_adopt=lsat_pp, binary_persona_adopt=bin_pp, corr_persona=corr_persona,
               coverage=coverage,
               criteria=dict(R1_noninvariance=bool(R1), R2_capvuln_sign=bool(R2),
                             R3_persona_concordance=bool(R3), N1_uniform_low=bool(N1),
                             N2_sign_flip=bool(N2), N3_persona_reversed=bool(N3)),
               verdict=verdict)
    json.dump(out, open('results/lsat_analysis.json', 'w'), indent=2)
    _print(out)


def _print(out):
    print('=' * 80)
    print('LSAT task-structure generalization  (kept backends: %s)' % ', '.join(out['kept']))
    if out['excluded']:
        print('EXCLUDED (parse<50%%): %s' % {m: round(v['rate'], 2) for m, v in out['excluded'].items()})
    print('  %-18s cap(S1) darkAdopt flip  p5Adopt confAdopt' % 'backend')
    for m in out['kept']:
        d = out['per_backend'][m]
        print('  %-18s %.3f   %.3f     %.3f %.3f   %.3f'
              % (m, d['capability_s1acc'], d['agg_adopt'], d['flip'], d['p5_adopt'], d['conf_adopt']))
    print('  dark-adopt RANGE across backends = %.3f  (R1 >=0.25: %s)'
          % (out['adopt_range'], out['criteria']['R1_noninvariance']))
    print('  cap vs dark-adopt  rho=%s p=%s' % (out['corr_cap_adopt']['rho'], out['corr_cap_adopt']['p']))
    print('  cap vs flip        rho=%s p=%s' % (out['corr_cap_flip']['rho'], out['corr_cap_flip']['p']))
    print('  persona ordering LSAT vs binary rho=%s p=%s (R3 >0: %s)'
          % (out['corr_persona']['rho'], out['corr_persona']['p'], out['criteria']['R3_persona_concordance']))
    print('  per-persona dark adopt (LSAT): %s' % {p: round(v, 2) for p, v in out['lsat_persona_adopt'].items()})
    print('  per-persona dark adopt (binary): %s' % {p: round(v, 2) for p, v in out['binary_persona_adopt'].items()})
    print('  coverage: single frontier %s -> %s/6 personas>=.5 ; full panel -> %s/6'
          % (out['coverage']['single_frontier'], out['coverage']['single_frontier_personas_over_0p5'],
             out['coverage']['full_panel_personas_over_0p5']))
    print('  >>> VERDICT: %s' % out['verdict'])
    print('-> results/lsat_analysis.json')


if __name__ == '__main__':
    main()
