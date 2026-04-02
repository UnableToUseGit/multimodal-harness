"""Canonical registry data and resolver helpers."""

from __future__ import annotations

from .canonical_atlas import CaptionProfile, FrameSamplingProfile, Profile, SegmentationProfile


DEFAULT_SEGMENTATION_PROFILE = "generic_longform_continuous"
DEFAULT_CAPTION_PROFILE = "generic_longform_continuous"
DEFAULT_SAMPLING_PROFILE = "balanced"
DEFAULT_PROFILE = "other"

ALLOWED_GENRES = {
    "narrative_film",
    "animation",
    "vlog_lifestyle",
    "podcast_interview",
    "lecture_talk",
    "tutorial_howto",
    "news_report",
    "documentary",
    "esports_broadcast",
    "compilation_montage",
    "sports_broadcast",
    "other",
}

ALLOWED_EVIDENCE = {
    "topic_shift_in_subtitles",
    "speaker_change",
    "scene_location_change",
    "shot_style_change",
    "on_screen_text_title_change",
    "music_or_audio_pattern_change",
    "step_transition",
    "time_jump_or_recap",
    "other",
}

PROFILES: dict[str, Profile] = {
    "lecture": Profile(
        route="text_first",
        segmentation_policy=(
            "Prefer concept-complete or section-complete segments. Cut when the speaker clearly moves to a new topic, "
            "section, or major explanatory step."
        ),
        caption_policy=(
            "Summarize each segment as a coherent lecture section. Emphasize the main concept, teaching goal, and key "
            "explanatory takeaway."
        ),
    ),
    "podcast": Profile(
        route="text_first",
        segmentation_policy=(
            "Prefer semantically complete discussion arcs. Cut when the conversation clearly moves into a new major "
            "theme or self-contained discussion thread."
        ),
        caption_policy=(
            "Summarize each segment as a coherent conversation arc. Emphasize the topic being discussed and the main "
            "point or story being developed."
        ),
    ),
    "explanatory_commentary": Profile(
        route="text_first",
        segmentation_policy=(
            "Prefer semantically complete explanation blocks. Cut only when the narration clearly moves to a new major "
            "question, analytical direction, or self-contained explanatory block."
        ),
        caption_policy=(
            "Summarize each segment as a coherent explanation block. Emphasize the argument, analysis, or explanatory "
            "point being advanced."
        ),
    ),
    "movie": Profile(
        route="multimodal",
        segmentation_policy=(
            "Prefer plot-complete or dramatic-unit-complete segments rather than shot-level cuts."
        ),
        caption_policy=(
            "Describe each segment as a coherent dramatic unit with emphasis on plot progression, conflict, and scene "
            "state."
        ),
    ),
    "drama": Profile(
        route="multimodal",
        segmentation_policy=(
            "Prefer scene-complete dramatic units rather than short local transitions or dialogue turns."
        ),
        caption_policy=(
            "Describe each segment as a coherent dramatic scene with emphasis on situation, character tension, and "
            "story movement."
        ),
    ),
    "sports": Profile(
        route="multimodal",
        segmentation_policy=(
            "Prefer structurally complete match phases, replay blocks, and analysis sections over isolated short-term "
            "events."
        ),
        caption_policy=(
            "Describe each segment as a coherent sports broadcast phase, emphasizing the game situation and analysis "
            "focus."
        ),
    ),
    "other": Profile(
        route="multimodal",
        segmentation_policy=(
            "Prefer self-contained coarse segments with defensible semantic boundaries. Avoid cutting on weak local "
            "variation alone."
        ),
        caption_policy=(
            "Describe each segment conservatively as a coherent content block without overcommitting to uncertain "
            "detail."
        ),
    ),
}


def resolve_profile(name: str) -> tuple[str, Profile]:
    normalized = (name or "").strip()
    if normalized in PROFILES:
        return normalized, PROFILES[normalized]
    return DEFAULT_PROFILE, PROFILES[DEFAULT_PROFILE]

ALLOWED_SIGNAL_PRIORITIES = {"visual", "language", "balanced"}
SAMPLING_PROFILE_DESCRIPTIONS: dict[str, str] = {
    "language_lean": "Use when language content is sufficient and visual detail can be sampled sparsely for cost efficiency.",
    "balanced": "Use when both visuals and language matter and a medium-cost setting is appropriate.",
    "visual_detail": "Use when visual state changes are semantically important and higher visual fidelity is worth the cost.",
}
ALLOWED_SAMPLING_PROFILES = set(SAMPLING_PROFILE_DESCRIPTIONS)

SEGMENTATION_PROFILE_DESCRIPTIONS: dict[str, str] = {
    "vlog_lifestyle": (
        "Use for personal vlogs and lifestyle travel videos where coherent experience blocks, location-based episodes, "
        "and self-contained narrative moments are the preferred navigation unit."
    ),
    "documentary": (
        "Use for documentaries and observational nonfiction where semantically complete story units, character arcs, "
        "or explanatory sections are the preferred navigation unit."
    ),
    "explanatory_commentary": (
        "Use for explanatory commentary videos where a narrator develops one topic through coherent explanation blocks, "
        "argument steps, and example clusters rather than turn-by-turn dialogue."
    ),
    "esports_match_broadcast": (
        "Use for professional esports match broadcasts with casters, overlays, replay blocks, draft or ban phases, "
        "and chronological match progression."
    ),
    "sports_broadcast": (
        "Use for sports match broadcasts and replay-inclusive event coverage where stable match phases, replay blocks, "
        "analysis inserts, and live-to-replay transitions are the preferred navigation units."
    ),
    "narrative_film": (
        "Use for narrative films and dramatic fiction where scene-complete or dramatic-beat-complete segments are the "
        "preferred navigation unit."
    ),
    "podcast_topic_conversation": (
        "Use for long-form spoken conversations, podcasts, interviews, and roundtables where semantic topic shifts "
        "matter more than visuals."
    ),
    "lecture_slide_driven": (
        "Use for talks, lectures, or presentations where subtitles or speech and on-screen slide titles jointly "
        "define section changes."
    ),
    DEFAULT_SEGMENTATION_PROFILE: "Use only as fallback when no specialized profile is clearly supported.",
}

SEGMENTATION_PROFILES: dict[str, SegmentationProfile] = {
    "vlog_lifestyle": SegmentationProfile(
        segmentation_route="multimodal_local",
        signal_priority="balanced",
        target_segment_length_sec=(60, 240),
        default_sampling_profile="balanced",
        boundary_evidence_primary=(
            "scene_location_change",
            "topic_shift_in_subtitles",
            "time_jump_or_recap",
        ),
        boundary_evidence_secondary=(
            "shot_style_change",
            "music_or_audio_pattern_change",
            "on_screen_text_title_change",
        ),
        segmentation_policy=(
            "Prefer semantically complete experience blocks rather than short visual snippets or moment-by-moment cuts."
            " Keep together footage that belongs to the same outing, location visit, reflective thread, or self-contained episode in the creator's journey."
            " Cut when the vlog clearly moves into a new place, activity, narrative purpose, or time period."
            " Do not cut on ordinary camera changes, brief scenic inserts, or short remarks alone."
        ),
    ),
    "documentary": SegmentationProfile(
        segmentation_route="multimodal_local",
        signal_priority="balanced",
        target_segment_length_sec=(90, 300),
        default_sampling_profile="balanced",
        boundary_evidence_primary=(
            "topic_shift_in_subtitles",
            "scene_location_change",
            "time_jump_or_recap",
        ),
        boundary_evidence_secondary=(
            "on_screen_text_title_change",
            "shot_style_change",
            "music_or_audio_pattern_change",
        ),
        segmentation_policy=(
            "Prefer semantically complete documentary story units rather than isolated shots or small informational fragments."
            " Keep together footage that is still developing the same character thread, place-based sequence, historical episode, or explanatory section."
            " Cut when a story unit clearly completes, or when the documentary moves into a new location, subject, time period, or self-contained line of explanation."
            " Do not cut on ordinary shot changes, local reaction shots, or brief illustrative inserts alone."
        ),
    ),
    "explanatory_commentary": SegmentationProfile(
        segmentation_route="text_llm",
        signal_priority="language",
        target_segment_length_sec=(120, 360),
        default_sampling_profile="language_lean",
        boundary_evidence_primary=("topic_shift_in_subtitles", "on_screen_text_title_change"),
        boundary_evidence_secondary=("scene_location_change", "time_jump_or_recap", "speaker_change"),
        segmentation_policy=(
            "Prefer semantically complete explanation blocks rather than sentence-level or example-level segmentation."
            " Keep together stretches that are still developing the same major concept, argument step, analytical theme, or explanatory thread."
            " Cut only when the narration clearly moves into a new major question, a new self-contained explanatory block, or a substantially different analytical direction."
            " Do not cut on ordinary rhetorical transitions, brief examples, local elaborations, or short topical detours that still serve the same broader explanation."
        ),
    ),
    "esports_match_broadcast": SegmentationProfile(
        segmentation_route="multimodal_local",
        signal_priority="balanced",
        target_segment_length_sec=(90, 240),
        default_sampling_profile="balanced",
        boundary_evidence_primary=(
            "on_screen_text_title_change",
            "time_jump_or_recap",
            "topic_shift_in_subtitles",
        ),
        boundary_evidence_secondary=(
            "shot_style_change",
            "music_or_audio_pattern_change",
            "scene_location_change",
        ),
        segmentation_policy=(
            "Prioritize structurally complete match phases and pre/post-game content over isolated, short-term action spikes."
            "Ensure cuts respect the natural narrative flow of the esports broadcast.",
            "Cut only on clear phase transitions or after a semantically complete block is complete."
            "Do not cut in the middle of a crucial game event or other ongoing high-stakes sequence."
        ),
    ),
    "sports_broadcast": SegmentationProfile(
        segmentation_route="multimodal_local",
        signal_priority="balanced",
        target_segment_length_sec=(60, 240),
        default_sampling_profile="balanced",
        boundary_evidence_primary=(
            "on_screen_text_title_change",
            "time_jump_or_recap",
            "shot_style_change",
        ),
        boundary_evidence_secondary=(
            "topic_shift_in_subtitles",
            "music_or_audio_pattern_change",
            "scene_location_change",
        ),
        segmentation_policy=(
            "Prioritize structurally complete match phases and pre/post-game content over isolated, short-term action spikes."
            "Ensure cuts respect the natural narrative flow of the sports broadcast.",
            "Cut only on clear phase transitions or after a semantically complete block is complete."
            "Do not cut in the middle of a crucial match event or other ongoing high-stakes sequence."
        ),
    ),
    "narrative_film": SegmentationProfile(
        segmentation_route="multimodal_local",
        signal_priority="balanced",
        target_segment_length_sec=(45, 240),
        default_sampling_profile="balanced",
        boundary_evidence_primary=(
            "scene_location_change",
            "topic_shift_in_subtitles",
            "time_jump_or_recap",
        ),
        boundary_evidence_secondary=(
            "shot_style_change",
            "speaker_change",
            "music_or_audio_pattern_change",
        ),
        segmentation_policy=(
            "Prefer plot-complete or dramatic-unit-complete segments rather than shot-level cuts."
            "Segment the video according to coherent plot units, where characters are typically engaged in a shared dramatic theme, objective, conflict, or emotional progression."
            "Cut when a plot unit has clearly completed, or when there is a clear transition such as a time jump, location shift, major objective change, or a new dramatic thread begins."
            "Do not cut on ordinary shot changes, dialogue turns, or local camera movement alone."
        ),
    ),
    "podcast_topic_conversation": SegmentationProfile(
        segmentation_route="text_llm",
        signal_priority="language",
        target_segment_length_sec=(180, 480),
        default_sampling_profile="language_lean",
        boundary_evidence_primary=("topic_shift_in_subtitles", "speaker_change"),
        boundary_evidence_secondary=("on_screen_text_title_change", "music_or_audio_pattern_change"),
        segmentation_policy=(
            "Prefer semantically complete discussion arcs rather than turn-by-turn or subtopic-level segmentation."
            "Keep together conversation stretches that are still developing the same broader theme, life stage, experience cluster, or narrative thread"
            "Cut only when the dialogue clearly shifts into a new major theme or a new self-contained discussion arc."
            "Do not cut on ordinary speaker alternation, acknowledgements, laughter, filler words, brief follow-up examples, or small subtopics that still belong to the same broader theme."
        ),
    ),
    "lecture_slide_driven": SegmentationProfile(
        segmentation_route="text_llm",
        signal_priority="balanced",
        target_segment_length_sec=(120, 360),
        default_sampling_profile="balanced",
        boundary_evidence_primary=("topic_shift_in_subtitles", "on_screen_text_title_change"),
        boundary_evidence_secondary=("step_transition", "speaker_change"),
        segmentation_policy=(
            "Prefer concept-complete or section-complete segments rather than slide-by-slide micro-segmentation. "
            "Cut when the lecture clearly moves to a new topic, section, or major explanatory step. Use on-screen "
            "titles and subtitles together to confirm section changes."
        ),
    ),
    DEFAULT_SEGMENTATION_PROFILE: SegmentationProfile(
        segmentation_route="multimodal_local",
        signal_priority="balanced",
        target_segment_length_sec=(90, 300),
        default_sampling_profile="balanced",
        boundary_evidence_primary=("topic_shift_in_subtitles", "on_screen_text_title_change"),
        boundary_evidence_secondary=("speaker_change", "shot_style_change"),
        segmentation_policy=(
            "Prefer self-contained coarse segments with defensible semantic boundaries. Avoid cutting on weak local "
            "variation alone, and favor stable navigation units over highlight-style micro-cuts."
        ),
    ),
}

ALLOWED_SEGMENTATION_PROFILES = set(SEGMENTATION_PROFILES)

SAMPLING_PROFILE_CONFIGS: dict[str, FrameSamplingProfile] = {
    "language_lean": FrameSamplingProfile(fps=0.1, max_resolution=480),
    "balanced": FrameSamplingProfile(fps=0.25, max_resolution=480),
    "visual_detail": FrameSamplingProfile(fps=0.5, max_resolution=720),
}

CAPTION_PROFILES: dict[str, CaptionProfile] = {
    "vlog_lifestyle": CaptionProfile(
        caption_policy=(
            "Summarize each segment as a coherent vlog episode or experience block. Emphasize where the creator is, "
            "what they are doing, the mood or reflective thread, and how the segment fits into the broader journey."
        ),
        title_policy=(
            "Prefer experience-oriented titles such as Arrival In Paris, Street Walk And Reflection, Café Break In Shanghai, "
            "Museum Visit, Evening City Impressions, or Travel Transition. Avoid titles that only describe isolated shots."
        ),
    ),
    "documentary": CaptionProfile(
        caption_policy=(
            "Summarize each segment as a documentary story unit or explanatory block. Emphasize the main subject, "
            "character thread, place, event, or argument being developed."
        ),
        title_policy=(
            "Prefer documentary-style navigation titles such as Early Life In Beijing, Entering The Underground Scene, "
            "How The Drug Trade Expanded, Industry Backdrop, or Turning Point In The Story. Avoid titles that only describe visuals."
        ),
    ),
    "explanatory_commentary": CaptionProfile(
        caption_policy=(
            "Summarize each segment as a coherent explanation block. Emphasize the major concept, argument, historical episode, "
            "case analysis, or interpretive claim being developed, rather than sentence-level detail."
        ),
        title_policy=(
            "Prefer explanation-oriented titles such as What World Models Are, Why The System Failed, Historical Background, "
            "How The Character Was Constructed, or The Core Technical Challenge. Avoid titles that only restate isolated examples."
        ),
    ),
    "esports_match_broadcast": CaptionProfile(
        caption_policy=(
            "Describe each segment as a stable match-phase summary. Prioritize objective setups, teamfights, "
            "replays, map control, and momentum shifts over fine-grained play-by-play."
        ),
        title_policy=(
            "Prefer phase-level navigational titles such as Draft And Ban, Early Lane Setup, Dragon Fight And Reset, "
            "Replay Of Baron Fight, or Post Game Analysis. Avoid highlight-style titles unless the whole segment is "
            "genuinely centered on one event."
        ),
    ),
    "sports_broadcast": CaptionProfile(
        caption_policy=(
            "Describe each segment as a stable sports broadcast block. Prioritize the match phase, the key events or "
            "turning points under discussion, and the broadcast context such as replay review, live action, or studio-style analysis."
        ),
        title_policy=(
            "Prefer broadcast-oriented titles such as First Half Midfield Control, Goal And Replay Review, Penalty Incident "
            "Analysis, Final Minutes Pressure, Halftime Summary, or Post Match Wrap Up. Avoid titles that only name camera moves."
        ),
    ),
    "narrative_film": CaptionProfile(
        caption_policy=(
            "Summarize each segment as a scene or dramatic unit. Emphasize the characters involved, the immediate "
            "objective or conflict, and the narrative development, rather than shot-by-shot visual description."
        ),
        title_policy=(
            "Prefer scene-level titles such as Opening Setup, Interrogation At The Station, Family Dinner Conflict, "
            "Escape Through The Alley, or Final Confrontation. Avoid titles that only describe isolated camera actions."
        ),
    ),
    "podcast_topic_conversation": CaptionProfile(
        caption_policy=(
            "Summarize the main topic, claims, and speaker positions. Prefer topic-level synthesis over turn-by-turn "
            "recap, and only mention delivery cues when they materially shape the exchange."
        ),
        title_policy=(
            "Prefer concise topic labels such as Opening And Show Setup, Why Model Costs Matter, Debate On Open Source, "
            "Sponsor Break, or Closing Recommendations. Avoid titles that only describe who is speaking."
        ),
    ),
    "lecture_slide_driven": CaptionProfile(
        caption_policy=(
            "Summarize each concept block clearly. Emphasize the section topic, explanatory claims, and progression "
            "through the lecture rather than visual minutiae or sentence-level narration."
        ),
        title_policy=(
            "Prefer section and concept titles such as Course Introduction, Problem Setup, Model Architecture, "
            "Training Pipeline, Evaluation Results, or Conclusion And Future Work. Avoid generic titles like Next Slide."
        ),
    ),
    DEFAULT_CAPTION_PROFILE: CaptionProfile(
        caption_policy=(
            "Use a stable segment-level description. Prioritize who, where, what, and the main topic or key events. "
            "Produce concise segment summaries rather than frame-by-frame narration."
        ),
        title_policy=(
            "Prefer neutral descriptive navigation titles that name the segment's dominant phase, topic, or event "
            "without sounding promotional or highlight-oriented."
        ),
    ),
}


def resolve_segmentation_profile(name: str) -> tuple[str, SegmentationProfile]:
    if name in SEGMENTATION_PROFILES:
        return name, SEGMENTATION_PROFILES[name]
    return DEFAULT_SEGMENTATION_PROFILE, SEGMENTATION_PROFILES[DEFAULT_SEGMENTATION_PROFILE]


def resolve_sampling_profile(name: str) -> tuple[str, FrameSamplingProfile]:
    if name in SAMPLING_PROFILE_CONFIGS:
        return name, SAMPLING_PROFILE_CONFIGS[name]
    return DEFAULT_SAMPLING_PROFILE, SAMPLING_PROFILE_CONFIGS[DEFAULT_SAMPLING_PROFILE]


def resolve_caption_profile(name: str) -> tuple[str, CaptionProfile]:
    if name in CAPTION_PROFILES:
        return name, CAPTION_PROFILES[name]
    return DEFAULT_CAPTION_PROFILE, CAPTION_PROFILES[DEFAULT_CAPTION_PROFILE]
