"""Contract and integration checks: no live services or model quality claims."""
from copy import deepcopy
import io
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from industry_search.contracts import REPO, canonical_url, config_check, digest, mentions, read_json, target_check
from industry_search.documents import FetchError, Fetcher, parse_html, parse_pdf, public_url, source_hint
from industry_search.evaluation import compare, score
from industry_search.models import ModelClient, ground_claims, select_text
from industry_search.pipeline import execute, frozen_hash, load_registry, load_run, merge_hits, replay, validate_run
from industry_search.planning import plan
from industry_search.providers import SearchClient
from ground_evidence import load as load_ledger, snapshot, instant


def configuration():
    config = read_json(REPO / 'config/search.default.json')
    config['budget']['request_interval_seconds'] = 0
    return config


def fixture():
    return read_json(REPO / 'examples/search/synthetic.json')


def document():
    f = fixture()
    url = 'https://source.example.invalid/sample'
    return {'id': 'doc_' + digest(url)[:20], 'url': url, 'text': f['documents'][url]['text'],
            'pages': [], 'status': 'FETCHED'}


def response(payload=None, status=200, headers=None):
    result = Mock(status_code=status, headers=headers or {}, encoding='utf-8')
    result.json.return_value = payload
    if status >= 400:
        result.raise_for_status.side_effect = requests.HTTPError('sensitive server body')
    return result


class ContractTests(unittest.TestCase):
    def test_every_dimension_before_followups(self):
        config = configuration()
        config['budget']['max_queries'] = 9
        result = plan(fixture()['target'], config['budget'])
        self.assertEqual({q['dimension'] for q in result['queries']}, set(fixture()['target']['dimensions']))
        self.assertFalse(result['unplanned_dimensions'])

    def test_query_budget_exposes_missing_dimensions(self):
        config = configuration()
        config['budget']['max_queries'] = 2
        result = plan(fixture()['target'], config['budget'])
        self.assertEqual(len(result['queries']), 2)
        self.assertEqual(len(result['unplanned_dimensions']), 7)

    def test_target_dates_and_unknown_fields_rejected(self):
        target = fixture()['target']
        target['time_range'] = {'after': '2026-02-30', 'before': None}
        with self.assertRaises(ValueError):
            target_check(target)
        target = fixture()['target']
        target['verified'] = True
        with self.assertRaises(ValueError):
            target_check(target)

    def test_query_keeps_name_and_time_constraints(self):
        target = fixture()['target']
        target['time_range'] = {'after': '2025-01-01', 'before': '2026-10-19'}
        tasks = plan(target, configuration()['budget'])['queries']
        self.assertTrue(all('after:2025-01-01' in x['query'] and 'before:2026-10-19' in x['query'] for x in tasks))

    def test_url_tracking_removed_but_document_identity_preserved(self):
        a = canonical_url('https://EXAMPLE.com/article?id=17&utm_source=x#part')
        self.assertEqual(a, 'https://example.com/article?id=17')
        self.assertNotEqual(a, canonical_url('https://example.com/article?id=18'))

    def test_private_and_credential_urls_rejected(self):
        for url in ('http://127.0.0.1/', 'http://169.254.169.254/', 'https://user:secret@example.com/',
                    'file:///etc/passwd', 'http://localhost/', 'https://example.com:8080/'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                canonical_url(url)

    def test_source_hint_exact_hostname_and_not_claim_verification(self):
        target = fixture()['target']
        hint = source_hint('https://cninfo.com.cn.evil.example/a', target, load_registry())
        self.assertEqual(hint['tier_hint'], 'UNKNOWN')
        self.assertNotIn('status', source_hint('https://www.cninfo.com.cn/a', target, load_registry()))

    def test_short_english_alias_not_substring_match(self):
        target = deepcopy(fixture()['target'])
        target.update(name='AMD', aliases=[])
        self.assertFalse(mentions('AMDGamingNotTheCompany', target))
        self.assertTrue(mentions('AMD supplied a component', target))

    def test_model_config_cannot_override_tools_budget_or_auth(self):
        config = configuration()
        config['models']['small']['enabled'] = True
        config['models']['small']['extra_body'] = {'tools': [{'type': 'browser'}]}
        with self.assertRaises(ValueError):
            config_check(config)


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cache = Path(self.temp.name)
        self.config = configuration()
        self.task = {'id': 'q1', 'query': '"测试公司" 供应商'}

    def tearDown(self):
        self.temp.cleanup()

    def test_missing_key_is_not_empty_success(self):
        session = Mock()
        with patch.dict('os.environ', {}, clear=True):
            client = SearchClient(self.cache, self.config['budget'], session)
            result = client.query('deepseek', self.task, 4)
        self.assertEqual(result['status'], 'NOT_CONFIGURED')
        self.assertEqual(client.calls, 0)
        session.post.assert_not_called()

    def test_search_adapters_preserve_query_and_ignore_ai_summary_as_evidence(self):
        for provider, payload in (
            ('brave', {'web': {'results': [{'url': 'https://example.com/a', 'title': 'title', 'description': 'lead'}]}}),
            ('tavily', {'results': [{'url': 'https://example.com/a', 'title': 'title', 'content': 'lead'}]}),
            ('firecrawl', {'success': True, 'data': {'web': [{'url': 'https://example.com/a', 'title': 'title', 'description': 'lead'}]}}),
            ('deepseek', {'results': [{'url': 'https://example.com/a', 'title': 'title', 'summary': 'generated summary', 'content': 'not an original snapshot'}]}),
        ):
            with self.subTest(provider=provider), tempfile.TemporaryDirectory() as folder:
                session = Mock()
                session.get.return_value = session.post.return_value = response(payload)
                with patch.dict('os.environ', {'BRAVE_SEARCH_API_KEY': 'test-key', 'TAVILY_API_KEY': 'test-key',
                                             'FIRECRAWL_API_KEY': 'test-key', 'DEEPSEEK_API_KEY': 'test-key'}):
                    result = SearchClient(Path(folder), self.config['budget'], session).query(provider, self.task, 4)
                self.assertEqual(result['status'], 'OK')
                self.assertNotIn('text', result['hits'][0])
                self.assertNotIn('test-key', json.dumps(result))
                call = session.get.call_args if provider == 'brave' else session.post.call_args
                self.assertEqual(call.kwargs['params']['q'] if provider == 'brave' else call.kwargs['json']['query'], self.task['query'])
                if provider == 'deepseek':
                    self.assertFalse(call.kwargs['json']['need_content'])

    def test_429_cooldown_survives_new_client(self):
        session = Mock()
        session.post.return_value = response(status=429, headers={'Retry-After': '3600'})
        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test-key'}):
            first = SearchClient(self.cache, self.config['budget'], session).query('tavily', self.task, 4)
            second = SearchClient(self.cache, self.config['budget'], session).query('tavily', self.task, 4)
        self.assertEqual(first['status'], 'UNAVAILABLE')
        self.assertEqual(second['status'], 'COOLDOWN')
        self.assertEqual(session.post.call_count, 1)

    def test_cache_retains_original_search_time(self):
        session = Mock()
        session.post.return_value = response({'results': []})
        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test-key'}):
            one = SearchClient(self.cache, self.config['budget'], session).query('tavily', self.task, 4)
            two = SearchClient(self.cache, self.config['budget'], session).query('tavily', self.task, 4)
        self.assertEqual(one['status'], 'NO_RESULTS')
        self.assertTrue(two['cached'])
        self.assertEqual(one['searched_at'], two['searched_at'])
        self.assertEqual(session.post.call_count, 1)

    def test_broken_provider_shape_is_failure(self):
        session = Mock()
        session.get.return_value = response({'web': None})
        with patch.dict('os.environ', {'BRAVE_SEARCH_API_KEY': 'test-key'}):
            result = SearchClient(self.cache, self.config['budget'], session).query('brave', self.task, 4)
        self.assertEqual(result['status'], 'FAILED')

    def test_search_budget_stops_requests(self):
        self.config['budget']['max_search_calls'] = 0
        session = Mock()
        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test-key'}):
            result = SearchClient(self.cache, self.config['budget'], session).query('tavily', self.task, 4)
        self.assertEqual(result['status'], 'BUDGET_EXHAUSTED')
        session.post.assert_not_called()


class DocumentTests(unittest.TestCase):
    def test_challenge_is_not_body(self):
        with self.assertRaises(FetchError):
            parse_html(b'<html><title>Just a moment</title><p>verify you are human</p></html>')

    def test_html_removes_navigation_keeps_body_and_date_hint(self):
        title, text, published = parse_html('''<html><head><title>Report</title><meta property="article:published_time" content="2026-10-01"></head><body><nav>noise</nav><article>Company supplied a chip.</article></body></html>''')
        self.assertEqual(text, 'Company supplied a chip.')
        self.assertEqual(published, '2026-10-01')

    def test_dns_private_destination_stops_request(self):
        with patch('industry_search.documents.socket.getaddrinfo', return_value=[(2, 1, 6, '', ('10.1.2.3', 0))]):
            with self.assertRaises(FetchError):
                public_url('https://public-looking.example/a')

    def test_redirect_is_checked_before_second_request(self):
        session = Mock()
        session.get.return_value = response(status=302, headers={'Location': 'http://127.0.0.1/private'})
        config = configuration()
        with tempfile.TemporaryDirectory() as folder:
            fetcher = Fetcher(config['budget'], folder, session=session)
            with patch('industry_search.documents.public_url', side_effect=['https://example.com/a', ValueError('private_url')]), patch.object(fetcher, '_allowed', return_value=True):
                with self.assertRaises(ValueError):
                    fetcher._http('https://example.com/a')
        self.assertEqual(session.get.call_count, 1)

    def test_fetch_failure_cannot_use_search_snippet(self):
        with tempfile.TemporaryDirectory() as folder:
            fetcher = Fetcher(configuration()['budget'], folder)
            with patch.object(fetcher, '_http', side_effect=FetchError('http_403')):
                doc = fetcher.fetch({'url': 'https://example.com/a', 'title': 'Company',
                                     'first_seen_at': '2026-10-01T00:00:00Z', 'snippet': 'A supplies B'}, fixture()['target'])
        self.assertEqual(doc['status'], 'FAILED')
        self.assertEqual(doc['text'], '')

    @unittest.skipUnless(importlib.util.find_spec('pypdf'), 'Optional PDF dependency is in requirements-search.txt')
    def test_pdf_text_retains_page_locations(self):
        from pypdf import PdfWriter
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.add_blank_page(width=100, height=100)
        stream = io.BytesIO()
        writer.write(stream)
        text, pages, parser = parse_pdf(stream.getvalue(), 'pypdf')
        self.assertEqual([p['page'] for p in pages], [1, 2])
        self.assertEqual(parser, 'pypdf_text_no_ocr')


class ModelTests(unittest.TestCase):
    def test_fabricated_quote_quarantined(self):
        f, doc = fixture(), document()
        claim = f['model_outputs'][doc['url']]['large']['claims'][0]
        claim['quote'] = '星港芯片（虚构）已完成所有商业化目标，未来客户规模将持续扩大。'
        accepted, bad = ground_claims({'claims': [claim]}, doc, f['target'], doc['text'])
        self.assertFalse(accepted)
        self.assertIn('quote_not_in_model_input_and_source', bad[0]['reasons'])

    def test_mass_production_upgrade_rejected_and_escalated(self):
        f, doc = fixture(), document()
        client = ModelClient(configuration(), fixture=f['model_outputs'])
        extraction = client.extract(doc, f['target'])
        self.assertTrue(extraction['rejected'])
        self.assertEqual(extraction['candidates'][0]['stage'], 'TESTING')
        self.assertIn('grounding_or_field_failure', extraction['escalation_reasons'])

    def test_output_cannot_approve_itself(self):
        f, doc = fixture(), document()
        payload = deepcopy(f['model_outputs'][doc['url']]['large'])
        payload['claims'][0]['review_status'] = 'VERIFIED'
        with self.assertRaises(ValueError):
            ground_claims(payload, doc, f['target'], doc['text'])

    def test_disabled_roles_do_not_make_requests(self):
        session = Mock()
        result = ModelClient(configuration(), session=session).extract(document(), fixture()['target'])
        self.assertTrue(all(a['status'] == 'MODEL_NOT_RUN' for a in result['attempts']))
        session.post.assert_not_called()

    def test_mock_api_json_and_returned_identity_recorded(self):
        config, f, doc = configuration(), fixture(), document()
        config['routing_mode'] = 'small_only'
        config['models']['small']['enabled'] = True
        payload = f['model_outputs'][doc['url']]['large']
        session = Mock()
        session.post.return_value = response({'model': 'served-model-revision', 'usage': {'prompt_tokens': 123, 'completion_tokens': 44},
            'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(payload, ensure_ascii=False)}}]})
        client = ModelClient(config, session=session)
        output = client.extract(doc, f['target'])
        self.assertEqual(output['attempts'][0]['response_model'], 'served-model-revision')
        self.assertEqual(client.calls, 1)
        self.assertEqual(output['candidates'][0]['review_status'], 'PENDING')
        self.assertNotIn('tools', session.post.call_args.kwargs['json'])

    def test_truncated_output_is_not_accepted(self):
        config, doc = configuration(), document()
        config['routing_mode'] = 'small_only'
        config['models']['small']['enabled'] = True
        session = Mock()
        session.post.return_value = response({'choices': [{'finish_reason': 'length', 'message': {'content': '{"claims": []}'}}]})
        output = ModelClient(config, session=session).extract(doc, fixture()['target'])
        self.assertEqual(output['attempts'][0]['status'], 'INVALID_OUTPUT')

    def test_budget_prevents_real_large_call(self):
        config = configuration()
        config['models']['large']['enabled'] = True
        config['budget']['max_large_calls'] = 0
        session = Mock()
        with patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test-key'}):
            output = ModelClient(config, session=session).extract(document(), fixture()['target'])
        self.assertEqual(output['attempts'][-1]['status'], 'BUDGET_EXHAUSTED')
        session.post.assert_not_called()

    def test_disagreement_preserved_for_human_review(self):
        f, doc = fixture(), document()
        f['model_outputs'][doc['url']]['small']['claims'][0]['stage'] = 'TESTING'
        f['model_outputs'][doc['url']]['small']['claims'][0]['polarity'] = 'UNCERTAIN'
        output = ModelClient(configuration(), fixture=f['model_outputs']).extract(doc, f['target'])
        self.assertEqual(len(output['candidates']), 2)
        self.assertTrue(all('model_disagreement' in c['flags'] for c in output['candidates']))

    def test_long_text_selection_still_uses_original_characters(self):
        target = fixture()['target']
        text = '无关材料。' * 500 + '星港芯片（虚构）与另一公司开展测试。' + '结束。' * 200
        selected = select_text(text, target, 2500)
        self.assertIn('星港芯片（虚构）与另一公司开展测试。', selected)
        self.assertLessEqual(len(selected), 2500)


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.f = fixture()
        self.config = configuration()

    def tearDown(self):
        self.temp.cleanup()

    def capture(self):
        return execute(self.f['target'], self.config, self.root / 'capture', fixture=self.f)

    def test_complete_synthetic_handoff_has_no_verified_facts(self):
        with patch('requests.Session.request', side_effect=AssertionError('offline fixture made a network call')):
            run = self.capture()
        self.assertEqual(run['status'], 'SYNTHETIC_ONLY')
        self.assertEqual(run['counts']['model_calls'], 0)
        self.assertTrue(run['candidates'])
        ledger = load_ledger(self.root / 'capture' / run['handoff'])
        self.assertFalse(ledger['reviews'])
        self.assertTrue(all(e['source_tier'] == 'UNKNOWN' for e in ledger['evidence']))
        view = snapshot(ledger, '2099-01-01T00:00:00Z')
        self.assertTrue(all(e['status'] == 'EARLY_SIGNAL' for e in view['events']))
        self.assertTrue(all(e['event_type'] == 'UNCLASSIFIED_LEAD' for e in view['events']))

    def test_same_content_is_flagged_not_counted_as_independent_confirmation(self):
        run = self.capture()
        self.assertEqual(sum(bool(d['duplicate_content_of']) for d in run['documents']), 1)
        ledger = load_ledger(self.root / 'capture' / run['handoff'])
        self.assertTrue(all(e['source_independence_group'] is None for e in ledger['evidence']))

    def test_nonempty_output_is_not_overwritten(self):
        self.capture()
        before = (self.root / 'capture/run.json').read_bytes()
        with self.assertRaises(ValueError):
            self.capture()
        self.assertEqual((self.root / 'capture/run.json').read_bytes(), before)

    def test_frozen_replay_retains_acquisition_times(self):
        original = self.capture()
        result = replay(self.root / 'capture/run.json', self.config, self.root / 'replay', fixture=self.f)
        self.assertEqual(result['frozen_input_sha256'], original['frozen_input_sha256'])
        self.assertEqual([d['first_seen_at'] for d in result['documents']], [d['first_seen_at'] for d in original['documents']])
        self.assertEqual(result['counts']['fetch_calls'], 0)

    def test_altered_source_cannot_replay_under_old_manifest(self):
        run = self.capture()
        run['documents'][0]['text'] += '篡改'
        with self.assertRaises(ValueError):
            validate_run(run)

    def test_raw_snapshot_tampering_rejected(self):
        self.capture()
        path = self.root / 'capture/run.json'
        run = read_json(path)
        run['documents'][0]['raw_path'] = 'tampered.bin'
        (path.parent / 'tampered.bin').write_bytes(b'not the saved source')
        path.write_text(json.dumps(run, ensure_ascii=False))
        with self.assertRaises(ValueError):
            load_run(path)

    def test_offset_or_synthetic_tampering_rejected(self):
        run = self.capture()
        run['candidates'][0]['quote_start'] += 1
        with self.assertRaises(ValueError):
            validate_run(run)
        run = read_json(self.root / 'capture/run.json')
        run['synthetic'] = False
        with self.assertRaises(ValueError):
            validate_run(run)

    def test_frozen_comparison_has_no_real_model_winner(self):
        self.capture()
        result = compare(self.root / 'capture/run.json', self.config, self.root / 'compare',
                         labels=read_json(REPO / 'examples/search/synthetic-gold.json'), fixture=self.f)
        self.assertEqual(result['selection_status'], 'NO_AUTOMATIC_WINNER')
        self.assertTrue(all(r['quality_status'] == 'SYNTHETIC_ONLY' for r in result['results']))
        self.assertEqual(len({r['frozen_input_sha256'] for r in result['results']}), 1)

    def test_unlabeled_runs_have_no_accuracy(self):
        run = self.capture()
        result = score(run, None)
        self.assertEqual(result['quality_status'], 'UNASSESSED')
        self.assertIsNone(result['precision'])

    def test_wrong_gold_fingerprint_rejected(self):
        run = self.capture()
        gold = read_json(REPO / 'examples/search/synthetic-gold.json')
        gold['documents'][0]['text_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            score(run, gold)

    def test_live_missing_configuration_does_not_simulate_success(self):
        target = read_json(REPO / 'examples/search/target-nvidia.json')
        with patch.dict('os.environ', {}, clear=True), patch('requests.Session.request', side_effect=AssertionError('missing key still called network')):
            run = execute(target, self.config, self.root / 'unconfigured')
        self.assertEqual(run['status'], 'NO_USABLE_DOCUMENTS')
        self.assertFalse(run['candidates'])
        self.assertTrue(all(r['status'] == 'NOT_CONFIGURED' for r in run['search_records']))
        self.assertIsNone(score(run, None)['precision'])

    def test_mock_captured_page_without_model_stays_unreviewed(self):
        self.config['providers'] = []
        target = read_json(REPO / 'examples/search/target-nvidia.json')
        target['seed_urls'] = ['https://example.com/original']
        text = 'NVIDIA supplied a component to DemoCustomer. ' * 4
        def fetch(hit, target):
            from industry_search.contracts import now
            return dict(id='doc_' + digest(hit['url'])[:20], url=hit['url'], resolved_url=hit['url'], title='NVIDIA original', text=text, pages=[],
                        status='FETCHED', first_seen_at=hit['first_seen_at'], retrieved_at=now(), raw_sha256=digest(text), text_sha256=digest(text),
                        raw_path=None, parser='test_transport', published_hint=None, error_code=None, synthetic=False, fetcher='http')
        with patch('industry_search.documents.Fetcher.fetch', side_effect=fetch):
            run = execute(target, self.config, self.root / 'model-disabled')
        self.assertEqual(run['status'], 'COLLECTED_MODEL_NOT_COMPLETED')
        self.assertFalse(run['candidates'])
        self.assertEqual(score(run, None)['quality_status'], 'MODEL_NOT_RUN')


if __name__ == '__main__':
    unittest.main()
