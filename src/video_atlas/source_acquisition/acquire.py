from __future__ import annotations

from dataclasses import asdict
import shutil
from pathlib import Path
from uuid import uuid4

from ..persistence import write_json_to
from .xiaoyuzhou import XiaoyuzhouAudioAcquirer
from .youtube import YouTubeVideoAcquirer

from urllib.parse import urlparse
from .xiaoyuzhou import is_supported_xiaoyuzhou_episode_url
from .youtube import is_supported_youtube_watch_url
from ..schemas import SourceAcquisitionResult


class InvalidSourceUrlError(ValueError):
    pass


class UnsupportedSourceError(ValueError):
    pass


def detect_source_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise InvalidSourceUrlError("invalid url")
    if is_supported_youtube_watch_url(url):
        return "youtube"
    if is_supported_xiaoyuzhou_episode_url(url):
        return "xiaoyuzhou"
    raise UnsupportedSourceError("unsupported source")


def acquire_from_url(
    url: str,
    output_dir: str | Path,
    *,
    prefer_youtube_subtitles: bool = True,
    youtube_output_template: str = "%(id)s.%(ext)s",
    max_youtube_video_duration_sec: int = 1500,
    youtube_cookies_file: str | None = None,
    youtube_cookies_from_browser: str | None = None,
) -> SourceAcquisitionResult:
    source_type = detect_source_from_url(url)
    if source_type == "youtube":
        return YouTubeVideoAcquirer(
            prefer_youtube_subtitles=prefer_youtube_subtitles,
            output_template=youtube_output_template,
            max_video_duration_sec=max_youtube_video_duration_sec,
            cookies_file=youtube_cookies_file,
            cookies_from_browser=youtube_cookies_from_browser,
        ).acquire(url, Path(output_dir))
    if source_type == "xiaoyuzhou":
        return XiaoyuzhouAudioAcquirer().acquire(url, Path(output_dir))
    raise RuntimeError(f"Unhandled source type: {source_type}")
