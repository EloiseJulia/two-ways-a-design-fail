"""Shared publication style for the paper-figure skill outputs.
Serif (Times), colorblind-safe Okabe-Ito palette, vector PDF, no in-figure titles.
Imported by the gen_pf_*.py scripts. Originals (fig1-8) are untouched; new files use the pf_ prefix.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FONT_SIZE = 10
DPI = 300
FIG_DIR = "."          # scripts are run from figures/
FORMAT = "pdf"

matplotlib.rcParams.update({
    "font.size": FONT_SIZE,
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "axes.labelsize": FONT_SIZE,
    "axes.titlesize": FONT_SIZE + 1,
    "xtick.labelsize": FONT_SIZE - 1,
    "ytick.labelsize": FONT_SIZE - 1,
    "legend.fontsize": FONT_SIZE - 1,
    "figure.dpi": DPI,
    "savefig.dpi": DPI,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.03,
    "axes.grid": False,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "text.usetex": False,
    "mathtext.fontset": "stix",
})

# Okabe-Ito colorblind-safe palette (matches the paper's data figures)
OKABE = {
    "blue":   "#0072B2",
    "orange": "#D55E00",
    "green":  "#009E73",
    "sky":    "#56B4E9",
    "yellow": "#E69F00",
    "purple": "#CC79A7",
    "gray":   "#6E6E6E",
}


def save_fig(fig, name, fmt=FORMAT):
    path = f"{FIG_DIR}/{name}.{fmt}"
    fig.savefig(path)
    print(f"Saved: {path}")
