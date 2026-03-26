from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from video_atlas.workflows.derived_atlas.loader import load_canonical_workspace


class CanonicalWorkspaceLoaderTest(unittest.TestCase):
    def test_load_canonical_workspace_reconstructs_segments_and_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Canonical\n", encoding="utf-8")
            (root / "video.mp4").write_bytes(b"mp4")
            (root / "subtitles.srt").write_text("1\n00:00:00,000 --> 00:00:02,000\nhello\n", encoding="utf-8")

            segment_dir = root / "segments" / "seg0001-opening-0.00-10.00s"
            segment_dir.mkdir(parents=True)
            (segment_dir / "README.md").write_text(
                "\n".join(
                    [
                        "# Segment Context",
                        "",
                        "**SegID**: seg_0001",
                        "**Start Time**: 0.0",
                        "**End Time**: 10.0",
                        "**Duration**: 10.0",
                        "**Title**: Opening",
                        "**Summary**: Setup summary.",
                        "**Detail Description**: Setup detail.",
                    ]
                ),
                encoding="utf-8",
            )
            (segment_dir / "SUBTITLES.md").write_text("segment subtitles", encoding="utf-8")
            (segment_dir / "video_clip.mp4").write_bytes(b"clip")

            atlas = load_canonical_workspace(root)

        self.assertEqual(atlas.atlas_dir, root.resolve())
        self.assertEqual(atlas.relative_video_path, Path("video.mp4"))
        self.assertEqual(len(atlas.segments), 1)
        segment = atlas.segments[0]
        self.assertEqual(segment.segment_id, "seg_0001")
        self.assertEqual(segment.title, "Opening")
        self.assertEqual(segment.summary, "Setup summary.")
        self.assertEqual(segment.caption, "Setup detail.")
        self.assertEqual(segment.subtitles_text, "segment subtitles")
        self.assertEqual(segment.relative_clip_path, Path("segments") / segment_dir.name / "video_clip.mp4")
        self.assertEqual(segment.relative_subtitles_path, Path("segments") / segment_dir.name / "SUBTITLES.md")


if __name__ == "__main__":
    unittest.main()
