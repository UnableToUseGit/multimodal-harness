from __future__ import annotations

import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from video_atlas.schemas import (
    AtlasSegment,
    AtlasUnit,
    CanonicalAtlas,
    CanonicalCompositionResult,
    CanonicalExecutionPlan,
    DerivationPolicy,
    DerivationResultInfo,
    DerivedAtlas,
    SourceInfoRecord,
)


class _WriterHarness:
    def __init__(self) -> None:
        self.written: dict[str, str] = {}


class WorkspaceWritersTest(unittest.TestCase):
    def test_slugify_segment_title_preserves_unicode_letters(self) -> None:
        from video_atlas.persistence.writers import slugify_segment_title

        self.assertEqual(slugify_segment_title("Hello World"), "hello-world")
        self.assertEqual(slugify_segment_title("中文标题"), "中文标题")
        self.assertEqual(slugify_segment_title("第一章：系统设计"), "第一章-系统设计")
        self.assertEqual(slugify_segment_title("播客｜人工智能与Future"), "播客-人工智能与future")
        self.assertEqual(slugify_segment_title("!!!"), "untitled")

    def test_copy_to_copies_file_into_destination_directory(self) -> None:
        from video_atlas.persistence.writers import copy_to

        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src_file = root / "source.txt"
            src_file.write_text("hello", encoding="utf-8")
            destination = root / "dest"
            destination.mkdir()

            copied = copy_to(src_file, destination)

            self.assertEqual(copied, destination / src_file.name)
            self.assertTrue(copied.is_file())
            self.assertEqual(copied.read_text(encoding="utf-8"), "hello")

    def test_copy_to_copies_directory_into_destination_directory(self) -> None:
        from video_atlas.persistence.writers import copy_to

        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src_dir = root / "source_dir"
            src_dir.mkdir()
            (src_dir / "nested.txt").write_text("nested", encoding="utf-8")
            destination = root / "dest"
            destination.mkdir()

            copied_dir = copy_to(src_dir, destination)

            self.assertEqual(copied_dir, destination / src_dir.name)
            self.assertTrue(copied_dir.is_dir())
            self.assertEqual((copied_dir / "nested.txt").read_text(encoding="utf-8"), "nested")

    def test_canonical_workspace_writer_persists_root_and_segment_files(self) -> None:
        from video_atlas.persistence import CanonicalAtlasWriter

        harness = _WriterHarness()
        writer = CanonicalAtlasWriter(caption_with_subtitles=True)
        atlas = CanonicalAtlas(
            title="Match Overview",
            duration=20.0,
            abstract="A concise abstract.",
            units=[
                AtlasUnit(
                    unit_id="unit_0001",
                    title="Opening Unit",
                    start_time=0.0,
                    end_time=20.0,
                    summary="Opening summary",
                    caption="Opening detail",
                    subtitles_text="segment subtitles",
                    folder_name="unit0001-opening-unit-00:00:00-00:00:20",
                )
            ],
            segments=[
                AtlasSegment(
                    segment_id="seg_0001",
                    unit_ids=["unit_0001"],
                    title="Opening",
                    start_time=0.0,
                    end_time=20.0,
                    summary="Opening summary",
                    composition_rationale="The first unit already forms a complete opening chapter.",
                    folder_name="seg0001-opening-00:00:00-00:00:20",
                )
            ],
            execution_plan=CanonicalExecutionPlan(),
            atlas_dir=Path("/tmp/canonical"),
            relative_video_path=Path("video.mp4"),
            source_info=SourceInfoRecord(
                source_type="youtube",
                source_url="https://www.youtube.com/watch?v=abc123xyz89",
                subtitle_source="youtube_caption",
            ),
            source_metadata={"title": "Match Overview", "channel": "Example Channel"},
        )

        with patch("video_atlas.persistence.writers.write_text_to") as mock_write:
            with patch("video_atlas.persistence.writers.clip_exists", return_value=False):
                with patch("video_atlas.persistence.writers.extract_clip") as mock_extract:
                    writer.write(atlas=atlas)

        for call in mock_write.call_args_list:
            harness.written[str(call.args[1])] = call.args[2]
        harness.written["units/unit0001-opening-unit-00:00:00-00:00:20/video_clip.mp4"] = "clip"
        harness.written["segments/seg0001-opening-00:00:00-00:00:20/unit0001-opening-unit-00:00:00-00:00:20/video_clip.mp4"] = "clip"
        self.assertEqual(mock_extract.call_count, 2)
        mock_extract.assert_any_call(
            Path("/tmp/canonical"),
            Path("/tmp/canonical/video.mp4"),
            0.0,
            20.0,
            Path("units/unit0001-opening-unit-00:00:00-00:00:20/video_clip.mp4"),
        )
        mock_extract.assert_any_call(
            Path("/tmp/canonical"),
            Path("/tmp/canonical/video.mp4"),
            0.0,
            20.0,
            Path("segments/seg0001-opening-00:00:00-00:00:20/unit0001-opening-unit-00:00:00-00:00:20/video_clip.mp4"),
        )

        self.assertIn("README.md", harness.written)
        self.assertIn("units/unit0001-opening-unit-00:00:00-00:00:20/README.md", harness.written)
        self.assertIn("units/unit0001-opening-unit-00:00:00-00:00:20/SUBTITLES.md", harness.written)
        self.assertIn("segments/seg0001-opening-00:00:00-00:00:20/README.md", harness.written)
        self.assertIn(
            "segments/seg0001-opening-00:00:00-00:00:20/unit0001-opening-unit-00:00:00-00:00:20/README.md",
            harness.written,
        )
        self.assertIn(
            "segments/seg0001-opening-00:00:00-00:00:20/unit0001-opening-unit-00:00:00-00:00:20/SUBTITLES.md",
            harness.written,
        )
        self.assertIn("units/unit0001-opening-unit-00:00:00-00:00:20/video_clip.mp4", harness.written)
        self.assertIn(
            "segments/seg0001-opening-00:00:00-00:00:20/unit0001-opening-unit-00:00:00-00:00:20/video_clip.mp4",
            harness.written,
        )
        self.assertIn("Match Overview", harness.written["README.md"])
        self.assertIn("There are 1 units extracted from the raw video.", harness.written["README.md"])
        self.assertIn("**Start Time**: 00:00:00", harness.written["segments/seg0001-opening-00:00:00-00:00:20/README.md"])
        self.assertIn("**End Time**: 00:00:20", harness.written["segments/seg0001-opening-00:00:00-00:00:20/README.md"])
        self.assertIn("**Duration**: 00:00:20", harness.written["segments/seg0001-opening-00:00:00-00:00:20/README.md"])
        self.assertIn("**Composition Rationale**: The first unit already forms a complete opening chapter.", harness.written["segments/seg0001-opening-00:00:00-00:00:20/README.md"])

    def test_derived_workspace_writer_persists_metadata_and_segments(self) -> None:
        from video_atlas.persistence import DerivedAtlasWriter

        harness = _WriterHarness()
        writer = DerivedAtlasWriter(caption_with_subtitles=True)
        derived_atlas = DerivedAtlas(
            task_request="find the key task moment",
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
                    subtitles_text="pruned subtitles",
                    folder_name="derived-seg-0001-task-segment-00:00:05-00:00:15",
                )
            ],
            derivation_result_info=DerivationResultInfo(
                derived_atlas_segment_count=1,
                derivation_reason={
                    "derived_seg_0001": DerivationPolicy(
                        intent="Find the key task moment",
                        grounding_instruction="focus on the setup action",
                    )
                },
                derivation_source={"derived_seg_0001": "seg_0001"},
            ),
            atlas_dir=Path("/tmp/out"),
            source_canonical_atlas_dir=Path("/tmp/canonical"),
            source_video_path=Path("/tmp/canonical/video.mp4"),
        )

        with patch("video_atlas.persistence.writers.write_text_to") as mock_write:
            with patch("video_atlas.persistence.writers.extract_clip") as mock_extract:
                writer.write(derived_atlas=derived_atlas)

        for call in mock_write.call_args_list:
            harness.written[str(call.args[1])] = call.args[2]
        harness.written["segments/derived-seg-0001-task-segment-00:00:05-00:00:15/video_clip.mp4"] = "clip"
        mock_extract.assert_called_once_with(
            Path("/tmp/out"),
            Path("/tmp/canonical/video.mp4"),
            5.0,
            15.0,
            Path("segments/derived-seg-0001-task-segment-00:00:05-00:00:15/video_clip.mp4"),
        )

        self.assertIn("README.md", harness.written)
        self.assertIn("TASK.md", harness.written)
        self.assertIn("derivation.json", harness.written)
        self.assertIn(".agentignore/DERIVATION_RESULT.json", harness.written)
        self.assertIn("segments/derived-seg-0001-task-segment-00:00:05-00:00:15/README.md", harness.written)
        self.assertIn("segments/derived-seg-0001-task-segment-00:00:05-00:00:15/video_clip.mp4", harness.written)
        self.assertIn("segments/derived-seg-0001-task-segment-00:00:05-00:00:15/SUBTITLES.md", harness.written)
        self.assertIn(
            "**Start Time**: 00:00:05",
            harness.written["segments/derived-seg-0001-task-segment-00:00:05-00:00:15/README.md"],
        )
        self.assertIn(
            "**End Time**: 00:00:15",
            harness.written["segments/derived-seg-0001-task-segment-00:00:05-00:00:15/README.md"],
        )
        self.assertIn(
            "**Duration**: 00:00:10",
            harness.written["segments/derived-seg-0001-task-segment-00:00:05-00:00:15/README.md"],
        )
        derivation = json.loads(harness.written["derivation.json"])
        self.assertEqual(derivation["derived_segment_count"], 1)
        self.assertEqual(derivation["task_request"], "find the key task moment")
        source_map = json.loads(
            harness.written["segments/derived-seg-0001-task-segment-00:00:05-00:00:15/SOURCE_MAP.json"]
        )
        self.assertEqual(source_map["source_segment_id"], "seg_0001")


if __name__ == "__main__":
    unittest.main()
