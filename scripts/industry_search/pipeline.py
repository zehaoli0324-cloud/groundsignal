"""Plan, collect, extract and hand off unreviewed sources to the existing ledger."""
from copy import deepcopy
from html import escape
from pathlib import Path
import time

from .contracts import (REPO, VERSION, canonical_url, check, config_check, digest,
                        hostname, mentions, now, read_json, target_check, write_json)
from .documents import Fetcher, source_hint
from .models import ModelClient, ground_claims
from .planning import plan
from .providers import SearchClient


def fresh_directory(out):
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise ValueError('output_directory_must_be_new_or_empty')
    out.mkdir(parents=True, exist_ok=True)
    return out


def new_run(target, config):
    at = now()
    return {'schema_version': VERSION, 'id': 'run_' + digest([target, at])[:20],
            'created_at': at, 'finished_at': None, 'synthetic': False,
            'status': 'RUNNING', 'target': target, 'config': config,
            'plan': plan(target, config['budget']), 'search_records': [],
            'hits': [], 'documents': [], 'extractions': [], 'candidates': [],
            'diagnostics': [], 'coverage': {}, 'counts': {}, 'parent_run_id': None,
            'frozen_input_sha256': None, 'handoff': None}


def load_registry():
    registry = read_json(REPO / 'config/search.sources.json')
    for source in registry['sources']:
        if (hostname('https://' + source['domain']) != source['domain']
                or source['tier_hint'] not in {'T1', 'T2', 'T3', 'UNKNOWN'}
                or type(source['priority']) is not int):
            raise ValueError('invalid_source_registry')
    return registry


def merge_hits(records, seeds, target, registry, at):
    hits = {}

    def insert(url, title, snippet, ref, first_seen):
        try:
            url = canonical_url(url)
        except ValueError:
            return
        hit = hits.setdefault(url, {'url': url, 'title': title, 'snippet': snippet,
                                    'first_seen_at': first_seen, 'references': [],
                                    'source_hint': source_hint(url, target, registry)})
        hit['references'].append(ref)
        hit['first_seen_at'] = min(hit['first_seen_at'], first_seen)

    for url in seeds:
        insert(url, 'Explicit seed URL', '', {'provider': 'seed', 'query_id': None,
                                             'dimension': None, 'rank': 0}, at)
    for record in records:
        for row in record['hits']:
            insert(row['url'], row['title'], row['snippet'],
                   {'provider': record['provider'], 'query_id': record['query_id'],
                    'dimension': record['dimension'], 'rank': row['rank']}, record['searched_at'])
    # Round-robin domains after ranking, so one source cannot consume the whole page budget.
    ranked = sorted(hits.values(), key=lambda h: (
        -any(r['provider'] == 'seed' for r in h['references']),
        -int(mentions(h['title'] + ' ' + h['snippet'], target)),
        -h['source_hint']['priority'], min(r['rank'] for r in h['references']), h['url']))
    bins = {}
    for item in ranked:
        bins.setdefault(hostname(item['url']), []).append(item)
    result = []
    while any(bins.values()):
        for values in bins.values():
            if values:
                result.append(values.pop(0))
    return result


def frozen_hash(documents):
    return digest([{'id': d['id'], 'url': d['url'], 'resolved_url': d['resolved_url'],
                    'status': d['status'], 'title': d['title'], 'text_sha256': d['text_sha256'],
                    'raw_sha256': d['raw_sha256'], 'pages': d['pages'],
                    'first_seen_at': d['first_seen_at'], 'retrieved_at': d['retrieved_at'],
                    'synthetic': d['synthetic']} for d in documents])


def validate_run(run):
    check('search-run', run)
    target_check(run['target'])
    config_check(run['config'])
    ids = [d['id'] for d in run['documents']]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate_document_id')
    docs = {d['id']: d for d in run['documents']}
    if [c for e in run['extractions'] for c in e['candidates']] != run['candidates']:
        raise ValueError('candidate_queue_inconsistent_with_extractions')
    if len({e['document_id'] for e in run['extractions']}) != len(run['extractions']):
        raise ValueError('duplicate_document_extraction')
    for document in docs.values():
        canonical_url(document['url'])
        canonical_url(document['resolved_url'])
        if document['synthetic'] != run['synthetic']:
            raise ValueError('synthetic_source_mode_mismatch')
        if document['status'] in {'FETCHED', 'IRRELEVANT'} and digest(document['text']) != document['text_sha256']:
            raise ValueError('source_text_fingerprint_mismatch')
    if run['frozen_input_sha256'] != frozen_hash(run['documents']):
        raise ValueError('frozen_source_manifest_mismatch')
    seen = set()
    for candidate in run['candidates']:
        if candidate['id'] in seen or candidate['review_status'] != 'PENDING' or candidate['identity_status'] != 'UNCONFIRMED':
            raise ValueError('duplicate_or_promoted_candidate')
        seen.add(candidate['id'])
        document = docs.get(candidate['document_id'])
        if not document or document['status'] != 'FETCHED':
            raise ValueError('candidate_without_original_source')
        text = document['text']
        if text[candidate['quote_start']:candidate['quote_end']] != candidate['quote']:
            raise ValueError('candidate_quote_location_mismatch')
        fields = {k: candidate[k] for k in ('subject', 'predicate', 'object', 'product', 'stage', 'polarity', 'event_time', 'quote')}
        valid, bad = ground_claims({'claims': [fields]}, document, run['target'], text)
        if bad or candidate['id'] != valid[0]['id'] or candidate['pages'] != valid[0]['pages']:
            raise ValueError('candidate_grounding_mismatch')
    return run


def load_run(path):
    path = Path(path)
    run = validate_run(read_json(path))
    for doc in run['documents']:
        if not doc.get('raw_path'):
            continue
        raw = (path.parent / doc['raw_path']).resolve()
        if not raw.is_relative_to(path.parent.resolve()):
            raise ValueError('raw_source_path_outside_run')
        if digest(raw.read_bytes()) != doc['raw_sha256']:
            raise ValueError('raw_source_fingerprint_mismatch')
    return run


def handoff(run, out):
    """Original documents enter as EARLY_SIGNAL; proposals stay in lineage, not graph facts."""
    from ground_evidence import evidence_record, new_dataset, validate, write_manifest
    at = now()
    data = new_dataset(run['target']['name'] + '：搜索原文待审核',
                       'synthetic' if run['synthetic'] else 'collector_import', at)
    target = run['target']
    data['entities'] = [{'id': target['id'], 'name': target['name'], 'aliases': target['aliases'],
                         'identity_status': 'UNCONFIRMED'}]
    for doc in run['documents']:
        if doc['status'] != 'FETCHED':
            continue
        event_id = 'lead_' + digest([target['id'], doc['id']])[:20]
        data['events'].append({'id': event_id, 'title': doc['title'] or doc['url'],
                               'event_type': 'UNCLASSIFIED_LEAD', 'entity_ids': [target['id']],
                               'product': None, 'event_time': None, 'created_at': at})
        data['evidence'].append(evidence_record('e_' + digest([event_id, doc['text_sha256']])[:20],
            event_id, doc['resolved_url'], doc['text'], doc['first_seen_at'],
            retrieved_at=doc['retrieved_at'], processed_at=at,
            raw_fingerprint=doc['text_sha256'], fingerprint_scope='saved_parsed_source_text',
            access_mode='synthetic_fixture' if run['synthetic'] else 'research_fetch',
            lineage={'run_id': run['id'], 'synthetic': run['synthetic'],
                     'snapshot_sha256': run['frozen_input_sha256'], 'document_id': doc['id'],
                     'raw_sha256': doc['raw_sha256'], 'parser': doc['parser'],
                     'source_hint_not_verification': doc['source_hint'],
                     'candidate_ids': [c['id'] for c in run['candidates'] if c['document_id'] == doc['id']],
                     'identity_confirmed': False, 'note': '原文已保存，未完成主体和事实审核；候选不构成关系确认'}))
    validate(data)
    return str(write_manifest(Path(out) / 'ledger', data).relative_to(out))


def coverage(run):
    result = {}
    for dimension in run['target']['dimensions']:
        tasks = [q['id'] for q in run['plan']['queries'] if q['dimension'] == dimension]
        records = [r for r in run['search_records'] if r['query_id'] in tasks]
        urls = {h['url'] for h in run['hits'] if any(r['dimension'] == dimension for r in h['references'])}
        docs = {d['id'] for d in run['documents'] if d['url'] in urls and d['status'] == 'FETCHED'}
        result[dimension] = {'planned_queries': len(tasks),
                             'successful_searches': sum(r['status'] in {'OK', 'NO_RESULTS', 'SIMULATED'} for r in records),
                             'hit_urls': len(urls), 'fetched_documents': len(docs),
                             'pending_candidates': sum(c['document_id'] in docs for c in run['candidates'])}
    return result


def report(run, out):
    def safe(value):
        return escape(str(value)).replace('[', '［').replace(']', '］').replace('\n', ' ')
    lines = ['# GroundSignal 搜索运行', '',
             '- 运行：' + run['id'], '- 状态：' + run['status'],
             '- 数据：' + ('合成测试，未执行真实模型' if run['synthetic'] else '实际采集；所有主张待审核'),
             '- 搜索/抓取/模型请求：' + str(run['counts']), '',
             '## 覆盖与缺口', '', '| 维度 | 查询 | 成功检索 | URL | 正文 | 待审候选 |',
             '|---|---:|---:|---:|---:|---:|']
    for dimension, row in run['coverage'].items():
        lines.append('| ' + dimension + ' | ' + ' | '.join(str(x) for x in row.values()) + ' |')
    lines += ['', '## 原文与候选', '']
    for doc in run['documents']:
        lines += ['### ' + safe(doc['title']), '',
                  '- URL：' + safe(doc['resolved_url']), '- 获取状态：' + doc['status'],
                  '- SHA-256：' + str(doc['text_sha256']), '- 诊断：' + str(doc['error_code']), '']
        for c in run['candidates']:
            if c['document_id'] == doc['id']:
                lines += ['- **待审核**：' + safe(c['subject']) + ' → ' + c['predicate'] + ' → ' + safe(c['object']),
                          '  - 阶段/极性：' + c['stage'] + ' / ' + c['polarity'],
                          '  - 引文区间：' + str([c['quote_start'], c['quote_end']]) + '；标记：' + str(c['flags']),
                          '> ' + safe(c['quote']), '']
    lines += ['## 限制', '', '搜索成功、原文可定位和模型一致均不表示事实已确认。',
              '同源归并提示不证明独立性。时间范围是搜索提示，正文事件时间仍需审核。',
              '本版本按调用边界检查总时长；在途请求受单次超时约束。浏览器抓取预算计调用次数，不计子资源 HTTP 请求。',
              '无标签时质量为 UNASSESSED；合成演示不证明真实模型质量。', '']
    Path(out, 'report.md').write_text('\n'.join(lines), encoding='utf-8')


def finish(run, out, model, counts):
    run['candidates'] = [c for extraction in run['extractions'] for c in extraction['candidates']]
    run['finished_at'] = now()
    run['frozen_input_sha256'] = frozen_hash(run['documents'])
    run['counts'] = {**counts, 'model_calls': model.calls, 'large_model_calls': model.large_calls,
                     'simulated_model_calls': model.simulated_calls,
                     'pending_candidates': len(run['candidates'])}
    for extraction in run['extractions']:
        incomplete = [a for a in extraction['attempts'] if a['status'] not in {'OK', 'SIMULATED'}]
        if incomplete:
            run['diagnostics'].append({'code': 'model_stage_incomplete', 'document_id': extraction['document_id'],
                                       'roles': [{k: a[k] for k in ('role', 'status', 'error_code')} for a in incomplete]})
    fetched = [d for d in run['documents'] if d['status'] == 'FETCHED']
    if run['synthetic']:
        run['status'] = 'SYNTHETIC_ONLY'
    elif run['candidates']:
        run['status'] = 'CANDIDATES_PENDING_REVIEW'
    elif fetched:
        attempts = [a for e in run['extractions'] for a in e['attempts']]
        run['status'] = 'NO_CANDIDATES' if any(a['status'] == 'OK' for a in attempts) else 'COLLECTED_MODEL_NOT_COMPLETED'
    else:
        run['status'] = 'NO_USABLE_DOCUMENTS'
    run['coverage'] = coverage(run)
    validate_run(run)
    run['handoff'] = handoff(run, out)
    write_json(Path(out) / 'run.json', run)
    write_json(Path(out) / 'review-queue.json', {'schema_version': 'groundsignal.review-queue.v1',
               'run_id': run['id'], 'synthetic': run['synthetic'], 'candidates': run['candidates'],
               'rejected': [c for e in run['extractions'] for c in e['rejected']]})
    report(run, out)
    return run


def execute(target, config, out, fixture=None):
    target_check(target)
    config_check(config)
    out = fresh_directory(out)
    run = new_run(target, config)
    registry = load_registry()
    write_json(out / 'plan.json', run['plan'])
    started = time.monotonic()
    search = SearchClient(REPO / '.collector-cache' / 'research', config['budget'])
    fetcher = Fetcher(config['budget'], out, config['fetcher'], config['pdf_parser'])
    model = ModelClient(config, fixture=fixture.get('model_outputs') if fixture else None)

    def expired():
        return time.monotonic() - started >= config['budget']['max_elapsed_seconds']

    if fixture is not None:
        if fixture.get('synthetic') is not True or fixture['target'] != target:
            raise ValueError('fixture_requires_explicit_synthetic_target')
        run['synthetic'] = True
        for task in run['plan']['queries']:
            rows = fixture['search_hits'].get(task['dimension'], [])
            run['search_records'].append({'provider': 'fixture', 'query_id': task['id'],
                'query': task['query'], 'dimension': task['dimension'], 'searched_at': run['created_at'],
                'status': 'SIMULATED', 'cached': False, 'hits': rows, 'usage': {}, 'error_code': None})
    else:
        # First pass covers all dimensions with provider 1, then adds other providers.
        # A NOT_CONFIGURED provider costs zero requests and does not block later providers.
        for provider in config['providers']:
            for task in run['plan']['queries']:
                if expired():
                    break
                record = search.query(provider, task, config['budget']['results_per_query'])
                run['search_records'].append({**record, 'dimension': task['dimension']})
                write_json(out / 'search-progress.json', run['search_records'])
            if expired():
                break
    run['hits'] = merge_hits(run['search_records'], target['seed_urls'], target, registry, run['created_at'])
    if len(run['hits']) > config['budget']['max_documents']:
        run['diagnostics'].append({'code': 'document_budget_truncated', 'remaining': len(run['hits']) - config['budget']['max_documents']})
    for hit in run['hits'][:config['budget']['max_documents']]:
        if expired():
            run['diagnostics'].append({'code': 'elapsed_budget_exhausted'})
            break
        if fixture is not None:
            source = fixture['documents'].get(hit['url'])
            if source is None:
                raise ValueError('fixture_document_missing')
            doc = {'id': 'doc_' + digest(hit['url'])[:20], 'url': hit['url'], 'resolved_url': hit['url'],
                'title': source['title'], 'text': source['text'], 'pages': source.get('pages', []),
                'status': 'FETCHED', 'first_seen_at': run['created_at'], 'retrieved_at': now(),
                'error_code': None, 'raw_sha256': digest(source['text']), 'text_sha256': digest(source['text']),
                'raw_path': None, 'parser': 'synthetic_fixture', 'published_hint': None,
                'synthetic': True, 'fetcher': 'fixture'}
        else:
            doc = fetcher.fetch(hit, target)
        doc['source_hint'] = source_hint(doc['resolved_url'], target, registry)
        doc['duplicate_content_of'] = next((d['id'] for d in run['documents'] if doc['text_sha256']
                                             and d['text_sha256'] == doc['text_sha256']), None)
        run['documents'].append(doc)
        write_json(out / 'documents' / (doc['id'] + '.json'), doc)
        if doc['status'] == 'FETCHED':
            if not expired():
                run['extractions'].append(model.extract(doc, target))
            else:
                run['diagnostics'].append({'code': 'elapsed_budget_before_model', 'document_id': doc['id']})
    if not run['hits']:
        run['diagnostics'].append({'code': 'no_search_hits', 'note': 'No facts inferred from missing results'})
    return finish(run, out, model, {'search_calls': search.calls, 'fetch_calls': fetcher.calls})


def replay(source_path, config, out, fixture=None):
    """Compare models using identical captured text and acquisition timestamps."""
    source = load_run(source_path)
    config_check(config)
    if fixture is not None and not source['synthetic']:
        raise ValueError('cannot_apply_fixture_model_to_live_sources')
    if source['synthetic'] and fixture is None:
        raise ValueError('synthetic_replay_requires_explicit_fixture')
    out = fresh_directory(out)
    run = new_run(source['target'], config)
    run.update(parent_run_id=source['id'], synthetic=source['synthetic'],
               documents=deepcopy(source['documents']), plan=deepcopy(source['plan']),
               hits=deepcopy(source['hits']))
    # Replayed document paths refer to the capture, not to nonexistent files in the new directory.
    for doc in run['documents']:
        doc['raw_path'] = None
    run['diagnostics'].append({'code': 'frozen_source_replay', 'source_run_id': source['id'],
                               'source_snapshot_sha256': source['frozen_input_sha256']})
    model = ModelClient(config, fixture=fixture.get('model_outputs') if fixture else None)
    started = time.monotonic()
    for doc in run['documents']:
        if time.monotonic() - started >= config['budget']['max_elapsed_seconds']:
            run['diagnostics'].append({'code': 'elapsed_budget_exhausted'})
            break
        if doc['status'] == 'FETCHED':
            run['extractions'].append(model.extract(doc, run['target']))
    return finish(run, out, model, {'search_calls': 0, 'fetch_calls': 0})
