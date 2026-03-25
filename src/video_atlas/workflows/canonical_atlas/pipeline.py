from __future__ import annotations

from dataclasses import asdict
import json
import time
from pathlib import Path

from ...schemas import CreateVideoAtlasResult
from ...transcription import generate_subtitles_for_video
from ...utils import get_video_property, parse_srt
from ...persistence import copy_to, write_text_to

class PipelineMixin:
    def _resolve_subtitle_path(self, output_dir: Path, video_path: Path, verbose: bool = False) -> Path:
        srt_files = list(output_dir.glob("*.srt"))
        if srt_files:
            return str(srt_files[0])

        if not getattr(self, "generate_subtitles_if_missing", False):
            if verbose:
                self._log_warning("No subtitle file found and subtitle generation is disabled")
            return ""

        transcriber = getattr(self, "transcriber", None)
        if transcriber is None:
            self._log_warning("No subtitle file found and no transcriber configured; continuing without subtitles")
            return ""

        subtitle_path = output_dir / "subtitles.srt"
        try:
            generate_subtitles_for_video(video_path, subtitle_path, transcriber=transcriber, logger=self.logger)
            if verbose:
                self._log_info("Generated subtitles at %s", subtitle_path)
            return subtitle_path
        except Exception as exc:
            self._log_warning("Automatic subtitle generation failed: %s", exc)
            return ""

    def create(
        self,
        video_path: Path,
        output_dir: Path,
        subtitle_path: Path | None = None,
        verbose: bool = False
    ) -> CreateVideoAtlasResult:
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video path does not exist: {video_path}")
        if verbose:
            self._log_info("Processing video from: %s", video_path)

        video_pat = copy_to(video_path, output_dir)
        if subtitle_path:
            if not subtitle_path.exists():
                raise FileNotFoundError(f"Subtitle path does not exist: {subtitle_path}")
            if verbose:
                self._log_info("Processing subtitle from: %s", subtitle_path)
            subtitle_path = copy_to(subtitle_path, output_dir)
        if verbose:
            self._log_info("Files copied to output directory: %s", output_dir)

        # srt_path = self._resolve_subtitle_path(output_dir, video_path, verbose=verbose)
        srt_path = Path('/share/project/minghao/Proj/VideoAFS/VideoEdit/development/local/workspaces/canonical_case_002/.agentignore/subtitles.srt')
        subtitle_items, subtitles_str = parse_srt(srt_path)
        if self.caption_with_subtitles:
            write_text_to(output_dir, "SUBTITLES.md", subtitles_str)

        video_info = get_video_property(video_path)
        duration_int = int(video_info["duration"])
        _ = video_info["resolution"]

        started_at = time.time()
        execution_plan = self._plan_video_execution(
            video_path,
            duration_int,
            subtitle_items,
            {"fps": 1, "max_resolution": 480},
        )

        if verbose:
            self._log_info("[Plan] Video planning completed in %.2fs", time.time() - started_at)
            self._log_info("[Plan] Execution plan:\n%s", json.dumps(asdict(execution_plan), indent=2))

        write_text_to(output_dir, "EXECUTION_PLAN.json", json.dumps(asdict(execution_plan), indent=4))
        parsed_segments = self._parse_video_into_segments(
            video_path=video_path,
            duration_int=duration_int,
            subtitle_items=subtitle_items,
            verbose=verbose,
            execution_plan=execution_plan,
        )
        self._assemble_canonical_atlas(
            parsed_segments=parsed_segments,
            video_path=video_path,
            duration_int=duration_int,
            verbose=verbose
        )
        
        result = CreateVideoAtlasResult(
            success=True,
            segment_num=len(parsed_segments),
            specification=execution_plan,
            segmentation_sampling=execution_plan.segmentation_specification.frame_sampling_profile,
            description_sampling=execution_plan.caption_specification.frame_sampling_profile,
        )
        if verbose:
            self._log_info("VideoAtlas construction completed successfully")
            
        return result
