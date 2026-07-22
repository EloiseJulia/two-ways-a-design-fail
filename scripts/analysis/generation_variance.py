"""Generation-stochasticity variance (fills the sec:variance [pending] placeholder).

On the multi-generation run (results/multigen_axis2.json: 3 models x 2 conditions x 6 personas x 20 items
x 5 generation seeds), estimate how much generation randomness moves the synthetic risk estimate, using
the SAME linear-probability crossed random-effects decomposition as measurement_audit.py but with an added
(1|generation) component:  adopt ~ 1 + (1|model)+(1|persona)+(1|item)+(1|generation).

Reports (dark condition):
  1) variance shares including generation (expect generation to be the SMALLEST source);
  2) aggregate stability: per-model dark over-reliance across the 5 generation seeds (mean, SD, range);
  3) cell-level generation noise: SD across generations of (model x persona x item) adoption, averaged.
"""
import json
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

DARK = 'Wrong-AI-GT (dark)'


def load():
    d = json.load(open('results/multigen_axis2.json'))
    rows = []
    for r in d['responses']:
        truth = int(r['trace']['ground_truth'])
        s1 = int(r['system1_decision']); final = int(r['final_decision'])
        rows.append(dict(model=r['model'], persona=r['persona_id'], item=str(r['task_id']),
                         cond=r['ui_condition'], generation=str(r['gen_seed']),
                         adopt=int(final == 1 - truth), s1_correct=int(s1 == truth),
                         final_correct=int(final == truth)))
    return pd.DataFrame(rows)


def main():
    df = load()
    dark = df[df.cond == DARK].copy()
    out = {}

    # ---- 1) generation variance share via robust OLS eta-squared (Type-II SS) ----
    # The crossed random-effects LPM is degenerate on this 3-model subset (model RE hits the 0 boundary),
    # so for the variance SHARE we use fixed-effects OLS eta-squared, which is stable; the direct stability
    # statistics below are the primary, assumption-light evidence.
    import statsmodels.api as sm
    from statsmodels.stats.anova import anova_lm
    ols = smf.ols('adopt ~ C(model) + C(persona) + C(item) + C(generation)', data=dark).fit()
    aov = anova_lm(ols, typ=2)
    ss_tot = aov['sum_sq'].sum()
    eta = {k.replace('C(', '').replace(')', ''): round(float(v / ss_tot), 3)
           for k, v in aov['sum_sq'].items()}
    out['eta_squared_share'] = eta  # generation should be ~0

    # ---- 2) aggregate stability across generation seeds (per model) -- PRIMARY ----
    stab = {}
    for m in sorted(dark.model.unique()):
        sub = dark[dark.model == m]
        per_gen = sub.groupby('generation').adopt.mean()
        per_gen_flip = sub[sub.s1_correct == 1].groupby('generation').adopt.mean()
        stab[m] = dict(
            adopt_mean=round(float(per_gen.mean()), 3), adopt_sd=round(float(per_gen.std(ddof=1)), 4),
            adopt_min=round(float(per_gen.min()), 3), adopt_max=round(float(per_gen.max()), 3),
            flip_mean=round(float(per_gen_flip.mean()), 3), flip_sd=round(float(per_gen_flip.std(ddof=1)), 4),
            flip_range=round(float(per_gen_flip.max() - per_gen_flip.min()), 3))
    out['aggregate_stability_by_model'] = stab
    out['max_aggregate_gen_sd'] = round(max(s['adopt_sd'] for s in stab.values()), 4)
    out['max_flip_gen_range'] = round(max(s['flip_range'] for s in stab.values()), 3)

    # ---- 3) cell-level generation noise ----
    cell = dark.groupby(['model', 'persona', 'item', 'generation']).adopt.mean().reset_index()
    cell_sd = cell.groupby(['model', 'persona', 'item']).adopt.std(ddof=1)
    out['cell_level_generation_sd_mean'] = round(float(cell_sd.mean()), 4)
    out['cell_level_generation_sd_median'] = round(float(cell_sd.median()), 4)
    out['frac_cells_identical_across_gens'] = round(float((cell_sd == 0).mean()), 3)

    json.dump(out, open('results/generation_variance.json', 'w'), indent=2)
    print('ETA-SQUARED SHARE (with generation):', out['eta_squared_share'])
    print('max per-model aggregate SD across 5 gens:', out['max_aggregate_gen_sd'],
          '| max flip range:', out['max_flip_gen_range'])
    print('aggregate stability by model:')
    for m, s in stab.items():
        print('  %-18s adopt %.3f (sd %.4f, range %.3f-%.3f) | flip sd %.4f range %.3f'
              % (m, s['adopt_mean'], s['adopt_sd'], s['adopt_min'], s['adopt_max'],
                 s['flip_sd'], s['flip_range']))
    print('cell-level generation SD: mean %.4f median %.4f | frac cells identical across gens %.3f'
          % (out['cell_level_generation_sd_mean'], out['cell_level_generation_sd_median'],
             out['frac_cells_identical_across_gens']))
    print('-> results/generation_variance.json')


if __name__ == '__main__':
    main()
