from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from video_atlas.agents.derived_atlas_agent import DerivedAtlasAgent
from video_atlas.schemas import AtlasSegment, CanonicalAtlas
from video_atlas.workspaces import LocalWorkspace


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

    def generate_batch(self, prompts=None, messages_list=None, schema=None, extra_body=None):
        entries = messages_list if messages_list is not None else prompts or []
        return [self.generate_single() for _ in entries]


class _TestDerivedAtlasAgent(DerivedAtlasAgent):
    def _extract_clip(self, video_path: str, seg_start_time: float, seg_end_time: float, relative_output_path):
        target = self._workspace_root() / Path(relative_output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(f"{seg_start_time:.1f}-{seg_end_time:.1f}".encode("utf-8"))


class DerivedPipelineTest(unittest.TestCase):
    def test_agent_derives_workspace_and_metadata(self) -> None:
        canonical = CanonicalAtlas(
            title="Canonical Title",
            abstract="Canonical abstract",
            root_path=Path("/tmp/canonical"),
            source_video_path=Path("/tmp/canonical/video.mp4"),
            segments=[
                AtlasSegment(
                    segment_id="seg_0001",
                    title="Opening",
                    start_time=0.0,
                    end_time=30.0,
                    summary="Opening summary",
                    caption="Opening detail",
                    folder_name="seg0001-opening-0.00-30.00s",
                    subtitles_path=Path("/tmp/canonical/segments/seg0001-opening-0.00-30.00s/SUBTITLES.md"),
                ),
                AtlasSegment(
                    segment_id="seg_0002",
                    title="Middle",
                    start_time=30.0,
                    end_time=60.0,
                    summary="Middle summary",
                    caption="Middle detail",
                    folder_name="seg0002-middle-30.00-60.00s",
                ),
            ],
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
            workspace = LocalWorkspace(root_path=tmpdir, name="derived", description="derived test workspace")
            source_subtitles = canonical.segments[0].subtitles_path
            assert source_subtitles is not None
            source_subtitles.parent.mkdir(parents=True, exist_ok=True)
            source_subtitles.write_text(
                "\n".join(
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
                encoding="utf-8",
            )
            agent = _TestDerivedAtlasAgent(
                planner=planner,
                segmentor=segmentor,
                captioner=captioner,
                workspace=workspace,
                num_workers=2,
            )

            result = agent.add(
                task_request="Find the opening setup needed for my edit",
                canonical_atlas=canonical,
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


if __name__ == "__main__":
    unittest.main()
