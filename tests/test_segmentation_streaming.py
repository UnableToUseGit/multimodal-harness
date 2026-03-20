import tempfile
import threading
import time
import unittest

from video_atlas.agents.video_atlas.video_parsing import VideoParsingMixin
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


class _StreamingSegmentationHarness(VideoParsingMixin):
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

    def _generate_local_caption(self, **kwargs):
        segment = kwargs["segment"]
        self.caption_started.set()
        time.sleep(0.05)
        return CaptionedSegment(
            seg_id=f"seg_{kwargs['seg_id']:04d}",
            start_time=segment.start_time,
            end_time=segment.end_time,
            summary="summary",
            detail="detail",
            subtitles_text="",
            token_usage=1,
        )

    def _detect_candidate_boundaries_for_chunk(self, **kwargs):
        core_start = kwargs["core_start_time"]
        core_end = kwargs["core_end_time"]
        self.detect_calls.append((core_start, core_end, self.caption_started.is_set()))
        if core_start == 0:
            return [CandidateBoundary(timestamp=40, confidence=0.8)]
        if core_start == 40:
            return [CandidateBoundary(timestamp=70, confidence=0.9)]
        return []

    def _refine_segment(self, **kwargs):
        return [kwargs["segment"]]


class SegmentationStreamingTest(unittest.TestCase):
    def _make_plan(self) -> CanonicalExecutionPlan:
        sampling = FrameSamplingProfile(fps=0.5, max_resolution=480)
        profile = SegmentationProfile(
            signal_priority="balanced",
            target_segment_length_sec=(30, 120),
            default_sampling_profile="balanced",
            boundary_evidence_primary=("topic_shift_in_subtitles",),
            boundary_evidence_secondary=("speaker_change",),
            segmentation_policy="Prefer stable segments.",
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
                {"timestamp": 12, "confidence": 0.7, "evidence": ["topic_shift_in_subtitles"]},
                {"timestamp": 12, "confidence": 0.8},
                {"timestamp": 9, "confidence": 0.9},
                {"timestamp": 19, "confidence": 0.2},
            ],
            chunk_start_time=10,
            chunk_end_time=20,
            min_confidence=0.35,
        )
        self.assertEqual(len(revised), 1)
        self.assertEqual(revised[0].timestamp, 12)
        self.assertEqual(revised[0].evidence, ["topic_shift_in_subtitles"])

    def test_update_chunk_start_uses_last_kept_boundary(self):
        harness = _StreamingSegmentationHarness()
        next_start = harness._update_chunk_start(
            core_end_time=60,
            candidate_boundaries=[CandidateBoundary(timestamp=35), CandidateBoundary(timestamp=44)],
        )
        self.assertEqual(next_start, 44)
        self.assertEqual(harness._update_chunk_start(60, []), 60)

    def test_build_then_postprocess_segments_marks_refine_need(self):
        harness = _StreamingSegmentationHarness()
        plan = self._make_plan()
        segments = harness._build_raw_segments_from_candidates(
            segment_start_time=0,
            segment_end_time=170,
            candidate_boundaries=[CandidateBoundary(timestamp=40, confidence=0.8)],
        )
        self.assertFalse(segments[1].refinement_needed)
        segments = harness._postprocess_segments(segments, plan)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].end_time, 40)
        self.assertTrue(segments[1].refinement_needed)

    def test_materialize_committed_segments_uses_current_chunk_boundaries(self):
        harness = _StreamingSegmentationHarness()
        plan = self._make_plan()
        committed_segments, next_open_start = harness._materialize_committed_segments(
            video_path="video.mp4",
            subtitle_items=[],
            execution_plan=plan,
            open_segment_start=0,
            candidate_boundaries=[CandidateBoundary(timestamp=40, confidence=0.8)],
        )
        self.assertEqual(next_open_start, 40)
        self.assertEqual(len(committed_segments), 1)
        self.assertEqual(committed_segments[0].start_time, 0)
        self.assertEqual(committed_segments[0].end_time, 40)

    def test_materialize_committed_segments_can_finalize_tail_without_boundaries(self):
        harness = _StreamingSegmentationHarness()
        plan = self._make_plan()
        tail_segments, next_open_start = harness._materialize_committed_segments(
            video_path="video.mp4",
            subtitle_items=[],
            execution_plan=plan,
            open_segment_start=40,
            candidate_boundaries=[],
            segment_end_time=100,
        )
        self.assertEqual(next_open_start, 100)
        self.assertEqual(len(tail_segments), 1)
        self.assertEqual(tail_segments[0].start_time, 40)
        self.assertEqual(tail_segments[0].end_time, 100)

    def test_parse_video_into_segments_pipelines_caption_with_boundary_detection(self):
        harness = _StreamingSegmentationHarness()
        plan = self._make_plan()
        contexts = harness._parse_video_into_segments(
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
