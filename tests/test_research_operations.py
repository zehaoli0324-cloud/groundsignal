"""Setup must remain offline, secrets stay private, audits never approve facts."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from industry_search.contracts import REPO, read_json
from industry_search.operations import audit, doctor, local_model_probe, prepare
from industry_search.pipeline import execute
from industry_search.planning import plan


class PlanningDepthTests(unittest.TestCase):
    def test_six_distinct_angles_keep_dimension_coverage_each_wave(self):
        target = read_json(REPO / 'examples/search/target-nvidia.json')
        budget = read_json(REPO / 'config/search.default.json')['budget']
        budget['max_queries'] = 54
        result = plan(target, budget)
        self.assertEqual(len(result['queries']), 54)
        self.assertEqual(len({q['query'] for q in result['queries']}), 54)
        for start in range(0, 54, 9):
            self.assertEqual({q['dimension'] for q in result['queries'][start:start + 9]}, set(target['dimensions']))
        self.assertIn('"NVIDIA"', result['queries'][9]['query'])
        self.assertIn('site:nvidia.com', result['queries'][18]['query'])
        self.assertTrue(all(len(q['query']) <= 128 for q in result['queries']))

    def test_deep_does_not_invent_dimensions_or_duplicate_to_fill_cap(self):
        target = read_json(REPO / 'examples/search/target-nvidia.json')
        target['dimensions'] = ['upstream', 'counterevidence']
        budget = read_json(REPO / 'config/search.default.json')['budget']
        budget['max_queries'] = 54
        self.assertEqual(len(plan(target, budget)['queries']), 12)


class SetupTests(unittest.TestCase):
    def test_prepare_has_no_network_and_preserves_seeds_only_mode(self):
        with tempfile.TemporaryDirectory() as directory, patch('requests.Session') as session:
            out = Path(directory) / 'session'
            result = prepare(REPO / 'examples/search/target-nvidia.seeded.json', 'deep', 'none', [], out)
            self.assertEqual(result['planned_queries'], 54)
            config = read_json(out / 'config.json')
            self.assertEqual(config['providers'], [])
            self.assertFalse(config['models']['large']['enabled'])
            self.assertEqual(config['budget']['max_search_calls'], 108)
            session.assert_not_called()
            with self.assertRaises(ValueError):
                prepare(out / 'target.json', 'quick', 'none', None, out)

    def test_doctor_is_offline_and_never_outputs_secret_values(self):
        config = read_json(REPO / 'config/search.qwen9b-flash.json')
        with patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'DO_NOT_EXPOSE_THIS_SECRET'}, clear=True), patch('requests.Session') as session:
            result = doctor(config)
            session.assert_not_called()
        self.assertTrue(result['collection_configuration_ready'])
        self.assertEqual(result['provider_authentication'], 'NOT_TESTED')
        self.assertEqual(result['models']['large']['status'], 'NOT_PROBED')
        self.assertNotIn('DO_NOT_EXPOSE_THIS_SECRET', json.dumps(result))
        self.assertEqual(result['source_permissions'], 'NOT_ASSESSED')

    def test_missing_keys_and_models_are_not_ready(self):
        config = read_json(REPO / 'config/search.qwen9b-flash.json')
        with patch.dict('os.environ', {}, clear=True):
            result = doctor(config)
        self.assertFalse(result['collection_configuration_ready'])
        self.assertFalse(result['extraction_configuration_ready'])

    def test_seed_mode_does_not_require_search_credentials(self):
        config = read_json(REPO / 'config/search.default.json')
        config['providers'] = []
        target = read_json(REPO / 'examples/search/target-nvidia.seeded.json')
        self.assertTrue(doctor(config, target)['collection_configuration_ready'])
        target['seed_urls'] = []
        self.assertFalse(doctor(config, target)['collection_configuration_ready'])

    def test_probe_never_contacts_a_remote_endpoint(self):
        model = read_json(REPO / 'config/search.qwen9b-flash.json')['models']['large']
        with patch('requests.Session') as session:
            result = local_model_probe(model)
            session.assert_not_called()
        self.assertEqual(result['status'], 'REMOTE_NOT_PROBED')

    def test_local_probe_is_metadata_only_and_missing_model_not_ready(self):
        config = read_json(REPO / 'config/search.qwen9b-flash.json')
        config['routing_mode'] = 'small_only'
        config['models']['large']['enabled'] = False
        session = Mock()
        session.get.return_value.status_code = 200
        session.get.return_value.json.return_value = {'data': [{'id': 'another-model'}]}
        with patch('requests.Session') as factory:
            factory.return_value.__enter__.return_value = session
            result = doctor(config, probe=True)
        self.assertFalse(result['extraction_configuration_ready'])
        self.assertEqual(result['models']['small']['status'], 'MODEL_NOT_LISTED')
        session.get.assert_called_once_with('http://127.0.0.1:11434/v1/models', timeout=3, allow_redirects=False)
        self.assertFalse(session.trust_env)
        session.post.assert_not_called()

    def test_probe_does_not_follow_redirects_or_echo_service_errors(self):
        model = read_json(REPO / 'config/search.qwen9b-flash.json')['models']['small']
        session = Mock()
        session.get.return_value.status_code = 302
        with patch('requests.Session') as factory:
            factory.return_value.__enter__.return_value = session
            result = local_model_probe(model)
        self.assertEqual(result['status'], 'LOCAL_METADATA_UNAVAILABLE')
        self.assertIsNone(result['model_available'])
        session.get.return_value.json.assert_not_called()


class AuditTests(unittest.TestCase):
    def test_model_budget_failure_exposes_unprocessed_documents(self):
        config = read_json(REPO / 'config/search.default.json')
        config['budget']['max_model_calls'] = 0
        fixture = read_json(REPO / 'examples/search/synthetic.json')
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'run'
            run = execute(fixture['target'], config, out, fixture=fixture)
            result = audit(out / 'run.json')
        self.assertEqual(len(result['documents_without_successful_model_response']), len(run['documents']))
        self.assertGreater(result['model_attempt_statuses'].get('BUDGET_EXHAUSTED', 0), 0)
        self.assertEqual(result['factual_precision'], 'UNASSESSED')

    def test_synthetic_integrity_never_becomes_factual_or_legal_approval(self):
        config = read_json(REPO / 'config/search.default.json')
        fixture = read_json(REPO / 'examples/search/synthetic.json')
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'run'
            execute(fixture['target'], config, out, fixture=fixture)
            result = audit(out / 'run.json')
        self.assertEqual(result['contract_integrity'], 'VALID')
        self.assertEqual(result['status'], 'TECHNICAL_AUDIT_ONLY')
        self.assertEqual(result['factual_precision'], 'UNASSESSED')
        self.assertEqual(result['legal_compliance'], 'NOT_ASSESSED')
        self.assertTrue(result['synthetic'])
        self.assertGreater(result['pending_candidates'], 0)


if __name__ == '__main__':
    unittest.main()
