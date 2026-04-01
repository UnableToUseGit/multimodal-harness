import json
import tempfile
import unittest
from pathlib import Path

from video_atlas.config import load_canonical_pipeline_config, load_derived_pipeline_config


class ConfigLoadingTest(unittest.TestCase):
    def test_load_canonical_pipeline_config_reads_acquisition_config(self) -> None:
        payload = {
            "planner": {"provider": "openai_compatible", "model_name": "planner-model"},
            "acquisition": {
                "enabled": True,
                "prefer_youtube_subtitles": True,
                "youtube_output_template": "%(id)s.%(ext)s",
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "canonical-acquisition.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            config = load_canonical_pipeline_config(path)

        self.assertTrue(config.acquisition.enabled)
        self.assertTrue(config.acquisition.prefer_youtube_subtitles)
        self.assertEqual(config.acquisition.youtube_output_template, "%(id)s.%(ext)s")

    def test_load_canonical_pipeline_config_supports_new_structure(self) -> None:
        payload = {
            "planner": {
                "provider": "openai_compatible",
                "model_name": "planner-model",
                "extra_body": {"chat_template_kwargs": {"enable_thinking": True}},
            },
            "text_segmentor": {
                "provider": "openai_compatible",
                "model_name": "text-segmentor-model",
                "connection": "remote",
            },
            "multimodal_segmentor": {
                "provider": "openai_compatible",
                "model_name": "multimodal-segmentor-model",
                "connection": "local",
            },
            "structure_composer": {
                "provider": "openai_compatible",
                "model_name": "structure-composer-model",
                "connection": "remote",
            },
            "captioner": {"provider": "openai_compatible", "model_name": "caption-model", "max_tokens": 3000},
            "runtime": {
                "verbose": True,
                "generate_subtitles_if_missing": False,
                "text_chunk_size_sec": 1800,
                "text_chunk_overlap_sec": 120,
                "multimodal_chunk_size_sec": 600,
                "multimodal_chunk_overlap_sec": 20,
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "canonical.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            config = load_canonical_pipeline_config(path)

        self.assertEqual(config.planner.model_name, "planner-model")
        self.assertEqual(config.text_segmentor.model_name, "text-segmentor-model")
        self.assertEqual(config.text_segmentor.connection, "remote")
        self.assertEqual(config.multimodal_segmentor.model_name, "multimodal-segmentor-model")
        self.assertEqual(config.multimodal_segmentor.connection, "local")
        self.assertEqual(config.structure_composer.model_name, "structure-composer-model")
        self.assertEqual(config.structure_composer.connection, "remote")
        self.assertEqual(config.segmentor.model_name, "text-segmentor-model")
        self.assertEqual(config.captioner.model_name, "caption-model")
        self.assertEqual(config.captioner.max_tokens, 3000)
        self.assertFalse(config.runtime.generate_subtitles_if_missing)
        self.assertTrue(config.runtime.verbose)
        self.assertEqual(config.runtime.text_chunk_size_sec, 1800)
        self.assertEqual(config.runtime.text_chunk_overlap_sec, 120)
        self.assertEqual(config.runtime.multimodal_chunk_size_sec, 600)
        self.assertEqual(config.runtime.multimodal_chunk_overlap_sec, 20)
        self.assertEqual(config.planner.extra_body, {"chat_template_kwargs": {"enable_thinking": True}})

    def test_load_canonical_pipeline_config_preserves_legacy_shape(self) -> None:
        payload = {
            "planner": {"provider": "openai_compatible", "model_name": "planner-model"},
            "segmentor": {"provider": "openai_compatible", "model_name": "segmentor-model"},
            "runtime": {
                "chunk_size_sec": 420,
                "chunk_overlap_sec": 24,
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "canonical-legacy.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            config = load_canonical_pipeline_config(path)

        self.assertEqual(config.segmentor.model_name, "segmentor-model")
        self.assertEqual(config.text_segmentor.model_name, "segmentor-model")
        self.assertEqual(config.multimodal_segmentor.model_name, "segmentor-model")
        self.assertEqual(config.structure_composer.model_name, "planner-model")
        self.assertEqual(config.runtime.text_chunk_size_sec, 420)
        self.assertEqual(config.runtime.text_chunk_overlap_sec, 24)
        self.assertEqual(config.runtime.multimodal_chunk_size_sec, 420)
        self.assertEqual(config.runtime.multimodal_chunk_overlap_sec, 24)

    def test_load_derived_pipeline_config(self) -> None:
        payload = {
            "planner": {"provider": "openai_compatible", "model_name": "planner-model"},
            "segmentor": {"provider": "openai_compatible", "model_name": "segmentor-model"},
            "captioner": {"provider": "openai_compatible", "model_name": "caption-model"},
            "runtime": {
                "verbose": True,
                "num_workers": 3,
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "derived.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            config = load_derived_pipeline_config(path)

        self.assertEqual(config.planner.model_name, "planner-model")
        self.assertEqual(config.segmentor.model_name, "segmentor-model")
        self.assertEqual(config.captioner.model_name, "caption-model")
        self.assertTrue(config.runtime.verbose)
        self.assertEqual(config.runtime.num_workers, 3)

if __name__ == "__main__":
    unittest.main()
