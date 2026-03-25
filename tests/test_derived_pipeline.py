from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from video_atlas.schemas import AtlasSegment, CanonicalAtlas, CanonicalExecutionPlan
from video_atlas.workflows.derived_atlas_workflow import DerivedAtlasWorkflow


class _QueueGenerator:
    def __init__(self, responses):
        self._responses = list(responses)

    def generate_single(self, prompt=None, messages=None, schema=None, extra_body=None):
        if not self._responses:
            raise AssertionError("No queued generator response left")
        payload = self._responses.pop(0)
        return {
            "text": json.dumps(payload, ensure_ascii=False),
            "json": payload,
            "response": {"usage": {"total_tokens": 1}},
        }


class _TestDerivedAtlasWorkflow(DerivedAtlasWorkflow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.video_message_calls = []

    def _build_video_messages_from_path(
        self,
        system_prompt: str,
        user_prompt: str,
        video_path: Path | str,
        start_time: float,
        end_time: float,
    ):
        self.video_message_calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "video_path": str(video_path),
                "start_time": start_time,
                "end_time": end_time,
            }
        )
        return [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"video-range:{start_time:.1f}-{end_time:.1f}"},
                    {"type": "text", "text": user_prompt},
                ],
            },
        ]


class DerivedPipelineTest(unittest.TestCase):
    def test_workflow_derives_workspace_and_metadata(self) -> None:
        canonical = CanonicalAtlas(
            title="Canonical Title",
            duration=60.0,
            abstract="Canonical abstract",
            segments=[
                AtlasSegment(
                    segment_id="seg_0001",
                    title="Opening",
                    start_time=0.0,
                    end_time=30.0,
                    summary="Opening summary",
                    caption="Opening detail",
                    subtitles_text="\n".join(
                        [
                            "Start Time: 4.0 --> End Time: 4.8 Subtitle: before",
                            "",
                            "Start Time: 6.0 --> End Time: 7.0 Subtitle: keep this",
                            "",
                            "Start Time: 14.0 --> End Time: 14.8 Subtitle: keep that",
                            "",
                            "Start Time: 16.0 --> End Time: 17.0 Subtitle: after",
                        ]
                    ),
                    folder_name="seg0001-opening-0.00-30.00s",
                ),
                AtlasSegment(
                    segment_id="seg_0002",
                    title="Middle",
                    start_time=30.0,
                    end_time=60.0,
                    summary="Middle summary",
                    caption="Middle detail",
                    subtitles_text="",
                    folder_name="seg0002-middle-30.00-60.00s",
                ),
            ],
            execution_plan=CanonicalExecutionPlan(),
            atlas_dir=Path("/tmp/canonical"),
            relative_video_path=Path("video.mp4"),
        )

        planner = _QueueGenerator(
            [
                {
                    "candidates": [
                        {
                            "segment_id": "seg_0001",
                            "intent": "Find the opening setup relevant to the task",
                            "grounding_instruction": "Focus on the first important action within the segment",
                        }
                    ]
                }
            ]
        )
        segmentor = _QueueGenerator(
            [
                {
                    "start_time": 5.0,
                    "end_time": 15.0,
                }
            ]
        )
        captioner = _QueueGenerator(
            [
                {
                    "title": "Opening Setup",
                    "summary": "The setup sequence needed for the task.",
                    "caption": "A tighter clip showing the key setup action.",
                }
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workflow = _TestDerivedAtlasWorkflow(
                planner=planner,
                segmentor=segmentor,
                captioner=captioner,
                num_workers=2,
            )

            def fake_extract_clip(workspace_root, video_path, seg_start_time, seg_end_time, relative_output_path):
                target = Path(workspace_root) / Path(relative_output_path)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(f"{seg_start_time:.1f}-{seg_end_time:.1f}".encode("utf-8"))

            with patch("video_atlas.persistence.writers.extract_clip", side_effect=fake_extract_clip):
                result = workflow.create(
                    task_request="Find the opening setup needed for my edit",
                    canonical_atlas=canonical,
                    output_dir=Path(tmpdir),
                )

            root = Path(tmpdir)
            self.assertTrue(result.success)
            self.assertEqual(result.derived_segment_count, 1)
            self.assertTrue((root / "README.md").exists())
            self.assertTrue((root / "derivation.json").exists())
            self.assertTrue((root / ".agentignore" / "DERIVATION_RESULT.json").exists())

            derivation = json.loads((root / "derivation.json").read_text(encoding="utf-8"))
            self.assertEqual(derivation["task_request"], "Find the opening setup needed for my edit")
            self.assertEqual(derivation["derived_segment_count"], 1)
            self.assertIn("average duration", derivation["global_summary"].lower())

            segment_dirs = list((root / "segments").iterdir())
            self.assertEqual(len(segment_dirs), 1)
            segment_dir = segment_dirs[0]
            readme = (segment_dir / "README.md").read_text(encoding="utf-8")
            subtitles = (segment_dir / "SUBTITLES.md").read_text(encoding="utf-8")
            clip_text = (segment_dir / "video_clip.mp4").read_bytes().decode("utf-8")
            result_info = json.loads((root / ".agentignore" / "DERIVATION_RESULT.json").read_text(encoding="utf-8"))

        self.assertIn("**DerivedSegID**: derived_seg_0001", readme)
        self.assertIn("**SourceSegID**: seg_0001", readme)
        self.assertIn("**Intent**: Find the opening setup relevant to the task", readme)
        self.assertIn("Opening Setup", readme)
        self.assertIn("keep this", subtitles)
        self.assertIn("keep that", subtitles)
        self.assertNotIn("before", subtitles)
        self.assertNotIn("after", subtitles)
        self.assertEqual(clip_text, "5.0-15.0")
        self.assertEqual(result_info["derived_atlas_segment_count"], 1)
        self.assertEqual(result_info["derivation_source"]["derived_seg_0001"], "seg_0001")
        self.assertEqual(len(workflow.video_message_calls), 2)
        self.assertEqual(workflow.video_message_calls[0]["video_path"], "/tmp/canonical/video.mp4")
        self.assertEqual(workflow.video_message_calls[0]["start_time"], 0.0)
        self.assertEqual(workflow.video_message_calls[0]["end_time"], 30.0)
        self.assertIn("keep this", workflow.video_message_calls[0]["user_prompt"])
        self.assertEqual(workflow.video_message_calls[1]["start_time"], 5.0)
        self.assertEqual(workflow.video_message_calls[1]["end_time"], 15.0)


if __name__ == "__main__":
    unittest.main()
