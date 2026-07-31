"""Generate the paper's key figures from existing results (compute-free, no API calls).

Outputs (both .png @200dpi and .pdf vector) into figures/:
  fig1_axis2_ladder      — axis-2 wrong-AI over-reliance across the capability ladder, both domains
  fig2_persona_heatmap   — persona x model dark-adoption heatmap (p5 row hot everywhere), both domains
  fig3_axis1_collapse    — axis-1 panel heterogeneity collapse at the frontier, both domains
  fig4_rate_vs_ordering  — aggregate RATE is model-idiosyncratic while persona ORDERING agrees

Run: python scripts/analysis/make_figures.py  (needs $env:PYTHONPATH=src for nothing extra; self-contained)
"""
import json
import os
import sys
import itertools
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
from axis2_robustness import load_dark_records, wilson_ci, PERSONAS, TARGET  # noqa: E402
import figstyle  # noqa: E402

LADDER = ['gpt-4o-mini', 'gpt-4.1', 'gpt-4o', 'gpt-5.5']
ALL_MODELS = ['gpt-4o-mini', 'gpt-4.1', 'gpt-4o', 'gpt-5.5', 'claude-sonnet-4.5', 'gemini-2.5-pro']
DOMAINS = ['beer', 'amzbook']
DCOL = figstyle.DATASET
PERSONA_SHORT = {'p1-novice-skeptical': 'p1 novice-skeptical',
                 'p2-expert-trusting': 'p2 expert-trusting',
                 'p3-moderate-balanced': 'p3 moderate-balanced',
                 'p4-skilled-skeptical': 'p4 skilled-skeptical',
                 'p5-novice-trusting': 'p5 novice-trusting',
                 'p6-expert-moderate': 'p6 expert-moderate'}
FIGDIR = 'figures'


def save(fig, name):
    figstyle.save(fig, name, FIGDIR)


def cell_rates(df):
    """(domain, model) -> overall dark over-reliance rate, and (k, n)."""
    out = {}
    for (dom, mod), g in df.groupby(['domain', 'model']):
        k, n = int(g.adopt.sum()), len(g)
        out[(dom, mod)] = (k, n, k / n)
    return out


def persona_rates(df):
    """(domain, model, persona) -> rate."""
    out = {}
    for (dom, mod, per), g in df.groupby(['domain', 'model', 'persona']):
        out[(dom, mod, per)] = g.adopt.mean()
    return out


def fig1_axis2_ladder(df):
    cr = cell_rates(df)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    x = np.arange(len(LADDER))
    for dom in DOMAINS:
        rates, los, his = [], [], []
        for m in LADDER:
            k, n, r = cr[(dom, m)]
            lo, hi = wilson_ci(k, n)
            rates.append(r); los.append(r - lo); his.append(hi - r)
        ax.errorbar(x, rates, yerr=[los, his], marker='o', capsize=3, lw=2,
                    color=DCOL[dom], label=dom)
    ax.axhline(0.5, ls='--', color='gray', lw=1)
    ax.text(len(LADDER) - 1, 0.51, 'chance (0.5)', color='gray', ha='right', va='bottom', fontsize=9)
    ax.annotate('frontier\nresists', xy=(3, 0.30), xytext=(2.3, 0.68),
                arrowprops=dict(arrowstyle='->', color='black'), fontsize=9, ha='center')
    ax.set_xticks(x); ax.set_xticklabels(LADDER, rotation=15)
    ax.set_ylabel('over-reliance on guaranteed-wrong AI\n(dark condition, Wilson 95% CI)')
    ax.set_xlabel('same-provider model set (small \u2192 frontier)')
    ax.set_ylim(0, 1)
    ax.set_title('Dark-condition wrong-advice adoption by backend, both datasets')
    ax.legend(title='dataset')
    save(fig, 'fig1_axis2_ladder')


def fig2_persona_heatmap(df):
    pr = persona_rates(df)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    for ax, dom in zip(axes, DOMAINS):
        M = np.array([[pr[(dom, m, p)] for m in ALL_MODELS] for p in PERSONAS])
        im = ax.imshow(M, cmap=figstyle.HEATMAP_CMAP, vmin=0, vmax=1, aspect='auto')
        ax.set_xticks(range(len(ALL_MODELS)))
        ax.set_xticklabels(ALL_MODELS, rotation=40, ha='right', fontsize=8)
        ax.set_yticks(range(len(PERSONAS)))
        ax.set_yticklabels([PERSONA_SHORT[p] for p in PERSONAS], fontsize=8)
        for i in range(len(PERSONAS)):
            for j in range(len(ALL_MODELS)):
                ax.text(j, i, f'{M[i, j]:.2f}', ha='center', va='center', fontsize=7,
                                color='white' if M[i, j] < 0.5 else 'black')
                ax.grid(False)
                # highlight the p5 row
                p5i = PERSONAS.index(TARGET)
                ax.add_patch(plt.Rectangle((-0.5, p5i - 0.5), len(ALL_MODELS), 1, fill=False,
                                           edgecolor=figstyle.OKABE['orange'], lw=2.2))
                ax.set_title(dom)
    fig.suptitle('Dark-condition wrong-advice adoption by persona and backend, both datasets '
                         '(p5 row highlighted)', fontsize=11)
    fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02, label='wrong-advice adoption')
    for ext in ('png', 'pdf'):
                fig.savefig(os.path.join(FIGDIR, f'fig2_persona_heatmap.{ext}'), bbox_inches='tight')
    plt.close(fig)
    print('wrote fig2_persona_heatmap')


def _axis1_disagreement():
    """(domain, model) -> list of per-condition panel disagreement values (5 conditions)."""
    files = {'beer': 'results/confirmatory_axis1_capladder.json',
             'amzbook': 'results/confirmatory_axis1_capladder_amzbook.json'}
    out = {}
    for dom, path in files.items():
        d = json.load(open(path))
        for m in LADDER:
            tbl = d['per_model'][m]['aligned_per_condition_table']
            out[(dom, m)] = [float(r['panel_disagreement']) for r in tbl]
    return out


def fig3_axis1_collapse():
    dis = _axis1_disagreement()
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    x = np.arange(len(LADDER))
    for i, dom in enumerate(DOMAINS):
        means = [float(np.mean(dis[(dom, m)])) for m in LADDER]
        sds = [float(np.std(dis[(dom, m)], ddof=1)) for m in LADDER]
        ax.errorbar(x + (i - 0.5) * 0.04, means, yerr=sds, marker='s', lw=2, capsize=3,
                    color=DCOL[dom], label=dom)
    ax.set_xticks(x); ax.set_xticklabels(LADDER, rotation=15)
    ax.set_ylabel('mean panel disagreement\n(error bars: SD across 5 UI conditions)')
    ax.set_xlabel('same-provider model set (small \u2192 frontier)')
    ax.set_ylim(0, None)
    ax.set_title('Mean panel disagreement by backend, both datasets')
    ax.legend(title='dataset')
    save(fig, 'fig3_axis1_collapse')


def fig4_rate_vs_ordering(df):
    cr = cell_rates(df)
    pr = persona_rates(df)
    fig, (axB, axA) = plt.subplots(1, 2, figsize=(11, 4.0), sharey=True)
    fig.subplots_adjust(wspace=0.10)
    # Per-persona vendor profiles, one per dataset (categorical personas: markers).
    # (The aggregate-adoption-by-backend bar panel was removed as redundant with fig5_decision_flip.)
    vendors = ['gpt-5.5', 'claude-sonnet-4.5', 'gemini-2.5-pro']
    vcol = {'gpt-5.5': figstyle.VIRIDIAN, 'claude-sonnet-4.5': figstyle.PLUM,
            'gemini-2.5-pro': figstyle.GOLD}
    vmark = {'gpt-5.5': 'o', 'claude-sonnet-4.5': 's', 'gemini-2.5-pro': '^'}
    xp = np.arange(len(PERSONAS))
    p5i = PERSONAS.index(TARGET)
    for ax, dom in [(axB, 'beer'), (axA, 'amzbook')]:
        ax.axvspan(p5i - 0.45, p5i + 0.45, color=figstyle.GOLD, alpha=0.07, lw=0, zorder=0)
        for m in vendors:
            y = [pr[(dom, m, p)] for p in PERSONAS]
            ax.plot(xp, y, marker=vmark[m], lw=1.4, ls=(0, (5, 2)), color=vcol[m], label=m,
                    ms=5.5, **figstyle.MARKER_KW)
        figstyle.note(ax, p5i, 1.045, 'p5', color=figstyle.SUBTLE, ha='center')
        ax.set_xticks(xp); ax.set_xticklabels([p.split('-', 1)[0] for p in PERSONAS], fontsize=8.5)
        ax.set_xlim(-0.5, len(PERSONAS) - 0.5)
        ax.set_xlabel('persona (categorical; order arbitrary)')
        if ax is axB:
            ax.set_ylabel('dark adoption')
        figstyle.panel_title(ax, f'Per-persona adoption, independent vendors ({dom})', size=9.5)
        ax.set_ylim(0, 1.1)
        figstyle.style_axis(ax, grid='y')
    figstyle.legend(axB, title='backend', loc='upper left', fontsize=7.6)
    save(fig, 'fig4_rate_vs_ordering')


def fig5_decision_flip(df):
    """Same dark interface, per-backend aggregate risk with a decision threshold: some backends flag,
    some clear -> the decision flips across backends."""
    cr = cell_rates(df)
    thr = 0.5
    FLAG, BELOW = figstyle.OKABE['vermillion'], figstyle.OKABE['blue']  # colorblind-safe
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharex=True)
    for ax, dom in zip(axes, DOMAINS):
        vals = [(m, cr[(dom, m)][2]) for m in ALL_MODELS]
        vals.sort(key=lambda t: t[1])
        names = [m for m, _ in vals]
        rates = [r for _, r in vals]
        colors = [FLAG if r >= thr else BELOW for r in rates]
        y = np.arange(len(names))
        ax.barh(y, rates, color=colors)
        ax.grid(True, axis='x'); ax.grid(False, axis='y')
        ax.axvline(thr, ls='--', color=figstyle.OKABE['black'], lw=1.2)
        ax.annotate(r'$\tau=0.5$', xy=(thr, len(names) - 0.4), xytext=(thr + 0.02, len(names) - 0.4),
                    fontsize=8, va='center')
        for yi, r in zip(y, rates):
            ax.text(r + 0.01, yi, f'{r:.2f}', va='center', fontsize=8)
        ax.set_yticks(y); ax.set_yticklabels(names, fontsize=8)
        n_flag = sum(r >= thr for r in rates)
        ax.set_title(f'{dom}: {n_flag}/6 at/above threshold, {6-n_flag}/6 below')
        ax.set_xlim(0, 1.0)
        ax.set_xlabel('aggregate wrong-advice adoption (same dark interface)')
    from matplotlib.patches import Patch
    axes[1].legend(handles=[Patch(color=FLAG, label=r'at/above $\tau$ (would flag)'),
                            Patch(color=BELOW, label=r'below $\tau$')],
                   fontsize=8, loc='lower right')
    fig.suptitle('Aggregate dark-condition adoption by backend, both datasets, at a fixed decision '
                 'threshold (pairwise flip rate 0.60 beer / 0.33 amzbook)', fontsize=11)
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(FIGDIR, f'fig5_decision_flip.{ext}'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('wrote fig5_decision_flip')


def fig6_capability_vulnerability(df):
    """Capability (System-1 accuracy) vs vulnerability coverage (p5 dark adoption) per backend, both
    datasets; plus panel-coverage bars (single frontier vs weak pair vs diverse)."""
    cv = json.load(open('results/capability_vulnerability.json'))
    fig, (axS, axB) = plt.subplots(1, 2, figsize=(11, 4.2))
    # LEFT: scatter capability vs AI-induced flip-from-correct (clean behavioral metric), both datasets
    for dom in DOMAINS:
        pb = cv['per_backend'][dom]
        xs = [pb[m]['capability_s1acc'] for m in ALL_MODELS]
        ys = [pb[m]['flip_from_correct'] for m in ALL_MODELS]
        axS.scatter(xs, ys, s=60, color=DCOL[dom], label=dom, zorder=3)
        z = np.polyfit(xs, ys, 1)
        xx = np.array([min(xs), max(xs)])
        axS.plot(xx, z[0] * xx + z[1], color=DCOL[dom], lw=1.2, alpha=0.6)
    fb = cv['per_backend']['beer']['gpt-5.5']
    axS.annotate('gpt-5.5\n(frontier)', xy=(fb['capability_s1acc'], fb['flip_from_correct']),
                 xytext=(fb['capability_s1acc'] - 0.03, fb['flip_from_correct'] + 0.15),
                 arrowprops=dict(arrowstyle='->'), fontsize=8, ha='center')
    rb = cv['correlations']['beer']['flip_from_correct']['spearman']
    ra = cv['correlations']['amzbook']['flip_from_correct']['spearman']
    axS.set_xlabel('backend task competence (System-1 accuracy)')
    axS.set_ylabel('AI-induced flip-to-wrong\n$P(\\mathrm{adopt}\\mid\\mathrm{System\\text{-}1\\ correct})$')
    axS.set_title(f'Capability vs AI-induced flip (directional, $n{{=}}6$)\n'
                  f'Spearman {rb:.2f} beer / {ra:.2f} amzbook (n.s.)')
    axS.set_ylim(0, None)
    axS.legend(title='dataset', fontsize=8)
    # RIGHT: panel coverage bars
    labels = ['single frontier\n(gpt-5.5)', 'weak pair\n(gpt-4.1, 4o-mini)', 'diverse\n(all 6)']
    keys = ['single_frontier_gpt55_personas_over_0p5', 'weak_pair_personas_over_0p5',
            'diverse_all6_personas_over_0p5']
    x = np.arange(len(labels)); w = 0.38
    for i, dom in enumerate(DOMAINS):
        vals = [cv['panel_coverage'][dom][k] for k in keys]
        axB.bar(x + (i - 0.5) * w, vals, w, color=DCOL[dom], label=dom)
    axB.set_xticks(x); axB.set_xticklabels(labels, fontsize=8)
    axB.set_ylabel('# personas surfacing risk\n(dark adoption $\\geq$ 0.5, of 6)')
    axB.set_title('Panel vulnerability coverage')
    axB.set_ylim(0, 6)
    axB.legend(title='dataset', fontsize=8)
    save(fig, 'fig6_capability_vulnerability')


def fig7_coverage_curve(_df):
    """Vulnerability-coverage as submodular set-cover: coverage-greedy vs capability-first (router)
    cumulative coverage of the high-severity failure cells, for both coverage metrics."""
    cr = json.load(open('results/coverage_and_reliance.json'))
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6))
    panels = [('adopt_tau0.5', 'wrong-AI adoption $\\geq 0.5$'),
              ('flip_tau0.5', 'AI-induced flip $\\geq 0.5$ (clean)')]
    for ax, (key, sub) in zip(axes, panels):
        c = cr['coverage'][key]
        U = c['universe_size']
        ks = np.arange(1, len(ALL_MODELS) + 1)
        gc = [v / U for v in c['greedy_curve']]
        cc = [v / U for v in c['capability_curve']]
        ax.plot(ks, gc, '-o', color=figstyle.GREEDY, label='coverage-greedy (ours)')
        ax.plot(ks, cc, '-s', color=figstyle.ROUTER, label='capability-first (router)')
        ax.axhline(1.0, ls=':', color=figstyle.OKABE['grey'], lw=0.8)
        ax.set_xlabel('panel size $k$ (backends)')
        ax.set_ylabel('vulnerability coverage\n(fraction of %d high-risk cells)' % U)
        ax.set_ylim(0, 1.05)
        ax.set_xticks(ks)
        ax.set_title(sub, fontsize=9)
        ax.legend(fontsize=8, loc='lower right')
        ax.annotate('router\'s 1st pick\n(frontier) = %.0f%%' % (100 * cc[0]),
                    xy=(1, cc[0]), xytext=(3.1, 0.30),
                    fontsize=7.5, color=figstyle.ROUTER, ha='center',
                    arrowprops=dict(arrowstyle='->', color=figstyle.ROUTER))
    fig.suptitle('Selecting a synthetic panel for vulnerability coverage inverts capability routing',
                 fontsize=10)
    save(fig, 'fig7_coverage_curve')


def fig8_protective(_df):
    """Experiment A: protective-intervention audit. Left: per-backend adoption across
    dark->plain->forcing->verify (the protective staircase is consistent across backends even though
    absolute levels differ). Right: the at-risk persona p5, pooled, showing a large protective drop."""
    pr = json.load(open('results/protective_intervention.json'))
    conds = ['dark', 'plain', 'forcing', 'verify']
    clabel = {'dark': 'dark\n(coercive)', 'plain': 'plain', 'forcing': 'forcing', 'verify': 'verify'}
    ccol = figstyle.CONDITION
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(9.6, 3.8), gridspec_kw={'width_ratios': [2.3, 1]})
    x = np.arange(len(ALL_MODELS)); w = 0.2
    for i, c in enumerate(conds):
        vals = [pr['per_backend_condition'][m][c] for m in ALL_MODELS]
        axL.bar(x + (i - 1.5) * w, vals, w, color=ccol[c], label=clabel[c])
    axL.set_xticks(x)
    axL.set_xticklabels([m.replace('-sonnet-4.5', '').replace('gemini-2.5-pro', 'gemini') for m in ALL_MODELS],
                        rotation=20, ha='right', fontsize=8)
    axL.set_ylabel('wrong-AI adoption')
    axL.axhline(0.5, ls=':', color='gray', lw=0.8)
    axL.set_ylim(0, 1.0)
    lr = pr['interaction_LRT']; cm = pr['condition_main_LRT']
    axL.set_title('Protective staircase by backend\n'
                  f'condition main effect $p={cm["p"]:.3f}$; backend$\\times$condition $p={lr["p"]:.2f}$ (n.s.)',
                  fontsize=9)
    axL.legend(fontsize=7.5, ncol=4, loc='upper center', columnspacing=0.8, handlelength=1.0)
    # right: p5 pooled
    p5 = pr['p5_pooled']
    axR.bar(range(len(conds)), [p5[c] for c in conds], color=[ccol[c] for c in conds])
    axR.set_xticks(range(len(conds)))
    axR.set_xticklabels([clabel[c].split('\n')[0] for c in conds], rotation=20, ha='right', fontsize=8)
    axR.set_ylabel('p5 wrong-AI adoption')
    axR.axhline(0.5, ls=':', color='gray', lw=0.8)
    axR.set_ylim(0, 1.0)
    axR.set_title('At-risk persona (p5)\n$0.78\\!\\to\\!0.46$\u2013$0.53$ ($p<10^{-6}$)', fontsize=9)
    save(fig, 'fig8_protective')


def main():
    os.makedirs(FIGDIR, exist_ok=True)
    figstyle.apply()
    df = load_dark_records()
    fig1_axis2_ladder(df)
    fig2_persona_heatmap(df)
    fig3_axis1_collapse()
    fig4_rate_vs_ordering(df)
    fig5_decision_flip(df)
    fig6_capability_vulnerability(df)
    fig7_coverage_curve(df)
    fig8_protective(df)
    print('all figures ->', FIGDIR)


if __name__ == '__main__':
    main()
