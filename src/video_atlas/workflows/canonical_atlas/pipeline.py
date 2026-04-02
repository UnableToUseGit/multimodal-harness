from __future__ import annotations

from dataclasses import asdict
import json
import time
from pathlib import Path
import math

from ...transcription import generate_subtitles_for_video
from ...utils import get_video_property, parse_srt
from ...persistence import CanonicalAtlasWriter, format_hms_time_range, slugify_segment_title, write_text_to, write_candidate_boundaries_for_debug
from ...schemas import AtlasSegment, CanonicalAtlas, CanonicalCreateRequest


def _serialize_source_metadata(source_metadata):
    if source_metadata is None:
        return {}
    if hasattr(source_metadata, "to_dict"):
        return source_metadata.to_dict()
    if hasattr(source_metadata, "__dataclass_fields__"):
        return asdict(source_metadata)
    return dict(source_metadata)


class PipelineMixin:
    def _finalize_composed_segments(self, composition_result):
        normalized_segments: list[AtlasSegment] = []
        for segment in composition_result.segments:
            folder_name = segment.folder_name or (
                f"{segment.segment_id.replace('_', '-')}-{slugify_segment_title(segment.title or segment.segment_id)}-"
                f"{format_hms_time_range(segment.start_time, segment.end_time)}"
            )
            normalized_segments.append(
                AtlasSegment(
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

    def _resolve_srt_file_path(
        self, input_dir: Path, video_path: Path, verbose: bool = False
    ) -> tuple[Path | None, Path | None]:
        srt_files = list(input_dir.glob("*.srt"))
        if srt_files:
            return srt_files[0], None

        if not getattr(self, "generate_subtitles_if_missing", False):
            if verbose:
                self._log_warning("No subtitle file found and subtitle generation is disabled")
            return None, None

        transcriber = getattr(self, "transcriber", None)
        if transcriber is None:
            self._log_warning("No subtitle file found and no transcriber configured; continuing without subtitles")
            return None, None

        srt_file_path = input_dir / "subtitles.srt"
        try:
            srt_file_path, audio_path = generate_subtitles_for_video(video_path, srt_file_path, transcriber=transcriber, logger=self.logger)
            if verbose:
                self._log_info("Generated subtitles at %s", srt_file_path)
            return srt_file_path, audio_path
        except Exception as exc:
            self._log_warning("Automatic subtitle generation failed: %s", exc)
            return None, None

    def create(
        self,
        request: CanonicalCreateRequest,
    ) -> CanonicalAtlas:
        atlas_dir = request.atlas_dir
        atlas_dir.mkdir(parents=True, exist_ok=True)
        verbose = bool(getattr(self, "verbose", False))
        source_video_path = request.video_path
        source_srt_file_path = request.subtitle_path

        if source_video_path is None:
            raise NotImplementedError("Text-only canonical create path is not implemented yet")
        if not source_video_path.exists():
            raise FileNotFoundError(f"Video path does not exist: {source_video_path}")
        if verbose:
            self._log_info("Processing video from: %s", source_video_path)

        video_path = source_video_path
        srt_file_path: Path | None = None
        if source_srt_file_path:
            if not source_srt_file_path.exists():
                raise FileNotFoundError(f"Subtitle srt file path does not exist: {source_srt_file_path}")
            if verbose:
                self._log_info("Processing subtitle from: %s", source_srt_file_path)
            srt_file_path = source_srt_file_path

        if srt_file_path is None:
            srt_file_path, audio_path = self._resolve_srt_file_path(request.input_dir, video_path, verbose=verbose)
        else:
            audio_path = None
        if srt_file_path is not None:
            subtitle_items, subtitles_str = parse_srt(srt_file_path)
        else:
            subtitle_items, subtitles_str = [], ""
        subtitles_path = None
        if self.caption_with_subtitles:
            subtitles_path = write_text_to(atlas_dir, "SUBTITLES.md", subtitles_str)

        video_info = get_video_property(video_path)
        duration = math.trunc(video_info["duration"] * 10) / 10
        _ = video_info["resolution"]

        started_at = time.time()
        execution_plan = self._plan_video_execution(
            video_path,
            duration,
            subtitle_items,
            {"fps": 0.5, "max_resolution": 480},
        )
        plan_cost_time = time.time() - started_at
        if verbose:
            self._log_info("[Plan] Video planning completed in %.2fs", time.time() - started_at)
            self._log_info("[Plan] Execution plan:\n%s", json.dumps(asdict(execution_plan), indent=2))

        write_text_to(atlas_dir, "EXECUTION_PLAN.json", json.dumps(asdict(execution_plan), indent=4))
        
        started_at = time.time()
        units, record_generated_boundaries = self._parse_video_into_segments(
            video_path=video_path,
            duration=duration,
            subtitle_items=subtitle_items,
            verbose=verbose,
            execution_plan=execution_plan,
        )
        parsing_cost_time = time.time() - started_at

        started_at = time.time()
        composition_result = self._compose_canonical_structure(
            units=units,
            concise_description=execution_plan.concise_description,
            genres=execution_plan.genres,
            structure_request=request.structure_request or "",
        )
        composition_cost_time = time.time() - started_at
        
        started_at = time.time()
        final_segments = self._finalize_composed_segments(composition_result)
        atlas = CanonicalAtlas(
            title=composition_result.title,
            duration=duration,
            abstract=composition_result.abstract,
            units=units,
            segments=final_segments,
            execution_plan=execution_plan,
            atlas_dir=atlas_dir,
            relative_video_path=video_path.relative_to(atlas_dir),
            relative_audio_path=audio_path.relative_to(atlas_dir) if audio_path is not None else None,
            relative_subtitles_path=subtitles_path.relative_to(atlas_dir) if subtitles_path is not None else None,
            relative_srt_file_path=srt_file_path.relative_to(atlas_dir) if srt_file_path is not None else None,
            source_info=request.source_info,
            source_metadata=_serialize_source_metadata(request.source_metadata),
        )
        assemble_cost_time = time.time() - started_at

        started_at = time.time()
        CanonicalAtlasWriter(caption_with_subtitles=self.caption_with_subtitles).write(atlas=atlas)
        persistence_cost_time = time.time() - started_at

        for item in record_generated_boundaries:
            write_candidate_boundaries_for_debug(atlas_dir, **item)

        if verbose:
            self._log_info("VideoAtlas construction completed successfully")

        cost_time_info = {
            "plan_cost_time": plan_cost_time,
            "parsing_cost_time": parsing_cost_time,
            "composition_cost_time": composition_cost_time,
            "assemble_cost_time": assemble_cost_time,
            "persistence_cost_time": persistence_cost_time,
        }
        
        return atlas, cost_time_info
