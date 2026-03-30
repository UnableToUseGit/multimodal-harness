from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import re
from pathlib import Path
from typing import Any


FIELD_RE = re.compile(r"\*\*(?P<key>[^*]+)\*\*:\s*(?P<value>.*)")
HUMAN_TIME_RE = re.compile(
    r"^\s*(?:(?P<hours>\d+)h\s*)?(?:(?P<minutes>\d+)min\s*)?(?:(?P<seconds>\d+)s)?\s*$"
)
HMS_TIME_RE = re.compile(r"^\s*(?P<hours>\d{2,}):(?P<minutes>\d{2}):(?P<seconds>\d{2})\s*$")


def _parse_markdown_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = FIELD_RE.match(line.strip())
        if match:
            fields[match.group("key").strip()] = match.group("value").strip()
    return fields


def _read_text_if_exists(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _read_json_if_exists(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_timestamp(value: str | None, default: float = 0.0) -> float:
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        hms_match = HMS_TIME_RE.match(value.strip())
        if hms_match:
            hours = int(hms_match.group("hours") or 0)
            minutes = int(hms_match.group("minutes") or 0)
            seconds = int(hms_match.group("seconds") or 0)
            return float(hours * 3600 + minutes * 60 + seconds)
        match = HUMAN_TIME_RE.match(value.strip())
        if not match:
            return default
        hours = int(match.group("hours") or 0)
        minutes = int(match.group("minutes") or 0)
        seconds = int(match.group("seconds") or 0)
        return float(hours * 3600 + minutes * 60 + seconds)


def _first_existing(root: Path, patterns: list[str]) -> Path | None:
    for pattern in patterns:
        match = next(iter(sorted(root.glob(pattern))), None)
        if match is not None and match.exists():
            return match
    return None


@dataclass
class ReviewSegment:
    segment_id: str
    folder_name: str
    title: str
    summary: str
    detail: str
    start_time: float
    end_time: float
    duration: float
    readme_text: str
    subtitles_text: str = ""
    readme_fields: dict[str, str] = field(default_factory=dict)
    clip_relative_path: str | None = None
    subtitles_relative_path: str | None = None
    readme_relative_path: str | None = None
    source_map: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewWorkspace:
    workspace_id: str
    label: str
    kind: str
    root_path: Path
    root_readme_text: str
    root_subtitles_text: str = ""
    task_text: str = ""
    execution_plan: dict[str, Any] | None = None
    derivation: dict[str, Any] | None = None
    source_video_relative_path: str | None = None
    normalized_audio_relative_path: str | None = None
    segments: list[ReviewSegment] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["root_path"] = str(self.root_path)
        data["segments"] = [segment.to_dict() for segment in self.segments]
        return data


def _detect_workspace_kind(root_path: Path) -> str:
    return "task" if (root_path / "derivation.json").exists() else "canonical"


def _segment_from_directory(segment_dir: Path, kind: str) -> ReviewSegment | None:
    readme_path = segment_dir / "README.md"
    if not readme_path.exists():
        return None

    readme_text = readme_path.read_text(encoding="utf-8")
    fields = _parse_markdown_fields(readme_text)
    start_time = _parse_timestamp(fields.get("Start Time"), default=0.0)
    end_time = _parse_timestamp(fields.get("End Time"), default=0.0)
    duration = _parse_timestamp(fields.get("Duration"), default=end_time - start_time)
    subtitles_path = segment_dir / "SUBTITLES.md"
    clip_path = segment_dir / "video_clip.mp4"
    source_map_path = segment_dir / "SOURCE_MAP.json"

    if kind == "task":
        segment_id = fields.get("DerivedSegID") or fields.get("TaskSegID") or segment_dir.name
        title = fields.get("Title", "")
        summary = fields.get("Summary", "")
        detail = fields.get("Detail Description") or fields.get("Original Detail", "")
    else:
        segment_id = fields.get("SegID", segment_dir.name)
        title = fields.get("Title", "")
        summary = fields.get("Summary", "")
        detail = fields.get("Detail Description", "")

    return ReviewSegment(
        segment_id=segment_id,
        folder_name=segment_dir.name,
        title=title,
        summary=summary,
        detail=detail,
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        readme_text=readme_text,
        subtitles_text=_read_text_if_exists(subtitles_path if subtitles_path.exists() else None),
        readme_fields=fields,
        clip_relative_path=str(clip_path.relative_to(segment_dir.parent.parent)) if clip_path.exists() else None,
        subtitles_relative_path=str(subtitles_path.relative_to(segment_dir.parent.parent)) if subtitles_path.exists() else None,
        readme_relative_path=str(readme_path.relative_to(segment_dir.parent.parent)),
        source_map=_read_json_if_exists(source_map_path if source_map_path.exists() else None),
    )


def load_review_workspace(root_path: str | Path, workspace_id: str, label: str | None = None) -> ReviewWorkspace:
    root = Path(root_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Workspace not found: {root}")

    kind = _detect_workspace_kind(root)
    root_readme_path = root / "README.md"
    if not root_readme_path.exists():
        raise FileNotFoundError(f"Workspace README not found: {root_readme_path}")

    segments_dir = root / "segments"
    segments: list[ReviewSegment] = []
    if segments_dir.exists():
        for segment_dir in sorted(path for path in segments_dir.iterdir() if path.is_dir()):
            segment = _segment_from_directory(segment_dir, kind=kind)
            if segment is not None:
                segments.append(segment)

    source_video = _first_existing(root, ["*.mp4"])
    normalized_audio = _first_existing(root, ["*.wav"])
    execution_plan_path = None
    if (root / ".agentignore").exists():
        execution_plan_path = _first_existing(root / ".agentignore", ["EXECUTION_PLAN.json", "PROBE_RESULT.json"])
    if execution_plan_path is None:
        execution_plan_path = _first_existing(root, ["EXECUTION_PLAN.json", "PROBE_RESULT.json"])

    workspace = ReviewWorkspace(
        workspace_id=workspace_id,
        label=label or root.name,
        kind=kind,
        root_path=root,
        root_readme_text=root_readme_path.read_text(encoding="utf-8"),
        root_subtitles_text=_read_text_if_exists((root / "SUBTITLES.md") if (root / "SUBTITLES.md").exists() else None),
        task_text=_read_text_if_exists((root / "TASK.md") if (root / "TASK.md").exists() else None),
        execution_plan=_read_json_if_exists(execution_plan_path),
        derivation=_read_json_if_exists((root / "derivation.json") if (root / "derivation.json").exists() else None),
        source_video_relative_path=str(source_video.relative_to(root)) if source_video is not None else None,
        normalized_audio_relative_path=str(normalized_audio.relative_to(root)) if normalized_audio is not None else None,
        segments=segments,
    )
    return workspace
