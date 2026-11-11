"""Offline tests for API profile selection and model discovery."""

from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from labs import common


class ApiProfileTests(unittest.TestCase):
    def test_course_profile_uses_separate_key_endpoint_and_models(self):
        env = {
            "LAB_API_PROFILE": "course",
            "API_KEY": "cloudru-key-must-not-be-used",
            "COURSE_API_KEY": "sk-bf-student-key",
            "COURSE_MODEL_A": "provider/model-a",
            "COURSE_MODEL_B": "provider/model-b",
        }
        with patch.dict(os.environ, env, clear=True), patch.object(
            common, "dotenv_values", return_value={}
        ):
            config = common.load_config()

        self.assertEqual(config.profile, "course")
        self.assertEqual(config.api_key, "sk-bf-student-key")
        self.assertEqual(config.base_url, "https://proxy-prompts.aiclab.tech/v1")
        self.assertEqual(config.models, ("provider/model-a", "provider/model-b"))

    def test_cloudru_profile_keeps_existing_configuration(self):
        env = {
            "LAB_API_PROFILE": "cloudru",
            "API_KEY": "cloudru-key",
            "COURSE_API_KEY": "course-key-must-not-be-used",
        }
        with patch.dict(os.environ, env, clear=True), patch.object(
            common, "dotenv_values", return_value={}
        ):
            config = common.load_config()

        self.assertEqual(config.profile, "cloudru")
        self.assertEqual(config.api_key, "cloudru-key")
        self.assertEqual(config.base_url, common.BASE_URL)
        self.assertEqual(config.models, common.DEFAULT_MODELS)

    def test_course_profile_requires_its_own_key(self):
        with patch.dict(
            os.environ, {"LAB_API_PROFILE": "course", "API_KEY": "old-key"}, clear=True
        ), patch.object(common, "dotenv_values", return_value={}):
            with self.assertRaisesRegex(RuntimeError, "COURSE_API_KEY"):
                common.load_config()

    def test_course_profile_rejects_example_key(self):
        with patch.dict(
            os.environ,
            {"LAB_API_PROFILE": "course", "COURSE_API_KEY": "your_course_api_key_here"},
            clear=True,
        ), patch.object(common, "dotenv_values", return_value={}):
            with self.assertRaisesRegex(RuntimeError, "COURSE_API_KEY"):
                common.load_config()

    def test_unknown_profile_is_rejected(self):
        with patch.dict(os.environ, {"LAB_API_PROFILE": "unknown"}, clear=True), patch.object(
            common, "dotenv_values", return_value={}
        ):
            with self.assertRaisesRegex(ValueError, "LAB_API_PROFILE"):
                common.load_config()

    def test_course_model_discovery_uses_usage_allowed_models(self):
        client = SimpleNamespace(
            base_url="https://proxy-prompts.aiclab.tech/v1",
            api_key="secret-test-key",
            _lab_api_profile="course",
        )
        response = SimpleNamespace(
            json=lambda: {
                "provider_configs": [
                    {"allowed_models": ["provider/model-b", "provider/model-a"]},
                    {"allowed_models": ["provider/model-a"]},
                ]
            },
            raise_for_status=lambda: None,
        )
        with patch.object(common.requests, "get", return_value=response) as get:
            models = common.list_models(client)

        self.assertEqual(models, ["provider/model-a", "provider/model-b"])
        args, kwargs = get.call_args
        self.assertEqual(args[0], "https://proxy-prompts.aiclab.tech/usage")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer secret-test-key")
        self.assertEqual(kwargs["timeout"], 30)

    def test_cloudru_model_discovery_keeps_openai_models_endpoint(self):
        client = SimpleNamespace(
            models=SimpleNamespace(
                list=lambda: SimpleNamespace(
                    data=[SimpleNamespace(id="provider/model-b"), SimpleNamespace(id="provider/model-a")]
                )
            )
        )
        self.assertEqual(common.list_models(client), ["provider/model-a", "provider/model-b"])

    def test_make_client_remembers_selected_profile(self):
        config = common.LabConfig(
            "test-key", common.COURSE_BASE_URL, common.COURSE_DEFAULT_MODELS,
            "unused", 2048, 30, "course"
        )
        client = common.make_client(config)
        try:
            self.assertEqual(client._lab_api_profile, "course")
        finally:
            client.close()


if __name__ == "__main__":
    unittest.main()
