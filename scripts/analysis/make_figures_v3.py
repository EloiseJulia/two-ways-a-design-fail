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


def clean_axis(ax, grid_axis=None):
    """Shared axis hygiene: drop top/right spines, outward ticks, optional light grid."""
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(direction='out', length=3, width=0.8)
    if grid_axis is not None:
        ax.grid(axis=grid_axis, color=figstyle.GRIDCLR, linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)
    return ax


def _declutter(pairs, min_gap):
    """Given [(label, y), ...], nudge y-values apart by >= min_gap for readable end-labels."""
    order = sorted(pairs, key=lambda t: t[1])
    out, prev = [], None
    for lab, y in order:
        if prev is not None and y - prev < min_gap:
            y = prev + min_gap
        out.append((lab, y)); prev = y
    return dict(out)


# ---------------------------------------------------------------- fig1
def fig1(df):
    cr = cell_rates(df)
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    x = np.arange(len(LADDER))
    for dom in DOMAINS:
        rate, err_lo, err_hi = [], [], []
        for m in LADDER:
            k, n, r = cr[(dom, m)]
            lo, hi = wilson_ci(k, n)
            rate.append(r); err_lo.append(r - lo); err_hi.append(hi - r)
        c = DCOL[dom]; mk = figstyle.DATASET_MARK[dom]
        ls = '-' if dom == 'beer' else '--'
        # discrete conditions -> Wilson whisker error bars (line only guides the eye)
        ax.errorbar(x, rate, yerr=[err_lo, err_hi], fmt=mk, ls=ls, color=c, lw=1.8, ms=6,
                    capsize=2.5, capthick=1.0, markeredgecolor='white', markeredgewidth=0.8, zorder=3)
        ax.text(x[-1] + 0.09, rate[-1], dom, color=c, va='center', ha='left', fontsize=10, weight='bold')
    ax.axhline(0.5, ls=(0, (4, 3)), color=figstyle.OKABE['grey'], lw=1.0)
    ax.text(0.02, 0.505, 'chance (0.5)', color=figstyle.OKABE['grey'], fontsize=8, va='bottom')
    # data-driven annotation: frontier is lowest on BOTH datasets (the robust cross-dataset pattern)
    yb = cr[('beer', 'gpt-5.5')][2]
    ax.annotate('frontier lowest\non both datasets', xy=(3, yb), xytext=(2.35, 0.80),
                fontsize=8.5, color='0.3', ha='center',
                arrowprops=dict(arrowstyle='->', color='0.45', lw=1.0))
    ax.set_xticks(x); ax.set_xticklabels(LADDER, rotation=12)
    ax.set_xlim(-0.25, 3.7); ax.set_ylim(0, 1.0)
    ax.set_ylabel('wrong-AI over-reliance (dark condition)')
    ax.set_xlabel('same-provider model set (small $\\rightarrow$ frontier)')
    ax.set_title('Wrong-advice adoption across model tiers')
    clean_axis(ax)
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
    # marginal: pooled susceptibility bar, aligned to the heatmap row order (y=0 at TOP, like imshow)
    y = np.arange(len(order))
    vals = [pooled[p] for p in order]
    axm.barh(y, vals, color=[figstyle.OKABE['orange'] if p == TARGET else figstyle.OKABE['skyblue']
                             for p in order], height=0.7)
    axm.set_ylim(len(order) - 0.5, -0.5); axm.set_yticks([]); axm.set_xlim(0, 1)
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
    ax.set_xlabel('mean panel disagreement (persona heterogeneity)')
    ax.set_title('Persona heterogeneity collapses at the frontier')
    frontier_x = float(np.mean([np.mean(dis[(dom, LADDER[-1])]) for dom in DOMAINS]))
    ax.annotate('frontier collapse', xy=(frontier_x, len(LADDER) - 1),
                xytext=(frontier_x + 0.06, len(LADDER) - 1.6), fontsize=9, color='0.3',
                arrowprops=dict(arrowstyle='->', color='0.4'))
    ax.legend(title='dataset', loc='lower right')
    clean_axis(ax, grid_axis='x')
    save(fig, 'fig3_axis1_collapse')


# ---------------------------------------------------------------- fig5
def fig5(df):
    cr = cell_rates(df)
    thr = 0.5
    FLAG, BELOW = figstyle.OKABE['vermillion'], figstyle.OKABE['blue']
    # common order across panels (pooled adoption) so a backend sits in the same row in both datasets
    pooled_order = sorted(ALL_MODELS, key=lambda m: np.mean([cr[(d, m)][2] for d in DOMAINS]))
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.9), sharex=True, sharey=True)
    for ax, dom in zip(axes, DOMAINS):
        names = [SHORT[m] for m in pooled_order]
        rates = [cr[(dom, m)][2] for m in pooled_order]
        y = np.arange(len(names))
        ax.axvspan(thr, 1.0, color=FLAG, alpha=0.06)
        for yi, r in zip(y, rates):
            c = FLAG if r >= thr else BELOW
            # stem encodes DISTANCE FROM the decision threshold, not magnitude from zero
            ax.hlines(yi, min(thr, r), max(thr, r), color=c, lw=1.8, alpha=0.6)
            ax.plot(r, yi, 'o', color=c, ms=9, markeredgecolor='white', markeredgewidth=0.9, zorder=3)
            ax.text(r + (0.015 if r >= thr else -0.015), yi, f'{r:.2f}', va='center',
                    ha='left' if r >= thr else 'right', fontsize=8.5)
        ax.axvline(thr, ls=(0, (4, 3)), color='0.35', lw=1.1)
        ax.text(thr + 0.015, len(names) - 0.35, r'$\tau=0.5$', fontsize=8.5)
        ax.set_yticks(y); ax.set_yticklabels(names)
        nf = sum(r >= thr for r in rates)
        ax.set_title(f'{dom}: {nf}/6 would flag, {6 - nf}/6 clear')
        ax.set_xlim(0, 1.0); ax.set_xlabel('aggregate wrong-advice adoption (same interface)')
        clean_axis(ax)
    from matplotlib.lines import Line2D
    axes[1].legend(handles=[Line2D([0], [0], marker='o', color=FLAG, lw=0, label='would flag ($\\geq\\tau$)'),
                            Line2D([0], [0], marker='o', color=BELOW, lw=0, label='clears ($<\\tau$)')],
                   loc='lower right')
    fig.suptitle('The same interface, six backends: the screening decision flips with the backend '
                 '(pairwise flip 0.60 / 0.33; common row order)', y=1.01)
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
        ax.fill_between(ks, cc, gc, step='post', where=gc >= cc, color=figstyle.GREEDY,
                        alpha=0.12, linewidth=0)
        ax.step(ks, gc, where='post', color=figstyle.GREEDY, lw=2, label='coverage-greedy (ours)', zorder=3)
        ax.step(ks, cc, where='post', color=figstyle.ROUTER, lw=2, ls='--',
                label='capability-first (router)', zorder=3)
        ax.plot(ks, gc, 'o', color=figstyle.GREEDY, ms=5, markeredgecolor='white', markeredgewidth=0.8, zorder=4)
        ax.plot(ks, cc, 's', color=figstyle.ROUTER, ms=5, markeredgecolor='white', markeredgewidth=0.8, zorder=4)
        ax.axhline(1.0, ls=':', color=figstyle.OKABE['grey'], lw=0.8)
        ax.set_xlabel('panel size $k$'); ax.set_xticks(ks); ax.set_ylim(0, 1.08)
        ax.set_ylabel('vulnerability coverage\n(fraction of %d high-risk cells)' % U)
        ax.set_title(sub, fontsize=9)
        # data-driven gap annotation: largest coverage gap and where it occurs
        gaps = gc - cc; kstar = int(np.argmax(gaps)); gap = gaps[kstar]
        ax.annotate(f'+{100 * gap:.0f} pp at $k={kstar + 1}$',
                    xy=(kstar + 1, (gc[kstar] + cc[kstar]) / 2), xytext=(kstar + 1.5, 0.42),
                    fontsize=8, color=figstyle.GREEDY,
                    arrowprops=dict(arrowstyle='->', color=figstyle.GREEDY))
        ax.legend(loc='lower right', fontsize=8)
        clean_axis(ax)
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
    # de-collide the right-hand end labels
    ends = {m: pr['per_backend_condition'][m][conds[-1]] for m in ALL_MODELS}
    lab_y = _declutter([(m, ends[m]) for m in ALL_MODELS], min_gap=0.032)
    for m in ALL_MODELS:
        axL.plot([xs[-1], xs[-1] + 0.05], [ends[m], lab_y[m]], color=bpal[m], lw=0.6, alpha=0.7)
        axL.text(xs[-1] + 0.08, lab_y[m], SHORT[m], color=bpal[m], va='center', fontsize=8.5, weight='bold')
    axL.axhline(0.5, ls=(0, (4, 3)), color=figstyle.OKABE['grey'], lw=1.0)
    axL.set_xticks(xs); axL.set_xticklabels([clab[c] for c in conds])
    axL.set_xlim(-0.2, 4.0); axL.set_ylim(0, 0.72)
    axL.set_ylabel('wrong-AI adoption')
    cm = pr['condition_main_LRT']; it = pr['interaction_LRT']
    d_pool = 100 * (pr['pooled_adoption']['plain'] - pr['pooled_adoption']['verify'])
    axL.set_title('Every backend descends dark$\\to$plain$\\to$protective\n'
                  f'(plain$\\to$verify $-{d_pool:.0f}$ pp, $p={cm["p"]:.3f}$; '
                  f'backend$\\times$condition $p={it["p"]:.2f}$, n.s.)', fontsize=8.5)
    clean_axis(axL)
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
    d_p5 = 100 * (p5['plain'] - p5['verify'])
    axR.set_title(f'At-risk persona (p5)\nplain$\\to$verify $-{d_p5:.0f}$ pp ($p<10^{{-6}}$)', fontsize=8.5)
    clean_axis(axR)
    save(fig, 'fig8_protective')


# ---------------------------------------------------------------- fig4, fig6 (restyled, kept type)
def fig6(_df):
    cv = json.load(open('results/capability_vulnerability.json'))
    fig, (axS, axB) = plt.subplots(1, 2, figsize=(9.4, 3.9), gridspec_kw={'width_ratios': [1.25, 1]})
    # LEFT: capability vs AI-induced flip, per dataset, with an OLS guide line
    for dom in DOMAINS:
        pb = cv['per_backend'][dom]
        xs = np.array([pb[m]['capability_s1acc'] for m in ALL_MODELS])
        ys = np.array([pb[m]['flip_from_correct'] for m in ALL_MODELS])
        c = DCOL[dom]
        axS.scatter(xs, ys, s=55, color=c, marker=figstyle.DATASET_MARK[dom], label=dom,
                    edgecolor='white', linewidth=0.8, zorder=3)
        b, a = np.polyfit(xs, ys, 1)
        xx = np.linspace(xs.min(), xs.max(), 20)
        axS.plot(xx, b * xx + a, color=c, lw=1.3, ls='--', alpha=0.7)
    rb = cv['correlations']['beer']['flip_from_correct']['spearman']
    ra = cv['correlations']['amzbook']['flip_from_correct']['spearman']
    # annotate the frontier point (lowest flip) data-driven
    fb = cv['per_backend']['beer']['gpt-5.5']
    axS.annotate('gpt-5.5\n(frontier)', xy=(fb['capability_s1acc'], fb['flip_from_correct']),
                 xytext=(fb['capability_s1acc'] - 0.02, fb['flip_from_correct'] + 0.14), fontsize=8,
                 ha='center', arrowprops=dict(arrowstyle='->', color='0.4'))
    axS.set_xlabel('backend task competence (System-1 accuracy)')
    axS.set_ylabel('AI-induced flip-to-wrong\n$P(\\mathrm{adopt}\\mid\\mathrm{S1\\ correct})$')
    axS.set_title(f'Capability vs vulnerability (directional, $n{{=}}6$)\n'
                  f'Spearman {rb:.2f} / {ra:.2f} (n.s.)', fontsize=9)
    axS.set_ylim(0, None); axS.legend(title='dataset', fontsize=8)
    clean_axis(axS, grid_axis='y')
    # RIGHT: panel vulnerability coverage as lollipops (single frontier / weak pair / diverse)
    labels = ['single frontier\n(gpt-5.5)', 'weak pair\n(gpt-4.1, 4o-mini)', 'diverse\n(all 6)']
    keys = ['single_frontier_gpt55_personas_over_0p5', 'weak_pair_personas_over_0p5',
            'diverse_all6_personas_over_0p5']
    yb = np.arange(len(labels))
    for i, dom in enumerate(DOMAINS):
        off = -0.14 if dom == 'beer' else 0.14
        vals = [cv['panel_coverage'][dom][k] for k in keys]
        c = DCOL[dom]
        axB.hlines(yb + off, 0, vals, color=c, lw=1.6, alpha=0.5)
        axB.plot(vals, yb + off, figstyle.DATASET_MARK[dom], color=c, ms=8, label=dom,
                 markeredgecolor='white', markeredgewidth=0.8, zorder=3)
    axB.set_yticks(yb); axB.set_yticklabels(labels, fontsize=8); axB.invert_yaxis()
    axB.set_xlabel('# personas surfacing risk\n(dark adoption $\\geq0.5$, of 6)')
    axB.set_xlim(0, 6); axB.set_title('Panel vulnerability coverage', fontsize=9)
    axB.legend(title='dataset', fontsize=8, loc='lower right')
    clean_axis(axB, grid_axis='x')
    save(fig, 'fig6_capability_vulnerability')


def fig4_only(df):
    import make_figures as mf
    mf.fig4_rate_vs_ordering(df)


def main():
    os.makedirs(FIGDIR, exist_ok=True)
    v3style()
    df = load_dark_records()
    fig1(df)
    fig2(df)
    fig3(df)
    fig5(df)
    fig6(df)
    fig7(df)
    fig8(df)
    fig4_only(df)
    print('v3 figures ->', FIGDIR)


if __name__ == '__main__':
    main()
