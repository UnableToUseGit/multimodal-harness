from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
from uuid import uuid4

from video_atlas.config import build_generator, build_transcriber
from video_atlas.config.models import CanonicalPipelineConfig
from video_atlas.persistence.writers import slugify_segment_title
from video_atlas.schemas import CanonicalCreateRequest, SourceMetadata, SourceInfoRecord
from video_atlas.persistence import write_json_to
from video_atlas.source_acquisition import acquire_from_url
from video_atlas.workflows.text_first_canonical_atlas_workflow import TextFirstCanonicalAtlasWorkflow


@dataclass(frozen=True)
class _MaterializedLocalInputs:
    video_path: Path | None
    audio_path: Path | None
    subtitle_path: Path | None
    source_info: SourceInfoRecord
    source_metadata: SourceMetadata | None


def _validate_requested_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("name must not be empty")
    if any(separator in cleaned for separator in ("/", "\\")):
        raise ValueError("name must not contain path separators")
    if cleaned in {".", ".."}:
        raise ValueError("name must not be '.' or '..'")
    return cleaned


def _suggest_atlas_dir_name(
    *,
    requested_name: str | None = None,
    source_title: str | None = None,
    source_path: str | Path | None = None,
) -> str:
    if requested_name is not None:
        return _validate_requested_name(requested_name)

    base_name = (source_title or "").strip()
    if not base_name and source_path is not None:
        base_name = Path(source_path).stem.strip()
    slug = slugify_segment_title(base_name) if base_name else "atlas"
    slug = (slug or "atlas")[:60].strip("-") or "atlas"
    return f"{slug}-{uuid4().hex[:8]}"


def _relocate_path(original_root: Path, final_root: Path, path: Path | None) -> Path | None:
    if path is None:
        return None
    try:
        relative = path.relative_to(original_root)
    except ValueError:
        return path
    return final_root / relative


def _relocate_acquisition_result(original_root: Path, final_root: Path, acquisition):
    acquisition.video_path = _relocate_path(original_root, final_root, acquisition.video_path)
    acquisition.audio_path = _relocate_path(original_root, final_root, acquisition.audio_path)
    acquisition.subtitles_path = _relocate_path(original_root, final_root, acquisition.subtitles_path)
    acquisition.artifacts = {
        key: _relocate_path(original_root, final_root, value)
        for key, value in acquisition.artifacts.items()
    }
    return acquisition


def _build_workflow(config: CanonicalPipelineConfig) -> TextFirstCanonicalAtlasWorkflow:
    text_segmentor = config.text_segmentor or config.segmentor
    return TextFirstCanonicalAtlasWorkflow(
        planner=build_generator(config.planner),
        text_segmentor=build_generator(text_segmentor) if text_segmentor is not None else None,
        structure_composer=build_generator(config.structure_composer) if config.structure_composer is not None else None,
        captioner=build_generator(config.captioner) if config.captioner is not None else None,
        transcriber=build_transcriber(config.transcriber),
        generate_subtitles_if_missing=config.runtime.generate_subtitles_if_missing,
        chunk_size_sec=config.runtime.text_chunk_size_sec,
        chunk_overlap_sec=config.runtime.text_chunk_overlap_sec,
        caption_with_subtitles=config.runtime.caption_with_subtitles,
        verbose=config.runtime.verbose,
    )


def _materialize_local_inputs(
    acquisition_dir: str | Path,
    *,
    video_file: str | Path | None = None,
    audio_file: str | Path | None = None,
    subtitle_file: str | Path | None = None,
    metadata_file: str | Path | None = None,
) -> _MaterializedLocalInputs:
    acquisition_dir = Path(acquisition_dir)
    acquisition_dir.mkdir(parents=True, exist_ok=True)

    video_path: Path | None = None
    audio_path: Path | None = None
    subtitle_path: Path | None = None
    source_metadata: SourceMetadata | None = None

    if video_file is not None:
        source = Path(video_file)
        video_path = shutil.copy2(source, acquisition_dir / source.name)
        video_path = Path(video_path)
    if audio_file is not None:
        source = Path(audio_file)
        audio_path = shutil.copy2(source, acquisition_dir / source.name)
        audio_path = Path(audio_path)
    if subtitle_file is not None:
        source = Path(subtitle_file)
        subtitle_path = shutil.copy2(source, acquisition_dir / source.name)
        subtitle_path = Path(subtitle_path)
    if metadata_file is not None:
        source = Path(metadata_file)
        payload = json.loads(source.read_text(encoding="utf-8"))
        source_metadata = SourceMetadata.from_dict(payload)
        write_json_to(acquisition_dir, "SOURCE_METADATA.json", source_metadata.to_dict())

    source_info = SourceInfoRecord(
        source_type="local",
        source_url=None,
        subtitle_source="local" if subtitle_file is not None else "missing",
    )

    return _MaterializedLocalInputs(
        video_path=video_path,
        audio_path=audio_path,
        subtitle_path=subtitle_path,
        source_info=source_info,
        source_metadata=source_metadata,
    )


def create_canonical_from_url(
    url: str,
    output_dir: str | Path,
    config: CanonicalPipelineConfig,
    *,
    name: str | None = None,
    structure_request: str = "",
    on_progress: Callable[[str], None] | None = None,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    staging_dir = output_dir / f".staging-{uuid4().hex}"
    staging_dir.mkdir(parents=True, exist_ok=False)
    acquisition_dir = staging_dir / "input"
    acquisition_dir.mkdir(parents=True, exist_ok=True)

    if on_progress is not None:
        on_progress("Acquiring source assets from URL...")

    acquisition = acquire_from_url(
        url,
        acquisition_dir,
        prefer_youtube_subtitles=config.acquisition.prefer_youtube_subtitles,
        youtube_output_template=config.acquisition.youtube_output_template,
        max_youtube_video_duration_sec=config.acquisition.max_youtube_video_duration_sec,
        youtube_cookies_file=config.acquisition.youtube_cookies_file,
        youtube_cookies_from_browser=config.acquisition.youtube_cookies_from_browser,
    )
    atlas_dir = output_dir / _suggest_atlas_dir_name(
        requested_name=name,
        source_title=acquisition.source_metadata.title if acquisition.source_metadata is not None else None,
    )
    if atlas_dir.exists():
        raise FileExistsError(f"atlas output directory already exists: {atlas_dir}")
    shutil.move(str(staging_dir), str(atlas_dir))
    acquisition = _relocate_acquisition_result(staging_dir, atlas_dir, acquisition)

    request = CanonicalCreateRequest(
        atlas_dir=atlas_dir,
        video_path=acquisition.video_path,
        audio_path=acquisition.audio_path,
        subtitle_path=acquisition.subtitles_path,
        structure_request=structure_request,
        source_info=acquisition.source_info,
        source_metadata=acquisition.source_metadata,
    )
    workflow = _build_workflow(config)
    return workflow.create(request, on_progress=on_progress)


def create_canonical_from_local(
    output_dir: str | Path,
    config: CanonicalPipelineConfig,
    *,
    name: str | None = None,
    video_file: str | Path | None = None,
    audio_file: str | Path | None = None,
    subtitle_file: str | Path | None = None,
    metadata_file: str | Path | None = None,
    structure_request: str = "",
    on_progress: Callable[[str], None] | None = None,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    source_path = video_file or audio_file or subtitle_file
    source_title: str | None = None
    if metadata_file is not None:
        payload = json.loads(Path(metadata_file).read_text(encoding="utf-8"))
        source_title = str(payload.get("title", "")).strip() or None
    atlas_dir = output_dir / _suggest_atlas_dir_name(
        requested_name=name,
        source_title=source_title,
        source_path=source_path,
    )
    atlas_dir.mkdir(parents=True, exist_ok=False)
    acquisition_dir = atlas_dir / "input"
    acquisition_dir.mkdir(parents=True, exist_ok=True)

    if on_progress is not None:
        on_progress("Preparing local input assets...")

    materialized_inputs = _materialize_local_inputs(
        acquisition_dir,
        video_file=video_file,
        audio_file=audio_file,
        subtitle_file=subtitle_file,
        metadata_file=metadata_file,
    )
    
    request = CanonicalCreateRequest(
        atlas_dir=atlas_dir,
        video_path=materialized_inputs.video_path,
        audio_path=materialized_inputs.audio_path,
        subtitle_path=materialized_inputs.subtitle_path,
        structure_request=structure_request,
        source_info=materialized_inputs.source_info,
        source_metadata=materialized_inputs.source_metadata,
    )
    workflow = _build_workflow(config)
    return workflow.create(request, on_progress=on_progress)
