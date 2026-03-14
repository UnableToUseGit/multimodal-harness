"""Backward-compatible utility exports."""

from .frames import get_frame_indices, prepare_video_input, process_one_frame
from .subtitles import get_subtitle_in_segment, parse_srt
from .video_metadata import get_video_property, read_json

__all__ = [
    "get_frame_indices",
    "get_subtitle_in_segment",
    "get_video_property",
    "parse_srt",
    "prepare_video_input",
    "process_one_frame",
    "read_json",
]
