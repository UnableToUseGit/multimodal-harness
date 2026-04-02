from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from video_atlas.review import load_review_workspace


class ReviewWorkspaceLoaderTest(unittest.TestCase):
    def test_loads_canonical_workspace_segment_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Canonical\n", encoding="utf-8")
            input_dir = root / "input"
            input_dir.mkdir()
            (input_dir / "SOURCE_INFO.json").write_text(
                json.dumps(
                    {
                        "source_type": "youtube",
                        "source_url": "https://www.youtube.com/watch?v=abc123",
                    }
                ),
                encoding="utf-8",
            )
            (input_dir / "SOURCE_METADATA.json").write_text(
                json.dumps(
                    {
                        "title": "Canonical Title",
                        "channel": "Example Channel",
                    }
                ),
                encoding="utf-8",
            )
            (root / "video.mp4").write_bytes(b"mp4")
            (root / "SUBTITLES.md").write_text("full subtitles", encoding="utf-8")
            unit_dir = root / "units" / "unit0001-opening"
            unit_dir.mkdir(parents=True)
            (unit_dir / "README.md").write_text(
                "\n".join(
                    [
                        "# Unit Context",
                        "",
                        "**UnitID**: unit0001",
                        "**Start Time**: 1.0",
                        "**End Time**: 3.5",
                        "**Duration**: 2.5",
                        "**Title**: Opening Unit",
                        "**Summary**: A quick setup.",
                        "**Detail Description**: Unit caption.",
                    ]
                ),
                encoding="utf-8",
            )
            (unit_dir / "SUBTITLES.md").write_text("unit subtitles", encoding="utf-8")
            (unit_dir / "video_clip.mp4").write_bytes(b"clip")
            segment_dir = root / "segments" / "seg0001-opening"
            segment_dir.mkdir(parents=True)
            (segment_dir / "README.md").write_text(
                "\n".join(
                    [
                        "# Segment Context",
                        "",
                        "**SegID**: seg0001",
                        "**Start Time**: 1.0",
                        "**End Time**: 3.5",
                        "**Duration**: 2.5",
                        "**Title**: Opening",
                        "**Summary**: A quick setup.",
                        "**Composition Rationale**: One coherent opening block.",
                    ]
                ),
                encoding="utf-8",
            )
            copied_unit_dir = segment_dir / "unit0001-opening"
            copied_unit_dir.mkdir(parents=True)
            (copied_unit_dir / "README.md").write_text((unit_dir / "README.md").read_text(encoding="utf-8"), encoding="utf-8")
            (copied_unit_dir / "SUBTITLES.md").write_text("unit subtitles", encoding="utf-8")
            (copied_unit_dir / "video_clip.mp4").write_bytes(b"clip")

            workspace = load_review_workspace(root, workspace_id="canonical")

        self.assertEqual(workspace.kind, "canonical")
        self.assertEqual(workspace.source_info["source_type"], "youtube")
        self.assertEqual(workspace.source_metadata["title"], "Canonical Title")
        self.assertEqual(len(workspace.units), 1)
        self.assertEqual(workspace.units[0].unit_id, "unit0001")
        self.assertEqual(workspace.segments[0].segment_id, "seg0001")
        self.assertEqual(workspace.segments[0].title, "Opening")
        self.assertEqual(workspace.segments[0].summary, "A quick setup.")
        self.assertEqual(workspace.segments[0].detail, "")
        self.assertEqual(len(workspace.segments[0].units), 1)
        self.assertEqual(workspace.segments[0].units[0].unit_id, "unit0001")
        self.assertEqual(workspace.segments[0].clip_relative_path, "segments/seg0001-opening/unit0001-opening/video_clip.mp4")

    def test_loads_human_readable_min_sec_times(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Canonical\n", encoding="utf-8")
            segment_dir = root / "segments" / "seg0003-example"
            segment_dir.mkdir(parents=True)
            (segment_dir / "README.md").write_text(
                "\n".join(
                    [
                        "# Segment Context",
                        "",
                        "**SegID**: seg0003",
                        "**Start Time**: 2min 29s",
                        "**End Time**: 3min 32s",
                        "**Duration**: 1min 3s",
                        "**Title**: Example",
                        "**Summary**: Summary.",
                        "**Detail Description**: Detail.",
                    ]
                ),
                encoding="utf-8",
            )

            workspace = load_review_workspace(root, workspace_id="canonical")

        self.assertEqual(workspace.segments[0].start_time, 149.0)
        self.assertEqual(workspace.segments[0].end_time, 212.0)
        self.assertEqual(workspace.segments[0].duration, 63.0)

    def test_loads_iso_hms_times(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Canonical\n", encoding="utf-8")
            segment_dir = root / "segments" / "seg0004-example"
            segment_dir.mkdir(parents=True)
            (segment_dir / "README.md").write_text(
                "\n".join(
                    [
                        "# Segment Context",
                        "",
                        "**SegID**: seg0004",
                        "**Start Time**: 00:02:29",
                        "**End Time**: 00:03:32",
                        "**Duration**: 00:01:03",
                        "**Title**: Example",
                        "**Summary**: Summary.",
                        "**Detail Description**: Detail.",
                    ]
                ),
                encoding="utf-8",
            )

            workspace = load_review_workspace(root, workspace_id="canonical")

        self.assertEqual(workspace.segments[0].start_time, 149.0)
        self.assertEqual(workspace.segments[0].end_time, 212.0)
        self.assertEqual(workspace.segments[0].duration, 63.0)

    def test_loads_derived_workspace_source_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Derived\n", encoding="utf-8")
            (root / "TASK.md").write_text("task details", encoding="utf-8")
            (root / "derivation.json").write_text(
                json.dumps({"task_request": "Highlights", "derived_segment_count": 1}),
                encoding="utf-8",
            )
            segment_dir = root / "segments" / "derived-seg-0001-highlight"
            segment_dir.mkdir(parents=True)
            (segment_dir / "README.md").write_text(
                "\n".join(
                    [
                        "# Derived Segment",
                        "",
                        "**DerivedSegID**: derived_seg_0001",
                        "**SourceSegID**: seg_0004",
                        "**Start Time**: 10.0",
                        "**End Time**: 22.0",
                        "**Duration**: 12.0",
                        "**Title**: Key moment",
                        "**Summary**: The important event.",
                        "**Detail Description**: Source detail.",
                        "**Intent**: Show the highlight moment.",
                    ]
                ),
                encoding="utf-8",
            )
            (segment_dir / "SOURCE_MAP.json").write_text(
                json.dumps({"source_segment_id": "seg_0004"}),
                encoding="utf-8",
            )

            workspace = load_review_workspace(root, workspace_id="task")

        self.assertEqual(workspace.kind, "task")
        self.assertEqual(workspace.derivation, {"task_request": "Highlights", "derived_segment_count": 1})
        self.assertEqual(workspace.segments[0].segment_id, "derived_seg_0001")
        self.assertEqual(workspace.segments[0].detail, "Source detail.")
        self.assertEqual(workspace.segments[0].source_map, {"source_segment_id": "seg_0004"})


if __name__ == "__main__":
    unittest.main()
