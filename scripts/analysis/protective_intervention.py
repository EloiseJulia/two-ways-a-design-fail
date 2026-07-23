"""D5.44 Experiment A analysis: protective-intervention audit.

Can a synthetic panel detect that a protective interface REDUCES wrong-AI over-reliance, and is that
verdict backend-dependent? Conditions (all guaranteed-wrong label, beer, 6 backends x 6 personas x 20
items, gen 42):
  plain   = neutral wrong-AI baseline           (results/protective_axis2.json)
  forcing = + cognitive forcing (Bucinca 2021)  (results/protective_axis2.json)
  verify  = + verification/uncertainty display   (results/protective_axis2.json)
  dark    = coercion extreme                     (pulled from capladder/crossvendor, matched)

Frozen analyses (docs/plans/2026-07-23-A-protective-intervention-prereg.md):
 1. Protective main effect: plain vs forcing vs verify adoption (pooled).
 2. Backend x condition interaction via plain-GLM LRT (NOT small-cluster GEE, per D5.39).
 3. Protective benefit (plain - protective) per backend vs baseline over-reliance and capability;
    H3 frontier floor (~0 benefit).
 4. p5 (at-risk persona) + AI-induced-flip metric focus.
"""
import json
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import spearmanr

ALL_MODELS = ['gpt-4o-mini', 'gpt-4.1', 'gpt-4o', 'gpt-5.5', 'claude-sonnet-4.5', 'gemini-2.5-pro']
CONDS = ['dark', 'plain', 'forcing', 'verify']
PROTECT = ['forcing', 'verify']
TARGET = 'p5-novice-trusting'
COND_MAP = {'Wrong-AI-GT (plain)': 'plain', 'Wrong-AI-GT (forcing)': 'forcing',
            'Wrong-AI-GT (verify)': 'verify', 'Wrong-AI-GT (dark)': 'dark'}
DARK_FILES = {'capladder': 'results/axis2_powered_capladder.json',
              'crossvendor': 'results/axis2_powered_crossvendor.json'}


def _rows_from(responses, arm=None):
    rows = []
    for r in responses:
        cond = COND_MAP.get(r['ui_condition'])
        if cond is None:
            continue
        m = r['model']
        if m not in ALL_MODELS:
            continue
        if cond == 'dark' and m == 'gpt-5.5' and arm != 'capladder':
            continue  # de-dup gpt-5.5 dark (byte-identical), keep capladder
        truth = int(r['trace']['ground_truth'])
        s1 = int(r['system1_decision']); final = int(r['final_decision'])
        rows.append(dict(model=m, persona=r['persona_id'], item=str(r['task_id']), cond=cond,
                         adopt=int(final == 1 - truth), s1_correct=int(s1 == truth)))
    return rows


def load():
    rows = _rows_from(json.load(open('results/protective_axis2.json'))['responses'])
    for arm, path in DARK_FILES.items():
        rows += _rows_from(json.load(open(path))['responses'], arm=arm)
    df = pd.DataFrame(rows)
    return df[df.persona.notna()].copy()


def adopt(sub):
    return float(sub.adopt.mean()) if len(sub) else float('nan')


def flip(sub):
    s = sub[sub.s1_correct == 1]
    return float(s.adopt.mean()) if len(s) else float('nan')


def main():
    df = load()
    out = {'per_backend_condition': {}, 'per_backend_condition_flip': {}}

    # capability proxy (S1 accuracy) per backend, pooled over conditions
    cap = {m: float(df[df.model == m].s1_correct.mean()) for m in ALL_MODELS}
    out['capability_s1acc'] = {m: round(cap[m], 3) for m in ALL_MODELS}

    # ---- per backend x condition adoption + flip ----
    for m in ALL_MODELS:
        out['per_backend_condition'][m] = {c: round(adopt(df[(df.model == m) & (df.cond == c)]), 3)
                                           for c in CONDS}
        out['per_backend_condition_flip'][m] = {c: round(flip(df[(df.model == m) & (df.cond == c)]), 3)
                                                 for c in CONDS}

    # ---- (1) protective main effect (pooled over backends/personas/items) ----
    pooled = {c: round(adopt(df[df.cond == c]), 3) for c in CONDS}
    out['pooled_adoption'] = pooled
    out['pooled_protective_benefit'] = {c: round(pooled['plain'] - pooled[c], 3) for c in PROTECT}

    # ---- (2) backend x condition interaction via plain-GLM LRT (plain/forcing/verify) ----
    import statsmodels.api as sm
    from scipy.stats import chi2
    d3 = df[df.cond.isin(['plain'] + PROTECT)].copy()
    B = sm.families.Binomial()
    m_backend = smf.glm('adopt ~ C(model)', data=d3, family=B).fit()          # backend only
    base = smf.glm('adopt ~ C(cond) + C(model)', data=d3, family=B).fit()      # + condition main effect
    inter = smf.glm('adopt ~ C(cond) * C(model)', data=d3, family=B).fit()     # + interaction
    # protective main effect (does condition matter, pooled over backends)
    lr_main = float(2 * (base.llf - m_backend.llf)); df_main = int(base.df_model - m_backend.df_model)
    out['condition_main_LRT'] = dict(chi2=round(lr_main, 3), df=df_main,
                                     p=round(float(chi2.sf(lr_main, df_main)), 5),
                                     note='plain vs forcing vs verify pooled over backends')
    # backend x condition interaction
    lr_stat = float(2 * (inter.llf - base.llf)); df_diff = int(inter.df_model - base.df_model)
    out['interaction_LRT'] = dict(chi2=round(lr_stat, 3), df=df_diff,
                                  p=round(float(chi2.sf(lr_stat, df_diff)), 4),
                                  note='condition x backend interaction (does protective benefit vary by backend)')
    # p5-only protective main effect
    d3p5 = d3[d3.persona == TARGET]
    b0 = smf.glm('adopt ~ C(model)', data=d3p5, family=B).fit()
    b1 = smf.glm('adopt ~ C(cond) + C(model)', data=d3p5, family=B).fit()
    lr_p5 = float(2 * (b1.llf - b0.llf)); df_p5 = int(b1.df_model - b0.df_model)
    out['p5_condition_main_LRT'] = dict(chi2=round(lr_p5, 3), df=df_p5,
                                        p=round(float(chi2.sf(lr_p5, df_p5)), 6))

    # ---- (3) protective benefit per backend vs baseline over-reliance + capability ----
    benefit = {}
    for m in ALL_MODELS:
        pc = out['per_backend_condition'][m]
        b_forcing = pc['plain'] - pc['forcing']
        b_verify = pc['plain'] - pc['verify']
        benefit[m] = dict(plain=pc['plain'], dark=pc['dark'],
                          benefit_forcing=round(b_forcing, 3), benefit_verify=round(b_verify, 3),
                          benefit_mean=round((b_forcing + b_verify) / 2, 3))
    out['protective_benefit_by_backend'] = benefit
    capv = np.array([cap[m] for m in ALL_MODELS])
    plainv = np.array([benefit[m]['plain'] for m in ALL_MODELS])
    benv = np.array([benefit[m]['benefit_mean'] for m in ALL_MODELS])
    r_bp, p_bp = spearmanr(plainv, benv)   # more baseline over-reliance -> more measured benefit?
    r_bc, p_bc = spearmanr(capv, benv)     # capability vs measured benefit
    out['benefit_vs_baseline_spearman'] = dict(rho=round(float(r_bp), 3), p=round(float(p_bp), 4))
    out['benefit_vs_capability_spearman'] = dict(rho=round(float(r_bc), 3), p=round(float(p_bc), 4))
    out['frontier_backend'] = sorted(ALL_MODELS, key=lambda m: cap[m], reverse=True)[0]
    out['frontier_benefit'] = benefit[out['frontier_backend']]['benefit_mean']

    # ---- (4) p5 focus (adoption + flip) ----
    p5 = {}
    for m in ALL_MODELS:
        sub = df[(df.model == m) & (df.persona == TARGET)]
        p5[m] = {c: round(adopt(sub[sub.cond == c]), 3) for c in CONDS}
    out['p5_by_backend_condition'] = p5
    out['p5_pooled'] = {c: round(adopt(df[(df.cond == c) & (df.persona == TARGET)]), 3) for c in CONDS}

    json.dump(out, open('results/protective_intervention.json', 'w'), indent=2)
    printout(out)


def printout(out):
    print('=' * 84)
    print('(1) POOLED adoption by condition:', out['pooled_adoption'])
    print('    protective benefit (plain - protective):', out['pooled_protective_benefit'])
    print('=' * 84)
    print('per-backend adoption  [cap(S1)]  dark  plain  forcing  verify | benefit(mean)')
    for m in ALL_MODELS:
        pc = out['per_backend_condition'][m]; b = out['protective_benefit_by_backend'][m]
        print('  %-18s %.3f     %.2f  %.2f   %.2f     %.2f  | %+.3f'
              % (m, out['capability_s1acc'][m], pc['dark'], pc['plain'], pc['forcing'], pc['verify'],
                 b['benefit_mean']))
    print('=' * 84)
    lr = out['interaction_LRT']
    cm = out['condition_main_LRT']; p5m = out['p5_condition_main_LRT']
    print('(2) condition MAIN effect LRT (pooled): chi2=%.2f df=%d p=%.5f' % (cm['chi2'], cm['df'], cm['p']))
    print('    backend x condition INTERACTION LRT: chi2=%.2f df=%d p=%.4f' % (lr['chi2'], lr['df'], lr['p']))
    print('    p5 condition main effect LRT:        chi2=%.2f df=%d p=%.6f' % (p5m['chi2'], p5m['df'], p5m['p']))
    print('(3) protective benefit vs baseline plain-adoption: Spearman %.2f (p=%.3f)'
          % (out['benefit_vs_baseline_spearman']['rho'], out['benefit_vs_baseline_spearman']['p']))
    print('    protective benefit vs capability:            Spearman %.2f (p=%.3f)'
          % (out['benefit_vs_capability_spearman']['rho'], out['benefit_vs_capability_spearman']['p']))
    print('    frontier (%s) benefit_mean = %+.3f' % (out['frontier_backend'], out['frontier_benefit']))
    print('=' * 84)
    print('(4) p5 pooled by condition:', out['p5_pooled'])
    print('-> results/protective_intervention.json')


if __name__ == '__main__':
    main()
