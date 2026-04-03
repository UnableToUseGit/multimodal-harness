import tempfile
import unittest
from pathlib import Path

from video_atlas.utils import get_subtitle_in_segment, parse_srt


class SubtitleUtilsTest(unittest.TestCase):
    def test_parse_srt_and_extract_segment(self) -> None:
        srt_text = """1
00:00:01,000 --> 00:00:03,000
hello

2
00:00:04,000 --> 00:00:05,500
world
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            srt_path = Path(tmpdir) / "sample.srt"
            srt_path.write_text(srt_text, encoding="utf-8")
            subtitle_items, subtitle_markdown = parse_srt(str(srt_path))

        self.assertEqual(len(subtitle_items), 2)
        self.assertIn("hello", subtitle_markdown)
        segment_items, segment_markdown = get_subtitle_in_segment(subtitle_items, 0, 4)
        self.assertEqual(len(segment_items), 1)
        self.assertIn("hello", segment_markdown)

    def test_parse_srt_accepts_webvtt_content(self) -> None:
        vtt_text = """WEBVTT

00:00:01.000 --> 00:00:03.000
你好

00:00:04.000 --> 00:00:05.500 align:start position:0%
世界
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            vtt_path = Path(tmpdir) / "sample.vtt"
            vtt_path.write_text(vtt_text, encoding="utf-8")
            subtitle_items, subtitle_markdown = parse_srt(vtt_path)

        self.assertEqual(len(subtitle_items), 2)
        self.assertEqual(subtitle_items[0]["text"], "你好")
        self.assertEqual(subtitle_items[1]["text"], "世界")
        self.assertIn("你好", subtitle_markdown)
        self.assertIn("世界", subtitle_markdown)


if __name__ == "__main__":
    unittest.main()
