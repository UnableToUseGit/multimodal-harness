import os
import subprocess
import sys
import unittest


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


if __name__ == "__main__":
    unittest.main()
