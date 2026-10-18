#!/usr/bin/env python3
"""Issue #1 MVP: migrate saved leads, review them, replay and export events."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import sys
from urllib.parse import quote

from ground_evidence import (VERSION, dump, evidence_record, export, fingerprint,
                             load, new_dataset, render_report, snapshot,
                             utc_now, validate, write_manifest)

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '5506f8fa131f446e884762996387afc0b4d29b5d'


def migrate_repository(vault, observed_at=None):
    import yaml
    now = observed_at or utc_now()
    data = new_dataset('现有 AI Compute 事件：历史回填', 'repository_backfill', now)
    pins = json.loads((ROOT / 'examples/ground-evidence/repository-source-fingerprints.json').read_text(encoding='utf-8'))
    if pins['repository_commit'] != BASE_SHA:
        raise ValueError('回填来源与固定的仓库版本不一致')
    aliases = {}
    for path in sorted((Path(vault) / '04-事件').glob('*.md')):
        raw = path.read_text(encoding='utf-8')
        if pins['files'].get(path.name) != fingerprint(raw):
            raise ValueError('事件笔记与固定源版本不同，不能复用旧来源 URL：' + path.name)
        match = re.match(r'^---\n(.*?)\n---\n(.*)', raw, re.S)
        if not match:
            raise ValueError('缺少事件 frontmatter：' + str(path))
        fm, body = yaml.safe_load(match.group(1)), match.group(2)
        names = re.findall(r'\[\[([^\]|]+)', str(fm.get('entity', '')))
        if not names:
            raise ValueError('事件没有可识别主体：' + str(path))
        entity_ids = []
        for name in names:
            entity_id = 'company_' + fingerprint(name)[:16]
            aliases[entity_id] = {'id': entity_id, 'name': name, 'aliases': [],
                                  'identity_status': 'REPOSITORY_LABEL_ONLY'}
            entity_ids.append(entity_id)
        event_id = str(fm['event_id'])
        content = re.search(r'^- 内容：(.*)$', body, re.M)
        excerpt = content.group(1).strip() if content else body.strip()[:1200]
        relative = 'ai-compute/04-事件/' + path.name
        source = 'https://github.com/zehaoli0324-cloud/groundsignal/blob/' + BASE_SHA + '/' + quote(relative, safe='/')
        data['events'].append({'id': event_id, 'title': path.stem,
                               'event_type': str(fm.get('event_type', 'UNCLASSIFIED_LEAD')),
                               'entity_ids': entity_ids, 'product': None,
                               'event_time': str(fm['event_date']) if fm.get('event_date') else None,
                               'created_at': now})
        data['evidence'].append(evidence_record(
            'repo_' + event_id, event_id, source, excerpt, now,
            evidence_type='capacity' if 'CAPACITY' in str(fm.get('event_type')) else 'disclosure',
            raw_fingerprint=fingerprint(raw), fingerprint_scope='repository_markdown',
            access_mode='repository_backfill', cited_source_url=fm.get('source_url') or None,
            lineage={'repository_commit': BASE_SHA, 'repository_path': relative,
                     'declared_fetched_at': str(fm.get('fetched_at') or ''),
                     'declared_verified_at': str(fm.get('last_verified_at') or ''),
                     'legacy_event_type': str(fm.get('event_type') or ''),
                     'original_article_retrieved': False,
                     'note': '原文是仓库事件笔记，不是原始商业凭证；历史置信度不继承为确认状态'}))
    data['entities'] = list(aliases.values())
    if len(data['events']) != len(pins['files']):
        raise ValueError('固定源版本的事件记录不完整')
    return validate(data)


def synthetic_scenario():
    """Entirely fictitious chronology for exercising the ledger, never a signal."""
    data = new_dataset('模拟供应关系：独立证据、确认与反证', 'synthetic', '2026-04-03T08:00:00Z')
    data['entities'] = [
        {'id': 'demo_supplier', 'name': '演示芯片厂（虚构）', 'aliases': []},
        {'id': 'demo_customer', 'name': '演示客户（虚构）', 'aliases': []}]
    data['events'] = [
        {'id': 'demo_supply_v1', 'title': '虚构案例：演示芯片厂向演示客户供货',
         'event_type': 'NEW_SUPPLIER', 'entity_ids': ['demo_supplier', 'demo_customer'],
         'product': '演示加速卡 V1（虚构）', 'event_time': None,
         'created_at': '2026-04-03T08:00:00Z'},
        {'id': 'demo_supply_v2', 'title': '虚构案例：V2 产品替代 V1',
         'event_type': 'SUPPLIER_REPLACED', 'entity_ids': ['demo_supplier', 'demo_customer'],
         'product': '演示加速卡 V2（虚构）', 'event_time': '2026-05-28',
         'created_at': '2026-05-28T08:00:00Z'}]
    specs = [
        ('qualification', 'demo_supply_v1', '2026-04-03T08:00:00Z',
         '虚构资格资料：演示加速卡 V1 已通过演示客户的资格审核。', 'T2', 'origin_qualification'),
        ('pilot', 'demo_supply_v1', '2026-04-10T08:00:00Z',
         '虚构交付记录：演示客户已收到演示加速卡 V1 的试产批次。', 'T2', 'origin_delivery'),
        ('reprint', 'demo_supply_v1', '2026-04-11T08:00:00Z',
         '虚构转载：根据资格资料，演示加速卡 V1 已通过演示客户的资格审核。', 'T3', 'origin_qualification'),
        ('confirmation', 'demo_supply_v1', '2026-05-21T08:00:00Z',
         '虚构客户公告：确认演示芯片厂为演示加速卡 V1 的供货方。', 'T1', 'origin_customer_confirmation'),
        ('counter', 'demo_supply_v1', '2026-05-25T08:00:00Z',
         '虚构反证：一份争议材料称演示加速卡 V1 的批次未被验收。', 'T2', 'origin_counter'),
        ('replacement', 'demo_supply_v2', '2026-05-28T08:00:00Z',
         '虚构客户公告：V2 正式替代 V1；V1 的旧供货主张不再作为当前版本。', 'T1', 'origin_v2_confirmation')]
    for name, event_id, at, text, tier, group in specs:
        evidence_id = 'demo_' + name
        data['evidence'].append(evidence_record(
            evidence_id, event_id, 'https://example.invalid/synthetic/' + name,
            text, at, evidence_type='qualification' if name == 'qualification' else 'delivery',
            source_tier=tier, published_at=at, access_mode='synthetic_fixture',
            fingerprint_scope='synthetic_document', original_source_checked=True,
            lineage={'synthetic': True, 'scenario': 'issue_1_state_machine',
                     'note': '全文、主体、来源和时间均为虚构测试材料'}))
        decision = 'CONFIRM' if tier == 'T1' else 'COUNTER' if name == 'counter' else 'SUPPORT'
        # Independent groups are only recognized when reviewed, not by URL count.
        data['reviews'].append({'id': 'review_' + name, 'evidence_id': evidence_id,
                                'at': at.replace('08:00:', '08:15:'), 'decision': decision,
                                'independence_group': group, 'supporting_quote': text,
                                'reviewer': 'synthetic_fixture', 'reason': '模拟审核，供回放测试'})
    data['reviews'].append({'id': 'review_counter_rejected', 'evidence_id': 'demo_counter',
                            'at': '2026-05-26T08:00:00Z', 'decision': 'REJECT',
                            'independence_group': 'origin_counter',
                            'reviewer': 'synthetic_fixture',
                            'reason': '模拟复核：争议材料与所讨论的 V1 批次不匹配'})
    data['event_updates'].append({'id': 'update_v1_superseded', 'event_id': 'demo_supply_v1',
                                 'at': '2026-05-29T08:00:00Z', 'action': 'SUPERSEDE',
                                 'replacement_event_id': 'demo_supply_v2',
                                 'reviewer': 'synthetic_fixture', 'reason': '模拟 V2 确认后替代 V1'})
    return validate(data)


def import_collection(path):
    """Consume collect.py's saved JSON; no fabricated extractor or verification."""
    raw = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(raw.get('query'), str) or not raw['query'].strip() or not raw.get('results'):
        raise ValueError('需要 collect.py 的 query/results 非空采集记录')
    now = utc_now()
    data = new_dataset(raw['query'] + '：采集线索导入', 'collector_import', now)
    entity_id = 'company_' + fingerprint(raw['query'])[:16]
    data['entities'] = [{'id': entity_id, 'name': raw['query'], 'aliases': [],
                         'identity_status': 'UNCONFIRMED'}]
    seen = set()
    for item in raw['results']:
        key = fingerprint(item['url'])[:20]
        if key in seen:
            continue
        seen.add(key)
        text = '\n'.join(str(item.get(k) or '') for k in ('title', 'snippet', 'excerpt')).strip()[:1600]
        event_id = 'lead_' + key
        data['events'].append({'id': event_id, 'title': str(item.get('title') or raw['query']),
                               'event_type': 'UNCLASSIFIED_LEAD', 'entity_ids': [entity_id],
                               'product': None, 'event_time': None, 'created_at': now})
        data['evidence'].append(evidence_record(
            'collected_' + key, event_id, item['url'], text, now, evidence_type='web_lead',
            access_mode='collector_snapshot', raw_fingerprint=fingerprint(item),
            fingerprint_scope='collector_result_json',
            lineage={'collection_file_sha256': fingerprint(Path(path).read_text(encoding='utf-8')),
                     'declared_retrieved_at': raw.get('retrieved_at'),
                     'page_fetch_status': item.get('status'),
                     'note': '导入时间不是原网页发布时间；搜索结果未做主体和商业事件核验'}))
    return validate(data)


def build_demo(out):
    manifest = ROOT / 'ai-compute/09-ground-evidence/manifest.json'
    if manifest.exists():
        backfill = load(manifest)
    else:
        backfill = migrate_repository(ROOT / 'ai-compute')
        write_manifest(manifest.parent, backfill)
    scenario = synthetic_scenario()
    out = Path(out)
    dump(ROOT / 'examples/ground-evidence/synthetic.json', scenario)
    render_report([backfill, scenario], out / 'demo.html', ROOT / 'templates/evidence-demo.html')
    repository_view = snapshot(backfill, max(e['processed_at'] for e in backfill['evidence']))
    export(out / 'repository', repository_view)
    export(out / 'synthetic-confirmed', snapshot(scenario, '2026-05-21T08:15:00Z'))
    print(json.dumps({'html': str(out / 'demo.html'), 'repository_events': len(backfill['events']),
                      'real_verified_events': repository_view['metrics']['states'].get('VERIFIED', 0),
                      'synthetic': True}, ensure_ascii=False))


def main(argv=None):
    parser = argparse.ArgumentParser(description='Issue #1 证据、事件与按时间回放 Demo')
    sub = parser.add_subparsers(dest='command')
    demo = sub.add_parser('demo', help='生成可直接打开的离线演示')
    demo.add_argument('--out', type=Path, default=ROOT / 'samples/ground-evidence')
    migrate = sub.add_parser('migrate', help='在新的目录迁移现有事件，观察时间取本次运行时间')
    migrate.add_argument('--vault', type=Path, default=ROOT / 'ai-compute')
    migrate.add_argument('--out', type=Path, required=True)
    collected = sub.add_parser('import-collection', help='导入 collect.py 的 JSON 记录为未审核线索')
    collected.add_argument('file', type=Path)
    collected.add_argument('--out', type=Path, required=True)
    snap = sub.add_parser('snapshot', help='只导出截止时刻已经可用的证据和审核结果')
    snap.add_argument('--input', type=Path, required=True)
    snap.add_argument('--as-of', required=True)
    snap.add_argument('--out', type=Path, required=True)
    review = sub.add_parser('review', help='追加当前时间的人工审核，不支持回填审核时间')
    review.add_argument('--input', type=Path, required=True)
    review.add_argument('--evidence', required=True)
    review.add_argument('--decision', required=True, choices=['SUPPORT', 'CONFIRM', 'COUNTER', 'REJECT'])
    review.add_argument('--quote', default='')
    review.add_argument('--group')
    review.add_argument('--reason', required=True)
    review.add_argument('--reviewer', required=True)
    review.add_argument('--out', type=Path, required=True)
    report = sub.add_parser('report', help='为导入或审核后的 ledger 生成同一回放界面')
    report.add_argument('--input', type=Path, required=True)
    report.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command in {None, 'demo'}:
            build_demo(args.out if args.command else ROOT / 'samples/ground-evidence')
        elif args.command in {'migrate', 'import-collection'}:
            if (args.out / 'manifest.json').exists():
                raise ValueError('目标已有 manifest；请用新的目录保留已有 lineage')
            data = migrate_repository(args.vault) if args.command == 'migrate' else import_collection(args.file)
            print(write_manifest(args.out, data))
        elif args.command == 'snapshot':
            export(args.out, snapshot(load(args.input), args.as_of))
            print(args.out / 'snapshot.json')
        elif args.command == 'review':
            data = deepcopy(load(args.input))
            now = utc_now()
            new_review = {'evidence_id': args.evidence, 'at': now, 'decision': args.decision,
                          'supporting_quote': args.quote, 'independence_group': args.group,
                          'reason': args.reason, 'reviewer': args.reviewer}
            new_review['id'] = 'review_' + fingerprint(new_review)[:24]
            if any(r['id'] == new_review['id'] for r in data['reviews']):
                raise ValueError('相同审核已存在')
            data['reviews'].append(new_review)
            validate(data)
            dump(args.out, data)
            print(args.out)
        elif args.command == 'report':
            print(render_report([load(args.input)], args.out, ROOT / 'templates/evidence-demo.html'))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print('Demo 失败：' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
