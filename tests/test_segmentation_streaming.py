import tempfile
import threading
import time
import unittest

from video_atlas.agents.video_atlas.segmentation import SegmentationMixin
from video_atlas.schemas.canonical_video_atlas import (
    CandidateBoundary,
    CaptionedSegment,
    CanonicalExecutionPlan,
    CaptionSpecification,
    FinalizedSegment,
    FrameSamplingProfile,
    SegmentationProfile,
    SegmentationSpecification,
)
from video_atlas.workspaces.base import get_logger


class _StreamingSegmentationHarness(SegmentationMixin):
    def __init__(self):
        self.logger = get_logger("StreamingSegmentationHarness")
        self.captioner = object()
        self.detect_calls = []
        self.caption_started = threading.Event()
        self._written = {}

    def _log_info(self, message, *args):
        self.logger.info(message, *args)

    def _log_warning(self, message, *args):
        self.logger.warning(message, *args)

    def _log_error(self, message, *args):
        self.logger.error(message, *args)

    def _write_workspace_text(self, relative_path, content):
        self._written[str(relative_path)] = content

    def _clip_exists(self, relative_path):
        return False

    def _extract_clip(self, video_path, seg_start_time, seg_end_time, relative_output_path):
        return None

    def _segment_save_name(self, seg_id, seg_title, seg_start_time, seg_end_time):
        return f"seg{seg_id:04d}"

    def _generate_final_title(self, **kwargs):
        return kwargs.get("title_hint") or f"Segment {int(kwargs['seg_start_time'])}"

    def _process_segment_task(self, **kwargs):
        segment = kwargs["segment"]
        self.caption_started.set()
        time.sleep(0.05)
        return CaptionedSegment(
            start_time=segment.start_time,
            end_time=segment.end_time,
            seg_title=segment.title_hint or f"Segment {int(segment.start_time)}",
            title_hint=segment.title_hint,
            summary="summary",
            detail="detail",
            token_usage=1,
        )

    def _detect_candidate_boundaries_for_chunk(self, **kwargs):
        core_start = kwargs["core_start_time"]
        core_end = kwargs["core_end_time"]
        self.detect_calls.append((core_start, core_end, self.caption_started.is_set()))
        if core_start == 0:
            return [CandidateBoundary(timestamp=40, confidence=0.8, title_hint="opening")]
        if core_start == 40:
            return [CandidateBoundary(timestamp=70, confidence=0.9, title_hint="middle")]
        return []

    def _refine_segment(self, **kwargs):
        return [kwargs["segment"]]


class SegmentationStreamingTest(unittest.TestCase):
    def _make_plan(self) -> CanonicalExecutionPlan:
        sampling = FrameSamplingProfile(fps=0.5, max_resolution=480, use_subtitles=True)
        profile = SegmentationProfile(
            signal_priority="balanced",
            target_segment_length_sec=(30, 120),
            default_sampling_profile="balanced",
            boundary_evidence_primary=("topic_shift_in_subtitles",),
            boundary_evidence_secondary=("speaker_change",),
            segmentation_policy="Prefer stable segments.",
            title_policy="Use stable titles.",
        )
        return CanonicalExecutionPlan(
            planner_confidence=0.9,
            genre_distribution={"other": 1.0},
            segmentation_specification=SegmentationSpecification(
                profile_name="test_profile",
                profile=profile,
                frame_sampling_profile=sampling,
            ),
            caption_specification=CaptionSpecification(frame_sampling_profile=sampling),
            chunk_size_sec=60,
            chunk_overlap_sec=10,
        )

    def test_check_candidate_boundaries_filters_by_chunk_and_confidence(self):
        harness = _StreamingSegmentationHarness()
        revised = harness._check_candidate_boundaries(
            [
                {"timestamp": 12, "confidence": 0.7, "title_hint": "keep", "evidence": ["topic_shift_in_subtitles"]},
                {"timestamp": 12, "confidence": 0.8, "title_hint": "dup"},
                {"timestamp": 9, "confidence": 0.9},
                {"timestamp": 19, "confidence": 0.2},
            ],
            chunk_start_time=10,
            chunk_end_time=20,
            min_confidence=0.35,
        )
        self.assertEqual(len(revised), 1)
        self.assertEqual(revised[0].timestamp, 12)
        self.assertEqual(revised[0].title_hint, "keep")

    def test_update_chunk_start_uses_last_kept_boundary(self):
        harness = _StreamingSegmentationHarness()
        next_start = harness._update_chunk_start(
            core_end_time=60,
            candidate_boundaries=[CandidateBoundary(timestamp=35), CandidateBoundary(timestamp=44)],
        )
        self.assertEqual(next_start, 44)
        self.assertEqual(harness._update_chunk_start(60, []), 60)

    def test_build_segments_from_candidates_marks_refine_need(self):
        harness = _StreamingSegmentationHarness()
        plan = self._make_plan()
        segments = harness._build_segments_from_candidates(
            segment_start_time=0,
            segment_end_time=170,
            candidate_boundaries=[CandidateBoundary(timestamp=40, confidence=0.8, title_hint="a")],
            execution_plan=plan,
        )
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].end_time, 40)
        self.assertTrue(segments[1].refinement_needed)

    def test_generate_local_atlas_pipelines_caption_with_boundary_detection(self):
        harness = _StreamingSegmentationHarness()
        plan = self._make_plan()
        contexts = harness._generate_local_atlas(
            video_path="video.mp4",
            duration_int=100,
            subtitle_items=[],
            execution_plan=plan,
            verbose=False,
        )
        self.assertEqual(len(contexts), 3)
        self.assertEqual([item["start_time"] for item in contexts], [0, 40, 70])
        self.assertFalse(harness.detect_calls[0][2])
        self.assertTrue(harness.detect_calls[1][2])


if __name__ == "__main__":
    unittest.main()
