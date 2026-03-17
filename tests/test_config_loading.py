import json
import tempfile
import unittest
from pathlib import Path

from video_atlas.config import load_canonical_pipeline_config, load_task_derivation_config


class ConfigLoadingTest(unittest.TestCase):
    def test_load_canonical_pipeline_config(self) -> None:
        payload = {
            "planner": {"provider": "openai_compatible", "model_name": "planner-model", "extra_body": {"chat_template_kwargs": {"enable_thinking": True}}},
            "segmentor": {"provider": "openai_compatible", "model_name": "segmentor-model"},
            "captioner": {"provider": "openai_compatible", "model_name": "caption-model", "max_tokens": 3000},
            "runtime": {"verbose": True, "generate_subtitles_if_missing": False}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "canonical.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            config = load_canonical_pipeline_config(path)

        self.assertEqual(config.planner.model_name, "planner-model")
        self.assertEqual(config.segmentor.model_name, "segmentor-model")
        self.assertEqual(config.captioner.model_name, "caption-model")
        self.assertEqual(config.captioner.max_tokens, 3000)
        self.assertFalse(config.runtime.generate_subtitles_if_missing)
        self.assertTrue(config.runtime.verbose)
        self.assertEqual(config.planner.extra_body, {"chat_template_kwargs": {"enable_thinking": True}})

    def test_load_task_derivation_config(self) -> None:
        payload = {
            "generator": {"provider": "openai_compatible", "model_name": "derive-model", "max_tokens": 3200},
            "runtime": {"verbose": True}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "task.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            config = load_task_derivation_config(path)

        self.assertEqual(config.generator.model_name, "derive-model")
        self.assertEqual(config.generator.max_tokens, 3200)
        self.assertTrue(config.runtime.verbose)


if __name__ == "__main__":
    unittest.main()
