import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from video_atlas.prompts import (
    BOUNDARY_DETECTION_PROMPT,
    CAPTION_GENERATION_PROMPT,
    DERIVED_CAPTION_PROMPT,
    DERIVED_CANDIDATE_PROMPT,
    DERIVED_GROUNDING_PROMPT,
    PLANNER_PROMPT,
    PROMPT_REGISTRY,
    PromptRegistry,
    PromptRenderError,
    PromptSpec,
    VIDEO_GLOBAL_PROMPT,
    get_prompt,
    list_prompts,
    prompt_names,
)
from video_atlas.prompts.specs import PromptSpec as RawPromptSpec
from video_atlas.workflows.canonical_atlas_workflow import CanonicalAtlasWorkflow


class _QueueGenerator:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def generate_single(self, prompt=None, messages=None, schema=None, extra_body=None):
        self.calls.append(messages)
        payload = self._responses.pop(0)
        return {
            "text": __import__("json").dumps(payload, ensure_ascii=False),
            "json": payload,
            "response": {"usage": {"total_tokens": 1}},
        }


class _CanonicalPromptWorkflow(CanonicalAtlasWorkflow):
    def __init__(self, planner, segmentor, captioner):
        super().__init__(planner=planner, segmentor=segmentor, captioner=captioner)
        self.video_message_calls = []

    def _build_video_messages_from_path(
        self,
        system_prompt: str,
        user_prompt: str,
        video_path: str,
        start_time: float,
        end_time: float,
        video_sampling=None,
    ):
        self.video_message_calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "video_path": video_path,
                "start_time": start_time,
                "end_time": end_time,
                "video_sampling": video_sampling,
            }
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _log_info(self, *args, **kwargs) -> None:
        return None

    def _log_warning(self, *args, **kwargs) -> None:
        return None

    def _log_error(self, *args, **kwargs) -> None:
        return None


class PromptSpecTest(unittest.TestCase):
    def test_prompt_spec_stores_metadata(self) -> None:
        spec = PromptSpec(
            name="demo",
            purpose="demo purpose",
            system_template="System {topic}",
            user_template="User {topic}",
            input_fields=("topic",),
            output_contract="json",
            metadata={"owner": "atlas", "version": 1},
            tags=("core", "demo"),
        )

        self.assertEqual(spec.name, "demo")
        self.assertEqual(spec.purpose, "demo purpose")
        self.assertEqual(spec.metadata, {"owner": "atlas", "version": 1})
        self.assertEqual(spec.tags, ("core", "demo"))

    def test_prompt_spec_render_success(self) -> None:
        spec = PromptSpec(
            name="render",
            purpose="render prompt",
            system_template="System {topic} {level}",
            user_template="User {topic} {level}",
            input_fields=("topic", "level"),
            output_contract="json",
        )

        system_text, user_text = spec.render(topic="video", level="high")

        self.assertEqual(system_text, "System video high")
        self.assertEqual(user_text, "User video high")

    def test_prompt_spec_render_system_ignores_user_only_placeholders(self) -> None:
        spec = PromptSpec(
            name="system-only",
            purpose="system rendering prompt",
            system_template="System static text",
            user_template="User {topic}",
            input_fields=("topic",),
            output_contract="json",
        )

        self.assertEqual(spec.render_system(), "System static text")
        self.assertEqual(spec.render_user(topic="video"), "User video")

    def test_prompt_spec_missing_field_failure(self) -> None:
        spec = PromptSpec(
            name="missing",
            purpose="missing field prompt",
            system_template="System {topic}",
            user_template="User {topic}",
            input_fields=("topic",),
            output_contract="json",
        )

        with self.assertRaises(PromptRenderError) as ctx:
            spec.render()

        self.assertIn("missing required fields", str(ctx.exception))

    def test_prompt_spec_nested_placeholder_failure(self) -> None:
        spec = PromptSpec(
            name="nested",
            purpose="nested placeholder prompt",
            system_template="System {user.name}",
            user_template="User {user.name}",
            input_fields=("user",),
            output_contract="json",
        )

        with self.assertRaises(PromptRenderError) as ctx:
            spec.render(user={})

        self.assertIn("could not render system template", str(ctx.exception))
        self.assertIn("'name'", str(ctx.exception))


class PromptRegistryTest(unittest.TestCase):
    def test_registry_register_get_list(self) -> None:
        registry = PromptRegistry()
        first = PromptSpec(
            name="first",
            purpose="first prompt",
            system_template="System {topic}",
            user_template="User {topic}",
            input_fields=("topic",),
            output_contract="json",
        )
        second = PromptSpec(
            name="second",
            purpose="second prompt",
            system_template="System {topic}",
            user_template="User {topic}",
            input_fields=("topic",),
            output_contract="json",
        )

        registry.register(first)
        registry.register(second)

        self.assertIs(registry.get("first"), first)
        self.assertIs(registry.get("second"), second)
        self.assertEqual([prompt.name for prompt in registry.list_prompts()], ["first", "second"])

    def test_registry_duplicate_name_failure(self) -> None:
        registry = PromptRegistry()
        spec = PromptSpec(
            name="duplicate",
            purpose="duplicate prompt",
            system_template="System {topic}",
            user_template="User {topic}",
            input_fields=("topic",),
            output_contract="json",
        )

        registry.register(spec)

        with self.assertRaises(ValueError) as ctx:
            registry.register(spec)

        self.assertIn("already registered", str(ctx.exception))


class PromptExportsTest(unittest.TestCase):
    def test_prompt_spec_mapping_access_is_intrinsic(self) -> None:
        spec = RawPromptSpec(
            name="compat",
            purpose="compatibility prompt",
            system_template="System {topic}",
            user_template="User {topic}",
            input_fields=("topic",),
            output_contract="json",
        )

        self.assertEqual(spec["SYSTEM"], "System {topic}")
        self.assertEqual(spec["USER"], "User {topic}")

    def test_exported_prompts_are_prompt_specs(self) -> None:
        for prompt in (
            PLANNER_PROMPT,
            BOUNDARY_DETECTION_PROMPT,
            CAPTION_GENERATION_PROMPT,
            VIDEO_GLOBAL_PROMPT,
            DERIVED_CANDIDATE_PROMPT,
            DERIVED_GROUNDING_PROMPT,
            DERIVED_CAPTION_PROMPT,
        ):
            with self.subTest(prompt=prompt.name):
                self.assertIsInstance(prompt, PromptSpec)

    def test_registry_lookup_entrypoints(self) -> None:
        names = prompt_names()
        self.assertEqual(tuple(name for name in names), tuple(prompt.name for prompt in list_prompts()))
        self.assertEqual(
            {
                "PLANNER_PROMPT",
                "BOUNDARY_DETECTION_PROMPT",
                "CAPTION_GENERATION_PROMPT",
                "VIDEO_GLOBAL_PROMPT",
                "DERIVED_CANDIDATE_PROMPT",
                "DERIVED_GROUNDING_PROMPT",
                "DERIVED_CAPTION_PROMPT",
            },
            set(names),
        )
        self.assertIs(get_prompt("PLANNER_PROMPT"), PLANNER_PROMPT)
        self.assertIs(PROMPT_REGISTRY.get("DERIVED_CAPTION_PROMPT"), DERIVED_CAPTION_PROMPT)

    def test_exported_prompt_specs_render(self) -> None:
        render_cases = [
            (PLANNER_PROMPT, {}),
            (
                BOUNDARY_DETECTION_PROMPT,
                {
                    "t_start": 0.0,
                    "t_end": 30.0,
                    "subtitles": "subtitles",
                    "core_start": 5.0,
                    "core_end": 25.0,
                    "concise_description": "A lecture-style explainer about a technical topic.",
                    "segmentation_profile": "profile",
                    "segmentation_policy": "policy",
                    "last_detection_point": 0.0,
                },
            ),
            (
                CAPTION_GENERATION_PROMPT,
                {
                    "genres": "lecture_talk, tutorial_howto",
                    "concise_description": "A technical explainer video that introduces a concept and then walks through examples.",
                    "segmentation_profile": "profile",
                    "signal_priority": "visual",
                    "caption_policy": "policy",
                    "subtitles": "subtitles",
                },
            ),
            (
                VIDEO_GLOBAL_PROMPT,
                {"segments_description": "segments"},
            ),
            (
                DERIVED_CANDIDATE_PROMPT,
                {"task_request": "task", "canonical_segments": "segments"},
            ),
            (
                DERIVED_GROUNDING_PROMPT,
                {
                    "segment_id": "seg-1",
                    "segment_start_time": 1.0,
                    "segment_end_time": 2.0,
                    "intent": "intent",
                    "grounding_instruction": "instruction",
                    "summary": "summary",
                    "detail": "detail",
                    "subtitles": "subtitles",
                },
            ),
            (
                DERIVED_CAPTION_PROMPT,
                {
                    "task_request": "task",
                    "segment_id": "seg-1",
                    "start_time": 1.0,
                    "end_time": 2.0,
                    "intent": "intent",
                    "grounding_instruction": "instruction",
                    "summary": "summary",
                    "detail": "detail",
                    "subtitles": "subtitles",
                },
            ),
        ]

        for prompt, kwargs in render_cases:
            with self.subTest(prompt=prompt.name):
                system_text, user_text = prompt.render(**kwargs)
                self.assertIsInstance(system_text, str)
                self.assertIsInstance(user_text, str)
                self.assertNotEqual(system_text, "")
                self.assertNotEqual(user_text, "")


class WorkflowPromptUsageTest(unittest.TestCase):
    def test_canonical_workflow_prompt_paths_do_not_require_mapping_access(self) -> None:
        workflow = _CanonicalPromptWorkflow(
            planner=_QueueGenerator([{"plan": "ok"}]),
            segmentor=_QueueGenerator(
                [
                    [
                        {
                            "timestamp": 12.0,
                            "boundary_rationale": "Topic changes here",
                            "evidence": ["other"],
                            "confidence": 0.8,
                        }
                    ]
                ]
            ),
            captioner=_QueueGenerator(
                [
                    {"summary": "Local summary", "caption": "Local detail"},
                    {
                        "title": "Atlas title",
                        "abstract": "Atlas abstract",
                        "segment_titles": [{"seg_id": "seg_0001", "title": "Segment title"}],
                    },
                ]
            ),
        )
        execution_plan = SimpleNamespace(
            genres=["lecture_talk"],
            concise_description="A lecture-style explainer with one speaker and supporting examples.",
            segmentation_specification=SimpleNamespace(
                profile_name="balanced",
                profile=SimpleNamespace(
                    signal_priority="balanced",
                    segmentation_policy="Prefer topic shifts",
                    target_segment_length_sec=(30, 120),
                ),
                frame_sampling_profile={"fps": 1},
            ),
            caption_specification=SimpleNamespace(
                frame_sampling_profile={"fps": 1},
                profile=SimpleNamespace(caption_policy="Summarize the clip faithfully"),
            ),
        )

        with patch.object(RawPromptSpec, "__getitem__", side_effect=AssertionError("dict-style prompt access is forbidden")):
            planner_output, planner_reasoning = workflow._run_plan_planner(
                prepared_probe_inputs=[],
                duration=90.0,
                subtitle_items=[{"text": "hello world"}],
            )
            candidate_boundaries = workflow._detect_candidate_boundaries_for_chunk(
                video_path="/tmp/video.mp4",
                subtitle_items=[{"start": 0.0, "end": 20.0, "text": "subtitle text"}],
                execution_plan=execution_plan,
                core_start_time=0.0,
                core_end_time=20.0,
                window_start_time=0.0,
                window_end_time=20.0,
                last_detection_point=0.0,
            )
            caption = workflow._generate_local_caption(
                video_path="/tmp/video.mp4",
                segment=SimpleNamespace(start_time=0.0, end_time=20.0),
                seg_id=1,
                subtitle_items=[{"start": 0.0, "end": 20.0, "text": "subtitle text"}],
                execution_plan=execution_plan,
            )
            atlas = workflow._assemble_canonical_atlas(
                atlas_dir=Path("/tmp/atlas"),
                duration=20.0,
                execution_plan=execution_plan,
                parsed_segments=[
                    {
                        "seg_id": "seg_0001",
                        "start_time": 0.0,
                        "end_time": 20.0,
                        "summary": caption.summary,
                        "detail": caption.detail,
                    }
                ],
                video_path=Path("/tmp/atlas/video.mp4"),
                audio_path=None,
                subtitles_path=None,
                srt_file_path=None,
                verbose=False,
            )

        self.assertEqual(planner_output, {"plan": "ok"})
        self.assertEqual(planner_reasoning, "")
        self.assertEqual(len(candidate_boundaries), 1)
        self.assertEqual(candidate_boundaries[0].timestamp, 12.0)
        self.assertEqual(caption.summary, "Local summary")
        self.assertEqual(atlas.title, "Atlas title")
        self.assertEqual(atlas.abstract, "Atlas abstract")
        self.assertEqual(atlas.segments[0].title, "Segment title")

    def test_representative_input_fields_are_declared(self) -> None:
        self.assertEqual(PLANNER_PROMPT.input_fields, ())
        self.assertEqual(
            BOUNDARY_DETECTION_PROMPT.input_fields,
            (
                "t_start",
                "t_end",
                "subtitles",
                "core_start",
                "core_end",
                "concise_description",
                "segmentation_profile",
                "segmentation_policy",
                "last_detection_point",
            ),
        )
        self.assertEqual(
            CAPTION_GENERATION_PROMPT.input_fields,
            ("genres", "concise_description", "segmentation_profile", "signal_priority", "caption_policy", "subtitles"),
        )
        self.assertEqual(
            DERIVED_CANDIDATE_PROMPT.input_fields,
            ("task_request", "canonical_segments"),
        )
        self.assertEqual(
            DERIVED_GROUNDING_PROMPT.input_fields,
            (
                "segment_id",
                "segment_start_time",
                "segment_end_time",
                "intent",
                "grounding_instruction",
                "summary",
                "detail",
                "subtitles",
            ),
        )
        self.assertEqual(
            DERIVED_CAPTION_PROMPT.input_fields,
            (
                "task_request",
                "segment_id",
                "start_time",
                "end_time",
                "intent",
                "grounding_instruction",
                "summary",
                "detail",
                "subtitles",
            ),
        )


if __name__ == "__main__":
    unittest.main()
