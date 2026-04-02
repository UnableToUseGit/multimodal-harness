import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from video_atlas.source_acquisition.xiaoyuzhou import (
    XiaoyuzhouAudioAcquirer,
    extract_audio_url_from_page,
    extract_title_from_page,
    is_supported_xiaoyuzhou_episode_url,
)


class XiaoyuzhouAcquisitionTest(unittest.TestCase):
    def test_is_supported_xiaoyuzhou_episode_url(self) -> None:
        self.assertTrue(is_supported_xiaoyuzhou_episode_url("https://www.xiaoyuzhoufm.com/episode/1234567890abcdef12345678"))
        self.assertFalse(is_supported_xiaoyuzhou_episode_url("https://www.xiaoyuzhoufm.com/podcast/123"))
        self.assertFalse(is_supported_xiaoyuzhou_episode_url("https://example.com/episode/123"))

    def test_extract_audio_url_and_title_from_page(self) -> None:
        page = """
        <html>
          <script id="__NEXT_DATA__" type="application/json">
            {"props":{"pageProps":{"episode":{"title":"Episode Title","enclosure":{"url":"https://media.xyzcdn.net/demo-file.m4a"}}}}}
          </script>
        </html>
        """
        self.assertEqual(extract_title_from_page(page), "Episode Title")
        self.assertEqual(extract_audio_url_from_page(page), "https://media.xyzcdn.net/demo-file.m4a")

    @patch("video_atlas.source_acquisition.xiaoyuzhou.urlopen")
    def test_acquire_downloads_audio_and_builds_metadata(self, mock_urlopen: object) -> None:
        page = """
        <html>
          <script id="__NEXT_DATA__" type="application/json">
            {
              "props": {
                "pageProps": {
                  "episode": {
                    "title": "Episode Title",
                    "description": "Episode Description",
                    "duration": 1234,
                    "pubDate": "2024-08-26T01:00:00.000Z",
                    "enclosure": {"url": "https://media.xyzcdn.net/demo-file.m4a"},
                    "image": {
                      "picUrl": "https://image.xyzcdn.net/episode.png",
                      "thumbnailUrl": "https://image.xyzcdn.net/episode-thumb.png"
                    },
                    "podcast": {
                      "author": "Podcast Author",
                      "image": {"picUrl": "https://image.xyzcdn.net/podcast.png"}
                    }
                  }
                }
              }
            }
          </script>
        </html>
        """
        mock_urlopen.side_effect = [
            io.BytesIO(page.encode("utf-8")),
            io.BytesIO(b"audio-bytes"),
        ]

        with TemporaryDirectory() as tmpdir:
            result = XiaoyuzhouAudioAcquirer().acquire(
                "https://www.xiaoyuzhoufm.com/episode/1234567890abcdef12345678",
                Path(tmpdir),
            )

        self.assertEqual(result.source_info.source_type, "xiaoyuzhou")
        self.assertEqual(result.audio_path.name, "audio.m4a")
        self.assertEqual(result.source_metadata.title, "Episode Title")
        self.assertEqual(result.source_metadata.introduction, "Episode Description")
        self.assertEqual(result.source_metadata.author, "Podcast Author")
        self.assertEqual(result.source_metadata.duration_seconds, 1234)
        self.assertIn("https://image.xyzcdn.net/episode.png", result.source_metadata.thumbnails)


if __name__ == "__main__":
    unittest.main()
