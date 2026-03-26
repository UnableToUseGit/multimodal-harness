# -*- coding: utf-8 -*-
"""Prompt templates used by the derived atlas pipeline."""

from .specs import PromptSpec

DERIVED_CANDIDATE_PROMPT = PromptSpec(
    name="DERIVED_CANDIDATE_PROMPT",
    purpose="Select canonical segments relevant to a task-aware derived atlas request.",
    system_template=(
        "You select source segments for task-aware derivation. "
        "Return strict JSON only with a `candidates` array."
    ),
    user_template="""
You will receive:
- a task request
- canonical atlas segments with ids, titles, time ranges, and detailed captions

Your task:
Select the canonical segments relevant to the task.

Output format:
Return ONLY strict JSON in this format:
{{
  "candidates": [
    {{
      "segment_id": "<canonical segment id>",
      "intent": "<what information this derived segment should contribute>",
      "grounding_instruction": "<how to refine the source segment into a tighter sub-clip>"
    }}
  ]
}}

Task Request:
{task_request}

Canonical Segments:
{canonical_segments}
""".strip(),
    input_fields=("task_request", "canonical_segments"),
    output_contract="strict JSON object with candidates array",
    tags=("derived", "candidate"),
)


DERIVED_GROUNDING_PROMPT = PromptSpec(
    name="DERIVED_GROUNDING_PROMPT",
    purpose="Refine task-aware clip boundaries inside a source canonical segment.",
    system_template=(
        "You refine task-aware clip boundaries inside a source canonical segment. "
        "Return strict JSON only with `start_time` and `end_time`."
    ),
    user_template="""
You will receive:
- one source canonical segment
- the task intent for this segment
- a grounding instruction

Your task:
Refine a task-aware sub-clip.
Use absolute times if confident, otherwise use offsets relative to the source segment start.

Output format:
Return ONLY strict JSON in this format:
{{
  "start_time": 0.0,
  "end_time": 0.0
}}

Source Segment ID: {segment_id}
Source Segment Range: {segment_start_time:.1f}-{segment_end_time:.1f}
Intent: {intent}
Grounding Instruction: {grounding_instruction}
Summary: {summary}
Detail: {detail}
Subtitles:
{subtitles}
""".strip(),
    input_fields=(
        "segment_id",
        "segment_start_time",
        "segment_end_time",
        "intent",
        "grounding_instruction",
        "summary",
        "detail",
        "subtitles",
    ),
    output_contract="strict JSON object with start_time and end_time",
    tags=("derived", "grounding"),
)


DERIVED_CAPTION_PROMPT = PromptSpec(
    name="DERIVED_CAPTION_PROMPT",
    purpose="Write metadata for a task-aware derived atlas segment.",
    system_template=(
        "You write metadata for a derived atlas segment. "
        "Return strict JSON only with `title`, `summary`, and `caption`."
    ),
    user_template="""
You will receive:
- the task request
- the source canonical segment id
- the derived time range
- the intent and grounding instruction
- source summary and detail
- pruned subtitles for the refined sub-clip

Your task:
Write metadata for a derived atlas segment.

Output format:
Return ONLY strict JSON in this format:
{{
  "title": "<derived segment title>",
  "summary": "<1-2 sentence summary>",
  "caption": "<detailed task-aware description>"
}}

Task Request: {task_request}
Source Segment ID: {segment_id}
Derived Range: {start_time:.1f}-{end_time:.1f}
Intent: {intent}
Grounding Instruction: {grounding_instruction}
Source Summary: {summary}
Source Detail: {detail}
Subtitles:
{subtitles}
""".strip(),
    input_fields=(
        "task_request",
        "segment_id",
        "start_time",
        "end_time",
        "intent",
        "grounding_instruction",
        "summary",
        "detail",
        "subtitles",
    ),
    output_contract="strict JSON object with title, summary, and caption",
    tags=("derived", "caption"),
)
