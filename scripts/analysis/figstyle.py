"""Shared publication-quality figure style for the CHI paper (Two Ways a Design Fails).

Single source of truth for the visual language of every main-text figure: typography, palette,
spines, grid, legends, error bars, annotations and saving. Figure text uses a Times-compatible
serif to match the acmart body; math uses STIX.

Palette rationale (colorblind- and print-safe)
---------------------------------------------
The two primary series (``beer`` / ``amzbook``) sit on the blue--orange axis, the one axis that
survives every common form of colour-vision deficiency. We use *deepened, desaturated* variants of
Okabe--Ito blue and vermillion -- petrol teal ``#00607B`` and burnt sienna ``#B4521A`` -- rather
than the saturated originals: they keep the same hue separation and add a lightness separation
(L* ~ 38 vs ~ 45), so they remain distinguishable in greyscale print, and they read as calmer and
more considered than primary blue/orange on a white page. Every accent colour is chosen dark enough
to survive an uncoated print run: no neon, no pale pastels on white. Marker shape is redundantly
encoded everywhere (beer = circle, amzbook = square) so colour is never the only channel.

Usage::

    import figstyle
    figstyle.apply()
    fig, ax = plt.subplots(figsize=figstyle.FIG_1COL)
    ...
    figstyle.style_axis(ax, grid='y')
    figstyle.legend(ax, title='dataset', loc='lower right')
    figstyle.save(fig, 'figX_name')
"""
import os

import matplotlib as mpl
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- core palette
INK = '#16181A'          # near-black for text (softer than pure black in print)
SUBTLE = '#5A6068'       # secondary text / annotation ink
FAINT = '#8A9096'        # tertiary: reference lines, de-emphasised marks
SPINE = '#4A5056'
GRIDCLR = '#DFE3E6'
PAPER = '#FFFFFF'

TEAL = '#00607B'         # primary series A  (beer)
SIENNA = '#B4521A'       # primary series B  (amzbook)
VIRIDIAN = '#1F7A63'     # coverage-greedy (ours)
PLUM = '#8E4585'         # capability-first router (green/plum stays separable for deuteranopes)
GOLD = '#B07C00'         # highlight / at-risk emphasis
SLATE = '#4A6D8C'        # cool neutral series
CLAY = '#8C6B4F'         # warm neutral series
CRIMSON = '#8E1F2F'      # harmful end of the protective ramp

# Backwards-compatible Okabe--Ito names (older call-sites keep working), retuned to the deepened,
# print-safe variants above so the whole figure set moves together.
OKABE = dict(
    black=INK, orange=GOLD, skyblue=SLATE, green=VIRIDIAN, yellow='#C9A227',
    blue=TEAL, vermillion=SIENNA, purple=PLUM, grey=FAINT)

# ---------------------------------------------------------------- semantic maps
DATASET = {'beer': TEAL, 'amzbook': SIENNA}
DATASET_MARK = {'beer': 'o', 'amzbook': 's'}
DATASET_LS = {'beer': '-', 'amzbook': (0, (5, 2))}

GREEDY = VIRIDIAN        # coverage-greedy (ours)
ROUTER = PLUM            # capability-first (router)

# protective-condition severity ramp (harmful -> protected): red--blue diverging, monotone lightness
CONDITION = {'dark': CRIMSON, 'plain': '#C4784E', 'forcing': '#5B8FA8', 'verify': '#1F4E6B'}

# capability ladder (sequential, weak -> strong): perceptually ordered teals
LADDER_COLOR = ['#C6DAD9', '#98BEBD', '#66A0A2', '#357E88', TEAL]

# categorical ramp for the six backends: hue- and lightness-separated, all print-safe
BACKEND_CYCLE = [TEAL, SIENNA, VIRIDIAN, PLUM, GOLD, SLATE]

HEATMAP_CMAP = 'cividis'  # perceptually uniform and colourblind-safe

# ---------------------------------------------------------------- shared geometry / kwargs
FIG_1COL = (6.4, 3.9)
FIG_2COL = (11.0, 3.9)

MARKER_KW = dict(markeredgecolor=PAPER, markeredgewidth=0.9)
SCATTER_KW = dict(edgecolor=PAPER, linewidth=0.9)
ERRORBAR_KW = dict(capsize=2.4, capthick=0.9, elinewidth=1.0, alpha=0.9)
ARROW_KW = dict(arrowstyle='-|>', color=SUBTLE, lw=0.9, shrinkA=2, shrinkB=3, mutation_scale=8)
REFLINE_KW = dict(ls=(0, (4, 3)), color=FAINT, lw=0.9, zorder=1)

ANNOT_SIZE = 8.0
VALUE_SIZE = 8.0


def apply():
    """Set global rcParams for a calm, camera-ready look. Call once per script."""
    mpl.rcParams.update({
        # -- typography: Times-compatible serif to match acmart; STIX math -------------
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'STIXGeneral', 'Nimbus Roman', 'DejaVu Serif'],
        'mathtext.fontset': 'stix',
        'font.size': 9.5,
        'axes.titlesize': 10.0,
        'axes.titleweight': 'regular',
        'axes.titlelocation': 'left',   # titles align with the y-axis label: calmer hierarchy
        'axes.titlepad': 7.0,
        'axes.labelsize': 9.5,
        'axes.labelpad': 4.5,
        'xtick.labelsize': 8.5,
        'ytick.labelsize': 8.5,
        'legend.fontsize': 8.5,
        'legend.title_fontsize': 8.5,
        'figure.titlesize': 10.5,
        'figure.titleweight': 'regular',
        # -- framing: light, open, top/right dropped ----------------------------------
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.linewidth': 0.7,
        'axes.edgecolor': SPINE,
        'axes.labelcolor': INK,
        'text.color': INK,
        'figure.facecolor': PAPER,
        'axes.facecolor': PAPER,
        'savefig.facecolor': PAPER,
        # -- ticks: short, outward, unobtrusive ---------------------------------------
        'xtick.color': SPINE,
        'ytick.color': SPINE,
        'xtick.labelcolor': INK,
        'ytick.labelcolor': INK,
        'xtick.direction': 'out',
        'ytick.direction': 'out',
        'xtick.major.size': 2.8,
        'ytick.major.size': 2.8,
        'xtick.major.width': 0.7,
        'ytick.major.width': 0.7,
        'xtick.major.pad': 3.0,
        'ytick.major.pad': 3.0,
        'axes.formatter.use_mathtext': True,   # tick numerals in STIX, matching inline math
        'axes.formatter.useoffset': False,
        # -- grid: a single soft guide ------------------------------------------------
        'axes.grid': True,
        'axes.grid.axis': 'y',
        'grid.color': GRIDCLR,
        'grid.linewidth': 0.6,
        'grid.alpha': 1.0,
        'axes.axisbelow': True,
        # -- lines / markers ----------------------------------------------------------
        'lines.linewidth': 1.6,
        'lines.markersize': 5.5,
        'lines.markeredgewidth': 0.9,
        'lines.solid_capstyle': 'round',
        'patch.linewidth': 0.7,
        'errorbar.capsize': 2.4,
        # -- legend: light, quiet ------------------------------------------------------
        'legend.frameon': True,
        'legend.framealpha': 0.94,
        'legend.facecolor': PAPER,
        'legend.edgecolor': GRIDCLR,
        'legend.borderpad': 0.45,
        'legend.labelspacing': 0.38,
        'legend.handlelength': 1.5,
        'legend.handletextpad': 0.6,
        'legend.borderaxespad': 0.5,
        'legend.columnspacing': 1.2,
        # -- layout / output -----------------------------------------------------------
        'figure.dpi': 150,
        'savefig.dpi': 400,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.04,
        'pdf.fonttype': 42,   # embed TrueType (editable/searchable text in the PDF)
        'ps.fonttype': 42,
        'axes.prop_cycle': mpl.cycler(color=BACKEND_CYCLE + [CLAY, INK]),
    })


# ---------------------------------------------------------------- axis helpers
def style_axis(ax, grid='y'):
    """Consistent per-axis hygiene: drop top/right spines, soften the rest, set the guide grid.

    ``grid`` is one of 'y' (default), 'x', 'both' or None.
    """
    ax.spines[['top', 'right']].set_visible(False)
    for s in ('left', 'bottom'):
        if s in ax.spines:
            ax.spines[s].set_color(SPINE)
            ax.spines[s].set_linewidth(0.7)
    ax.tick_params(direction='out', length=2.8, width=0.7, color=SPINE, labelcolor=INK, pad=3.0)
    ax.grid(False)
    if grid in ('y', 'both'):
        ax.grid(True, axis='y', color=GRIDCLR, linewidth=0.6, zorder=0)
    if grid in ('x', 'both'):
        ax.grid(True, axis='x', color=GRIDCLR, linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    return ax


def hide_spines(ax, spines=('top', 'right', 'left')):
    for s in spines:
        ax.spines[s].set_visible(False)
    return ax


def legend(ax, handles=None, title=None, loc='best', ncol=1, frameon=True, **kw):
    """One legend treatment everywhere: hairline frame, quiet title, generous padding."""
    kw.setdefault('borderpad', 0.45)
    kw.setdefault('labelspacing', 0.38)
    kw.setdefault('handletextpad', 0.6)
    if handles is not None:
        lg = ax.legend(handles=handles, title=title, loc=loc, ncol=ncol, frameon=frameon, **kw)
    else:
        lg = ax.legend(title=title, loc=loc, ncol=ncol, frameon=frameon, **kw)
    if lg is None:
        return None
    fr = lg.get_frame()
    fr.set_linewidth(0.6)
    fr.set_edgecolor(GRIDCLR)
    fr.set_facecolor(PAPER)
    fr.set_alpha(0.94)
    if lg.get_title() is not None:
        lg.get_title().set_color(SUBTLE)
    for t in lg.get_texts():
        t.set_color(INK)
    return lg


def annotate(ax, text, xy, xytext, color=None, size=ANNOT_SIZE, ha='center', va='center',
             arrow=True, **kw):
    """Consistent callout: quiet ink, thin tapered leader, one type size everywhere."""
    color = color or SUBTLE
    ap = dict(ARROW_KW)
    ap['color'] = color
    return ax.annotate(text, xy=xy, xytext=xytext, fontsize=size, color=color, ha=ha, va=va,
                       linespacing=1.25, arrowprops=ap if arrow else None, **kw)


def value_label(ax, x, y, text, color=None, size=VALUE_SIZE, ha='center', va='center', **kw):
    """Consistent in-plot numeric label."""
    return ax.text(x, y, text, fontsize=size, color=color or INK, ha=ha, va=va, **kw)


def refline(ax, value, axis='y', **kw):
    """A consistent, recessive reference line (chance level, threshold, ceiling)."""
    k = dict(REFLINE_KW)
    k.update(kw)
    return ax.axhline(value, **k) if axis == 'y' else ax.axvline(value, **k)


def note(ax, x, y, text, size=7.8, color=None, **kw):
    """Small quiet marginal note (units, reference-line captions, caveats)."""
    return ax.text(x, y, text, fontsize=size, color=color or FAINT, **kw)


def panel_title(ax, text, size=None):
    """Left-aligned panel title in the shared hierarchy."""
    ax.set_title(text, loc='left', fontsize=size or mpl.rcParams['axes.titlesize'], color=INK)
    return ax


def suptitle(fig, text, y=1.02, size=None):
    """Figure-level caption line: left-aligned to the figure, quiet ink, one notch up in size."""
    return fig.suptitle(text, y=y, x=0.0, ha='left',
                        fontsize=size or mpl.rcParams['figure.titlesize'], color=INK)


def save(fig, name, figdir='figures'):
    """Write the vector PDF plus a raster preview under the same basename."""
    os.makedirs(figdir, exist_ok=True)
    fig.savefig(os.path.join(figdir, f'{name}.png'), bbox_inches='tight')
    fig.savefig(os.path.join(figdir, f'{name}.pdf'), bbox_inches='tight')
    plt.close(fig)
    print('wrote', name)
