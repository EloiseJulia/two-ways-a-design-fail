"""Version 3 figures --- a genuine scientific redesign (not a recolor).

Different visual ENCODINGS from v1/v2, in a journal (SciencePlots) idiom:
  fig1  capability ladder  -> line with Wilson CONFIDENCE BANDS + direct end-labels + effect bracket
  fig2  persona x backend  -> heatmap with a MARGINAL susceptibility bar (rows sorted by susceptibility)
  fig3  axis-1 collapse    -> Cleveland DOT plot with a frontier-collapse annotation
  fig4  rate vs ordering   -> (kept 2-panel; restyled)
  fig5  decision flip      -> Cleveland LOLLIPOP dot plot with a threshold line + flip shading (not bars)
  fig6  capability/vuln    -> scatter with regression + coverage lollipops
  fig7  coverage curve     -> step curves with the coverage-GAP shaded between greedy and router
  fig8  protective         -> SLOPEGRAPH (per-backend connected slopes dark->plain->forcing->verify)

Old versions are preserved: make_figures.py (v2) and figures/archive/{v0,v1,v2}. This writes to figures/.
Run: python scripts/analysis/make_figures_v3.py
"""
import json
import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import scienceplots  # noqa: F401  (registers the 'science' style)

sys.path.insert(0, os.path.dirname(__file__))
import figstyle  # noqa: E402
from axis2_robustness import load_dark_records, wilson_ci, PERSONAS, TARGET  # noqa: E402
from make_figures import cell_rates, persona_rates, _axis1_disagreement, PERSONA_SHORT  # noqa: E402

LADDER = ['gpt-4o-mini', 'gpt-4.1', 'gpt-4o', 'gpt-5.5']
ALL_MODELS = ['gpt-4o-mini', 'gpt-4.1', 'gpt-4o', 'gpt-5.5', 'claude-sonnet-4.5', 'gemini-2.5-pro']
SHORT = {'gpt-4o-mini': 'gpt-4o-mini', 'gpt-4.1': 'gpt-4.1', 'gpt-4o': 'gpt-4o', 'gpt-5.5': 'gpt-5.5',
         'claude-sonnet-4.5': 'claude', 'gemini-2.5-pro': 'gemini'}
DOMAINS = ['beer', 'amzbook']
FIGDIR = 'figures'
DCOL = figstyle.DATASET


def v3style():
    plt.style.use(['science', 'no-latex'])
    figstyle.apply()  # re-assert our serif + Okabe palette on top of scienceplots
    plt.rcParams.update({'axes.grid': False, 'legend.frameon': False,
                         'figure.dpi': 150, 'savefig.dpi': 400})


def save(fig, name):
    fig.savefig(os.path.join(FIGDIR, f'{name}.png'), bbox_inches='tight')
    fig.savefig(os.path.join(FIGDIR, f'{name}.pdf'), bbox_inches='tight')
    plt.close(fig)
    print('wrote', name)


# ---------------------------------------------------------------- fig1
def fig1(df):
    cr = cell_rates(df)
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    x = np.arange(len(LADDER))
    for dom in DOMAINS:
        rate, lo, hi = [], [], []
        for m in LADDER:
            k, n, r = cr[(dom, m)]
            l, h = wilson_ci(k, n)
            rate.append(r); lo.append(l); hi.append(h)
        c = DCOL[dom]
        ax.fill_between(x, lo, hi, color=c, alpha=0.15, linewidth=0)
        ax.plot(x, rate, '-', color=c, lw=2.0, zorder=3)
        ax.plot(x, rate, figstyle.DATASET_MARK[dom], color=c, ms=6, zorder=4,
                markeredgecolor='white', markeredgewidth=0.8)
        ax.text(x[-1] + 0.08, rate[-1], dom, color=c, va='center', ha='left', fontsize=10, weight='bold')
    ax.axhline(0.5, ls=(0, (4, 3)), color=figstyle.OKABE['grey'], lw=1.0)
    ax.text(0.02, 0.505, 'chance (0.5)', color=figstyle.OKABE['grey'], fontsize=8, va='bottom')
    # effect bracket: peak (gpt-4.1) -> frontier (gpt-5.5)
    yb = cr[('beer', 'gpt-5.5')][2]
    ax.annotate('', xy=(3, yb), xytext=(3, cr[('beer', 'gpt-4.1')][2]),
                arrowprops=dict(arrowstyle='<->', color='0.35', lw=1.1))
    ax.text(2.86, (yb + cr[('beer', 'gpt-4.1')][2]) / 2, 'frontier\nresists', color='0.3',
            fontsize=8.5, ha='right', va='center')
    ax.set_xticks(x); ax.set_xticklabels(LADDER, rotation=12)
    ax.set_xlim(-0.25, 3.7); ax.set_ylim(0, 1.0)
    ax.set_ylabel('wrong-AI over-reliance\n(dark condition; Wilson 95% band)')
    ax.set_xlabel('same-provider model set (small $\\rightarrow$ frontier)')
    ax.set_title('Wrong-advice adoption collapses at the frontier, on both datasets')
    ax.spines[['top', 'right']].set_visible(False)
    save(fig, 'fig1_axis2_ladder')


# ---------------------------------------------------------------- fig2
def fig2(df):
    pr = persona_rates(df)
    # order personas by pooled susceptibility (mean over models+datasets), descending
    pooled = {p: np.mean([pr[(d, m, p)] for d in DOMAINS for m in ALL_MODELS]) for p in PERSONAS}
    order = sorted(PERSONAS, key=lambda p: pooled[p], reverse=True)
    fig = plt.figure(figsize=(11.5, 4.4))
    gs = fig.add_gridspec(1, 3, width_ratios=[6, 6, 1.5], wspace=0.08)
    axes = [fig.add_subplot(gs[0, i]) for i in range(2)]
    axm = fig.add_subplot(gs[0, 2])
    im = None
    for ax, dom in zip(axes, DOMAINS):
        M = np.array([[pr[(dom, m, p)] for m in ALL_MODELS] for p in order])
        im = ax.imshow(M, cmap=figstyle.HEATMAP_CMAP, vmin=0, vmax=1, aspect='auto')
        ax.set_xticks(range(len(ALL_MODELS)))
        ax.set_xticklabels([SHORT[m] for m in ALL_MODELS], rotation=40, ha='right', fontsize=8)
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels([PERSONA_SHORT[p] for p in order] if ax is axes[0] else [], fontsize=8)
        for i in range(len(order)):
            for j in range(len(ALL_MODELS)):
                ax.text(j, i, f'{M[i, j]:.2f}', ha='center', va='center', fontsize=6.5,
                        color='white' if M[i, j] < 0.5 else 'black')
        ax.set_title(dom)
        ax.grid(False)
        pi = order.index(TARGET)
        ax.add_patch(plt.Rectangle((-0.5, pi - 0.5), len(ALL_MODELS), 1, fill=False,
                                   edgecolor=figstyle.OKABE['orange'], lw=2.2))
    # marginal: pooled susceptibility bar (rows aligned to the heatmap order)
    yv = np.arange(len(order))[::-1]
    vals = [pooled[p] for p in order]
    axm.barh(yv, vals, color=[figstyle.OKABE['orange'] if p == TARGET else figstyle.OKABE['skyblue']
                              for p in order], height=0.7)
    axm.set_ylim(-0.5, len(order) - 0.5); axm.set_yticks([]); axm.set_xlim(0, 1)
    axm.set_xlabel('mean\nsusceptibility', fontsize=8)
    axm.set_title('persona\nrisk', fontsize=8.5)
    for s in ['top', 'right', 'left']:
        axm.spines[s].set_visible(False)
    axm.grid(False)
    fig.suptitle('Dark-condition adoption by persona and backend (personas sorted by susceptibility; '
                 'p5 highlighted)', y=1.02)
    fig.colorbar(im, ax=axes, fraction=0.02, pad=0.01, label='wrong-advice adoption')
    save(fig, 'fig2_persona_heatmap')


# ---------------------------------------------------------------- fig3
def fig3(_df):
    dis = _axis1_disagreement()
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    y = np.arange(len(LADDER))
    for dom in DOMAINS:
        means = [float(np.mean(dis[(dom, m)])) for m in LADDER]
        c = DCOL[dom]
        off = 0.12 if dom == 'amzbook' else -0.12
        ax.hlines(y + off, 0, means, color=c, lw=1.4, alpha=0.55)
        ax.plot(means, y + off, figstyle.DATASET_MARK[dom], color=c, ms=7, label=dom,
                markeredgecolor='white', markeredgewidth=0.8)
    ax.set_yticks(y); ax.set_yticklabels(LADDER)
    ax.invert_yaxis()
    ax.set_xlabel('mean panel disagreement (between-persona variance of reliance rates)')
    ax.set_title('Persona heterogeneity collapses at the frontier')
    ax.annotate('collapse', xy=(0.02, len(LADDER) - 1), xytext=(0.09, len(LADDER) - 1.5),
                fontsize=9, color='0.3', arrowprops=dict(arrowstyle='->', color='0.4'))
    ax.legend(title='dataset', loc='lower right')
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='x', color=figstyle.GRIDCLR, lw=0.6)
    save(fig, 'fig3_axis1_collapse')


# ---------------------------------------------------------------- fig5
def fig5(df):
    cr = cell_rates(df)
    thr = 0.5
    FLAG, BELOW = figstyle.OKABE['vermillion'], figstyle.OKABE['blue']
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.9), sharex=True)
    for ax, dom in zip(axes, DOMAINS):
        vals = sorted(((m, cr[(dom, m)][2]) for m in ALL_MODELS), key=lambda t: t[1])
        names = [SHORT[m] for m, _ in vals]
        rates = [r for _, r in vals]
        y = np.arange(len(names))
        ax.axvspan(thr, 1.0, color=FLAG, alpha=0.06)
        for yi, r in zip(y, rates):
            c = FLAG if r >= thr else BELOW
            ax.hlines(yi, 0, r, color=c, lw=1.6, alpha=0.55)
            ax.plot(r, yi, 'o', color=c, ms=9, markeredgecolor='white', markeredgewidth=0.9, zorder=3)
            ax.text(r + 0.015, yi, f'{r:.2f}', va='center', fontsize=8.5)
        ax.axvline(thr, ls=(0, (4, 3)), color='0.35', lw=1.1)
        ax.text(thr + 0.015, len(names) - 0.35, r'$\tau=0.5$', fontsize=8.5)
        ax.set_yticks(y); ax.set_yticklabels(names)
        nf = sum(r >= thr for r in rates)
        ax.set_title(f'{dom}: {nf}/6 would flag, {6 - nf}/6 clear')
        ax.set_xlim(0, 1.0); ax.set_xlabel('aggregate wrong-advice adoption (same interface)')
        ax.spines[['top', 'right']].set_visible(False)
    from matplotlib.lines import Line2D
    axes[1].legend(handles=[Line2D([0], [0], marker='o', color=FLAG, lw=0, label='would flag ($\\geq\\tau$)'),
                            Line2D([0], [0], marker='o', color=BELOW, lw=0, label='clears ($<\\tau$)')],
                   loc='lower right')
    fig.suptitle('The same interface, six backends: the screening decision flips with the backend '
                 '(pairwise flip 0.60 / 0.33)', y=1.01)
    save(fig, 'fig5_decision_flip')


# ---------------------------------------------------------------- fig7
def fig7(_df):
    cr = json.load(open('results/coverage_and_reliance.json'))
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8))
    panels = [('adopt_tau0.5', 'wrong-AI adoption $\\geq 0.5$'),
              ('flip_tau0.5', 'AI-induced flip $\\geq 0.5$ (clean)')]
    for ax, (key, sub) in zip(axes, panels):
        c = cr['coverage'][key]; U = c['universe_size']
        ks = np.arange(1, len(ALL_MODELS) + 1)
        gc = np.array(c['greedy_curve']) / U
        cc = np.array(c['capability_curve']) / U
        ax.fill_between(ks, cc, gc, where=gc >= cc, color=figstyle.GREEDY, alpha=0.12, linewidth=0)
        ax.plot(ks, gc, '-o', color=figstyle.GREEDY, lw=2, ms=6, label='coverage-greedy (ours)',
                markeredgecolor='white', markeredgewidth=0.8, zorder=3)
        ax.plot(ks, cc, '--s', color=figstyle.ROUTER, lw=2, ms=6, label='capability-first (router)',
                markeredgecolor='white', markeredgewidth=0.8, zorder=3)
        ax.axhline(1.0, ls=':', color=figstyle.OKABE['grey'], lw=0.8)
        ax.set_xlabel('panel size $k$'); ax.set_xticks(ks); ax.set_ylim(0, 1.08)
        ax.set_ylabel('vulnerability coverage\n(fraction of %d high-risk cells)' % U)
        ax.set_title(sub, fontsize=9)
        ax.annotate('coverage gap', xy=(3, (gc[2] + cc[2]) / 2), xytext=(3.4, 0.45),
                    fontsize=8, color=figstyle.GREEDY, arrowprops=dict(arrowstyle='->', color=figstyle.GREEDY))
        ax.legend(loc='lower right', fontsize=8)
        ax.spines[['top', 'right']].set_visible(False)
    fig.suptitle('Selecting a panel for vulnerability coverage inverts capability routing', y=1.02)
    save(fig, 'fig7_coverage_curve')


# ---------------------------------------------------------------- fig8 (SLOPEGRAPH)
def fig8(_df):
    pr = json.load(open('results/protective_intervention.json'))
    conds = ['dark', 'plain', 'forcing', 'verify']
    clab = {'dark': 'dark', 'plain': 'plain', 'forcing': 'forcing', 'verify': 'verify'}
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(9.8, 4.4), gridspec_kw={'width_ratios': [2.4, 1]})
    xs = np.arange(len(conds))
    # backend palette (sequential-ish, distinct)
    bpal = dict(zip(ALL_MODELS, [figstyle.OKABE['blue'], figstyle.OKABE['vermillion'], figstyle.OKABE['green'],
                                 figstyle.OKABE['purple'], figstyle.OKABE['orange'], figstyle.OKABE['skyblue']]))
    for m in ALL_MODELS:
        ys = [pr['per_backend_condition'][m][c] for c in conds]
        axL.plot(xs, ys, '-', color=bpal[m], lw=1.6, alpha=0.9, zorder=2)
        axL.plot(xs, ys, 'o', color=bpal[m], ms=5, markeredgecolor='white', markeredgewidth=0.8, zorder=3)
        axL.text(xs[-1] + 0.06, ys[-1], SHORT[m], color=bpal[m], va='center', fontsize=8.5, weight='bold')
    axL.axhline(0.5, ls=(0, (4, 3)), color=figstyle.OKABE['grey'], lw=1.0)
    axL.set_xticks(xs); axL.set_xticklabels([clab[c] for c in conds])
    axL.set_xlim(-0.2, 3.9); axL.set_ylim(0, 0.72)
    axL.set_ylabel('wrong-AI adoption')
    cm = pr['condition_main_LRT']; it = pr['interaction_LRT']
    axL.set_title('Every backend descends dark$\\to$plain$\\to$protective\n'
                  f'(condition $p={cm["p"]:.3f}$; backend$\\times$condition $p={it["p"]:.2f}$, n.s.)',
                  fontsize=9)
    axL.spines[['top', 'right']].set_visible(False)
    # right: p5 slope (single emphasized line)
    p5 = pr['p5_pooled']
    ys = [p5[c] for c in conds]
    axR.plot(xs, ys, '-', color=figstyle.OKABE['vermillion'], lw=2.4, zorder=2)
    for xi, c in zip(xs, conds):
        axR.plot(xi, p5[c], 'o', color=figstyle.CONDITION[c], ms=10, markeredgecolor='white',
                 markeredgewidth=1.0, zorder=3)
        axR.text(xi, p5[c] + 0.03, f'{p5[c]:.2f}', ha='center', fontsize=8.5)
    axR.axhline(0.5, ls=(0, (4, 3)), color=figstyle.OKABE['grey'], lw=1.0)
    axR.set_xticks(xs); axR.set_xticklabels([clab[c] for c in conds], rotation=20)
    axR.set_ylim(0, 1.0); axR.set_ylabel('p5 wrong-AI adoption')
    axR.set_title('At-risk persona (p5)\n$p<10^{-6}$', fontsize=9)
    axR.spines[['top', 'right']].set_visible(False)
    save(fig, 'fig8_protective')


# ---------------------------------------------------------------- fig4, fig6 (restyled, kept type)
def fig4_fig6(df):
    # re-use v2 implementations under the v3 style for consistency (these types are already appropriate)
    import make_figures as mf
    mf.fig4_rate_vs_ordering(df)
    mf.fig6_capability_vulnerability(df)


def main():
    os.makedirs(FIGDIR, exist_ok=True)
    v3style()
    df = load_dark_records()
    fig1(df)
    fig2(df)
    fig3(df)
    fig5(df)
    fig7(df)
    fig8(df)
    fig4_fig6(df)
    print('v3 figures ->', FIGDIR)


if __name__ == '__main__':
    main()
