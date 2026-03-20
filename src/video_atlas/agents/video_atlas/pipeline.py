from __future__ import annotations

from dataclasses import asdict
import json
import time
from pathlib import Path

from ...schemas import CreateVideoAtlasResult
from ...transcription import generate_subtitles_for_video
from ...utils import get_video_property, parse_srt


class PipelineMixin:
    def _resolve_subtitle_path(self, workspace_dir: Path, video_path: str, verbose: bool = False) -> str:
        srt_files = list(workspace_dir.glob("*.srt"))
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

        subtitle_path = workspace_dir / "subtitles.srt"
        try:
            generate_subtitles_for_video(video_path, subtitle_path, transcriber=transcriber, logger=self.logger)
            if verbose:
                self._log_info("Generated subtitles at %s", subtitle_path)
            return str(subtitle_path)
        except Exception as exc:
            self._log_warning("Automatic subtitle generation failed: %s", exc)
            return ""

    def _create(self, verbose: bool = False) -> CreateVideoAtlasResult:
        workspace_dir = self._workspace_root()
        video_path = str(list(workspace_dir.glob("*.mp4"))[0])
        srt_path = self._resolve_subtitle_path(workspace_dir, video_path, verbose=verbose)
        subtitle_items, subtitles_str = parse_srt(srt_path)
        if self.caption_with_subtitles:
            self._write_workspace_text("SUBTITLES.md", subtitles_str)

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

        self._write_workspace_text("EXECUTION_PLAN.json", json.dumps(asdict(execution_plan), indent=4))
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

        if not self._check_video_workspace():
            raise RuntimeError(f"workspace {self.workspace} is not a valid video workspace")
        self._organize_video_workspace()

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

    def add(
        self,
        input_path: str | Path | None = None,
        video_path: str | Path | None = None,
        subtitle_path: str | Path | None = None,
        verbose: bool = False
    ) -> CreateVideoAtlasResult:
        assert input_path or video_path, "Either input_path or video_path must be provided."
        if input_path:
            source_path = Path(input_path)
            if not source_path.exists():
                raise FileNotFoundError(f"Input path does not exist: {source_path}")
            if verbose:
                self._log_info("Processing input video from: %s", source_path)

            mp4_files = list(source_path.glob("*.mp4"))
            srt_files = list(source_path.glob("*.srt"))
            if len(mp4_files) != 1:
                raise ValueError(f"Expected exactly one .mp4 file in {source_path}, found {len(mp4_files)}")
            if len(srt_files) > 1 and verbose:
                self._log_warning("Multiple .srt files found in %s. Using the first one.", source_path)

            workspace_root = self._workspace_root()
            self.workspace.copy_to_workspace(str(mp4_files[0]), str(workspace_root / mp4_files[0].name))
            if srt_files:
                self.workspace.copy_to_workspace(str(srt_files[0]), str(workspace_root / srt_files[0].name))
            if verbose:
                self._log_info("Files copied to workspace: %s", workspace_root)
        elif video_path:
            source_video_path = Path(video_path)
            if not source_video_path.exists():
                raise FileNotFoundError(f"Video path does not exist: {source_video_path}")
            if verbose:
                self._log_info("Processing video from: %s", source_video_path)

            workspace_root = self._workspace_root()
            self.workspace.copy_to_workspace(str(source_video_path), str(workspace_root / source_video_path.name))
            if subtitle_path:
                source_subtitle_path = Path(subtitle_path)
                if not source_subtitle_path.exists():
                    raise FileNotFoundError(f"Subtitle path does not exist: {source_subtitle_path}")
                if verbose:
                    self._log_info("Processing subtitle from: %s", source_subtitle_path)
                self.workspace.copy_to_workspace(str(source_subtitle_path), str(workspace_root / source_subtitle_path.name))
            if verbose:
                self._log_info("Files copied to workspace: %s", workspace_root)

        return self._create(verbose=verbose)
