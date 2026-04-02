from __future__ import annotations

import json
import re
from datetime import datetime
from html import unescape
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from dateutil import parser

from ..persistence import write_json_to
from ..schemas import SourceAcquisitionResult, SourceInfoRecord, SourceMetadata


_AUDIO_URL_RE = re.compile(r'https://media\.xyzcdn\.net/[^"]*\.(?:m4a|mp3)')
_TITLE_RE = re.compile(r'"title":"([^"]*)"')
_NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.DOTALL)
_LD_JSON_RE = re.compile(r'<script name="schema:podcast-show" type="application/ld\+json">(.*?)</script>', re.DOTALL)


def is_supported_xiaoyuzhou_episode_url(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.scheme in {"http", "https"}
        and parsed.netloc.lower() in {"www.xiaoyuzhoufm.com", "xiaoyuzhoufm.com"}
        and parsed.path.startswith("/episode/")
    )


def extract_audio_url_from_page(page: str) -> str | None:
    next_data = extract_next_data_from_page(page)
    if next_data is not None:
        episode = _extract_episode(next_data)
        enclosure = episode.get("enclosure")
        if isinstance(enclosure, dict) and enclosure.get("url"):
            return str(enclosure["url"])
        media = episode.get("media")
        if isinstance(media, dict):
            source = media.get("source")
            if isinstance(source, dict) and source.get("url"):
                return str(source["url"])

    match = _AUDIO_URL_RE.search(page)
    return match.group(0) if match else None


def extract_title_from_page(page: str) -> str | None:
    next_data = extract_next_data_from_page(page)
    if next_data is not None:
        episode = _extract_episode(next_data)
        title = episode.get("title")
        if isinstance(title, str) and title:
            return title

    match = _TITLE_RE.search(page)
    return unescape(match.group(1)) if match else None


def extract_next_data_from_page(page: str) -> dict[str, object] | None:
    match = _NEXT_DATA_RE.search(page)
    if not match:
        return None
    return json.loads(match.group(1))


def extract_ld_json_from_page(page: str) -> dict[str, object] | None:
    match = _LD_JSON_RE.search(page)
    if not match:
        return None
    return json.loads(match.group(1))


def _extract_episode(next_data: dict[str, object]) -> dict[str, object]:
    props = next_data.get("props")
    if not isinstance(props, dict):
        return {}
    page_props = props.get("pageProps")
    if not isinstance(page_props, dict):
        return {}
    episode = page_props.get("episode")
    return episode if isinstance(episode, dict) else {}


def _collect_image_urls(*image_blocks: object) -> list[str]:
    urls: list[str] = []
    for block in image_blocks:
        if not isinstance(block, dict):
            continue
        for key in ("picUrl", "thumbnailUrl", "smallPicUrl", "middlePicUrl", "largePicUrl"):
            value = block.get(key)
            if isinstance(value, str) and value and value not in urls:
                urls.append(value)
    return urls


class XiaoyuzhouAudioAcquirer:
    def acquire(self, episode_url: str, output_dir: Path) -> SourceAcquisitionResult:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        page = self._read_text(episode_url)
        audio_url = extract_audio_url_from_page(page)
        if not audio_url:
            raise ValueError("failed to extract xiaoyuzhou audio url")

        source_metadata = self._build_source_metadata(page)
        suffix = Path(urlparse(audio_url).path).suffix or ".m4a"
        audio_path = output_dir / f"audio{suffix}"
        self._download_binary(audio_url, audio_path)

        source_info = SourceInfoRecord(
            source_type="xiaoyuzhou",
            source_url=episode_url,
            subtitle_source="missing",
        )
        write_json_to(output_dir, "SOURCE_INFO.json", source_info.to_dict())
        write_json_to(output_dir, "SOURCE_METADATA.json", source_metadata.to_dict())

        return SourceAcquisitionResult(
            source_info=source_info,
            audio_path=audio_path,
            source_metadata=source_metadata,
        )

    def _build_source_metadata(self, page: str) -> SourceMetadata:
        next_data = extract_next_data_from_page(page)
        ld_json = extract_ld_json_from_page(page)
        episode = _extract_episode(next_data or {})

        title = str(episode.get("title") or (ld_json or {}).get("name") or "")
        introduction = str(
            episode.get("description")
            or (ld_json or {}).get("description")
            or episode.get("shownotes")
            or ""
        )
        podcast = episode.get("podcast")
        podcast_author = podcast.get("author") if isinstance(podcast, dict) else None
        author = str(podcast_author or "")
        publish_raw = episode.get("pubDate") or (ld_json or {}).get("datePublished")
        publish_date = parser.parse(str(publish_raw)) if publish_raw else datetime(1970, 1, 1)
        duration_seconds = float(episode.get("duration") or 0)

        episode_image = episode.get("image")
        podcast_image = podcast.get("image") if isinstance(podcast, dict) else None
        thumbnails = _collect_image_urls(episode_image, podcast_image)

        return SourceMetadata(
            title=title,
            introduction=introduction,
            author=author,
            publish_date=publish_date,
            duration_seconds=duration_seconds,
            thumbnails=thumbnails,
        )

    def _read_text(self, url: str) -> str:
        with urlopen(url) as response:  # noqa: S310
            return response.read().decode("utf-8", errors="replace")

    def _download_binary(self, url: str, destination: Path) -> None:
        with urlopen(url) as response:  # noqa: S310
            destination.write_bytes(response.read())
