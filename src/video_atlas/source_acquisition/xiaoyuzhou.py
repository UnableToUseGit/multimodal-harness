from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from ..schemas import SourceInfoRecord, SourceAcquisitionResult


_AUDIO_URL_RE = re.compile(r'https://media\.xyzcdn\.net/[^"]*\.(?:m4a|mp3)')
_TITLE_RE = re.compile(r'"title":"([^"]*)"')


def is_supported_xiaoyuzhou_episode_url(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.scheme in {"http", "https"}
        and parsed.netloc.lower() in {"www.xiaoyuzhoufm.com", "xiaoyuzhoufm.com"}
        and parsed.path.startswith("/episode/")
    )


def extract_audio_url_from_page(page: str) -> str | None:
    match = _AUDIO_URL_RE.search(page)
    return match.group(0) if match else None


def extract_title_from_page(page: str) -> str | None:
    match = _TITLE_RE.search(page)
    return match.group(1) if match else None


class XiaoyuzhouAudioAcquirer:
    def acquire(self, episode_url: str, output_dir: Path) -> SourceAcquisitionResult:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        page = self._read_text(episode_url)
        audio_url = extract_audio_url_from_page(page)
        if not audio_url:
            raise ValueError("failed to extract xiaoyuzhou audio url")

        title = extract_title_from_page(page)
        suffix = Path(urlparse(audio_url).path).suffix or ".m4a"
        audio_path = output_dir / f"audio{suffix}"
        self._download_binary(audio_url, audio_path)

        return SourceAcquisitionResult(
            source_info=SourceInfoRecord(
                source_type="xiaoyuzhou",
                source_url=episode_url,
                canonical_source_url=episode_url,
                subtitle_source="missing",
                subtitle_fallback_required=True,
            ),
            audio_path=audio_path,
            source_metadata={
                "title": title or "",
                "webpage_url": episode_url,
                "audio_url": audio_url,
            },
        )

    def _read_text(self, url: str) -> str:
        with urlopen(url) as response:  # noqa: S310
            return response.read().decode("utf-8", errors="replace")

    def _download_binary(self, url: str, destination: Path) -> None:
        with urlopen(url) as response:  # noqa: S310
            destination.write_bytes(response.read())
