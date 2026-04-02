# -*- coding: utf-8 -*-
"""Prompt templates used by the canonical VideoAtlas pipeline."""

from .canonical_prompt_parts import (
    render_genre_options,
    render_profile_options,
    render_sampling_profile_options,
    render_segmentation_profile_options,
)
from .specs import PromptSpec


PLANNER_SEGMENTATION_PROFILE_OPTIONS = render_segmentation_profile_options()
TEXT_FIRST_PROFILE_OPTIONS = render_profile_options()
PLANNER_SAMPLING_PROFILE_OPTIONS = render_sampling_profile_options()
PLANNER_GENRE_OPTIONS = render_genre_options()


PLANNER_PROMPT_USER = """
You will receive:
- 4 probes sampled from the video at progress 0%, 50%, and 100%. Each probe contains:
  - a sequence of frames (in temporal order)
  - subtitle text for the same time window (may be noisy/incomplete)
- Global statistics for the whole video: total duration, subtitle density (chars/min or tokens/min), and optionally other stats.

Your task:
Based ONLY on the provided probes and global stats, output the key planner decisions (JSON) needed to construct an execution plan for:
1) genre understanding
2) concise description of this video
3) segmentation profile selection
4) shared frame sampling profile selection

Guidelines:
1) Use ONLY the probes + global stats. Do NOT hallucinate specific plot details. If uncertain, reflect that via lower confidence and/or conservative strategy.
2) The genres are provided at most 2.
3) Provide a brief description of the video to supply necessary context for the subsequent process.
4) segmentation_profile MUST be exactly ONE value from the profile list below.
5) sampling_profile MUST be exactly ONE value from the sampling profile list below. This single sampling profile will be shared by segmentation and captioning.
6) Output MUST be valid JSON following the schema below. No markdown, no comments, no extra keys.

SEGMENTATION PROFILE OPTIONS
__SEGMENTATION_PROFILE_OPTIONS__

SAMPLING PROFILE OPTIONS
__SAMPLING_PROFILE_OPTIONS__

ENUMS (MUST USE)
GENRE OPTIONS
__GENRE_OPTIONS__

STRICT OUTPUT JSON SCHEMA (MUST FOLLOW EXACTLY)
{{
  "planner_confidence": 0.0,
  "genres": ["<genre_1>", "<genre_2>"],
  "concise_description": "<concise_description>",
  "segmentation_profile": "<profile_name>",
  "sampling_profile": "<sampling_profile>"
}}

YOU WILL RECEIVE THE DATA IN THIS FORMAT
[GLOBAL_STATS]
... (duration, subtitle_density, etc.)

[PROBE_0%]
Frames: ...
Subtitles: ...

[PROBE_50%]
Frames: ...
Subtitles: ...

[PROBE_100%]
Frames: ...
Subtitles: ...

NOW produce JSON that strictly matches the schema. Output JSON ONLY.
""".replace("__SEGMENTATION_PROFILE_OPTIONS__", PLANNER_SEGMENTATION_PROFILE_OPTIONS).replace(
    "__SAMPLING_PROFILE_OPTIONS__", PLANNER_SAMPLING_PROFILE_OPTIONS
).replace("__GENRE_OPTIONS__", PLANNER_GENRE_OPTIONS)


PLANNER_PROMPT = PromptSpec(
    name="PLANNER_PROMPT",
    purpose="Plan canonical atlas segmentation and shared sampling decisions from probe inputs.",
    system_template="""You are a planner for a canonical video atlas. Given a few probes from a video, your goal is to produce the key decisions needed to construct an execution plan that will drive the SAME multimodal LLM to do:
1) full-video segmentation
2) downstream segment captioning
You MUST output strict JSON only. Do not output any extra text.""",
    user_template=PLANNER_PROMPT_USER,
    input_fields=(),
    output_contract="strict JSON object with planner_confidence, genres, concise_description, segmentation_profile, and sampling_profile",
    tags=("canonical", "planner"),
)


TEXT_FIRST_PLANNER_PROMPT_USER = """
You will receive:
- The input kind. It will be exactly one of:
  - video_with_visual_access
  - video_without_visual_access
  - audio
- A small subtitle probe assembled from representative excerpts of the source text. This probe is only a partial view, not the full subtitle file.
- An optional metadata summary.
- A required output language instruction that tells you what language all generated planner text must use.
- For video_with_visual_access only: sparse visual probe frames may also be provided after the user text.

Your task:
Based ONLY on the provided subtitle probe, optional metadata summary, and optional sparse visual probe frames, output the key planner decisions (JSON) needed to construct an execution plan for:
1) profile selection
2) genre understanding
3) concise description of this content

Guidelines:
1) Use ONLY the provided probe context. Do NOT hallucinate detailed unseen content.
2) profile MUST be exactly ONE value from the profile list below.
3) genres must contain at most 2 items, and every item MUST come from the genre list below.
4) concise_description should be brief, stable, and useful as global context for later segmentation and composition.
5) If the content looks ambiguous, choose the most conservative profile.
6) Output MUST be valid JSON following the schema below. No markdown, no comments, no extra keys.
7) The concise_description must follow the output language instruction exactly.

PROFILE OPTIONS
__PROFILE_OPTIONS__

GENRE OPTIONS
__GENRE_OPTIONS__

STRICT OUTPUT JSON SCHEMA (MUST FOLLOW EXACTLY)
{{
  "planner_confidence": 0.0,
  "genres": ["<genre_1>", "<genre_2>"],
  "concise_description": "<concise_description>",
  "profile": "<profile_name>"
}}

YOU WILL RECEIVE THE DATA IN THIS FORMAT
[INPUT_KIND]
{input_kind}

[SUBTITLE_PROBE]
{subtitle_probe}

[METADATA_SUMMARY]
{metadata_summary}

[OUTPUT_LANGUAGE]
{output_language}

NOW produce JSON that strictly matches the schema. Output JSON ONLY.
""".replace("__PROFILE_OPTIONS__", TEXT_FIRST_PROFILE_OPTIONS).replace("__GENRE_OPTIONS__", PLANNER_GENRE_OPTIONS)


TEXT_FIRST_PLANNER_PROMPT = PromptSpec(
    name="TEXT_FIRST_PLANNER_PROMPT",
    purpose="Plan canonical text-first execution decisions from subtitle probes, optional metadata, and optional sparse visual probes.",
    system_template="""You are a planner for a text-first canonical atlas workflow. Given sampled subtitle evidence, optional metadata, and optional sparse visual frames, produce the minimal strict-JSON planning result needed for downstream execution. Output JSON only.""",
    user_template=TEXT_FIRST_PLANNER_PROMPT_USER,
    input_fields=("input_kind", "subtitle_probe", "metadata_summary", "output_language"),
    output_contract="strict JSON object with planner_confidence, genres, concise_description, and profile",
    tags=("canonical", "planner", "text-first"),
)


BOUNDARY_DETECTION_PROMPT = PromptSpec(
    name="BOUNDARY_DETECTION_PROMPT",
    purpose="Detect semantic boundaries inside a long video chunk using local context.",
    system_template=r"""
Role:
You are a semantic boundary detector for long videos.

Goal:
Given a video chunk from T_start to T_end, a core detection window [Core_start, Core_end), and prior information about the video, detect valid semantic boundaries inside the core window.

Input:
You will be given:
1. A sequence of frames and subtitles from the video chunk [T_start, T_end].
2. A core detection window [Core_start, Core_end).
3. A concise description of the whole video.
4. The video category.
5. A segmentation policy that tells you how this video should be segmented.
6. The last detection point produced in the previous turn.
7. An output language instruction for all generated titles and rationales.
7. An output language instruction for all generated titles and rationales.

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
{{
  "timestamp": <number in seconds>,
  "boundary_rationale": "<brief evidence-based reason for the cut>",
  "confidence": <0..1>
}}
Do not output any extra text.
""".strip(),
    user_template=r"""
Given the above frames from [T_start:{t_start}, T_end:{t_end}) and the following:

Subtitles:
{subtitles}

Detection window:
- Core_start: {core_start}
- Core_end: {core_end}

Concise description: {concise_description}

Video category: {segmentation_profile}

Segmentation policy: {segmentation_policy}

Last detection point: {last_detection_point}

Output language instruction: {output_language}

Now output the JSON list of boundaries within the detection window.
Only include boundaries whose timestamps fall inside [Core_start, Core_end).
""".strip(),
    input_fields=(
        "t_start",
        "t_end",
        "subtitles",
        "core_start",
        "core_end",
        "concise_description",
        "segmentation_profile",
        "segmentation_policy",
        "last_detection_point",
        "output_language",
    ),
    output_contract="strict JSON array of boundary candidates",
    tags=("canonical", "boundary-detection"),
)


TEXT_BOUNDARY_DETECTION_PROMPT = PromptSpec(
    name="TEXT_BOUNDARY_DETECTION_PROMPT",
    purpose="Detect semantic boundaries inside a long video chunk using subtitles and text priors only.",
    system_template=r"""
Role:
You are a semantic boundary detector for subtitle-driven long videos.

Goal:
Given subtitles from a long video chunk, a core detection window [Core_start, Core_end), and prior information about the video, detect valid semantic boundaries inside the core window.

Input:
You will be given:
1. Subtitle text from the video chunk.
2. A core detection window [Core_start, Core_end).
3. A concise description of the whole video.
4. The video category.
5. A segmentation policy that tells you how this video should be segmented.
6. The last detection point produced in the previous turn.

Guidelines:
1) Use the subtitles as the primary source of truth for semantic structure.
2) The segmentation policy comes from a planner that has already analyzed the video. Follow it carefully.
3) It is completely acceptable to detect no boundary. If the chunk belongs to a single semantic unit, return an empty list.
4) Every time you detect a boundary point, you should simultaneously generate a title for the segment ending at that point. The title should be stable, descriptive, and useful for navigation.
5) Output hygiene:
   - Output timestamps MUST be strictly within (Core_start, Core_end).
   - Sort boundaries by timestamp in ascending order.
   - Remove duplicates (timestamps within 0.5s count as duplicates; keep the higher-confidence one).
   - If no valid boundary exists in (Core_start, Core_end), return [].

Output format:
Return ONLY a strict JSON array. Each item represents a boundary candidate:
{{
  "timestamp": <number in seconds>,
  "boundary_rationale": "<brief evidence-based reason for the cut>",
  "segment_title": "<concise title for the current segment that ends with the boundary>",
  "confidence": <0..1>
}}
""".strip(),
    user_template=r"""
Given the following:

Subtitles:
{subtitles}

Detection window:
- Core_start: {core_start}
- Core_end: {core_end}

Concise description: {concise_description}

Video category: {segmentation_profile}

Segmentation policy: {segmentation_policy}

Last detection point: {last_detection_point}

Output language instruction: {output_language}

Now output the JSON list of boundaries within the detection window.
Only include boundaries whose timestamps fall inside [Core_start, Core_end).

""".strip(),
    input_fields=(
        "subtitles",
        "core_start",
        "core_end",
        "concise_description",
        "segmentation_profile",
        "segmentation_policy",
        "last_detection_point",
        "output_language",
    ),
    output_contract="strict JSON array of boundary candidates",
    tags=("canonical", "boundary-detection", "text"),
)


CAPTION_GENERATION_PROMPT = PromptSpec(
    name="CAPTION_GENERATION_PROMPT",
    purpose="Generate segment-level canonical captions from frames and subtitles.",
    system_template=r"""
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
3. The top genres for the full video.
4. A concise description of the whole video.
4. The segmentation profile for the full video.
5. Signal priority for this video type.
6. A caption policy that tells you what kind of segment description is expected.
7. An output language instruction for all generated text.

Guidelines:
1) Use genres, concise_description, and segmentation_profile to understand what kind of segment this is and what kind of description is most appropriate.
2) Use signal_priority to decide which modality is more trustworthy when visual evidence and subtitle evidence do not fully align.
3) Use caption_policy as the main stylistic guide for what to emphasize.
4) Describe the segment at the segment level, not frame by frame.
5) Be concrete and evidence-based. Do not invent unsupported details.
6) It is acceptable to be uncertain. If some detail is unclear, stay conservative instead of guessing.
7) The summary should be short and easy to scan.
8) The caption should be self-contained, coherent, and detailed enough to describe the segment as a stable semantic unit.
9) The summary and caption must follow the output language instruction exactly.

Output format:
Return ONLY a strict JSON object with exactly these keys:
{{
  "summary": "<1 sentence summary>",
  "caption": "<4-8 sentence paragraph>",
  "confidence": <number between 0 and 1>
}}
""".strip(),
    user_template=r"""
Given the above frames and the following:

Captioning priors:
- genres: {genres}
- concise_description: {concise_description}
- segmentation_profile: {segmentation_profile}
- signal_priority: {signal_priority}
- caption_policy: {caption_policy}
- output_language: {output_language}

Segment subtitles (if provided; may be noisy/incomplete):
{subtitles}

Now generate the JSON output.
""".strip(),
    input_fields=("genres", "concise_description", "segmentation_profile", "signal_priority", "caption_policy", "subtitles", "output_language"),
    output_contract="strict JSON object with summary, caption, and confidence",
    tags=("canonical", "caption"),
)


CANONICAL_STRUCTURE_COMPOSITION_PROMPT = PromptSpec(
    name="CANONICAL_STRUCTURE_COMPOSITION_PROMPT",
    purpose="Compose canonical atlas units into final segment-level structure.",
    system_template=r"""
Role:
You are a canonical atlas structure composer.

Goal:
Given a full ordered list of units from a video atlas, compose them into final atlas segments.

Input:
You will receive:
1. The ordered textual descriptions of all units in the video atlas.
2. A concise description of the whole video.
3. The top genres for the full video.
4. An optional structure request from the user.
5. An output language instruction for all generated atlas text.

Guidelines:
1) Treat each unit as an atomic source block. Compose final segments by grouping units in their original order.
2) Preserve the original order of units. Every unit must appear exactly once in the final output.
3) Create segments that are semantically coherent and useful for navigation.
4) Respect the structure request when it is provided.
5) Do not invent units that were not present in the input.
6) Output only strict JSON.
7) title, abstract, segment titles, and segment summaries must follow the output language instruction exactly.

Output format:
Return ONLY a strict JSON object with exactly these keys:
{{
  "title": "<global title> ",
  "abstract": "<global abstract>",
  "composition_rationale": "<brief global rationale>",
  "segments": [
    {{
      "segment_id": "<stable segment id>",
      "unit_ids": ["<unit_id_1>", "<unit_id_2>"],
      "title": "<segment title>",
      "summary": "<segment summary>",
      "composition_rationale": "<why these units belong together>"
    }}
  ]
}}

""".strip(),
    user_template=r"""
Video metadata priors:
- genres: {genres}
- concise_description: {concise_description}
- structure_request: {structure_request}
- output_language: {output_language}

Ordered units:
{units_description}

Compose the final atlas structure. Every unit must appear exactly once and in its original order.
""".strip(),
    input_fields=("units_description", "concise_description", "genres", "structure_request", "output_language"),
    output_contract="strict JSON object with title, abstract, composition_rationale, and segments",
    tags=("canonical", "composition", "stage2"),
)


VIDEO_GLOBAL_PROMPT = PromptSpec(
    name="VIDEO_GLOBAL_PROMPT",
    purpose="Write global metadata and stable segment titles for a canonical atlas.",
    system_template=r"""
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
{{
  "title": "<string>",
  "abstract": "<string>",
  "segment_titles": [
    {{
      "seg_id": "<segment id>",
      "title": "<canonical segment title>"
    }}
  ]
}}
""".strip(),
    user_template=r"""
Given the following video segments description:

**video segments description**
```
{segments_description}
```

Now generate the global video title, abstract, and segment titles.
""",
    input_fields=("segments_description",),
    output_contract="strict JSON object with title, abstract, and segment_titles",
    tags=("canonical", "global"),
)
