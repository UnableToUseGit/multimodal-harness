from __future__ import annotations

from pathlib import Path

from ...review.workspace_loader import _first_existing, _parse_markdown_fields, _parse_timestamp
from ...schemas import AtlasSegment, CanonicalAtlas


def load_canonical_workspace(root_path: str | Path) -> CanonicalAtlas:
    root = Path(root_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Canonical workspace not found: {root}")

    readme_path = root / "README.md"
    if not readme_path.exists():
        raise FileNotFoundError(f"Canonical workspace README not found: {readme_path}")

    segments_dir = root / "segments"
    if not segments_dir.exists():
        raise FileNotFoundError(f"Canonical workspace segments directory not found: {segments_dir}")

    segments: list[AtlasSegment] = []
    for segment_dir in sorted(path for path in segments_dir.iterdir() if path.is_dir()):
        readme = segment_dir / "README.md"
        if not readme.exists():
            continue

        fields = _parse_markdown_fields(readme.read_text(encoding="utf-8"))
        segment_id = fields.get("SegID", segment_dir.name)
        start_time = _parse_timestamp(fields.get("Start Time"), default=0.0)
        end_time = _parse_timestamp(fields.get("End Time"), default=0.0)
        clip_path = segment_dir / "video_clip.mp4"
        subtitles_path = segment_dir / "SUBTITLES.md"
        segments.append(
            AtlasSegment(
                segment_id=segment_id,
                title=fields.get("Title", segment_id),
                start_time=start_time,
                end_time=end_time,
                summary=fields.get("Summary", ""),
                caption=fields.get("Detail Description", ""),
                folder_name=segment_dir.name,
                readme_path=readme.resolve(),
                clip_path=clip_path.resolve() if clip_path.exists() else None,
                subtitles_path=subtitles_path.resolve() if subtitles_path.exists() else None,
            )
        )

    root_readme = readme_path.read_text(encoding="utf-8")
    source_video = _first_existing(root, ["*.mp4"])
    return CanonicalAtlas(
        title=root.name,
        abstract=root_readme,
        segments=segments,
        root_path=root,
        readme_text=root_readme,
        source_video_path=source_video.resolve() if source_video is not None else None,
    )
