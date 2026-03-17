import tempfile
import unittest
from pathlib import Path

from video_atlas.transcription import TranscriptSegment, generate_subtitles_for_video, transcript_segments_to_srt


class _FakeTranscriber:
    def __init__(self, segments: list[TranscriptSegment]):
        self.segments = segments

    def transcribe_audio(self, audio_path):
        return self.segments


def _fake_audio_extractor(video_path, audio_path):
    Path(audio_path).write_text("fake wav", encoding="utf-8")
    return Path(audio_path)


class TranscriptionTest(unittest.TestCase):
    def test_transcript_segments_to_srt(self) -> None:
        srt_text = transcript_segments_to_srt(
            [
                TranscriptSegment(start=0.0, end=1.25, text="hello world"),
                TranscriptSegment(start=2.0, end=3.5, text="second line"),
            ]
        )

        self.assertIn("00:00:00,000 --> 00:00:01,250", srt_text)
        self.assertIn("hello world", srt_text)
        self.assertIn("00:00:02,000 --> 00:00:03,500", srt_text)

    def test_generate_subtitles_for_video(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            video_path = root / "sample.mp4"
            subtitle_path = root / "subtitles.srt"
            audio_path = root / "sample.wav"
            video_path.write_text("fake video", encoding="utf-8")

            generate_subtitles_for_video(
                video_path=video_path,
                subtitle_path=subtitle_path,
                transcriber=_FakeTranscriber([TranscriptSegment(start=0.0, end=1.0, text="generated speech")]),
                audio_extractor=_fake_audio_extractor,
            )

            self.assertTrue(subtitle_path.exists())
            self.assertTrue(audio_path.exists())
            self.assertIn("generated speech", subtitle_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
