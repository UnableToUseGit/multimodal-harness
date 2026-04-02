from __future__ import annotations

from typing import Any

from ...parsing import parse_json_response
from ...prompts import TEXT_FIRST_PLANNER_PROMPT
from ...schemas import CanonicalCreateRequest, CanonicalExecutionPlan
from ...utils import get_frame_indices, prepare_video_input
from .execution_plan_builder import ExecutionPlanBuilderMixin
from .language import render_output_language_instruction


class _ExecutionPlanBuilder(ExecutionPlanBuilderMixin):
    def __init__(self, chunk_size_sec: int, chunk_overlap_sec: int) -> None:
        self.chunk_size_sec = chunk_size_sec
        self.chunk_overlap_sec = chunk_overlap_sec


def _serialize_subtitle_items(subtitle_items: list[dict[str, Any]] | None) -> str:
    lines: list[str] = []
    for index, item in enumerate(subtitle_items or [], start=1):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        start = item.get("start", "")
        end = item.get("end", "")
        lines.append(f"[{index}] {start} -> {end}: {text}")
    return "\n".join(lines).strip()


def _sample_subtitle_probe(subtitle_items: list[dict[str, Any]] | None, probe_window_size: int = 3) -> str:
    items = [item for item in (subtitle_items or []) if isinstance(item, dict) and str(item.get("text", "")).strip()]
    if not items:
        return "[NO_SUBTITLES]"
    if len(items) <= probe_window_size * 3:
        return _serialize_subtitle_items(items)

    anchor_indices = (0, len(items) // 2, len(items) - 1)
    selected_indices: list[int] = []
    seen: set[int] = set()
    half_window = max(0, probe_window_size // 2)
    for anchor in anchor_indices:
        start = max(0, anchor - half_window)
        end = min(len(items), anchor + half_window + 1)
        for index in range(start, end):
            if index in seen:
                continue
            seen.add(index)
            selected_indices.append(index)

    selected_items = [items[index] for index in selected_indices]
    return _serialize_subtitle_items(selected_items)


def _summarize_source_metadata(source_metadata: Any) -> str:
    if source_metadata is None:
        return ""
    if hasattr(source_metadata, "to_dict"):
        payload = source_metadata.to_dict()
    elif isinstance(source_metadata, dict):
        payload = source_metadata
    else:
        payload = {
            key: getattr(source_metadata, key)
            for key in dir(source_metadata)
            if not key.startswith("_") and not callable(getattr(source_metadata, key))
        }
    lines: list[str] = []
    for key in ("title", "introduction", "author", "publish_date", "duration_seconds"):
        value = payload.get(key)
        if value in (None, "", []):
            continue
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def _collect_visual_probe(video_path, max_frames: int = 20) -> list[dict[str, str]]:
    frame_indices = get_frame_indices(str(video_path), 0, None, fps=0.1)
    if len(frame_indices) == 0:
        return []
    if max_frames > 0:
        frame_indices = frame_indices[:max_frames]
    frame_base64_list, timestamps = prepare_video_input(str(video_path), frame_indices, max_resolution=480, max_workers=4)
    probes: list[dict[str, str]] = []
    for frame_base64, timestamp in zip(frame_base64_list, timestamps):
        probes.append(
            {
                "timestamp": f"{timestamp:.1f}",
                "image_url": f"data:image/jpeg;base64,{frame_base64}",
            }
        )
    return probes


def build_text_first_execution_plan(
    *,
    request: CanonicalCreateRequest,
    planner,
    subtitle_items,
    output_language: str,
    verbose: bool,
    chunk_size_sec: int = 600,
    chunk_overlap_sec: int = 20,
) -> CanonicalExecutionPlan:
    del verbose

    if planner is None:
        raise ValueError("planner is required")

    subtitle_probe = _sample_subtitle_probe(subtitle_items)
    if request.video_path is not None:
        input_kind = "video_with_visual_access"
    else:
        input_kind = "audio"

    metadata_summary = _summarize_source_metadata(request.source_metadata)
    system_prompt = TEXT_FIRST_PLANNER_PROMPT.render_system()
    user_prompt = TEXT_FIRST_PLANNER_PROMPT.render_user(
        input_kind=input_kind,
        subtitle_probe=subtitle_probe,
        metadata_summary=metadata_summary or "[NONE]",
        output_language=render_output_language_instruction(output_language),
    )
    user_content: list[dict[str, Any]] = [
        {"type": "text", "text": user_prompt},
    ]

    if request.video_path is not None and request.video_path.exists():
        try:
            visual_probe = _collect_visual_probe(request.video_path)
        except Exception:
            visual_probe = []
        if visual_probe:
            user_content.append({"type": "text", "text": "Sparse visual probe frames:"})
            for item in visual_probe:
                user_content.append({"type": "text", "text": f"<{item['timestamp']} seconds>"})
                user_content.append({"type": "image_url", "image_url": {"url": item["image_url"]}})

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    generated = planner.generate_single(messages=messages)
    payload = generated.get("json")
    if not isinstance(payload, dict):
        payload = parse_json_response(generated.get("text", ""))
    if not isinstance(payload, dict):
        payload = {}
    payload["output_language"] = output_language or "en"

    builder = _ExecutionPlanBuilder(chunk_size_sec=chunk_size_sec, chunk_overlap_sec=chunk_overlap_sec)
    planner_reasoning_content = ""
    try:
        planner_reasoning_content = generated["response"]["choices"][0]["message"]["reasoning"]
    except Exception:
        planner_reasoning_content = ""
    return builder._construct_execution_plan(payload, planner_reasoning_content)
