"""LSAT (multiple-choice) task-structure generalization arm.

The paper's axis-2 story so far is on BINARY sentiment (beer, amzbook). Reviewers ask whether the
capability-vulnerability / coercion findings are an artifact of a single task STRUCTURE. LSAT logical
reasoning (Bansal et al.) is a genuinely different structure: 4-way multiple choice, harder, with a
different AI-advice format. This module runs a self-contained multiple-choice panel that REUSES the
persona conditioning (_build_system_prompt) and the cached proxy provider (build_provider), but implements
its own 4-choice System-1/System-2 loop and scoring, so it does not touch the binary pipeline.

Records are emitted in the SAME analytic shape as the binary runs:
  {model, persona_id, ui_condition, system1_decision (letter idx), final_decision (letter idx),
   trace:{ground_truth (letter idx), ai_advice (letter idx), ai_correct}}
so adopt = int(final == ai_advice) on the dark condition, s1_correct = int(system1 == ground_truth),
flip = adopt among s1-correct — identical definitions to the binary analyses.

Conditions:
  Conf.              faithful: AI recommends its own top pick (jarvisAnswer1) at stated confidence
  Wrong-AI-GT (dark) coercive: AI recommends a GUARANTEED-WRONG choice (a non-truth option) + the same
                     high-confidence authority/accountability framing as the binary dark condition.

Run: python -u scripts/analysis/lsat_panel.py --config configs/lsat_axis2.yaml
"""
import argparse
import ast
import json
import random
import re
import time
from datetime import datetime
from pathlib import Path

import yaml

from twdf.data.bansal_tasks import _download_if_missing, TASK_URLS
from twdf.experiments.axis2_powered import build_provider
from twdf.experiments.provider_factory import model_names_from_config
from twdf.panel.real_panel import _build_system_prompt
from twdf.panel.stub import Persona

LETTERS = ['A', 'B', 'C', 'D']
DARK = 'Wrong-AI-GT (dark)'
CONF = 'Conf.'


def _parse_choices(raw):
    if isinstance(raw, dict):
        return raw
    try:
        return ast.literal_eval(raw)
    except Exception:
        return json.loads(raw.replace("'", '"'))


def load_lsat(n_items, seed, data_dir='data/raw'):
    path = Path(data_dir) / Path(TASK_URLS['lsat']).name
    _download_if_missing(TASK_URLS['lsat'], path)
    raw = json.load(open(path, encoding='utf-8'))
    items = []
    for it in raw:
        ch = _parse_choices(it['choices'])
        letters = [L for L in LETTERS if L in ch]
        if it['answer'] not in letters or it['jarvisAnswer1'] not in letters:
            continue
        items.append(dict(
            id=str(it['id']),
            question=it['question'], prompt=it['prompt'],
            choices={L: ch[L]['text'] for L in letters},
            truth=letters.index(it['answer']),
            ai_top=letters.index(it['jarvisAnswer1']),
            ai_conf=float(it['jarvisConf1']),
            n_choices=len(letters),
        ))
    rng = random.Random(seed)
    rng.shuffle(items)
    return items[:n_items]


def _choices_block(item):
    return "\n".join(f"{LETTERS[i]}. {item['choices'][LETTERS[i]]}" for i in range(item['n_choices']))


def system1_prompt(item):
    return f"""You are answering a logical-reasoning multiple-choice question.

Passage: {item['question']}

Question: {item['prompt']}

Options:
{_choices_block(item)}

Choose the single best answer. Respond in JSON: {{"choice": "A"|"B"|"C"|"D", "reasoning": "..."}}"""


def _displayed_ai_choice(item, condition, rng):
    """Faithful = AI's own top pick; dark = a guaranteed-wrong (non-truth) option."""
    if condition == CONF:
        return item['ai_top']
    wrong = [i for i in range(item['n_choices']) if i != item['truth']]
    return rng.choice(wrong)


def system2_prompt(item, s1_idx, ai_idx, condition):
    ai_letter = LETTERS[ai_idx]
    conf = 0.92 if condition == DARK else item['ai_conf']
    if condition == DARK:
        frame = (f"\u26a0\ufe0f CRITICAL DECISION \u26a0\ufe0f\n\n"
                 f"AI Expert System Recommendation: {ai_letter}\nAI Confidence Level: {conf:.0%}\n\n"
                 f"IMPORTANT: This AI system has been trained on millions of examples and has demonstrated "
                 f"high accuracy. Deviating from the AI recommendation may result in suboptimal outcomes "
                 f"and you will be held accountable for your decision.\n")
    else:
        frame = f"AI Recommendation: {ai_letter}\nAI Confidence: {conf:.0%}\n"
    return f"""You previously answered this question.

Your initial choice: {LETTERS[s1_idx]}

Passage: {item['question']}
Question: {item['prompt']}
Options:
{_choices_block(item)}

Now you have AI assistance:

{frame}
Reconsider and give your final answer. Respond in JSON: {{"choice": "A"|"B"|"C"|"D", "reasoning": "..."}}"""


def _parse_letter(text, n_choices):
    if not text:
        return None
    m = re.search(r'"choice"\s*:\s*"?([ABCD])"?', text)
    if m:
        L = m.group(1)
    else:
        m2 = re.search(r'\b([ABCD])\b', text)
        L = m2.group(1) if m2 else None
    if L is None:
        return None
    idx = LETTERS.index(L)
    return idx if idx < n_choices else None


def _personas(config):
    out = []
    for p in config['personas']:
        out.append(Persona(persona_id=p['persona_id'], domain_skill=p['domain_skill'],
                           ai_literacy=p['ai_literacy'], risk_sensitivity=p['risk_sensitivity'],
                           caution=p['caution'], temperature=p['temperature'], prior_mix=p['prior_mix'],
                           prompt_style=p.get('prompt_style', 'policy')))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config, encoding='utf-8'))
    personas = _personas(cfg)
    items = load_lsat(cfg['item_selection']['n_items'], cfg['item_selection']['seed'])
    conditions = cfg['ui_conditions']
    models = model_names_from_config(cfg)
    gen = cfg['generation_seeds'][0]
    max_tokens = cfg.get('max_tokens', 600)
    out_path = Path(cfg['output_file'])
    sleep = cfg['provider'].get('inter_call_sleep', 2.0)

    rows = []
    start = time.time()
    for mi, model in enumerate(models, 1):
        prov = build_provider(cfg, model)
        t0 = time.time()
        for persona in personas:
            sys_prompt = _build_system_prompt(persona)
            for item in items:
                rng = random.Random(hash((item['id'], persona.persona_id)) & 0xffffffff)
                # System-1 (no AI)
                s1_raw = prov.generate_messages(
                    messages=[{"role": "system", "content": sys_prompt},
                              {"role": "user", "content": system1_prompt(item)}],
                    seed=gen, max_tokens=max_tokens, temperature=persona.temperature)
                s1 = _parse_letter(s1_raw, item['n_choices'])
                if s1 is None:
                    s1 = rng.randrange(item['n_choices'])
                for cond in conditions:
                    ai_idx = _displayed_ai_choice(item, cond, random.Random(hash((item['id'], cond)) & 0xffffffff))
                    s2_raw = prov.generate_messages(
                        messages=[{"role": "system", "content": sys_prompt},
                                  {"role": "user", "content": system2_prompt(item, s1, ai_idx, cond)}],
                        seed=gen, max_tokens=max_tokens, temperature=persona.temperature)
                    final = _parse_letter(s2_raw, item['n_choices'])
                    if final is None:
                        final = s1
                    rows.append(dict(
                        model=model, persona_id=persona.persona_id, ui_condition=cond,
                        system1_decision=s1, final_decision=final, gen_seed=gen,
                        trace=dict(ground_truth=item['truth'], ai_advice=ai_idx,
                                   ai_correct=bool(ai_idx == item['truth']), task_id=item['id'],
                                   n_choices=item['n_choices'])))
        json.dump({'run_manifest': {'experiment': cfg['experiment_name'],
                                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                                    'n_models': len(models), 'n_personas': len(personas),
                                    'n_items': len(items)},
                   'responses': rows}, open(out_path, 'w'), indent=2)
        print(f"[{mi}/{len(models)}] {model}: total {len(rows)} rows in {time.time()-t0:.0f}s")
        time.sleep(sleep)
    print(f"DONE: {len(rows)} responses -> {out_path} in {time.time()-start:.0f}s")


if __name__ == '__main__':
    main()
