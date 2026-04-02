from pathlib import Path
import tempfile
import unittest

from video_atlas.schemas import CanonicalAtlas, CanonicalExecutionPlan
from video_atlas.schemas import SourceInfoRecord
from video_atlas.source_acquisition import SourceAcquisitionResult


class SourceAcquisitionModelsTest(unittest.TestCase):
    def test_source_info_record_exposes_expected_fields(self) -> None:
        record = SourceInfoRecord(
            source_type="youtube",
            source_url="https://www.youtube.com/watch?v=abc123",
            canonical_source_url="https://www.youtube.com/watch?v=abc123",
            subtitle_source="youtube_caption",
            subtitle_fallback_required=False,
            acquisition_timestamp="2026-04-01T00:00:00Z",
        )

        self.assertEqual(record.source_type, "youtube")
        self.assertEqual(record.source_url, "https://www.youtube.com/watch?v=abc123")
        self.assertEqual(record.canonical_source_url, "https://www.youtube.com/watch?v=abc123")
        self.assertEqual(record.subtitle_source, "youtube_caption")
        self.assertFalse(record.subtitle_fallback_required)
        self.assertEqual(record.acquisition_timestamp, "2026-04-01T00:00:00Z")

    def test_source_info_record_uses_optional_timestamp_default(self) -> None:
        record = SourceInfoRecord(
            source_type="youtube",
            source_url="https://www.youtube.com/watch?v=abc123",
            canonical_source_url="https://www.youtube.com/watch?v=abc123",
        )

        self.assertIsNone(record.acquisition_timestamp)

    def test_source_acquisition_result_tracks_local_assets_and_metadata(self) -> None:
        record = SourceInfoRecord(
            source_type="youtube",
            source_url="https://www.youtube.com/watch?v=abc123",
            canonical_source_url="https://www.youtube.com/watch?v=abc123",
            subtitle_source="youtube_caption",
            subtitle_fallback_required=False,
            acquisition_timestamp="2026-04-01T00:00:00Z",
        )
        result = SourceAcquisitionResult(
            source_info=record,
            local_video_path=Path("/tmp/video.mp4"),
            local_subtitles_path=Path("/tmp/subtitles.srt"),
            source_metadata={"title": "Sample Title", "channel": "Sample Channel"},
            artifacts={"info_json": Path("source/info.json")},
        )

        self.assertEqual(result.source_info, record)
        self.assertEqual(result.local_video_path.name, "video.mp4")
        self.assertEqual(result.local_subtitles_path.name, "subtitles.srt")
        self.assertEqual(result.source_metadata["title"], "Sample Title")
        self.assertEqual(result.artifacts["info_json"], Path("source/info.json"))

    def test_source_acquisition_result_supports_audio_assets(self) -> None:
        record = SourceInfoRecord(
            source_type="xiaoyuzhou",
            source_url="https://www.xiaoyuzhoufm.com/episode/1234567890abcdef12345678",
            canonical_source_url="https://www.xiaoyuzhoufm.com/episode/1234567890abcdef12345678",
        )
        result = SourceAcquisitionResult(
            source_info=record,
            local_audio_path=Path("/tmp/audio.m4a"),
            source_metadata={"title": "Podcast"},
        )

        self.assertEqual(result.local_audio_path, Path("/tmp/audio.m4a"))
        self.assertIsNone(result.local_video_path)

    def test_canonical_atlas_accepts_optional_source_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            atlas = CanonicalAtlas(
                title="Example",
                duration=12.0,
                abstract="Summary",
                segments=[],
                execution_plan=CanonicalExecutionPlan(),
                atlas_dir=Path(tmpdir),
                relative_video_path=Path("video.mp4"),
                source_info=SourceInfoRecord(
                    source_type="youtube",
                    source_url="https://www.youtube.com/watch?v=abc123",
                    canonical_source_url="https://www.youtube.com/watch?v=abc123",
                ),
                source_metadata={"title": "Example"},
            )

        self.assertIsInstance(atlas.source_info, SourceInfoRecord)
        self.assertEqual(atlas.source_info.source_type, "youtube")
        self.assertEqual(atlas.source_metadata["title"], "Example")


if __name__ == "__main__":
    unittest.main()
