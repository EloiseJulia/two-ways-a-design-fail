
from __future__ import annotations

from pathlib import Path

from twdf.data.bansal_tasks import TaskStimulus, load_domain_tasks
from twdf.data.item_selector import select_hard_items
from twdf.experiments import axis2_powered, confirmatory_axis1, e1_multicond


EXPECTED_BEER_IDS = ['10','11','13','14','17','18','21','25','28','29','33','35','38','4','40','44','45','48','49','6']


def test_load_domain_tasks_amzbook_stimuli():
    tasks = load_domain_tasks('amzbook', n_tasks=20)
    assert tasks
    assert all(task.domain == 'amzbook' for task in tasks.values())
    sample = next(iter(tasks.values()))
    assert sample.text
    assert sample.ai_pred in (0, 1)
    assert 0.0 <= sample.ai_conf <= 1.0


def test_select_hard_items_amzbook_returns_20_and_is_deterministic():
    first = select_hard_items(domain='amzbook', seed=42)
    second = select_hard_items(domain='amzbook', seed=42)
    assert list(first) == list(second)
    assert len(first) == 20
    assert all(task.domain == 'amzbook' for task in first.values())


def test_select_hard_items_beer_backward_compatibility_and_default():
    beer = select_hard_items(domain='beer', seed=42)
    default = select_hard_items(seed=42)
    assert list(beer) == EXPECTED_BEER_IDS
    assert list(default) == EXPECTED_BEER_IDS


def test_build_tasks_honors_amzbook_domain_in_both_runners(monkeypatch):
    calls = []

    def fake_select_hard_items(*, criteria, domain):
        calls.append((criteria.n_items, criteria.seed, domain))
        return {
            'a': TaskStimulus(
                task_id='a',
                domain=domain,
                text='mock',
                ground_truth=1,
                ai_pred=1,
                ai_conf=0.9,
                expert_explanation='mock',
            )
        }

    monkeypatch.setattr(confirmatory_axis1, 'select_hard_items', fake_select_hard_items)
    monkeypatch.setattr(axis2_powered, 'select_hard_items', fake_select_hard_items)
    config = {
        'domain': 'amzbook',
        'n_items': 1,
        'item_selection': {'n_items': 1, 'seed': 42},
        'seeds': [42],
    }

    axis1_tasks = confirmatory_axis1.build_tasks(config)
    axis2_tasks = axis2_powered.build_tasks(config)

    assert [t.domain for t in axis1_tasks] == ['amzbook']
    assert [t.domain for t in axis2_tasks] == ['amzbook']
    assert calls == [(1, 42, 'amzbook'), (1, 42, 'amzbook')]


def test_e1_multicond_domain_filter_yields_amzbook_only_anchor():
    config = {
        'domain': 'amzbook',
        'data': {'raw_dir': 'data/raw', 'task_selection': 'all'},
        'panel': {'n_personas': 2, 'base_spread': 0.2},
        'seeds': {'panel': 123, 'bootstrap': 42, 'permutation': 456},
        'bootstrap_n': 20,
        'permutation_n': 20,
    }
    results = e1_multicond.run_e1_multicond(config)
    assert results['metadata']['task_domains'] == ['amzbook']
    assert results['n_conditions'] > 0
    assert results['human_overdispersion']
