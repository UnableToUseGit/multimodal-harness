import tempfile
import threading
import time
import unittest
from types import SimpleNamespace

from video_atlas.workflows.canonical_atlas.video_parsing import VideoParsingMixin
from video_atlas.schemas.canonical_atlas import (
    CandidateBoundary,
    CaptionedSegment,
    CanonicalExecutionPlan,
    FinalizedSegment,
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
            return [CandidateBoundary(timestamp=40, boundary_rationale="topic shift", confidence=0.8)]
        if core_start == 40:
            return [CandidateBoundary(timestamp=70, boundary_rationale="phase change", confidence=0.9)]
        return []

    def _refine_segment(self, **kwargs):
        return [kwargs["segment"]]


class SegmentationStreamingTest(unittest.TestCase):
    def _make_plan(self) -> CanonicalExecutionPlan:
        profile = SimpleNamespace(
            route="multimodal",
            segmentation_policy="Prefer stable segments.",
            caption_policy="Describe the segment conservatively.",
            target_segment_length_sec=(30, 120),
        )
        return CanonicalExecutionPlan(
            planner_confidence=0.9,
            genres=["other"],
            concise_description="A test video.",
            profile_name="sports",
            profile=profile,
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
        units, boundary_records = harness._parse_video_into_segments(
            video_path="video.mp4",
            duration=100,
            subtitle_items=[],
            execution_plan=plan,
            verbose=False,
        )
        self.assertEqual(len(units), 3)
        self.assertEqual([item.start_time for item in units], [0, 40, 70])
        self.assertFalse(harness.detect_calls[0][2])
        self.assertTrue(harness.detect_calls[1][2])
        self.assertEqual(len(boundary_records), 2)

    def test_parse_video_into_segments_does_not_reprocess_partial_final_chunk(self):
        harness = _StreamingSegmentationHarness()
        plan = self._make_plan()

        harness._parse_video_into_segments(
            video_path="video.mp4",
            duration=100,
            subtitle_items=[],
            execution_plan=plan,
            verbose=False,
        )

        self.assertEqual([(start, end) for start, end, _ in harness.detect_calls], [(0, 60), (40, 100)])

    def test_parse_video_into_segments_writes_candidate_boundary_debug_files(self):
        harness = _StreamingSegmentationHarness()
        plan = self._make_plan()

        _, boundary_records = harness._parse_video_into_segments(
            video_path="video.mp4",
            duration=100,
            subtitle_items=[],
            execution_plan=plan,
            verbose=False,
        )

        self.assertEqual(len(boundary_records), 2)
        first_payload = {
            "core_start": boundary_records[0]["core_start_time"],
            "core_end": boundary_records[0]["core_end_time"],
            "last_detection_point": boundary_records[0]["last_detection_point"],
            "candidate_boundaries": [
                {
                    "boundary_rationale": item.boundary_rationale,
                }
                for item in boundary_records[0]["candidate_boundaries"]
            ],
        }
        self.assertEqual(first_payload["core_start"], 0.0)
        self.assertEqual(first_payload["core_end"], 60.0)
        self.assertEqual(first_payload["last_detection_point"], 0.0)
        self.assertEqual(first_payload["candidate_boundaries"][0]["boundary_rationale"], "topic shift")

    def test_truncate_prompt_subtitles_keeps_budget(self):
        harness = _StreamingSegmentationHarness()
        source = "A" * 5000

        truncated = harness._truncate_prompt_subtitles(source, max_chars=1000)

        self.assertLessEqual(len(truncated), 1000)
        self.assertIn("[TRUNCATED]", truncated)

    def test_truncate_prompt_subtitles_returns_original_when_short(self):
        harness = _StreamingSegmentationHarness()
        source = "short subtitles"

        self.assertEqual(harness._truncate_prompt_subtitles(source, max_chars=1000), source)


if __name__ == "__main__":
    unittest.main()
