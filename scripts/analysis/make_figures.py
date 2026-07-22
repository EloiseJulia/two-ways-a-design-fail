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

LADDER = ['gpt-4o-mini', 'gpt-4.1', 'gpt-4o', 'gpt-5.5']
ALL_MODELS = ['gpt-4o-mini', 'gpt-4.1', 'gpt-4o', 'gpt-5.5', 'claude-sonnet-4.5', 'gemini-2.5-pro']
DOMAINS = ['beer', 'amzbook']
DCOL = {'beer': '#1f77b4', 'amzbook': '#d62728'}
PERSONA_SHORT = {'p1-novice-skeptical': 'p1 novice-skeptical',
                 'p2-expert-trusting': 'p2 expert-trusting',
                 'p3-moderate-balanced': 'p3 moderate-balanced',
                 'p4-skilled-skeptical': 'p4 skilled-skeptical',
                 'p5-novice-trusting': 'p5 novice-trusting',
                 'p6-expert-moderate': 'p6 expert-moderate'}
FIGDIR = 'figures'


def save(fig, name):
    fig.tight_layout()
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(FIGDIR, f'{name}.{ext}'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('wrote', name)


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
    ax.set_xlabel('capability ladder (same provider, identical config)')
    ax.set_ylim(0, 1)
    ax.set_title('Axis-2 wrong-AI over-reliance is model-idiosyncratic;\nthe frontier resists (both domains)')
    ax.legend(title='domain')
    save(fig, 'fig1_axis2_ladder')


def fig2_persona_heatmap(df):
    pr = persona_rates(df)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    for ax, dom in zip(axes, DOMAINS):
        M = np.array([[pr[(dom, m, p)] for m in ALL_MODELS] for p in PERSONAS])
        im = ax.imshow(M, cmap='magma', vmin=0, vmax=1, aspect='auto')
        ax.set_xticks(range(len(ALL_MODELS)))
        ax.set_xticklabels(ALL_MODELS, rotation=40, ha='right', fontsize=8)
        ax.set_yticks(range(len(PERSONAS)))
        ax.set_yticklabels([PERSONA_SHORT[p] for p in PERSONAS], fontsize=8)
        for i in range(len(PERSONAS)):
            for j in range(len(ALL_MODELS)):
                ax.text(j, i, f'{M[i, j]:.2f}', ha='center', va='center', fontsize=7,
                        color='white' if M[i, j] < 0.6 else 'black')
        # highlight the p5 row
        p5i = PERSONAS.index(TARGET)
        ax.add_patch(plt.Rectangle((-0.5, p5i - 0.5), len(ALL_MODELS), 1, fill=False,
                                   edgecolor='cyan', lw=2))
        ax.set_title(dom)
    fig.suptitle('Persona × model dark-adoption: p5 (novice-trusting) is the top-adopting persona in every cell (12/12)',
                 fontsize=11)
    fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02, label='wrong-AI adoption')
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(FIGDIR, f'fig2_persona_heatmap.{ext}'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('wrote fig2_persona_heatmap')


def _axis1_disagreement():
    """(domain, model) -> mean panel disagreement across 5 conditions."""
    files = {'beer': 'results/confirmatory_axis1_capladder.json',
             'amzbook': 'results/confirmatory_axis1_capladder_amzbook.json'}
    out = {}
    for dom, path in files.items():
        d = json.load(open(path))
        for m in LADDER:
            tbl = d['per_model'][m]['aligned_per_condition_table']
            out[(dom, m)] = float(np.mean([r['panel_disagreement'] for r in tbl]))
    return out


def fig3_axis1_collapse():
    dis = _axis1_disagreement()
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    x = np.arange(len(LADDER))
    for dom in DOMAINS:
        y = [dis[(dom, m)] for m in LADDER]
        ax.plot(x, y, marker='s', lw=2, color=DCOL[dom], label=dom)
    ax.annotate('frontier collapses\nto near-homogeneity', xy=(3, dis[('beer', 'gpt-5.5')]),
                xytext=(1.6, 0.15), arrowprops=dict(arrowstyle='->', color='black'),
                fontsize=9, ha='center')
    ax.set_xticks(x); ax.set_xticklabels(LADDER, rotation=15)
    ax.set_ylabel('mean panel disagreement (axis-1 heterogeneity)')
    ax.set_xlabel('capability ladder')
    ax.set_ylim(0, max(dis.values()) * 1.15)
    ax.set_title('Axis-1 panel heterogeneity collapses at the frontier (both domains)')
    ax.legend(title='domain')
    save(fig, 'fig3_axis1_collapse')


def fig4_rate_vs_ordering(df):
    cr = cell_rates(df)
    pr = persona_rates(df)
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 4.4))
    # LEFT: aggregate rate per model (idiosyncrasy) — grouped bars
    x = np.arange(len(ALL_MODELS))
    w = 0.38
    for i, dom in enumerate(DOMAINS):
        vals = [cr[(dom, m)][2] for m in ALL_MODELS]
        axL.bar(x + (i - 0.5) * w, vals, w, color=DCOL[dom], label=dom)
    axL.axhline(0.5, ls='--', color='gray', lw=1)
    axL.set_xticks(x); axL.set_xticklabels(ALL_MODELS, rotation=40, ha='right', fontsize=8)
    axL.set_ylabel('aggregate wrong-AI over-reliance')
    axL.set_title('Aggregate RATE is model-idiosyncratic\n(beer range 0.30, amzbook range 0.51)')
    axL.legend(title='domain', fontsize=8)
    axL.set_ylim(0, 1)
    # RIGHT: persona ordering profiles overlaid (beer), independent vendors — ordering agrees
    vendors = ['gpt-5.5', 'claude-sonnet-4.5', 'gemini-2.5-pro']
    vcol = {'gpt-5.5': '#2ca02c', 'claude-sonnet-4.5': '#9467bd', 'gemini-2.5-pro': '#ff7f0e'}
    xp = np.arange(len(PERSONAS))
    for m in vendors:
        y = [pr[('beer', m, p)] for p in PERSONAS]
        axR.plot(xp, y, marker='o', lw=1.8, color=vcol[m], label=m)
    axR.set_xticks(xp)
    axR.set_xticklabels([p.split('-', 1)[0] for p in PERSONAS], fontsize=9)
    p5i = PERSONAS.index(TARGET)
    axR.axvline(p5i, ls=':', color='cyan', lw=2)
    axR.text(p5i, 1.02, 'p5', color='teal', ha='center', fontsize=9)
    axR.set_ylabel('dark adoption')
    axR.set_xlabel('persona')
    axR.set_title('Persona ORDERING agrees across independent vendors\n(beer mean pairwise Spearman 0.87)')
    axR.legend(fontsize=8)
    axR.set_ylim(0, 1.08)
    save(fig, 'fig4_rate_vs_ordering')


def fig5_decision_flip(df):
    """Same dark interface, per-backend aggregate risk with a decision threshold: some backends flag,
    some clear -> the decision flips across backends."""
    cr = cell_rates(df)
    thr = 0.5
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharex=True)
    for ax, dom in zip(axes, DOMAINS):
        vals = [(m, cr[(dom, m)][2]) for m in ALL_MODELS]
        vals.sort(key=lambda t: t[1])
        names = [m for m, _ in vals]
        rates = [r for _, r in vals]
        colors = ['#d62728' if r >= thr else '#2ca02c' for r in rates]  # red=flag, green=clear
        y = np.arange(len(names))
        ax.barh(y, rates, color=colors)
        ax.axvline(thr, ls='--', color='black', lw=1.2)
        ax.text(thr + 0.01, -0.6, r'threshold $\tau=0.5$', fontsize=8, va='top')
        for yi, r in zip(y, rates):
            ax.text(r + 0.01, yi, f'{r:.2f}', va='center', fontsize=8)
        ax.set_yticks(y); ax.set_yticklabels(names, fontsize=8)
        n_flag = sum(r >= thr for r in rates)
        ax.set_title(f'{dom}: {n_flag}/6 flag, {6-n_flag}/6 clear')
        ax.set_xlim(0, 1.0)
        ax.set_xlabel('aggregate wrong-advice adoption (same dark interface)')
    from matplotlib.patches import Patch
    axes[1].legend(handles=[Patch(color='#d62728', label=r'flag ($\geq\tau$)'),
                            Patch(color='#2ca02c', label=r'clear ($<\tau$)')],
                   fontsize=8, loc='lower right')
    fig.suptitle('The same interface, flipped: backends disagree on the risk decision '
                 '(pairwise flip rate 0.60 beer / 0.33 amzbook)', fontsize=11)
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(FIGDIR, f'fig5_decision_flip.{ext}'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('wrote fig5_decision_flip')


def main():
    os.makedirs(FIGDIR, exist_ok=True)
    df = load_dark_records()
    fig1_axis2_ladder(df)
    fig2_persona_heatmap(df)
    fig3_axis1_collapse()
    fig4_rate_vs_ordering(df)
    fig5_decision_flip(df)
    print('all figures ->', FIGDIR)


if __name__ == '__main__':
    main()
