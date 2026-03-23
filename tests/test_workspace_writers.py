from __future__ import annotations

import json
import unittest
from pathlib import Path

from video_atlas.schemas import (
    AtlasSegment,
    CanonicalAtlas,
    DerivationPolicy,
    DerivationResultInfo,
    DerivedAtlas,
)


class _WriterHarness:
    def __init__(self) -> None:
        self.written: dict[str, str] = {}

    def write_text(self, relative_path, content: str) -> None:
        self.written[str(relative_path)] = content

    def clip_exists(self, relative_path) -> bool:
        return str(relative_path) in self.written

    def extract_clip(self, video_path: str, start_time: float, end_time: float, relative_output_path) -> None:
        self.written[str(relative_output_path)] = f"clip:{video_path}:{start_time:.1f}-{end_time:.1f}"


class WorkspaceWritersTest(unittest.TestCase):
    def test_canonical_workspace_writer_persists_root_and_segment_files(self) -> None:
        from video_atlas.persistence import CanonicalWorkspaceWriter

        harness = _WriterHarness()
        writer = CanonicalWorkspaceWriter(
            write_text=harness.write_text,
            extract_clip=harness.extract_clip,
            clip_exists=harness.clip_exists,
            caption_with_subtitles=True,
        )
        atlas = CanonicalAtlas(
            title="Match Overview",
            abstract="A concise abstract.",
            segments=[
                AtlasSegment(
                    segment_id="seg_0001",
                    title="Opening",
                    start_time=0.0,
                    end_time=20.0,
                    summary="Opening summary",
                    caption="Opening detail",
                    folder_name="seg0001-opening-0.00-20.00s",
                )
            ],
            root_path=Path("/tmp/canonical"),
        )

        writer.write(
            atlas=atlas,
            source_video_path="video.mp4",
            segment_artifacts={
                "seg_0001": {
                    "subtitles_text": "segment subtitles",
                }
            },
        )

        self.assertIn("README.md", harness.written)
        self.assertIn("segments/seg0001-opening-0.00-20.00s/README.md", harness.written)
        self.assertIn("segments/seg0001-opening-0.00-20.00s/SUBTITLES.md", harness.written)
        self.assertIn("segments/seg0001-opening-0.00-20.00s/video_clip.mp4", harness.written)
        self.assertIn("Match Overview", harness.written["README.md"])
        self.assertIn("Opening", harness.written["segments/seg0001-opening-0.00-20.00s/README.md"])

    def test_derived_workspace_writer_persists_metadata_and_segments(self) -> None:
        from video_atlas.persistence import DerivedWorkspaceWriter

        harness = _WriterHarness()
        writer = DerivedWorkspaceWriter(
            write_text=harness.write_text,
            extract_clip=harness.extract_clip,
            caption_with_subtitles=True,
        )
        derived_atlas = DerivedAtlas(
            global_summary="Derived 1 segment.",
            detailed_breakdown="- derived_seg_0001: summary",
            segments=[
                AtlasSegment(
                    segment_id="derived_seg_0001",
                    title="Task Segment",
                    start_time=5.0,
                    end_time=15.0,
                    summary="Task summary",
                    caption="Task detail",
                    folder_name="derived-seg-0001-task-segment-5.00-15.00s",
                )
            ],
            root_path=Path("/tmp/derived"),
            readme_text="# Derived Atlas",
            source_canonical_atlas_path=Path("/tmp/canonical"),
        )
        result_info = DerivationResultInfo(
            derived_atlas_segment_count=1,
            derivation_reason={
                "derived_seg_0001": DerivationPolicy(
                    intent="Find the key task moment",
                    grounding_instruction="focus on the setup action",
                )
            },
            derivation_source={"derived_seg_0001": "seg_0001"},
        )

        writer.write(
            derived_atlas=derived_atlas,
            result_info=result_info,
            task_request="find the key task moment",
            source_video_path="video.mp4",
            segment_artifacts={
                "derived_seg_0001": {
                    "subtitles_text": "pruned subtitles",
                }
            },
        )

        self.assertIn("README.md", harness.written)
        self.assertIn("TASK.md", harness.written)
        self.assertIn("derivation.json", harness.written)
        self.assertIn(".agentignore/DERIVATION_RESULT.json", harness.written)
        self.assertIn("segments/derived-seg-0001-task-segment-5.00-15.00s/README.md", harness.written)
        self.assertIn("segments/derived-seg-0001-task-segment-5.00-15.00s/video_clip.mp4", harness.written)
        self.assertIn("segments/derived-seg-0001-task-segment-5.00-15.00s/SUBTITLES.md", harness.written)
        derivation = json.loads(harness.written["derivation.json"])
        self.assertEqual(derivation["derived_segment_count"], 1)
        self.assertEqual(derivation["task_request"], "find the key task moment")
        source_map = json.loads(
            harness.written["segments/derived-seg-0001-task-segment-5.00-15.00s/SOURCE_MAP.json"]
        )
        self.assertEqual(source_map["source_segment_id"], "seg_0001")


if __name__ == "__main__":
    unittest.main()
