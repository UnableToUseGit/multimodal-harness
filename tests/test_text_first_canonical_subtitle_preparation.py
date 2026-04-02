from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from video_atlas.workflows.text_first_canonical.subtitle_preparation import resolve_subtitle_assets


class SubtitlePreparationTest(unittest.TestCase):
    def test_reuses_existing_subtitle_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            subtitle_path = input_dir / "source.srt"
            subtitle_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nhi\n", encoding="utf-8")

            result = resolve_subtitle_assets(
                input_dir=input_dir,
                subtitle_path=subtitle_path,
                audio_path=None,
                video_path=None,
                transcriber=None,
                generate_subtitles_if_missing=True,
                logger=None,
            )

        self.assertEqual(result.srt_file_path, subtitle_path)
        self.assertIsNone(result.generated_audio_path)

    @patch("video_atlas.workflows.text_first_canonical.subtitle_preparation.generate_subtitles_for_video")
    def test_generates_subtitles_from_video_when_missing(self, mock_generate: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            video_path = input_dir / "video.mp4"
            video_path.write_bytes(b"video")
            generated_srt = input_dir / "subtitles.srt"
            generated_audio = input_dir / "audio.wav"
            mock_generate.return_value = (generated_srt, generated_audio)

            result = resolve_subtitle_assets(
                input_dir=input_dir,
                subtitle_path=None,
                audio_path=None,
                video_path=video_path,
                transcriber=MagicMock(),
                generate_subtitles_if_missing=True,
                logger=None,
            )

        self.assertEqual(result.srt_file_path, generated_srt)
        self.assertEqual(result.generated_audio_path, generated_audio)

    def test_transcribes_audio_only_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            audio_path = input_dir / "audio.wav"
            audio_path.write_bytes(b"audio")
            transcriber = MagicMock()
            transcriber.transcribe_audio.return_value = []

            result = resolve_subtitle_assets(
                input_dir=input_dir,
                subtitle_path=None,
                audio_path=audio_path,
                video_path=None,
                transcriber=transcriber,
                generate_subtitles_if_missing=True,
                logger=None,
            )

        self.assertEqual(result.srt_file_path, input_dir / "subtitles.srt")
        self.assertEqual(result.generated_audio_path, audio_path)
        transcriber.transcribe_audio.assert_called_once_with(audio_path)

    def test_raises_when_explicit_subtitle_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            subtitle_path = input_dir / "missing.srt"

            with self.assertRaises(FileNotFoundError):
                resolve_subtitle_assets(
                    input_dir=input_dir,
                    subtitle_path=subtitle_path,
                    audio_path=None,
                    video_path=None,
                    transcriber=None,
                    generate_subtitles_if_missing=True,
                    logger=None,
                )

    def test_raises_when_explicit_video_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            video_path = input_dir / "missing.mp4"

            with self.assertRaises(FileNotFoundError):
                resolve_subtitle_assets(
                    input_dir=input_dir,
                    subtitle_path=None,
                    audio_path=None,
                    video_path=video_path,
                    transcriber=MagicMock(),
                    generate_subtitles_if_missing=True,
                    logger=None,
                )

    def test_raises_when_explicit_audio_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            audio_path = input_dir / "missing.wav"

            with self.assertRaises(FileNotFoundError):
                resolve_subtitle_assets(
                    input_dir=input_dir,
                    subtitle_path=None,
                    audio_path=audio_path,
                    video_path=None,
                    transcriber=MagicMock(),
                    generate_subtitles_if_missing=True,
                    logger=None,
                )

    def test_raises_when_no_text_asset_can_be_prepared(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            with self.assertRaises(ValueError):
                resolve_subtitle_assets(
                    input_dir=input_dir,
                    subtitle_path=None,
                    audio_path=None,
                    video_path=None,
                    transcriber=None,
                    generate_subtitles_if_missing=False,
                    logger=None,
                )


if __name__ == "__main__":
    unittest.main()
