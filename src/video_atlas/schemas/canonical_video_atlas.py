"""Canonical VideoAtlas generation schemas."""

from __future__ import annotations

from dataclasses import dataclass, field


DEFAULT_SEGMENTATION_PROFILE = "generic_longform_continuous"

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
ALLOWED_SAMPLING_PROFILES = {"language_lean", "balanced", "visual_detail"}

DESCRIPTION_SLOTS = [
    "cast_speaker",
    "setting",
    "core_events",
    "topic_claims",
    "outcome_progress",
    "notable_cues",
]


@dataclass
class FrameSamplingProfile:
    fps: float = 0.5
    max_resolution: int = 480


SamplingConfig = FrameSamplingProfile


@dataclass(frozen=True)
class SegmentationProfile:
    signal_priority: str
    target_segment_length_sec: tuple[int, int]
    default_sampling_profile: str
    boundary_evidence_primary: tuple[str, ...]
    boundary_evidence_secondary: tuple[str, ...]
    segmentation_policy: str


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


SAMPLING_PROFILE_CONFIGS: dict[str, dict[str, int | float]] = {
    "language_lean": FrameSamplingProfile(fps=0.25, max_resolution=360),
    "balanced": FrameSamplingProfile(fps=0.5, max_resolution=480),
    "visual_detail": FrameSamplingProfile(fps=1.0, max_resolution=720),
}

def resolve_segmentation_profile(name: str) -> tuple[str, SegmentationProfile]:
    if name in SEGMENTATION_PROFILES:
        return name, SEGMENTATION_PROFILES[name]
    return DEFAULT_SEGMENTATION_PROFILE, SEGMENTATION_PROFILES[DEFAULT_SEGMENTATION_PROFILE]


def resolve_sampling_profile(name: str) -> tuple[str, dict[str, int | float]]:
    if name in SAMPLING_PROFILE_CONFIGS:
        return name, SAMPLING_PROFILE_CONFIGS[name]
    
    return "balanced", SAMPLING_PROFILE_CONFIGS["balanced"]


@dataclass
class SegmentationSpecification:
    profile_name: str = DEFAULT_SEGMENTATION_PROFILE
    profile: SegmentationProfile = field(default_factory=lambda: SEGMENTATION_PROFILES[DEFAULT_SEGMENTATION_PROFILE])
    frame_sampling_profile: FrameSamplingProfile = field(default_factory=FrameSamplingProfile)


DEFAULT_CAPTION_PROFILE = "generic_longform_continuous"


@dataclass(frozen=True)
class CaptionProfile:
    slots_weight: dict[str, float]
    caption_policy: str
    title_policy: str


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


def resolve_caption_profile(name: str) -> tuple[str, CaptionProfile]:
    if name in CAPTION_PROFILES:
        return name, CAPTION_PROFILES[name]
    return DEFAULT_CAPTION_PROFILE, CAPTION_PROFILES[DEFAULT_CAPTION_PROFILE]


@dataclass
class CaptionSpecification:
    profile_name: str = DEFAULT_CAPTION_PROFILE
    profile: CaptionProfile = field(default_factory=lambda: CAPTION_PROFILES[DEFAULT_CAPTION_PROFILE])
    frame_sampling_profile: FrameSamplingProfile = field(default_factory=FrameSamplingProfile)


@dataclass
class CanonicalExecutionPlan:
    planner_confidence: float = 0.25
    genre_distribution: dict[str, float] = field(default_factory=lambda: {"other": 1.0})
    segmentation_specification: SegmentationSpecification = field(default_factory=SegmentationSpecification)
    caption_specification: CaptionSpecification = field(default_factory=CaptionSpecification)
    chunk_size_sec: int = 600
    chunk_overlap_sec: int = 20


@dataclass
class CandidateBoundary:
    timestamp: float
    boundary_rationale: str = ""
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class FinalizedSegment:
    start_time: float
    end_time: float
    boundary_rationale: str = ""
    boundary_confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    refinement_needed: bool = False


@dataclass
class CaptionedSegment:
    seg_id: str
    start_time: float
    end_time: float
    summary: str
    detail: str
    subtitles_text: str = ""
    token_usage: int = 0
