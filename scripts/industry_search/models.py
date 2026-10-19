"""Small/large JSON extraction and grounded proposals, with no approval authority."""
from datetime import datetime
import json
import os
import re
import time

import requests

from .contracts import REPO, aliases, check, digest, mentions, now, read_json


def select_text(text, target, limit):
    """Keep original characters; select alias-centered windows across long sources."""
    if len(text) <= limit:
        return text
    ranges = [(0, min(700, len(text)))]
    for name in aliases(target):
        for match in list(re.finditer(re.escape(name), text, re.I))[:60]:
            ranges.append((max(0, match.start() - 500), min(len(text), match.end() + 1000)))
    merged = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    selected = '\n[OMITTED SOURCE REGION]\n'.join(text[a:b] for a, b in merged)
    return selected[:limit]


def ground_claims(payload, document, target, input_text):
    check('research-extraction', payload)
    accepted, rejected = [], []
    for claim in payload['claims']:
        reasons = []
        quote = claim['quote']
        start = document['text'].find(quote)
        if start < 0 or quote not in input_text:
            reasons.append('quote_not_in_model_input_and_source')
        if claim['subject'] not in quote or claim['object'] not in quote:
            reasons.append('named_endpoints_not_in_quote')
        if not mentions(quote, target):
            reasons.append('target_not_in_quote')
        if claim['product'] and claim['product'] not in quote:
            reasons.append('product_not_in_quote')
        if claim['event_time']:
            value = claim['event_time']
            try:
                datetime.strptime(value, {4: '%Y', 7: '%Y-%m', 10: '%Y-%m-%d'}[len(value)])
            except (ValueError, KeyError):
                reasons.append('invalid_event_time')
            normalized = re.sub(r'[年月日/.]', '-', quote)
            if value not in normalized:
                reasons.append('event_time_not_in_quote')
        if claim['stage'] == 'MASS_PRODUCTION':
            if not re.search(r'量产|mass production|volume production', quote, re.I):
                reasons.append('mass_production_not_in_quote')
            if claim['polarity'] == 'ASSERTED' and re.search(
                    r'(尚未|未能|没有|计划|预计).{0,12}量产|(?:not|plan\w*|expect\w*).{0,30}(?:mass|volume) production', quote, re.I):
                reasons.append('mass_production_modality_mismatch')
        if reasons:
            rejected.append({'claim': claim, 'reasons': reasons})
            continue
        flags = []
        if claim['predicate'] in {'OWNS', 'CONTROLS', 'INVESTED_IN', 'COMPETES_WITH'}:
            flags.append('ownership_or_competition_requires_review')
        if claim['polarity'] != 'ASSERTED' or re.search(r'据悉|可能|预计|计划|否认|尚未|rumou?r|reportedly|may |not ', quote, re.I):
            flags.append('modality_or_counterevidence')
        pages = [p['page'] for p in document['pages'] if p['start'] < start + len(quote) and p['end'] > start]
        accepted.append({**claim, 'id': 'cand_' + digest([document['id'], claim])[:20],
                         'document_id': document['id'], 'quote_start': start,
                         'quote_end': start + len(quote), 'pages': pages,
                         'review_status': 'PENDING', 'identity_status': 'UNCONFIRMED',
                         'flags': flags, 'proposed_by': []})
    return accepted, rejected


class ModelClient:
    def __init__(self, config, session=None, fixture=None):
        self.config = config
        self.session = session or requests.Session()
        self.fixture = fixture
        self.calls = self.large_calls = self.simulated_calls = self.simulated_large_calls = 0

    def call(self, role, document, target, input_text):
        model = self.config['models'][role]
        schema = read_json(REPO / 'schemas/research-extraction.v1.schema.json')
        system = (REPO / 'prompts/search/extract.md').read_text(encoding='utf-8')
        user = json.dumps({'target': {'name': target['name'], 'aliases': target['aliases']},
                           'schema': schema, 'document_text': input_text}, ensure_ascii=False)
        attempt = {'role': role, 'document_id': document['id'], 'at': now(),
                   'requested_model': model['model'], 'response_model': None,
                   'prompt_sha256': digest([system, user]), 'input_sha256': digest(input_text),
                   'config_sha256': digest(self.config), 'endpoint': model['base_url'],
                   'status': 'MODEL_NOT_RUN', 'error_code': None, 'usage': {},
                   'elapsed_ms': 0, 'synthetic': self.fixture is not None,
                   'payload': None, 'raw_response_text': None}
        if self.fixture is not None:
            budget = self.config['budget']
            if (self.simulated_calls >= budget['max_model_calls'] or
                    (role == 'large' and self.simulated_large_calls >= budget['max_large_calls'])):
                return dict(attempt, status='BUDGET_EXHAUSTED', error_code='synthetic_call_budget')
            self.simulated_calls += 1
            self.simulated_large_calls += role == 'large'
            attempt.update(requested_model='fixture/' + role, response_model='fixture/' + role,
                           endpoint='offline-fixture', status='SIMULATED',
                           payload=self.fixture.get(document['url'], {}).get(role, {'claims': []}))
            return attempt
        if not model['enabled']:
            return dict(attempt, error_code='role_disabled')
        key = os.environ.get(model['api_key_env'], '') if model['api_key_env'] else ''
        if model['api_key_env'] and not key:
            return dict(attempt, error_code='missing_' + model['api_key_env'])
        budget = self.config['budget']
        if self.calls >= budget['max_model_calls'] or (role == 'large' and self.large_calls >= budget['max_large_calls']):
            return dict(attempt, status='BUDGET_EXHAUSTED', error_code='model_call_budget')
        self.calls += 1
        self.large_calls += role == 'large'
        started = time.monotonic()
        body = {'model': model['model'], 'messages': [{'role': 'system', 'content': system},
                 {'role': 'user', 'content': user}], 'max_tokens': budget['max_output_tokens'],
                'response_format': {'type': 'json_object'}, 'stream': False, **model['extra_body']}
        try:
            response = self.session.post(model['base_url'].rstrip('/') + '/chat/completions',
                headers={'Authorization': 'Bearer ' + (key or 'local-no-key')}, json=body,
                timeout=(5, budget['timeout_seconds']), allow_redirects=False)
            if response.status_code != 200:
                attempt.update(status='FAILED', error_code='http_' + str(response.status_code))
                return attempt
            result = response.json()
            if not isinstance(result, dict) or not isinstance(result.get('usage', {}), dict):
                raise ValueError('invalid_api_envelope')
            attempt['response_model'] = result.get('model')
            attempt['usage'] = result.get('usage') or {}
            choice = result['choices'][0]
            content = choice['message']['content']
            if not isinstance(content, str) or len(content) > budget['max_output_tokens'] * 30:
                raise ValueError('invalid_content')
            attempt['raw_response_text'] = content
            if choice.get('finish_reason') not in {'stop', None}:
                attempt.update(status='INVALID_OUTPUT', error_code='unfinished_model_response')
                return attempt
            attempt['payload'] = json.loads(content)
            check('research-extraction', attempt['payload'])
            attempt['status'] = 'OK'
        except requests.RequestException as exc:
            attempt.update(status='FAILED', error_code=type(exc).__name__)
        except (ValueError, KeyError, TypeError, IndexError, AttributeError):
            attempt.update(status='INVALID_OUTPUT', error_code='invalid_extraction_json')
        finally:
            attempt['elapsed_ms'] = round((time.monotonic() - started) * 1000)
        return attempt

    def extract(self, document, target):
        mode = self.config['routing_mode']
        input_text = select_text(document['text'], target, self.config['budget']['max_input_chars'])
        attempts, proposals, rejected, reasons = [], [], [], []

        def execute(role):
            attempt = self.call(role, document, target, input_text)
            attempts.append(attempt)
            accepted, bad = [], []
            if attempt['status'] in {'OK', 'SIMULATED'}:
                try:
                    accepted, bad = ground_claims(attempt['payload'], document, target, input_text)
                except ValueError:
                    attempt.update(status='INVALID_OUTPUT', error_code='invalid_extraction_schema')
            for item in accepted:
                item['proposed_by'] = [role]
            for item in bad:
                item.update(document_id=document['id'], role=role)
            rejected.extend(bad)
            proposals.extend(accepted)
            return attempt, accepted, bad

        first, small, bad = execute('large' if mode == 'large_only' else 'small')
        if mode == 'cascade':
            if first['status'] not in {'OK', 'SIMULATED'}:
                reasons.append('small_unavailable_or_invalid')
            if bad:
                reasons.append('grounding_or_field_failure')
            if any(c['flags'] for c in small):
                reasons.append('high_risk_claim')
            if not small and first['status'] in {'OK', 'SIMULATED'}:
                reasons.append('empty_small_extraction')
            sample = int(digest(document['id'])[:8], 16) / 0x100000000
            if sample < self.config['audit_fraction']:
                reasons.append('deterministic_audit_sample')
            if reasons:
                second, large, _ = execute('large')
                if second['status'] in {'OK', 'SIMULATED'} and {x['id'] for x in small} != {x['id'] for x in large}:
                    for c in proposals:
                        c['flags'].append('model_disagreement')
                elif second['status'] not in {'OK', 'SIMULATED'}:
                    for c in small:
                        c['flags'].append('large_review_not_completed')
        merged = {}
        for candidate in proposals:
            if candidate['id'] in merged:
                previous = merged[candidate['id']]
                previous['proposed_by'] = sorted(set(previous['proposed_by'] + candidate['proposed_by']))
                previous['flags'] = sorted(set(previous['flags'] + candidate['flags']))
            else:
                candidate['flags'] = sorted(set(candidate['flags']))
                merged[candidate['id']] = candidate
        return {'document_id': document['id'], 'routing_mode': mode,
                'input_truncated': len(input_text) < len(document['text']),
                'escalation_reasons': reasons, 'attempts': attempts,
                'candidates': list(merged.values()), 'rejected': rejected}
