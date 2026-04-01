from __future__ import annotations

from dataclasses import asdict
import shutil
from pathlib import Path
from uuid import uuid4

from ..persistence import write_json_to
from .detection import detect_source_from_url
from .models import SourceAcquisitionResult
from .youtube import YouTubeVideoAcquirer


def acquire_from_url(
    url: str,
    output_dir: str | Path,
    *,
    prefer_youtube_subtitles: bool = True,
    youtube_output_template: str = "%(id)s.%(ext)s",
) -> SourceAcquisitionResult:
    source_type = detect_source_from_url(url)
    if source_type == "youtube":
        return YouTubeVideoAcquirer(
            prefer_youtube_subtitles=prefer_youtube_subtitles,
            output_template=youtube_output_template,
        ).acquire(url, Path(output_dir))
    raise RuntimeError(f"Unhandled source type: {source_type}")


def create_acquisition_subdir(output_dir: str | Path) -> Path:
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    output_path = output_root / uuid4().hex
    output_path.mkdir(parents=True, exist_ok=False)
    return output_path


def materialize_fetch_workspace(acquisition: SourceAcquisitionResult, output_dir: str | Path) -> Path:
    output_path = create_acquisition_subdir(output_dir)

    target_video_path = output_path / "video.mp4"
    if acquisition.local_video_path.resolve() != target_video_path.resolve():
        shutil.copy2(acquisition.local_video_path, target_video_path)

    if acquisition.local_subtitles_path is not None:
        target_subtitles_path = output_path / "subtitles.srt"
        if acquisition.local_subtitles_path.resolve() != target_subtitles_path.resolve():
            shutil.copy2(acquisition.local_subtitles_path, target_subtitles_path)

    write_json_to(output_path, "SOURCE_INFO.json", asdict(acquisition.source_info))
    write_json_to(output_path, "SOURCE_METADATA.json", acquisition.source_metadata)
    return output_path
