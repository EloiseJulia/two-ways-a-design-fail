"""D5.36 Experiment M runner — multi-generation generation-stochasticity arm.

Loops over `generation_seeds`, running the axis-2 panel (Conf. + dark) for each model at each generation
seed, and saves raw responses tagged with `gen_seed`. Reuses the axis2_powered building blocks and the
cache-backed provider (resumable: re-running skips cached calls). Serial, throttled (config
inter_call_sleep). Output: results/multigen_axis2.json (rewritten after every model×gen slice).

Run detached:
    python -u scripts/analysis/run_multigen.py --config configs/multigen_axis2.yaml
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import yaml

from twdf.experiments.axis2_powered import (
    _personas_from_config, build_tasks, build_provider, _serialize_response,
)
from twdf.experiments.provider_factory import model_names_from_config
from twdf.panel.real_panel import run_panel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    config = yaml.safe_load(open(args.config, encoding="utf-8"))

    personas = _personas_from_config(config)
    tasks = list({t.task_id: t for t in build_tasks(config)}.values())
    ui_conditions = tuple(config["ui_conditions"])
    gen_seeds = config["generation_seeds"]
    models = model_names_from_config(config)
    out_path = Path(config["output_file"])

    all_rows = []
    done = set()  # (model, gen) slices already collected (for in-process idempotency)
    failed = []
    start = time.time()
    total_slices = len(models) * len(gen_seeds)
    k = 0

    def run_slice(model_name, provider, gen):
        t0 = time.time()
        responses = run_panel(
            personas=personas, tasks=tasks, ui_pair=ui_conditions,
            providers=[provider], seeds=[gen], mode=config["mode"],
        )
        for r in responses:
            row = _serialize_response(r)
            row["gen_seed"] = gen
            all_rows.append(row)
        done.add((model_name, gen))
        return len(responses), time.time() - t0

    def save(kk):
        manifest = {
            "experiment_name": config["experiment_name"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "models": models, "generation_seeds": gen_seeds,
            "ui_conditions": list(ui_conditions), "item_seed": config["item_selection"]["seed"],
            "n_personas": len(personas), "n_tasks": len(tasks),
            "slices_done": len(done), "total_slices": total_slices,
            "failed_slices": [f"{m}|{g}" for (m, g) in failed],
            "n_responses": len(all_rows), "wall_time_seconds": time.time() - start,
        }
        json.dump({"run_manifest": manifest, "responses": all_rows},
                  open(out_path, "w", encoding="utf-8"), indent=2)

    for model_name in models:
        provider = build_provider(config, model_name)
        for gen in gen_seeds:
            k += 1
            if (model_name, gen) in done:
                continue
            try:
                n, dt = run_slice(model_name, provider, gen)
                save(k)
                print(f"[{k}/{total_slices}] {model_name} gen={gen}: +{n} rows "
                      f"(total {len(all_rows)}) in {dt:.0f}s", flush=True)
            except Exception as e:
                failed.append((model_name, gen))
                save(k)
                print(f"[{k}/{total_slices}] {model_name} gen={gen}: FAILED ({e}); continuing", flush=True)

    # one retry pass over failed slices (transient upstream errors)
    if failed:
        print(f"Retrying {len(failed)} failed slices...", flush=True)
        retry = list(failed)
        failed.clear()
        for model_name, gen in retry:
            provider = build_provider(config, model_name)
            try:
                n, dt = run_slice(model_name, provider, gen)
                save(0)
                print(f"[retry] {model_name} gen={gen}: +{n} rows in {dt:.0f}s", flush=True)
            except Exception as e:
                failed.append((model_name, gen))
                save(0)
                print(f"[retry] {model_name} gen={gen}: FAILED AGAIN ({e})", flush=True)

    print(f"DONE: {len(all_rows)} responses -> {out_path} in {time.time()-start:.0f}s "
          f"({len(failed)} slices still failed: {failed})", flush=True)


if __name__ == "__main__":
    main()
