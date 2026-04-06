"""Helpers for YouTube acquisition."""

from __future__ import annotations

from datetime import datetime
import mimetypes
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

from dateutil import parser
import cv2
import requests

from ..persistence import write_json_to
from ..schemas import SourceAcquisitionResult, SourceInfoRecord, SourceMetadata

try:  # pragma: no cover - exercised through mocking in tests
    import yt_dlp  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - kept minimal for environments without yt-dlp
    class _UnavailableYoutubeDL:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            raise ImportError("yt_dlp is required for YouTube acquisition")

    yt_dlp = SimpleNamespace(YoutubeDL=_UnavailableYoutubeDL)


def is_supported_youtube_watch_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    query = parse_qs(parsed.query)

    if parsed.scheme not in {"http", "https"}:
        return False
    if host not in {"youtube.com", "www.youtube.com"}:
        return False
    if parsed.path != "/watch":
        return False
    if "list" in query:
        return False

    video_ids = query.get("v", [])
    return bool(video_ids and video_ids[0].strip())


def choose_subtitle_candidate(candidates: list[dict[str, str]]) -> dict[str, str] | None:
    if not candidates:
        return None

    manual_candidates = [candidate for candidate in candidates if candidate.get("kind") == "manual"]
    if manual_candidates:
        return manual_candidates[0]

    automatic_candidates = [candidate for candidate in candidates if candidate.get("kind") == "automatic"]
    if automatic_candidates:
        return automatic_candidates[0]

    return candidates[0]


class YouTubeVideoAcquirer:
    def __init__(
        self,
        prefer_youtube_subtitles: bool = True,
        output_template: str = "%(id)s.%(ext)s",
        max_video_duration_sec: int = 1500,
        cookies_file: str | None = None,
        cookies_from_browser: str | None = None,
    ) -> None:
        self.prefer_youtube_subtitles = prefer_youtube_subtitles
        self.output_template = output_template
        self.max_video_duration_sec = max_video_duration_sec
        self.cookies_file = cookies_file
        self.cookies_from_browser = cookies_from_browser

    def acquire(self, youtube_url: str, output_dir: Path) -> SourceAcquisitionResult:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        metadata_info = self._extract_metadata(youtube_url)
        source_metadata = self._build_source_metadata(metadata_info)
        should_download_video = self._should_download_video(metadata_info)
        thumbnail_paths = self._download_thumbnails(metadata_info, output_dir)

        download_info = self._download_assets(
            youtube_url=youtube_url,
            output_dir=output_dir,
            should_download_video=should_download_video,
        )
        video_path = self._resolve_video_path(download_info, output_dir) if should_download_video else None
        subtitle_path = self._resolve_subtitle_path(download_info)

        source_info = SourceInfoRecord(
            source_type="youtube",
            source_url=youtube_url,
            subtitle_source="youtube_caption" if subtitle_path is not None else "missing",
        )
        write_json_to(output_dir, "SOURCE_INFO.json", source_info.to_dict())
        write_json_to(output_dir, "SOURCE_METADATA.json", source_metadata.to_dict())

        return SourceAcquisitionResult(
            source_info=source_info,
            source_metadata=source_metadata,
            video_path=video_path,
            subtitles_path=subtitle_path,
            artifacts={"thumbnail_dir": output_dir / "thumbnails"} if thumbnail_paths else {},
        )

    def _extract_metadata(self, youtube_url: str) -> dict[str, object]:
        with yt_dlp.YoutubeDL(self._build_common_options(skip_download=True)) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return ydl.sanitize_info(info)

    def _download_assets(
        self,
        *,
        youtube_url: str,
        output_dir: Path,
        should_download_video: bool,
    ) -> dict[str, object]:
        yt_dlp_options = self._build_common_options(skip_download=not should_download_video)
        yt_dlp_options.update({
            "outtmpl": self.output_template,
            "paths": {"home": str(output_dir)},
        })
        if self.prefer_youtube_subtitles:
            yt_dlp_options["writesubtitles"] = True
            yt_dlp_options["writeautomaticsub"] = True

        with yt_dlp.YoutubeDL(yt_dlp_options) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            return ydl.sanitize_info(info)

    def _build_common_options(self, *, skip_download: bool) -> dict[str, object]:
        options: dict[str, object] = {"skip_download": skip_download}
        if self.cookies_file:
            options["cookiefile"] = self.cookies_file
        if self.cookies_from_browser:
            options["cookiesfrombrowser"] = self.cookies_from_browser
        return options

    def _should_download_video(self, metadata_info: dict[str, object]) -> bool:
        duration = metadata_info.get("duration")
        if not isinstance(duration, (int, float)):
            return True
        return float(duration) <= float(self.max_video_duration_sec)

    def _build_source_metadata(self, info: dict[str, object]) -> SourceMetadata:
        upload_date = info.get("upload_date")
        publish_date = parser.parse(str(upload_date)) if upload_date else datetime(1970, 1, 1)
        thumbnails = [
            str(item.get("url"))
            for item in info.get("thumbnails", [])
            if isinstance(item, dict) and item.get("url")
        ]
        return SourceMetadata(
            title=str(info.get("title", "")),
            introduction=str(info.get("description", "")),
            author=str(info.get("uploader") or info.get("channel") or ""),
            publish_date=publish_date,
            duration_seconds=float(info.get("duration") or 0),
            thumbnails=thumbnails,
        )

    def _download_thumbnails(self, info: dict[str, object], output_dir: Path) -> list[Path]:
        thumbnail_urls = [
            str(item.get("url"))
            for item in info.get("thumbnails", [])
            if isinstance(item, dict) and item.get("url")
        ]
        thumbnail_dir = output_dir / "thumbnails"
        downloaded_paths: list[Path] = []
        for index, thumbnail_url in enumerate(thumbnail_urls, start=1):
            try:
                response = requests.get(thumbnail_url, timeout=30)
                response.raise_for_status()
            except requests.RequestException:
                continue

            extension = self._resolve_thumbnail_extension(thumbnail_url, response.headers.get("Content-Type", ""))
            thumbnail_dir.mkdir(parents=True, exist_ok=True)
            dimensions = self._read_image_dimensions(response.content, extension)
            if dimensions is not None:
                width, height = dimensions
                thumbnail_path = thumbnail_dir / f"thumb_{index:03d}_{width}x{height}{extension}"
            else:
                thumbnail_path = thumbnail_dir / f"thumb_{index:03d}{extension}"
            thumbnail_path.write_bytes(response.content)
            downloaded_paths.append(thumbnail_path)
        return downloaded_paths

    def _resolve_thumbnail_extension(self, url: str, content_type: str) -> str:
        url_suffix = Path(urlparse(url).path).suffix.lower()
        if url_suffix in {".jpg", ".jpeg", ".png", ".webp"}:
            return url_suffix

        guessed_extension = mimetypes.guess_extension(content_type.split(";", 1)[0].strip()) if content_type else None
        if guessed_extension in {".jpg", ".jpeg", ".png", ".webp"}:
            return guessed_extension
        return ".jpg"

    def _read_image_dimensions(self, image_bytes: bytes, extension: str) -> tuple[int, int] | None:
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp_file:
            tmp_file.write(image_bytes)
            tmp_path = Path(tmp_file.name)

        try:
            image = cv2.imread(str(tmp_path))
            if image is None:
                return None
            height, width = image.shape[:2]
            return int(width), int(height)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _resolve_video_path(self, info: dict[str, object], output_dir: Path) -> Path:
        filepath = info.get("filepath") or info.get("_filename")
        if isinstance(filepath, str) and filepath:
            return Path(filepath)

        requested_downloads = info.get("requested_downloads")
        if isinstance(requested_downloads, list):
            for item in requested_downloads:
                if isinstance(item, dict):
                    candidate = item.get("filepath") or item.get("_filename")
                    if isinstance(candidate, str) and candidate:
                        return Path(candidate)

        video_id = str(info.get("id", "video"))
        extension = str(info.get("ext", "mp4"))
        return output_dir / self.output_template.replace("%(id)s", video_id).replace("%(ext)s", extension)

    def _resolve_subtitle_path(self, info: dict[str, object]) -> Path | None:
        requested_subtitles = info.get("requested_subtitles")
        if isinstance(requested_subtitles, dict):
            selected = choose_subtitle_candidate(
                [
                    {
                        "kind": "automatic" if subtitle.get("is_auto") else "manual",
                        "filepath": str(subtitle.get("filepath", "")),
                        "language": language,
                        "ext": str(subtitle.get("ext", "")),
                    }
                    for language, subtitle in requested_subtitles.items()
                    if isinstance(subtitle, dict)
                ]
            )
            if selected and selected.get("filepath"):
                return Path(selected["filepath"])

            for subtitle in requested_subtitles.values():
                if isinstance(subtitle, dict) and subtitle.get("filepath"):
                    return Path(str(subtitle["filepath"]))

        subtitles = info.get("subtitles")
        if isinstance(subtitles, dict):
            for subtitle_list in subtitles.values():
                if not isinstance(subtitle_list, list) or not subtitle_list:
                    continue
                candidate = choose_subtitle_candidate(
                    [
                        {
                            "kind": "automatic" if subtitle.get("is_auto") else "manual",
                            "filepath": str(subtitle.get("filepath", "")),
                            "language": str(subtitle.get("language", "")),
                            "ext": str(subtitle.get("ext", "")),
                        }
                        for subtitle in subtitle_list
                        if isinstance(subtitle, dict)
                    ]
                )
                if candidate and candidate.get("filepath"):
                    return Path(candidate["filepath"])

        return None
