"""Shared source information schema."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceInfoRecord:
    source_type: str
    source_url: str
    canonical_source_url: str
    subtitle_source: str = "none"
    subtitle_fallback_required: bool = False
    acquisition_timestamp: str | None = None
