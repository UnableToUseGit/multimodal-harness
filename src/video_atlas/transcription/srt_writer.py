from __future__ import annotations

from .types import TranscriptSegment


def _format_srt_timestamp(seconds: float) -> str:
    milliseconds = max(0, int(round(seconds * 1000)))
    hours, remainder = divmod(milliseconds, 3600 * 1000)
    minutes, remainder = divmod(remainder, 60 * 1000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def transcript_segments_to_srt(segments: list[TranscriptSegment]) -> str:
    lines: list[str] = []
    for index, segment in enumerate(segments, start=1):
        text = segment.text.strip()
        if not text:
            continue
        lines.extend(
            [
                str(index),
                f"{_format_srt_timestamp(segment.start)} --> {_format_srt_timestamp(segment.end)}",
                text,
                "",
            ]
        )
    return "\n".join(lines).strip() + ("\n" if lines else "")
