"""Collection metrics must expose omissions, duplicate evidence and missing judgment."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from industry_search.benchmark import (benchmark_check, draft_benchmark, evaluate, governance_metrics,
                                      human_metrics, retrieval, review_template, wilson)
from industry_search.contracts import REPO, digest, read_json, write_json
from industry_search.pipeline import execute, frozen_hash


class CollectionBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.fixture = read_json(REPO / 'examples/search/synthetic.json')
        self.config = read_json(REPO / 'config/search.default.json')
        self.benchmark = read_json(REPO / 'examples/search/eval-benchmark.synthetic.json')
        self.bench_path = self.root / 'benchmark.json'
        self.policy_path = REPO / 'config/research-eval.default.json'
        self.run = execute(self.fixture['target'], self.config, self.root / 'run', fixture=self.fixture)
        self.run_path = self.root / 'run/run.json'
        write_json(self.bench_path, self.benchmark)

    def tearDown(self):
        self.temp.cleanup()

    def score(self, reviews=None, allow_draft=False):
        write_json(self.bench_path, self.benchmark)
        review_path = None
        if reviews is not None:
            review_path = self.root / 'reviews.json'
            write_json(review_path, reviews)
        return evaluate(self.run_path, self.bench_path, self.policy_path, review_path, allow_draft)

    def test_duplicate_reprint_and_missing_source_have_honest_denominators(self):
        result = self.score()
        self.assertEqual(result['retrieval']['reference_recall_at_k'], .75)
        self.assertEqual(result['acquisition']['fetched_documents'], 4)
        self.assertEqual(result['acquisition']['reference_capture_recall'], .75)
        self.assertEqual(result['extraction']['raw_labeled_candidates'], 4)
        self.assertEqual(result['extraction']['scored_unique_predictions'], 3)
        self.assertEqual(result['extraction']['precision'], 1)
        self.assertEqual(result['extraction']['recall_on_fetched'], 1)
        self.assertEqual(result['extraction']['end_to_end_reference_recall'], .75)
        self.assertEqual(result['acquisition']['missing_required_reference_groups'], ['missing_capacity'])
        self.assertEqual(result['quality_status'], 'SYNTHETIC_ONLY')
        self.assertEqual(result['decision'], 'NOT_READY')
        self.assertIsNone(result['overall_score'])
        self.assertIsNone(result['operations']['input_tokens'])
        self.assertFalse(result['operations']['token_usage_complete'])
        self.assertEqual(next(g['status'] for g in result['gates'] if g['name'] == 'retrieval_recall:capacity'), 'FAILED')

    def test_evaluation_is_offline(self):
        with patch('requests.Session') as session:
            self.score()
        session.assert_not_called()

    def test_changed_source_version_cannot_reuse_labels(self):
        self.benchmark['documents'][0]['text_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'fingerprint_mismatch'):
            self.score()

    def test_real_and_synthetic_benchmarks_cannot_mix(self):
        self.benchmark['synthetic'] = False
        with self.assertRaisesRegex(ValueError, 'scope_or_synthetic_mismatch'):
            self.score()

    def test_fixture_cannot_be_promoted_by_changing_run_and_source_flags(self):
        self.run['synthetic'] = False
        for doc in self.run['documents']:
            doc['synthetic'] = False
        self.run['frozen_input_sha256'] = frozen_hash(self.run['documents'])
        write_json(self.run_path, self.run)
        self.benchmark['synthetic'] = False
        with self.assertRaisesRegex(ValueError, 'mixed_synthetic_model_attempt'):
            self.score()

    def test_same_id_but_changed_target_scope_is_rejected(self):
        self.benchmark['target_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'scope_or_synthetic_mismatch'):
            self.score()

    def test_unlabeled_candidates_do_not_become_false_positives_or_success(self):
        self.benchmark['documents'] = [d for d in self.benchmark['documents'] if d['source_group'] != 'ownership_origin']
        result = self.score()
        self.assertEqual(result['extraction']['unlabeled_candidates'], 1)
        self.assertEqual(result['extraction']['candidate_label_coverage'], .75)
        self.assertEqual(result['extraction']['false_positive'], 0)
        self.assertEqual(next(g['status'] for g in result['gates'] if g['name'] == 'candidate_label_coverage'), 'FAILED')

    def test_zero_positive_gold_and_empty_predictions_are_not_perfect_scores(self):
        for doc in self.benchmark['documents']:
            doc['claims'] = []
        result = self.score()
        self.assertEqual(result['extraction']['precision'], 0)
        self.assertIsNone(result['extraction']['end_to_end_reference_recall'])
        self.assertIsNone(wilson(0, 0))

    def test_no_model_output_is_not_quality_pass(self):
        config = deepcopy(self.config)
        config['budget']['max_model_calls'] = 0
        execute(self.fixture['target'], config, self.root / 'no-model', fixture=self.fixture)
        result = evaluate(self.root / 'no-model/run.json', self.bench_path, self.policy_path)
        self.assertIsNone(result['extraction']['precision'])
        self.assertEqual(result['extraction']['end_to_end_reference_recall'], 0)
        self.assertEqual(result['decision'], 'NOT_READY')

    def test_semantically_reversed_valid_quote_loses_credit(self):
        fixture = deepcopy(self.fixture)
        for role in ('small', 'large'):
            c = fixture['model_outputs']['https://source.example.invalid/sample'][role]['claims'][0]
            c['subject'], c['object'] = c['object'], c['subject']
        execute(fixture['target'], self.config, self.root / 'reversed', fixture=fixture)
        result = evaluate(self.root / 'reversed/run.json', self.bench_path, self.policy_path)
        self.assertGreater(result['extraction']['false_positive'], 0)
        self.assertLess(result['extraction']['precision'], 1)

    def test_unknown_rank_judgments_do_not_get_fake_ndcg(self):
        groups, lookup = benchmark_check(self.benchmark)
        result = retrieval(['https://unjudged.example/a', 'https://source.example.invalid/sample'], groups, lookup, 10)
        self.assertEqual(result['judgment_coverage_at_k'], .5)
        self.assertEqual(result['precision_on_judged_at_k'], 1)
        self.assertIsNone(result['ndcg_at_k'])
        self.assertEqual(result['reference_reciprocal_rank'], .5)

    def test_url_aliases_cannot_inflate_reference_denominator(self):
        self.benchmark['sources'][1]['urls'].append('https://source.example.invalid/sample?utm_source=mirror')
        with self.assertRaisesRegex(ValueError, 'multiple_groups'):
            self.score()

    def test_draft_creation_does_not_copy_model_answers(self):
        draft = draft_benchmark(self.run)
        self.assertTrue(all(not d['claims'] and not d['annotation_complete'] for d in draft['documents']))
        self.assertTrue(all(s['relevance'] is None for s in draft['sources']))
        self.benchmark = draft
        with self.assertRaisesRegex(ValueError, 'explicit_allow_draft'):
            self.score()
        self.assertEqual(self.score(allow_draft=True)['decision'], 'NOT_READY')

    def test_adjudication_requires_distinct_reviewers_and_group_review(self):
        self.benchmark['annotation']['annotators'] = ['same', 'same']
        with self.assertRaises(ValueError):
            self.score()
        self.benchmark['annotation']['annotators'] = ['a', 'b']
        self.benchmark['annotation']['groups_reviewed'] = False
        with self.assertRaisesRegex(ValueError, 'complete_review'):
            self.score()

    def test_gold_cannot_contain_post_cutoff_sources(self):
        self.benchmark['sources'][0]['published_at'] = '2027-01-01T00:00:00Z'
        with self.assertRaisesRegex(ValueError, 'after_cutoff'):
            self.score()

    def test_review_template_is_unknown_and_stale_bindings_are_rejected(self):
        reviews = review_template(self.run_path, self.bench_path)
        self.assertEqual(reviews['candidates'], [])
        self.assertTrue(all(r['capture_permission'] == 'UNKNOWN' for r in reviews['documents']))
        reviews['run_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'binding_mismatch'):
            self.score(reviews)

    def test_duplicate_human_review_cannot_fake_two_reviewers(self):
        reviews = review_template(self.run_path, self.bench_path)
        row = {'candidate_id': self.run['candidates'][0]['id'], 'reviewer': 'human_a', 'reviewer_type': 'HUMAN',
               'verdict': 'CORRECT', 'error_types': [], 'reason': 'synthetic test', 'reviewed_at': self.run['finished_at']}
        reviews['candidates'] = [row, deepcopy(row)]
        with self.assertRaisesRegex(ValueError, 'duplicate_or_unknown_candidate_review'):
            self.score(reviews)

    def test_model_reviews_are_excluded_and_conflicts_preserved(self):
        candidate = self.run['candidates'][0]['id']
        base = {'candidate_id': candidate, 'reviewer_type': 'MODEL', 'verdict': 'CORRECT', 'error_types': [],
                'reason': 'synthetic test', 'reviewed_at': self.run['finished_at']}
        reviews = {'candidates': [{**base, 'reviewer': 'model_a'}, {**base, 'reviewer': 'model_b'}]}
        self.assertEqual(human_metrics(self.run, reviews, 2)['reviewed_candidates'], 0)
        reviews['candidates'] += [{**base, 'reviewer': 'human_a', 'reviewer_type': 'HUMAN'},
                                 {**base, 'reviewer': 'human_b', 'reviewer_type': 'HUMAN',
                                  'verdict': 'INCORRECT', 'error_types': ['REVERSED_RELATION']}]
        result = human_metrics(self.run, reviews, 2)
        self.assertEqual(result['conflicting_candidates'], 1)
        self.assertEqual(result['critical_error_reviews'], 1)

    def test_cloud_denial_and_missing_permissions_stay_visible(self):
        run = deepcopy(self.run)
        doc = run['extractions'][0]['document_id']
        attempt = run['extractions'][0]['attempts'][0]
        attempt.update(status='FAILED', synthetic=False, endpoint='https://model.example/v1')
        reviews = {'documents': [{'document_id': doc, 'capture_permission': 'ALLOWED', 'cloud_permission': 'DENIED'}]}
        result = governance_metrics(run, reviews)
        self.assertEqual(result['outbound_with_denied_permission'], [doc])
        self.assertTrue(result['documents_missing_capture_permission'])
        self.assertEqual(result['legal_compliance'], 'NOT_ASSESSED')

    def test_permission_placeholder_cannot_become_approval(self):
        reviews = review_template(self.run_path, self.bench_path)
        reviews['documents'][0]['capture_permission'] = 'ALLOWED'
        with self.assertRaisesRegex(ValueError, 'requires_basis_and_reviewer'):
            self.score(reviews)

    def test_human_time_is_unknown_until_every_review_row_is_timed(self):
        base = {'candidate_id': self.run['candidates'][0]['id'], 'reviewer_type': 'HUMAN',
                'verdict': 'CORRECT', 'error_types': [], 'reason': 'synthetic test',
                'reviewed_at': self.run['finished_at']}
        rows = [{**base, 'reviewer': 'a', 'effort_minutes': 2}, {**base, 'reviewer': 'b'}]
        self.assertIsNone(human_metrics(self.run, {'candidates': rows}, 2)['human_minutes_declared'])
        rows[1]['effort_minutes'] = 3
        result = human_metrics(self.run, {'candidates': rows}, 2)
        self.assertEqual(result['human_minutes_declared'], 5)
        self.assertEqual(result['minutes_per_unanimously_correct_candidate'], 5)

    def test_human_verdict_conflicting_with_gold_is_exposed(self):
        reviews = review_template(self.run_path, self.bench_path)
        reviews['candidates'] = [{'candidate_id': self.run['candidates'][0]['id'], 'reviewer': 'human',
                                  'reviewer_type': 'HUMAN', 'verdict': 'INCORRECT', 'error_types': ['OTHER'],
                                  'reason': 'unit-test disagreement', 'reviewed_at': self.run['finished_at']}]
        result = self.score(reviews)
        self.assertEqual(result['human_review']['gold_disagreement_review_rows'], 1)
        self.assertEqual(next(g['status'] for g in result['gates'] if g['name'] == 'human_gold_disagreements'), 'FAILED')

    def test_cli_not_ready_is_exit_three_and_writes_report(self):
        p = subprocess.run([sys.executable, str(REPO / 'scripts/evaluate_research.py'), 'score',
                            '--run', str(self.run_path), '--benchmark', str(self.bench_path),
                            '--out', str(self.root / 'cli-score')], capture_output=True, text=True)
        self.assertEqual(p.returncode, 3, p.stderr)
        self.assertTrue((self.root / 'cli-score/metrics.csv').exists())
        self.assertEqual(json.loads(p.stdout)['decision'], 'NOT_READY')


if __name__ == '__main__':
    unittest.main()
