from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from video_atlas.schemas import AtlasSegment, CanonicalCompositionResult, CanonicalExecutionPlan
from video_atlas.workflows.canonical_atlas_workflow import CanonicalAtlasWorkflow


class _NoopGenerator:
    def generate_single(self, *args, **kwargs):
        return {"text": "{}", "json": {}, "response": {"usage": {"total_tokens": 1}}}


class _TwoStageHarness(CanonicalAtlasWorkflow):
    def __init__(self):
        super().__init__(
            planner=_NoopGenerator(),
            text_segmentor=_NoopGenerator(),
            multimodal_segmentor=_NoopGenerator(),
            structure_composer=_NoopGenerator(),
            captioner=_NoopGenerator(),
            transcriber=None,
        )
        self.structure_request_seen = None
        self.written_atlas = None

    def _plan_video_execution(self, video_path: str, duration: float, subtitle_items=None, frame_sampling_params=None):
        return CanonicalExecutionPlan()

    def _parse_video_into_segments(self, video_path: str, duration: float, subtitle_items: list, execution_plan, verbose: bool = False):
        return (
            [
                {
                    "seg_id": "unit_0001",
                    "start_time": 0.0,
                    "end_time": 15.0,
                    "title": "Intro Unit",
                    "summary": "Opening setup",
                    "detail": "Opening detail",
                    "subtitles_text": "hello world",
                },
                {
                    "seg_id": "unit_0002",
                    "start_time": 15.0,
                    "end_time": 30.0,
                    "title": "Development Unit",
                    "summary": "Follow-up explanation",
                    "detail": "Follow-up detail",
                    "subtitles_text": "continued",
                },
            ],
            [],
        )

    def _compose_canonical_structure(self, units, concise_description: str = "", genres=None, structure_request: str = ""):
        self.structure_request_seen = structure_request
        return CanonicalCompositionResult(
            title="Composed Atlas",
            abstract="Composed abstract",
            segments=[
                AtlasSegment(
                    segment_id="seg_0001",
                    unit_ids=["unit_0001", "unit_0002"],
                    title="Opening Chapter",
                    start_time=0.0,
                    end_time=30.0,
                    summary="Combined unit summary",
                    composition_rationale="The two units form one coarse chapter.",
                    folder_name="seg-0001-opening-chapter-00:00:00-00:00:30",
                )
            ],
            composition_rationale="Keep the structure coarse.",
            structure_request=structure_request,
        )


class CanonicalTwoStagePipelineTest(unittest.TestCase):
    def test_create_routes_units_into_structure_composition(self) -> None:
        harness = _TwoStageHarness()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            video_path = root / "video.mp4"
            video_path.write_bytes(b"video")
            srt_path = root / "subtitles.srt"
            srt_path.write_text("1\n00:00:00,000 --> 00:00:10,000\nhello\n", encoding="utf-8")
            output_dir = root / "atlas"

            with patch("video_atlas.workflows.canonical_atlas.pipeline.copy_to", side_effect=lambda src, dest: Path(dest) / Path(src).name), \
                patch("video_atlas.workflows.canonical_atlas.pipeline.write_text_to", side_effect=lambda dest, rel, content: Path(dest) / Path(rel)), \
                patch("video_atlas.workflows.canonical_atlas.pipeline.parse_srt", return_value=([{"start": 0.0, "end": 10.0, "text": "hello"}], "hello")), \
                patch("video_atlas.workflows.canonical_atlas.pipeline.get_video_property", return_value={"duration": 30.0, "resolution": "1280x720"}), \
                patch("video_atlas.workflows.canonical_atlas.pipeline.CanonicalAtlasWriter.write", autospec=True) as mock_write:
                atlas, cost_time_info = harness.create(
                    output_dir=output_dir,
                    source_video_path=video_path,
                    source_srt_file_path=srt_path,
                    structure_request="请按较粗的章节划分",
                    verbose=False,
                )

        self.assertEqual(harness.structure_request_seen, "请按较粗的章节划分")
        self.assertEqual(atlas.title, "Composed Atlas")
        self.assertEqual(len(atlas.units), 2)
        self.assertEqual(len(atlas.segments), 1)
        self.assertEqual(atlas.segments[0].unit_ids, ["unit_0001", "unit_0002"])
        self.assertIn("composition_cost_time", cost_time_info)
        self.assertEqual(mock_write.call_count, 1)


if __name__ == "__main__":
    unittest.main()
