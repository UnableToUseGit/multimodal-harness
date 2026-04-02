import os
import tempfile
import unittest
from pathlib import Path

from video_atlas.settings import (
    ENV_API_BASE,
    ENV_API_KEY,
    ENV_LOCAL_API_BASE,
    ENV_LOCAL_API_KEY,
    ENV_REMOTE_API_BASE,
    ENV_REMOTE_API_KEY,
    Settings,
    get_settings,
    load_dotenv,
)


class SettingsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.original = {
            ENV_API_BASE: os.environ.get(ENV_API_BASE),
            ENV_API_KEY: os.environ.get(ENV_API_KEY),
            ENV_LOCAL_API_BASE: os.environ.get(ENV_LOCAL_API_BASE),
            ENV_LOCAL_API_KEY: os.environ.get(ENV_LOCAL_API_KEY),
            ENV_REMOTE_API_BASE: os.environ.get(ENV_REMOTE_API_BASE),
            ENV_REMOTE_API_KEY: os.environ.get(ENV_REMOTE_API_KEY),
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
                        "LOCAL_API_BASE=https://local.example.test/v1",
                        "LOCAL_API_KEY=local-secret-token",
                        "REMOTE_API_BASE=https://remote.example.test/v1",
                        "REMOTE_API_KEY=remote-secret-token",
                    ]
                ),
                encoding="utf-8",
            )

            load_dotenv(dotenv_path)

        self.assertEqual(os.environ[ENV_LOCAL_API_BASE], "https://local.example.test/v1")
        self.assertEqual(os.environ[ENV_LOCAL_API_KEY], "local-secret-token")
        self.assertEqual(os.environ[ENV_REMOTE_API_BASE], "https://remote.example.test/v1")
        self.assertEqual(os.environ[ENV_REMOTE_API_KEY], "remote-secret-token")

    def test_get_settings_supports_local_remote_and_default_connections(self) -> None:
        os.environ[ENV_API_BASE] = "https://default.example.test/v1"
        os.environ[ENV_API_KEY] = "default-secret-token"
        os.environ[ENV_LOCAL_API_BASE] = "https://local.example.test/v1"
        os.environ[ENV_LOCAL_API_KEY] = "local-secret-token"
        os.environ[ENV_REMOTE_API_BASE] = "https://remote.example.test/v1"
        os.environ[ENV_REMOTE_API_KEY] = "remote-secret-token"

        default_settings = get_settings(connection="default", load_local_env=False)
        local_settings = get_settings(connection="local", load_local_env=False)
        remote_settings = get_settings(connection="remote", load_local_env=False)

        self.assertEqual(default_settings.api_base, "https://default.example.test/v1")
        self.assertEqual(default_settings.api_key, "default-secret-token")
        self.assertEqual(local_settings.api_base, "https://local.example.test/v1")
        self.assertEqual(local_settings.api_key, "local-secret-token")
        self.assertEqual(remote_settings.api_base, "https://remote.example.test/v1")
        self.assertEqual(remote_settings.api_key, "remote-secret-token")

    def test_masked_api_key(self) -> None:
        settings = Settings(api_base="https://example.test/v1", api_key="secret-token-1234")
        self.assertEqual(settings.masked_api_key, "secr...1234")


if __name__ == "__main__":
    unittest.main()
