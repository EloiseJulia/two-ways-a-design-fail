"""Vulnerability-coverage inversion (n=11), from results/expand12_analysis.json (adopt, tau=0.5).
Coverage-greedy reaches full coverage almost immediately; capability-first (a quality-optimal router's
order) needs nearly all backends. Reads data; vector PDF; no in-figure title.
"""
import json
import numpy as np
from paper_plot_style import plt, save_fig, OKABE

D = json.load(open("../results/expand12_analysis.json"))
cov = D["coverage"]["adopt_tau0.5"]
universe = cov["universe"]
def as_nums(v):
    return [int(x) for x in (v.split() if isinstance(v, str) else v)]
greedy = np.array(as_nums(cov["greedy_curve"]), dtype=float) / universe
capfirst = np.array(as_nums(cov["capability_curve"]), dtype=float) / universe
k = np.arange(1, len(greedy) + 1)

fig, ax = plt.subplots(figsize=(5.0, 3.4))
ax.step(k, greedy, where="post", color=OKABE["green"], lw=2.0,
        label=f"coverage-greedy (complete at $k={cov['greedy_k_full']}$)")
ax.step(k, capfirst, where="post", color=OKABE["orange"], lw=2.0, ls="--",
        label=f"capability-first / router (complete at $k={cov['capability_k_full']}$)")
ax.scatter(k, greedy, s=16, color=OKABE["green"], zorder=3)
ax.scatter(k, capfirst, s=16, color=OKABE["orange"], zorder=3)

# frontier's first pick covers almost nothing
ax.annotate("router's first pick\n(frontier) covers 1/9",
            (1, capfirst[0]), textcoords="offset points", xytext=(12, -2),
            fontsize=8, color=OKABE["gray"],
            arrowprops=dict(arrowstyle="-", color=OKABE["gray"], lw=0.6))

ax.set_xlabel("Panel size  $k$  (backends added in order)")
ax.set_ylabel("High-risk cells covered  (of %d)" % universe)
ax.set_xticks(k)
ax.set_ylim(0, 1.08)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.legend(frameon=False, loc="lower right", fontsize=8)
save_fig(fig, "pf_coverage_inversion")
