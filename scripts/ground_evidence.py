"""Small, deterministic evidence ledger with point-in-time event aggregation.

Evidence, reviews and event updates are append-only records. A source's authority
does not establish a claim; only explicit, dated reviews can promote an event.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import csv
import hashlib
import io
import json
from pathlib import Path
import re
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker


VERSION = 'groundsignal.ground-evidence.v1'
SNAPSHOT_VERSION = 'groundsignal.event-snapshot.v1'
FEED_VERSION = 'groundsignal.event-feed.v1'
DECISIONS = {'SUPPORT', 'CONFIRM', 'COUNTER', 'REJECT'}
STATES = {'EARLY_SIGNAL', 'WATCH', 'SUPPORTED', 'VERIFIED', 'DISPUTED',
          'STALE', 'SUPERSEDED', 'REJECTED'}
TIERS = {'T1', 'T2', 'T3', 'UNKNOWN'}
MODES = {'repository_backfill', 'collector_import', 'synthetic'}


@lru_cache(maxsize=1)
def structural_validator():
    path = Path(__file__).resolve().parents[1] / 'schemas/ground-evidence.v1.schema.json'
    schema = json.loads(path.read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def instant(value):
    if not isinstance(value, str):
        raise ValueError('时间必须是带时区的 ISO 8601 字符串')
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('无效时间：' + value) from exc
    if dt.tzinfo is None:
        raise ValueError('时间必须包含时区：' + value)
    return dt.astimezone(timezone.utc)


def fingerprint(value):
    if not isinstance(value, str):
        value = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def legal_metadata():
    # Public accessibility never implies a reviewed redistribution licence.
    return {'public_access': 'UNKNOWN', 'auth_required': 'UNKNOWN',
            'robots_reviewed': False, 'tos_reviewed': False,
            'redistribution_status': 'UNKNOWN', 'personal_data': 'UNASSESSED',
            'reviewer': None, 'reviewed_at': None}


def new_dataset(title, mode, now=None):
    return {'schema_version': VERSION, 'title': title, 'mode': mode,
            'created_at': now or utc_now(), 'stale_after_days': 45,
            'entities': [], 'events': [], 'evidence': [], 'reviews': [],
            'event_updates': []}


def evidence_record(record_id, event_id, source_url, excerpt, observed_at,
                    evidence_type='disclosure', **extra):
    record = {'id': record_id, 'event_id': event_id,
              'evidence_type': evidence_type, 'source_url': source_url,
              'source_domain': urlparse(source_url).netloc,
              'source_tier': 'UNKNOWN', 'published_at': None,
              'first_seen_at': observed_at, 'retrieved_at': observed_at,
              'processed_at': observed_at, 'raw_fingerprint': fingerprint(excerpt),
              'fingerprint_scope': 'saved_excerpt', 'source_independence_group': None,
              'content_excerpt': excerpt, 'access_mode': 'manual_import',
              'original_source_checked': False, 'legal_basis': legal_metadata(),
              'cited_source_url': None, 'lineage': {}}
    record.update(extra)
    return record


def _unique(records, label):
    ids = []
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get('id'), str) or not record['id']:
            raise ValueError(label + ' 必须有非空字符串 id')
        ids.append(record['id'])
    if len(ids) != len(set(ids)):
        raise ValueError(label + ' id 重复')
    return {r['id']: r for r in records}


def validate(data):
    """Fail closed on malformed times, references, reviews and provenance."""
    error = next(structural_validator().iter_errors(data), None)
    if error:
        location = '/'.join(str(x) for x in error.absolute_path) or 'ledger'
        raise ValueError('字段契约不满足：' + location + ' (' + error.validator + ')')
    if data.get('schema_version') != VERSION or data.get('mode') not in MODES:
        raise ValueError('不支持的数据版本或模式')
    instant(data['created_at'])
    ttl = data.get('stale_after_days')
    if type(ttl) is not int or not 1 <= ttl <= 3650:
        raise ValueError('stale_after_days 必须是 1–3650 的整数')
    entities = _unique(data['entities'], 'entity')
    events = _unique(data['events'], 'event')
    evidence = _unique(data['evidence'], 'evidence')
    _unique(data['reviews'], 'review')
    _unique(data['event_updates'], 'event update')
    for item in entities.values():
        if not isinstance(item.get('name'), str) or not item['name'].strip():
            raise ValueError('实体缺少名称')
    for event in events.values():
        instant(event['created_at'])
        if not event.get('title') or not event.get('event_type'):
            raise ValueError('事件缺少标题或类型')
        if not event.get('entity_ids') or any(x not in entities for x in event['entity_ids']):
            raise ValueError('事件包含未归一的实体')
        # Month/year precision stays month/year; never fabricate a day or clock time.
        when = event.get('event_time')
        if when is not None and not re.fullmatch(r'\d{4}(?:-\d{2}(?:-\d{2})?)?', when):
            raise ValueError('event_time 必须保留原始年/月/日精度')
        if when is not None:
            fmt = {4: '%Y', 7: '%Y-%m', 10: '%Y-%m-%d'}[len(when)]
            try:
                datetime.strptime(when, fmt)
            except ValueError as exc:
                raise ValueError('event_time 包含无效日期') from exc
    for item in evidence.values():
        if item['event_id'] not in events:
            raise ValueError('证据指向不存在的事件')
        if item.get('source_tier') not in TIERS:
            raise ValueError('未知来源层级')
        url = urlparse(item.get('source_url', ''))
        if url.scheme not in {'http', 'https'} or not url.netloc or url.username or url.password:
            raise ValueError('证据来源必须是无凭据的 HTTP(S) URL')
        if item.get('source_domain') != url.netloc:
            raise ValueError('source_domain 与 URL 不一致')
        if item.get('cited_source_url'):
            cited = urlparse(item['cited_source_url'])
            if cited.scheme not in {'http', 'https'} or not cited.netloc or cited.username or cited.password:
                raise ValueError('引用网址必须是无凭据的 HTTP(S) URL')
        published = instant(item['published_at']) if item.get('published_at') else None
        seen, fetched, processed = [instant(item[k]) for k in
                                    ('first_seen_at', 'retrieved_at', 'processed_at')]
        if seen > fetched or fetched > processed or (published and published > seen):
            raise ValueError('时间顺序错误：published ≤ first_seen ≤ retrieved ≤ processed')
        if instant(events[item['event_id']]['created_at']) > processed:
            raise ValueError('事件创建时间晚于证据处理时间')
        if not re.fullmatch(r'[0-9a-f]{64}', item.get('raw_fingerprint', '')):
            raise ValueError('证据缺少 SHA-256 指纹')
        if not item.get('fingerprint_scope') or not item.get('access_mode') or not item.get('lineage'):
            raise ValueError('证据缺少采集方式、指纹范围或 lineage')
        if not isinstance(item.get('content_excerpt'), str) or not item['content_excerpt'].strip():
            raise ValueError('证据缺少摘录')
        legal = item.get('legal_basis', {})
        if legal.get('redistribution_status') not in {'UNKNOWN', 'ALLOWED', 'RESTRICTED'}:
            raise ValueError('缺少来源再分发状态')
        if legal.get('redistribution_status') != 'UNKNOWN' and not (
                legal.get('reviewer') and legal.get('reviewed_at')):
            raise ValueError('来源授权判断必须带审核人和时间')
        if type(item.get('original_source_checked')) is not bool:
            raise ValueError('必须声明是否读取并核对原始来源')
        synthetic = item['access_mode'] == 'synthetic_fixture' or item['lineage'].get('synthetic')
        if bool(synthetic) != (data['mode'] == 'synthetic'):
            raise ValueError('模拟证据必须与真实数据模式隔离')
    reviewed_instants = set()
    for review in data['reviews']:
        item = evidence.get(review.get('evidence_id'))
        if not item or review.get('decision') not in DECISIONS:
            raise ValueError('审核引用或决定无效')
        if instant(review['at']) < instant(item['processed_at']):
            raise ValueError('审核不能早于证据可用时间')
        if not review.get('reviewer') or not review.get('reason'):
            raise ValueError('审核必须有审核人和原因')
        key = (review['evidence_id'], instant(review['at']))
        if key in reviewed_instants:
            raise ValueError('同一证据在同一时刻存在多个审核，无法确定顺序')
        reviewed_instants.add(key)
        group = review.get('independence_group')
        if group is not None and (not isinstance(group, str) or not group.strip()):
            raise ValueError('来源组必须是非空字符串或 null')
        if review['decision'] in {'SUPPORT', 'CONFIRM', 'COUNTER'}:
            quote = review.get('supporting_quote', '')
            if not quote or quote not in item['content_excerpt']:
                raise ValueError('审核支持句必须能在保存的摘录中定位')
        if review['decision'] == 'CONFIRM' and not (
                item['source_tier'] == 'T1' and item['original_source_checked']):
            raise ValueError('确认必须核对一手来源；高层级标签不能代替验证')
    for update in data['event_updates']:
        if update.get('event_id') not in events or update.get('action') not in {'REJECT', 'SUPERSEDE'}:
            raise ValueError('事件更新无效')
        if not update.get('reason') or not update.get('reviewer'):
            raise ValueError('事件更新缺少审核人或原因')
        if instant(update['at']) < instant(events[update['event_id']]['created_at']):
            raise ValueError('事件更新不能早于事件')
        if update['action'] == 'SUPERSEDE':
            replacement = events.get(update.get('replacement_event_id'))
            if not replacement or replacement['id'] == update['event_id']:
                raise ValueError('替代事件无效')
            matching = [e for e in evidence.values() if e['event_id'] == replacement['id']
                        and instant(e['processed_at']) <= instant(update['at'])]
            if not matching:
                raise ValueError('替代事件在更新时尚不可见')
    for update in data['event_updates']:
        if update['action'] == 'SUPERSEDE':
            replacement = _state(data, events[update['replacement_event_id']], instant(update['at']))
            if replacement['status'] not in {'SUPPORTED', 'VERIFIED'}:
                raise ValueError('替代事件必须在替代时已被支持或确认')
    return data


def load(path):
    path = Path(path)
    data = json.loads(path.read_text(encoding='utf-8'))
    if 'evidence_files' in data:
        if 'evidence' in data:
            raise ValueError('manifest 不应同时内嵌和引用 evidence')
        files = data.pop('evidence_files')
        data['evidence'] = []
        for relative in files:
            target = (path.parent / relative).resolve()
            if not target.is_relative_to(path.parent.resolve()):
                raise ValueError('evidence 文件不能越出 manifest 目录')
            data['evidence'].append(json.loads(target.read_text(encoding='utf-8')))
    return validate(data)


def dump(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_manifest(folder, data):
    validate(data)
    folder = Path(folder)
    manifest = {k: v for k, v in data.items() if k != 'evidence'}
    manifest['evidence_files'] = []
    for record in data['evidence']:
        # IDs and categories cannot introduce arbitrary filesystem paths.
        if not re.fullmatch(r'[A-Za-z0-9_-]+', record['id'] + record['evidence_type']):
            raise ValueError('证据 id/type 不可用作安全文件名')
        relative = record['evidence_type'] + '/' + record['id'] + '.json'
        dump(folder / relative, record)
        manifest['evidence_files'].append(relative)
    dump(folder / 'manifest.json', manifest)
    return folder / 'manifest.json'


def _groups(items, latest):
    """Count reviewed origins, merging both declared syndication and equal payloads."""
    parents = {e['id']: e['id'] for e in items}

    def root(x):
        while parents[x] != x:
            x = parents[x]
        return x

    for i, a in enumerate(items):
        ga = latest[a['id']].get('independence_group')
        for b in items[:i]:
            gb = latest[b['id']].get('independence_group')
            if (ga and ga == gb) or a['raw_fingerprint'] == b['raw_fingerprint']:
                parents[root(a['id'])] = root(b['id'])
    known = {root(e['id']) for e in items if latest[e['id']].get('independence_group')}
    return len(known)


def _state(data, event, cutoff):
    items = [e for e in data['evidence'] if e['event_id'] == event['id']
             and instant(e['processed_at']) <= cutoff]
    if not items or instant(event['created_at']) > cutoff:
        return None
    ids = {e['id'] for e in items}
    latest = {}
    for review in sorted(data['reviews'], key=lambda r: (instant(r['at']), r['id'])):
        if review['evidence_id'] in ids and instant(review['at']) <= cutoff:
            latest[review['evidence_id']] = review
    support = [e for e in items if latest.get(e['id'], {}).get('decision') in {'SUPPORT', 'CONFIRM'}]
    confirmation = [e for e in support if latest[e['id']]['decision'] == 'CONFIRM']
    counter = [e for e in items if latest.get(e['id'], {}).get('decision') == 'COUNTER']
    independent = _groups(support, latest)
    if counter:
        status, reason = 'DISPUTED', '存在已审核反证，等待裁决'
    elif confirmation:
        status, reason = 'VERIFIED', '一手来源已被明确核对并确认'
    elif independent >= 2:
        status, reason = 'SUPPORTED', '至少两个已审核且独立的来源支持'
    elif support:
        status, reason = 'WATCH', '已有支持证据，独立来源数量尚不足'
    elif all(latest.get(e['id'], {}).get('decision') == 'REJECT' for e in items):
        status, reason = 'REJECTED', '所有可见证据已被拒绝'
    else:
        status, reason = 'EARLY_SIGNAL', '未审核线索，不表示商业事实已成立'
    updates = [u for u in data['event_updates'] if u['event_id'] == event['id']
               and instant(u['at']) <= cutoff]
    update = max(updates, key=lambda u: (instant(u['at']), u['id'])) if updates else None
    if update:
        status = 'SUPERSEDED' if update['action'] == 'SUPERSEDE' else 'REJECTED'
        reason = update['reason']
    last_check = max((instant(r['at']) for r in latest.values()), default=None)
    if status in {'WATCH', 'SUPPORTED', 'VERIFIED'} and last_check and (
            cutoff >= last_check + timedelta(days=data['stale_after_days'])):
        status, reason = 'STALE', '超过复核间隔；过期不代表关系已终止'
    visible_evidence = []
    for item in sorted(items, key=lambda e: (instant(e['processed_at']), e['id'])):
        displayed = dict(item)
        displayed['review'] = latest.get(item['id'])
        # Future reviews and revisions are never attached to an older snapshot.
        visible_evidence.append(displayed)
    return {'event_id': event['id'], 'title': event['title'],
            'event_type': event['event_type'], 'entity_ids': event['entity_ids'],
            'product': event.get('product'), 'event_time': event.get('event_time'),
            'status': status, 'status_reason': reason,
            'evidence_count': len(items), 'independent_sources': independent,
            'unresolved_origins': sum(not latest.get(e['id'], {}).get('independence_group') for e in items),
            'last_verified_at': last_check.isoformat() if last_check else None,
            'superseded_at': update['at'] if update and status == 'SUPERSEDED' else None,
            'superseded_by': update.get('replacement_event_id') if update and status == 'SUPERSEDED' else None,
            'evidence': visible_evidence}


def boundaries(data):
    times = {instant(data['created_at'])}
    times.update(instant(e['processed_at']) for e in data['evidence'])
    times.update(instant(r['at']) for r in data['reviews'])
    times.update(instant(u['at']) for u in data['event_updates'])
    times.update(instant(r['at']) + timedelta(days=data['stale_after_days']) for r in data['reviews'])
    first = min(times) - timedelta(seconds=1)
    return sorted({first, *times})


def snapshot(data, as_of, check=True):
    if check:
        validate(data)
    cutoff = instant(as_of)
    states = []
    for event in data['events']:
        state = _state(data, event, cutoff)
        if state is None:
            continue
        first_supported = None
        for at in boundaries(data):
            if at > cutoff:
                break
            past = _state(data, event, at)
            if past and past['status'] in {'SUPPORTED', 'VERIFIED'}:
                first_supported = at
                break
        confirmed_dates = [instant(e['published_at']) for e in state['evidence']
                           if e.get('published_at') and e.get('review')
                           and e['review']['decision'] == 'CONFIRM']
        confirmed = min(confirmed_dates) if confirmed_dates else None
        lead = None
        if data['mode'] == 'repository_backfill':
            lead_reason = '历史回填；不能证明历史监测提前量'
        elif not first_supported or not confirmed:
            lead_reason = '缺少当时可见的支持或公开确认时间'
        elif state['status'] in {'DISPUTED', 'REJECTED', 'SUPERSEDED', 'STALE'}:
            lead_reason = '当前结论需复核或已失效，不计算提前量'
        else:
            lead = round((confirmed - first_supported).total_seconds() / 86400, 4)
            lead_reason = '模拟值，不代表真实检测表现' if data['mode'] == 'synthetic' else '基于已记录的可用与确认时间'
        state.update(first_supported_at=first_supported.isoformat() if first_supported else None,
                     public_confirmation_at=confirmed.isoformat() if confirmed else None,
                     lead_time_days=lead, lead_time_note=lead_reason)
        states.append(state)
    visible_entity_ids = {i for e in states for i in e['entity_ids']}
    return {'schema_version': SNAPSHOT_VERSION, 'mode': data['mode'],
            'title': data['title'], 'as_of': cutoff.isoformat(),
            'entities': [e for e in data['entities'] if e['id'] in visible_entity_ids],
            'events': sorted(states, key=lambda e: e['event_id']),
            'metrics': {'visible_events': len(states),
                        'states': dict(Counter(e['status'] for e in states)),
                        'visible_evidence': sum(e['evidence_count'] for e in states),
                        'independent_supports': sum(e['independent_sources'] for e in states),
                        'lead_time_measured_events': sum(e['lead_time_days'] is not None for e in states)}}


def feed_rows(view):
    return [{k: e.get(k) for k in ('event_id', 'title', 'event_type', 'product', 'event_time',
                                  'status', 'evidence_count', 'independent_sources',
                                  'first_supported_at', 'public_confirmation_at', 'lead_time_days',
                                  'lead_time_note', 'last_verified_at', 'superseded_at', 'superseded_by')}
            | {'schema_version': FEED_VERSION, 'entity_ids': e['entity_ids'], 'as_of': view['as_of'], 'mode': view['mode'],
               'evidence_ids': [x['id'] for x in e['evidence']],
               'source_urls': [x['source_url'] for x in e['evidence']]}
            for e in view['events']]


def csv_feed(view):
    rows = feed_rows(view)
    fields = list(rows[0]) if rows else ['event_id', 'status', 'as_of', 'mode']
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        cleaned = {}
        for k, value in row.items():
            if isinstance(value, list):
                value = json.dumps(value, ensure_ascii=False)
            if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
                value = "'" + value
            cleaned[k] = value
        writer.writerow(cleaned)
    return stream.getvalue()


def export(folder, view):
    folder = Path(folder)
    dump(folder / 'snapshot.json', view)
    rows = feed_rows(view)
    (folder / 'events.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
    (folder / 'events.csv').write_text(csv_feed(view), encoding='utf-8-sig')


def render_report(datasets, path, template):
    series = []
    for dataset in datasets:
        validate(dataset)
        points = [snapshot(dataset, t.isoformat(), check=False) for t in boundaries(dataset)]
        # The UI is an offline viewer, not an access-control boundary: the bundle
        # contains all times, but displayed/exported snapshots are cut off in Python.
        activity = [instant(dataset['created_at'])]
        activity += [instant(x['processed_at']) for x in dataset['evidence']]
        activity += [instant(x['at']) for x in dataset['reviews'] + dataset['event_updates']]
        series.append({'title': dataset['title'], 'mode': dataset['mode'],
                       'default_at': max(activity).isoformat(), 'snapshots': points})
    payload = json.dumps({'datasets': series}, ensure_ascii=False)
    payload = payload.replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    payload = payload.replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    html = Path(template).read_text(encoding='utf-8').replace('__EVIDENCE_DATA__', payload)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding='utf-8')
    return path
