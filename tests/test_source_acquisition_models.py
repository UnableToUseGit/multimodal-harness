from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from video_atlas.schemas import CanonicalAtlas, CanonicalExecutionPlan, SourceAcquisitionResult, SourceInfoRecord, SourceMetadata


class SourceAcquisitionModelsTest(unittest.TestCase):
    def test_source_info_record_exposes_expected_fields(self) -> None:
        record = SourceInfoRecord(
            source_type="youtube",
            source_url="https://www.youtube.com/watch?v=abc123",
            subtitle_source="youtube_caption",
            acquisition_timestamp=datetime(2026, 4, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(record.source_type, "youtube")
        self.assertEqual(record.source_url, "https://www.youtube.com/watch?v=abc123")
        self.assertEqual(record.subtitle_source, "youtube_caption")
        self.assertEqual(record.to_dict()["acquisition_timestamp"], "2026-04-01T00:00:00+00:00")

    def test_source_acquisition_result_tracks_assets_and_metadata(self) -> None:
        record = SourceInfoRecord(source_type="youtube", source_url="https://www.youtube.com/watch?v=abc123")
        metadata = SourceMetadata(title="Sample Title", author="Sample Channel")
        result = SourceAcquisitionResult(
            source_info=record,
            video_path=Path("/tmp/video.mp4"),
            subtitles_path=Path("/tmp/subtitles.srt"),
            source_metadata=metadata,
            artifacts={"info_json": Path("source/info.json")},
        )

        self.assertEqual(result.source_info, record)
        self.assertEqual(result.video_path.name, "video.mp4")
        self.assertEqual(result.subtitles_path.name, "subtitles.srt")
        self.assertEqual(result.source_metadata.title, "Sample Title")
        self.assertEqual(result.artifacts["info_json"], Path("source/info.json"))

    def test_source_acquisition_result_supports_audio_assets(self) -> None:
        record = SourceInfoRecord(
            source_type="xiaoyuzhou",
            source_url="https://www.xiaoyuzhoufm.com/episode/1234567890abcdef12345678",
        )
        result = SourceAcquisitionResult(
            source_info=record,
            audio_path=Path("/tmp/audio.m4a"),
            source_metadata=SourceMetadata(title="Podcast"),
        )

        self.assertEqual(result.audio_path, Path("/tmp/audio.m4a"))
        self.assertIsNone(result.video_path)

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
                ),
                source_metadata={"title": "Example"},
            )

        self.assertIsInstance(atlas.source_info, SourceInfoRecord)
        self.assertEqual(atlas.source_info.source_type, "youtube")
        self.assertEqual(atlas.source_metadata["title"], "Example")


if __name__ == "__main__":
    unittest.main()
