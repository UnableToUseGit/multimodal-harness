from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4

from video_atlas.config import build_generator, build_transcriber
from video_atlas.config.models import CanonicalPipelineConfig
from video_atlas.schemas import CanonicalCreateRequest, SourceMetadata, SourceInfoRecord
from video_atlas.persistence import write_json_to
from video_atlas.source_acquisition import acquire_from_url
from video_atlas.workflows.canonical_atlas_workflow import CanonicalAtlasWorkflow


@dataclass(frozen=True)
class _MaterializedLocalInputs:
    video_path: Path | None
    audio_path: Path | None
    subtitle_path: Path | None
    source_info: SourceInfoRecord
    source_metadata: SourceMetadata | None


def _build_workflow(config: CanonicalPipelineConfig) -> CanonicalAtlasWorkflow:
    return CanonicalAtlasWorkflow(
        planner=build_generator(config.planner),
        text_segmentor=build_generator(config.text_segmentor) if config.text_segmentor is not None else None,
        multimodal_segmentor=build_generator(config.multimodal_segmentor) if config.multimodal_segmentor is not None else None,
        structure_composer=build_generator(config.structure_composer) if config.structure_composer is not None else None,
        captioner=build_generator(config.captioner) if config.captioner is not None else None,
        transcriber=build_transcriber(config.transcriber),
        generate_subtitles_if_missing=config.runtime.generate_subtitles_if_missing,
        text_chunk_size_sec=config.runtime.text_chunk_size_sec,
        text_chunk_overlap_sec=config.runtime.text_chunk_overlap_sec,
        multimodal_chunk_size_sec=config.runtime.multimodal_chunk_size_sec,
        multimodal_chunk_overlap_sec=config.runtime.multimodal_chunk_overlap_sec,
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
    structure_request: str = "",
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    atlas_dir = output_dir / uuid4().hex
    atlas_dir.mkdir(parents=True, exist_ok=False)
    acquisition_dir = atlas_dir / "input"
    acquisition_dir.mkdir(parents=True, exist_ok=True)
    
    acquisition = acquire_from_url(
        url,
        acquisition_dir,
        prefer_youtube_subtitles=config.acquisition.prefer_youtube_subtitles,
        youtube_output_template=config.acquisition.youtube_output_template,
    )
    
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
    return workflow.create(request)


def create_canonical_from_local(
    output_dir: str | Path,
    config: CanonicalPipelineConfig,
    *,
    video_file: str | Path | None = None,
    audio_file: str | Path | None = None,
    subtitle_file: str | Path | None = None,
    metadata_file: str | Path | None = None,
    structure_request: str = "",
):
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    atlas_dir = output_dir / uuid4().hex
    atlas_dir.mkdir(parents=True, exist_ok=False)
    acquisition_dir = atlas_dir / "input"
    acquisition_dir.mkdir(parents=True, exist_ok=True)
    
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
    return workflow.create(request)
