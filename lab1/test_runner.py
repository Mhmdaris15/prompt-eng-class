"""Offline regression tests: python -m unittest lab1.test_runner -v."""

import csv
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lab1 import runner
from labs.common import LabConfig


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.models = ['moonshotai/Kimi-K2.6', 'Qwen/Qwen3-Coder-Next']
        self.config = LabConfig('fake-test-key', 'https://example.invalid/v1',
                                tuple(self.models), 'unused', 8192, 1)
        self.requests = []
        self.failure = False
        self.finish = 'stop'
        self.content = 'connection verified.'

        def create(**kwargs):
            self.requests.append(kwargs)
            if self.failure:
                raise RuntimeError('simulated failure')
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=self.content),
                                         finish_reason=self.finish)],
                usage=SimpleNamespace(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            )
        self.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    def run_batch(self):
        with patch.object(runner, 'OUTPUT_DIR', self.root), \
             patch.object(runner, 'list_models', return_value=self.models):
            return runner.run(self.config, self.client, self.models)

    def test_configured_budget_reaches_both_models(self):
        self.run_batch()
        self.assertEqual({r['max_tokens'] for r in self.requests}, {8192})
        for first, second in zip(self.requests[::2], self.requests[1::2]):
            self.assertEqual(first['messages'], second['messages'])

    def test_rerun_preserves_completed_review_and_raw_data(self):
        first = self.run_batch()
        first_path = Path(first.get('output_dir', self.root))
        review = first_path / 'quality_scores.csv'
        review.write_text('completed review', encoding='utf-8')
        raw = (first_path / 'lab1_results.csv').read_bytes()
        second = self.run_batch()
        self.assertEqual(review.read_text(encoding='utf-8'), 'completed review')
        self.assertEqual((first_path / 'lab1_results.csv').read_bytes(), raw)
        self.assertNotEqual(first['output_dir'], second['output_dir'])

    def test_failures_are_reported_and_saved(self):
        self.failure = True
        result = self.run_batch()
        self.assertEqual(result['status'], 'failed')
        self.assertGreater(result['error_count'], 0)
        with (Path(result['output_dir']) / 'connection_checks.csv').open(encoding='utf-8-sig') as handle:
            saved = list(csv.DictReader(handle))
        self.assertTrue(all(r['error'] for r in saved))

    def test_truncation_is_not_success(self):
        self.finish = 'length'
        self.assertEqual(self.run_batch()['status'], 'incomplete')

    def test_empty_response_is_not_success(self):
        self.content = ''
        self.assertNotEqual(self.run_batch()['status'], 'success')

    def test_caution_does_not_match_confident_substring(self):
        self.assertEqual(runner.metrics('недостаточно данных')['confident_marker_count'], 0)
        self.assertEqual(runner.metrics('Точно. Однозначно.')['confident_marker_count'], 2)

    def test_missing_context_marker_is_recognized(self):
        self.assertEqual(runner.metrics('The information is unavailable.')['caution_marker_count'], 1)

    def test_duplicate_models_are_rejected(self):
        with patch.object(runner, 'OUTPUT_DIR', self.root), \
             patch.object(runner, 'list_models', return_value=self.models):
            with self.assertRaises(ValueError):
                runner.run(self.config, self.client, [self.models[0]] * 2)
        self.assertEqual(self.requests, [])


if __name__ == '__main__':
    unittest.main()
