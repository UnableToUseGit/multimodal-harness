"""Subtitle parsing helpers."""

from __future__ import annotations

import os
import re
from typing import Dict, List
from pathlib import Path


def _ts_to_seconds(ts: str) -> float:
    hh, mm, rest = ts.split(":")
    ss, ms = rest.replace(".", ",").split(",")
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000.0


def parse_srt(srt_path: Path):
    if not Path(srt_path).exists():
        return [], ""

    with open(srt_path, "r", encoding="utf-8", errors="replace") as file:
        srt_text = file.read()

    srt_text = srt_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if srt_text.startswith("\ufeff"):
        srt_text = srt_text.lstrip("\ufeff")
    if srt_text.startswith("WEBVTT"):
        srt_text = srt_text[len("WEBVTT") :].lstrip()
    blocks = re.split(r"\n\s*\n", srt_text)
    subtitle_items: List[Dict] = []
    time_re = re.compile(
        r"(?P<start>\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(?P<end>\d{2}:\d{2}:\d{2}[,.]\d{3})"
    )

    for block in blocks:
        lines = [line.strip("\ufeff").strip() for line in block.split("\n") if line.strip()]
        if len(lines) < 2:
            continue
        if lines[0].startswith("NOTE"):
            continue

        match = None
        time_line_idx = None
        for index, line in enumerate(lines[:3]):
            match = time_re.search(line)
            if match:
                time_line_idx = index
                break
        if time_line_idx is None or match is None:
            continue

        start_s = _ts_to_seconds(match.group("start"))
        end_s = _ts_to_seconds(match.group("end"))
        text = "\n".join(lines[time_line_idx + 1 :]).strip()
        text = re.sub(r"<[^>]+>", "", text)
        text = (
            text.replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .strip()
        )
        if text:
            subtitle_items.append({"start": start_s, "end": end_s, "text": text})

    subtitle_items.sort(key=lambda item: (item["start"], item["end"]))
    subtitle_text = ""
    for item in subtitle_items:
        subtitle_text += (
            f'Start Time: {item["start"]:.1f} --> End Time: {item["end"]:.1f} '
            f'Subtitle: {item["text"]}\n\n'
        )
    return subtitle_items, subtitle_text


def get_subtitle_in_segment(subtitle_items: List[Dict], start_time, end_time):
    subtitles_in_segment = []
    for subtitle in subtitle_items:
        if start_time <= subtitle["start"] and end_time >= subtitle["end"]:
            subtitles_in_segment.append(
                {
                    "start": subtitle["start"],
                    "end": subtitle["end"],
                    "offset": start_time,
                    "shift_start": subtitle["start"] - start_time,
                    "shift_end": subtitle["end"] - start_time,
                    "text": subtitle["text"],
                }
            )

    subtitle_text = ""
    for item in subtitles_in_segment:
        subtitle_text += (
            f'Start Time: {item["start"]:.1f} --> End Time: {item["end"]:.1f} '
            f'Subtitle: {item["text"]}\n\n'
        )
    return subtitles_in_segment, subtitle_text
