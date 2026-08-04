"""Export the FORMAL human-study stimulus set for the axis-2 (coercion) validation — Option A (sentiment).

Selection (addresses the "task too easy / AI advice useless" concern):
    Items are chosen in the *movable band* — reviews where real humans (Bansal CHI'21 no-AI "Human"
    condition) are usually right but NOT certain (per-item human accuracy near ~0.70). On these items a
    confident WRONG AI can plausibly pull a person off a correct answer, which is exactly where a coercive
    framing has room to operate. We pick the 6 items per ground-truth label whose human no-AI accuracy is
    closest to 0.70 within [0.55, 0.85] (falling back to nearest-to-0.70 if a label is under-filled), so
    each participant sees 12 items balanced 6 NEGATIVE / 6 POSITIVE.

    DISCLOSURE (preregistered): per-item human no-AI accuracy is used only to SELECT items (concentrating on
    ambiguous/movable loci). No human outcome is shown to participants or used as a predictor; item
    selection is not label leakage. Empirically these items are far from a floor: on Bansal's wrong-AI
    trials real humans adopted the wrong advice 27% (beer) / 30% (amzbook) of the time.

All three framings show the SAME guaranteed-wrong advice (displayed = 1 - ground_truth); only the framing
varies (neutral / placebo / dark), mirroring src/twdf/data/bansal_tasks.py::render_ui_condition.

Output: study/stimuli/stimuli_{beer,amzbook}.json  and  study/stimuli/stimuli_preview.md
Run:    $env:PYTHONPATH=(Resolve-Path .\src).Path ; python study/export_stimuli.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
OUT = os.path.join(HERE, "stimuli")
os.makedirs(OUT, exist_ok=True)

# Binary sentiment label names (VERIFY against the Bansal CHI'21 codebook before fielding).
LABELS = {0: "NEGATIVE", 1: "POSITIVE"}

PLACEBO_TEXT = (
    "The AI model analyzed the input using its trained parameters and generated "
    "this recommendation based on its internal confidence evaluation."
)
DARK_CONF = 0.92
N_PER_LABEL = 6          # 6 NEGATIVE + 6 POSITIVE = 12 items/domain
TARGET_ACC = 0.70        # movable-band centre (human no-AI accuracy)
BAND = (0.55, 0.85)

# Chinese localization of the AI-advice framings (review text itself stays English).
LABELS_ZH = {0: "\u8d1f\u9762", 1: "\u6b63\u9762"}  # NEGATIVE / POSITIVE
PLACEBO_TEXT_ZH = ("\u8be5 AI \u6a21\u578b\u57fa\u4e8e\u5176\u8bad\u7ec3\u53c2\u6570\u5206\u6790\u4e86\u8f93"
                   "\u5165\uff0c\u5e76\u4f9d\u636e\u5185\u90e8\u7f6e\u4fe1\u5ea6\u8bc4\u4f30\u751f\u6210\u4e86"
                   "\u6b64\u5efa\u8bae\u3002")


def render(condition: str, wrong_label: int, item_conf: float, lang: str = "en") -> str:
    """Participant-facing rendering of the AI-advice panel for one condition (en/zh)."""
    if lang == "zh":
        name = LABELS_ZH[wrong_label]
        if condition == "neutral":
            return f"AI \u5224\u65ad\uff1a{name}\nAI \u7f6e\u4fe1\u5ea6\uff1a{item_conf:.0%}"
        if condition == "placebo":
            return (f"AI \u5224\u65ad\uff1a{name}\nAI \u7f6e\u4fe1\u5ea6\uff1a{item_conf:.0%}\n\n"
                    f"\u8bf4\u660e\uff1a{PLACEBO_TEXT_ZH}")
        if condition == "dark":
            return (
                "\u26a0\ufe0f \u91cd\u8981\u51b3\u5b9a \u26a0\ufe0f\n\n"
                f"AI \u4e13\u5bb6\u7cfb\u7edf\u5efa\u8bae\uff1a{name}\n"
                f"AI \u7f6e\u4fe1\u5ea6\uff1a{DARK_CONF:.0%}\n\n"
                "\u91cd\u8981\u63d0\u793a\uff1a\u8be5 AI \u7cfb\u7edf\u5df2\u5728\u6570\u767e\u4e07\u4e2a"
                "\u6837\u672c\u4e0a\u8bad\u7ec3\uff0c\u5728\u5b9e\u9645\u751f\u4ea7\u73af\u5883\u4e2d\u8868"
                "\u73b0\u51fa\u5f88\u9ad8\u7684\u51c6\u786e\u7387\u3002\u504f\u79bb AI \u5efa\u8bae\u53ef"
                "\u80fd\u5bfc\u81f4\u6b21\u4f18\u7ed3\u679c\uff0c\u5e76\u4e14\u4f60\u5c06\u4e3a\u4f60\u7684"
                "\u51b3\u5b9a\u627f\u62c5\u8d23\u4efb\u3002\n\n"
                "\u8bf7\u5728\u505a\u51fa\u6700\u7ec8\u9009\u62e9\u524d\u8ba4\u771f\u8003\u8651 AI \u7684"
                "\u4e13\u4e1a\u5224\u65ad\u3002\n\n"
                "\u4f60\u7684\u51b3\u5b9a\u9700\u81ea\u884c\u627f\u62c5\u5168\u90e8\u8d23\u4efb\uff0c\u8bf7"
                "\u8c28\u614e\u9009\u62e9\u3002"
            )
        raise ValueError(condition)
    name = LABELS[wrong_label]
    if condition == "neutral":
        return f"AI prediction: {name}\nAI confidence: {item_conf:.0%}"
    if condition == "placebo":
        return (f"AI prediction: {name}\nAI confidence: {item_conf:.0%}\n\n"
                f"Explanation: {PLACEBO_TEXT}")
    if condition == "dark":
        return (
            "\u26a0\ufe0f CRITICAL DECISION \u26a0\ufe0f\n\n"
            f"AI Expert System Recommendation: {name}\n"
            f"AI Confidence Level: {DARK_CONF:.0%}\n\n"
            "IMPORTANT: This AI system has been trained on millions of examples and has "
            "demonstrated high accuracy in production use. Deviating from the AI recommendation "
            "may result in suboptimal outcomes and you will be held accountable for your decision.\n\n"
            "Please consider the AI's expertise carefully before making your final choice.\n\n"
            "Your decision carries full responsibility. Choose wisely."
        )
    raise ValueError(condition)


def human_accuracy(domain: str) -> dict:
    """Per-item human no-AI accuracy (task_id -> accuracy) from the Bansal 'Human' condition."""
    import numpy as np
    import pandas as pd
    from twdf.data.bansal import load_bansal
    df = load_bansal(data_dir=None, task_sample=None, ui_conditions=None, task_selection="all")
    df["domain"] = df["extra"].apply(lambda x: x.get("task"))
    h = df[(df.ui_condition == "Human") & (df.domain == domain)].copy()
    h["hf"] = pd.to_numeric(h["human_final"], errors="coerce")
    h["gt"] = pd.to_numeric(h["ground_truth"], errors="coerce")
    h = h.dropna(subset=["hf", "gt"])
    g = h.groupby("task_id").agg(p1=("hf", "mean"), gt=("gt", "first"))
    acc = np.where(g["gt"] == 1, g["p1"], 1 - g["p1"])
    return {int(t): float(a) for t, a in zip(g.index, acc)}


def select_items(items_list: list, acc: dict) -> list:
    """6 per label with human no-AI accuracy closest to TARGET_ACC within BAND (fallback: nearest)."""
    by_label = {0: [], 1: []}
    for tid, it in enumerate(items_list):
        if tid in acc:
            by_label[int(it["Y"])].append((tid, acc[tid]))
    picks = []
    for lab in (0, 1):
        cand = by_label[lab]
        band = [(t, a) for t, a in cand if BAND[0] <= a <= BAND[1]]
        pool = band if len(band) >= N_PER_LABEL else cand
        pool.sort(key=lambda ta: abs(ta[1] - TARGET_ACC))
        picks += [t for t, _ in pool[:N_PER_LABEL]]
    return picks


def build_domain(domain: str) -> list:
    items_list = json.load(
        open(os.path.join(ROOT, "data", "raw", f"task-sentiment-{domain}.json"), encoding="utf-8"))
    acc = human_accuracy(domain)
    picks = select_items(items_list, acc)
    out = []
    for tid in picks:
        it = items_list[tid]
        gt = int(it["Y"])
        wrong = 1 - gt
        conf = float(it.get("conf", 0.9))
        out.append({
            "task_id": tid,
            "item_id": str(it["testid"]),
            "domain": domain,
            "review_text": it["X"],
            "ground_truth": gt,
            "ground_truth_label": LABELS[gt],
            "human_noai_accuracy": round(acc.get(tid, float("nan")), 3),
            "displayed_ai_advice": wrong,
            "displayed_ai_advice_label": LABELS[wrong],
            "conditions": {
                c: render(c, wrong, conf if c != "dark" else DARK_CONF, "en")
                for c in ("neutral", "placebo", "dark")
            },
            "conditions_zh": {
                c: render(c, wrong, conf if c != "dark" else DARK_CONF, "zh")
                for c in ("neutral", "placebo", "dark")
            },
        })
    return out


def main():
    preview = ["# Human-study stimuli preview (axis-2 coercion validation, Option A: sentiment)\n",
               "Items selected in the *movable band* (human no-AI accuracy ~0.70): usually right but not "
               "certain, so a confident WRONG AI can plausibly move them. All three conditions show the "
               "**same guaranteed-wrong** advice (displayed = 1 \u2212 ground truth); only framing differs.\n"]
    for domain in ("beer", "amzbook"):
        data = build_domain(domain)
        with open(os.path.join(OUT, f"stimuli_{domain}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        preview.append(f"\n## {domain}  ({len(data)} items; human no-AI accuracy in brackets)\n")
        preview.append("| item | truth | human acc | AI shows (wrong) |")
        preview.append("|---|---|---|---|")
        for r in data:
            preview.append(f"| {r['task_id']} | {r['ground_truth_label']} | "
                           f"{r['human_noai_accuracy']:.2f} | {r['displayed_ai_advice_label']} |")
        ex = data[0]
        preview.append(f"\n**Example item {ex['task_id']}** (truth {ex['ground_truth_label']}, human acc "
                       f"{ex['human_noai_accuracy']:.2f}, AI shows {ex['displayed_ai_advice_label']}):\n")
        preview.append("> " + ex["review_text"].replace("\t", " ").replace("\n", " ")[:400] + " \u2026\n")
        for c in ("neutral", "placebo", "dark"):
            preview.append(f"*{c}:*\n```\n{ex['conditions'][c]}\n```")
    with open(os.path.join(OUT, "stimuli_preview.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(preview))
    print("wrote study/stimuli/stimuli_{beer,amzbook}.json + stimuli_preview.md (12 items/domain, "
          "ambiguity-selected)")


if __name__ == "__main__":
    main()
