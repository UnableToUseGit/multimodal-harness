from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from ...persistence import CanonicalAtlasWriter, write_text_to
from ...persistence import format_hms_time_range, slugify_segment_title
from ...schemas import CanonicalAtlas, CanonicalCreateRequest
from ...utils import parse_srt
from ...utils.video_metadata import seconds_to_hms
from .structure_composition import compose_canonical_structure
from .language import resolve_atlas_language
from .parsing import build_text_units
from .plan import build_text_first_execution_plan
from .subtitle_preparation import resolve_subtitle_assets


def _serialize_source_metadata(source_metadata):
    if source_metadata is None:
        return {}
    if hasattr(source_metadata, "to_dict"):
        return source_metadata.to_dict()
    if hasattr(source_metadata, "__dataclass_fields__"):
        return asdict(source_metadata)
    return dict(source_metadata)


class TextFirstPipelineMixin:
    def _notify_progress(self, on_progress: Callable[[str], None] | None, message: str) -> None:
        if on_progress is not None:
            on_progress(message)

    def _finalize_composed_segments(self, composition_result):
        normalized_segments = []
        for segment in composition_result.segments:
            folder_name = segment.folder_name or (
                f"{segment.segment_id.replace('_', '-')}-"
                f"{slugify_segment_title(segment.title or segment.segment_id)}-"
                f"{format_hms_time_range(segment.start_time, segment.end_time)}"
            )
            normalized_segments.append(
                type(segment)(
                    segment_id=segment.segment_id,
                    unit_ids=list(segment.unit_ids),
                    title=segment.title,
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    summary=segment.summary,
                    composition_rationale=segment.composition_rationale,
                    folder_name=folder_name,
                    caption=segment.caption,
                    subtitles_text=segment.subtitles_text,
                    relative_clip_path=segment.relative_clip_path,
                    relative_subtitles_path=segment.relative_subtitles_path,
                )
            )
        return normalized_segments

    def _relative_path(self, atlas_dir: Path, source_path: Path | None) -> Path | None:
        if source_path is None:
            return None
        try:
            return source_path.relative_to(atlas_dir)
        except ValueError:
            return Path(source_path.name)

    def _resolve_duration(self, request: CanonicalCreateRequest, subtitle_items: list[dict[str, object]]) -> float:
        if request.video_path is not None and request.video_path.exists():
            try:
                from ...utils import get_video_property

                video_info = get_video_property(request.video_path)
                duration = float(video_info.get("duration", 0.0) or 0.0)
                if duration > 0:
                    return duration
            except Exception:
                pass

        if subtitle_items:
            duration = 0.0
            for item in subtitle_items:
                try:
                    duration = max(duration, float(item.get("end", 0.0) or 0.0))
                except Exception:
                    continue
            if duration > 0:
                return duration

        return 0.0

    def _write_text_only_workspace(self, atlas: CanonicalAtlas, subtitles_text: str) -> None:
        caption_with_subtitles = getattr(self, "caption_with_subtitles", True)
        writer = CanonicalAtlasWriter(caption_with_subtitles=caption_with_subtitles)
        units_by_id = {unit.unit_id: unit for unit in atlas.units}

        readme_text = "\n".join(
            [
                "# Text-First Canonical Atlas",
                "",
                f"**Title**: {atlas.title}",
                f"**Duration**: {seconds_to_hms(atlas.duration)}",
                f"**Abstract**: {atlas.abstract}",
                f"**Profile**: {atlas.execution_plan.profile_name}",
                f"**Route**: {atlas.execution_plan.profile.route}",
                "",
                "# Structure Context",
                f"There are {len(atlas.units)} units extracted from the prepared subtitles.",
                f"There are {len(atlas.segments)} final composed segments generated from those units.",
                "- All original units are saved in `./units`.",
                "- Final composed segments are saved in `./segments`.",
                "- Each segment folder contains its own `README.md` and a copied view of the units it is composed from.",
                "",
                "# Additional Files",
                "- Prepared subtitles: `./SUBTITLES.md`",
                "- Subtitle source file: `./input/subtitles.srt`",
            ]
        )
        write_text_to(atlas.atlas_dir, "README.md", readme_text)
        if subtitles_text and caption_with_subtitles:
            write_text_to(atlas.atlas_dir, "SUBTITLES.md", subtitles_text)

        for unit in atlas.units:
            unit_dir = Path("units") / unit.folder_name
            write_text_to(atlas.atlas_dir, unit_dir / "README.md", writer._unit_readme_text(unit))
            if caption_with_subtitles and unit.subtitles_text:
                write_text_to(atlas.atlas_dir, unit_dir / "SUBTITLES.md", unit.subtitles_text)

        for segment in atlas.segments:
            segment_dir = Path("segments") / segment.folder_name
            composed_units = [units_by_id[unit_id] for unit_id in segment.unit_ids if unit_id in units_by_id]
            write_text_to(atlas.atlas_dir, segment_dir / "README.md", writer._segment_readme_text(segment, composed_units))
            if caption_with_subtitles and segment.subtitles_text:
                write_text_to(atlas.atlas_dir, segment_dir / "SUBTITLES.md", segment.subtitles_text)
            for unit in composed_units:
                nested_unit_dir = segment_dir / unit.folder_name
                write_text_to(atlas.atlas_dir, nested_unit_dir / "README.md", writer._unit_readme_text(unit))
                if caption_with_subtitles and unit.subtitles_text:
                    write_text_to(atlas.atlas_dir, nested_unit_dir / "SUBTITLES.md", unit.subtitles_text)

    def create(self, request: CanonicalCreateRequest, on_progress: Callable[[str], None] | None = None):
        atlas_dir = request.atlas_dir
        atlas_dir.mkdir(parents=True, exist_ok=True)
        request.input_dir.mkdir(parents=True, exist_ok=True)
        verbose = bool(getattr(self, "verbose", False))

        self._notify_progress(on_progress, "Preparing subtitles...")
        subtitle_assets = resolve_subtitle_assets(
            input_dir=request.input_dir,
            subtitle_path=request.subtitle_path,
            audio_path=request.audio_path,
            video_path=request.video_path,
            transcriber=getattr(self, "transcriber", None),
            generate_subtitles_if_missing=getattr(self, "generate_subtitles_if_missing", False),
            logger=self.logger,
        )

        prepared_srt_path = subtitle_assets.srt_file_path
        normalized_srt_path = request.input_dir / "subtitles.srt"
        if prepared_srt_path != normalized_srt_path:
            normalized_srt_path.write_text(prepared_srt_path.read_text(encoding="utf-8"), encoding="utf-8")
            prepared_srt_path = normalized_srt_path
        subtitle_items, subtitles_text = parse_srt(prepared_srt_path)
        self._notify_progress(on_progress, "Resolving atlas output language...")
        output_language = resolve_atlas_language(
            structure_request=request.structure_request or "",
            source_metadata=request.source_metadata,
            subtitles_text=subtitles_text,
        )
        self._notify_progress(on_progress, "Planning canonical atlas...")
        execution_plan = build_text_first_execution_plan(
            request=request,
            planner=getattr(self, "planner", None),
            subtitle_items=subtitle_items,
            output_language=output_language,
            verbose=verbose,
            chunk_size_sec=int(getattr(self, "chunk_size_sec", 600)),
            chunk_overlap_sec=int(getattr(self, "chunk_overlap_sec", 20)),
        )
        if execution_plan.profile.route != "text_first":
            raise NotImplementedError(f"Unsupported text-first route: {execution_plan.profile.route}")

        self._notify_progress(on_progress, "Parsing units...")
        started_at = time.time()
        units = build_text_units(
            text_segmentor=getattr(self, "text_segmentor", None),
            captioner=getattr(self, "captioner", None),
            execution_plan=execution_plan,
            subtitle_items=subtitle_items,
            subtitles_text=subtitles_text,
            verbose=verbose,
        )
        parsing_cost_time = time.time() - started_at

        self._notify_progress(on_progress, "Composing final structure...")
        started_at = time.time()
        composition_result = compose_canonical_structure(
            getattr(self, "structure_composer", None),
            units=units,
            concise_description=execution_plan.concise_description,
            genres=execution_plan.genres,
            structure_request=request.structure_request or "",
            output_language=execution_plan.output_language,
        )
        composition_cost_time = time.time() - started_at

        duration = self._resolve_duration(request, subtitle_items)
        final_segments = self._finalize_composed_segments(composition_result)
        source_path = request.video_path or request.audio_path or subtitle_assets.generated_audio_path or prepared_srt_path
        atlas = CanonicalAtlas(
            title=composition_result.title or execution_plan.profile_name.replace("_", " ").title() or "Text-First Atlas",
            duration=duration,
            abstract=composition_result.abstract or execution_plan.concise_description,
            segments=final_segments,
            execution_plan=execution_plan,
            atlas_dir=atlas_dir,
            relative_video_path=self._relative_path(atlas_dir, source_path) or Path("input/subtitles.srt"),
            relative_audio_path=(
                self._relative_path(atlas_dir, request.audio_path or subtitle_assets.generated_audio_path)
            ),
            relative_subtitles_path=Path("SUBTITLES.md") if subtitles_text and getattr(self, "caption_with_subtitles", True) else None,
            relative_srt_file_path=self._relative_path(atlas_dir, prepared_srt_path) or Path("input/subtitles.srt"),
            units=units,
            source_info=request.source_info,
            source_metadata=_serialize_source_metadata(request.source_metadata),
        ) 
    
        self._notify_progress(on_progress, "Writing atlas workspace...")
        started_at = time.time()
        if request.video_path is not None and request.video_path.exists():
            CanonicalAtlasWriter(caption_with_subtitles=getattr(self, "caption_with_subtitles", True)).write(atlas=atlas)
        else:
            self._write_text_only_workspace(atlas, subtitles_text)
        persistence_cost_time = time.time() - started_at

        if verbose:
            self._log_info("Text-first atlas construction completed successfully")

        return atlas, {
            "parsing_cost_time": parsing_cost_time,
            "composition_cost_time": composition_cost_time,
            "persistence_cost_time": persistence_cost_time,
        }
