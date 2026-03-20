"""Canonical registry data and resolver helpers."""

from __future__ import annotations

from .canonical_video_atlas import CaptionProfile, FrameSamplingProfile, SegmentationProfile


DEFAULT_SEGMENTATION_PROFILE = "generic_longform_continuous"
DEFAULT_CAPTION_PROFILE = "generic_longform_continuous"
DEFAULT_SAMPLING_PROFILE = "balanced"

ALLOWED_GENRES = {
    "narrative_film",
    "animation",
    "vlog_lifestyle",
    "podcast_interview",
    "lecture_talk",
    "tutorial_howto",
    "news_report",
    "documentary",
    "gameplay",
    "compilation_montage",
    "sports_event",
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

ALLOWED_SIGNAL_PRIORITIES = {"visual", "language", "balanced"}
DESCRIPTION_SLOTS = (
    "cast_speaker",
    "setting",
    "core_events",
    "topic_claims",
    "outcome_progress",
    "notable_cues",
)

SAMPLING_PROFILE_DESCRIPTIONS: dict[str, str] = {
    "language_lean": "Use when language content is sufficient and visual detail can be sampled sparsely for cost efficiency.",
    "balanced": "Use when both visuals and language matter and a medium-cost setting is appropriate.",
    "visual_detail": "Use when visual state changes are semantically important and higher visual fidelity is worth the cost.",
}
ALLOWED_SAMPLING_PROFILES = set(SAMPLING_PROFILE_DESCRIPTIONS)

SEGMENTATION_PROFILE_DESCRIPTIONS: dict[str, str] = {
    "esports_match_broadcast": (
        "Use for professional esports match broadcasts with casters, overlays, replay blocks, draft or ban phases, "
        "and chronological match progression."
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
    "esports_match_broadcast": SegmentationProfile(
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
            "Prefer stable broadcast blocks and match phases over local action spikes. "
            "Cut on strong transitions such as desk-to-draft, draft-to-game, live-to-replay, replay-to-live, "
            "pause or reset, and post-game analysis. Within live gameplay, cut only when there is a clear phase "
            "change or semantically complete block, not on every kill, skirmish, or camera pan."
        ),
    ),
    "podcast_topic_conversation": SegmentationProfile(
        signal_priority="language",
        target_segment_length_sec=(180, 480),
        default_sampling_profile="language_lean",
        boundary_evidence_primary=("topic_shift_in_subtitles", "speaker_change"),
        boundary_evidence_secondary=("on_screen_text_title_change", "music_or_audio_pattern_change"),
        segmentation_policy=(
            "Prefer topic-complete blocks rather than turn-by-turn segmentation. Cut when the conversation moves to a "
            "new question, argument, or subtopic with clear semantic separation. Do not cut on ordinary speaker "
            "alternation, acknowledgements, laughter, filler words, or short digressions alone."
        ),
    ),
    "lecture_slide_driven": SegmentationProfile(
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
    "language_lean": FrameSamplingProfile(fps=0.25, max_resolution=360),
    "balanced": FrameSamplingProfile(fps=0.5, max_resolution=480),
    "visual_detail": FrameSamplingProfile(fps=1.0, max_resolution=720),
}

CAPTION_PROFILES: dict[str, CaptionProfile] = {
    "esports_match_broadcast": CaptionProfile(
        slots_weight={
            "cast_speaker": 0.10,
            "setting": 0.08,
            "core_events": 0.34,
            "topic_claims": 0.08,
            "outcome_progress": 0.30,
            "notable_cues": 0.10,
        },
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
    "podcast_topic_conversation": CaptionProfile(
        slots_weight={
            "cast_speaker": 0.18,
            "setting": 0.04,
            "core_events": 0.08,
            "topic_claims": 0.44,
            "outcome_progress": 0.08,
            "notable_cues": 0.18,
        },
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
        slots_weight={
            "cast_speaker": 0.08,
            "setting": 0.06,
            "core_events": 0.14,
            "topic_claims": 0.42,
            "outcome_progress": 0.20,
            "notable_cues": 0.10,
        },
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
        slots_weight={
            "cast_speaker": 0.18,
            "setting": 0.12,
            "core_events": 0.22,
            "topic_claims": 0.22,
            "outcome_progress": 0.18,
            "notable_cues": 0.08,
        },
        caption_policy=(
            "Use a stable slot-based description. Prioritize who, where, what, and the main topic or key events. "
            "Produce concise segment-level summaries rather than frame-by-frame narration."
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
