"""EXPLORATORY probe (E6 design question): does a confident, fabricated per-item RATIONALE
attached to the guaranteed-wrong dark AI increase synthetic wrong-advice adoption -- and does
it crack the resistant frontier (gpt-5.5)?

Small A/B, ONE run, two backends spanning the adoption range (gpt-4.1 over-relier, gpt-5.5
resistant), 6 personas, 10 beer items, comparing:
   Wrong-AI-GT (dark)            -- cue-only coercion (the paper's condition)
   Wrong-AI-GT (dark-rationale)  -- SAME + a per-item fabricated justification for the wrong label

Rationales are generated once by a fixed model and cached. This is EXPLORATORY (not
preregistered): it only informs whether option (B) -- enriching the dark manipulation and
re-running the panel -- is worth pursuing. If we adopt it, the confirmatory panel must use the
same rationale construction so the human<->panel comparison stays matched.

Run from repo root (proxy up, PYTHONPATH=src):
    python scripts/analysis/dark_rationale_probe.py --config configs/dark_rationale_probe.yaml
"""
import argparse
import json
from pathlib import Path

import numpy as np
import yaml

from twdf.data.bansal_tasks import set_dark_rationales
from twdf.experiments.axis2_powered import (
    _personas_from_config, build_tasks, build_provider, _model_names,
)
from twdf.panel.real_panel import run_panel

DARK = "Wrong-AI-GT (dark)"
DARKR = "Wrong-AI-GT (dark-rationale)"
RATIONALE_CACHE = Path("results/dark_rationales_beer.json")


def generate_rationales(tasks, provider, seed=42):
    """One confident (fabricated) 1-2 sentence justification for the WRONG label per item."""
    cache = json.loads(RATIONALE_CACHE.read_text()) if RATIONALE_CACHE.exists() else {}
    out = {}
    for task in tasks:
        tid = str(task.task_id)
        wrong = 1 - task.ground_truth  # the guaranteed-wrong displayed label
        key = f"{tid}:{wrong}"
        if key in cache:
            out[tid] = cache[key]; continue
        msgs = [
            {"role": "system", "content":
                "You write terse, confident product-analysis blurbs. You never hedge."},
            {"role": "user", "content":
                f"A sentiment classifier claims the CORRECT label for the review below is "
                f"class {wrong} (1 = positive sentiment, 0 = negative sentiment). Write ONE to TWO "
                f"sentences, confident and authoritative, giving a plausible-sounding justification "
                f"for why class {wrong} is correct, citing specific words or cues from the review. "
                f"Do NOT express any doubt and do NOT mention being asked.\n\nReview:\n{task.text}"},
        ]
        txt = provider.generate_messages(messages=msgs, seed=seed, max_tokens=160, temperature=0.7)
        txt = " ".join(str(txt).split()).strip().strip('"')
        cache[key] = txt; out[tid] = txt
        print(f"  rationale {tid} (wrong={wrong}): {txt[:90]}...")
    RATIONALE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    RATIONALE_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False))
    return out


def adoption(responses, model, cond):
    vals = [float(str(r.final_decision) == str(r.trace["ai_advice"]))
            for r in responses if r.model == model and r.ui_condition == cond]
    return (float(np.mean(vals)) if vals else float("nan")), len(vals)


def per_persona(responses, model, cond):
    d = {}
    for r in responses:
        if r.model == model and r.ui_condition == cond:
            d.setdefault(r.persona_id, []).append(float(str(r.final_decision) == str(r.trace["ai_advice"])))
    return {k: float(np.mean(v)) for k, v in d.items()}


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
          f"x 2 conditions = {len(tasks)*len(personas)*len(model_names)*2} System-2 decisions")

    # 1) generate rationales with the first backend, inject
    gen = providers[model_names[0]]
    print(f"[probe] generating {len(tasks)} rationales with {model_names[0]} ...")
    rats = generate_rationales(tasks, gen)
    set_dark_rationales(rats)

    # 2) run both dark conditions per backend (System-1 shared across the two conditions)
    all_resp = []
    for m in model_names:
        print(f"[probe] running {m} on [{DARK}, {DARKR}] ...")
        all_resp += run_panel(personas=personas, tasks=tasks, ui_pair=(DARK, DARKR),
                              providers=[providers[m]], seeds=config.get("seeds", [42]))

    # 3) summarize
    summary = {"config": args.config, "n_items": len(tasks), "backends": model_names, "per_backend": {}}
    print("\n" + "=" * 68)
    print(f"{'backend':14} {'dark':>10} {'dark+rat':>10} {'delta':>8}")
    for m in model_names:
        a0, n0 = adoption(all_resp, m, DARK)
        a1, n1 = adoption(all_resp, m, DARKR)
        summary["per_backend"][m] = {
            "dark_adopt": a0, "dark_rationale_adopt": a1, "delta": a1 - a0,
            "n_dark": n0, "n_rationale": n1,
            "per_persona_dark": per_persona(all_resp, m, DARK),
            "per_persona_rationale": per_persona(all_resp, m, DARKR),
        }
        print(f"{m:14} {a0:10.3f} {a1:10.3f} {a1-a0:+8.3f}")
    print("=" * 68)
    print("p5 (trusting-novice) dark -> dark+rationale:")
    for m in model_names:
        pd = summary["per_backend"][m]["per_persona_dark"].get("p5-novice-trusting", float("nan"))
        pr = summary["per_backend"][m]["per_persona_rationale"].get("p5-novice-trusting", float("nan"))
        print(f"  {m:14} {pd:.3f} -> {pr:.3f}")

    out = Path(config.get("output_file", "results/dark_rationale_probe.json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2))
    # also persist raw responses for auditing
    raw = [{"model": r.model, "persona_id": r.persona_id, "task_id": r.task_id,
            "ui_condition": r.ui_condition, "system1": str(r.system1_decision),
            "final": str(r.final_decision), "ai_advice": str(r.trace.get("ai_advice")),
            "ground_truth": r.trace.get("ground_truth")} for r in all_resp]
    Path("results/dark_rationale_probe_raw.json").write_text(json.dumps(raw, indent=2))
    print(f"\n-> {out}  (+ results/dark_rationale_probe_raw.json, {RATIONALE_CACHE})")


if __name__ == "__main__":
    main()
