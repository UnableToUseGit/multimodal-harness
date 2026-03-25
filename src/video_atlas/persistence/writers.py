from __future__ import annotations

from dataclasses import asdict
import json
import re
import shlex
import shutil
import subprocess
from pathlib import Path

from ..schemas import CanonicalAtlas, DerivationResultInfo, DerivedAtlas

def copy_to(src_path: Path, destination: Path) -> Path:
    """Copy a file/directory to destination dir."""
    src = Path(src_path)
    dest_dir = Path(destination)

    if not dest_dir.exists() or not dest_dir.is_dir():
        raise ValueError("destination must be an existing directory")
    if not src.exists():
        raise FileNotFoundError(src)

    dest = dest_dir / src.name
    if src.is_dir():
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)
    return dest


def write_text_to(destination: str | Path, relative_path: str | Path, content: str) -> None:
    target_path = Path(destination) / Path(relative_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding="utf-8")
    return target_path

def slugify_segment_title(title: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return normalized or "untitled"


def clip_exists(workspace_root: str | Path, relative_path: str | Path) -> bool:
    return (Path(workspace_root) / Path(relative_path)).exists()


def extract_clip(
    workspace_root: str | Path,
    video_path: str,
    seg_start_time: float,
    seg_end_time: float,
    relative_output_path: str | Path,
) -> None:
    root_path = Path(workspace_root)
    output_path = root_path / Path(relative_output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = (
        "ffmpeg -y -loglevel quiet "
        f"-ss {seg_start_time} -to {seg_end_time} "
        f"-i {shlex.quote(Path(video_path).name)} "
        f"-c copy {shlex.quote(str(output_path.relative_to(root_path)))}"
    )
    result = subprocess.run(
        command,
        shell=True,
        cwd=root_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed with exit code {result.returncode}: {result.stdout}")


class CanonicalAtlasWriter:
    def __init__(self, caption_with_subtitles: bool = True) -> None:
        self.caption_with_subtitles = caption_with_subtitles

    def _segment_readme_text(self, segment) -> str:
        
        return "\n".join(
            [
                "# Segment",
                "",
                f"**SegID**: {segment.segment_id}",
                f"**Start Time**: {segment.start_time:.1f}",
                f"**End Time**: {segment.end_time:.1f}",
                f"**Duration**: {segment.duration:.1f}",
                f"**Title**: {segment.title}",
                f"**Summary**: {segment.summary}",
                f"**Detail Description**: {segment.caption}",
                "",
                "# Additional Files",
                "- Raw video for this segment: `./video_clip.mp4`",
                "- Subtitles for this segment: `./SUBTITLES.md`",
            ]
        )
        
    def _global_readme_text(self, atlas, max_end_time) -> str:
        
        return "\n".join(
            [
                f"**Title**: {atlas.title}",
                f"**Duration**: {max_end_time:.1f}",
                f"**Abstract**: {atlas.abstract}",
                "**# Segmentation Context**:",
                f"There are {len(atlas.segments)} segments are extracted from raw video."
                "- Each segment is saved in `./segments`."
                "- Each segment includes:"
                "- A `README.md` file containing the title, description, start time, and end time."
                "- A `video_clip.mp4` file with the corresponding video clip."
                "- A `SUBTITLES.md` file with the corresponding subtitles."
                "",
                "# Additional Files"
                "- Raw video: `./video.mp4`"
                "- Detail information of segments: `./segments/`"
                "- Full subtitles for this video: `./SUBTITLES.md`"
            ]
        )
    
    def write(
        self,
        atlas: CanonicalAtlas,
    ) -> None:
        segments_quickview_items = []
        
        atlas_dir = atlas.atlas_dir
        video_path = atlas.atlas_dir / atlas.relative_video_path

        for segment in atlas.segments:
            segment_dir = Path("segments") / segment.folder_name
            write_text_to(atlas_dir, segment_dir / "README.md", self._segment_readme_text(segment))
            
            subtitles_text = segment.subtitles_text
            if self.caption_with_subtitles and subtitles_text:
                write_text_to(atlas_dir, segment_dir / "SUBTITLES.md", subtitles_text)

            clip_relative_path = segment_dir / "video_clip.mp4"
            if not clip_exists(atlas_dir, clip_relative_path):
                extract_clip(atlas_dir, video_path, segment.start_time, segment.end_time, clip_relative_path)

            segments_quickview_items.append(
                f"- {segment.segment_id} ({segment.title}): {segment.start_time:.1f} - {segment.end_time:.1f} seconds: {segment.summary}"
            )

        # TODO segments_quickview_items 没用上，是否还需要添加？
        markdown_text = self._global_readme_text(atlas, atlas.duration, "\n".join(segments_quickview_items)
                                 
        if not self.caption_with_subtitles:
            markdown_text = markdown_text.replace("- Full subtitles for this video: `./SUBTITLES.md`", "").replace("- A `SUBTITLES.md` file with the corresponding subtitles.", "")
                                 
        write_text_to(atlas_dir, "README.md", markdown_text)


class DerivedAtlasWriter:
    def __init__(self, caption_with_subtitles: bool = True) -> None:
        self.caption_with_subtitles = caption_with_subtitles

    def _segment_readme_text(self, segment, source_segment_id: str, intent: str) -> str:
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
        workspace_root: str | Path,
        segment_artifacts: dict[str, dict[str, str]] | None = None,
    ) -> None:
        segment_artifacts = segment_artifacts or {}
        write_text_to(workspace_root, "README.md", derived_atlas.readme_text)
        write_text_to(workspace_root, "TASK.md", task_request)
        write_text_to(
            workspace_root,
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
        write_text_to(
            workspace_root,
            ".agentignore/DERIVATION_RESULT.json",
            json.dumps(asdict(result_info), ensure_ascii=False, indent=2),
        )

        for segment in derived_atlas.segments:
            source_segment_id = result_info.derivation_source.get(segment.segment_id, "")
            policy = result_info.derivation_reason.get(segment.segment_id)
            intent = policy.intent if policy is not None else ""
            segment_dir = Path("segments") / segment.folder_name
            write_text_to(workspace_root, segment_dir / "README.md", self._segment_readme_text(segment, source_segment_id, intent))
            subtitles_text = segment_artifacts.get(segment.segment_id, {}).get("subtitles_text", "")
            if self.caption_with_subtitles and subtitles_text:
                write_text_to(workspace_root, segment_dir / "SUBTITLES.md", subtitles_text)
            write_text_to(
                workspace_root,
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

            extract_clip(workspace_root, source_video_path, segment.start_time, segment.end_time, segment_dir / "video_clip.mp4")
