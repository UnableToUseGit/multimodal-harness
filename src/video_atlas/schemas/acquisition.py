"""Acquisition dataclasses."""

from __future__ import annotations
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from dateutil import parser


@dataclass(frozen=True)
class SourceInfoRecord:
    source_type: str
    source_url: str | None = None
    subtitle_source: str | None = None
    acquisition_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
@dataclass
class SourceMetadata:
    title: str = ""
    introduction: str = ""
    author: str = ""
    publish_date: datetime = field(default_factory=lambda: datetime(1970, 1, 1))
    duration_seconds: float = 0
    thumbnails: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "introduction": self.introduction,
            "author": self.author,
            "publish_date": self.publish_date.isoformat(),
            "duration_seconds": self.duration_seconds,
            "thumbnails": list(self.thumbnails),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SourceMetadata":
        clean_data = data.copy()

        if "publish_date" in clean_data and isinstance(clean_data["publish_date"], str):
            try:
                clean_data["publish_date"] = parser.parse(clean_data["publish_date"])
            except Exception:
                clean_data.pop("publish_date")

        if "thumbnails" in clean_data:
            val = clean_data["thumbnails"]
            if isinstance(val, (list, tuple)):
                clean_data["thumbnails"] = list(val)
            else:
                clean_data["thumbnails"] = []

        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in clean_data.items() if k in valid_fields}

        return cls(**filtered_data)


@dataclass
class SourceAcquisitionResult:
    source_info: SourceInfoRecord
    source_metadata: SourceMetadata
    video_path: Path | None = None
    audio_path: Path | None = None
    subtitles_path: Path | None = None
    artifacts: dict[str, Path] = field(default_factory=dict)
