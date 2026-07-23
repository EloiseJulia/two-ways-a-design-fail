"""Shared publication-quality figure style for the CHI paper (Two Ways a Design Fails).

A single place that sets matplotlib rcParams and a consistent, colorblind-safe visual language so all
figures share fonts, colors, spines, grid, and sizing. Palette = Okabe--Ito (colorblind-safe); figure
text uses a Times-compatible serif to match the acmart body text.

Usage:
    import figstyle
    figstyle.apply()
    ... figstyle.DATASET['beer'] ...
"""
import matplotlib as mpl
import matplotlib.pyplot as plt

# ---- Okabe--Ito colorblind-safe palette ----
OKABE = dict(
    black='#000000', orange='#E69F00', skyblue='#56B4E9', green='#009E73',
    yellow='#F0E442', blue='#0072B2', vermillion='#D55E00', purple='#CC79A7', grey='#9A9A9A')

# ---- semantic maps (consistent across every figure) ----
DATASET = {'beer': OKABE['blue'], 'amzbook': OKABE['vermillion']}
DATASET_MARK = {'beer': 'o', 'amzbook': 's'}
GREEDY = OKABE['green']        # coverage-greedy (ours)
ROUTER = OKABE['vermillion']   # capability-first (router)
# protective-condition severity ramp (harmful red -> protected blue), colorblind-friendly diverging
CONDITION = {'dark': '#9E1B32', 'plain': '#E8896A', 'forcing': '#5AA0C8', 'verify': '#20558A'}
# capability ladder (sequential, weak -> strong): perceptually ordered blues/greens
LADDER_COLOR = ['#BFD3C1', '#88B7A6', '#4E9C87', '#2E7C6E', '#0072B2']
HEATMAP_CMAP = 'cividis'       # perceptually-uniform, colorblind-safe
GRIDCLR = '#D9D9D9'


def apply():
    """Set global rcParams for a clean, professional, camera-ready look."""
    mpl.rcParams.update({
        # typography: Times-compatible serif to match the acmart body; STIX math
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'STIXGeneral', 'DejaVu Serif'],
        'mathtext.fontset': 'stix',
        'font.size': 10,
        'axes.titlesize': 10.5,
        'axes.labelsize': 10,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 8.5,
        'figure.titlesize': 11.5,
        # spines: drop top/right for a lighter frame
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.linewidth': 0.8,
        'axes.edgecolor': '#4D4D4D',
        'axes.labelcolor': '#1A1A1A',
        'text.color': '#1A1A1A',
        'xtick.color': '#4D4D4D',
        'ytick.color': '#4D4D4D',
        'xtick.direction': 'out',
        'ytick.direction': 'out',
        'xtick.major.size': 3.0,
        'ytick.major.size': 3.0,
        # grid: light horizontal guide only
        'axes.grid': True,
        'axes.grid.axis': 'y',
        'grid.color': GRIDCLR,
        'grid.linewidth': 0.7,
        'grid.alpha': 0.9,
        'axes.axisbelow': True,
        # lines / markers
        'lines.linewidth': 1.8,
        'lines.markersize': 5.5,
        'lines.markeredgewidth': 0.8,
        # legend
        'legend.frameon': True,
        'legend.framealpha': 0.92,
        'legend.edgecolor': '#CCCCCC',
        'legend.borderpad': 0.4,
        'legend.handlelength': 1.6,
        # output
        'figure.dpi': 150,
        'savefig.dpi': 400,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.03,
        'pdf.fonttype': 42,   # embed TrueType (editable/searchable text in the PDF)
        'ps.fonttype': 42,
        'axes.prop_cycle': mpl.cycler(color=[
            OKABE['blue'], OKABE['vermillion'], OKABE['green'], OKABE['orange'],
            OKABE['purple'], OKABE['skyblue'], OKABE['yellow'], OKABE['black']]),
    })


def style_axis(ax):
    """Per-axis cleanups that rcParams cannot express (call after plotting)."""
    ax.tick_params(length=3.0, width=0.8)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color('#4D4D4D')
    return ax
