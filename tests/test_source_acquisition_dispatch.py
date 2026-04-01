from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from video_atlas.schemas import SourceInfoRecord
from video_atlas.source_acquisition import (
    InvalidSourceUrlError,
    SourceAcquisitionResult,
    UnsupportedSourceError,
    acquire_from_url,
    detect_source_from_url,
    materialize_fetch_workspace,
)


class SourceAcquisitionDispatchTest(unittest.TestCase):
    def test_detect_source_from_url_recognizes_youtube(self) -> None:
        source_type = detect_source_from_url("https://www.youtube.com/watch?v=abc123xyz89")
        self.assertEqual(source_type, "youtube")

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
                canonical_source_url="https://www.youtube.com/watch?v=abc123xyz89",
            ),
            local_video_path=Path("/tmp/video.mp4"),
        )
        mock_acquirer_cls.return_value.acquire.return_value = expected

        result = acquire_from_url(
            "https://www.youtube.com/watch?v=abc123xyz89",
            "/tmp/acquisition",
            prefer_youtube_subtitles=True,
            youtube_output_template="%(id)s.%(ext)s",
        )

        self.assertEqual(result, expected)

    def test_materialize_fetch_workspace_writes_normalized_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            downloaded_video = root / "downloaded.mp4"
            downloaded_video.write_bytes(b"video")
            downloaded_subtitles = root / "downloaded.srt"
            downloaded_subtitles.write_text("subtitle", encoding="utf-8")

            result = SourceAcquisitionResult(
                source_info=SourceInfoRecord(
                    source_type="youtube",
                    source_url="https://www.youtube.com/watch?v=abc123xyz89",
                    canonical_source_url="https://www.youtube.com/watch?v=abc123xyz89",
                    subtitle_source="youtube_caption",
                    subtitle_fallback_required=False,
                ),
                local_video_path=downloaded_video,
                local_subtitles_path=downloaded_subtitles,
                source_metadata={"title": "Example"},
            )

            output_dir = root / "fetch-output"
            fetch_workspace = materialize_fetch_workspace(result, output_dir)

            self.assertEqual(fetch_workspace.parent, output_dir)
            self.assertNotEqual(fetch_workspace.name, "")
            self.assertTrue((fetch_workspace / "video.mp4").exists())
            self.assertTrue((fetch_workspace / "subtitles.srt").exists())
            self.assertEqual(
                json.loads((fetch_workspace / "SOURCE_INFO.json").read_text(encoding="utf-8"))["source_type"],
                "youtube",
            )
            self.assertEqual(
                json.loads((fetch_workspace / "SOURCE_METADATA.json").read_text(encoding="utf-8"))["title"],
                "Example",
            )


if __name__ == "__main__":
    unittest.main()
