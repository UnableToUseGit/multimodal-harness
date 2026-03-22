import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from video_atlas.agents.canonical_atlas.pipeline import PipelineMixin
from video_atlas.workspaces.base import get_logger


class _DummyPipeline(PipelineMixin):
    def __init__(self, transcriber=None, generate_subtitles_if_missing=True):
        self.transcriber = transcriber
        self.generate_subtitles_if_missing = generate_subtitles_if_missing
        self.logger = get_logger("DummyPipeline")

    def _log_info(self, message, *args):
        self.logger.info(message, *args)

    def _log_warning(self, message, *args):
        self.logger.warning(message, *args)


class VideoAtlasSubtitleResolutionTest(unittest.TestCase):
    def test_resolve_existing_subtitle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            srt_path = root / "existing.srt"
            srt_path.write_text("existing", encoding="utf-8")
            pipeline = _DummyPipeline()

            resolved = pipeline._resolve_subtitle_path(root, "video.mp4")

            self.assertEqual(resolved, str(srt_path))

    def test_generate_subtitle_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            pipeline = _DummyPipeline(transcriber=object(), generate_subtitles_if_missing=True)

            def _fake_generate(video_path, subtitle_path, transcriber, logger):
                Path(subtitle_path).write_text("generated", encoding="utf-8")
                return Path(subtitle_path)

            with patch("video_atlas.agents.canonical_atlas.pipeline.generate_subtitles_for_video", side_effect=_fake_generate):
                resolved = pipeline._resolve_subtitle_path(root, "video.mp4", verbose=True)

            self.assertEqual(resolved, str(root / "subtitles.srt"))
            self.assertTrue((root / "subtitles.srt").exists())

    def test_fallback_when_transcriber_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            pipeline = _DummyPipeline(transcriber=None, generate_subtitles_if_missing=True)

            resolved = pipeline._resolve_subtitle_path(root, "video.mp4", verbose=True)

            self.assertEqual(resolved, "")


if __name__ == "__main__":
    unittest.main()
