import json
import os
import tempfile
import unittest
from pathlib import Path

from video_atlas.config import ModelRuntimeConfig, build_generator, load_canonical_pipeline_config
from video_atlas.prompts import get_prompt
from video_atlas.schemas.canonical_registry import SEGMENTATION_PROFILES
from video_atlas.settings import (
    ENV_LOCAL_API_BASE,
    ENV_LOCAL_API_KEY,
    ENV_REMOTE_API_BASE,
    ENV_REMOTE_API_KEY,
    get_settings,
)
from video_atlas.workflows.canonical_atlas.video_parsing import VideoParsingMixin
from video_atlas.workflows.canonical_atlas_workflow import CanonicalAtlasWorkflow


class CanonicalHighEfficiencyRouteRegistryTest(unittest.TestCase):
    def test_text_narrative_profiles_use_text_llm_route(self):
        self.assertEqual(SEGMENTATION_PROFILES["podcast_topic_conversation"].segmentation_route, "text_llm")
        self.assertEqual(SEGMENTATION_PROFILES["lecture_slide_driven"].segmentation_route, "text_llm")
        self.assertEqual(SEGMENTATION_PROFILES["explanatory_commentary"].segmentation_route, "text_llm")

    def test_visual_profiles_use_multimodal_local_route(self):
        self.assertEqual(SEGMENTATION_PROFILES["narrative_film"].segmentation_route, "multimodal_local")
        self.assertEqual(SEGMENTATION_PROFILES["sports_broadcast"].segmentation_route, "multimodal_local")
        self.assertEqual(SEGMENTATION_PROFILES["vlog_lifestyle"].segmentation_route, "multimodal_local")


class CanonicalHighEfficiencyConfigTest(unittest.TestCase):
    def test_load_canonical_config_supports_dual_segmentors_and_dual_chunk_settings(self):
        payload = {
            "planner": {"provider": "openai_compatible", "model_name": "planner-model"},
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
            "captioner": {"provider": "openai_compatible", "model_name": "caption-model"},
            "runtime": {
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

        self.assertEqual(config.text_segmentor.model_name, "text-segmentor-model")
        self.assertEqual(config.multimodal_segmentor.model_name, "multimodal-segmentor-model")
        self.assertEqual(config.text_segmentor.connection, "remote")
        self.assertEqual(config.multimodal_segmentor.connection, "local")
        self.assertEqual(config.structure_composer.model_name, "structure-composer-model")
        self.assertEqual(config.runtime.text_chunk_size_sec, 1800)
        self.assertEqual(config.runtime.text_chunk_overlap_sec, 120)
        self.assertEqual(config.runtime.multimodal_chunk_size_sec, 600)
        self.assertEqual(config.runtime.multimodal_chunk_overlap_sec, 20)


class CanonicalHighEfficiencyPromptTest(unittest.TestCase):
    def test_text_boundary_detection_prompt_is_registered(self):
        prompt = get_prompt("TEXT_BOUNDARY_DETECTION_PROMPT")

        self.assertEqual(prompt.name, "TEXT_BOUNDARY_DETECTION_PROMPT")
        self.assertIn("subtitles", prompt.input_fields)
        self.assertNotIn("t_start", prompt.render_user(
            subtitles="hello",
            core_start=0.0,
            core_end=30.0,
            concise_description="desc",
            segmentation_profile="podcast_topic_conversation",
            segmentation_policy="keep semantic blocks",
            last_detection_point="None",
        ))


class CanonicalHighEfficiencySettingsTest(unittest.TestCase):
    def setUp(self):
        self.original = {
            ENV_LOCAL_API_BASE: os.environ.get(ENV_LOCAL_API_BASE),
            ENV_LOCAL_API_KEY: os.environ.get(ENV_LOCAL_API_KEY),
            ENV_REMOTE_API_BASE: os.environ.get(ENV_REMOTE_API_BASE),
            ENV_REMOTE_API_KEY: os.environ.get(ENV_REMOTE_API_KEY),
        }
        for key in self.original:
            os.environ.pop(key, None)

    def tearDown(self):
        for key in self.original:
            os.environ.pop(key, None)
        for key, value in self.original.items():
            if value is not None:
                os.environ[key] = value

    def test_get_settings_supports_local_and_remote_connections(self):
        os.environ[ENV_LOCAL_API_BASE] = "http://local.test/v1"
        os.environ[ENV_LOCAL_API_KEY] = "local-key"
        os.environ[ENV_REMOTE_API_BASE] = "http://remote.test/v1"
        os.environ[ENV_REMOTE_API_KEY] = "remote-key"

        local = get_settings(connection="local", load_local_env=False)
        remote = get_settings(connection="remote", load_local_env=False)

        self.assertEqual(local.api_base, "http://local.test/v1")
        self.assertEqual(local.api_key, "local-key")
        self.assertEqual(remote.api_base, "http://remote.test/v1")
        self.assertEqual(remote.api_key, "remote-key")

    def test_build_generator_uses_connection_specific_settings(self):
        os.environ[ENV_LOCAL_API_BASE] = "http://local.test/v1"
        os.environ[ENV_LOCAL_API_KEY] = "local-key"
        os.environ[ENV_REMOTE_API_BASE] = "http://remote.test/v1"
        os.environ[ENV_REMOTE_API_KEY] = "remote-key"

        local_generator = build_generator(
            ModelRuntimeConfig(
                provider="openai_compatible",
                model_name="local-model",
                connection="local",
            )
        )
        remote_generator = build_generator(
            ModelRuntimeConfig(
                provider="openai_compatible",
                model_name="remote-model",
                connection="remote",
            )
        )

        self.assertEqual(local_generator.api_base, "http://local.test/v1")
        self.assertEqual(local_generator.api_key, "local-key")
        self.assertEqual(local_generator.config["connection"], "local")
        self.assertEqual(remote_generator.api_base, "http://remote.test/v1")
        self.assertEqual(remote_generator.api_key, "remote-key")
        self.assertEqual(remote_generator.config["connection"], "remote")


class _RouteHarness(VideoParsingMixin):
    pass


class CanonicalHighEfficiencyRouteDecisionTest(unittest.TestCase):
    def test_text_route_is_used_when_profile_is_text_and_subtitles_are_available(self):
        harness = _RouteHarness()
        execution_plan = type(
            "Plan",
            (),
            {
                "segmentation_specification": type(
                    "SegSpec",
                    (),
                    {"profile": type("Profile", (), {"segmentation_route": "text_llm"})()},
                )()
            },
        )()

        route = harness._resolve_segmentation_route(execution_plan, subtitle_items=[{"text": "hello"}])

        self.assertEqual(route, "text_llm")

    def test_text_route_falls_back_to_multimodal_when_subtitles_are_missing(self):
        harness = _RouteHarness()
        execution_plan = type(
            "Plan",
            (),
            {
                "segmentation_specification": type(
                    "SegSpec",
                    (),
                    {"profile": type("Profile", (), {"segmentation_route": "text_llm"})()},
                )()
            },
        )()

        route = harness._resolve_segmentation_route(execution_plan, subtitle_items=[])

        self.assertEqual(route, "multimodal_local")

    def test_visual_profile_always_uses_multimodal_route(self):
        harness = _RouteHarness()
        execution_plan = type(
            "Plan",
            (),
            {
                "segmentation_specification": type(
                    "SegSpec",
                    (),
                    {"profile": type("Profile", (), {"segmentation_route": "multimodal_local"})()},
                )()
            },
        )()

        route = harness._resolve_segmentation_route(execution_plan, subtitle_items=[{"text": "hello"}])

        self.assertEqual(route, "multimodal_local")


class CanonicalHighEfficiencyWorkflowInitTest(unittest.TestCase):
    def test_workflow_accepts_dual_segmentors_and_route_chunk_settings(self):
        workflow = CanonicalAtlasWorkflow(
            planner=object(),
            text_segmentor=object(),
            multimodal_segmentor=object(),
            captioner=object(),
            text_chunk_size_sec=1800,
            text_chunk_overlap_sec=120,
            multimodal_chunk_size_sec=600,
            multimodal_chunk_overlap_sec=20,
        )

        self.assertEqual(workflow.text_chunk_size_sec, 1800)
        self.assertEqual(workflow.text_chunk_overlap_sec, 120)
        self.assertEqual(workflow.multimodal_chunk_size_sec, 600)
        self.assertEqual(workflow.multimodal_chunk_overlap_sec, 20)


class _RoutePathHarness(VideoParsingMixin):
    def __init__(self):
        self.text_segmentor = type("TextSegmentor", (), {"generate_single": lambda *args, **kwargs: {"text": "[]"}})()
        self.multimodal_segmentor = type("MultimodalSegmentor", (), {"generate_single": lambda *args, **kwargs: {"text": "[]"}})()
        self.prepared_messages = []

    def _build_video_messages_from_path(self, **kwargs):
        self.prepared_messages.append(("video", kwargs))
        return [{"role": "user", "content": "video"}]

    def _prepare_messages(self, system_prompt: str, user_prompt: str):
        self.prepared_messages.append(("text", {"system_prompt": system_prompt, "user_prompt": user_prompt}))
        return [{"role": "user", "content": user_prompt}]

    def parse_response(self, generated_text: str):
        return []


class CanonicalHighEfficiencyRouteExecutionTest(unittest.TestCase):
    def _make_execution_plan(self, route: str):
        return type(
            "Plan",
            (),
            {
                "concise_description": "desc",
                "segmentation_specification": type(
                    "SegSpec",
                    (),
                    {
                        "profile_name": "profile",
                        "profile": type("Profile", (), {"segmentation_route": route, "segmentation_policy": "policy"})(),
                        "frame_sampling_profile": object(),
                    },
                )(),
            },
        )()

    def test_text_route_uses_text_prompt_and_text_segmentor(self):
        harness = _RoutePathHarness()

        harness._detect_candidate_boundaries_for_chunk_text(
            subtitle_items=[{"text": "hello", "start": 0.0, "end": 10.0}],
            execution_plan=self._make_execution_plan("text_llm"),
            core_start_time=0.0,
            core_end_time=30.0,
            window_start_time=0.0,
            window_end_time=30.0,
        )

        self.assertEqual(harness.prepared_messages[0][0], "text")

    def test_multimodal_route_uses_video_messages_and_multimodal_segmentor(self):
        harness = _RoutePathHarness()

        harness._detect_candidate_boundaries_for_chunk_multimodal(
            video_path="video.mp4",
            subtitle_items=[{"text": "hello", "start": 0.0, "end": 10.0}],
            execution_plan=self._make_execution_plan("multimodal_local"),
            core_start_time=0.0,
            core_end_time=30.0,
            window_start_time=0.0,
            window_end_time=30.0,
        )

        self.assertEqual(harness.prepared_messages[0][0], "video")


if __name__ == "__main__":
    unittest.main()
