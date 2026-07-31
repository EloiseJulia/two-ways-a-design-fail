"""Extra figures for the three review-hardening analyses (compute-free; reads results/*_n50.json):
  fig_threshold_sweep   -- pairwise backend flip rate vs tau (tau=0.5 recedes to one point)
  fig_specificity       -- sensitivity (dark) vs false-flag (neutral, non-coercive) per backend
Run: python scripts/analysis/make_figures_extra.py
"""
import json
import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import scienceplots  # noqa: F401

sys.path.insert(0, os.path.dirname(__file__))
import figstyle  # noqa: E402

FILES = {
    ('beer', 'capladder'): 'results/axis2_powered_capladder_n50.json',
    ('beer', 'crossvendor'): 'results/axis2_powered_crossvendor_n50.json',
    ('amzbook', 'capladder'): 'results/axis2_powered_capladder_amzbook_n50.json',
    ('amzbook', 'crossvendor'): 'results/axis2_powered_crossvendor_amzbook_n50.json',
}
MOD = ['gpt-4o-mini', 'gpt-4.1', 'gpt-4o', 'gpt-5.5', 'claude-sonnet-4.5', 'gemini-2.5-pro']
SHORT = {'gpt-4o-mini': 'gpt-4o-mini', 'gpt-4.1': 'gpt-4.1', 'gpt-4o': 'gpt-4o', 'gpt-5.5': 'gpt-5.5',
         'claude-sonnet-4.5': 'claude', 'gemini-2.5-pro': 'gemini'}
DARK, NEUT = 'Wrong-AI-GT (dark)', 'Conf.'
FIGDIR = 'figures'


def load():
    rec = []
    for (dom, arm), path in FILES.items():
        d = json.load(open(path, encoding='utf-8'))
        for r in d['responses']:
            m = r['model']
            if m == 'gpt-5.5' and arm != 'capladder':
                continue
            t = r['trace']
            gt = int(t['ground_truth'])
            cond = r['ui_condition']
            disp = (1 - gt) if 'Wrong-AI' in cond else int(t['ai_advice'])
            wrong_adopt = 1 if (int(r['final_decision']) == disp and disp != gt) else 0
            adopt = 1 if int(r['final_decision']) == disp else 0
            rec.append((dom, m, str(r['task_id']), cond, gt, disp, adopt, wrong_adopt))
    return rec


def style():
    plt.style.use(['science', 'no-latex'])
    figstyle.apply()
    plt.rcParams.update({'axes.grid': False, 'legend.frameon': False,
                         'figure.dpi': 150, 'savefig.dpi': 400})


def save(fig, name):
    fig.savefig(os.path.join(FIGDIR, name + '.png'), bbox_inches='tight')
    fig.savefig(os.path.join(FIGDIR, name + '.pdf'), bbox_inches='tight')
    plt.close(fig)
    print('wrote', name)


def dark_rate(rec, dom, m):
    xs = [a for (d, mm, it, c, gt, disp, a, wa) in rec if d == dom and mm == m and 'Wrong-AI' in c]
    return sum(xs) / len(xs)


def fig_threshold_sweep(rec):
    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    taus = np.linspace(0.0, 1.0, 101)
    for dom in ['beer', 'amzbook']:
        rates = [dark_rate(rec, dom, m) for m in MOD]
        flips = []
        for tau in taus:
            nf = sum(1 for x in rates if x >= tau)
            flips.append(nf * (6 - nf) / 15.0)
        c = figstyle.DATASET[dom]
        ls = '-' if dom == 'beer' else '--'
        ax.plot(taus, flips, ls, color=c, lw=2, label=dom)
    ax.axvline(0.5, ls=(0, (2, 2)), color=figstyle.OKABE['grey'], lw=1.0)
    ax.text(0.5, 0.62, r'$\tau=0.5$ (one operating point)', rotation=90, va='top', ha='right',
            fontsize=8, color='0.4')
    ax.set_xlabel(r'decision threshold $\tau$')
    ax.set_ylabel('pairwise backend flip rate')
    ax.set_xlim(0, 1); ax.set_ylim(0, 0.66)
    ax.set_title('Backends disagree across the whole threshold range, not just at $\\tau=0.5$')
    ax.legend(title='dataset', loc='upper right')
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', color=figstyle.GRIDCLR, lw=0.6); ax.set_axisbelow(True)
    save(fig, 'fig_threshold_sweep')


def fig_specificity(rec):
    # matched-wrong items per dom (AI wrong under neutral)
    mw = {}
    for dom in ['beer', 'amzbook']:
        mw[dom] = set(it for (d, m, it, c, gt, disp, a, wa) in rec
                      if d == dom and c == NEUT and disp != gt)

    def rate(dom, m, cond):
        xs = [wa for (d, mm, it, c, gt, disp, a, wa) in rec
              if d == dom and mm == m and c == cond and it in mw[dom]]
        return sum(xs) / len(xs) if xs else float('nan')

    fig, ax = plt.subplots(figsize=(5.8, 5.2))
    ax.plot([0, 0.75], [0, 0.75], ls=(0, (3, 3)), color='0.6', lw=1.0, zorder=1)
    ax.text(0.55, 0.585, 'flag-everything\n(no discrimination)', rotation=45, fontsize=7.5,
            color='0.5', ha='center', va='center')
    for dom in ['beer', 'amzbook']:
        c = figstyle.DATASET[dom]; mk = figstyle.DATASET_MARK[dom]
        for m in MOD:
            x = rate(dom, m, NEUT)   # false-flag
            y = rate(dom, m, DARK)   # sensitivity
            ax.scatter(x, y, s=60, color=c, marker=mk, edgecolor='white', linewidth=0.8, zorder=3)
            if m in ('gpt-5.5', 'gpt-4.1'):
                ax.annotate(SHORT[m], (x, y), textcoords='offset points', xytext=(6, -2),
                            fontsize=8, color=c)
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([0], [0], marker='o', color=figstyle.DATASET['beer'], lw=0, label='beer'),
                       Line2D([0], [0], marker='s', color=figstyle.DATASET['amzbook'], lw=0, label='amzbook')],
              title='dataset', loc='lower right')
    ax.set_xlabel('false-flag: wrong-advice adoption on the\nNON-coercive (neutral) interface')
    ax.set_ylabel('sensitivity: wrong-advice adoption on the\ncoercive (dark) interface')
    ax.set_xlim(0, 0.7); ax.set_ylim(0, 0.75)
    ax.set_title('Coverage is a sensitivity--specificity trade-off\n'
                 '(high-coverage backends also over-flag safe interfaces; Spearman 0.86)', fontsize=9.5)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(color=figstyle.GRIDCLR, lw=0.6); ax.set_axisbelow(True)
    save(fig, 'fig_specificity')


def main():
    os.makedirs(FIGDIR, exist_ok=True)
    style()
    rec = load()
    fig_threshold_sweep(rec)
    fig_specificity(rec)


if __name__ == '__main__':
    main()
