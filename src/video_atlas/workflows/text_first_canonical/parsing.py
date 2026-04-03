from __future__ import annotations

import concurrent.futures
from typing import Any, Sequence

from ...parsing import parse_json_response
from ...persistence import format_hms_time_range, slugify_segment_title
from ...prompts import CAPTION_GENERATION_PROMPT, TEXT_BOUNDARY_DETECTION_PROMPT
from ...schemas import AtlasUnit, CandidateBoundary, CanonicalExecutionPlan
from ...utils import get_subtitle_in_segment
from .language import render_output_language_instruction


def _normalize_text(value: Any) -> str:
    if not isinstance(value, str):
        value = str(value)
    return " ".join(value.split()).strip()


def _truncate_text(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 3)].rstrip() + "..."


def _clamp_confidence(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except Exception:
        return default
    return max(0.0, min(1.0, numeric))


def _dedupe_boundaries(boundaries: list[CandidateBoundary], threshold_sec: float = 0.5) -> list[CandidateBoundary]:
    deduped: list[CandidateBoundary] = []
    for boundary in sorted(boundaries, key=lambda item: item.timestamp):
        if deduped and abs(boundary.timestamp - deduped[-1].timestamp) <= threshold_sec:
            if boundary.confidence > deduped[-1].confidence:
                deduped[-1] = boundary
            continue
        deduped.append(boundary)
    return deduped


def _build_unit(
    *,
    unit_id: str,
    start_time: float,
    end_time: float,
    title: str,
    summary: str,
    caption: str,
    subtitles_text: str,
) -> AtlasUnit:
    safe_title = _truncate_text(_normalize_text(title) or unit_id, 80)
    folder_name = (
        f"{unit_id.replace('_', '-')}-{slugify_segment_title(safe_title)}-"
        f"{format_hms_time_range(start_time, end_time)}"
    )
    return AtlasUnit(
        unit_id=unit_id,
        title=safe_title,
        start_time=start_time,
        end_time=end_time,
        summary=_truncate_text(_normalize_text(summary) or safe_title, 240),
        caption=_normalize_text(caption) or safe_title,
        subtitles_text=_normalize_text(subtitles_text),
        folder_name=folder_name,
    )


def _build_chunk_messages(
    execution_plan: CanonicalExecutionPlan,
    subtitles: str,
    core_start: float,
    core_end: float,
    last_detection_point: float | None,
) -> list[dict[str, str]]:
    system_prompt = TEXT_BOUNDARY_DETECTION_PROMPT.render_system()
    user_prompt = TEXT_BOUNDARY_DETECTION_PROMPT.render_user(
        subtitles=subtitles,
        core_start=core_start,
        core_end=core_end,
        concise_description=execution_plan.concise_description,
        segmentation_profile=execution_plan.profile_name,
        segmentation_policy=execution_plan.profile.segmentation_policy,
        last_detection_point="None" if last_detection_point is None else str(last_detection_point),
        output_language=render_output_language_instruction(execution_plan.output_language),
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _materialize_committed_ranges(
    *,
    open_segment_start: float,
    candidate_boundaries: list[CandidateBoundary],
    segment_end_time: float | None = None,
) -> tuple[list[tuple[float, float, str]], float]:
    committed_end = candidate_boundaries[-1].timestamp if candidate_boundaries else segment_end_time
    if committed_end is None or committed_end <= open_segment_start:
        return [], open_segment_start

    ranges: list[tuple[float, float, str]] = []
    current_start = open_segment_start
    for boundary in candidate_boundaries:
        if boundary.timestamp <= current_start or boundary.timestamp > committed_end:
            continue
        ranges.append((current_start, boundary.timestamp, boundary.segment_title))
        current_start = boundary.timestamp
    if segment_end_time is not None and committed_end > current_start:
        ranges.append((current_start, committed_end, ""))
    return ranges, committed_end


def _generate_caption_payload(
    *,
    captioner,
    execution_plan: CanonicalExecutionPlan,
    subtitles_text: str,
) -> tuple[str, str]:
    fallback = _normalize_text(subtitles_text)
    if captioner is None:
        return _truncate_text(fallback, 240), fallback

    system_prompt = CAPTION_GENERATION_PROMPT.render_system()
    user_prompt = CAPTION_GENERATION_PROMPT.render_user(
        genres=", ".join(execution_plan.genres),
        concise_description=execution_plan.concise_description,
        segmentation_profile=execution_plan.profile_name,
        signal_priority="language",
        caption_policy=execution_plan.profile.caption_policy,
        subtitles=subtitles_text,
        output_language=render_output_language_instruction(execution_plan.output_language),
    )
    output = captioner.generate_single(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    payload = parse_json_response(output.get("text", ""))
    if not isinstance(payload, dict):
        payload = {}
    summary = _normalize_text(payload.get("summary", "")) or _truncate_text(fallback, 240)
    caption = _normalize_text(payload.get("caption", "")) or fallback
    return summary, caption


def _build_text_unit_from_range(
    *,
    start_time: float,
    end_time: float,
    boundary_title: str,
    subtitle_items: Sequence[dict[str, Any]],
    subtitles_text: str,
    captioner,
    execution_plan: CanonicalExecutionPlan,
    unit_id: str,
) -> AtlasUnit:
    segment_subtitle_items, segment_subtitles = get_subtitle_in_segment(list(subtitle_items), start_time, end_time)
    normalized_subtitles = _normalize_text(segment_subtitles)
    if not normalized_subtitles:
        normalized_subtitles = _normalize_text(subtitles_text)
    if not normalized_subtitles:
        raise ValueError("text-first parsing requires subtitle text")

    summary, caption = _generate_caption_payload(
        captioner=captioner,
        execution_plan=execution_plan,
        subtitles_text=normalized_subtitles,
    )
    title = boundary_title or summary or caption
    if not title and segment_subtitle_items:
        title = _normalize_text(segment_subtitle_items[0].get("text", ""))
    return _build_unit(
        unit_id=unit_id,
        start_time=start_time,
        end_time=end_time,
        title=title,
        summary=summary,
        caption=caption,
        subtitles_text=normalized_subtitles,
    )


def build_text_units(
    *,
    text_segmentor,
    captioner,
    execution_plan: CanonicalExecutionPlan,
    subtitle_items: Sequence[dict[str, Any]] | None,
    subtitles_text: str,
    verbose: bool,
) -> list[AtlasUnit]:

    normalized_items = [item for item in (subtitle_items or []) if isinstance(item, dict)]
    if normalized_items:
        duration = max(float(item.get("end", 0.0) or 0.0) for item in normalized_items)
    else:
        duration = 0.0

    units: list[AtlasUnit] = []
    caption_futures = []
    next_unit_id = 1
    open_segment_start = 0.0

    chunk_size_sec = max(1, int(execution_plan.chunk_size_sec))
    chunk_overlap_sec = max(0, int(execution_plan.chunk_overlap_sec))
    chunk_start = 0.0
    
    import time
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        while chunk_start < max(duration, 0.1):
            
            started_at = time.time()
            
            core_end = min(chunk_start + chunk_size_sec, duration)
            window_start = max(0.0, chunk_start - chunk_overlap_sec)
            window_end = min(duration, core_end + chunk_overlap_sec)
            _, subtitles_in_window = get_subtitle_in_segment(list(normalized_items), window_start, window_end)
            messages = _build_chunk_messages(
                execution_plan=execution_plan,
                subtitles=subtitles_in_window,
                core_start=chunk_start,
                core_end=core_end,
                last_detection_point=open_segment_start,
            )
            output = text_segmentor.generate_single(messages=messages) if text_segmentor is not None else {"text": []}
            
            payload = parse_json_response(output.get("text", ""))
            if not isinstance(payload, list):
                payload = []

            chunk_boundaries: list[CandidateBoundary] = []
            for item in payload:
                if not isinstance(item, dict):
                    continue
                try:
                    timestamp = float(item.get("timestamp", 0.0))
                except Exception:
                    continue
                if not (chunk_start < timestamp < core_end):
                    continue
                chunk_boundaries.append(
                    CandidateBoundary(
                        timestamp=timestamp,
                        boundary_rationale=str(item.get("boundary_rationale", "")).strip(),
                        segment_title=str(item.get("segment_title", "")).strip(),
                        confidence=_clamp_confidence(item.get("confidence", 0.0)),
                    )
                )
            chunk_boundaries = _dedupe_boundaries(chunk_boundaries)

            committed_ranges, open_segment_start = _materialize_committed_ranges(
                open_segment_start=open_segment_start,
                candidate_boundaries=chunk_boundaries,
            )
            
            if verbose:
                print(f"[Duration: {duration}; Chunk {chunk_start}-{core_end}] Candidate boundary detection completed in {time.time() - started_at:.2f}s | Boundaries kept: {len(chunk_boundaries)}")
            
            for start_time, end_time, boundary_title in committed_ranges:
                future = executor.submit(
                    _build_text_unit_from_range,
                    start_time=start_time,
                    end_time=end_time,
                    boundary_title=boundary_title,
                    subtitle_items=normalized_items,
                    subtitles_text=subtitles_text,
                    captioner=captioner,
                    execution_plan=execution_plan,
                    unit_id=f"unit_{next_unit_id:04d}",
                )
                caption_futures.append(future)
                next_unit_id += 1

            if core_end >= duration:
                break
            next_chunk_start = chunk_boundaries[-1].timestamp if chunk_boundaries else core_end
            chunk_start = next_chunk_start if next_chunk_start > chunk_start else core_end

        tail_ranges, _ = _materialize_committed_ranges(
            open_segment_start=open_segment_start,
            candidate_boundaries=[],
            segment_end_time=duration,
        )
        for start_time, end_time, boundary_title in tail_ranges:
            future = executor.submit(
                _build_text_unit_from_range,
                start_time=start_time,
                end_time=end_time,
                boundary_title=boundary_title,
                subtitle_items=normalized_items,
                subtitles_text=subtitles_text,
                captioner=captioner,
                execution_plan=execution_plan,
                unit_id=f"unit_{next_unit_id:04d}",
            )
            caption_futures.append(future)
            next_unit_id += 1

        for future in concurrent.futures.as_completed(caption_futures):
            units.append(future.result())

    if units:
        units.sort(key=lambda item: item.start_time)
        return units

    fallback_text = _normalize_text(subtitles_text)
    if not fallback_text:
        raise ValueError("text-first parsing requires subtitle text")
    return [
        _build_text_unit_from_range(
            start_time=0.0,
            end_time=duration,
            boundary_title="",
            subtitle_items=normalized_items,
            subtitles_text=fallback_text,
            captioner=captioner,
            execution_plan=execution_plan,
            unit_id="unit_0001",
        )
    ]
