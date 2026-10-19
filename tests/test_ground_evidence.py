from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from evidence_demo import import_collection, migrate_repository, synthetic_scenario
from ground_evidence import (csv_feed, export, load, render_report, snapshot,
                             validate, write_manifest)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data = synthetic_scenario()

    def state(self, at, data=None):
        return snapshot(data or self.data, at)['events'][0]

    def test_before_first_seen_contains_no_future_entities_or_event(self):
        result = snapshot(self.data, '2026-04-03T07:59:59Z')
        self.assertEqual(result['events'], [])
        self.assertEqual(result['entities'], [])
        self.assertNotIn('demo_supplier', json.dumps(result))

    def test_replay_waits_for_processing_and_review(self):
        self.data['evidence'][0]['processed_at'] = '2026-04-03T08:10:00Z'
        self.assertEqual(snapshot(self.data, '2026-04-03T08:09:59Z')['events'], [])
        self.assertEqual(self.state('2026-04-03T08:10:00Z')['status'], 'EARLY_SIGNAL')
        self.assertEqual(self.state('2026-04-03T08:15:00Z')['status'], 'WATCH')

    def test_two_independent_supports_promote_and_reprint_does_not(self):
        before = self.state('2026-04-10T08:15:00Z')
        after = self.state('2026-04-11T08:15:00Z')
        self.assertEqual(before['status'], 'SUPPORTED')
        self.assertEqual(before['evidence_count'], 2)
        self.assertEqual(after['evidence_count'], 3)
        self.assertEqual(after['independent_sources'], 2)

    def test_same_payload_cannot_masquerade_as_two_origins(self):
        self.data['evidence'][1]['raw_fingerprint'] = self.data['evidence'][0]['raw_fingerprint']
        result = self.state('2026-04-10T08:15:00Z')
        self.assertEqual(result['independent_sources'], 1)
        self.assertEqual(result['status'], 'WATCH')

    def test_unknown_origins_do_not_count_as_independent(self):
        for review in self.data['reviews']:
            review['independence_group'] = None
        result = self.state('2026-04-11T08:15:00Z')
        self.assertEqual(result['independent_sources'], 0)
        self.assertEqual(result['status'], 'WATCH')

    def test_source_tier_alone_never_verifies(self):
        self.data['evidence'][0]['source_tier'] = 'T1'
        self.assertEqual(self.state('2026-04-03T08:00:00Z')['status'], 'EARLY_SIGNAL')

    def test_confirmation_and_lead_time_are_not_backdated(self):
        early = self.state('2026-04-11T08:15:00Z')
        self.assertIsNone(early['public_confirmation_at'])
        self.assertIsNone(early['lead_time_days'])
        self.assertNotIn('demo_confirmation', json.dumps(early))
        confirmed = self.state('2026-05-21T08:15:00Z')
        self.assertEqual(confirmed['status'], 'VERIFIED')
        self.assertAlmostEqual(confirmed['lead_time_days'], 40.9896)

    def test_future_rejection_does_not_rewrite_prior_counter_evidence(self):
        disputed = self.state('2026-05-25T08:15:00Z')
        corrected = self.state('2026-05-26T08:00:00Z')
        self.assertEqual(disputed['status'], 'DISPUTED')
        self.assertIsNone(disputed['lead_time_days'])
        self.assertEqual(next(e for e in disputed['evidence'] if e['id'] == 'demo_counter')['review']['decision'], 'COUNTER')
        self.assertEqual(corrected['status'], 'VERIFIED')

    def test_supersession_is_visible_only_after_update(self):
        self.assertEqual(self.state('2026-05-28T08:15:00Z')['status'], 'VERIFIED')
        result = self.state('2026-05-29T08:00:00Z')
        self.assertEqual(result['status'], 'SUPERSEDED')
        self.assertEqual(result['superseded_by'], 'demo_supply_v2')

    def test_stale_requires_review_but_does_not_assert_relationship_ended(self):
        result = snapshot(self.data, '2026-08-01T00:00:00Z')['events'][1]
        self.assertEqual(result['status'], 'STALE')
        self.assertIsNone(result['lead_time_days'])

    def test_rejected_evidence_cannot_support_event(self):
        data = deepcopy(self.data)
        for review in data['reviews']:
            review['decision'] = 'REJECT'
        data['event_updates'] = []
        result = self.state('2026-04-11T08:15:00Z', data)
        self.assertEqual(result['status'], 'REJECTED')
        self.assertEqual(result['independent_sources'], 0)

    def test_invalid_timestamps_and_missing_timezone_fail_closed(self):
        for field, bad in [('published_at', '2027-01-01T00:00:00Z'),
                           ('first_seen_at', '2026-04-03T08:00:00'),
                           ('processed_at', '2026-04-03T07:00:00Z')]:
            data = deepcopy(self.data)
            data['evidence'][0][field] = bad
            with self.assertRaises(ValueError):
                validate(data)

    def test_review_cannot_precede_processing(self):
        self.data['reviews'][0]['at'] = '2026-04-03T07:00:00Z'
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_review_quote_and_primary_source_are_required(self):
        for mutate in ['quote', 'tier', 'source_check']:
            data = deepcopy(self.data)
            if mutate == 'quote':
                data['reviews'][3]['supporting_quote'] = '原文没有这句话'
            elif mutate == 'tier':
                data['evidence'][3]['source_tier'] = 'T3'
            else:
                data['evidence'][3]['original_source_checked'] = False
            with self.assertRaises(ValueError):
                validate(data)

    def test_duplicates_and_unknown_entity_references_are_rejected(self):
        for mutate in ['duplicate', 'entity']:
            data = deepcopy(self.data)
            if mutate == 'duplicate':
                data['evidence'].append(deepcopy(data['evidence'][0]))
            else:
                data['events'][0]['entity_ids'] = ['unknown_entity']
            with self.assertRaises(ValueError):
                validate(data)

    def test_legal_review_is_not_invented(self):
        data = deepcopy(self.data)
        data['evidence'][0]['legal_basis']['redistribution_status'] = 'ALLOWED'
        with self.assertRaises(ValueError):
            validate(data)

    def test_export_excludes_future_evidence_and_reviews(self):
        view = snapshot(self.data, '2026-04-11T08:15:00Z')
        with tempfile.TemporaryDirectory() as temp:
            export(temp, view)
            for filename in ('snapshot.json', 'events.jsonl', 'events.csv'):
                text = (Path(temp) / filename).read_text(encoding='utf-8-sig')
                self.assertNotIn('demo_confirmation', text)
                self.assertNotIn('demo_counter', text)
                self.assertNotIn('2026-05-21', text)

    def test_csv_formula_prefix_is_escaped(self):
        view = snapshot(self.data, '2026-04-11T08:15:00Z')
        view['events'][0]['title'] = '=SUM(1,2)'
        self.assertIn("'=SUM", csv_feed(view))

    def test_manifest_roundtrip_and_path_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_manifest(temp, self.data)
            self.assertEqual(load(path), self.data)
            manifest = json.loads(path.read_text())
            manifest['evidence_files'] = ['../escape.json']
            path.write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                load(path)

    def test_report_keeps_external_text_out_of_script_markup(self):
        self.data['events'][0]['title'] = '</script><script>alert(1)</script>'
        with tempfile.TemporaryDirectory() as temp:
            path = render_report([self.data], Path(temp) / 'demo.html',
                                 Path(__file__).resolve().parents[1] / 'templates/evidence-demo.html')
            text = path.read_text()
            self.assertNotIn('</script><script>alert(1)', text)
            self.assertIn('\\u003c/script', text)

    def test_existing_repository_backfill_preserves_unknowns(self):
        data = migrate_repository(Path(__file__).resolve().parents[1] / 'ai-compute',
                                  observed_at='2026-10-13T12:00:00Z')
        self.assertEqual(len(data['events']), 8)
        self.assertEqual(snapshot(data, '2026-08-26T00:00:00Z')['events'], [])
        view = snapshot(data, '2026-10-13T12:00:00Z')
        self.assertEqual(view['metrics']['states'], {'EARLY_SIGNAL': 8})
        self.assertTrue(all(e['lead_time_days'] is None for e in view['events']))
        self.assertTrue(all(e['published_at'] is None for e in data['evidence']))
        self.assertTrue(any(e['event_time'] == '2025' for e in data['events']))

    def test_collector_handoff_creates_unreviewed_traceable_leads(self):
        raw = {'query': '测试公司', 'retrieved_at': '2020-01-01T00:00:00Z',
               'results': [{'title': '测试公司公告', 'url': 'https://example.com/a',
                            'snippet': '一条线索', 'excerpt': '需要进一步核实', 'status': 'page_fetched'}]}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'collection.json'
            path.write_text(json.dumps(raw))
            data = import_collection(path)
            item = data['evidence'][0]
            self.assertNotEqual(item['first_seen_at'], raw['retrieved_at'])
            self.assertEqual(item['lineage']['declared_retrieved_at'], raw['retrieved_at'])
            self.assertIsNone(item['published_at'])
            self.assertFalse(item['original_source_checked'])
            view = snapshot(data, data['created_at'])
            self.assertEqual(view['events'][0]['status'], 'EARLY_SIGNAL')

    def test_synthetic_data_cannot_be_relabelled_as_real(self):
        self.data['mode'] = 'collector_import'
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_structural_schema_is_bound_to_runtime_validation(self):
        del self.data['evidence'][0]['legal_basis']['robots_reviewed']
        with self.assertRaisesRegex(ValueError, '字段契约'):
            validate(self.data)

    def test_supersession_cannot_use_not_yet_confirmed_replacement(self):
        self.data['event_updates'][0]['at'] = '2026-05-28T08:00:00Z'
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_ambiguous_simultaneous_reviews_are_rejected(self):
        review = deepcopy(self.data['reviews'][0])
        review['id'] = 'conflicting_review'
        review['decision'] = 'REJECT'
        self.data['reviews'].append(review)
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_invalid_month_is_not_invented_into_a_timestamp(self):
        self.data['events'][0]['event_time'] = '2026-13'
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_changed_source_note_cannot_reuse_pinned_repository_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / '04-事件'
            folder.mkdir()
            (folder / 'new.md').write_text('---\nevent_id: altered\n---\nchanged')
            with self.assertRaises(ValueError):
                migrate_repository(temp)


if __name__ == '__main__':
    unittest.main()
