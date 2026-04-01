import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from video_atlas.cli.main import build_parser, main
from video_atlas.source_acquisition import UnsupportedSourceError
from video_atlas.schemas import SourceInfoRecord


ROOT = os.path.dirname(os.path.dirname(__file__))


class CliSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.env_backup = {
            "VIDEO_ATLAS_API_BASE": os.environ.get("VIDEO_ATLAS_API_BASE"),
            "VIDEO_ATLAS_API_KEY": os.environ.get("VIDEO_ATLAS_API_KEY"),
        }

    def tearDown(self) -> None:
        for key in self.env_backup:
            os.environ.pop(key, None)
        for key, value in self.env_backup.items():
            if value is not None:
                os.environ[key] = value

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        src_path = os.path.join(ROOT, "src")
        env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}:{env['PYTHONPATH']}"
        return subprocess.run(
            [sys.executable, "-m", "video_atlas.cli", *args],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_info_command(self) -> None:
        result = self._run_cli("info")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("video_atlas 0.1.0", result.stdout)

    def test_check_import_command(self) -> None:
        result = self._run_cli("check-import")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("import-ok 0.1.0", result.stdout)

    def test_config_command(self) -> None:
        os.environ["VIDEO_ATLAS_API_BASE"] = "https://example.test/v1"
        os.environ["VIDEO_ATLAS_API_KEY"] = "secret-token-1234"

        result = self._run_cli("config")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("configured yes", result.stdout)
        self.assertIn("api_base https://example.test/v1", result.stdout)
        self.assertIn("api_key secr...1234", result.stdout)

    def test_build_parser_supports_create_with_url(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "create",
                "--url",
                "https://www.youtube.com/watch?v=abc123xyz89",
                "--output-dir",
                "/tmp/out",
                "--config",
                "configs/canonical/default.json",
                "--structure-request",
                "keep it coarse",
            ]
        )

        self.assertEqual(args.command, "create")
        self.assertEqual(args.url, "https://www.youtube.com/watch?v=abc123xyz89")
        self.assertEqual(args.output_dir, "/tmp/out")
        self.assertEqual(args.config, "configs/canonical/default.json")
        self.assertEqual(args.structure_request, "keep it coarse")

    @patch("video_atlas.cli.main.CanonicalAtlasWorkflow")
    @patch("video_atlas.cli.main.acquire_from_url")
    @patch("video_atlas.cli.main.create_acquisition_subdir")
    @patch("video_atlas.cli.main.build_generator")
    @patch("video_atlas.cli.main.build_transcriber")
    @patch("video_atlas.cli.main.load_canonical_pipeline_config")
    def test_main_runs_create_from_url(
        self,
        mock_load_config: MagicMock,
        mock_build_transcriber: MagicMock,
        mock_build_generator: MagicMock,
        mock_create_acquisition_subdir: MagicMock,
        mock_acquire_from_url: MagicMock,
        mock_workflow_cls: MagicMock,
    ) -> None:
        mock_load_config.return_value = MagicMock(
            planner=MagicMock(),
            text_segmentor=MagicMock(),
            multimodal_segmentor=MagicMock(),
            structure_composer=MagicMock(),
            captioner=MagicMock(),
            transcriber=MagicMock(),
            runtime=MagicMock(
                generate_subtitles_if_missing=True,
                text_chunk_size_sec=1800,
                text_chunk_overlap_sec=120,
                multimodal_chunk_size_sec=600,
                multimodal_chunk_overlap_sec=60,
                caption_with_subtitles=True,
            ),
            acquisition=MagicMock(
                prefer_youtube_subtitles=True,
                youtube_output_template="%(id)s.%(ext)s",
            ),
        )
        mock_build_generator.side_effect = lambda config: config
        mock_build_transcriber.return_value = "transcriber"
        mock_create_acquisition_subdir.return_value = Path("/tmp/downloaded/session-uid")

        source_info = SourceInfoRecord(
            source_type="youtube",
            source_url="https://www.youtube.com/watch?v=abc123xyz89",
            canonical_source_url="https://www.youtube.com/watch?v=abc123xyz89",
            subtitle_source="youtube_caption",
            subtitle_fallback_required=False,
        )
        mock_acquire_from_url.return_value = MagicMock(
            local_video_path=Path("/tmp/downloaded/video.mp4"),
            local_subtitles_path=Path("/tmp/downloaded/subtitles.srt"),
            source_info=source_info,
            source_metadata={"title": "Example Video"},
        )

        mock_workflow = mock_workflow_cls.return_value
        mock_workflow.create.return_value = (MagicMock(), {})

        with TemporaryDirectory() as tmpdir:
            exit_code = main(
                [
                    "create",
                    "--url",
                    "https://www.youtube.com/watch?v=abc123xyz89",
                    "--output-dir",
                    tmpdir,
                    "--config",
                    "configs/canonical/default.json",
                    "--structure-request",
                    "keep it coarse",
                ]
            )

        self.assertEqual(exit_code, 0)
        mock_create_acquisition_subdir.assert_called_once_with(Path(tmpdir) / ".acquisition")
        mock_acquire_from_url.assert_called_once()
        mock_workflow.create.assert_called_once_with(
            output_dir=Path(tmpdir),
            source_video_path=Path("/tmp/downloaded/video.mp4"),
            source_srt_file_path=Path("/tmp/downloaded/subtitles.srt"),
            structure_request="keep it coarse",
            verbose=False,
            source_info=source_info,
            source_metadata={"title": "Example Video"},
        )

    @patch("video_atlas.cli.main.materialize_fetch_workspace")
    @patch("video_atlas.cli.main.acquire_from_url")
    @patch("video_atlas.cli.main.create_acquisition_subdir")
    @patch("video_atlas.cli.main.load_canonical_pipeline_config")
    def test_main_runs_fetch_from_url(
        self,
        mock_load_config: MagicMock,
        mock_create_acquisition_subdir: MagicMock,
        mock_acquire_from_url: MagicMock,
        mock_materialize_fetch_workspace: MagicMock,
    ) -> None:
        mock_load_config.return_value = MagicMock(
            acquisition=MagicMock(
                prefer_youtube_subtitles=True,
                youtube_output_template="%(id)s.%(ext)s",
            )
        )
        acquisition = MagicMock()
        mock_acquire_from_url.return_value = acquisition
        mock_create_acquisition_subdir.return_value = Path("/tmp/downloaded/session-uid")

        with TemporaryDirectory() as tmpdir:
            exit_code = main(
                [
                    "fetch",
                    "--url",
                    "https://www.youtube.com/watch?v=abc123xyz89",
                    "--output-dir",
                    tmpdir,
                ]
            )

        self.assertEqual(exit_code, 0)
        mock_create_acquisition_subdir.assert_called_once_with(Path(tmpdir) / ".acquisition")
        mock_acquire_from_url.assert_called_once()
        mock_materialize_fetch_workspace.assert_called_once_with(acquisition, Path(tmpdir))

    @patch("video_atlas.cli.main.acquire_from_url", side_effect=UnsupportedSourceError("unsupported source"))
    def test_main_returns_error_for_unsupported_url(self, _mock_acquire_from_url: MagicMock) -> None:
        with TemporaryDirectory() as tmpdir:
            exit_code = main(
                [
                    "fetch",
                    "--url",
                    "https://example.com/video",
                    "--output-dir",
                    tmpdir,
                ]
            )

        self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
