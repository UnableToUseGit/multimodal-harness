from __future__ import annotations

from dataclasses import asdict
import json
import re
import shlex
import shutil
import subprocess
from pathlib import Path

from ..schemas import AtlasUnit, CanonicalAtlas, DerivedAtlas, CandidateBoundary
from ..utils.video_metadata import seconds_to_hms


def format_hms_time_range(start_time: float, end_time: float) -> str:
    return f"{seconds_to_hms(start_time)}-{seconds_to_hms(end_time)}"

def write_candidate_boundaries_for_debug(
    atlas_dir: str,
    chunk_index: int,
    core_start_time: float,
    core_end_time: float,
    window_start_time: float,
    window_end_time: float,
    last_detection_point: float | None,
    candidate_boundaries: list[CandidateBoundary],
) -> None:
    payload = {
        "chunk_index": chunk_index,
        "core_start": core_start_time,
        "core_end": core_end_time,
        "window_start": window_start_time,
        "window_end": window_end_time,
        "last_detection_point": last_detection_point,
        "candidate_boundaries": [
            {
                "timestamp": item.timestamp,
                "boundary_rationale": item.boundary_rationale,
                "boundary_rationale": item.segment_title,
                "evidence": list(item.evidence),
                "confidence": item.confidence,
            }
            for item in candidate_boundaries
        ],
    }
    relative_path = (
        f"./boundary_for_debug/"
        f"chunk_{chunk_index:04d}_core_{core_start_time:.2f}_{core_end_time:.2f}.json"
    )
    write_text_to(atlas_dir, relative_path, json.dumps(payload, indent=2, ensure_ascii=False))


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


def write_text_to(destination: str | Path, relative_path: str | Path, content: str) -> Path:
    target_path = Path(destination) / Path(relative_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding="utf-8")
    return target_path


def write_json_to(destination: str | Path, relative_path: str | Path, payload: dict[str, object]) -> Path:
    return write_text_to(destination, relative_path, json.dumps(payload, indent=2, ensure_ascii=False))

def slugify_segment_title(title: str) -> str:
    slug_chars: list[str] = []
    previous_was_separator = False

    for char in title.lower().strip():
        if char.isalnum():
            slug_chars.append(char)
            previous_was_separator = False
            continue

        if not previous_was_separator:
            slug_chars.append("-")
            previous_was_separator = True

    normalized = "".join(slug_chars).strip("-")
    return normalized or "untitled"


def clip_exists(destination: str | Path, relative_path: str | Path) -> bool:
    return (Path(destination) / Path(relative_path)).exists()


def extract_clip(
    destination: str | Path,
    video_path: str | Path,
    seg_start_time: float,
    seg_end_time: float,
    relative_output_path: str | Path,
) -> None:
    root_path = Path(destination)
    output_path = root_path / Path(relative_output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = (
        "ffmpeg -y -loglevel quiet "
        f"-ss {seg_start_time} -to {seg_end_time} "
        f"-i {shlex.quote(str(video_path.relative_to(root_path)))} "
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


def build_canonical_root_readme_text(
    atlas,
    *,
    duration_seconds: float,
    has_video: bool = True,
    has_audio: bool = False,
    has_subtitles: bool = True,
    has_thumbnail_dir: bool = False,
) -> str:
    source_type = getattr(getattr(atlas, "source_info", None), "source_type", None) or "unknown"
    source_metadata = getattr(atlas, "source_metadata", {}) or {}
    source_title = source_metadata.get("title", "") if isinstance(source_metadata, dict) else ""
    source_author = source_metadata.get("author", "") if isinstance(source_metadata, dict) else ""

    input_lines = [
        "- `input/` stores the source assets and acquisition metadata for this run.",
        "- It may include the original video or audio file, prepared subtitles, downloaded thumbnails, `SOURCE_INFO.json`, and `SOURCE_METADATA.json`.",
    ]
    if has_video:
        input_lines.append("- If the source video was downloaded, you will find it under `input/`.")
    if has_audio:
        input_lines.append("- If the source is audio-first, the copied audio file is stored under `input/`.")
    if has_subtitles:
        input_lines.append("- Prepared subtitles are stored under `input/subtitles.srt` and summarized again in `SUBTITLES.md` when enabled.")
    if has_thumbnail_dir:
        input_lines.append("- Downloaded thumbnails are stored under `input/thumbnails/` for cover selection and downstream creative tasks.")

    return "\n".join(
        [
            "# MM Harness Output",
            "",
            "This directory is the result of one `mm-harness create` run.",
            "It converts a long video or audio source into a structured workspace that is easier to read, search, and reuse.",
            "",
            "## At A Glance",
            f"- Title: {atlas.title}",
            f"- Source type: {source_type}",
            f"- Duration: {seconds_to_hms(duration_seconds)}",
            f"- Units: {len(getattr(atlas, 'units', []) or [])}",
            f"- Segments: {len(getattr(atlas, 'segments', []) or [])}",
            *(([f"- Original source title: {source_title}"] if source_title else [])),
            *(([f"- Source author: {source_author}"] if source_author else [])),
            "",
            "## Recommended Reading Order",
            "- Start with `segments/` if you want the quickest understanding of the content.",
            "- Go to `units/` if you need a finer-grained breakdown of the source.",
            "- Use `input/` when you need the raw source assets, subtitles, metadata, or thumbnails.",
            "",
            "## Directory Guide",
            "### input/",
            *input_lines,
            "",
            "### units/",
            "- `units/` stores the smallest content units extracted from the source.",
            "- Each unit usually represents one continuous span of content with its own title, summary, detail description, and time range.",
            "- Open a unit folder when you need a precise local view of the material.",
            "",
            "### segments/",
            "- `segments/` stores higher-level grouped results built from one or more units.",
            "- A segment is usually the best place to start if you want a readable chapter-like view of the source.",
            "- Each segment folder contains its own `README.md` and a copied view of the units it is composed from.",
            "",
            "## Workspace Files",
            "- `README.md` is this overview page.",
            "- `SUBTITLES.md` contains the prepared full subtitles when subtitle export is enabled.",
            "- `units/` contains the detailed low-level breakdown.",
            "- `segments/` contains the higher-level grouped structure.",
            "",
            "## Abstract",
            atlas.abstract,
        ]
    )


class CanonicalAtlasWriter:
    def __init__(self, caption_with_subtitles: bool = True) -> None:
        self.caption_with_subtitles = caption_with_subtitles

    def _unit_readme_text(self, unit: AtlasUnit) -> str:
        return "\n".join(
            [
                "# Unit",
                "",
                f"**UnitID**: {unit.unit_id}",
                "",
                f"**Start Time**: {seconds_to_hms(unit.start_time)}",
                "",
                f"**End Time**: {seconds_to_hms(unit.end_time)}",
                "",
                f"**Duration**: {seconds_to_hms(unit.duration)}",
                "",
                f"**Title**: {unit.title}",
                "",
                f"**Summary**: {unit.summary}",
                "",
                f"**Detail Description**: {unit.caption}",
                "",
                "# Additional Files",
                "- Raw video for this unit: `./video_clip.mp4`",
                "- Subtitles for this unit: `./SUBTITLES.md`",
            ]
        )

    def _segment_readme_text(self, segment, composed_units: list[AtlasUnit]) -> str:
        unit_lines = [
            f"- {unit.unit_id}: {unit.title} ({seconds_to_hms(unit.start_time)} - {seconds_to_hms(unit.end_time)})"
            for unit in composed_units
        ]
        return "\n".join(
            [
                "# Segment",
                "",
                f"**SegID**: {segment.segment_id}",
                "",
                f"**Start Time**: {seconds_to_hms(segment.start_time)}",
                "",
                f"**End Time**: {seconds_to_hms(segment.end_time)}",
                "",
                f"**Duration**: {seconds_to_hms(segment.duration)}",
                "",
                f"**Title**: {segment.title}",
                "",
                f"**Summary**: {segment.summary}",
                "",
                f"**Composition Rationale**: {segment.composition_rationale}",
                "",
                "## Composed Units",
                *unit_lines,
            ]
        )

    def _global_readme_text(self, atlas, max_end_time) -> str:
        has_audio = getattr(atlas, "relative_audio_path", None) is not None
        source_metadata = getattr(atlas, "source_metadata", {}) or {}
        has_thumbnail_dir = bool(source_metadata.get("thumbnails"))
        return build_canonical_root_readme_text(
            atlas,
            duration_seconds=max_end_time,
            has_video=True,
            has_audio=has_audio,
            has_subtitles=self.caption_with_subtitles,
            has_thumbnail_dir=has_thumbnail_dir,
        )

    def _write_unit_directory(
        self,
        atlas_dir: Path,
        video_path: Path,
        unit: AtlasUnit,
        relative_dir: Path,
    ) -> None:
        write_text_to(atlas_dir, relative_dir / "README.md", self._unit_readme_text(unit))
        if self.caption_with_subtitles and unit.subtitles_text:
            write_text_to(atlas_dir, relative_dir / "SUBTITLES.md", unit.subtitles_text)
        clip_relative_path = relative_dir / "video_clip.mp4"
        if not clip_exists(atlas_dir, clip_relative_path):
            extract_clip(atlas_dir, video_path, unit.start_time, unit.end_time, clip_relative_path)
    
    def write(
        self,
        atlas: CanonicalAtlas,
    ) -> None:
        atlas_dir = atlas.atlas_dir
        video_path = atlas.atlas_dir / atlas.relative_video_path
        units = list(getattr(atlas, "units", []) or [])
        units_by_id = {unit.unit_id: unit for unit in units}

        for unit in units:
            self._write_unit_directory(
                atlas_dir=atlas_dir,
                video_path=video_path,
                unit=unit,
                relative_dir=Path("units") / unit.folder_name,
            )

        for segment in atlas.segments:
            segment_dir = Path("segments") / segment.folder_name
            composed_units = [units_by_id[unit_id] for unit_id in segment.unit_ids if unit_id in units_by_id]
            write_text_to(atlas_dir, segment_dir / "README.md", self._segment_readme_text(segment, composed_units))

            for unit in composed_units:
                self._write_unit_directory(
                    atlas_dir=atlas_dir,
                    video_path=video_path,
                    unit=unit,
                    relative_dir=segment_dir / unit.folder_name,
                )

        markdown_text = self._global_readme_text(atlas, atlas.duration)
                                 
        if not self.caption_with_subtitles:
            markdown_text = markdown_text.replace("- Full subtitles for this video: `./SUBTITLES.md`", "")
        
        write_text_to(atlas_dir, "README.md", markdown_text)


class DerivedAtlasWriter:
    def __init__(self, caption_with_subtitles: bool = True) -> None:
        self.caption_with_subtitles = caption_with_subtitles

    def _root_readme_text(self, derived_atlas: DerivedAtlas) -> str:
        return "\n".join(
            [
                "# Derived Atlas",
                "",
                "## Task Request",
                derived_atlas.task_request,
                "",
                "## Global Summary",
                derived_atlas.global_summary,
                "",
                "## Detailed Breakdown",
                derived_atlas.detailed_breakdown,
            ]
        )

    def _segment_readme_text(self, segment, source_segment_id: str, intent: str) -> str:
        return "\n".join(
            [
                "# Derived Segment",
                "",
                f"**DerivedSegID**: {segment.segment_id}",
                f"**SourceSegID**: {source_segment_id}",
                f"**Start Time**: {seconds_to_hms(segment.start_time)}",
                f"**End Time**: {seconds_to_hms(segment.end_time)}",
                f"**Duration**: {seconds_to_hms(segment.duration)}",
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
    ) -> None:
        atlas_dir = derived_atlas.atlas_dir
        result_info = derived_atlas.derivation_result_info
        write_text_to(atlas_dir, "README.md", self._root_readme_text(derived_atlas))
        write_text_to(atlas_dir, "TASK.md", derived_atlas.task_request)
        write_text_to(
            atlas_dir,
            "derivation.json",
            json.dumps(
                {
                    "task_request": derived_atlas.task_request,
                    "global_summary": derived_atlas.global_summary,
                    "detailed_breakdown": derived_atlas.detailed_breakdown,
                    "derived_segment_count": len(derived_atlas.segments),
                    "source_canonical_atlas_path": str(derived_atlas.source_canonical_atlas_dir),
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        write_text_to(
            atlas_dir,
            ".agentignore/DERIVATION_RESULT.json",
            json.dumps(asdict(result_info), ensure_ascii=False, indent=2),
        )

        for segment in derived_atlas.segments:
            source_segment_id = result_info.derivation_source.get(segment.segment_id, "")
            policy = result_info.derivation_reason.get(segment.segment_id)
            intent = policy.intent if policy is not None else ""
            segment_dir = Path("segments") / segment.folder_name
            write_text_to(atlas_dir, segment_dir / "README.md", self._segment_readme_text(segment, source_segment_id, intent))
            subtitles_text = segment.subtitles_text
            if self.caption_with_subtitles and subtitles_text:
                write_text_to(atlas_dir, segment_dir / "SUBTITLES.md", subtitles_text)
            write_text_to(
                atlas_dir,
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

            extract_clip(
                atlas_dir,
                derived_atlas.source_video_path,
                segment.start_time,
                segment.end_time,
                segment_dir / "video_clip.mp4",
            )
