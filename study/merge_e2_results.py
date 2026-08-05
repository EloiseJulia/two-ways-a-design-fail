"""Merge exact-stimulus E2 results into a six-backend human-comparison table.

Four same-provider ladder backends are newly rerun on all three matched human
framings. The proxy no longer serves the paper's original Claude/Gemini models,
so for those two backends we extract the exact 12-item subset of the already
completed n50 static-dark condition. Static dark is identical across the old and
human-match runs (guaranteed-wrong advice, 92% confidence, same coercive text).

Output:
  results/e2_human_match_summary.json
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
STIMULI = ROOT / "study" / "stimuli"

LADDER_MODELS = ("gpt-4o-mini", "gpt-4.1", "gpt-4o", "gpt-5.5")
VENDOR_MODELS = ("claude-sonnet-4.5", "gemini-2.5-pro")
NEW_CONDITIONS = {
    "Wrong-AI-GT (neutral92)": "neutral",
    "Wrong-AI-GT (placebo92)": "placebo",
    "Wrong-AI-GT (dark)": "dark",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def selected_ids(domain: str) -> set[str]:
    payload = load(STIMULI / f"stimuli_{domain}.json")
    return {str(row["task_id"]) for row in payload["main"]}


def summarize(rows: list[dict]) -> dict:
    adopted = [
        int(str(r["final_decision"]) == str(r["trace"].get("ai_advice")))
        for r in rows
    ]
    correct = [
        r for r in rows
        if str(r["system1_decision"]) == str(r["trace"].get("ground_truth"))
    ]
    flipped = [
        int(str(r["final_decision"]) == str(r["trace"].get("ai_advice")))
        for r in correct
    ]
    p5 = [
        a for r, a in zip(rows, adopted)
        if r["persona_id"] == "p5-novice-trusting"
    ]
    return {
        "n": len(rows),
        "adoption": sum(adopted) / len(adopted) if adopted else None,
        "n_system1_correct": len(correct),
        "flip_from_correct": sum(flipped) / len(flipped) if flipped else None,
        "p5_adoption": sum(p5) / len(p5) if p5 else None,
    }


def main() -> None:
    summary: dict[str, dict] = {}
    provenance: dict[str, str] = {}

    for domain in ("beer", "amzbook"):
        ids = selected_ids(domain)
        ladder = load(RESULTS / f"e2_human_match_{domain}_capladder.json")
        old_vendor = load(
            RESULTS
            / (
                "axis2_powered_crossvendor_amzbook_n50.json"
                if domain == "amzbook"
                else "axis2_powered_crossvendor_n50.json"
            )
        )
        summary[domain] = {}

        # New exact 3-condition ladder results.
        for model in LADDER_MODELS:
            summary[domain][model] = {}
            for raw_cond, short_cond in NEW_CONDITIONS.items():
                rows = [
                    r for r in ladder["responses"]
                    if r["model"] == model and r["ui_condition"] == raw_cond
                ]
                summary[domain][model][short_cond] = summarize(rows)
            provenance[f"{domain}|{model}"] = "new exact 3-condition rerun"

        # Old vendors: exact item subset, static dark only.
        for model in VENDOR_MODELS:
            rows = [
                r for r in old_vendor["responses"]
                if r["model"] == model
                and r["ui_condition"] == "Wrong-AI-GT (dark)"
                and str(r["task_id"]) in ids
            ]
            summary[domain][model] = {
                "neutral": None,
                "placebo": None,
                "dark": summarize(rows),
            }
            provenance[f"{domain}|{model}"] = (
                "extracted exact 12-item static-dark subset from n50; "
                "old model unavailable for new neutral/placebo calls"
            )

    out = {
        "description": (
            "Six-backend exact-human-item comparison. Four ladder backends have "
            "all matched framings; original Claude/Gemini have exact static-dark "
            "subsets only because the proxy no longer serves those models."
        ),
        "summary": summary,
        "provenance": provenance,
    }
    path = RESULTS / "e2_human_match_summary.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")
    for domain, models in summary.items():
        print(f"\n{domain}")
        for model, conds in models.items():
            d = conds["dark"]
            print(
                f"  {model:22s} dark adoption={d['adoption']:.3f} "
                f"flip={d['flip_from_correct']:.3f} p5={d['p5_adoption']:.3f} "
                f"n={d['n']}"
            )


if __name__ == "__main__":
    main()
