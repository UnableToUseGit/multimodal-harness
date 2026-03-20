import unittest

from video_atlas.schemas.workspace import VideoGlobal, VideoSeg


class WorkspaceMarkdownTest(unittest.TestCase):
    def test_segment_markdown_formats_times_as_min_sec(self):
        markdown = VideoSeg(
            seg_id="seg_0003",
            start_time=148.8,
            end_time=212.1,
            duration=63.3,
            seg_title="Test Title",
            summary="summary",
            detail="detail",
        ).to_markdown()

        self.assertIn("**Start Time**: 2min 29s", markdown)
        self.assertIn("**End Time**: 3min 32s", markdown)
        self.assertIn("**Duration**: 1min 3s", markdown)

    def test_global_markdown_formats_duration_as_min_sec(self):
        markdown = VideoGlobal(
            title="title",
            abstract="abstract",
            num_segments=3,
            segments_quickview="",
            duration=195,
        ).to_markdown()

        self.assertIn("**Duration**: 3min 15s", markdown)
        self.assertNotIn("seconds", markdown)


if __name__ == "__main__":
    unittest.main()
