import os
import tempfile
import unittest
from pathlib import Path

from video_atlas.settings import ENV_API_BASE, ENV_API_KEY, Settings, load_dotenv


class SettingsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.original = {
            ENV_API_BASE: os.environ.get(ENV_API_BASE),
            ENV_API_KEY: os.environ.get(ENV_API_KEY),
        }
        for key in self.original:
            os.environ.pop(key, None)

    def tearDown(self) -> None:
        for key in self.original:
            os.environ.pop(key, None)
        for key, value in self.original.items():
            if value is not None:
                os.environ[key] = value

    def test_load_dotenv_populates_missing_environment_variables(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dotenv_path = Path(tmpdir) / ".env"
            dotenv_path.write_text(
                "\n".join(
                    [
                        "VIDEO_ATLAS_API_BASE=https://example.test/v1",
                        "VIDEO_ATLAS_API_KEY=secret-token-1234",
                    ]
                ),
                encoding="utf-8",
            )

            load_dotenv(dotenv_path)

        self.assertEqual(os.environ[ENV_API_BASE], "https://example.test/v1")
        self.assertEqual(os.environ[ENV_API_KEY], "secret-token-1234")

    def test_masked_api_key(self) -> None:
        settings = Settings(api_base="https://example.test/v1", api_key="secret-token-1234")
        self.assertEqual(settings.masked_api_key, "secr...1234")


if __name__ == "__main__":
    unittest.main()
