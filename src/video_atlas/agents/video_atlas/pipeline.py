from __future__ import annotations

import json
import time
from pathlib import Path

from ...schemas import CreateVideoAtlasResult
from ...utils import get_video_property, parse_srt


class PipelineMixin:
    def _create(self, verbose: bool = False, caption_with_subtitles: bool = True) -> CreateVideoAtlasResult:
        workspace_dir = self._workspace_root()
        video_path = str(list(workspace_dir.glob("*.mp4"))[0])
        srt_files = list(workspace_dir.glob("*.srt"))
        srt_path = str(srt_files[0]) if srt_files else ""

        subtitle_items, subtitles_str = parse_srt(srt_path)
        if caption_with_subtitles:
            self._write_workspace_text("SUBTITLES.md", subtitles_str)

        video_info = get_video_property(video_path)
        duration_int = int(video_info["duration"])
        _ = video_info["resolution"]

        started_at = time.time()
        video_process_spec = self._probe_video_content(
            video_path,
            duration_int,
            subtitle_items,
            {"fps": 1, "max_resolution": 480},
        )
        probe_result = video_process_spec.normalized_strategy
        video_process_spec.description_sampling.use_subtitles = caption_with_subtitles

        if verbose:
            print(f"[Probe] Video analysis completed in {time.time() - started_at:.2f}s")
            print(f"[Probe] Strategy determined:\n{json.dumps(probe_result, indent=2)}")

        self._write_workspace_text("PROBE_RESULT.json", json.dumps(probe_result, indent=4))
        all_contexts = self._generate_segments_and_context(
            video_path=video_path,
            duration_int=duration_int,
            subtitle_items=subtitle_items,
            verbose=verbose,
            video_process_spec=video_process_spec,
        )
        self._generate_global_context(all_contexts, duration_int, verbose, caption_with_subtitles)

        if not self.tree.check_video_workspace(self.workspace):
            raise RuntimeError(f"workspace {self.workspace} is not a valid video workspace")
        self.tree.organize_video_workspace(self.workspace)

        result = CreateVideoAtlasResult(
            success=True,
            segment_num=len(all_contexts),
            segmentation_sampling=video_process_spec.segmentation_sampling,
            description_sampling=video_process_spec.description_sampling,
            segment_spec=video_process_spec.segment_spec,
            caption_spec=video_process_spec.caption_spec,
        )
        if verbose:
            print("✅ VideoAtlas construction completed successfully!")
        return result

    def add(
        self,
        input_path: str | Path | None = None,
        video_path: str | Path | None = None,
        subtitle_path: str | Path | None = None,
        verbose: bool = False,
        caption_with_subtitles: bool = True,
    ) -> CreateVideoAtlasResult:
        assert input_path or video_path, "Either input_path or video_path must be provided."

        if input_path:
            source_path = Path(input_path)
            if not source_path.exists():
                raise FileNotFoundError(f"Input path does not exist: {source_path}")
            if verbose:
                print(f"📂 Processing input video from: {source_path}")

            mp4_files = list(source_path.glob("*.mp4"))
            srt_files = list(source_path.glob("*.srt"))
            if len(mp4_files) != 1:
                raise ValueError(f"Expected exactly one .mp4 file in {source_path}, found {len(mp4_files)}")
            if len(srt_files) > 1 and verbose:
                print(f"⚠️ Warning: Multiple .srt files found in {source_path}. Using the first one.")

            workspace_root = self._workspace_root()
            self.workspace.copy_to_workspace(str(mp4_files[0]), str(workspace_root / mp4_files[0].name))
            if srt_files:
                self.workspace.copy_to_workspace(str(srt_files[0]), str(workspace_root / srt_files[0].name))
            if verbose:
                print(f"✅ Files copied to workspace: {workspace_root}")
        elif video_path:
            source_video_path = Path(video_path)
            if not source_video_path.exists():
                raise FileNotFoundError(f"Video path does not exist: {source_video_path}")
            if verbose:
                print(f"📂 Processing video from: {source_video_path}")

            workspace_root = self._workspace_root()
            self.workspace.copy_to_workspace(str(source_video_path), str(workspace_root / source_video_path.name))
            if subtitle_path:
                source_subtitle_path = Path(subtitle_path)
                if not source_subtitle_path.exists():
                    raise FileNotFoundError(f"Subtitle path does not exist: {source_subtitle_path}")
                if verbose:
                    print(f"📂 Processing subtitle from: {source_subtitle_path}")
                self.workspace.copy_to_workspace(str(source_subtitle_path), str(workspace_root / source_subtitle_path.name))
            if verbose:
                print(f"✅ Files copied to workspace: {workspace_root}")

        return self._create(verbose=verbose, caption_with_subtitles=caption_with_subtitles)
