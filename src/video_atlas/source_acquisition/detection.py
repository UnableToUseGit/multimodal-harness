from __future__ import annotations

from urllib.parse import urlparse

from .youtube import is_supported_youtube_watch_url


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
    raise UnsupportedSourceError("unsupported source")
