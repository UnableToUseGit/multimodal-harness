from __future__ import annotations

import re

from ...persistence import slugify_segment_title
from ...prompts import DERIVED_CAPTION_PROMPT, DERIVED_GROUNDING_PROMPT
from ...schemas import AtlasSegment, DerivationPolicy


class DerivationMixin:
    def _grounding_prompt(self, segment: AtlasSegment, policy: DerivationPolicy) -> str:
        return DERIVED_GROUNDING_PROMPT["USER"].format(
            segment_id=segment.segment_id,
            segment_start_time=segment.start_time,
            segment_end_time=segment.end_time,
            intent=policy.intent,
            grounding_instruction=policy.grounding_instruction,
            summary=segment.summary,
            detail=segment.caption,
        )

    def _caption_prompt(
        self,
        task_request: str,
        segment: AtlasSegment,
        policy: DerivationPolicy,
        start_time: float,
        end_time: float,
        subtitles_text: str,
    ) -> str:
        return DERIVED_CAPTION_PROMPT["USER"].format(
            task_request=task_request,
            segment_id=segment.segment_id,
            start_time=start_time,
            end_time=end_time,
            intent=policy.intent,
            grounding_instruction=policy.grounding_instruction,
            summary=segment.summary,
            detail=segment.caption,
            subtitles=subtitles_text,
        )

    def _load_subtitles_text(self, segment: AtlasSegment) -> str:
        if segment.subtitles_path is None or not segment.subtitles_path.exists():
            return ""
        return segment.subtitles_path.read_text(encoding="utf-8")

    def _prune_subtitles_text(self, subtitles_text: str, start_time: float, end_time: float) -> str:
        if not subtitles_text.strip():
            return ""

        kept_blocks: list[str] = []
        pattern = re.compile(
            r"Start Time:\s*(?P<start>[0-9.]+)\s*-->\s*End Time:\s*(?P<end>[0-9.]+)\s*Subtitle:\s*(?P<text>.*)",
            flags=re.DOTALL,
        )
        for block in [item.strip() for item in subtitles_text.split("\n\n") if item.strip()]:
            match = pattern.fullmatch(block)
            if match is None:
                continue
            item_start = float(match.group("start"))
            item_end = float(match.group("end"))
            if item_start >= start_time and item_end <= end_time:
                kept_blocks.append(block)
        return "\n\n".join(kept_blocks)

    def _resolve_refined_times(self, segment: AtlasSegment, response: dict) -> tuple[float, float] | None:
        raw_start = float(response.get("start_time", segment.start_time))
        raw_end = float(response.get("end_time", segment.end_time))
        if raw_end <= raw_start:
            return None

        if segment.start_time <= raw_start < raw_end <= segment.end_time:
            start_time = raw_start
            end_time = raw_end
        else:
            start_time = segment.start_time + raw_start
            end_time = segment.start_time + raw_end

        start_time = max(segment.start_time, start_time)
        end_time = min(segment.end_time, end_time)
        if end_time <= start_time:
            return None
        return start_time, end_time

    def _next_derived_segment_id(self, index: int) -> str:
        return f"derived_seg_{index:04d}"

    def _derive_one_segment(self, item: tuple[int, AtlasSegment, DerivationPolicy], task_request: str, source_video_path: str) -> dict | None:
        index, segment, policy = item
        grounding_output = self.segmentor.generate_single(
            messages=self._build_video_messages_from_path(
                system_prompt=DERIVED_GROUNDING_PROMPT["SYSTEM"],
                user_prompt=self._grounding_prompt(segment, policy),
                video_path=source_video_path,
                start_time=segment.start_time,
                end_time=segment.end_time,
            )
        )
        grounded = self.parse_response(grounding_output["text"])
        resolved = self._resolve_refined_times(segment, grounded if isinstance(grounded, dict) else {})
        if resolved is None:
            return None
        start_time, end_time = resolved

        pruned_subtitles = self._prune_subtitles_text(self._load_subtitles_text(segment), start_time, end_time)
        caption_output = self.captioner.generate_single(
            messages=self._build_video_messages_from_path(
                system_prompt=DERIVED_CAPTION_PROMPT["SYSTEM"],
                user_prompt=self._caption_prompt(task_request, segment, policy, start_time, end_time, pruned_subtitles),
                video_path=source_video_path,
                start_time=start_time,
                end_time=end_time,
            )
        )
        caption_data = self.parse_response(caption_output["text"])
        if not isinstance(caption_data, dict):
            caption_data = {}

        derived_segment_id = self._next_derived_segment_id(index)
        title = str(caption_data.get("title", f"Derived Segment {index}"))
        summary = str(caption_data.get("summary", segment.summary))
        caption = str(caption_data.get("caption", segment.caption))
        folder_name = (
            f"{derived_segment_id.replace('_', '-')}-"
            f"{slugify_segment_title(title)}-{start_time:.2f}-{end_time:.2f}s"
        )

        return {
            "segment": AtlasSegment(
                segment_id=derived_segment_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                summary=summary,
                caption=caption,
                folder_name=folder_name,
            ),
            "policy": policy,
            "source_segment_id": segment.segment_id,
            "subtitles_text": pruned_subtitles,
        }
