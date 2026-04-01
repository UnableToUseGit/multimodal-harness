import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from video_atlas.source_acquisition.youtube import (
    YouTubeVideoAcquirer,
    choose_subtitle_candidate,
    is_supported_youtube_watch_url,
)


class YouTubeAcquisitionTest(unittest.TestCase):
    def test_is_supported_youtube_watch_url_rejects_short_playlist_and_invalid_urls(self) -> None:
        self.assertTrue(is_supported_youtube_watch_url("https://www.youtube.com/watch?v=abc123xyz89"))
        self.assertFalse(is_supported_youtube_watch_url("https://youtu.be/abc123xyz89"))
        self.assertFalse(is_supported_youtube_watch_url("https://www.youtube.com/playlist?list=demo"))
        self.assertFalse(is_supported_youtube_watch_url("https://www.youtube.com/watch?v=abc123xyz89&list=demo"))
        self.assertFalse(is_supported_youtube_watch_url("ftp://www.youtube.com/watch?v=abc123xyz89"))
        self.assertFalse(is_supported_youtube_watch_url("https://www.youtube.com/shorts/abc123xyz89"))
        self.assertFalse(is_supported_youtube_watch_url("https://m.youtube.com/watch?v=abc123xyz89"))

    def test_choose_subtitle_candidate_prefers_manual_subtitles(self) -> None:
        candidates = [
            {"kind": "automatic", "language": "en", "ext": "vtt"},
            {"kind": "manual", "language": "en", "ext": "vtt"},
        ]

        selected = choose_subtitle_candidate(candidates)

        self.assertIsNotNone(selected)
        self.assertEqual(selected["kind"], "manual")

    def test_choose_subtitle_candidate_falls_back_to_automatic_when_manual_is_missing(self) -> None:
        candidates = [{"kind": "automatic", "language": "en", "ext": "vtt"}]

        selected = choose_subtitle_candidate(candidates)

        self.assertIsNotNone(selected)
        self.assertEqual(selected["kind"], "automatic")

    def test_choose_subtitle_candidate_falls_back_to_first_unknown_candidate(self) -> None:
        candidates = [{"kind": "unknown", "language": "en", "ext": "vtt"}]

        selected = choose_subtitle_candidate(candidates)

        self.assertIsNotNone(selected)
        self.assertEqual(selected["kind"], "unknown")

    def test_choose_subtitle_candidate_returns_none_for_empty_input(self) -> None:
        self.assertIsNone(choose_subtitle_candidate([]))

    @patch("video_atlas.source_acquisition.youtube.yt_dlp.YoutubeDL")
    def test_acquire_uses_downloaded_subtitles_when_available(self, mock_youtube_dl: object) -> None:
        mock_context = mock_youtube_dl.return_value.__enter__.return_value
        raw_info = {
            "id": "abc123xyz89",
            "title": "Sample video",
            "webpage_url": "https://www.youtube.com/watch?v=abc123xyz89",
            "filepath": "/tmp/downloads/abc123xyz89.mp4",
            "requested_subtitles": {
                "en": {
                    "filepath": "/tmp/downloads/abc123xyz89.en.vtt",
                    "ext": "vtt",
                }
            },
        }
        mock_context.extract_info.return_value = raw_info
        mock_context.sanitize_info.return_value = {
            "id": "abc123xyz89",
            "title": "Sample video",
            "webpage_url": "https://www.youtube.com/watch?v=abc123xyz89",
        }

        with TemporaryDirectory() as tmpdir:
            result = YouTubeVideoAcquirer().acquire(
                "https://www.youtube.com/watch?v=abc123xyz89",
                Path(tmpdir),
            )
            mock_youtube_dl.assert_called_once_with(
                {
                    "outtmpl": "%(id)s.%(ext)s",
                    "paths": {"home": str(Path(tmpdir))},
                    "writesubtitles": True,
                    "writeautomaticsub": True,
                }
            )

        self.assertEqual(result.local_video_path, Path("/tmp/downloads/abc123xyz89.mp4"))
        self.assertEqual(result.local_subtitles_path, Path("/tmp/downloads/abc123xyz89.en.vtt"))
        self.assertEqual(result.source_info.subtitle_source, "youtube_caption")
        self.assertFalse(result.source_info.subtitle_fallback_required)
        self.assertEqual(result.source_metadata["title"], "Sample video")

    @patch("video_atlas.source_acquisition.youtube.yt_dlp.YoutubeDL")
    def test_acquire_requests_transcriber_fallback_when_no_subtitles_exist(self, mock_youtube_dl: object) -> None:
        mock_context = mock_youtube_dl.return_value.__enter__.return_value
        raw_info = {
            "id": "abc123xyz89",
            "title": "Sample video",
            "webpage_url": "https://www.youtube.com/watch?v=abc123xyz89",
            "filepath": "/tmp/downloads/abc123xyz89.mp4",
            "requested_subtitles": {},
        }
        mock_context.extract_info.return_value = raw_info
        mock_context.sanitize_info.return_value = {
            "id": "abc123xyz89",
            "title": "Sample video",
            "webpage_url": "https://www.youtube.com/watch?v=abc123xyz89",
        }

        with TemporaryDirectory() as tmpdir:
            result = YouTubeVideoAcquirer().acquire(
                "https://www.youtube.com/watch?v=abc123xyz89",
                Path(tmpdir),
            )

        self.assertEqual(result.local_video_path, Path("/tmp/downloads/abc123xyz89.mp4"))
        self.assertIsNone(result.local_subtitles_path)
        self.assertEqual(result.source_info.subtitle_source, "missing")
        self.assertTrue(result.source_info.subtitle_fallback_required)
        self.assertEqual(result.source_metadata["title"], "Sample video")


if __name__ == "__main__":
    unittest.main()
