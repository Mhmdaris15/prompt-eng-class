"""Offline tests for Lab 2 profile configuration and result persistence."""

from __future__ import annotations

import csv
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from labs import common as shared
from lab2 import common


def shared_config(profile: str) -> shared.LabConfig:
    if profile == "course":
        return shared.LabConfig(
            api_key="course-test-secret",
            base_url="https://course.example/v1",
            models=("provider/course-a", "provider/course-b"),
            embedding_model="provider/embed",
            max_tokens=3072,
            timeout=75.0,
            profile="course",
        )
    return shared.LabConfig(
        api_key="cloudru-test-secret",
        base_url="https://cloudru.example/v1",
        models=("provider/cloud-a", "provider/cloud-b"),
        embedding_model="provider/embed",
        max_tokens=2048,
        timeout=90.0,
        profile="cloudru",
    )


def legacy_config() -> common.Lab2Config:
    return common.Lab2Config(
        api_key="test-key",
        base_url="https://example.invalid/v1",
        primary_model="provider/fallback-a",
        secondary_model="provider/fallback-b",
    )


class Lab2ProfileTests(unittest.TestCase):
    def test_cloudru_profile_maps_endpoint_and_models(self):
        with patch.dict(os.environ, {"LAB_API_PROFILE": "cloudru", "API_KEY": "legacy-key"}), \
             patch.object(shared, "load_config", return_value=shared_config("cloudru")) as load:
            config = common.Lab2Config.from_env()

        load.assert_called_once_with(None)
        self.assertEqual(config.api_key, "cloudru-test-secret")
        self.assertEqual(config.base_url, "https://cloudru.example/v1")
        self.assertEqual((config.primary_model, config.secondary_model),
                         ("provider/cloud-a", "provider/cloud-b"))
        self.assertEqual(config.max_tokens, 2048)
        self.assertEqual(config.timeout, 90.0)
        self.assertEqual(config.profile, "cloudru")

    def test_course_profile_maps_its_own_endpoint_and_models(self):
        with patch.dict(os.environ, {"LAB_API_PROFILE": "course", "API_KEY": "legacy-cloud-key"}), \
             patch.object(shared, "load_config", return_value=shared_config("course")) as load:
            config = common.Lab2Config.from_env()

        load.assert_called_once_with(None)
        self.assertEqual(config.api_key, "course-test-secret")
        self.assertEqual(config.base_url, "https://course.example/v1")
        self.assertEqual((config.primary_model, config.secondary_model),
                         ("provider/course-a", "provider/course-b"))
        self.assertEqual(config.max_tokens, 3072)
        self.assertEqual(config.timeout, 75.0)
        self.assertEqual(config.profile, "course")

    def test_model_discovery_uses_cloudru_models_endpoint_client(self):
        client = SimpleNamespace(
            models=SimpleNamespace(
                list=lambda: SimpleNamespace(data=[
                    SimpleNamespace(id="provider/model-a"),
                    SimpleNamespace(id="provider/model-b"),
                ])
            )
        )
        config = legacy_config()
        with patch.object(shared, "make_client", return_value=client) as make_client:
            actual = common.Lab2Client(config).list_models()

        make_client.assert_called_once()
        self.assertEqual(actual, ["provider/model-a", "provider/model-b"])

    def test_model_discovery_uses_course_allowed_models(self):
        client = SimpleNamespace(
            _lab_api_profile="course",
            models=SimpleNamespace(list=lambda: (_ for _ in ()).throw(RuntimeError("wrong endpoint"))),
        )
        config = legacy_config()
        usage = {"provider_configs": [
            {"allowed_models": ["provider/course-b", "provider/course-a"]}
        ]}
        with patch.object(shared, "make_client", return_value=client), \
             patch.object(shared, "course_usage", return_value=usage):
            actual = common.Lab2Client(config).list_models()

        self.assertEqual(actual, ["provider/course-a", "provider/course-b"])

    def test_manifest_does_not_serialize_api_key(self):
        with patch.dict(os.environ, {"LAB_API_PROFILE": "course", "API_KEY": "legacy-cloud-key"}), \
             patch.object(shared, "load_config", return_value=shared_config("course")):
            config = common.Lab2Config.from_env()
        manifest = common.create_manifest(config, [], "source-hash", "runner-hash")
        serialized = json.dumps(manifest)

        self.assertNotIn(config.api_key, serialized)
        self.assertEqual(manifest["config"].get("api_profile"), "course")

    def test_nonpositive_token_limit_is_rejected(self):
        invalid = shared.LabConfig(
            api_key="test-key",
            base_url="https://course.example/v1",
            models=("provider/a", "provider/b"),
            embedding_model="provider/embed",
            max_tokens=0,
            timeout=30.0,
            profile="course",
        )
        with patch.dict(os.environ, {"LAB_API_PROFILE": "course", "API_KEY": "legacy-key"}), \
             patch.object(shared, "load_config", return_value=invalid):
            with self.assertRaisesRegex(ValueError, "must be positive"):
                common.Lab2Config.from_env()

    def test_nonpositive_timeout_is_rejected(self):
        invalid = shared.LabConfig(
            api_key="test-key",
            base_url="https://course.example/v1",
            models=("provider/a", "provider/b"),
            embedding_model="provider/embed",
            max_tokens=1024,
            timeout=0.0,
            profile="course",
        )
        with patch.dict(os.environ, {"LAB_API_PROFILE": "course", "API_KEY": "legacy-key"}), \
             patch.object(shared, "load_config", return_value=invalid):
            with self.assertRaisesRegex(ValueError, "must be positive"):
                common.Lab2Config.from_env()

    def test_csv_round_trip_preserves_commas_and_newlines(self):
        result = common.CompletionResult(
            model="provider/model-a",
            prompt_name="v1",
            prompt="Line one, with comma\nline two",
            answer="Answer, with comma\nand newline",
            status="ok",
            latency_sec=1.25,
            answer_length=30,
            finish_reason="stop",
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "results.csv"
            common.save_results_csv([result], str(path))
            with path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["prompt"], "Line one, with comma\nline two")
        self.assertEqual(rows[0]["answer"], "Answer, with comma\nand newline")
        self.assertEqual(rows[0]["model"], "provider/model-a")


class Lab2RunnerBehaviorTests(unittest.TestCase):
    def make_runner(self, temporary, fake_client):
        from lab2.runner import Lab2Runner

        config = legacy_config()
        config.primary_model = "anthropic/claude-haiku-4.5"
        config.secondary_model = "meta-llama/llama-3.3-70b-instruct"
        config.output_dir = str(Path(temporary) / "run")
        runner = Lab2Runner.__new__(Lab2Runner)
        runner.config = config
        runner.client = fake_client
        runner.results = []
        runner.output_dir = Path(config.output_dir)
        runner.output_dir.mkdir(parents=True)
        runner.prompts = {}
        runner.prompt_versions = {}
        runner.evaluation_results = []
        return runner

    def test_baseline_is_primary_only_and_review_is_one_way_with_full_context(self):
        from lab2 import runner as runner_module

        class FakeClient:
            def __init__(self):
                self.calls = []

            def list_models(self):
                return ["anthropic/claude-haiku-4.5", "meta-llama/llama-3.3-70b-instruct"]

            def complete_with_metrics(self, model, prompt_name, prompt, **kwargs):
                self.calls.append((model, prompt_name, prompt))
                answer = " ".join(["This is a careful educational essay sentence."] * 28)
                if prompt_name == "evaluation":
                    answer = json.dumps({"scores": {}, "overall_assessment": "Acceptable"})
                return common.CompletionResult(model, prompt_name, prompt, answer, "ok", finish_reason="stop")

        with tempfile.TemporaryDirectory() as temporary:
            client = FakeClient()
            runner = self.make_runner(temporary, client)
            with patch.object(runner_module, "Lab2Client", return_value=client):
                runner.run_all()

        baseline_models = [model for model, name, _ in client.calls if name == "simple"]
        self.assertEqual(baseline_models, [runner.config.primary_model])
        for version in ("v1", "v2", "v3"):
            prompts = [prompt for _, name, prompt in client.calls if name == version]
            self.assertEqual(len(prompts), 2)
            self.assertEqual(prompts[0], prompts[1])
        reviewers = [(model, name) for model, name, _ in client.calls if name.startswith("evaluation")]
        self.assertEqual(reviewers, [(runner.config.secondary_model, "evaluation")])
        review_prompt = next(prompt for _, name, prompt in client.calls if name == "evaluation")
        from lab2.source_text import TASK, GOOD_RESULT_CRITERIA
        self.assertIn(TASK, review_prompt)
        self.assertIn(GOOD_RESULT_CRITERIA[0], review_prompt)
        self.assertIn(runner.prompts["v3"], review_prompt)

    def test_v3_primary_retry_is_limited_to_two_and_records_attempts(self):
        from lab2.runner import Lab2Runner

        class FakeClient:
            def __init__(self):
                self.calls = []

            def complete_with_metrics(self, model, prompt_name, prompt, **kwargs):
                self.calls.append((model, prompt_name))
                return common.CompletionResult(model, prompt_name, prompt, "too short", "ok")

        with tempfile.TemporaryDirectory() as temporary:
            client = FakeClient()
            runner = self.make_runner(temporary, client)
            runner._task4_few_shot_examples = lambda: runner.prompt_versions.update({
                "examples": {"good_example": {"text": "example"}}
            })
            Lab2Runner._task6_v3_few_shot(runner)

        primary_attempts = [r for r in runner.results if r.model == runner.config.primary_model]
        secondary_attempts = [r for r in runner.results if r.model == runner.config.secondary_model]
        self.assertEqual(len(primary_attempts), 2)
        self.assertEqual([r.attempt for r in primary_attempts], [1, 2])
        self.assertEqual([r.word_count for r in primary_attempts], [2, 2])
        self.assertEqual(len(secondary_attempts), 1)

    def test_unavailable_model_stops_before_any_completion(self):
        from lab2.runner import Lab2Runner

        class FakeClient:
            def __init__(self):
                self.completion_calls = 0

            def list_models(self):
                return ["anthropic/claude-haiku-4.5"]

            def complete_with_metrics(self, **kwargs):
                self.completion_calls += 1

        with tempfile.TemporaryDirectory() as temporary:
            client = FakeClient()
            runner = self.make_runner(temporary, client)
            with self.assertRaisesRegex(ValueError, "unavailable"):
                runner.run_all()
        self.assertEqual(client.completion_calls, 0)

    def test_audience_edge_prompt_contains_previous_model_a_essay(self):
        from lab2.runner import Lab2Runner

        class FakeClient:
            def __init__(self):
                self.prompts = []

            def complete_with_metrics(self, model, prompt_name, prompt, **kwargs):
                self.prompts.append((prompt_name, prompt))
                return common.CompletionResult(model, prompt_name, prompt, "edge answer", "ok")

        with tempfile.TemporaryDirectory() as temporary:
            client = FakeClient()
            runner = self.make_runner(temporary, client)
            essay = "PRIMARY ESSAY CONTEXT"
            runner.results.append(common.CompletionResult(
                runner.config.primary_model, "v3", "final prompt", essay, "ok"
            ))
            Lab2Runner._task8_edge_cases(runner)

        audience_prompt = next(prompt for name, prompt in client.prompts if name == "edge_audience_change")
        self.assertIn(essay, audience_prompt)

    def test_empty_completion_is_not_success(self):
        class FakeCompletions:
            def create(self, **kwargs):
                return SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content=""), finish_reason="stop")],
                    usage=None,
                )

        client = common.Lab2Client.__new__(common.Lab2Client)
        client.config = legacy_config()
        client.client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
        result = client.complete("provider/model", "prompt")
        self.assertEqual(result.status, "error")

    def test_length_finish_reason_is_truncated(self):
        class FakeCompletions:
            def create(self, **kwargs):
                return SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content="partial answer"), finish_reason="length")],
                    usage=None,
                )

        client = common.Lab2Client.__new__(common.Lab2Client)
        client.config = legacy_config()
        client.client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
        result = client.complete("provider/model", "prompt")
        self.assertEqual(result.status, "truncated")

    def test_evaluation_parser_accepts_fenced_json_with_trailing_text(self):
        from lab2.runner import parse_evaluation_response

        raw = 'Reviewer note:\n```json\n{"scores":{"criterion_1":2}}\n```\nExtra commentary.'
        self.assertEqual(parse_evaluation_response(raw), {"scores": {"criterion_1": 2}})

    def test_evaluation_parser_rejects_invalid_json_without_losing_source_text(self):
        from lab2.runner import parse_evaluation_response

        raw = 'Reviewer gave scores but no JSON object.'
        with self.assertRaises(json.JSONDecodeError):
            parse_evaluation_response(raw)
        self.assertIn("scores", raw)

    def test_existing_output_folder_is_rejected(self):
        from lab2.runner import Lab2Runner

        with tempfile.TemporaryDirectory() as temporary:
            config = legacy_config()
            config.output_dir = temporary
            with self.assertRaises(FileExistsError):
                Lab2Runner(config)


if __name__ == "__main__":
    unittest.main()
