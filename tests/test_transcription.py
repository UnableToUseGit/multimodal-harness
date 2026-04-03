from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from video_atlas.config import TranscriberRuntimeConfig, build_transcriber, load_canonical_pipeline_config
from video_atlas.transcription import TranscriptSegment


class TranscriptionConfigAndFactoryTest(unittest.TestCase):
    def test_load_canonical_pipeline_config_supports_groq_transcriber_fields(self) -> None:
        payload = {
            "planner": {"provider": "openai_compatible", "model_name": "planner-model"},
            "segmentor": {"provider": "openai_compatible", "model_name": "segmentor-model"},
            "captioner": {"provider": "openai_compatible", "model_name": "caption-model"},
            "transcriber": {
                "enabled": True,
                "backend": "groq_whisper",
                "groq_model": "whisper-large-v3",
                "groq_language": "zh",
                "groq_max_chunk_size_mb": 18,
                "groq_audio_bitrate": "48k",
                "groq_timestamp_granularities": ["segment"],
                "groq_request_timeout_sec": 180.0,
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "canonical.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            config = load_canonical_pipeline_config(path)

        self.assertEqual(config.transcriber.backend, "groq_whisper")
        self.assertEqual(config.transcriber.groq_model, "whisper-large-v3")
        self.assertEqual(config.transcriber.groq_language, "zh")
        self.assertEqual(config.transcriber.groq_max_chunk_size_mb, 18)
        self.assertEqual(config.transcriber.groq_audio_bitrate, "48k")
        self.assertEqual(config.transcriber.groq_timestamp_granularities, ["segment"])

    def test_load_canonical_pipeline_config_supports_aliyun_transcriber_fields(self) -> None:
        payload = {
            "planner": {"provider": "openai_compatible", "model_name": "planner-model"},
            "segmentor": {"provider": "openai_compatible", "model_name": "segmentor-model"},
            "captioner": {"provider": "openai_compatible", "model_name": "caption-model"},
            "transcriber": {
                "enabled": True,
                "backend": "aliyun_asr",
                "sample_rate": 16000,
                "channels": 1,
                "aliyun_model": "fun-asr",
                "aliyun_language_hints": ["zh", "en"],
                "aliyun_diarization_enabled": True,
                "aliyun_oss_endpoint": "https://oss-cn-beijing.aliyuncs.com",
                "aliyun_oss_bucket_name": "bucket-name",
                "aliyun_oss_prefix": "audios/",
                "aliyun_signed_url_expires_sec": 3600,
                "aliyun_poll_interval_sec": 2.0,
                "aliyun_poll_timeout_sec": 900.0,
                "retain_remote_artifacts": False,
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "canonical.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            config = load_canonical_pipeline_config(path)

        self.assertEqual(config.transcriber.backend, "aliyun_asr")
        self.assertEqual(config.transcriber.aliyun_model, "fun-asr")
        self.assertEqual(config.transcriber.aliyun_language_hints, ["zh", "en"])
        self.assertEqual(config.transcriber.aliyun_oss_bucket_name, "bucket-name")
        self.assertEqual(config.transcriber.aliyun_poll_timeout_sec, 900.0)

    def test_build_transcriber_supports_aliyun_backend(self) -> None:
        config = TranscriberRuntimeConfig(
            backend="aliyun_asr",
            aliyun_oss_endpoint="https://oss-cn-beijing.aliyuncs.com",
            aliyun_oss_bucket_name="bucket-name",
        )

        transcriber = build_transcriber(config)

        self.assertEqual(transcriber.__class__.__name__, "AliyunAsrTranscriber")

    def test_build_transcriber_supports_groq_backend(self) -> None:
        config = TranscriberRuntimeConfig(
            backend="groq_whisper",
            groq_model="whisper-large-v3",
        )

        transcriber = build_transcriber(config)

        self.assertEqual(transcriber.__class__.__name__, "GroqWhisperTranscriber")


class AliyunTranscriberTest(unittest.TestCase):
    def test_parse_aliyun_transcription_result_returns_transcript_segments(self) -> None:
        from video_atlas.transcription.aliyun_asr import parse_aliyun_transcription_result

        raw_result = {
            "transcripts": [
                {
                    "sentences": [
                        {"begin_time": 0, "end_time": 1200, "text": "第一句"},
                        {"begin_time": 1200, "end_time": 3100, "text": " second sentence "},
                        {"begin_time": 3100, "end_time": 4000, "text": "   "},
                    ]
                }
            ]
        }

        segments = parse_aliyun_transcription_result(raw_result)

        self.assertEqual(
            segments,
            [
                TranscriptSegment(start=0.0, end=1.2, text="第一句"),
                TranscriptSegment(start=1.2, end=3.1, text="second sentence"),
            ],
        )

    def test_transcribe_audio_orchestrates_oss_and_asr_clients(self) -> None:
        from video_atlas.transcription.aliyun_transcriber import AliyunAsrConfig, AliyunAsrTranscriber

        oss_client = Mock()
        asr_client = Mock()
        oss_client.upload_file.return_value = None
        oss_client.get_signed_download_url.return_value = "https://signed.example/audio.wav"
        asr_client.transcribe_from_url.return_value = [
            TranscriptSegment(start=0.0, end=1.5, text="hello"),
        ]

        transcriber = AliyunAsrTranscriber(
            AliyunAsrConfig(
                oss_endpoint="https://oss-cn-beijing.aliyuncs.com",
                oss_bucket_name="bucket-name",
            ),
            oss_client=oss_client,
            asr_client=asr_client,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "audio.wav"
            audio_path.write_bytes(b"audio")

            segments = transcriber.transcribe_audio(audio_path)

        self.assertEqual(segments, [TranscriptSegment(start=0.0, end=1.5, text="hello")])
        oss_client.upload_file.assert_called_once()
        oss_client.get_signed_download_url.assert_called_once()
        asr_client.transcribe_from_url.assert_called_once_with("https://signed.example/audio.wav")


class GroqTranscriberTest(unittest.TestCase):
    def test_parse_groq_transcription_result_returns_transcript_segments(self) -> None:
        from video_atlas.transcription.groq_whisper import parse_groq_transcription_result

        raw_result = {
            "segments": [
                {"start": 0.0, "end": 1.5, "text": " 第一段 "},
                {"start": 1.5, "end": 3.2, "text": "second segment"},
                {"start": 3.2, "end": 4.0, "text": "   "},
            ]
        }

        segments = parse_groq_transcription_result(raw_result)

        self.assertEqual(
            segments,
            [
                TranscriptSegment(start=0.0, end=1.5, text="第一段"),
                TranscriptSegment(start=1.5, end=3.2, text="second segment"),
            ],
        )

    def test_transcribe_audio_chunks_and_merges_offsets(self) -> None:
        from video_atlas.transcription.groq_whisper import GroqWhisperConfig, GroqWhisperTranscriber

        transcriber = GroqWhisperTranscriber(
            GroqWhisperConfig(api_key_env="TEST_GROQ_API_KEY"),
            session=Mock(),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            audio_path = root / "audio.wav"
            audio_path.write_bytes(b"audio")
            prepared_audio = root / "prepared.mp3"
            prepared_audio.write_bytes(b"prepared")
            chunk_0 = root / "chunk_0.mp3"
            chunk_1 = root / "chunk_1.mp3"
            chunk_0.write_bytes(b"c0")
            chunk_1.write_bytes(b"c1")

            with patch.object(transcriber, "_transcode_audio_for_upload", return_value=prepared_audio), \
                patch.object(transcriber, "_split_audio_if_needed", return_value=[(chunk_0, 0.0), (chunk_1, 10.0)]), \
                patch.object(
                    transcriber,
                    "_transcribe_chunk",
                    side_effect=[
                        [TranscriptSegment(start=0.0, end=1.0, text="alpha")],
                        [TranscriptSegment(start=0.5, end=1.5, text="beta")],
                    ],
                ):
                segments = transcriber.transcribe_audio(audio_path)

        self.assertEqual(
            segments,
            [
                TranscriptSegment(start=0.0, end=1.0, text="alpha"),
                TranscriptSegment(start=10.5, end=11.5, text="beta"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
