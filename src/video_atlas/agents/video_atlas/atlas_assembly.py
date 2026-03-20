from __future__ import annotations

import time
from pathlib import Path

from ...prompts import VIDEO_GLOBAL_PROMPT
from ...schemas import VideoGlobal, VideoSeg


class AtlasAssemblyMixin:
    def _write_segment_artifacts(
        self,
        video_path: str,
        segment: dict,
        save_name: str,
        segment_readme: str
    ) -> None:
        segment_dir = Path("segments") / save_name
        self._write_workspace_text(segment_dir / "README.md", segment_readme)
        if self.caption_with_subtitles and segment.get("subtitles_text"):
            self._write_workspace_text(segment_dir / "SUBTITLES.md", segment["subtitles_text"])

        clip_relative_path = segment_dir / "video_clip.mp4"
        if not self._clip_exists(clip_relative_path):
            self._extract_clip(video_path, segment["start_time"], segment["end_time"], clip_relative_path)

    def _assemble_canonical_atlas(
        self,
        parsed_segments,
        video_path: str,
        duration_int: int,
        verbose: bool
    ):
        started_at = time.time()
        segments_description = "\n".join(
            [
                f'- {seg["seg_id"]}: {seg["start_time"]:.1f} - {seg["end_time"]:.1f} seconds\n'
                f'Summary: {seg["summary"]}\nDetail Description: {seg["detail"]}\n'
                for seg in parsed_segments
            ]
        )
        user_prompt = VIDEO_GLOBAL_PROMPT["USER"].format(segments_description=segments_description)
        output = self.captioner.generate_single(
            messages=self._prepare_messages(system_prompt=VIDEO_GLOBAL_PROMPT["SYSTEM"], user_prompt=user_prompt)
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

        segments_quickview_items = []
        for seg in parsed_segments:
            seg_title = title_map.get(seg["seg_id"], seg.get("seg_title") or seg["seg_id"])
            seg_index = int(seg["seg_id"].split("_")[-1])
            save_name = self._segment_save_name(seg_index, seg_title, seg["start_time"], seg["end_time"])
            video_seg = VideoSeg(
                seg_id=seg["seg_id"],
                seg_title=seg_title,
                summary=seg["summary"],
                start_time=seg["start_time"],
                end_time=seg["end_time"],
                duration=seg["end_time"] - seg["start_time"],
                detail=seg["detail"],
            )
            self._write_segment_artifacts(
                video_path=video_path,
                segment=seg,
                save_name=save_name,
                segment_readme=video_seg.to_markdown(with_subtitles=self.caption_with_subtitles)
            )
            segments_quickview_items.append(
                f'- {seg["seg_id"]} ({seg_title}): {seg["start_time"]:.1f} - {seg["end_time"]:.1f} seconds: {seg["summary"]}'
            )

        video_global = VideoGlobal(
            title=global_context.get("title", ""),
            abstract=global_context.get("abstract", ""),
            duration=duration_int,
            num_segments=len(parsed_segments),
            segments_quickview="\n".join(segments_quickview_items),
        )
        self._write_workspace_text("README.md", video_global.to_markdown(with_subtitles=self.caption_with_subtitles))
