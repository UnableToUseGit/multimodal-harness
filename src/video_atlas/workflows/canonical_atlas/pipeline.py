from __future__ import annotations

from dataclasses import asdict
import json
import time
from pathlib import Path
import math

from ...transcription import generate_subtitles_for_video
from ...utils import get_video_property, parse_srt
from ...persistence import CanonicalAtlasWriter, copy_to, write_text_to, write_candidate_boundaries_for_debug
from ...schemas import CanonicalAtlas

class PipelineMixin:
    def _resolve_srt_file_path(
        self, output_dir: Path, video_path: Path, verbose: bool = False
    ) -> tuple[Path | None, Path | None]:
        srt_files = list(output_dir.glob("*.srt"))
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

        srt_file_path = output_dir / "subtitles.srt"
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
        output_dir: Path,
        source_video_path: Path,
        source_srt_file_path: Path | None = None,
        verbose: bool = False
    ) -> CanonicalAtlas:
        
        if not source_video_path.exists():
            raise FileNotFoundError(f"Video path does not exist: {source_video_path}")
        if verbose:
            self._log_info("Processing video from: %s", source_video_path)

        output_dir.mkdir(parents=True, exist_ok=True)
        video_path = copy_to(source_video_path, output_dir)
        srt_file_path: Path | None = None
        if source_srt_file_path:
            if not source_srt_file_path.exists():
                raise FileNotFoundError(f"Subtitle srt file path does not exist: {source_srt_file_path}")
            if verbose:
                self._log_info("Processing subtitle from: %s", source_srt_file_path)
            srt_file_path = copy_to(source_srt_file_path, output_dir)
        if verbose:
            self._log_info("Files copied to output directory: %s", output_dir)

        if srt_file_path is None:
            srt_file_path, audio_path = self._resolve_srt_file_path(output_dir, video_path, verbose=verbose)
        else:
            audio_path = None
        if srt_file_path is not None:
            subtitle_items, subtitles_str = parse_srt(srt_file_path)
        else:
            subtitle_items, subtitles_str = [], ""
        subtitles_path = None
        if self.caption_with_subtitles:
            subtitles_path = write_text_to(output_dir, "SUBTITLES.md", subtitles_str)

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

        write_text_to(output_dir, "EXECUTION_PLAN.json", json.dumps(asdict(execution_plan), indent=4))
        
        started_at = time.time()
        parsed_segments, record_generated_boundaries = self._parse_video_into_segments(
            video_path=video_path,
            duration=duration,
            subtitle_items=subtitle_items,
            verbose=verbose,
            execution_plan=execution_plan,
        )
        parsing_cost_time = time.time() - started_at
        
        started_at = time.time()
        atlas = self._assemble_canonical_atlas(
            atlas_dir=output_dir,
            duration=duration,
            execution_plan=execution_plan,
            parsed_segments=parsed_segments,
            video_path=video_path,
            audio_path=audio_path,
            subtitles_path=subtitles_path,
            srt_file_path=srt_file_path,
            verbose=verbose
        )
        assemble_cost_time = time.time() - started_at

        started_at = time.time()
        CanonicalAtlasWriter(caption_with_subtitles=self.caption_with_subtitles).write(atlas=atlas)
        persistence_cost_time = time.time() - started_at

        for item in record_generated_boundaries:
            write_candidate_boundaries_for_debug(output_dir, **item)

        if verbose:
            self._log_info("VideoAtlas construction completed successfully")

        cost_time_info = {"plan_cost_time": plan_cost_time, "parsing_cost_time": parsing_cost_time, "assemble_cost_time":assemble_cost_time, "persistence_cost_time": persistence_cost_time}
        
        return atlas, cost_time_info
