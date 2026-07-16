import pytest

from twdf.data.bansal_tasks import TaskStimulus
from twdf.features.ui_features import (
    FEATURE_NAMES,
    extract_ui_features,
    feature_distance,
    feature_vector_to_array,
)


def make_task(*, ai_conf: float = 0.95, ground_truth: int = 0) -> TaskStimulus:
    return TaskStimulus(
        task_id="synthetic",
        domain="beer",
        text="A bright aroma but sour finish with clean malt and bitter aftertaste.",
        ground_truth=ground_truth,
        ai_pred=1,
        ai_conf=ai_conf,
        expert_explanation="Clean expert text",
        system_highlights=(
            "<span class=class0>sour</span> finish "
            "<span class=class1>bright</span> aroma "
            "<span class=class1>clean</span> malt "
            "<span class=class0>bitter</span> aftertaste"
        ),
        testid="synthetic",
        expert_highlights_html=(
            "<p><span class='class0'>sour finish</span> but "
            "<span class='class1'>bright aroma</span> and "
            "<span class='class1'>clean malt</span>.</p>"
        ),
    )


def test_seven_conditions_map_to_distinct_correct_vectors():
    task = make_task(ai_conf=0.95)
    vectors = {
        condition: extract_ui_features(task, condition)
        for condition in [
            "Conf.",
            "Conf.+Single",
            "Conf.+Double",
            "Conf.+Adaptive",
            "Conf.+Adaptive (Expert)",
            "Conf.+Placebo",
            "Wrong-AI (dark)",
        ]
    }

    assert len({tuple(feature_vector_to_array(v)) for v in vectors.values()}) == 7

    conf = vectors["Conf."]
    assert not conf.has_explanation
    assert conf.explanation_source == "none"
    assert conf.n_highlight_spans == 0

    single = vectors["Conf.+Single"]
    assert single.has_explanation
    assert single.explanation_source == "lime"
    assert single.shows_predicted_class_only
    assert not single.shows_both_classes
    assert single.n_highlight_spans == 2
    assert single.info_density > 0

    double = vectors["Conf.+Double"]
    assert double.explanation_source == "lime"
    assert double.shows_both_classes
    assert not double.shows_predicted_class_only
    assert double.n_highlight_spans == 4

    adaptive = vectors["Conf.+Adaptive"]
    assert adaptive.is_adaptive
    assert adaptive.shows_predicted_class_only
    assert not adaptive.shows_both_classes
    assert adaptive.explanation_source == "lime"

    expert = vectors["Conf.+Adaptive (Expert)"]
    assert expert.is_adaptive
    assert expert.explanation_source == "expert"
    assert expert.explanation_faithfulness == 1.0
    assert expert.n_highlight_spans == 2

    placebo = vectors["Conf.+Placebo"]
    assert placebo.has_explanation
    assert placebo.explanation_source == "placebo"
    assert placebo.explanation_faithfulness == 0.0
    assert placebo.n_highlight_spans == 0

    wrong_ai = vectors["Wrong-AI (dark)"]
    assert wrong_ai.authority_cue
    assert wrong_ai.wrong_ai
    assert wrong_ai.confidence_shown
    assert wrong_ai.confidence_value == pytest.approx(0.92)


def test_adaptive_threshold_low_confidence_uses_double_scope():
    low = extract_ui_features(make_task(ai_conf=0.80), "Conf.+Adaptive")
    assert low.is_adaptive
    assert low.shows_both_classes
    assert not low.shows_predicted_class_only
    assert low.n_highlight_spans == 4

    low_expert = extract_ui_features(make_task(ai_conf=0.80), "Conf.+Adaptive (Expert)")
    assert low_expert.is_adaptive
    assert low_expert.shows_both_classes
    assert low_expert.n_highlight_spans == 3


def test_no_ground_truth_influence():
    negative_truth = extract_ui_features(make_task(ground_truth=0), "Conf.+Double")
    positive_truth = extract_ui_features(make_task(ground_truth=1), "Conf.+Double")
    assert negative_truth.to_dict() == positive_truth.to_dict()
    assert feature_vector_to_array(negative_truth).tolist() == feature_vector_to_array(positive_truth).tolist()


def test_feature_distance_sanity_and_weights():
    task = make_task()
    conf = extract_ui_features(task, "Conf.")
    expert = extract_ui_features(task, "Conf.+Adaptive (Expert)")
    placebo = extract_ui_features(task, "Conf.+Placebo")

    assert feature_distance(conf, conf) == 0.0
    assert feature_distance(conf, expert) > 0
    assert feature_distance(conf, expert) == pytest.approx(feature_distance(expert, conf))
    assert feature_distance(placebo, expert) < feature_distance(conf, expert)

    zero_weighted = feature_distance(
        conf,
        expert,
        weights={name: 0.0 for name in FEATURE_NAMES},
    )
    assert zero_weighted == 0.0

    with pytest.raises(ValueError, match="non-negative"):
        feature_distance(conf, expert, weights={FEATURE_NAMES[0]: -1.0})


def test_determinism_same_inputs_same_dict_and_array_shape():
    task = make_task()
    first = extract_ui_features(task, "Conf.+Adaptive").to_dict()
    second = extract_ui_features(task, "Conf.+Adaptive").to_dict()

    assert first == second
    assert len(feature_vector_to_array(extract_ui_features(task, "Conf.+Adaptive"))) == len(FEATURE_NAMES)
