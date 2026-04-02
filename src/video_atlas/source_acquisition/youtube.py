"""Helpers for validating YouTube URLs and choosing subtitle candidates."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse
from dateutil import parser
from datetime import datetime, timezone

from ..schemas import SourceInfoRecord, SourceAcquisitionResult

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
    def __init__(self, prefer_youtube_subtitles: bool = True, output_template: str = "%(id)s.%(ext)s") -> None:
        self.prefer_youtube_subtitles = prefer_youtube_subtitles
        self.output_template = output_template

    def acquire(self, youtube_url: str, output_dir: Path) -> SourceAcquisitionResult:
        output_dir = Path(output_dir)
        yt_dlp_options: dict[str, object] = {
            "outtmpl": self.output_template,
            "paths": {"home": str(output_dir)},
        }
        if self.prefer_youtube_subtitles:
            yt_dlp_options.update(
                {
                    "writesubtitles": True,
                    "writeautomaticsub": True,
                }
            )
        with yt_dlp.YoutubeDL(yt_dlp_options) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            sanitized_info = ydl.sanitize_info(info)

        video_path = self._resolve_video_path(info, output_dir)
        subtitle_path = self._resolve_subtitle_path(info)
        source_info = SourceInfoRecord(
            source_type="youtube",
            source_url=youtube_url,
            subtitle_source="youtube_caption" if subtitle_path is not None else "missing",
        )
        
        publish_date = parser.parse(sanitized_info.get("upload_date")) if sanitized_info.get("upload_date", "") else datetime(1970, 1, 1)
        thumbnails = [item['url'] for item in sanitized_info.get("thumbnails", [])]
        source_metadata = SourceMetadata(
            title=sanitized_info.get("title", ""),
            introduction=sanitized_info.get("description", ""),
            author=sanitized_info.get("uploader", ""),
            publish_date=publish_date,
            thumbnails=thumbnails
        )
        
        write_json_to(output_dir, "SOURCE_INFO.json", asdict(source_info))
        write_json_to(output_dir, "SOURCE_METADATA.json", source_metadata)

        return SourceAcquisitionResult(
            source_info=source_info,
            source_metadata=source_metadata,
            video_path=video_path,
            subtitles_path=subtitle_path,
        )

    def _resolve_video_path(self, info: dict[str, object], output_dir: Path) -> Path:
        filepath = info.get("filepath") or info.get("_filename")
        if isinstance(filepath, str) and filepath:
            return Path(filepath)

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
            if selected:
                subtitle_filepath = selected.get("filepath")
                if subtitle_filepath:
                    return Path(subtitle_filepath)

            for subtitle in requested_subtitles.values():
                if isinstance(subtitle, dict):
                    subtitle_filepath = subtitle.get("filepath")
                    if subtitle_filepath:
                        return Path(str(subtitle_filepath))

        subtitles = info.get("subtitles")
        if isinstance(subtitles, dict):
            for subtitle_list in subtitles.values():
                if isinstance(subtitle_list, list) and subtitle_list:
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
