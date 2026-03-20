from __future__ import annotations

import re
from pathlib import Path

from ...schemas import CanonicalAtlas, CanonicalSegment


SEGMENT_FIELD_RE = re.compile(r"\*\*(?P<key>[^*]+)\*\*:\s*(?P<value>.*)")


def _parse_segment_readme(readme_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in readme_text.splitlines():
        match = SEGMENT_FIELD_RE.match(line.strip())
        if match:
            fields[match.group("key").strip()] = match.group("value").strip()
    return fields


def load_canonical_atlas(source_workspace: str | Path) -> CanonicalAtlas:
    root_path = Path(source_workspace).resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"Source workspace not found: {root_path}")

    root_readme_path = root_path / "README.md"
    if not root_readme_path.exists():
        raise FileNotFoundError(f"Canonical atlas README not found: {root_readme_path}")

    segments_dir = root_path / "segments"
    if not segments_dir.exists():
        raise FileNotFoundError(f"Canonical atlas segments directory not found: {segments_dir}")

    segments: list[CanonicalSegment] = []
    for segment_dir in sorted([path for path in segments_dir.iterdir() if path.is_dir()]):
        readme_path = segment_dir / "README.md"
        if not readme_path.exists():
            continue

        fields = _parse_segment_readme(readme_path.read_text(encoding="utf-8"))
        source_segment_id = fields.get("SegID", segment_dir.name)
        start_time = float(fields.get("Start Time", "0") or 0)
        end_time = float(fields.get("End Time", "0") or 0)
        duration = float(fields.get("Duration", str(end_time - start_time)) or (end_time - start_time))
        segments.append(
            CanonicalSegment(
                source_segment_id=source_segment_id,
                source_folder=segment_dir.name,
                seg_title=fields.get("Title", ""),
                summary=fields.get("Summary", ""),
                detail=fields.get("Detail Description", ""),
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                readme_path=readme_path,
                subtitles_path=(segment_dir / "SUBTITLES.md") if (segment_dir / "SUBTITLES.md").exists() else None,
                clip_path=(segment_dir / "video_clip.mp4") if (segment_dir / "video_clip.mp4").exists() else None,
            )
        )

    source_video_path = next(iter(sorted(root_path.glob("*.mp4"))), None)
    execution_plan_path = root_path / ".agentignore" / "EXECUTION_PLAN.json"
    if execution_plan_path.exists():
        resolved_execution_plan_path = execution_plan_path
    else:
        resolved_execution_plan_path = root_path / ".agentignore" / "PROBE_RESULT.json"
        if not resolved_execution_plan_path.exists():
            resolved_execution_plan_path = None

    return CanonicalAtlas(
        root_path=root_path,
        root_readme=root_readme_path.read_text(encoding="utf-8"),
        source_video_path=source_video_path,
        execution_plan_path=resolved_execution_plan_path,
        segments=segments,
    )
