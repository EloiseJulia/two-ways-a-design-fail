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
    """figstyle is the single source of truth for typography, palette, spines, grid and legends."""
    figstyle.apply()


def save(fig, name):
    figstyle.save(fig, name, FIGDIR)


def clean_axis(ax, grid_axis=None):
    """Thin wrapper kept for call-site compatibility; delegates to the shared style module."""
    return figstyle.style_axis(ax, grid=grid_axis)


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
        ls = figstyle.DATASET_LS[dom]
        # discrete conditions -> Wilson whisker error bars (line only guides the eye)
        ax.errorbar(x, rate, yerr=[err_lo, err_hi], fmt=mk, ls=ls, color=c, lw=1.6, ms=6,
                    zorder=3, **figstyle.ERRORBAR_KW, **figstyle.MARKER_KW)
        ax.text(x[-1] + 0.09, rate[-1], dom, color=c, va='center', ha='left', fontsize=9)
    figstyle.refline(ax, 0.5)
    figstyle.note(ax, 0.02, 0.508, 'chance (0.5)', va='bottom')
    # data-driven annotation: frontier is lowest on BOTH datasets (the robust cross-dataset pattern)
    yb = cr[('beer', 'gpt-5.5')][2]
    figstyle.annotate(ax, 'frontier lowest\non both datasets', xy=(3, yb), xytext=(2.42, 0.62))
    ax.set_xticks(x); ax.set_xticklabels(LADDER, rotation=12)
    ax.set_xlim(-0.25, 3.75); ax.set_ylim(0, 1.0)
    ax.set_ylabel('wrong-AI over-reliance (dark condition)')
    ax.set_xlabel('same-provider model set (small $\\rightarrow$ frontier)')
    figstyle.panel_title(ax, 'Wrong-advice adoption across model tiers')
    clean_axis(ax, grid_axis='y')
    save(fig, 'fig1_axis2_ladder')


# ---------------------------------------------------------------- fig2
def fig2(df):
    pr = persona_rates(df)
    # order personas by pooled susceptibility (mean over models+datasets), descending
    pooled = {p: np.mean([pr[(d, m, p)] for d in DOMAINS for m in ALL_MODELS]) for p in PERSONAS}
    order = sorted(PERSONAS, key=lambda p: pooled[p], reverse=True)
    fig = plt.figure(figsize=(11.8, 4.4))
    gs = fig.add_gridspec(1, 4, width_ratios=[6, 6, 1.5, 0.22], wspace=0.14)
    axes = [fig.add_subplot(gs[0, i]) for i in range(2)]
    axm = fig.add_subplot(gs[0, 2])
    axc = fig.add_subplot(gs[0, 3])
    cmap = plt.get_cmap(figstyle.HEATMAP_CMAP)

    def _ink_on(v):
        """Pick the cell label colour by the actual luminance of the cividis swatch."""
        r, g, b, _ = cmap(v)
        return figstyle.PAPER if (0.2126 * r + 0.7152 * g + 0.0722 * b) < 0.45 else figstyle.INK

    im = None
    for ax, dom in zip(axes, DOMAINS):
        M = np.array([[pr[(dom, m, p)] for m in ALL_MODELS] for p in order])
        im = ax.imshow(M, cmap=figstyle.HEATMAP_CMAP, vmin=0, vmax=1, aspect='auto')
        ax.set_xticks(range(len(ALL_MODELS)))
        ax.set_xticklabels([SHORT[m] for m in ALL_MODELS], rotation=35, ha='right', fontsize=8)
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels([PERSONA_SHORT[p] for p in order] if ax is axes[0] else [], fontsize=8)
        for i in range(len(order)):
            for j in range(len(ALL_MODELS)):
                ax.text(j, i, f'{M[i, j]:.2f}', ha='center', va='center', fontsize=7,
                        color=_ink_on(M[i, j]))
        figstyle.panel_title(ax, dom, size=9.5)
        ax.grid(False)
        ax.tick_params(length=0, labelcolor=figstyle.INK)
        for s in ('top', 'right', 'left', 'bottom'):
            ax.spines[s].set_visible(False)
        pi = order.index(TARGET)
        ax.add_patch(plt.Rectangle((-0.5, pi - 0.5), len(ALL_MODELS), 1, fill=False,
                                   edgecolor=figstyle.GOLD, lw=2.0, zorder=5))
    # marginal: pooled susceptibility bar, aligned to the heatmap row order (y=0 at TOP, like imshow)
    y = np.arange(len(order))
    vals = [pooled[p] for p in order]
    axm.barh(y, vals, color=[figstyle.GOLD if p == TARGET else figstyle.SLATE for p in order],
             height=0.66, zorder=3)
    axm.set_ylim(len(order) - 0.5, -0.5); axm.set_yticks([]); axm.set_xlim(0, 1)
    axm.set_xticks([0, 0.5, 1.0])
    axm.set_xlabel('mean\nsusceptibility', fontsize=8)
    figstyle.panel_title(axm, 'persona risk', size=8.5)
    figstyle.hide_spines(axm, ('top', 'right', 'left'))
    axm.tick_params(labelsize=8)
    axm.grid(True, axis='x', color=figstyle.GRIDCLR, linewidth=0.6, zorder=0)
    axm.set_axisbelow(True)
    figstyle.suptitle(fig, 'Dark-condition adoption by persona and backend '
                           '(personas sorted by susceptibility; p5 highlighted)', y=1.03)
    cb = fig.colorbar(im, cax=axc)
    cb.set_label('wrong-advice adoption', labelpad=8)
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=2.4, width=0.7, labelsize=8, color=figstyle.SPINE)
    save(fig, 'fig2_persona_heatmap')


# ---------------------------------------------------------------- fig3
def fig3(_df):
    dis = _axis1_disagreement()
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    y = np.arange(len(LADDER))
    for dom in DOMAINS:
        means = [float(np.mean(dis[(dom, m)])) for m in LADDER]
        c = DCOL[dom]
        off = 0.13 if dom == 'amzbook' else -0.13
        ax.hlines(y + off, 0, means, color=c, lw=1.3, alpha=0.45, zorder=2)
        ax.plot(means, y + off, figstyle.DATASET_MARK[dom], color=c, ms=7, label=dom, ls='none',
                zorder=3, **figstyle.MARKER_KW)
    ax.set_yticks(y); ax.set_yticklabels(LADDER)
    ax.invert_yaxis()
    ax.set_xlim(0, None)
    ax.set_xlabel('mean panel disagreement (persona heterogeneity)')
    figstyle.panel_title(ax, 'Persona heterogeneity is lowest at the frontier model')
    frontier_x = float(np.mean([np.mean(dis[(dom, LADDER[-1])]) for dom in DOMAINS]))
    figstyle.annotate(ax, 'lowest at frontier', xy=(frontier_x, len(LADDER) - 1),
                      xytext=(frontier_x + 0.030, len(LADDER) - 1.38), ha='left')
    figstyle.legend(ax, title='dataset', loc='lower right')
    clean_axis(ax, grid_axis='x')
    save(fig, 'fig3_axis1_collapse')


# ---------------------------------------------------------------- fig5
def fig5(df):
    cr = cell_rates(df)
    thr = 0.5
    FLAG, BELOW = figstyle.SIENNA, figstyle.TEAL
    # common order across panels (pooled adoption) so a backend sits in the same row in both datasets
    pooled_order = sorted(ALL_MODELS, key=lambda m: np.mean([cr[(d, m)][2] for d in DOMAINS]))
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.9), sharex=True, sharey=True)
    fig.subplots_adjust(wspace=0.10)
    for ax, dom in zip(axes, DOMAINS):
        names = [SHORT[m] for m in pooled_order]
        rates = [cr[(dom, m)][2] for m in pooled_order]
        cis = [wilson_ci(cr[(dom, m)][0], cr[(dom, m)][1]) for m in pooled_order]
        y = np.arange(len(names))
        ax.axvspan(thr, 1.0, color=FLAG, alpha=0.05, lw=0, zorder=0)
        for yi, r, (lo, hi) in zip(y, rates, cis):
            c = FLAG if r >= thr else BELOW
            # stem encodes DISTANCE FROM the decision threshold, not magnitude from zero
            ax.hlines(yi, min(thr, r), max(thr, r), color=c, lw=1.6, alpha=0.45, zorder=2)
            # Wilson 95% CI whisker: shows the flip is fragile where the CI straddles tau
            ax.errorbar(r, yi, xerr=[[r - lo], [hi - r]], fmt='none', ecolor=c, zorder=2,
                        **figstyle.ERRORBAR_KW)
            ax.plot(r, yi, 'o', color=c, ms=8, zorder=3, **figstyle.MARKER_KW)
            lab_x = hi + 0.018 if r >= thr else lo - 0.018
            figstyle.value_label(ax, lab_x, yi, f'{r:.2f}', color=c,
                                 ha='left' if r >= thr else 'right')
        figstyle.refline(ax, thr, axis='x', color=figstyle.SUBTLE, lw=1.0)
        figstyle.note(ax, thr + 0.018, len(names) - 0.32, r'$\tau=0.5$', color=figstyle.SUBTLE)
        ax.set_yticks(y); ax.set_yticklabels(names)
        ax.set_ylim(-0.7, len(names) - 0.2)
        nf = sum(r >= thr for r in rates)
        figstyle.panel_title(ax, f'{dom}: {nf}/6 would flag, {6 - nf}/6 clear', size=9.5)
        ax.set_xlim(0, 1.05); ax.set_xlabel('aggregate wrong-advice adoption (same interface)')
        clean_axis(ax, grid_axis=None)
    from matplotlib.lines import Line2D
    figstyle.legend(axes[1],
                    handles=[Line2D([0], [0], marker='o', color=FLAG, lw=0, markeredgecolor='white',
                                    label='would flag ($\\geq\\tau$)'),
                             Line2D([0], [0], marker='o', color=BELOW, lw=0, markeredgecolor='white',
                                    label='clears ($<\\tau$)')],
                    loc='lower right')
    # pairwise flip = fraction of the 15 backend pairs that disagree = nflag*nclear/15
    def _flip(dom):
        rs = [cr[(dom, m)][2] for m in ALL_MODELS]
        nf = sum(1 for r in rs if r >= thr)
        return nf * (6 - nf) / 15.0
    figstyle.suptitle(fig, 'The same interface, six backends: the screening decision flips with the '
                           'backend (pairwise flip %.2f / %.2f; Wilson 95%% CIs; common row order)'
                           % (_flip('beer'), _flip('amzbook')), y=1.02)
    save(fig, 'fig5_decision_flip')


# ---------------------------------------------------------------- fig7
def fig7(_df):
    cr = json.load(open('results/coverage_and_reliance.json'))
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.9))
    fig.subplots_adjust(wspace=0.28)
    panels = [('adopt_tau0.5', 'wrong-AI adoption $\\geq 0.5$'),
              ('flip_tau0.5', 'AI-induced flip $\\geq 0.5$ (clean)')]
    for ax, (key, sub) in zip(axes, panels):
        c = cr['coverage'][key]; U = c['universe_size']
        ks = np.arange(1, len(ALL_MODELS) + 1)
        gc = np.array(c['greedy_curve']) / U
        cc = np.array(c['capability_curve']) / U
        ax.fill_between(ks, cc, gc, step='post', where=gc >= cc, color=figstyle.GREEDY,
                        alpha=0.10, linewidth=0, zorder=1)
        ax.step(ks, gc, where='post', color=figstyle.GREEDY, lw=1.8, label='coverage-greedy (ours)', zorder=3)
        ax.step(ks, cc, where='post', color=figstyle.ROUTER, lw=1.8, ls=(0, (5, 2)),
                label='capability-first (router)', zorder=3)
        ax.plot(ks, gc, 'o', color=figstyle.GREEDY, ms=5, zorder=4, **figstyle.MARKER_KW)
        ax.plot(ks, cc, 's', color=figstyle.ROUTER, ms=5, zorder=4, **figstyle.MARKER_KW)
        figstyle.refline(ax, 1.0, ls=':', lw=0.8)
        ax.set_xlabel('panel size $k$'); ax.set_xticks(ks); ax.set_ylim(0, 1.10)
        ax.set_ylabel('vulnerability coverage\n(fraction of %d high-risk cells)' % U)
        figstyle.panel_title(ax, sub, size=9.5)
        # data-driven gap annotation: largest coverage gap and where it occurs
        gaps = gc - cc; kstar = int(np.argmax(gaps)); gap = gaps[kstar]
        figstyle.annotate(ax, f'+{100 * gap:.0f} pp at $k={kstar + 1}$',
                          xy=(kstar + 1, (gc[kstar] + cc[kstar]) / 2), xytext=(kstar + 1.7, 0.40),
                          color=figstyle.GREEDY, ha='left')
        figstyle.legend(ax, loc='lower right')
        clean_axis(ax, grid_axis='y')
    figstyle.suptitle(fig, 'Selecting a panel for vulnerability coverage inverts capability routing',
                      y=1.03)
    save(fig, 'fig7_coverage_curve')


# ---------------------------------------------------------------- fig8 (SLOPEGRAPH)
def fig8(_df):
    pr = json.load(open('results/protective_intervention.json'))
    conds = ['dark', 'plain', 'forcing', 'verify']
    clab = {'dark': 'dark', 'plain': 'plain', 'forcing': 'forcing', 'verify': 'verify'}
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(9.8, 4.4), gridspec_kw={'width_ratios': [2.4, 1]})
    fig.subplots_adjust(wspace=0.30)
    xs = np.arange(len(conds))
    # backend palette: the shared six-way categorical ramp (hue + lightness separated)
    bpal = dict(zip(ALL_MODELS, figstyle.BACKEND_CYCLE))
    for m in ALL_MODELS:
        ys = [pr['per_backend_condition'][m][c] for c in conds]
        axL.plot(xs, ys, '-', color=bpal[m], lw=1.5, alpha=0.9, zorder=2)
        axL.plot(xs, ys, 'o', color=bpal[m], ms=4.8, zorder=3, **figstyle.MARKER_KW)
    # de-collide the right-hand end labels
    ends = {m: pr['per_backend_condition'][m][conds[-1]] for m in ALL_MODELS}
    lab_y = _declutter([(m, ends[m]) for m in ALL_MODELS], min_gap=0.052)
    for m in ALL_MODELS:
        axL.plot([xs[-1], xs[-1] + 0.06], [ends[m], lab_y[m]], color=bpal[m], lw=0.6, alpha=0.6)
        axL.text(xs[-1] + 0.10, lab_y[m], SHORT[m], color=bpal[m], va='center', fontsize=8.5)
    figstyle.refline(axL, 0.5)
    axL.set_xticks(xs); axL.set_xticklabels([clab[c] for c in conds])
    axL.set_xlim(-0.2, 4.05); axL.set_ylim(0, 1.0)
    axL.set_ylabel('wrong-AI adoption')
    cm = pr['condition_main_LRT']; it = pr['interaction_LRT']
    d_pool = 100 * (pr['pooled_adoption']['plain'] - pr['pooled_adoption']['verify'])
    figstyle.panel_title(axL, 'Every backend descends dark$\\to$plain$\\to$protective\n'
                              f'(plain$\\to$verify $-{d_pool:.0f}$ pp, $p={cm["p"]:.3f}$; '
                              f'backend$\\times$condition $p={it["p"]:.2f}$, n.s.)', size=9.0)
    clean_axis(axL, grid_axis='y')
    # right: p5 slope (single emphasized line)
    p5 = pr['p5_pooled']
    ys = [p5[c] for c in conds]
    axR.plot(xs, ys, '-', color=figstyle.SUBTLE, lw=1.6, alpha=0.7, zorder=2)
    for xi, c in zip(xs, conds):
        axR.plot(xi, p5[c], 'o', color=figstyle.CONDITION[c], ms=9.5, zorder=3,
                 markeredgecolor=figstyle.PAPER, markeredgewidth=1.0)
        figstyle.value_label(axR, xi, p5[c] + 0.045, f'{p5[c]:.2f}', color=figstyle.CONDITION[c],
                             bbox=dict(boxstyle='round,pad=0.12', fc=figstyle.PAPER, ec='none',
                                       alpha=0.9), zorder=4)
    figstyle.refline(axR, 0.5)
    axR.set_xticks(xs); axR.set_xticklabels([clab[c] for c in conds], rotation=20, ha='right')
    axR.set_xlim(-0.45, len(conds) - 0.55)
    axR.set_ylim(0, 1.0); axR.set_ylabel('p5 wrong-AI adoption')
    d_p5 = 100 * (p5['plain'] - p5['verify'])
    figstyle.panel_title(axR, 'At-risk persona (p5)\n'
                              f'plain$\\to$verify $-{d_p5:.0f}$ pp ($p<10^{{-6}}$)', size=9.0)
    clean_axis(axR, grid_axis='y')
    save(fig, 'fig8_protective')


# ---------------------------------------------------------------- fig4, fig6 (restyled, kept type)
def fig6(_df):
    cv = json.load(open('results/capability_vulnerability.json'))
    fig, (axS, axB) = plt.subplots(1, 2, figsize=(9.8, 4.0), gridspec_kw={'width_ratios': [1.25, 1]})
    fig.subplots_adjust(wspace=0.34)
    # LEFT: capability vs AI-induced flip, per dataset, with an OLS guide line
    for dom in DOMAINS:
        pb = cv['per_backend'][dom]
        xs = np.array([pb[m]['capability_s1acc'] for m in ALL_MODELS])
        ys = np.array([pb[m]['flip_from_correct'] for m in ALL_MODELS])
        c = DCOL[dom]
        axS.scatter(xs, ys, s=52, color=c, marker=figstyle.DATASET_MARK[dom], label=dom,
                    zorder=3, **figstyle.SCATTER_KW)
        b, a = np.polyfit(xs, ys, 1)
        xx = np.linspace(xs.min(), xs.max(), 20)
        axS.plot(xx, b * xx + a, color=c, lw=1.2, ls=(0, (5, 2)), alpha=0.6, zorder=2)
    rb = cv['correlations']['beer']['flip_from_correct']['spearman']
    ra = cv['correlations']['amzbook']['flip_from_correct']['spearman']
    # annotate the frontier point (lowest flip) data-driven
    fb = cv['per_backend']['beer']['gpt-5.5']
    figstyle.annotate(axS, 'gpt-5.5\n(frontier)',
                      xy=(fb['capability_s1acc'], fb['flip_from_correct']),
                      xytext=(fb['capability_s1acc'] - 0.028, fb['flip_from_correct'] - 0.072))
    axS.set_xlabel('backend task competence (System-1 accuracy)')
    axS.set_ylabel('AI-induced flip-to-wrong\n$P(\\mathrm{adopt}\\mid\\mathrm{S1\\ correct})$')
    figstyle.panel_title(axS, 'Capability vs. reproduced vulnerability (directional guide)', size=9.5)
    axS.set_ylim(0, None)
    figstyle.legend(axS, title='dataset', loc='upper right')
    figstyle.note(axS, 0.015, 0.03, f'Spearman {rb:.2f} / {ra:.2f}\n'
                  '(n.s. at $n{=}6$; fit is a guide only;\nthe reading rests on coverage, right)',
                  size=7.2, color=figstyle.SUBTLE, transform=axS.transAxes, va='bottom', ha='left',
                  linespacing=1.35)
    clean_axis(axS, grid_axis='y')
    # RIGHT: panel vulnerability coverage as lollipops (single frontier / weak pair / diverse)
    labels = ['single frontier\n(gpt-5.5)', 'weak pair\n(gpt-4.1, 4o-mini)', 'diverse\n(all 6)']
    keys = ['single_frontier_gpt55_personas_over_0p5', 'weak_pair_personas_over_0p5',
            'diverse_all6_personas_over_0p5']
    yb = np.arange(len(labels))
    for i, dom in enumerate(DOMAINS):
        off = -0.15 if dom == 'beer' else 0.15
        vals = [cv['panel_coverage'][dom][k] for k in keys]
        c = DCOL[dom]
        axB.hlines(yb + off, 0, vals, color=c, lw=1.5, alpha=0.45, zorder=2)
        axB.plot(vals, yb + off, figstyle.DATASET_MARK[dom], color=c, ms=7.5, label=dom, ls='none',
                 zorder=3, **figstyle.MARKER_KW)
    axB.set_yticks(yb); axB.set_yticklabels(labels, fontsize=8.5); axB.invert_yaxis()
    axB.set_xlabel('# personas surfacing risk\n(dark adoption $\\geq0.5$, of 6)')
    axB.set_xlim(0, 6.2); axB.set_xticks(np.arange(0, 7))
    figstyle.panel_title(axB, 'Panel vulnerability coverage', size=9.5)
    figstyle.legend(axB, title='dataset', loc='lower right')
    clean_axis(axB, grid_axis='x')
    figstyle.suptitle(fig, 'The frontier backend is nearly blind to the at-risk persona '
                           '(coverage, not the fit, carries this)', y=1.03)
    save(fig, 'fig6_capability_vulnerability')


def fig6b_expand11(_df):
    """n=11 expansion: capability vs the three vulnerability measures (tiered by audited robustness:
    aggregate adoption = solid/robust; flip & p5 = open/suggestive), and the n=11 coverage curve."""
    ex = json.load(open('results/expand12_analysis.json'))
    models = ex['capability_order_strong_to_weak']
    cap = np.array([ex['capability_s1acc'][m] for m in models])
    pb = ex['per_backend']
    cor = ex['correlations']
    fig, (axS, axC) = plt.subplots(1, 2, figsize=(9.8, 4.1), gridspec_kw={'width_ratios': [1.15, 1]})
    fig.subplots_adjust(wspace=0.30)
    # LEFT: scatter of 3 metrics vs capability, tiered
    series = [('agg_adopt', 'aggregate adoption', figstyle.SIENNA, 'o', True),
              ('flip', 'AI-induced flip', figstyle.TEAL, 's', False),
              ('p5_adopt', 'p5 adoption', figstyle.PLUM, '^', False)]
    for key, lab, col, mk, robust in series:
        y = np.array([pb[m][key] for m in models])
        face = col if robust else figstyle.PAPER
        rho = cor[key]['spearman']; pbh = cor[key]['p_bh']
        tier = 'robust' if robust else 'suggestive'
        axS.scatter(cap, y, s=46, marker=mk, facecolor=face, edgecolor=col, linewidth=1.3, zorder=3,
                    label=f'{lab} ($\\rho{{=}}{rho:.2f}$, BH$\\,p{{=}}{pbh:.3f}$; {tier})')
        b, a = np.polyfit(cap, y, 1)
        xx = np.linspace(cap.min(), cap.max(), 20)
        axS.plot(xx, b * xx + a, color=col, lw=1.1, ls='-' if robust else (0, (5, 2)), alpha=0.55,
                 zorder=2)
    fm = ex['coverage']['adopt_tau0.5']['frontier_backend']
    figstyle.annotate(axS, f'{fm}\n(frontier)', xy=(cap[0], pb[models[0]]['agg_adopt']),
                      xytext=(cap[0] - 0.035, pb[models[0]]['agg_adopt'] + 0.18))
    axS.set_xlabel('backend task competence (System-1 accuracy)')
    axS.set_ylabel('dark-condition vulnerability metric')
    figstyle.panel_title(axS, f'Capability vs vulnerability at $n{{=}}{ex["n_backends"]}$ backends\n'
                              '(pooled both datasets; tiered by robustness)', size=9.5)
    axS.set_ylim(0, None)
    figstyle.legend(axS, loc='lower left', fontsize=7.2)
    clean_axis(axS, grid_axis='y')
    # RIGHT: n=11 coverage curve (adopt metric), greedy vs capability-first
    c = ex['coverage']['adopt_tau0.5']; U = c['universe']
    ks = np.arange(1, len(models) + 1)
    gc = np.array(c['greedy_curve']) / U
    cc = np.array(c['capability_curve']) / U
    axC.fill_between(ks, cc, gc, step='post', where=gc >= cc, color=figstyle.GREEDY, alpha=0.10,
                     linewidth=0, zorder=1)
    axC.step(ks, gc, where='post', color=figstyle.GREEDY, lw=1.8, label='coverage-greedy (ours)', zorder=3)
    axC.step(ks, cc, where='post', color=figstyle.ROUTER, lw=1.8, ls=(0, (5, 2)),
             label='capability-first (router)', zorder=3)
    axC.plot(ks, gc, 'o', color=figstyle.GREEDY, ms=4.2, zorder=4, **figstyle.MARKER_KW)
    axC.plot(ks, cc, 's', color=figstyle.ROUTER, ms=4.2, zorder=4, **figstyle.MARKER_KW)
    figstyle.refline(axC, 1.0, ls=':', lw=0.8)
    figstyle.annotate(axC, f'router reaches full\ncoverage only at $k{{=}}{c["capability_k_full"]}$',
                      xy=(c['capability_k_full'], 1.0), xytext=(1.6, 0.80), size=7.6,
                      color=figstyle.ROUTER, ha='left', va='center')
    axC.set_xlabel('panel size $k$'); axC.set_xticks(ks[::2])
    axC.set_ylabel('vulnerability coverage\n(fraction of %d high-risk cells)' % U)
    axC.set_ylim(0, 1.10)
    figstyle.panel_title(axC, f'Coverage at $n{{=}}{ex["n_backends"]}$', size=9.5)
    figstyle.legend(axC, loc='lower right')
    clean_axis(axC, grid_axis='y')
    figstyle.suptitle(fig, 'Backend expansion ($n{=}11$): capability anti-correlates with '
                           'vulnerability; coverage routing still inverted', y=1.03)
    save(fig, 'fig6b_expand11')


def fig9_variance(_df):
    """RQ2: which choices move the synthetic-panel number. eta^2 shares from the preregistered
    multi-generation run (3 backends x 2 UI x 6 personas x 20 items x 5 seeds)."""
    gv = json.load(open('results/generation_variance.json'))
    sh = gv['eta_squared_share']
    order = [('item', 'item (analyst-chosen)'), ('persona', 'persona (analyst-chosen)'),
             ('model', 'backend'), ('generation', 'generation (random draw)'), ('Residual', 'residual')]
    labels = [lab for _, lab in order]
    vals = [sh[k] for k, _ in order]
    ANALYST = figstyle.PLUM; BACK = figstyle.TEAL
    cols = [ANALYST, ANALYST, BACK, figstyle.FAINT, '#C4CBD1']
    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    y = np.arange(len(labels))[::-1]
    ax.barh(y, vals, color=cols, edgecolor=figstyle.PAPER, height=0.62, zorder=3)
    for yi, v in zip(y, vals):
        figstyle.value_label(ax, v + 0.009, yi, (f'{v:.3f}' if v < 0.01 else f'{v:.2f}'),
                             ha='left', color=figstyle.SUBTLE)
    ax.set_yticks(y); ax.set_yticklabels(labels)
    ax.set_xlim(0, max(vals) * 1.22)
    ax.set_xlabel(r'variance share ($\eta^2$, multi-generation run)')
    figstyle.panel_title(ax, 'The analyst moves the number more than the backend;\n'
                             'the random draw barely moves it')
    clean_axis(ax, grid_axis='x')
    save(fig, 'fig9_variance_decomp')


def fig10_ablation(_df):
    """RQ3: non-policy dispositional ablation. A deferential disposition stated only as facts (no trust
    policy) out-adopts an independent one on every backend; low self-confidence is the driving facet."""
    ab = json.load(open('results/dispositional_ablation.json'))
    backs = ab['backends']
    SB = {'gpt-3.5-turbo': 'gpt-3.5', 'gpt-4': 'gpt-4', 'gpt-5.4': 'gpt-5.4',
          'gemini-3.1-pro-preview': 'gemini-3.1-pro'}
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 4.0))
    fig.subplots_adjust(wspace=0.26)
    DEF = figstyle.SIENNA; IND = figstyle.TEAL
    y = np.arange(len(backs))
    for yi, b in zip(y, backs):
        a = ab['per_backend'][b]['adopt']
        d1 = a['d1-defer-lowconf']; d2 = a['d2-indep-highconf']
        axL.plot([d2, d1], [yi, yi], color=figstyle.GRIDCLR, lw=2.6, solid_capstyle='round', zorder=1)
        axL.plot(d2, yi, 'o', color=IND, ms=7.5, zorder=3, **figstyle.MARKER_KW)
        axL.plot(d1, yi, 'o', color=DEF, ms=7.5, zorder=3, **figstyle.MARKER_KW)
        figstyle.value_label(axL, (d1 + d2) / 2, yi + 0.18, f'+{d1 - d2:.2f}', va='bottom',
                             color=figstyle.SUBTLE)
    axL.set_yticks(y); axL.set_yticklabels([SB[b] for b in backs])
    axL.set_ylim(-0.6, len(backs) - 0.35)
    axL.set_xlim(0, 1.03); axL.set_xlabel('wrong-AI adoption (dark)')
    figstyle.panel_title(axL, 'Deferential disposition adopts more on every backend', size=9.5)
    from matplotlib.lines import Line2D
    figstyle.legend(axL,
                    handles=[Line2D([0], [0], marker='o', color=DEF, lw=0, markeredgecolor='white',
                                    label='d1 deferential (low self-confidence)'),
                             Line2D([0], [0], marker='o', color=IND, lw=0, markeredgecolor='white',
                                    label='d2 independent')],
                    loc='upper center', bbox_to_anchor=(0.5, -0.20), ncol=2, frameon=False)
    clean_axis(axL, grid_axis='x')
    facets = [('facet_confidence_d1_d6', 'low self-confidence'),
              ('facet_experience_d1_d5', 'low experience'),
              ('facet_aiuse_d1_d4', 'high AI-use')]
    fcol = [figstyle.VIRIDIAN, figstyle.SLATE, figstyle.GOLD]
    x = np.arange(len(backs)); w = 0.25
    for j, (key, lab) in enumerate(facets):
        vals = [ab['per_backend'][b][key] for b in backs]
        axR.bar(x + (j - 1) * w, vals, w, color=fcol[j], label=lab, edgecolor=figstyle.PAPER,
                linewidth=0.7, zorder=3)
    axR.axhline(0, color=figstyle.SPINE, lw=0.7, zorder=2)
    axR.set_xticks(x); axR.set_xticklabels([SB[b] for b in backs], rotation=12, fontsize=8.5)
    axR.set_ylabel('adoption gap vs d1 (isolating one fact)')
    figstyle.panel_title(axR, 'Low self-confidence is the lever, not the novice label', size=9.5)
    figstyle.legend(axR, loc='upper left', fontsize=7.6)
    clean_axis(axR, grid_axis='y')
    figstyle.suptitle(fig, 'Non-policy dispositional ablation '
                           '(exploratory: 12 items, 1 generation, 4 backends)', y=1.03)
    save(fig, 'fig10_dispositional_ablation')


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
    fig6b_expand11(df)
    fig7(df)
    fig8(df)
    fig9_variance(df)
    fig10_ablation(df)
    fig4_only(df)
    print('v3 figures ->', FIGDIR)


if __name__ == '__main__':
    main()
