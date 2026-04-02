import os
import subprocess
import sys
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from video_atlas.cli.main import build_parser, main
from video_atlas.source_acquisition import UnsupportedSourceError


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

    def test_build_parser_supports_create_with_local_files(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "create",
                "--video-file",
                "/tmp/video.mp4",
                "--subtitle-file",
                "/tmp/subtitles.srt",
                "--metadata-file",
                "/tmp/metadata.json",
                "--output-dir",
                "/tmp/out",
            ]
        )

        self.assertEqual(args.command, "create")
        self.assertEqual(args.video_file, "/tmp/video.mp4")
        self.assertEqual(args.subtitle_file, "/tmp/subtitles.srt")
        self.assertEqual(args.metadata_file, "/tmp/metadata.json")
        self.assertIsNone(args.url)

    def test_build_parser_supports_create_with_audio_file(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "create",
                "--audio-file",
                "/tmp/audio.m4a",
                "--output-dir",
                "/tmp/out",
            ]
        )

        self.assertEqual(args.command, "create")
        self.assertEqual(args.audio_file, "/tmp/audio.m4a")
        self.assertIsNone(args.url)

    @patch("video_atlas.cli.main.create_canonical_from_url")
    @patch("video_atlas.cli.main.load_canonical_pipeline_config")
    def test_main_runs_create_from_url(
        self,
        mock_load_config: MagicMock,
        mock_create_canonical_from_url: MagicMock,
    ) -> None:
        mock_load_config.return_value = MagicMock(
            runtime=MagicMock(),
            acquisition=MagicMock(),
        )

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
        mock_create_canonical_from_url.assert_called_once_with(
            "https://www.youtube.com/watch?v=abc123xyz89",
            tmpdir,
            mock_load_config.return_value,
            structure_request="keep it coarse",
        )

    @patch("video_atlas.cli.main.create_canonical_from_local")
    @patch("video_atlas.cli.main.load_canonical_pipeline_config")
    def test_main_runs_create_from_local_files(
        self,
        mock_load_config: MagicMock,
        mock_create_canonical_from_local: MagicMock,
    ) -> None:
        mock_load_config.return_value = MagicMock(
            runtime=MagicMock(),
            acquisition=MagicMock(),
        )

        with TemporaryDirectory() as tmpdir:
            exit_code = main(
                [
                    "create",
                    "--video-file",
                    "/tmp/video.mp4",
                    "--subtitle-file",
                    "/tmp/subtitles.srt",
                    "--metadata-file",
                    "/tmp/metadata.json",
                    "--output-dir",
                    tmpdir,
                ]
            )

        self.assertEqual(exit_code, 0)
        mock_create_canonical_from_local.assert_called_once_with(
            tmpdir,
            mock_load_config.return_value,
            video_file="/tmp/video.mp4",
            audio_file=None,
            subtitle_file="/tmp/subtitles.srt",
            metadata_file="/tmp/metadata.json",
            structure_request="",
        )

    @patch("video_atlas.cli.main.create_canonical_from_local")
    @patch("video_atlas.cli.main.load_canonical_pipeline_config")
    def test_main_runs_create_from_local_audio_file(
        self,
        mock_load_config: MagicMock,
        mock_create_canonical_from_local: MagicMock,
    ) -> None:
        mock_load_config.return_value = MagicMock(
            runtime=MagicMock(),
            acquisition=MagicMock(),
        )

        with TemporaryDirectory() as tmpdir:
            exit_code = main(
                [
                    "create",
                    "--audio-file",
                    "/tmp/audio.m4a",
                    "--output-dir",
                    tmpdir,
                ]
            )

        self.assertEqual(exit_code, 0)
        mock_create_canonical_from_local.assert_called_once_with(
            tmpdir,
            mock_load_config.return_value,
            video_file=None,
            audio_file="/tmp/audio.m4a",
            subtitle_file=None,
            metadata_file=None,
            structure_request="",
        )

    @patch("video_atlas.cli.main.acquire_from_url")
    @patch("video_atlas.cli.main.load_canonical_pipeline_config")
    def test_main_runs_fetch_from_url(
        self,
        mock_load_config: MagicMock,
        mock_acquire_from_url: MagicMock,
    ) -> None:
        mock_load_config.return_value = MagicMock(
            acquisition=MagicMock(),
        )

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
        mock_acquire_from_url.assert_called_once_with(
            "https://www.youtube.com/watch?v=abc123xyz89",
            tmpdir,
            prefer_youtube_subtitles=mock_load_config.return_value.acquisition.prefer_youtube_subtitles,
            youtube_output_template=mock_load_config.return_value.acquisition.youtube_output_template,
            max_youtube_video_duration_sec=mock_load_config.return_value.acquisition.max_youtube_video_duration_sec,
            youtube_cookies_file=mock_load_config.return_value.acquisition.youtube_cookies_file,
            youtube_cookies_from_browser=mock_load_config.return_value.acquisition.youtube_cookies_from_browser,
        )

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
