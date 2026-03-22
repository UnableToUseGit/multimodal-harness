import json
import tempfile
import unittest
from pathlib import Path

from video_atlas.config import load_canonical_pipeline_config


class ConfigLoadingTest(unittest.TestCase):
    def test_load_canonical_pipeline_config(self) -> None:
        payload = {
            "planner": {"provider": "openai_compatible", "model_name": "planner-model", "extra_body": {"chat_template_kwargs": {"enable_thinking": True}}},
            "segmentor": {"provider": "openai_compatible", "model_name": "segmentor-model"},
            "captioner": {"provider": "openai_compatible", "model_name": "caption-model", "max_tokens": 3000},
            "runtime": {
                "verbose": True,
                "generate_subtitles_if_missing": False,
                "chunk_size_sec": 420,
                "chunk_overlap_sec": 24,
            },
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
        self.assertEqual(config.runtime.chunk_size_sec, 420)
        self.assertEqual(config.runtime.chunk_overlap_sec, 24)
        self.assertEqual(config.planner.extra_body, {"chat_template_kwargs": {"enable_thinking": True}})

if __name__ == "__main__":
    unittest.main()
