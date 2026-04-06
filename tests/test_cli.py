import os
import io
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from importlib.machinery import ModuleSpec
from tempfile import TemporaryDirectory
from unittest.mock import ANY, MagicMock, patch

from video_atlas.cli.main import build_parser, main


ROOT = os.path.dirname(os.path.dirname(__file__))


class CliSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.env_backup = {
            "LLM_API_BASE_URL": os.environ.get("LLM_API_BASE_URL"),
            "LLM_API_KEY": os.environ.get("LLM_API_KEY"),
            "YOUTUBE_COOKIES_FILE": os.environ.get("YOUTUBE_COOKIES_FILE"),
            "YOUTUBE_COOKIES_FROM_BROWSER": os.environ.get("YOUTUBE_COOKIES_FROM_BROWSER"),
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
        self.assertIn("MM Harness", result.stdout)
        self.assertIn("version      0.1.0", result.stdout)

    def test_check_import_command(self) -> None:
        result = self._run_cli("check-import")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("import-ok 0.1.0", result.stdout)

    def test_config_command(self) -> None:
        os.environ["LLM_API_BASE_URL"] = "https://example.test/v1"
        os.environ["LLM_API_KEY"] = "secret-token-1234"

        result = self._run_cli("config")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("configured yes", result.stdout)
        self.assertIn("api_base https://example.test/v1", result.stdout)
        self.assertIn("api_key secr...1234", result.stdout)

    def test_doctor_warns_with_cookie_env_var_names(self) -> None:
        stdout = io.StringIO()
        with patch("video_atlas.cli.main.shutil.which", return_value="/usr/bin/fake"):
            with patch.dict(
                os.environ,
                {
                    "LLM_API_BASE_URL": "https://example.test/v1",
                    "LLM_API_KEY": "secret",
                    "GROQ_API_KEY": "groq-secret",
                },
                clear=False,
            ):
                with redirect_stdout(stdout):
                    exit_code = main(["doctor"])

        self.assertEqual(exit_code, 0)
        self.assertIn(
            "Ask the user for YOUTUBE_COOKIES_FILE or YOUTUBE_COOKIES_FROM_BROWSER",
            stdout.getvalue(),
        )

    def test_doctor_detects_ytdlp_from_python_environment(self) -> None:
        stdout = io.StringIO()

        def fake_which(name: str):
            if name == "yt-dlp":
                return None
            return f"/usr/bin/{name}"

        with patch("video_atlas.cli.main.shutil.which", side_effect=fake_which):
            with patch("video_atlas.cli.main.importlib.util.find_spec", return_value=ModuleSpec("yt_dlp", loader=None)):
                with patch.dict(
                    os.environ,
                    {
                        "LLM_API_BASE_URL": "https://example.test/v1",
                        "LLM_API_KEY": "secret",
                        "GROQ_API_KEY": "groq-secret",
                    },
                    clear=False,
                ):
                    with redirect_stdout(stdout):
                        exit_code = main(["doctor"])

        self.assertEqual(exit_code, 0)
        self.assertIn("OK    yt-dlp", stdout.getvalue())

    def test_build_parser_supports_create_with_url(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "create",
                "--url",
                "https://www.youtube.com/watch?v=abc123xyz89",
                "--output-dir",
                "/tmp/out",
                "--structure-request",
                "keep it coarse",
            ]
        )

        self.assertEqual(args.command, "create")
        self.assertEqual(args.url, "https://www.youtube.com/watch?v=abc123xyz89")
        self.assertEqual(args.output_dir, "/tmp/out")
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

    def test_build_parser_supports_skill_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["skill", "--install"])
        self.assertEqual(args.command, "skill")
        self.assertTrue(args.install)

    def test_info_and_help_do_not_require_heavy_runtime_imports(self) -> None:
        import builtins

        real_import = builtins.__import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.startswith("video_atlas.application") or name.startswith("video_atlas.source_acquisition"):
                raise AssertionError(f"unexpected heavy import: {name}")
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=guarded_import):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["info"])
            self.assertEqual(exit_code, 0)

            parser = build_parser()
            help_text = parser.format_help()
            self.assertIn("create", help_text)

    @patch("video_atlas.cli.main.install_skill")
    def test_main_runs_install(self, mock_install_skill: MagicMock) -> None:
        mock_install_skill.return_value = MagicMock(target_dir="/tmp/skills/mm-harness")
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["install"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Installing MM Harness assets...", stdout.getvalue())
        self.assertIn("skill_dir: /tmp/skills/mm-harness", stdout.getvalue())

    @patch("video_atlas.cli.main.install_skill")
    def test_main_runs_skill_install(self, mock_install_skill: MagicMock) -> None:
        mock_install_skill.return_value = MagicMock(target_dir="/tmp/skills/mm-harness")
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["skill", "--install"])

        self.assertEqual(exit_code, 0)
        self.assertIn("skill_dir: /tmp/skills/mm-harness", stdout.getvalue())

    @patch("video_atlas.cli.main.uninstall_skill")
    def test_main_runs_skill_uninstall(self, mock_uninstall_skill: MagicMock) -> None:
        mock_uninstall_skill.return_value = MagicMock(removed_paths=["a", "b"])
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["skill", "--uninstall"])

        self.assertEqual(exit_code, 0)
        self.assertIn("removed: 2", stdout.getvalue())

    @patch("video_atlas.cli.main.create_canonical_from_url")
    @patch("video_atlas.cli.main.load_default_canonical_pipeline_config")
    def test_main_runs_create_from_url(
        self,
        mock_load_config: MagicMock,
        mock_create_canonical_from_url: MagicMock,
    ) -> None:
        mock_load_config.return_value = MagicMock(
            runtime=MagicMock(),
            acquisition=MagicMock(),
        )
        atlas = MagicMock()
        atlas.atlas_dir = "/tmp/out/run-url"
        atlas.title = "URL Atlas"
        atlas.execution_plan.output_language = "en"
        atlas.segments = [MagicMock()]
        mock_create_canonical_from_url.return_value = (atlas, {})

        with TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "create",
                        "--url",
                        "https://www.youtube.com/watch?v=abc123xyz89",
                        "--output-dir",
                        tmpdir,
                        "--structure-request",
                        "keep it coarse",
                    ]
                )

        self.assertEqual(exit_code, 0)
        self.assertIn("Creating canonical atlas...", stdout.getvalue())
        self.assertIn("Done", stdout.getvalue())
        self.assertIn("atlas_dir: /tmp/out/run-url", stdout.getvalue())
        mock_create_canonical_from_url.assert_called_once_with(
            "https://www.youtube.com/watch?v=abc123xyz89",
            tmpdir,
            mock_load_config.return_value,
            structure_request="keep it coarse",
            on_progress=ANY,
        )

    @patch("video_atlas.cli.main.create_canonical_from_local")
    @patch("video_atlas.cli.main.load_default_canonical_pipeline_config")
    def test_main_runs_create_from_local_files(
        self,
        mock_load_config: MagicMock,
        mock_create_canonical_from_local: MagicMock,
    ) -> None:
        mock_load_config.return_value = MagicMock(
            runtime=MagicMock(),
            acquisition=MagicMock(),
        )
        atlas = MagicMock()
        atlas.atlas_dir = "/tmp/out/run-001"
        atlas.title = "Local Atlas"
        atlas.execution_plan.output_language = "zh"
        atlas.segments = [MagicMock(), MagicMock()]
        mock_create_canonical_from_local.return_value = (atlas, {})

        with TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
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
        self.assertIn("Creating canonical atlas...", stdout.getvalue())
        self.assertIn("atlas_dir: /tmp/out/run-001", stdout.getvalue())
        self.assertIn("output_language: zh", stdout.getvalue())
        self.assertIn("segments: 2", stdout.getvalue())
        mock_create_canonical_from_local.assert_called_once_with(
            tmpdir,
            mock_load_config.return_value,
            video_file="/tmp/video.mp4",
            audio_file=None,
            subtitle_file="/tmp/subtitles.srt",
            metadata_file="/tmp/metadata.json",
            structure_request="",
            on_progress=ANY,
        )

    @patch("video_atlas.cli.main.create_canonical_from_local")
    @patch("video_atlas.cli.main.load_default_canonical_pipeline_config")
    def test_main_runs_create_from_local_audio_file(
        self,
        mock_load_config: MagicMock,
        mock_create_canonical_from_local: MagicMock,
    ) -> None:
        mock_load_config.return_value = MagicMock(
            runtime=MagicMock(),
            acquisition=MagicMock(),
        )
        atlas = MagicMock()
        atlas.atlas_dir = "/tmp/out/run-002"
        atlas.title = "Audio Atlas"
        atlas.execution_plan.output_language = "en"
        atlas.segments = [MagicMock()]
        mock_create_canonical_from_local.return_value = (atlas, {})

        with TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
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
            on_progress=ANY,
        )

    def test_packaged_default_config_is_loadable(self) -> None:
        from video_atlas.config import load_default_canonical_pipeline_config

        config = load_default_canonical_pipeline_config()

        self.assertEqual(config.planner.model_name, "gpt-5.1")
        self.assertEqual(config.transcriber.backend, "groq_whisper")

    @patch.dict(
        os.environ,
        {
            "LLM_API_BASE_URL": "https://example.test/v1",
            "LLM_API_KEY": "secret-token-1234",
            "GROQ_API_KEY": "gsk_test_123",
            "YOUTUBE_COOKIES_FROM_BROWSER": "chrome",
        },
        clear=False,
    )
    def test_main_runs_doctor(
        self,
    ) -> None:
        with patch("video_atlas.cli.main.shutil.which", side_effect=lambda name: f"/usr/bin/{name}"):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["doctor"])

        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("MM Harness Doctor", output)
        self.assertIn("Required", output)
        self.assertIn("OK    ffmpeg", output)
        self.assertIn("OK    yt-dlp", output)
        self.assertIn("OK    deno", output)
        self.assertIn("OK    LLM_API_BASE_URL", output)
        self.assertIn("OK    LLM_API_KEY", output)
        self.assertIn("OK    GROQ_API_KEY", output)
        self.assertIn("Optional", output)
        self.assertIn("WARN  youtube-cookies", output)

    @patch.dict(
        os.environ,
        {
            "LLM_API_BASE_URL": "",
            "LLM_API_KEY": "",
            "GROQ_API_KEY": "",
            "YOUTUBE_COOKIES_FILE": "",
            "YOUTUBE_COOKIES_FROM_BROWSER": "",
        },
        clear=False,
    )
    def test_main_returns_error_when_doctor_finds_missing_requirements(self) -> None:
        with patch("video_atlas.cli.main.shutil.which", return_value=None):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["doctor"])

        self.assertEqual(exit_code, 2)
        output = stdout.getvalue()
        self.assertIn("FAIL  ffmpeg", output)
        self.assertIn("FAIL  GROQ_API_KEY", output)
        self.assertIn("Hints", output)
        self.assertIn("- ask the user for a Groq API key for transcription, then set GROQ_API_KEY", output)


if __name__ == "__main__":
    unittest.main()
