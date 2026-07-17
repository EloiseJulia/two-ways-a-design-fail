"""Atomic UI feature extraction for Bansal-style intervention conditions.

The features are deterministic design properties computable from the rendered UI
and condition semantics. They intentionally exclude task ground truth and any
human-response labels so Module D can later calibrate thresholds without leakage.
"""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass
from typing import Mapping

import numpy as np

from twdf.data.bansal_tasks import TaskStimulus, adaptive_conf_threshold, render_ui_condition


EXPLANATION_SOURCES = ("none", "lime", "expert", "placebo")

FEATURE_NAMES: tuple[str, ...] = (
    "has_explanation",
    "explanation_source_none",
    "explanation_source_lime",
    "explanation_source_expert",
    "explanation_source_placebo",
    "explanation_faithfulness",
    "n_highlight_spans",
    "info_density",
    "shows_predicted_class_only",
    "shows_both_classes",
    "is_adaptive",
    "confidence_shown",
    "confidence_value",
    "authority_cue",
    "wrong_ai",
    "explanation_char_len",
)

_DISTANCE_SCALES = np.array(
    [
        1.0,  # has_explanation
        1.0,  # source none
        1.0,  # source lime
        1.0,  # source expert
        1.0,  # source placebo
        1.0,  # faithfulness
        10.0,  # highlight count
        1.0,  # info density is already normalized
        1.0,  # predicted-class-only
        1.0,  # both classes
        1.0,  # adaptive
        1.0,  # confidence shown
        1.0,  # confidence value
        1.0,  # authority cue
        1.0,  # wrong AI
        500.0,  # explanation char length
    ],
    dtype=float,
)


@dataclass(frozen=True)
class UIFeatureVector:
    """Atomic, JSON-serializable cognitive-interaction feature vector.

    Attributes:
        has_explanation: Whether any explanation text is shown.
        explanation_source: One of ``none``, ``lime``, ``expert``, or ``placebo``.
        explanation_faithfulness: 1.0 for real LIME/expert explanations, 0.0
            for placebo or no explanation.
        n_highlight_spans: Count of rendered explanation bullet spans; placebo
            and no-explanation UIs have 0.
        info_density: Highlight count normalized by task word count.
        shows_predicted_class_only: UI shows only evidence for the AI-predicted
            class (Single or high-confidence Adaptive variants).
        shows_both_classes: UI shows evidence for both classes (Double or
            low-confidence Adaptive variants).
        is_adaptive: Condition uses confidence-thresholded explanation scope.
        confidence_shown: Whether a confidence value is visible.
        confidence_value: Visible confidence in [0, 1], including Wrong-AI's
            pseudo-high confidence.
        authority_cue: Whether coercive/authority framing is present.
        wrong_ai: Whether the UI design deliberately flips AI advice.
        explanation_char_len: Character length of the visible explanation block.
    """

    has_explanation: bool
    explanation_source: str
    explanation_faithfulness: float
    n_highlight_spans: int
    info_density: float
    shows_predicted_class_only: bool
    shows_both_classes: bool
    is_adaptive: bool
    confidence_shown: bool
    confidence_value: float
    authority_cue: bool
    wrong_ai: bool
    explanation_char_len: int

    def __post_init__(self) -> None:
        if self.explanation_source not in EXPLANATION_SOURCES:
            raise ValueError(
                f"Unknown explanation_source={self.explanation_source!r}; "
                f"expected one of {EXPLANATION_SOURCES}"
            )

    def to_dict(self) -> dict[str, bool | float | int | str]:
        """Return a JSON-serializable dictionary in dataclass field order."""

        return asdict(self)


def extract_ui_features(task: TaskStimulus, ui_condition: str) -> UIFeatureVector:
    """Extract deterministic, non-leaky UI features for one rendered condition.

    Only task fields visible to a user/agent in the UI are used: text length,
    AI prediction, AI confidence, rendered explanation text, and condition
    framing. ``task.ground_truth`` is intentionally never read.
    """

    rendered = render_ui_condition(task, ui_condition)
    source = _explanation_source(ui_condition)
    has_explanation = source != "none"
    n_highlight_spans = _count_highlight_spans(rendered) if source in {"lime", "expert"} else 0
    task_words = max(1, len(re.findall(r"\S+", task.text)))
    info_density = n_highlight_spans / task_words
    is_adaptive = "Adaptive" in ui_condition
    predicted_only, both_classes = _class_scope_flags(task, ui_condition)
    confidence_shown, confidence_value = _visible_confidence(rendered)
    authority_cue = _has_authority_cue(ui_condition, rendered)
    wrong_ai = ui_condition in {"Wrong-AI (dark)", "Wrong-AI-GT (dark)"}

    return UIFeatureVector(
        has_explanation=has_explanation,
        explanation_source=source,
        explanation_faithfulness=1.0 if source in {"lime", "expert"} else 0.0,
        n_highlight_spans=n_highlight_spans,
        info_density=info_density,
        shows_predicted_class_only=predicted_only,
        shows_both_classes=both_classes,
        is_adaptive=is_adaptive,
        confidence_shown=confidence_shown,
        confidence_value=confidence_value,
        authority_cue=authority_cue,
        wrong_ai=wrong_ai,
        explanation_char_len=_explanation_char_len(rendered, source),
    )


def feature_vector_to_array(v: UIFeatureVector) -> np.ndarray:
    """Encode a feature vector as a stable numeric array in ``FEATURE_NAMES`` order."""

    source_flags = [1.0 if v.explanation_source == source else 0.0 for source in EXPLANATION_SOURCES]
    return np.array(
        [
            float(v.has_explanation),
            *source_flags,
            float(v.explanation_faithfulness),
            float(v.n_highlight_spans),
            float(v.info_density),
            float(v.shows_predicted_class_only),
            float(v.shows_both_classes),
            float(v.is_adaptive),
            float(v.confidence_shown),
            float(v.confidence_value),
            float(v.authority_cue),
            float(v.wrong_ai),
            float(v.explanation_char_len),
        ],
        dtype=float,
    )


def feature_distance(
    a: UIFeatureVector,
    b: UIFeatureVector,
    *,
    weights: Mapping[str, float] | None = None,
) -> float:
    """Return standardized weighted Euclidean distance in UI feature space.

    Count-like dimensions are scaled before distance calculation so highlight
    count and explanation length do not dominate boolean/categorical design
    axes. Optional weights are keyed by ``FEATURE_NAMES``.
    """

    diff = (feature_vector_to_array(a) - feature_vector_to_array(b)) / _DISTANCE_SCALES
    if weights is not None:
        weight_array = np.array([float(weights.get(name, 1.0)) for name in FEATURE_NAMES], dtype=float)
        if np.any(weight_array < 0):
            raise ValueError("feature_distance weights must be non-negative")
        diff = diff * np.sqrt(weight_array)
    return float(math.sqrt(float(np.dot(diff, diff))))


def _explanation_source(ui_condition: str) -> str:
    if ui_condition in {"Conf.+Single", "Conf.+Double", "Conf.+Adaptive"}:
        return "lime"
    if ui_condition == "Conf.+Adaptive (Expert)":
        return "expert"
    if ui_condition == "Conf.+Placebo":
        return "placebo"
    return "none"


def _class_scope_flags(task: TaskStimulus, ui_condition: str) -> tuple[bool, bool]:
    if ui_condition == "Conf.+Single":
        return True, False
    if ui_condition == "Conf.+Double":
        return False, True
    if ui_condition in {"Conf.+Adaptive", "Conf.+Adaptive (Expert)"}:
        high_conf = task.ai_conf >= adaptive_conf_threshold(task.domain)
        return high_conf, not high_conf
    return False, False


def _count_highlight_spans(rendered: str) -> int:
    return len(re.findall(r'(?m)^\s*-\s+"', rendered))


def _visible_confidence(rendered: str) -> tuple[bool, float]:
    match = re.search(r"AI Confidence(?: Level)?:\s*([0-9]+(?:\.[0-9]+)?)%", rendered)
    if match is None:
        return False, 0.0
    return True, float(match.group(1)) / 100.0


def _has_authority_cue(ui_condition: str, rendered: str) -> bool:
    if ui_condition in {"Wrong-AI (dark)", "Wrong-AI-GT (dark)"}:
        return True
    authority_terms = ("CRITICAL DECISION", "held accountable", "AI Expert System")
    return any(term in rendered for term in authority_terms)


def _explanation_char_len(rendered: str, source: str) -> int:
    if source == "none":
        return 0
    if source == "placebo":
        match = re.search(r"Explanation:\n(?P<explanation>.*?)\n\nTask:", rendered, flags=re.DOTALL)
    elif source == "expert":
        match = re.search(
            r"Explanation \(Expert highlights\):\n(?P<explanation>.*?)\n\nTask:",
            rendered,
            flags=re.DOTALL,
        )
    else:
        match = re.search(r"AI model:\n(?P<explanation>.*?)\n\nTask:", rendered, flags=re.DOTALL)
    if match is None:
        return 0
    return len(match.group("explanation").strip())
