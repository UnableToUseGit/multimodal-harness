from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from ...parsing import parse_json_response
from ...persistence import format_hms_time_range, slugify_segment_title
from ...prompts import CANONICAL_STRUCTURE_COMPOSITION_PROMPT
from ...schemas import AtlasSegment, AtlasUnit, CanonicalCompositionResult
from .language import render_output_language_instruction


class CanonicalStructureCompositionError(ValueError):
    pass


def serialize_units_for_composition(units: Sequence[AtlasUnit]) -> str:
    lines: list[str] = []
    for index, unit in enumerate(units, start=1):
        lines.extend(
            [
                f"[UNIT_{index}]",
                f"unit_id: {unit.unit_id}",
                f"title: {unit.title}",
                f"time_range: {format_hms_time_range(unit.start_time, unit.end_time)}",
                f"summary: {unit.summary}",
                f"caption: {unit.caption}",
                "subtitles_text:",
                unit.subtitles_text.strip(),
                "",
            ]
        )
    return "\n".join(lines).strip()


def build_canonical_structure_composition_messages(
    units: Sequence[AtlasUnit],
    concise_description: str = "",
    genres: Sequence[str] | None = None,
    structure_request: str = "",
    output_language: str = "en",
) -> list[dict[str, Any]]:
    system_prompt, user_prompt = CANONICAL_STRUCTURE_COMPOSITION_PROMPT.render(
        units_description=serialize_units_for_composition(units),
        concise_description=concise_description,
        genres=list(genres or []),
        structure_request=structure_request,
        output_language=render_output_language_instruction(output_language),
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _normalize_unit_ids(raw_unit_ids: Any) -> list[str]:
    if not isinstance(raw_unit_ids, list):
        raise CanonicalStructureCompositionError("Each composed segment must include a non-empty unit_ids list")

    unit_ids: list[str] = []
    for item in raw_unit_ids:
        if not isinstance(item, str):
            raise CanonicalStructureCompositionError("unit_ids must only contain strings")
        unit_id = item.strip()
        if not unit_id:
            raise CanonicalStructureCompositionError("unit_ids must not contain empty strings")
        if unit_id in unit_ids:
            raise CanonicalStructureCompositionError(f"Duplicate unit_id within a segment is not allowed: {unit_id}")
        unit_ids.append(unit_id)

    if not unit_ids:
        raise CanonicalStructureCompositionError("Each composed segment must include at least one unit_id")
    return unit_ids


def _build_segment_folder_name(segment_id: str, title: str, start_time: float, end_time: float) -> str:
    safe_segment_id = segment_id.replace("_", "-")
    safe_title = slugify_segment_title(title)
    time_range = format_hms_time_range(start_time, end_time)
    return f"{safe_segment_id}-{safe_title}-{time_range}"


def _compose_segments_from_payload(
    payload_segments: Sequence[dict[str, Any]],
    units: Sequence[AtlasUnit],
) -> list[AtlasSegment]:
    unit_lookup = {unit.unit_id: unit for unit in units}
    ordered_unit_ids = [unit.unit_id for unit in units]

    flattened_unit_ids: list[str] = []
    composed_segments: list[AtlasSegment] = []

    for index, segment_payload in enumerate(payload_segments, start=1):
        if not isinstance(segment_payload, dict):
            raise CanonicalStructureCompositionError("Each segment entry must be a JSON object")

        unit_ids = _normalize_unit_ids(segment_payload.get("unit_ids"))
        for unit_id in unit_ids:
            if unit_id not in unit_lookup:
                raise CanonicalStructureCompositionError(f"Unknown unit_id referenced by composition result: {unit_id}")

        flattened_unit_ids.extend(unit_ids)
        first_unit = unit_lookup[unit_ids[0]]
        last_unit = unit_lookup[unit_ids[-1]]

        segment_id = str(segment_payload.get("segment_id", "")).strip() or f"seg_{index:04d}"
        title = str(segment_payload.get("title", "")).strip() or first_unit.title
        summary = str(segment_payload.get("summary", "")).strip() or first_unit.summary
        composition_rationale = str(segment_payload.get("composition_rationale", "")).strip()
        if not composition_rationale:
            composition_rationale = str(segment_payload.get("rationale", "")).strip()
            
        segment_folder_name = _build_segment_folder_name(segment_id, title, first_unit.start_time, last_unit.end_time)
        for unit in units:
            unit.relative_clip_path = Path(f'{segment_folder_name}/{unit.folder_name}/video_clip.mp4')
            unit.relative_subtitles_path = Path(f'{segment_folder_name}/{unit.folder_name}/SUBTITLES.md')

        composed_segments.append(
            AtlasSegment(
                segment_id=segment_id,
                unit_ids=unit_ids,
                title=title,
                start_time=first_unit.start_time,
                end_time=last_unit.end_time,
                summary=summary,
                composition_rationale=composition_rationale,
                folder_name=segment_folder_name,
                caption=str(segment_payload.get("caption", "")).strip(),
                subtitles_text=str(segment_payload.get("subtitles_text", "")).strip(),
            )
        )

    if flattened_unit_ids != ordered_unit_ids:
        raise CanonicalStructureCompositionError(
            "Composed segments must cover all units exactly once, in the original order, without gaps or reordering"
        )

    return composed_segments


def parse_canonical_structure_composition_result(
    payload: dict[str, Any],
    units: Sequence[AtlasUnit],
    structure_request: str = "",
) -> CanonicalCompositionResult:
    if not isinstance(payload, dict):
        raise CanonicalStructureCompositionError("Structure composition output must be a JSON object")

    segments_payload = payload.get("segments")
    if not isinstance(segments_payload, list):
        raise CanonicalStructureCompositionError("Structure composition output must include a segments list")

    title = str(payload.get("title", "")).strip()
    abstract = str(payload.get("abstract", "")).strip()
    composition_rationale = str(payload.get("composition_rationale", "")).strip()

    return CanonicalCompositionResult(
        title=title,
        abstract=abstract,
        segments=_compose_segments_from_payload(segments_payload, units),
        composition_rationale=composition_rationale,
        structure_request=structure_request,
    )


def compose_canonical_structure(
    structure_composer,
    units: Sequence[AtlasUnit],
    concise_description: str = "",
    genres: Sequence[str] | None = None,
    structure_request: str = "",
    output_language: str = "en",
) -> CanonicalCompositionResult:
    if structure_composer is None:
        raise CanonicalStructureCompositionError("A structure_composer instance is required")
    if not units:
        raise CanonicalStructureCompositionError("At least one unit is required to compose canonical structure")

    messages = build_canonical_structure_composition_messages(
        units=units,
        concise_description=concise_description,
        genres=genres,
        structure_request=structure_request,
        output_language=output_language,
    )
    output = structure_composer.generate_single(messages=messages)
    payload = output.get("json")
    if not isinstance(payload, dict):
        payload = parse_json_response(output.get("text"))

    if not isinstance(payload, dict) or not payload:
        raise CanonicalStructureCompositionError("Structure composer did not return a valid JSON object")

    return parse_canonical_structure_composition_result(
        payload=payload,
        units=units,
        structure_request=structure_request,
    )


@dataclass(frozen=True)
class CanonicalStructureComposer:
    structure_composer: Any

    def compose(
        self,
        units: Sequence[AtlasUnit],
        concise_description: str = "",
        genres: Sequence[str] | None = None,
        structure_request: str = "",
        output_language: str = "en",
    ) -> CanonicalCompositionResult:
        return compose_canonical_structure(
            self.structure_composer,
            units=units,
            concise_description=concise_description,
            genres=genres,
            structure_request=structure_request,
            output_language=output_language,
        )
