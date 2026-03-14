# -*- coding: utf-8 -*-
"""Workspace-facing markdown models."""

from __future__ import annotations

from dataclasses import dataclass


SEG_TEMPLATE = """# Segment Context

**SegID**: {seg_id}

**Start Time**: {start_time}

**End Time**: {end_time}

**Duration**: {duration}

**Title**: {seg_title}

**Summary**: {summary}

**Detail Description**: {detail}

# Additional Files
- Raw video for this segment: `./video_clip.mp4`
- Subtitles for this segment: `./SUBTITLES.md`
""".strip()


GLOBAL_TEMPLATE = """
**Title**: {title}

**Duration**: {duration} seconds

**Abstract**: {abstract}

# Segmentation Context
There are {num_segments} segments are extracted from raw video.
- Each segment is saved in `./segments`.
- Each segment includes:
- A `README.md` file containing the title, description, start time, and end time.
- A `video.mp4` file with the corresponding video clip.
- A `SUBTITLES.md` file with the corresponding subtitles.

# Additional Files
- Raw video: `./video.mp4`
- Detail information of segments: `./segments/`
- Full subtitles for this video: `./SUBTITLES.md`
""".strip()


@dataclass
class VideoSeg:
    seg_id: str
    start_time: float
    end_time: float
    duration: float
    seg_title: str
    summary: str
    detail: str

    def to_markdown(self, with_subtitles: bool = True) -> str:
        markdown = SEG_TEMPLATE.format(
            seg_id=self.seg_id,
            seg_title=self.seg_title,
            summary=self.summary,
            start_time=self.start_time,
            end_time=self.end_time,
            duration=self.duration,
            detail=self.detail,
        )
        if not with_subtitles:
            markdown = markdown.replace("- Subtitles for this segment: `./SUBTITLES.md`", "")
        return markdown


@dataclass
class VideoGlobal:
    title: str
    abstract: str
    num_segments: int
    segments_quickview: str
    duration: float

    def to_markdown(self, with_subtitles: bool = True) -> str:
        markdown = GLOBAL_TEMPLATE.format(
            title=self.title,
            duration=self.duration,
            abstract=self.abstract,
            num_segments=self.num_segments,
        )
        if not with_subtitles:
            markdown = markdown.replace("- Full subtitles for this video: `./SUBTITLES.md`", "")
            markdown = markdown.replace("- A `SUBTITLES.md` file with the corresponding subtitles.", "")
        return markdown
