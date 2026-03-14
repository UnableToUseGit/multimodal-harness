from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


ENV_API_BASE = "VIDEO_ATLAS_API_BASE"
ENV_API_KEY = "VIDEO_ATLAS_API_KEY"
ENV_MODEL = "VIDEO_ATLAS_MODEL"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _parse_dotenv(dotenv_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not dotenv_path.exists():
        return values

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        values[key] = value

    return values


def load_dotenv(dotenv_path: Path | None = None, override: bool = False) -> dict[str, str]:
    path = dotenv_path or (_repo_root() / ".env")
    loaded = _parse_dotenv(path)
    for key, value in loaded.items():
        if override or key not in os.environ:
            os.environ[key] = value
    return loaded


@dataclass(frozen=True)
class Settings:
    api_base: str | None = None
    api_key: str | None = None
    model: str | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_base and self.api_key and self.model)

    @property
    def masked_api_key(self) -> str:
        if not self.api_key:
            return "<missing>"
        if len(self.api_key) <= 8:
            return "*" * len(self.api_key)
        return f"{self.api_key[:4]}...{self.api_key[-4:]}"


def get_settings(load_local_env: bool = True) -> Settings:
    if load_local_env:
        load_dotenv()

    return Settings(
        api_base=os.getenv(ENV_API_BASE),
        api_key=os.getenv(ENV_API_KEY),
        model=os.getenv(ENV_MODEL),
    )
