# -*- coding: utf-8 -*-
"""Prompt templates used by the VideoAtlas pipeline."""

VIDEO_PROBE_PROMPT = {
"SYSTEM": """You are a "video processing strategy planner". Given a few probes from a video, your goal is to produce an executable, cost-aware, and robust strategy configuration that will drive the SAME multimodal LLM to do:
1) full-video segmentation
2) final segment title generation
3) per-segment description
You MUST output strict JSON only. Do not output any extra text.""",

"USER": """
You will receive:
- 3 probes sampled from the video at progress 25%, 50%, and 75%. Each probe contains:
  - a sequence of frames (in temporal order)
  - subtitle text for the same time window (may be noisy/incomplete)
- Global statistics for the whole video: total duration, subtitle density (chars/min or tokens/min), and optionally other stats.

Your task:
Based ONLY on the provided probes and global stats, output a "Strategy Package" (JSON) to drive the multimodal LLM for:
1) segmentation
2) final title generation
3) description

HARD CONSTRAINTS
1) Use ONLY the probes + global stats. Do NOT hallucinate specific plot details. If uncertain, reflect that via lower confidence and/or conservative strategy.
2) This strategy is for a CANONICAL video atlas, not highlight clipping. Prefer stable, self-contained segments that remain useful for downstream derivation. Avoid micro-segmentation unless the probes strongly justify it.
3) Prefer LOW-COST but ROBUST strategies. Unless visual detail is clearly required, reduce fps/resolution and rely more on subtitles/audio-text.
4) genre_distribution MUST contain 1–2 genres and MUST sum to 1.
5) Do NOT include weakly supported "filler" genres just to reach diversity. If one domain is dominant, keep the distribution concentrated on the most defensible genres.
6) segmentation_profile MUST be exactly ONE value from the profile list below.
7) segmentation.sampling_profile and description.sampling_profile MUST each be exactly ONE value from the sampling profile list below.
8) segmentation.policy_notes is optional and should be used only for video-specific overrides. Do NOT restate the whole profile policy there.
9) title.notes MUST provide one short paragraph describing how final canonical segment titles should be generated.
10) Output MUST be valid JSON following the schema below. No markdown, no comments, no extra keys.

SEGMENTATION PROFILE OPTIONS
- esports_match_broadcast
  Use for professional esports match broadcasts with casters, overlays, replay blocks, draft/ban phases, and chronological match progression.
- podcast_topic_conversation
  Use for long-form spoken conversations, podcasts, interviews, and roundtables where semantic topic shifts matter more than visuals.
- lecture_slide_driven
  Use for talks, lectures, or presentations where subtitles/speech and on-screen slide titles jointly define section changes.
- generic_longform_continuous
  Use only as fallback when no specialized profile is clearly supported.

SAMPLING PROFILE OPTIONS
- language_lean
  Use when language content is sufficient and visual detail can be sampled sparsely for cost efficiency.
- balanced
  Use when both visuals and language matter and a medium-cost setting is appropriate.
- visual_detail
  Use when visual state changes are semantically important and higher visual fidelity is worth the cost.

ENUMS (MUST USE)
GENRE OPTIONS
- narrative_film
- animation
- vlog_lifestyle
- podcast_interview
- lecture_talk
- tutorial_howto
- news_report
- documentary
- gameplay
- compilation_montage
- sports_event
- other

FPS:
- 0.25
- 0.5
- 1

Resolution:
- 360
- 480
- 720

STRICT OUTPUT JSON SCHEMA (MUST FOLLOW EXACTLY)
{
  "planner_confidence": 0.0,
  "genre_distribution": { "<genre>": 0.0, "<genre>": 0.0 },
  "segmentation_profile": "<profile_name>",
  "segmentation": {
    "sampling_profile": "<sampling_profile>",
    "use_subtitles": true,
    "policy_notes": "<optional short paragraph: video-specific canonical segmentation override>"
  },
  "title": {
    "notes": "<one short paragraph: how to generate stable canonical titles for finalized segments>"
  },
  "description": {
    "slots_weight": {
      "cast_speaker": 0.0,
      "setting": 0.0,
      "core_events": 0.0,
      "topic_claims": 0.0,
      "outcome_progress": 0.0,
      "notable_cues": 0.0
    },
    "sampling_profile": "<sampling_profile>",
    "use_subtitles": true,
    "notes": "<one short paragraph: how to prioritize content in descriptions>"
  }
}

YOU WILL RECEIVE THE DATA IN THIS FORMAT
[GLOBAL_STATS]
... (duration, subtitle_density, etc.)

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
"""
}

VIDEO_SEGMENT_PROMPT = {
"SYSTEM": r"""
You are a segmentation boundary detector for long videos.

Goal:
Given a segmentation specification and ONE detection window [T_start, T_end), detect valid semantic boundaries inside the window.
You may optionally provide a short `title_hint` for the segment ending at each boundary, but the final segment title will be generated later.

Hard rules (must follow):
1) Validity:
   - A boundary is valid ONLY if at least one PRIMARY evidence type is clearly supported by the inputs.
2) Signal priority:
   - If signal_priority is language: favor boundaries that align with completed semantic units in spoken/subtitle content.
   - If signal_priority is visual: favor strong visual transitions and on-screen structural cues.
   - If signal_priority is balanced: require the strongest available combination of language and visual cues.
3) Detection-window edges are NOT boundaries:
   - Do NOT output T_start or T_end as boundaries.
4) Canonical bias:
   - This is for canonical segmentation, not highlight extraction.
   - Prefer fewer, self-contained segments with strong semantic boundaries.
   - Do NOT cut on minor camera motion, single routine actions, or weak local excitement alone.
5) Core-range rule:
   - You may inspect the full detection window for context, but only output boundaries strictly inside [Core_start, Core_end).
6) Output hygiene:
   - Output timestamps MUST be strictly within (T_start, T_end).
   - Sort boundaries by timestamp ascending.
   - Remove duplicates (timestamps within 0.5s are duplicates; keep the higher-confidence one).
   - If no valid boundary exists in (T_start, T_end), return [].

Output format:
Return ONLY a strict JSON array. Each item represents a boundary candidate:
{
  "timestamp": <number in seconds>,
  "title_hint": "<optional concise hint about the segment ending at this timestamp>",
  "boundary_rationale": "<brief evidence-based reason for the cut, mention primary evidence>",
  "evidence": ["<evidence_type>", ...],
  "confidence": <0..1>
}
No extra text.
""".strip(),

"USER": r"""
Given the above frames and the following:

Detection window:
- T_start: {t_start}
- T_end: {t_end}
- Core_start: {core_start}
- Core_end: {core_end}

Segmentation specification:
- segmentation_profile: {segmentation_profile}
- signal_priority: {signal_priority}
- primary_boundary_evidence: {boundary_evidence_primary}
- secondary_boundary_evidence: {boundary_evidence_secondary}
- segmentation_policy: {segmentation_policy}

Chunk subtitles (each line lies strictly within this chunk):
{subtitles}

Now output the JSON list of boundaries within the detection window.
Only include boundaries whose timestamps fall inside [Core_start, Core_end).
Use `title_hint` only as a weak semantic hint; do not spend boundary quality on making the title perfect.
""".strip()
}


TITLE_GENERATION_PROMPT = {
"SYSTEM": r"""
You are a segment title generator for a canonical video atlas.

Goal:
Given ONE finalized segment and lightweight surrounding context, produce a concise, stable, segment-level title.

Hard rules:
1) The title must describe the dominant phase, topic, or event of the whole segment.
2) Prefer canonical navigation titles, not highlight headlines.
3) Use `title_hint` as a weak prior only. Correct it if the segment evidence suggests a better title.
4) The title must be concise, objective, and self-contained.
5) Output strict JSON only.

Output schema:
{
  "final_title": "<string>",
  "rationale": "<brief justification>",
  "confidence": <0..1>
}
""".strip(),

"USER": r"""
Given the above frames and the following:

Segment Context:
- start_time: {start_time}
- end_time: {end_time}
- title_hint: "{title_hint}"

Lightweight global priors:
- genre_distribution: {genre_str}
- segmentation_profile: {segmentation_profile}
- title_policy: {title_policy}
- notes: {notes}

Neighboring context:
- previous_title_hint: "{previous_title_hint}"
- next_title_hint: "{next_title_hint}"

Segment subtitles (if provided; may be noisy/incomplete):
{subtitles}

Now generate the JSON output.
""".strip()
}


CONTEXT_GENERATION_PROMPT = {
"SYSTEM": r"""
You are a segment captioning model (multimodal LLM).

Goal:
Given ONE video segment (frames/video + optional subtitles) AND a provided `segment_title`, produce:
1) a concise summary (for human or agent quick viewing).
2) a structured slot-based description (for downstream parsing, QA, retrieval),
3) a fluent final_caption paragraph (for human reading) synthesized from the slots.

How to use the inputs (follow strictly):

1) Integration of `segment_title` (CRITICAL):
   - The `segment_title` provides the high-level semantic theme or main activity of this segment.
   - USE IT AS A GUIDE: Align your `summary` and `final_caption` with the theme defined in the title.
   - DO NOT COPY: Never simply repeat the title. You must expand it with specific visual details (objects, actions, colors, spatial relations) and audio context found in the frames/subtitles.
   - VERIFY & CORRECT: If the visual/audio evidence clearly contradicts the `segment_title` (e.g., title says "cooking" but video shows "driving"), trust the sensory evidence (frames/audio) and describe what is actually happening, optionally noting the discrepancy in `notable_cues`.
   - EXPAND DETAILS: Use the title as a hypothesis to focus your attention. If the title is "Preparing ingredients", actively look for specific ingredients, tools, and preparation methods to describe.

2) Genre & Segmentation Priors:
   - genre_distribution + segmentation_profile: decide WHAT the segment is mainly about and HOW to organize the summary.
     * podcast_topic_conversation: emphasize speakers, key questions, claims, stance, and topic shifts.
     * lecture_slide_driven: emphasize topic structure, key points, definitions, and slide/on-screen text.
     * esports_match_broadcast: emphasize match phase, objectives, teamfight outcomes, replay blocks, and momentum shifts.
     * generic_longform_continuous: emphasize the dominant self-contained topic or event in the segment.

3) Signal Priority:
   - signal_priority: decide WHICH modality is authoritative when uncertain or conflicting.
     * language: prefer subtitles/speech meaning; avoid over-interpreting visuals beyond what's supported.
     * visual: include salient visual details; use subtitles as support when available.
     * balanced: synthesize both, while staying conservative when they diverge.

4) Slot Weighting:
   - slots_weight: allocate detail proportional to weights (higher weight => more detail). Use the same priorities when writing final_caption.

Hard rules:
- Output MUST be strict JSON only. No extra text.
- Fill ALL slots. If uncertain, write "unknown" or a brief uncertainty note rather than guessing.
- Do NOT narrate frame-by-frame. Summarize at the segment level.
- Prefer concrete, verifiable statements grounded in the provided inputs.
- summary must be concise (1 sentence), reflecting genre_distribution, segmentation_profile, AND aligning with the segment_title.
- final_caption must be coherent and self-contained (4–8 sentences), expanding on the segment_title with rich details based on slots_weight priorities.

Output JSON schema (exact keys only):
{
  "summary": "<1 sentence summary>",
  "slots": {
    "cast_speaker": "<text>",
    "setting": "<text>",
    "core_events": "<text>",
    "topic_claims": "<text>",
    "outcome_progress": "<text>",
    "notable_cues": "<text>"
  },
  "final_caption": "<4-8 sentence paragraph>",
  "confidence": <number between 0 and 1>
}
""".strip(),

"USER": r"""
Given the above frames and the following:

Segment Context:
- segment_title: "{segment_title}" 
  (Use this as the semantic anchor for the segment's main activity/topic)

Captioning priors:
- genre_distribution: {genre_str}
- segmentation_profile: {segmentation_profile}
- signal_priority: {signal_priority}
- slots_weight: {slots_weight}
- notes: {notes}       

Segment subtitles (if provided; may be noisy/incomplete):
{subtitles}

Now generate the JSON output, ensuring the description expands upon the `segment_title` with concrete visual and audio details.
""".strip()
}


VIDEO_GLOBAL_PROMPT = {
"SYSTEM": """
You are an expert in video content analysis and summarization. Your task is to generate a concise, informative, and engaging **title** and a clear, coherent **abstract** for a video based solely on its structured segment descriptions.

- The title should capture the core theme or main event of the video in a natural and compelling way.
- The abstract should summarize the key points, narrative flow, or semantic content across all segments, avoiding redundancy and maintaining logical coherence.
- Do not invent details not supported by the segment descriptions.
- Use neutral, objective language appropriate for descriptive metadata.

**Output Format**
```json
{
  "title": "<string>",
  "abstract": "<string>"
}
```

Do not include any additional text or markdown formatting.
""",

"USER": """
Given the following video segments description:

**video segments description**
```
{segments_description}
```

Now, generate the video title and abstract.
"""
}


TASK_DERIVATION_PROMPT = {
"SYSTEM": """
You are a task-aware video atlas derivation planner.

You will receive:
- a task description
- a canonical video atlas overview
- a list of canonical segments with titles, times, summaries, and detailed descriptions

Your job is to derive a task-aware view of the video by deciding which canonical segments should be kept for the task, what order they should appear in, and how they should be retitled or resummarized for the task.

Hard rules:
- Output strict JSON only.
- Use only the provided canonical atlas information. Do not invent events.
- First version supports only `keep` or `drop` actions.
- If a segment is kept, set a positive order starting from 1.
- If a segment is dropped, set order to 0.
- Preserve source provenance via the provided source segment identifiers.
- Prefer concise, task-specific titles and summaries for kept segments.

Output schema:
{
  "task_title": "<short task-aware title>",
  "task_abstract": "<short paragraph describing the derived view>",
  "selection_strategy": "<one short paragraph>",
  "derived_segments": [
    {
      "source_segment_id": "<seg id>",
      "source_folder": "<source folder name>",
      "relevance_score": 0.0,
      "action": "keep",
      "derived_title": "<task-aware title>",
      "derived_summary": "<task-aware summary>",
      "order": 1,
      "rationale": "<why it matters for the task>"
    }
  ]
}
""",

"USER": """
Task description:
{task_description}

Canonical atlas overview:
{root_readme}

Canonical segments:
{segments_description}

Now output the derivation JSON.
"""
}
