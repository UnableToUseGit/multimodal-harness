from __future__ import annotations

import time
from pathlib import Path

from ...persistence import CanonicalAtlasWriter, slugify_segment_title
from ...prompts import VIDEO_GLOBAL_PROMPT
from ...schemas import AtlasSegment, CanonicalAtlas

class AtlasAssemblyMixin:
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

        atlas_segments: list[AtlasSegment] = []
        segment_artifacts: dict[str, dict[str, str]] = {}
        for seg in parsed_segments:
            seg_title = title_map.get(seg["seg_id"], seg.get("seg_title") or seg["seg_id"])
            seg_index = int(seg["seg_id"].split("_")[-1])
            save_name = f"{seg["seg_id"]}-{slugify_segment_title(seg_title)}-{seg["start_time"]:.2f}-{seg["end_time"]:.2f}s"
            atlas_segments.append(
                AtlasSegment(
                    segment_id=seg["seg_id"],
                    title=seg_title,
                    start_time=seg["start_time"],
                    end_time=seg["end_time"],
                    summary=seg["summary"],
                    caption=seg["detail"],
                    folder_name=save_name,
                )
            )
            segment_artifacts[seg["seg_id"]] = {"subtitles_text": seg.get("subtitles_text", "")}

        atlas = CanonicalAtlas(
            title=global_context.get("title", ""),
            abstract=global_context.get("abstract", ""),
            segments=atlas_segments,
            root_path=self._workspace_root() if hasattr(self, "_workspace_root") else Path("."),
        )
        CanonicalAtlasWriter(caption_with_subtitles=self.caption_with_subtitles).write(
            atlas=atlas,
            source_video_path=video_path,
            workspace_root=self._workspace_root() if hasattr(self, "_workspace_root") else Path("."),
            segment_artifacts=segment_artifacts,
        )
