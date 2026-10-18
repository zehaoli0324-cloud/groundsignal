"""Frozen-input route comparison. Missing labels/models never become quality PASS."""
from copy import deepcopy
from pathlib import Path

from .contracts import digest, read_json, write_json
from .pipeline import fresh_directory, replay

FIELDS = ('subject', 'predicate', 'object', 'product', 'stage', 'polarity', 'event_time')


def score(run, labels):
    attempts = [a for e in run['extractions'] for a in e['attempts']]
    model_ran = any(a['status'] in {'OK', 'SIMULATED'} for a in attempts)
    result = {'quality_status': 'UNASSESSED', 'precision': None, 'recall': None,
              'true_positive': None, 'false_positive': None, 'false_negative': None,
              'scored_documents': 0, 'all_fetched_documents': sum(d['status'] == 'FETCHED' for d in run['documents']),
              'model_calls': run['counts']['model_calls'], 'large_calls': run['counts']['large_model_calls'],
              'input_tokens': sum(a['usage'].get('prompt_tokens', 0) for a in attempts),
              'output_tokens': sum(a['usage'].get('completion_tokens', 0) for a in attempts),
              'estimated_money_cost': None, 'synthetic': run['synthetic'],
              'frozen_input_sha256': run['frozen_input_sha256']}
    if not model_ran:
        result['quality_status'] = 'MODEL_NOT_RUN'
        return result
    if labels is None:
        return result
    if labels.get('synthetic') != run['synthetic']:
        raise ValueError('gold_synthetic_mode_mismatch')
    docs = {d['id']: d for d in run['documents']}
    annotated = labels.get('documents', [])
    if not annotated or len({x['document_id'] for x in annotated}) != len(annotated):
        raise ValueError('gold_must_have_unique_document_labels')
    gold, predicted = set(), set()
    for row in annotated:
        doc = docs.get(row['document_id'])
        if not doc or doc['status'] != 'FETCHED' or row['text_sha256'] != doc['text_sha256']:
            raise ValueError('gold_source_fingerprint_mismatch')
        for item in row['claims']:
            gold.add((doc['id'], *(item[k] for k in FIELDS)))
        for item in run['candidates']:
            if item['document_id'] == doc['id']:
                predicted.add((doc['id'], *(item[k] for k in FIELDS)))
    tp, fp, fn = len(gold & predicted), len(predicted - gold), len(gold - predicted)
    result.update(quality_status='SYNTHETIC_ONLY' if run['synthetic'] else 'LABELED_SUBSET',
                  precision=tp / (tp + fp) if tp + fp else None,
                  recall=tp / (tp + fn) if tp + fn else None,
                  true_positive=tp, false_positive=fp, false_negative=fn,
                  scored_documents=len(annotated))
    return result


def compare(source_path, config, out, labels=None, fixture=None):
    out = fresh_directory(out)
    rows = []
    for mode in ('small_only', 'large_only', 'cascade'):
        selected = deepcopy(config)
        selected['routing_mode'] = mode
        run = replay(source_path, selected, out / mode, fixture=fixture)
        rows.append({'mode': mode, **score(run, labels)})
    if len({row['frozen_input_sha256'] for row in rows}) != 1:
        raise ValueError('comparison_inputs_changed')
    output = {'schema_version': 'groundsignal.model-comparison.v1',
              'selection_status': 'NO_AUTOMATIC_WINNER', 'results': rows,
              'note': 'Compare only this labeled subset. Synthetic fixtures are not model measurements; money cost is unknown without provider pricing/account data.'}
    write_json(out / 'comparison.json', output)
    return output
