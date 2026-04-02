import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

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

    def test_choose_subtitle_candidate_returns_none_for_empty_input(self) -> None:
        self.assertIsNone(choose_subtitle_candidate([]))

    @patch("video_atlas.source_acquisition.youtube.yt_dlp.YoutubeDL")
    def test_acquire_downloads_video_and_subtitles_for_short_video(self, mock_youtube_dl: MagicMock) -> None:
        metadata_context = MagicMock()
        metadata_context.extract_info.return_value = {
            "id": "abc123xyz89",
            "title": "Sample video",
            "duration": 600,
            "upload_date": "20240401",
            "thumbnails": [{"url": "https://image.example/thumb.jpg"}],
        }
        metadata_context.sanitize_info.return_value = metadata_context.extract_info.return_value

        download_context = MagicMock()
        download_context.extract_info.return_value = {
            "id": "abc123xyz89",
            "filepath": "/tmp/downloads/abc123xyz89.mp4",
            "requested_subtitles": {
                "en": {
                    "filepath": "/tmp/downloads/abc123xyz89.en.vtt",
                    "ext": "vtt",
                }
            },
        }
        download_context.sanitize_info.return_value = download_context.extract_info.return_value

        mock_youtube_dl.side_effect = [
            MagicMock(__enter__=MagicMock(return_value=metadata_context), __exit__=MagicMock(return_value=False)),
            MagicMock(__enter__=MagicMock(return_value=download_context), __exit__=MagicMock(return_value=False)),
        ]

        with TemporaryDirectory() as tmpdir:
            result = YouTubeVideoAcquirer(max_video_duration_sec=1500).acquire(
                "https://www.youtube.com/watch?v=abc123xyz89",
                Path(tmpdir),
            )

        self.assertEqual(mock_youtube_dl.call_args_list[0].args[0], {"skip_download": True})
        self.assertEqual(
            mock_youtube_dl.call_args_list[1].args[0],
            {
                "skip_download": False,
                "outtmpl": "%(id)s.%(ext)s",
                "paths": {"home": str(Path(tmpdir))},
                "writesubtitles": True,
                "writeautomaticsub": True,
            },
        )
        self.assertEqual(result.video_path, Path("/tmp/downloads/abc123xyz89.mp4"))
        self.assertEqual(result.subtitles_path, Path("/tmp/downloads/abc123xyz89.en.vtt"))
        self.assertEqual(result.source_info.subtitle_source, "youtube_caption")
        self.assertEqual(result.source_metadata.duration_seconds, 600)

    @patch("video_atlas.source_acquisition.youtube.yt_dlp.YoutubeDL")
    def test_acquire_passes_cookie_options_to_metadata_and_download(self, mock_youtube_dl: MagicMock) -> None:
        metadata_context = MagicMock()
        metadata_context.extract_info.return_value = {
            "id": "abc123xyz89",
            "title": "Sample video",
            "duration": 600,
        }
        metadata_context.sanitize_info.return_value = metadata_context.extract_info.return_value

        download_context = MagicMock()
        download_context.extract_info.return_value = {"id": "abc123xyz89", "filepath": "/tmp/downloads/abc123xyz89.mp4"}
        download_context.sanitize_info.return_value = download_context.extract_info.return_value

        mock_youtube_dl.side_effect = [
            MagicMock(__enter__=MagicMock(return_value=metadata_context), __exit__=MagicMock(return_value=False)),
            MagicMock(__enter__=MagicMock(return_value=download_context), __exit__=MagicMock(return_value=False)),
        ]

        with TemporaryDirectory() as tmpdir:
            YouTubeVideoAcquirer(
                max_video_duration_sec=1500,
                cookies_file="/tmp/cookies.txt",
                cookies_from_browser="chrome",
            ).acquire(
                "https://www.youtube.com/watch?v=abc123xyz89",
                Path(tmpdir),
            )

        self.assertEqual(
            mock_youtube_dl.call_args_list[0].args[0],
            {
                "skip_download": True,
                "cookiefile": "/tmp/cookies.txt",
                "cookiesfrombrowser": "chrome",
            },
        )
        self.assertEqual(mock_youtube_dl.call_args_list[1].args[0]["cookiefile"], "/tmp/cookies.txt")
        self.assertEqual(mock_youtube_dl.call_args_list[1].args[0]["cookiesfrombrowser"], "chrome")

    @patch("video_atlas.source_acquisition.youtube.yt_dlp.YoutubeDL")
    def test_acquire_skips_video_download_for_long_video(self, mock_youtube_dl: MagicMock) -> None:
        metadata_context = MagicMock()
        metadata_context.extract_info.return_value = {
            "id": "abc123xyz89",
            "title": "Long video",
            "duration": 2000,
            "upload_date": "20240401",
        }
        metadata_context.sanitize_info.return_value = metadata_context.extract_info.return_value

        download_context = MagicMock()
        download_context.extract_info.return_value = {
            "id": "abc123xyz89",
            "requested_subtitles": {
                "en": {
                    "filepath": "/tmp/downloads/abc123xyz89.en.vtt",
                    "ext": "vtt",
                }
            },
        }
        download_context.sanitize_info.return_value = download_context.extract_info.return_value

        mock_youtube_dl.side_effect = [
            MagicMock(__enter__=MagicMock(return_value=metadata_context), __exit__=MagicMock(return_value=False)),
            MagicMock(__enter__=MagicMock(return_value=download_context), __exit__=MagicMock(return_value=False)),
        ]

        with TemporaryDirectory() as tmpdir:
            result = YouTubeVideoAcquirer(max_video_duration_sec=1500).acquire(
                "https://www.youtube.com/watch?v=abc123xyz89",
                Path(tmpdir),
            )

        self.assertEqual(mock_youtube_dl.call_args_list[1].args[0]["skip_download"], True)
        self.assertIsNone(result.video_path)
        self.assertEqual(result.subtitles_path, Path("/tmp/downloads/abc123xyz89.en.vtt"))
        self.assertEqual(result.source_metadata.duration_seconds, 2000)


if __name__ == "__main__":
    unittest.main()
