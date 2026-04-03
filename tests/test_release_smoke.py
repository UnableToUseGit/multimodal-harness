import io
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from video_atlas.cli.main import main


ROOT = os.path.dirname(os.path.dirname(__file__))


class ReleaseSmokeTest(unittest.TestCase):
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

    def test_info_entrypoint_smoke(self) -> None:
        result = self._run_cli("info")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("MM Harness", result.stdout)
        self.assertIn("version", result.stdout)

    def test_create_help_entrypoint_smoke(self) -> None:
        result = self._run_cli("create", "--help")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--url", result.stdout)
        self.assertIn("--video-file", result.stdout)
        self.assertIn("--audio-file", result.stdout)
        self.assertIn("--subtitle-file", result.stdout)
        self.assertIn("--output-dir", result.stdout)

    def test_doctor_entrypoint_smoke(self) -> None:
        stdout = io.StringIO()
        with patch("video_atlas.cli.main.shutil.which", side_effect=lambda name: f"/usr/bin/{name}"):
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
        output = stdout.getvalue()
        self.assertIn("MM Harness Doctor", output)
        self.assertIn("Required", output)
        self.assertIn("Optional", output)


if __name__ == "__main__":
    unittest.main()
