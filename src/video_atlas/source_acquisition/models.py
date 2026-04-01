"""Source acquisition dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..schemas.source_info import SourceInfoRecord


@dataclass
class SourceAcquisitionResult:
    source_info: SourceInfoRecord
    local_video_path: Path
    local_subtitles_path: Path | None = None
    source_metadata: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Path] = field(default_factory=dict)
