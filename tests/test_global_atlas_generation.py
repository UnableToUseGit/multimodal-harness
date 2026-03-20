import unittest

from video_atlas.agents.video_atlas.atlas_assembly import AtlasAssemblyMixin


class _GlobalAtlasHarness(AtlasAssemblyMixin):
    def __init__(self):
        self._written = {}
        self._messages = None
        self.captioner = self
        self.caption_with_subtitles = True

    def _write_workspace_text(self, relative_path, content):
        self._written[str(relative_path)] = content

    def _prepare_messages(self, system_prompt: str, user_prompt: str):
        self._messages = {"system": system_prompt, "user": user_prompt}
        return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

    def generate_single(self, messages):
        return {
            "text": """
{
  "title": "Full Match Overview",
  "abstract": "The video moves from draft into early setup and then into a decisive mid-game swing.",
  "segment_titles": [
    {"seg_id": "seg_0001", "title": "Draft And Ban"},
    {"seg_id": "seg_0002", "title": "Early Lane Setup"}
  ]
}
""",
            "response": {"usage": {"total_tokens": 42}},
        }

    def parse_response(self, text):
        import json

        return json.loads(text)

    def _log_info(self, *args, **kwargs):
        return None

    def _clip_exists(self, relative_path):
        return False

    def _extract_clip(self, video_path, seg_start_time, seg_end_time, relative_output_path):
        self._written[str(relative_output_path)] = f"clip:{seg_start_time:.1f}-{seg_end_time:.1f}"
        return None

    def _segment_save_name(self, seg_id, seg_title, seg_start_time, seg_end_time):
        return f"seg{seg_id:04d}-{seg_title.lower().replace(' ', '-')}-{seg_start_time:.2f}-{seg_end_time:.2f}s"


class GlobalAtlasGenerationTest(unittest.TestCase):
    def test_assemble_canonical_atlas_writes_root_and_segment_artifacts(self):
        harness = _GlobalAtlasHarness()
        parsed_segments = [
            {
                "seg_id": "seg_0001",
                "start_time": 0.0,
                "end_time": 30.0,
                "summary": "summary 1",
                "detail": "detail 1",
                "subtitles_text": "subtitles 1",
            },
            {
                "seg_id": "seg_0002",
                "start_time": 30.0,
                "end_time": 60.0,
                "summary": "summary 2",
                "detail": "detail 2",
                "subtitles_text": "subtitles 2",
            },
        ]

        harness._assemble_canonical_atlas(
            parsed_segments=parsed_segments,
            video_path="video.mp4",
            duration_int=60,
            verbose=False,
        )

        self.assertIn("README.md", harness._written)
        self.assertIn("segments/seg0001-draft-and-ban-0.00-30.00s/README.md", harness._written)
        self.assertIn("segments/seg0002-early-lane-setup-30.00-60.00s/README.md", harness._written)
        self.assertIn("segments/seg0001-draft-and-ban-0.00-30.00s/SUBTITLES.md", harness._written)
        self.assertIn("segments/seg0001-draft-and-ban-0.00-30.00s/video_clip.mp4", harness._written)
        self.assertIn("Full Match Overview", harness._written["README.md"])
        self.assertIn("Draft And Ban", harness._written["segments/seg0001-draft-and-ban-0.00-30.00s/README.md"])
        self.assertIn("Early Lane Setup", harness._written["segments/seg0002-early-lane-setup-30.00-60.00s/README.md"])
        self.assertIn("detail 1", harness._messages["user"])
        self.assertIn("detail 2", harness._messages["user"])


if __name__ == "__main__":
    unittest.main()
