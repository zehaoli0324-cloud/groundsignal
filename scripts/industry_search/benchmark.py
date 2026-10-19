"""Offline collection evaluation against explicit, scoped reference evidence.

No LLM judges, network calls, automatic winner, legal certification or publication.
"""
from collections import Counter
from datetime import datetime, date
import math
from pathlib import Path
from statistics import median
from urllib.parse import urlsplit

from .contracts import DIMENSIONS, canonical_url, check, digest, now, read_json, write_json
from .evaluation import FIELDS
from .pipeline import fresh_directory, load_run

CRITICAL = {'WRONG_ENTITY', 'REVERSED_RELATION', 'STAGE_OVERCLAIM', 'POLARITY_ERROR', 'UNSUPPORTED'}
HIGH_RISK = {'OWNS', 'CONTROLS', 'INVESTED_IN', 'COMPETES_WITH'}


def instant(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def fraction(numerator, denominator):
    return numerator / denominator if denominator else None


def wilson(correct, total):
    if not total:
        return None
    z, p = 1.959963984540054, correct / total
    center = (p + z * z / (2 * total)) / (1 + z * z / total)
    width = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return [max(0, center - width), min(1, center + width)]


def benchmark_check(benchmark):
    check('research-benchmark', benchmark)
    groups, urls, labels = {}, {}, set()
    for source in benchmark['sources']:
        if source['id'] in groups:
            raise ValueError('duplicate_reference_group')
        groups[source['id']] = source
        for url in source['urls']:
            url = canonical_url(url)
            if url in urls:
                raise ValueError('reference_url_in_multiple_groups')
            urls[url] = source['id']
        if source['published_at'] and instant(source['published_at']) > instant(benchmark['as_of']):
            raise ValueError('reference_published_after_cutoff')
    for document in benchmark['documents']:
        key = (document['source_group'], document['text_sha256'])
        if key in labels or document['source_group'] not in groups:
            raise ValueError('duplicate_or_unknown_reference_document')
        labels.add(key)
        tuples = set()
        for claim in document['claims']:
            key = tuple(claim[x] for x in FIELDS)
            if key in tuples:
                raise ValueError('duplicate_gold_claim')
            tuples.add(key)
            if claim['event_time']:
                date.fromisoformat((claim['event_time'] + '-01-01')[:10])
    annotation = benchmark['annotation']
    if annotation['status'] == 'ADJUDICATED' and (
            len(annotation['annotators']) < 2 or not annotation['adjudicator']
            or not annotation['groups_reviewed'] or not groups
            or any(s['relevance'] is None for s in groups.values())
            or any(not d['annotation_complete'] for d in benchmark['documents'])):
        raise ValueError('adjudicated_benchmark_requires_complete_review')
    return groups, urls


def draft_benchmark(run):
    sources, documents = [], []
    seen = set()
    for doc in run['documents']:
        url = canonical_url(doc['resolved_url'])
        if url in seen:
            continue
        seen.add(url)
        group = 'provisional_' + digest(url)[:16]
        sources.append({'id': group, 'urls': [url], 'relevance': None,
                        'dimensions': [], 'required': False, 'published_at': None})
        if doc['status'] == 'FETCHED':
            documents.append({'source_group': group, 'text_sha256': doc['text_sha256'],
                              'annotation_complete': False, 'claims': []})
    return {'schema_version': 'groundsignal.research-benchmark.v1',
            'id': 'draft_' + run['id'], 'synthetic': run['synthetic'],
            'target_id': run['target']['id'], 'scope': 'DRAFT: define question, source pool and time window',
            'target_sha256': digest(run['target']),
            'as_of': run['finished_at'], 'split': 'development',
            'annotation': {'status': 'DRAFT', 'annotators': [], 'adjudicator': None, 'groups_reviewed': False},
            'sources': sources, 'documents': documents}


def review_template(run_path, benchmark_path):
    run = load_run(run_path)
    benchmark_check(read_json(benchmark_path))
    return {'schema_version': 'groundsignal.research-review.v1', 'run_id': run['id'],
            'run_sha256': digest(Path(run_path).read_bytes()),
            'benchmark_sha256': digest(Path(benchmark_path).read_bytes()),
            'documents': [{'document_id': d['id'], 'capture_permission': 'UNKNOWN',
                           'cloud_permission': 'UNKNOWN', 'basis': 'NOT_REVIEWED',
                           'reviewer': 'UNASSIGNED', 'reviewed_at': now()}
                          for d in run['documents'] if d['status'] == 'FETCHED'],
            'candidates': []}


def review_check(reviews, run, run_sha, benchmark_sha):
    if reviews is None:
        return {'documents': [], 'candidates': []}
    check('research-review', reviews)
    if (reviews['run_id'] != run['id'] or reviews['run_sha256'] != run_sha
            or reviews['benchmark_sha256'] != benchmark_sha):
        raise ValueError('review_binding_mismatch')
    docs = {d['id'] for d in run['documents']}
    candidates = {c['id'] for c in run['candidates']}
    seen_docs, seen_reviews = set(), set()
    for row in reviews['documents']:
        if row['document_id'] not in docs or row['document_id'] in seen_docs:
            raise ValueError('duplicate_or_unknown_document_review')
        seen_docs.add(row['document_id'])
        if ((row['capture_permission'] != 'UNKNOWN' or row['cloud_permission'] != 'UNKNOWN')
                and (row['basis'] == 'NOT_REVIEWED' or row['reviewer'] == 'UNASSIGNED')):
            raise ValueError('permission_decision_requires_basis_and_reviewer')
    for row in reviews['candidates']:
        key = (row['candidate_id'], row['reviewer'])
        if row['candidate_id'] not in candidates or key in seen_reviews:
            raise ValueError('duplicate_or_unknown_candidate_review')
        seen_reviews.add(key)
        if row['verdict'] == 'CORRECT' and row['error_types']:
            raise ValueError('correct_review_cannot_have_errors')
    return reviews


def retrieval(urls, groups, lookup, k):
    ranked, seen = [], set()
    for url in urls:
        url = canonical_url(url)
        key = lookup.get(url, 'unjudged:' + url)
        if key not in seen:
            ranked.append(key)
            seen.add(key)
    top = ranked[:k]
    relevant = {g for g, row in groups.items() if row['relevance'] is not None and row['relevance'] > 0}
    judged = [g for g in top if g in groups and groups[g]['relevance'] is not None]
    found = relevant.intersection(top)
    gain = lambda value: 2 ** value - 1
    dcg = sum(gain(groups[g]['relevance']) / math.log2(i + 2) for i, g in enumerate(top)) if len(judged) == len(top) else None
    ideal = sorted((s['relevance'] for s in groups.values() if s['relevance'] is not None), reverse=True)[:k]
    idcg = sum(gain(r) / math.log2(i + 2) for i, r in enumerate(ideal))
    return {'k': k, 'unique_ranked_groups': len(ranked), 'returned_at_k': len(top),
            'judged_at_k': len(judged), 'judgment_coverage_at_k': fraction(len(judged), len(top)),
            'known_relevant_reference_groups': len(relevant), 'found_relevant_at_k': len(found),
            'reference_recall_at_k': fraction(len(found), len(relevant)),
            'precision_on_judged_at_k': fraction(len(found), len(judged)),
            'ndcg_at_k': dcg / idcg if dcg is not None and idcg else None,
            'reference_reciprocal_rank': next((1 / (i + 1) for i, g in enumerate(top) if g in relevant), 0) if relevant else None,
            'ranked_reference_groups': top,
            'by_dimension': {dim: {'known_relevant': len(expected := {g for g in relevant if dim in groups[g]['dimensions']}),
                                   'found_at_k': len(expected.intersection(top)),
                                   'reference_recall_at_k': fraction(len(expected.intersection(top)), len(expected))}
                             for dim in DIMENSIONS}}


def labeled_claims(benchmark):
    labels = {(d['source_group'], d['text_sha256']): d for d in benchmark['documents'] if d['annotation_complete']}
    gold = {(*key, *(c[x] for x in FIELDS)) for key, d in labels.items() for c in d['claims']}
    return labels, gold


def claim_metrics(run, benchmark, lookup):
    labels, gold = labeled_claims(benchmark)
    keys, available = {}, set()
    for doc in run['documents']:
        if doc['status'] != 'FETCHED':
            continue
        group = lookup.get(canonical_url(doc['resolved_url'])) or lookup.get(canonical_url(doc['url']))
        key = (group, doc['text_sha256'])
        # A labeled group with a changed source version cannot quietly reuse old gold.
        if group and any(g == group for g, sha in labels) and key not in labels:
            raise ValueError('benchmark_document_fingerprint_mismatch')
        if key in labels:
            keys[doc['id']] = key
            available.add(key)
    predicted, covered = set(), 0
    for candidate in run['candidates']:
        if candidate['document_id'] in keys:
            covered += 1
            predicted.add((*keys[candidate['document_id']], *(candidate[x] for x in FIELDS)))
    conditional_gold = {g for g in gold if g[:2] in available}
    tp, fp = len(gold.intersection(predicted)), len(predicted - gold)
    denominator = tp + fp
    def breakdown(index):
        return {value: {'gold': len(g := {c for c in gold if c[index] == value}),
                        'predicted': len(p := {c for c in predicted if c[index] == value}),
                        'true_positive': len(g & p), 'precision': fraction(len(g & p), len(p)),
                        'end_to_end_reference_recall': fraction(len(g & p), len(g))}
                for value in sorted({c[index] for c in gold | predicted})}
    return {'labeled_reference_documents': len(labels), 'available_reference_document_versions': len(available),
            'gold_claims': len(gold), 'available_gold_claims': len(conditional_gold),
            'scored_unique_predictions': denominator, 'raw_labeled_candidates': covered,
            'unlabeled_candidates': len(run['candidates']) - covered,
            'candidate_label_coverage': fraction(covered, len(run['candidates'])),
            'true_positive': tp, 'false_positive': fp,
            'false_negative_on_fetched': len(conditional_gold - predicted),
            'false_negative_end_to_end': len(gold - predicted),
            'precision': fraction(tp, denominator), 'precision_wilson95': wilson(tp, denominator),
            'recall_on_fetched': fraction(tp, len(conditional_gold)),
            'end_to_end_reference_recall': fraction(tp, len(gold)),
            'by_predicate': breakdown(3), 'by_stage': breakdown(6), 'by_polarity': breakdown(7),
            'matching': 'source_group + text_sha256 + exact atomic fields; duplicate reprints do not multiply credit'}


def human_metrics(run, reviews, required_reviewers):
    records = reviews['candidates']
    humans = [r for r in records if r['reviewer_type'] == 'HUMAN']
    decisions = {c['id']: [r for r in humans if r['candidate_id'] == c['id']] for c in run['candidates']}
    reviewed = [rows for rows in decisions.values() if rows]
    unanimous = sum(all(r['verdict'] == 'CORRECT' for r in rows) for rows in reviewed)
    conflicts = sum(len({r['verdict'] for r in rows}) > 1 for rows in reviewed)
    errors = Counter(e for r in humans for e in r['error_types'])
    high = [c for c in run['candidates'] if c['predicate'] in HIGH_RISK or c['polarity'] != 'ASSERTED'
            or c['stage'] in {'MASS_PRODUCTION', 'ORDERED', 'SHIPPING'}]
    double = sum(len(decisions[c['id']]) >= required_reviewers
                 and all(r['verdict'] == 'CORRECT' for r in decisions[c['id']]) for c in high)
    timed = [r for r in humans if r.get('effort_minutes') is not None]
    minutes = sum(r['effort_minutes'] for r in timed) if timed and len(timed) == len(humans) else None
    return {'reviewed_candidates': len(reviewed), 'candidate_count': len(decisions),
            'human_review_coverage': fraction(len(reviewed), len(decisions)),
            'unanimously_correct': unanimous, 'unanimously_correct_fraction': fraction(unanimous, len(reviewed)),
            'conflicting_candidates': conflicts, 'uncertain_candidates': sum(any(r['verdict'] == 'UNCERTAIN' for r in rows) for rows in reviewed),
            'critical_error_reviews': sum(errors[e] for e in CRITICAL), 'errors_by_type': dict(errors),
            'high_risk_candidates': len(high), 'high_risk_fully_reviewed': double,
            'high_risk_review_coverage': fraction(double, len(high)),
            'model_judgments_excluded': sum(r['reviewer_type'] == 'MODEL' for r in records),
            'human_minutes_declared': minutes, 'timed_human_review_rows': len(timed),
            'minutes_per_unanimously_correct_candidate': fraction(minutes, unanimous) if minutes is not None else None,
            'identity_note': 'Reviewer identities and verdicts are declarations, not authenticated signatures.'}


def governance_metrics(run, reviews):
    permissions = {r['document_id']: r for r in reviews['documents']}
    fetched = [d for d in run['documents'] if d['status'] == 'FETCHED']
    missing = [d['id'] for d in fetched if permissions.get(d['id'], {}).get('capture_permission', 'UNKNOWN') == 'UNKNOWN']
    denied = [d['id'] for d in fetched if permissions.get(d['id'], {}).get('capture_permission') == 'DENIED']
    outbound = []
    for extraction in run['extractions']:
        for attempt in extraction['attempts']:
            host = urlsplit(attempt.get('endpoint', '')).hostname
            if (not attempt.get('synthetic') and host not in {None, 'localhost', '127.0.0.1', '::1'}
                    and attempt['status'] not in {'MODEL_NOT_RUN', 'BUDGET_EXHAUSTED', 'SIMULATED'}):
                outbound.append(extraction['document_id'])
    outbound = sorted(set(outbound))
    return {'status': 'DECLARATIONS_ONLY', 'legal_compliance': 'NOT_ASSESSED',
            'documents_missing_capture_permission': missing, 'documents_declared_capture_denied': denied,
            'outbound_attempt_document_ids': outbound,
            'outbound_with_denied_permission': [d for d in outbound if permissions.get(d, {}).get('cloud_permission') == 'DENIED'],
            'outbound_with_unknown_permission': [d for d in outbound if permissions.get(d, {}).get('cloud_permission', 'UNKNOWN') == 'UNKNOWN'],
            'note': 'Checks supplied declarations after the run; does not prevent access or certify rights.'}


def evaluate(run_path, benchmark_path, policy_path, reviews_path=None, allow_draft=False):
    run = load_run(run_path)
    benchmark, policy = read_json(benchmark_path), check('research-eval-policy', read_json(policy_path))
    groups, lookup = benchmark_check(benchmark)
    if (run['synthetic'] != benchmark['synthetic'] or run['target']['id'] != benchmark['target_id']
            or digest(run['target']) != benchmark['target_sha256']):
        raise ValueError('benchmark_run_scope_or_synthetic_mismatch')
    if benchmark['annotation']['status'] == 'DRAFT' and not allow_draft:
        raise ValueError('draft_benchmark_requires_explicit_allow_draft')
    run_sha, bench_sha = digest(Path(run_path).read_bytes()), digest(Path(benchmark_path).read_bytes())
    reviews = review_check(read_json(reviews_path) if reviews_path else None, run, run_sha, bench_sha)
    retrieved = retrieval([h['url'] for h in run['hits']], groups, lookup, policy['k'])
    claims = claim_metrics(run, benchmark, lookup)
    human = human_metrics(run, reviews, policy['high_risk_human_reviewers'])
    labels, gold = labeled_claims(benchmark)
    doc_keys = {d['id']: (lookup.get(canonical_url(d['resolved_url'])) or lookup.get(canonical_url(d['url'])),
                         d['text_sha256']) for d in run['documents']}
    correctness = {c['id']: (*doc_keys[c['document_id']], *(c[x] for x in FIELDS)) in gold
                   for c in run['candidates'] if doc_keys[c['document_id']] in labels}
    human['gold_disagreement_review_rows'] = sum(
        (r['verdict'] == 'CORRECT') != correctness[r['candidate_id']]
        for r in reviews['candidates'] if r['reviewer_type'] == 'HUMAN'
        and r['candidate_id'] in correctness and r['verdict'] != 'UNCERTAIN')
    governance = governance_metrics(run, reviews)
    attempts = [a for e in run['extractions'] for a in e['attempts']]
    if any(a.get('synthetic') != run['synthetic'] or (not run['synthetic'] and a['status'] == 'SIMULATED')
           for a in attempts):
        raise ValueError('mixed_synthetic_model_attempt')
    real_model = any(a['status'] == 'OK' and not a.get('synthetic') for a in attempts)
    fetched = [d for d in run['documents'] if d['status'] == 'FETCHED']
    fetched_groups = {lookup.get(canonical_url(d['resolved_url'])) or lookup.get(canonical_url(d['url'])) for d in fetched}
    required = {s['id'] for s in groups.values() if s['required']}
    relevant = {s['id'] for s in groups.values() if s['relevance'] is not None and s['relevance'] > 0}
    lags = [max(0, (instant(d['first_seen_at']) - instant(groups[group]['published_at'])).total_seconds())
            for d in fetched if (group := lookup.get(canonical_url(d['resolved_url']))) in groups
            and groups[group]['published_at'] and instant(d['first_seen_at']) >= instant(groups[group]['published_at'])]
    elapsed = (instant(run['finished_at']) - instant(run['created_at'])).total_seconds()
    if elapsed < 0:
        raise ValueError('invalid_run_timeline')
    budgets = {'search_calls': 'max_search_calls', 'fetch_calls': 'max_fetch_calls',
               'model_calls': 'max_model_calls', 'large_model_calls': 'max_large_calls'}
    breaches = []
    for count, cap in budgets.items():
        value = run['counts'].get(count)
        if type(value) is not int or value < 0:
            raise ValueError('invalid_run_call_count')
        if value > run['config']['budget'][cap]:
            breaches.append(count)
    if len(run['documents']) > run['config']['budget']['max_documents']:
        breaches.append('max_documents')
    if len(run['plan']['queries']) > run['config']['budget']['max_queries']:
        breaches.append('max_queries')
    gates = []

    def gate(name, value, threshold, direction='min'):
        met = value is not None and (value >= threshold if direction == 'min' else value <= threshold)
        gates.append({'name': name, 'status': 'UNASSESSED' if value is None else 'MET' if met else 'FAILED',
                      'value': value, 'threshold': threshold})

    gate('reference_sample_size', len(relevant), policy['min_reference_groups'])
    gate('gold_claim_sample_size', claims['gold_claims'], policy['min_labeled_claims'])
    for name, value in [('retrieval_recall', retrieved['reference_recall_at_k']),
                        ('rank_judgment_coverage', retrieved['judgment_coverage_at_k']),
                        ('extraction_precision', claims['precision']),
                        ('end_to_end_recall', claims['end_to_end_reference_recall']),
                        ('candidate_label_coverage', claims['candidate_label_coverage']),
                        ('human_review_coverage', human['human_review_coverage'])]:
        gate(name, value, policy['min_' + name])
    for dimension, row in retrieved['by_dimension'].items():
        if row['known_relevant']:
            gate('retrieval_recall:' + dimension, row['reference_recall_at_k'], policy['min_retrieval_recall'])
    gate('high_risk_review_coverage', human['high_risk_review_coverage'] if human['high_risk_candidates'] else 1, 1)
    gate('critical_error_reviews', human['critical_error_reviews'] if human['reviewed_candidates'] else None, 0, 'max')
    gate('unanimous_human_correctness', human['unanimously_correct_fraction'], 1)
    gate('human_gold_disagreements', human['gold_disagreement_review_rows'] if human['reviewed_candidates'] else None, 0, 'max')
    gate('budget_breaches', len(breaches), 0, 'max')
    gate('missing_required_reference_groups', len(required - fetched_groups), 0, 'max')
    permission_unknown = len(governance['documents_missing_capture_permission']) + len(governance['outbound_with_unknown_permission'])
    permission_denied = len(governance['documents_declared_capture_denied']) + len(governance['outbound_with_denied_permission'])
    gate('declared_permission_violations', permission_denied, 0, 'max')
    gate('permission_declaration_completeness', 0 if permission_unknown else 1, 1)
    gate('live_run', int(not run['synthetic']), 1)
    gate('adjudicated_reference', int(benchmark['annotation']['status'] == 'ADJUDICATED'), 1)
    quality = 'SYNTHETIC_ONLY' if run['synthetic'] else 'ANNOTATION_DRAFT' if benchmark['annotation']['status'] == 'DRAFT' else 'REAL_LABELED_SUBSET'
    ready = not run['synthetic'] and all(g['status'] == 'MET' for g in gates)
    actual_attempts = [a for a in attempts if not a.get('synthetic')
                       and a['status'] not in {'MODEL_NOT_RUN', 'BUDGET_EXHAUSTED', 'SIMULATED'}]
    token_rows = [a for a in actual_attempts if all(type(a['usage'].get(k)) is int and a['usage'][k] >= 0
                                                  for k in ('prompt_tokens', 'completion_tokens'))]
    token_complete = bool(actual_attempts) and len(token_rows) == len(actual_attempts)
    return {'schema_version': 'groundsignal.collection-evaluation.v1', 'evaluated_at': now(),
            'run_id': run['id'], 'run_sha256': run_sha, 'benchmark_id': benchmark['id'],
            'benchmark_sha256': bench_sha, 'policy_sha256': digest(Path(policy_path).read_bytes()),
            'reviews_sha256': digest(Path(reviews_path).read_bytes()) if reviews_path else None,
            'synthetic': run['synthetic'], 'quality_status': quality, 'scope': benchmark['scope'],
            'split': benchmark['split'], 'as_of': benchmark['as_of'], 'retrieval': retrieved,
            'retrieval_by_provider': {provider: retrieval(
                [hit['url'] for record in run['search_records'] if record['provider'] == provider for hit in record['hits']],
                groups, lookup, policy['k']) for provider in sorted({r['provider'] for r in run['search_records']})},
            'acquisition': {'attempted_documents': len(run['documents']), 'fetched_documents': len(fetched),
                            'fetch_success_fraction': fraction(len(fetched), len(run['documents'])),
                            'relevant_reference_groups_captured': len(relevant & fetched_groups),
                            'reference_capture_recall': fraction(len(relevant & fetched_groups), len(relevant)),
                            'missing_required_reference_groups': sorted(required - fetched_groups),
                            'duplicate_content_documents': sum(bool(d.get('duplicate_content_of')) for d in fetched),
                            'known_publication_capture_lag_seconds_median': median(lags) if lags else None,
                            'lag_measured_documents': len(lags)},
            'extraction': claims, 'human_review': human, 'governance': governance,
            'operations': {'counts': run['counts'], 'wall_seconds': elapsed,
                           'real_successful_model_response': real_model,
                           'search_statuses': dict(Counter(r['status'] for r in run['search_records'])),
                           'model_attempt_statuses': dict(Counter(a['status'] for a in attempts)),
                           'budget_breaches': breaches,
                           'input_truncated_documents': sum(e['input_truncated'] for e in run['extractions']),
                           'input_tokens': sum(a['usage']['prompt_tokens'] for a in token_rows) if token_complete else None,
                           'output_tokens': sum(a['usage']['completion_tokens'] for a in token_rows) if token_complete else None,
                           'attempts_with_complete_token_usage': len(token_rows), 'token_usage_complete': token_complete,
                           'money_cost': None, 'cost_per_correct_claim': None},
            'gates': gates, 'decision': 'REQUIRES_HUMAN_RELEASE' if ready else 'NOT_READY',
            'overall_score': None, 'note': 'Scoped reference-set metrics; no automatic winner or legal/factual certification.'}


def save_report(report, out):
    out = fresh_directory(out)
    write_json(out / 'evaluation.json', report)
    import csv
    with (out / 'metrics.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['layer', 'metric', 'value'])
        for layer in ('retrieval', 'acquisition', 'extraction', 'human_review', 'operations'):
            for key, value in report[layer].items():
                if value is None or type(value) in {int, float, str, bool}:
                    writer.writerow([layer, key, '' if value is None else value])
    lines = ['# GroundSignal 采集评测', '', '- 状态：' + report['quality_status'],
             '- 决策：' + report['decision'], '- run SHA：' + report['run_sha256'],
             '- benchmark SHA：' + report['benchmark_sha256'],
             '', '指标限于明确定义的参考集；未知项保持 null。合成数据不证明真实模型效果。',
             '', '| 门槛 | 状态 | 实际值 | 阈值 |', '|---|---|---:|---:|']
    lines += [f"| {g['name']} | {g['status']} | {g['value']} | {g['threshold']} |" for g in report['gates']]
    lines += ['', '分层指标、分母与已知缺口见 evaluation.json / metrics.csv。',
              '权限检查仅核对声明，不阻止访问或证明合法性；审核身份未进行签名认证。', '']
    (out / 'report.md').write_text('\n'.join(lines), encoding='utf-8')
    return out
