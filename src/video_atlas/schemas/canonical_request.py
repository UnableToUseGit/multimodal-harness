from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .acquisition import SourceInfoRecord, SourceMetadata


@dataclass
class CanonicalCreateRequest:
    atlas_dir: Path
    video_path: Path | None = None
    audio_path: Path | None = None
    subtitle_path: Path | None = None
    structure_request: str = ""
    source_info: SourceInfoRecord | None = None
    source_metadata: SourceMetadata | None = None
    
    @property
    def input_dir(self) -> Path:
        return self.atlas_dir / "input"
