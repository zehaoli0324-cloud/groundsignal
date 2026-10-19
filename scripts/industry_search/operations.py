"""Offline setup and honest diagnostics; no legal or factual approval states."""
from collections import Counter
from copy import deepcopy
import importlib.util
import os
import platform
import sys
from urllib.parse import urlsplit

import requests

from .contracts import REPO, config_check, now, read_json, target_check, write_json
from .pipeline import fresh_directory, load_run
from .planning import plan
from .providers import KEYS

# Caps are ceilings, not promised coverage, elapsed time, tokens or a monetary limit.
INTENSITIES = {
    'quick': dict(max_queries=9, max_search_calls=9, results_per_query=3,
                  max_documents=5, max_fetch_calls=24, max_model_calls=8,
                  max_large_calls=3, max_elapsed_seconds=300),
    'standard': dict(max_queries=27, max_search_calls=54, results_per_query=4,
                     max_documents=15, max_fetch_calls=64, max_model_calls=24,
                     max_large_calls=9, max_elapsed_seconds=900),
    'deep': dict(max_queries=54, max_search_calls=108, results_per_query=5,
                 max_documents=30, max_fetch_calls=128, max_model_calls=48,
                 max_large_calls=18, max_elapsed_seconds=1800),
}
MODEL_PRESETS = {'none': 'search.default.json', 'qwen9b-flash': 'search.qwen9b-flash.json',
                 'qwen4b-pro': 'search.qwen4b-pro.json'}


def prepare(target_path, intensity, models, providers, out):
    target = target_check(read_json(target_path))
    config = deepcopy(read_json(REPO / 'config' / MODEL_PRESETS[models]))
    config['budget'].update(INTENSITIES[intensity])
    if providers is not None:
        config['providers'] = providers
    config_check(config)
    out = fresh_directory(out)
    write_json(out / 'target.json', target)
    write_json(out / 'config.json', config)
    preview = plan(target, config['budget'])
    write_json(out / 'plan-preview.json', preview)
    result = {'schema_version': 'groundsignal.session.v1', 'created_at': now(),
              'intensity': intensity, 'models': models, 'planned_queries': len(preview['queries']),
              'out': str(out), 'status': 'PREPARED_OFFLINE',
              'note': 'No network or models executed; permissions and factual quality not assessed.'}
    write_json(out / 'session.json', result)
    return result


def local_model_probe(model):
    """Explicit opt-in, loopback metadata only. No tokens, prompts or remote probes."""
    parsed = urlsplit(model['base_url'])
    if parsed.hostname not in {'localhost', '127.0.0.1', '::1'}:
        return {'status': 'REMOTE_NOT_PROBED', 'model_available': None}
    try:
        with requests.Session() as session:
            session.trust_env = False
            result = session.get(model['base_url'].rstrip('/') + '/models', timeout=3,
                                 allow_redirects=False)
            if result.status_code != 200:
                return {'status': 'LOCAL_METADATA_UNAVAILABLE', 'model_available': None}
            payload = result.json()
            available = {row.get('id') for row in payload.get('data', []) if isinstance(row, dict)}
            present = model['model'] in available
            return {'status': 'MODEL_LISTED' if present else 'MODEL_NOT_LISTED',
                    'model_available': present}
    except (requests.RequestException, ValueError, TypeError, AttributeError):
        return {'status': 'LOCAL_METADATA_UNAVAILABLE', 'model_available': None}


def doctor(config, target=None, probe=False):
    config_check(config)
    if target is not None:
        target_check(target)
    modules = ['requests', 'bs4', 'yaml', 'jsonschema',
               'pypdf' if config['pdf_parser'] == 'pypdf' else 'docling']
    if config['fetcher'] == 'crawl4ai':
        modules.append('crawl4ai')
    dependencies = {name: importlib.util.find_spec(name) is not None for name in modules}
    providers = [{'provider': name, 'key_required': name in KEYS,
                  'key_present': bool(os.environ.get(KEYS[name])) if name in KEYS else None,
                  'network_tested': False} for name in config['providers']]
    roles = {'small_only': ('small',), 'large_only': ('large',), 'cascade': ('small', 'large')}[config['routing_mode']]
    models = {}
    for role, model in config['models'].items():
        key_present = bool(os.environ.get(model['api_key_env'])) if model['api_key_env'] else None
        row = {'enabled': model['enabled'], 'required_by_routing': role in roles,
               'key_present': key_present, 'model': model['model'],
               'status': 'DISABLED' if not model['enabled'] else 'NOT_PROBED',
               'model_available': None}
        if model['enabled'] and probe:
            row.update(local_model_probe(model))
        models[role] = row
    has_search = config['budget']['max_search_calls'] > 0 and any(
        p['key_present'] is True or not p['key_required'] for p in providers)
    has_seed = bool(target and target['seed_urls'])
    collection_configured = bool((has_search or has_seed) and all(dependencies.values())
                                 and config['budget']['max_documents'] > 0
                                 and config['budget']['max_fetch_calls'] > 0)
    extraction_configured = (all(dependencies.values()) and config['budget']['max_model_calls'] > 0
                            and all(models[r]['enabled'] and models[r]['key_present'] is not False
                                    and models[r]['model_available'] is not False for r in roles)
                            and ('large' not in roles or config['budget']['max_large_calls'] > 0))
    return {'schema_version': 'groundsignal.doctor.v1', 'status': 'DIAGNOSTIC_ONLY',
            'python': platform.python_version(), 'in_virtualenv': sys.prefix != sys.base_prefix,
            'dependencies': dependencies, 'providers': providers, 'models': models,
            'collection_configuration_ready': collection_configured,
            'extraction_configuration_ready': bool(extraction_configured),
            'local_probe_requested': probe, 'provider_authentication': 'NOT_TESTED',
            'inference_quality': 'UNASSESSED', 'source_permissions': 'NOT_ASSESSED',
            'note': 'Configuration readiness is not service availability; listed models may fail inference.'}


def audit(path):
    run = load_run(path)
    documents = run['documents']
    fetched = [d for d in documents if d['status'] == 'FETCHED']
    searches = Counter(r['status'] for r in run['search_records'])
    attempts = [a for e in run['extractions'] for a in e['attempts']]
    errors = Counter(a['status'] for a in attempts)
    successful = {e['document_id'] for e in run['extractions']
                  if any(a['status'] in {'OK', 'SIMULATED'} for a in e['attempts'])}
    unprocessed = [d['id'] for d in fetched if d['id'] not in successful]
    truncated = [e['document_id'] for e in run['extractions'] if e['input_truncated']]
    missing = [dim for dim, row in run['coverage'].items() if not row['fetched_documents']]
    actions = []
    if run['synthetic']:
        actions.append('Synthetic engineering demo only; collect permitted real sources before judging quality.')
    if missing:
        actions.append('Review dimensions without fetched evidence; lack of a hit is not evidence of absence.')
    if any(s not in {'OK', 'NO_RESULTS', 'SIMULATED'} for s in searches):
        actions.append('Inspect search failure/configuration/budget statuses before increasing scope.')
    if any(s not in {'OK', 'SIMULATED'} for s in errors):
        actions.append('Resolve incomplete model attempts; never treat unavailable escalation as approval.')
    if run['diagnostics']:
        actions.append('Review run diagnostics, including truncated coverage or elapsed budget.')
    if unprocessed:
        actions.append('Fetched documents without a successful model response remain unprocessed, not negative evidence.')
    if truncated:
        actions.append('Read omitted source regions manually; selected model input is not full-document review.')
    actions.append('Review each candidate against original context, identities, dates and independent sources.')
    return {'schema_version': 'groundsignal.run-audit.v1', 'run_id': run['id'],
            'status': 'TECHNICAL_AUDIT_ONLY', 'run_status': run['status'], 'synthetic': run['synthetic'],
            'contract_integrity': 'VALID', 'counts': run['counts'],
            'search_statuses': dict(searches), 'document_statuses': dict(Counter(d['status'] for d in documents)),
            'model_attempt_statuses': dict(errors), 'coverage': run['coverage'],
            'documents_without_successful_model_response': unprocessed,
            'truncated_model_input_documents': truncated,
            'dimensions_without_fetched_evidence': missing,
            'duplicate_content_documents': sum(bool(d.get('duplicate_content_of')) for d in fetched),
            'rejected_outputs': sum(len(e['rejected']) for e in run['extractions']),
            'pending_candidates': len(run['candidates']), 'diagnostics': run['diagnostics'],
            'factual_precision': 'UNASSESSED', 'source_independence': 'REQUIRES_REVIEW',
            'legal_compliance': 'NOT_ASSESSED', 'next_actions': actions}
