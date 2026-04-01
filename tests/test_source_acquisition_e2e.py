from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from video_atlas.source_acquisition.youtube import YouTubeVideoAcquirer


class SourceAcquisitionE2ETest(unittest.TestCase):
    def test_can_acquire_real_youtube_video_when_enabled(self) -> None:
        youtube_url = os.environ.get("VIDEO_ATLAS_E2E_YOUTUBE_URL")
        if not youtube_url:
            self.skipTest("VIDEO_ATLAS_E2E_YOUTUBE_URL is not set")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = YouTubeVideoAcquirer().acquire(youtube_url, Path(tmpdir))

        self.assertTrue(result.local_video_path.exists())
        self.assertEqual(result.source_info.source_type, "youtube")
        self.assertTrue(result.source_metadata)


if __name__ == "__main__":
    unittest.main()
