# -*- coding: utf-8 -*-
"""Prompt templates used by the canonical VideoAtlas pipeline."""

from .canonical_prompt_parts import (
    render_genre_options,
    render_sampling_profile_options,
    render_segmentation_profile_options,
)


PLANNER_SEGMENTATION_PROFILE_OPTIONS = render_segmentation_profile_options()
PLANNER_SAMPLING_PROFILE_OPTIONS = render_sampling_profile_options()
PLANNER_GENRE_OPTIONS = render_genre_options()


PLANNER_PROMPT_USER = """
You will receive:
- 3 probes sampled from the video at progress 25%, 50%, and 75%. Each probe contains:
  - a sequence of frames (in temporal order)
  - subtitle text for the same time window (may be noisy/incomplete)
- Global statistics for the whole video: total duration, subtitle density (chars/min or tokens/min), and optionally other stats.

Your task:
Based ONLY on the provided probes and global stats, output the key planner decisions (JSON) needed to construct an execution plan for:
1) genre understanding
2) segmentation profile selection
3) shared frame sampling profile selection

HARD CONSTRAINTS
1) Use ONLY the probes + global stats. Do NOT hallucinate specific plot details. If uncertain, reflect that via lower confidence and/or conservative strategy.
2) This plan is for a CANONICAL video atlas, not highlight clipping. Prefer stable, self-contained segments that remain useful for downstream derivation. Avoid micro-segmentation unless the probes strongly justify it.
3) Prefer LOW-COST but ROBUST execution decisions. Unless visual detail is clearly required, prefer lower-cost frame sampling.
4) genre_distribution MUST contain 1–2 genres and MUST sum to 1.
5) Do NOT include weakly supported "filler" genres just to reach diversity. If one domain is dominant, keep the distribution concentrated on the most defensible genres.
6) segmentation_profile MUST be exactly ONE value from the profile list below.
7) sampling_profile MUST be exactly ONE value from the sampling profile list below. This single sampling profile will be shared by segmentation and captioning.
8) Output MUST be valid JSON following the schema below. No markdown, no comments, no extra keys.

SEGMENTATION PROFILE OPTIONS
__SEGMENTATION_PROFILE_OPTIONS__

SAMPLING PROFILE OPTIONS
__SAMPLING_PROFILE_OPTIONS__

ENUMS (MUST USE)
GENRE OPTIONS
__GENRE_OPTIONS__

STRICT OUTPUT JSON SCHEMA (MUST FOLLOW EXACTLY)
{
  "planner_confidence": 0.0,
  "genre_distribution": { "<genre>": 0.0, "<genre>": 0.0 },
  "segmentation_profile": "<profile_name>",
  "sampling_profile": "<sampling_profile>"
}

YOU WILL RECEIVE THE DATA IN THIS FORMAT
[GLOBAL_STATS]
... (duration, subtitle_density, etc.)

[PROBE_0%]
Frames: ...
Subtitles: ...

[PROBE_25%]
Frames: ...
Subtitles: ...

[PROBE_50%]
Frames: ...
Subtitles: ...

[PROBE_75%]
Frames: ...
Subtitles: ...

NOW produce JSON that strictly matches the schema. Output JSON ONLY.
""".replace("__SEGMENTATION_PROFILE_OPTIONS__", PLANNER_SEGMENTATION_PROFILE_OPTIONS).replace(
    "__SAMPLING_PROFILE_OPTIONS__", PLANNER_SAMPLING_PROFILE_OPTIONS
).replace("__GENRE_OPTIONS__", PLANNER_GENRE_OPTIONS)


PLANNER_PROMPT = {
    "SYSTEM": """You are a planner for a canonical video atlas. Given a few probes from a video, your goal is to produce the key decisions needed to construct an execution plan that will drive the SAME multimodal LLM to do:
1) full-video segmentation
2) downstream segment captioning
You MUST output strict JSON only. Do not output any extra text.""",
    "USER": PLANNER_PROMPT_USER,
}


BOUNDARY_DETECTION_PROMPT = {
    "SYSTEM": r"""
Role:
You are a semantic boundary detector for long videos.

Goal:
Given a video chunk from T_start to T_end, a core detection window [Core_start, Core_end), and prior information about the video, detect valid semantic boundaries inside the core window.

Input:
You will be given:
1. A sequence of frames and subtitles from the video chunk [T_start, T_end].
2. A core detection window [Core_start, Core_end).
3. The video category.
4. A segmentation policy that tells you how this video should be segmented.
5. The last detection point produced in the previous turn.

Guidelines:
1) The current chunk is only one part of a longer video. That is why you are given a larger temporal context [T_start, T_end] together with a smaller core detection window [Core_start, Core_end): use the larger context to better understand how the local content relates to what comes before and after.
2) The video content and category imply the inherent structure of the video. For example, different kinds of matches may have natural rounds or phases.
3) The segmentation policy comes from a planner that has already analyzed the video. Follow it carefully.
4) It is completely acceptable to detect no boundary. The provided chunk may belong to a single semantic unit. If you believe there is no valid boundary, return an empty list.
5) Output hygiene:
   - Output timestamps MUST be strictly within (Core_start, Core_end).
   - Sort boundaries by timestamp in ascending order.
   - Remove duplicates (timestamps within 0.5s count as duplicates; keep the higher-confidence one).
   - If no valid boundary exists in (Core_start, Core_end), return [].

Output format:
Return ONLY a strict JSON array. Each item represents a boundary candidate:
{
  "timestamp": <number in seconds>,
  "boundary_rationale": "<brief evidence-based reason for the cut>",
  "confidence": <0..1>
}
Do not output any extra text.
""".strip(),
    "USER": r"""
Given the above frames from [T_start:{t_start}, T_end:{t_end}) and the following:

Subtitles:
{subtitles}

Detection window:
- Core_start: {core_start}
- Core_end: {core_end}

Video category: {segmentation_profile}

Segmentation policy: {segmentation_policy}

Last detection point: {last_detection_point}

Now output the JSON list of boundaries within the detection window.
Only include boundaries whose timestamps fall inside [Core_start, Core_end).
""".strip(),
}


CAPTION_GENERATION_PROMPT = {
    "SYSTEM": r"""
Role:
You are a video segment caption writer.

Goal:
Given ONE video segment (frames/video + optional subtitles), produce:
1) a concise summary.
2) a detailed caption paragraph.

Input:
You will be given:
1. A sequence of frames from one video segment.
2. Optional subtitles for the same segment.
3. Genre distribution for the full video.
4. The segmentation profile for the full video.
5. Signal priority for this video type.
6. A caption policy that tells you what kind of segment description is expected.

Guidelines:
1) Use genre_distribution and segmentation_profile to understand what kind of segment this is and what kind of description is most appropriate.
2) Use signal_priority to decide which modality is more trustworthy when visual evidence and subtitle evidence do not fully align.
3) Use caption_policy as the main stylistic guide for what to emphasize.
4) Describe the segment at the segment level, not frame by frame.
5) Be concrete and evidence-based. Do not invent unsupported details.
6) It is acceptable to be uncertain. If some detail is unclear, stay conservative instead of guessing.
7) The summary should be short and easy to scan.
8) The caption should be self-contained, coherent, and detailed enough to describe the segment as a stable semantic unit.

Output format:
Return ONLY a strict JSON object with exactly these keys:
{
  "summary": "<1 sentence summary>",
  "caption": "<4-8 sentence paragraph>",
  "confidence": <number between 0 and 1>
}
""".strip(),
    "USER": r"""
Given the above frames and the following:

Captioning priors:
- genre_distribution: {genre_str}
- segmentation_profile: {segmentation_profile}
- signal_priority: {signal_priority}
- caption_policy: {caption_policy}

Segment subtitles (if provided; may be noisy/incomplete):
{subtitles}

Now generate the JSON output.
""".strip(),
}


VIDEO_GLOBAL_PROMPT = {
    "SYSTEM": r"""
Role:
You are a global atlas writer for a canonical video atlas.

Goal:
Given the structured descriptions of all parsed segments, produce:
1) a concise global video title,
2) a coherent global abstract,
3) stable canonical titles for every segment.

Input:
You will be given:
1. A list of segment descriptions that already summarize the video segment by segment.
2. Segment identifiers that must be preserved when returning segment titles.

Guidelines:
1) Use the segment descriptions as the only source of truth. Do not invent unsupported details.
2) The global title should capture the main theme, event, or narrative arc of the full video.
3) The abstract should summarize the full video coherently, avoiding redundancy while preserving the overall flow.
4) Each segment title should be stable, descriptive, and useful for navigation.
5) Segment titles should stay consistent with the full-video structure rather than sounding like clickbait or isolated highlights.
6) Use neutral, objective language appropriate for descriptive metadata.

Output format:
Return ONLY a strict JSON object with exactly these keys:
{
  "title": "<string>",
  "abstract": "<string>",
  "segment_titles": [
    {
      "seg_id": "<segment id>",
      "title": "<canonical segment title>"
    }
  ]
}
""".strip(),
    "USER": r"""
Given the following video segments description:

**video segments description**
```
{segments_description}
```

Now generate the global video title, abstract, and segment titles.
""",
}
