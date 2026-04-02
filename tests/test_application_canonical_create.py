from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from video_atlas.application.canonical_create import create_canonical_from_local, create_canonical_from_url
from video_atlas.config.models import CanonicalPipelineConfig
from video_atlas.schemas import SourceAcquisitionResult, SourceInfoRecord, SourceMetadata
from video_atlas.workflows.text_first_canonical_atlas_workflow import TextFirstCanonicalAtlasWorkflow


class CanonicalCreateApplicationTest(unittest.TestCase):
    def test_build_workflow_moves_verbose_into_workflow_instance(self) -> None:
        from video_atlas.application.canonical_create import _build_workflow

        config = CanonicalPipelineConfig(planner=None)
        config.runtime.verbose = True

        with patch("video_atlas.application.canonical_create.build_generator", side_effect=lambda value: value), \
            patch("video_atlas.application.canonical_create.build_transcriber", return_value=None):
            workflow = _build_workflow(config)

        self.assertIsInstance(workflow, TextFirstCanonicalAtlasWorkflow)
        self.assertTrue(workflow.verbose)

    @patch("video_atlas.application.canonical_create._build_workflow")
    @patch("video_atlas.application.canonical_create.acquire_from_url")
    def test_create_canonical_from_url_builds_request_from_acquisition_result(
        self,
        mock_acquire_from_url: MagicMock,
        mock_build_workflow: MagicMock,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir)
            run_dir = output_root / "run-001"
            input_dir = run_dir / "input"
            input_dir.mkdir(parents=True)
            video_path = input_dir / "video.mp4"
            subtitle_path = input_dir / "subtitles.srt"
            video_path.write_bytes(b"video")
            subtitle_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nhi\n", encoding="utf-8")
            mock_acquire_from_url.return_value = SourceAcquisitionResult(
                source_info=SourceInfoRecord(
                    source_type="youtube",
                    source_url="https://www.youtube.com/watch?v=abc123xyz89",
                    subtitle_source="youtube_caption",
                ),
                source_metadata=SourceMetadata(title="Example Video"),
                video_path=video_path,
                subtitles_path=subtitle_path,
            )

            workflow = mock_build_workflow.return_value
            workflow.create.return_value = ("atlas", {})

            result = create_canonical_from_url(
                "https://www.youtube.com/watch?v=abc123xyz89",
                tmpdir,
                CanonicalPipelineConfig(planner=None),
                structure_request="keep it coarse",
            )

        self.assertEqual(result, ("atlas", {}))
        acquire_call = mock_acquire_from_url.call_args
        self.assertEqual(acquire_call.kwargs["max_youtube_video_duration_sec"], 1500)
        self.assertIsNone(acquire_call.kwargs["youtube_cookies_file"])
        self.assertIsNone(acquire_call.kwargs["youtube_cookies_from_browser"])
        request_arg = workflow.create.call_args.args[0]
        self.assertEqual(len(workflow.create.call_args.args), 1)
        self.assertEqual(request_arg.atlas_dir.parent, output_root)
        self.assertEqual(request_arg.video_path, video_path)
        self.assertEqual(request_arg.subtitle_path, subtitle_path)
        self.assertEqual(request_arg.structure_request, "keep it coarse")
        self.assertEqual(request_arg.source_info.source_type, "youtube")
        self.assertEqual(request_arg.source_metadata.title, "Example Video")

    @patch("video_atlas.application.canonical_create._build_workflow")
    def test_create_canonical_from_local_materializes_local_inputs(self, mock_build_workflow: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_video = root / "source-video.mp4"
            source_video.write_bytes(b"video")
            source_subtitles = root / "source-subtitles.srt"
            source_subtitles.write_text("1\n00:00:00,000 --> 00:00:01,000\nhi\n", encoding="utf-8")
            source_metadata = root / "metadata.json"
            source_metadata.write_text(json.dumps({"title": "Local Video"}), encoding="utf-8")

            workflow = mock_build_workflow.return_value
            workflow.create.return_value = ("atlas", {})

            result = create_canonical_from_local(
                output_dir=root / "outputs",
                config=CanonicalPipelineConfig(planner=None),
                video_file=source_video,
                subtitle_file=source_subtitles,
                metadata_file=source_metadata,
                structure_request="local request",
            )

            self.assertEqual(result, ("atlas", {}))
            request_arg = workflow.create.call_args.args[0]
            self.assertEqual(request_arg.atlas_dir.parent.name, "outputs")
            self.assertTrue(request_arg.video_path.exists())
            self.assertTrue(request_arg.subtitle_path.exists())
            self.assertEqual(request_arg.structure_request, "local request")
            self.assertEqual(request_arg.source_metadata.title, "Local Video")


if __name__ == "__main__":
    unittest.main()
