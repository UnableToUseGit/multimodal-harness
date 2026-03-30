from __future__ import annotations

import time
from pathlib import Path
from typing import List

from ...persistence import CanonicalAtlasWriter, format_hms_time_range, slugify_segment_title
from ...prompts import VIDEO_GLOBAL_PROMPT
from ...schemas import AtlasSegment, CanonicalAtlas, CanonicalExecutionPlan


class AtlasAssemblyMixin:
    def _assemble_canonical_atlas(
        self,
        atlas_dir: Path,
        duration: float,
        execution_plan: CanonicalExecutionPlan,
        parsed_segments: List[dict],
        video_path: Path,
        audio_path: Path | None,
        subtitles_path: Path | None,
        srt_file_path: Path | None,
        verbose: bool,
    ) -> CanonicalAtlas:
        started_at = time.time()
        segments_description = "\n".join(
            [
                f'- {seg["seg_id"]}: {seg["start_time"]:.1f} - {seg["end_time"]:.1f} seconds\n'
                f'Summary: {seg["summary"]}\nDetail Description: {seg["detail"]}\n'
                for seg in parsed_segments
            ]
        )
        system_prompt = VIDEO_GLOBAL_PROMPT.render_system()
        user_prompt = VIDEO_GLOBAL_PROMPT.render_user(segments_description=segments_description)
        output = self.captioner.generate_single(
            messages=self._prepare_messages(system_prompt=system_prompt, user_prompt=user_prompt)
        )
        global_context = self.parse_response(output["text"])

        if verbose:
            self._log_info(
                "[Global] Atlas generation completed in %.2fs | Token usage: %s",
                time.time() - started_at,
                output["response"]["usage"]["total_tokens"],
            )

        title_map = {}
        for item in global_context.get("segment_titles", []) or []:
            if isinstance(item, dict):
                seg_id = item.get("seg_id", "")
                seg_title = item.get("title", "")
                if isinstance(seg_id, str) and isinstance(seg_title, str) and seg_id.strip() and seg_title.strip():
                    title_map[seg_id.strip()] = seg_title.strip()

        atlas_segments: list[AtlasSegment] = []
        for seg in parsed_segments:
            seg_title = title_map.get(seg["seg_id"], seg.get("seg_title") or seg["seg_id"])
            save_name = (
                f"{seg['seg_id']}-{slugify_segment_title(seg_title)}-"
                f"{format_hms_time_range(seg['start_time'], seg['end_time'])}"
            )
            atlas_segments.append(
                AtlasSegment(
                    segment_id=seg["seg_id"],
                    title=seg_title,
                    start_time=seg["start_time"],
                    end_time=seg["end_time"],
                    summary=seg["summary"],
                    caption=seg["detail"],
                    subtitles_text=seg.get("subtitles_text", ""),
                    folder_name=save_name,
                    relative_clip_path=Path(f"segments/{save_name}/video_clip.mp4"),
                    relative_subtitles_path=Path(f"segments/{save_name}/SUBTITLES.md"),
                )
            )
            
        atlas = CanonicalAtlas(
            title=global_context.get("title", ""),
            duration=duration,
            abstract=global_context.get("abstract", ""),
            segments=atlas_segments,
            execution_plan=execution_plan,
            atlas_dir=atlas_dir,
            relative_video_path=video_path.relative_to(atlas_dir),
            relative_audio_path=audio_path.relative_to(atlas_dir) if audio_path is not None else None,
            relative_subtitles_path=subtitles_path.relative_to(atlas_dir) if subtitles_path is not None else None,
            relative_srt_file_path=srt_file_path.relative_to(atlas_dir) if srt_file_path is not None else None,
        )
        
        return atlas
