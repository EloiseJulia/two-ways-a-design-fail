"""Generate exact-human-stimulus synthetic rerun configs.

Outputs four configs (capability ladder + independent vendors, two domains).
The cross-vendor arm excludes gpt-5.5 because it is already in the ladder arm.

Run:
  python study/make_e2_configs.py
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ROOT / "configs"
STIMULI = ROOT / "study" / "stimuli"


BASES = {
    ("beer", "capladder"): CONFIGS / "axis2_powered_capladder_n50.yaml",
    ("beer", "crossvendor"): CONFIGS / "axis2_powered_crossvendor_n50.yaml",
    ("amzbook", "capladder"): CONFIGS / "axis2_powered_capladder_amzbook_n50.yaml",
    ("amzbook", "crossvendor"): CONFIGS / "axis2_powered_crossvendor_amzbook_n50.yaml",
}


def main() -> None:
    for (domain, arm), base_path in BASES.items():
        cfg = yaml.safe_load(base_path.read_text(encoding="utf-8"))
        stimuli = json.loads(
            (STIMULI / f"stimuli_{domain}.json").read_text(encoding="utf-8")
        )
        task_ids = [int(row["task_id"]) for row in stimuli["main"]]

        cfg["experiment_name"] = "e2_human_match"
        cfg["description"] = (
            "Exact-stimulus synthetic rerun for the planned N=80 human validation: "
            "same 12 main items, guaranteed-wrong advice, fixed 92% confidence, "
            "neutral/placebo/static-dark framings."
        )
        cfg["exploratory_vs_confirmatory"] = "EXPLORATORY-EXACT-STIMULUS"
        cfg["analysis_mode"] = "human_match"
        cfg["ui_conditions"] = [
            "Wrong-AI-GT (neutral92)",
            "Wrong-AI-GT (placebo92)",
            "Wrong-AI-GT (dark)",
        ]
        cfg["domain"] = domain
        cfg["item_selection"] = {"task_ids": task_ids, "seed": 2024}
        cfg["output_file"] = f"results/e2_human_match_{domain}_{arm}.json"

        # gpt-5.5 is already in capladder; avoid duplicate calls in crossvendor.
        if arm == "crossvendor":
            cfg["models"] = [
                m for m in cfg["models"] if m["name"] != "gpt-5.5"
            ]
        cfg.setdefault("model_runtime", {})["max_retries"] = 20
        cfg.setdefault("provider", {})["max_retries"] = 20

        out = CONFIGS / f"e2_human_match_{domain}_{arm}.yaml"
        out.write_text(
            yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        print(
            f"wrote {out.relative_to(ROOT)}: {len(task_ids)} tasks, "
            f"{len(cfg['models'])} models, {len(cfg['ui_conditions'])} conditions"
        )


if __name__ == "__main__":
    main()
