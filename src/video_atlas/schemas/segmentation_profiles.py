"""Canonical segmentation profiles and profile resolution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SegmentationProfile:
    signal_priority: str
    target_segment_length_sec: tuple[int, int]
    segmentation_sampling_profile: str
    description_sampling_profile: str
    boundary_evidence_primary: tuple[str, ...]
    boundary_evidence_secondary: tuple[str, ...]
    segmentation_policy: str
    title_policy: str


DEFAULT_SEGMENTATION_PROFILE = "generic_longform_continuous"

SEGMENTATION_PROFILES: dict[str, SegmentationProfile] = {
    "esports_match_broadcast": SegmentationProfile(
        signal_priority="balanced",
        target_segment_length_sec=(90, 240),
        segmentation_sampling_profile="balanced",
        description_sampling_profile="balanced",
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
        title_policy=(
            "Prefer phase-level navigational titles such as Draft And Ban, Early Lane Setup, Dragon Fight And Reset, "
            "Replay Of Baron Fight, or Post Game Analysis. Avoid highlight-style titles unless the whole segment is "
            "genuinely centered on one event."
        ),
    ),
    "podcast_topic_conversation": SegmentationProfile(
        signal_priority="language",
        target_segment_length_sec=(180, 480),
        segmentation_sampling_profile="language_lean",
        description_sampling_profile="language_lean",
        boundary_evidence_primary=(
            "topic_shift_in_subtitles",
            "speaker_change",
        ),
        boundary_evidence_secondary=(
            "on_screen_text_title_change",
            "music_or_audio_pattern_change",
        ),
        segmentation_policy=(
            "Prefer topic-complete blocks rather than turn-by-turn segmentation. Cut when the conversation moves to a "
            "new question, argument, or subtopic with clear semantic separation. Do not cut on ordinary speaker "
            "alternation, acknowledgements, laughter, filler words, or short digressions alone."
        ),
        title_policy=(
            "Prefer concise topic labels such as Opening And Show Setup, Why Model Costs Matter, Debate On Open Source, "
            "Sponsor Break, or Closing Recommendations. Avoid titles that only describe who is speaking."
        ),
    ),
    "lecture_slide_driven": SegmentationProfile(
        signal_priority="balanced",
        target_segment_length_sec=(120, 360),
        segmentation_sampling_profile="balanced",
        description_sampling_profile="language_lean",
        boundary_evidence_primary=(
            "topic_shift_in_subtitles",
            "on_screen_text_title_change",
        ),
        boundary_evidence_secondary=(
            "step_transition",
            "speaker_change",
        ),
        segmentation_policy=(
            "Prefer concept-complete or section-complete segments rather than slide-by-slide micro-segmentation. "
            "Cut when the lecture clearly moves to a new topic, section, or major explanatory step. Use on-screen "
            "titles and subtitles together to confirm section changes."
        ),
        title_policy=(
            "Prefer section and concept titles such as Course Introduction, Problem Setup, Model Architecture, "
            "Training Pipeline, Evaluation Results, or Conclusion And Future Work. Avoid generic titles like Next Slide."
        ),
    ),
    DEFAULT_SEGMENTATION_PROFILE: SegmentationProfile(
        signal_priority="balanced",
        target_segment_length_sec=(90, 300),
        segmentation_sampling_profile="balanced",
        description_sampling_profile="balanced",
        boundary_evidence_primary=(
            "topic_shift_in_subtitles",
            "on_screen_text_title_change",
        ),
        boundary_evidence_secondary=(
            "speaker_change",
            "shot_style_change",
        ),
        segmentation_policy=(
            "Prefer self-contained coarse segments with defensible semantic boundaries. Avoid cutting on weak local "
            "variation alone, and favor stable navigation units over highlight-style micro-cuts."
        ),
        title_policy=(
            "Prefer neutral descriptive navigation titles that name the segment's dominant phase, topic, or event "
            "without sounding promotional or highlight-oriented."
        ),
    ),
}

ALLOWED_SEGMENTATION_PROFILES = set(SEGMENTATION_PROFILES)
ALLOWED_SAMPLING_PROFILES = {"language_lean", "balanced", "visual_detail"}

SAMPLING_PROFILE_CONFIGS: dict[str, dict[str, int | float]] = {
    "language_lean": {"fps": 0.25, "max_resolution": 360},
    "balanced": {"fps": 0.5, "max_resolution": 480},
    "visual_detail": {"fps": 1.0, "max_resolution": 720},
}


def resolve_segmentation_profile(name: str) -> tuple[str, SegmentationProfile]:
    if name in SEGMENTATION_PROFILES:
        return name, SEGMENTATION_PROFILES[name]
    return DEFAULT_SEGMENTATION_PROFILE, SEGMENTATION_PROFILES[DEFAULT_SEGMENTATION_PROFILE]


def resolve_sampling_profile(name: str, fallback: str) -> tuple[str, dict[str, int | float]]:
    if name in SAMPLING_PROFILE_CONFIGS:
        return name, SAMPLING_PROFILE_CONFIGS[name]
    if fallback in SAMPLING_PROFILE_CONFIGS:
        return fallback, SAMPLING_PROFILE_CONFIGS[fallback]
    return "balanced", SAMPLING_PROFILE_CONFIGS["balanced"]
