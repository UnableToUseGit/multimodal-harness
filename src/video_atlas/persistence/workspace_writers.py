from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Callable

from ..schemas import CanonicalAtlas, DerivationResultInfo, DerivedAtlas, VideoGlobal, VideoSeg


WriteText = Callable[[str | Path, str], None]
ExtractClip = Callable[[str, float, float, str | Path], None]
ClipExists = Callable[[str | Path], bool]


class CanonicalWorkspaceWriter:
    def __init__(
        self,
        write_text: WriteText,
        extract_clip: ExtractClip,
        clip_exists: ClipExists,
        caption_with_subtitles: bool = True,
    ) -> None:
        self.write_text = write_text
        self.extract_clip = extract_clip
        self.clip_exists = clip_exists
        self.caption_with_subtitles = caption_with_subtitles

    def write(
        self,
        atlas: CanonicalAtlas,
        source_video_path: str,
        segment_artifacts: dict[str, dict[str, str]] | None = None,
    ) -> None:
        segment_artifacts = segment_artifacts or {}
        segments_quickview_items = []
        max_end_time = 0.0
        for segment in atlas.segments:
            segment_dir = Path("segments") / segment.folder_name
            video_seg = VideoSeg(
                seg_id=segment.segment_id,
                seg_title=segment.title,
                summary=segment.summary,
                start_time=segment.start_time,
                end_time=segment.end_time,
                duration=segment.duration,
                detail=segment.caption,
            )
            self.write_text(segment_dir / "README.md", video_seg.to_markdown(with_subtitles=self.caption_with_subtitles))

            subtitles_text = segment_artifacts.get(segment.segment_id, {}).get("subtitles_text", "")
            if self.caption_with_subtitles and subtitles_text:
                self.write_text(segment_dir / "SUBTITLES.md", subtitles_text)

            clip_relative_path = segment_dir / "video_clip.mp4"
            if not self.clip_exists(clip_relative_path):
                self.extract_clip(source_video_path, segment.start_time, segment.end_time, clip_relative_path)

            segments_quickview_items.append(
                f"- {segment.segment_id} ({segment.title}): {segment.start_time:.1f} - {segment.end_time:.1f} seconds: {segment.summary}"
            )
            max_end_time = max(max_end_time, segment.end_time)

        video_global = VideoGlobal(
            title=atlas.title,
            abstract=atlas.abstract,
            duration=max_end_time,
            num_segments=len(atlas.segments),
            segments_quickview="\n".join(segments_quickview_items),
        )
        self.write_text("README.md", video_global.to_markdown(with_subtitles=self.caption_with_subtitles))


class DerivedWorkspaceWriter:
    def __init__(
        self,
        write_text: WriteText,
        extract_clip: ExtractClip,
        caption_with_subtitles: bool = True,
    ) -> None:
        self.write_text = write_text
        self.extract_clip = extract_clip
        self.caption_with_subtitles = caption_with_subtitles

    def _segment_readme_text(
        self,
        segment,
        source_segment_id: str,
        intent: str,
    ) -> str:
        return "\n".join(
            [
                "# Derived Segment",
                "",
                f"**DerivedSegID**: {segment.segment_id}",
                f"**SourceSegID**: {source_segment_id}",
                f"**Start Time**: {segment.start_time:.1f}",
                f"**End Time**: {segment.end_time:.1f}",
                f"**Duration**: {segment.duration:.1f}",
                f"**Title**: {segment.title}",
                f"**Summary**: {segment.summary}",
                f"**Detail Description**: {segment.caption}",
                f"**Intent**: {intent}",
                "",
                "# Additional Files",
                "- Raw video for this segment: `./video_clip.mp4`",
                "- Subtitles for this segment: `./SUBTITLES.md`",
            ]
        )

    def write(
        self,
        derived_atlas: DerivedAtlas,
        result_info: DerivationResultInfo,
        task_request: str,
        source_video_path: str,
        segment_artifacts: dict[str, dict[str, str]] | None = None,
    ) -> None:
        segment_artifacts = segment_artifacts or {}
        self.write_text("README.md", derived_atlas.readme_text)
        self.write_text("TASK.md", task_request)
        self.write_text(
            "derivation.json",
            json.dumps(
                {
                    "task_request": task_request,
                    "global_summary": derived_atlas.global_summary,
                    "detailed_breakdown": derived_atlas.detailed_breakdown,
                    "derived_segment_count": len(derived_atlas.segments),
                    "source_canonical_atlas_path": str(derived_atlas.source_canonical_atlas_path),
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        self.write_text(".agentignore/DERIVATION_RESULT.json", json.dumps(asdict(result_info), ensure_ascii=False, indent=2))

        for segment in derived_atlas.segments:
            source_segment_id = result_info.derivation_source.get(segment.segment_id, "")
            policy = result_info.derivation_reason.get(segment.segment_id)
            intent = policy.intent if policy is not None else ""
            segment_dir = Path("segments") / segment.folder_name
            self.write_text(segment_dir / "README.md", self._segment_readme_text(segment, source_segment_id, intent))
            subtitles_text = segment_artifacts.get(segment.segment_id, {}).get("subtitles_text", "")
            if self.caption_with_subtitles and subtitles_text:
                self.write_text(segment_dir / "SUBTITLES.md", subtitles_text)
            self.write_text(
                segment_dir / "SOURCE_MAP.json",
                json.dumps(
                    {
                        "source_segment_id": source_segment_id,
                        "derivation_policy": asdict(policy) if policy is not None else {},
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
            self.extract_clip(source_video_path, segment.start_time, segment.end_time, segment_dir / "video_clip.mp4")
