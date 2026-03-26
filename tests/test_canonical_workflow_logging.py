from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from video_atlas.workflows.canonical_atlas_workflow import CanonicalAtlasWorkflow


class _DummyGenerator:
    def generate_single(self, *args, **kwargs):
        raise AssertionError("generator should not be called in this test")


class CanonicalWorkflowLoggingTest(unittest.TestCase):
    def test_resolve_srt_file_path_does_not_crash_without_logger_helpers(self) -> None:
        workflow = CanonicalAtlasWorkflow(
            planner=_DummyGenerator(),
            segmentor=_DummyGenerator(),
            captioner=_DummyGenerator(),
            transcriber=None,
            generate_subtitles_if_missing=False,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            video_path = output_dir / "video.mp4"
            video_path.write_bytes(b"mp4")

            srt_path, audio_path = workflow._resolve_srt_file_path(output_dir, video_path, verbose=True)

        self.assertIsNone(srt_path)
        self.assertIsNone(audio_path)


if __name__ == "__main__":
    unittest.main()
