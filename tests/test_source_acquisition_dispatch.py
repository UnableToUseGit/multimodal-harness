from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from video_atlas.schemas import SourceAcquisitionResult, SourceInfoRecord, SourceMetadata
from video_atlas.source_acquisition import (
    InvalidSourceUrlError,
    UnsupportedSourceError,
    acquire_from_url,
    detect_source_from_url,
)


class SourceAcquisitionDispatchTest(unittest.TestCase):
    def test_detect_source_from_url_recognizes_youtube(self) -> None:
        source_type = detect_source_from_url("https://www.youtube.com/watch?v=abc123xyz89")
        self.assertEqual(source_type, "youtube")

    def test_detect_source_from_url_recognizes_xiaoyuzhou(self) -> None:
        source_type = detect_source_from_url("https://www.xiaoyuzhoufm.com/episode/1234567890abcdef12345678")
        self.assertEqual(source_type, "xiaoyuzhou")

    def test_detect_source_from_url_rejects_invalid_and_unsupported_urls(self) -> None:
        with self.assertRaises(InvalidSourceUrlError):
            detect_source_from_url("not-a-url")

        with self.assertRaises(UnsupportedSourceError):
            detect_source_from_url("https://example.com/video")

    @patch("video_atlas.source_acquisition.acquire.YouTubeVideoAcquirer")
    def test_acquire_from_url_dispatches_to_youtube_acquirer(self, mock_acquirer_cls) -> None:
        expected = SourceAcquisitionResult(
            source_info=SourceInfoRecord(
                source_type="youtube",
                source_url="https://www.youtube.com/watch?v=abc123xyz89",
            ),
            source_metadata=SourceMetadata(title="Example"),
            video_path=Path("/tmp/video.mp4"),
        )
        mock_acquirer_cls.return_value.acquire.return_value = expected

        result = acquire_from_url(
            "https://www.youtube.com/watch?v=abc123xyz89",
            "/tmp/acquisition",
            prefer_youtube_subtitles=True,
            youtube_output_template="%(id)s.%(ext)s",
        )

        self.assertEqual(result, expected)

    @patch("video_atlas.source_acquisition.acquire.XiaoyuzhouAudioAcquirer")
    def test_acquire_from_url_dispatches_to_xiaoyuzhou_acquirer(self, mock_acquirer_cls) -> None:
        expected = SourceAcquisitionResult(
            source_info=SourceInfoRecord(
                source_type="xiaoyuzhou",
                source_url="https://www.xiaoyuzhoufm.com/episode/1234567890abcdef12345678",
            ),
            source_metadata=SourceMetadata(title="Podcast"),
            audio_path=Path("/tmp/audio.m4a"),
        )
        mock_acquirer_cls.return_value.acquire.return_value = expected

        result = acquire_from_url(
            "https://www.xiaoyuzhoufm.com/episode/1234567890abcdef12345678",
            "/tmp/acquisition",
            prefer_youtube_subtitles=True,
            youtube_output_template="%(id)s.%(ext)s",
        )

        self.assertEqual(result, expected)
if __name__ == "__main__":
    unittest.main()
