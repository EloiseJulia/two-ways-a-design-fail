"""EXPLORATORY probe: does over-reliance differentiation survive a DISPOSITIONAL persona
(no explicit AI-deference decision policy)?  Addresses the persona-circularity critique.

We run 6 dispositional personas (prompt_style="dispositional": only experience / AI-use /
self-confidence are stated, with an identical decision instruction and NO "trust the AI"
policy) plus 2 policy anchors (p4 skeptic, p5 trusting-novice) on the guaranteed-wrong dark
condition, across 4 capability-spanning backends, on the same beer held-out items.

Reported per backend:
  - adoption for each persona
  - dispositional gap  d1(defer,low-conf) - d2(indep,high-conf)
  - policy gap         p5(trusting) - p4(skeptic)          [matched baseline]
  - one-facet contrasts around the deferential anchor d1:
        confidence  d1 - d6   (both low-exp/high-use; differ only in self-confidence)
        experience  d1 - d5   (both high-use/low-conf; differ only in experience)
        AI-use      d1 - d4   (both low-exp/low-conf; differ only in AI-use frequency)
  - Spearman rank stability of the persona ordering across backends (mean pairwise rho)

Run from repo root (proxy up, PYTHONPATH=src):
    python scripts/analysis/dispositional_probe.py --config configs/dispositional_ablation.yaml
"""
import argparse
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import spearmanr

from twdf.experiments.axis2_powered import (
    _personas_from_config, build_tasks, build_provider, _model_names,
)
from twdf.panel.real_panel import run_panel

DARK = "Wrong-AI-GT (dark)"


def per_persona(responses, model, cond):
    d = {}
    for r in responses:
        if r.model == model and r.ui_condition == cond:
            d.setdefault(r.persona_id, []).append(
                float(str(r.final_decision) == str(r.trace["ai_advice"])))
    return {k: float(np.mean(v)) for k, v in d.items()}, {k: len(v) for k, v in d.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    config = yaml.safe_load(Path(args.config).read_text())

    personas = _personas_from_config(config)
    tasks = build_tasks(config)
    model_names = _model_names(config)
    providers = {m: build_provider(config, m) for m in model_names}
    print(f"[probe] {len(tasks)} items x {len(personas)} personas x {len(model_names)} backends "
          f"x 1 condition = {len(tasks)*len(personas)*len(model_names)} System-2 decisions")

    all_resp = []
    for m in model_names:
        print(f"[probe] running {m} on [{DARK}] ...", flush=True)
        all_resp += run_panel(personas=personas, tasks=tasks, ui_pair=(DARK,),
                              providers=[providers[m]], seeds=config.get("seeds", [42]))

    pids = [p.persona_id for p in personas]
    summary = {"config": args.config, "n_items": len(tasks), "backends": model_names,
               "personas": pids, "per_backend": {}}
    adopt_by_backend = {}
    print("\n" + "=" * 92)
    header = f"{'backend':22}" + "".join(f"{p.split('-')[0]:>7}" for p in pids)
    print(header)
    for m in model_names:
        ad, ns = per_persona(all_resp, m, DARK)
        adopt_by_backend[m] = ad
        def g(a, b):
            if a in ad and b in ad:
                return round(ad[a] - ad[b], 3)
            return None
        summary["per_backend"][m] = {
            "adopt": {k: round(v, 3) for k, v in ad.items()},
            "n": ns,
            "disp_gap_d1_d2": g("d1-defer-lowconf", "d2-indep-highconf"),
            "policy_gap_p5_p4": g("p5-novice-trusting", "p4-skilled-skeptical"),
            "facet_confidence_d1_d6": g("d1-defer-lowconf", "d6-novice-highuse-confident"),
            "facet_experience_d1_d5": g("d1-defer-lowconf", "d5-expert-highuse-unsure"),
            "facet_aiuse_d1_d4": g("d1-defer-lowconf", "d4-novice-lowuse-unsure"),
        }
        row = f"{m:22}" + "".join(f"{ad.get(p, float('nan')):7.2f}" for p in pids)
        print(row)
    print("=" * 92)
    print(f"{'':22}disp_gap(d1-d2)  policy_gap(p5-p4)  conf(d1-d6)  exp(d1-d5)  aiuse(d1-d4)")
    for m in model_names:
        b = summary["per_backend"][m]
        print(f"{m:22}{str(b['disp_gap_d1_d2']):>13}{str(b['policy_gap_p5_p4']):>18}"
              f"{str(b['facet_confidence_d1_d6']):>13}{str(b['facet_experience_d1_d5']):>12}"
              f"{str(b['facet_aiuse_d1_d4']):>14}")

    # rank stability of the dispositional ordering across backends (Spearman, disp personas only)
    disp = [p for p in pids if p.startswith("d")]
    vecs = []
    for m in model_names:
        ad = adopt_by_backend[m]
        if all(p in ad for p in disp):
            vecs.append([ad[p] for p in disp])
    rhos = []
    for i, j in combinations(range(len(vecs)), 2):
        rho, _ = spearmanr(vecs[i], vecs[j])
        if not np.isnan(rho):
            rhos.append(rho)
    summary["rank_stability_mean_spearman"] = round(float(np.mean(rhos)), 3) if rhos else None
    summary["rank_stability_pairwise"] = [round(float(x), 3) for x in rhos]
    print("=" * 92)
    print(f"dispositional-ordering rank stability (mean pairwise Spearman): "
          f"{summary['rank_stability_mean_spearman']}  pairs={summary['rank_stability_pairwise']}")

    out = Path(config.get("output_file", "results/dispositional_ablation.json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2))
    raw = [{"model": r.model, "persona_id": r.persona_id, "task_id": r.task_id,
            "ui_condition": r.ui_condition, "system1": str(r.system1_decision),
            "final": str(r.final_decision), "ai_advice": str(r.trace.get("ai_advice")),
            "ground_truth": r.trace.get("ground_truth")} for r in all_resp]
    Path("results/dispositional_ablation_raw.json").write_text(json.dumps(raw, indent=2))
    print(f"\n-> {out}  (+ results/dispositional_ablation_raw.json)")


if __name__ == "__main__":
    main()
