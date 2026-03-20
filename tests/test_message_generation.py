import importlib
import sys
import types
import unittest
from unittest.mock import patch

from video_atlas.schemas import FrameSamplingProfile


class _StubGenerator:
    def generate_single(self, messages):
        return {"text": "ok", "response": {"usage": {"total_tokens": 1}}, "messages": messages}


class MessageGenerationTest(unittest.TestCase):
    def test_generate_single_w_video_reads_frame_sampling_profile(self):
        fake_utils = types.ModuleType("video_atlas.utils")
        fake_utils.get_frame_indices = lambda *args, **kwargs: [1, 2]
        fake_utils.prepare_video_input = lambda *args, **kwargs: (["frame1", "frame2"], [0.1, 0.2])

        with patch.dict(sys.modules, {"video_atlas.utils": fake_utils}):
            module = importlib.import_module("video_atlas.agents.video_atlas.message_generation")
            importlib.reload(module)

            class _MessageGenerationHarness(module.MessageGenerationMixin):
                def __init__(self):
                    self.planner = _StubGenerator()

            harness = _MessageGenerationHarness()
            sampling = FrameSamplingProfile(fps=0.5, max_resolution=360)

            with patch.object(module, "get_frame_indices", return_value=[1, 2]) as mock_get_frame_indices:
                with patch.object(module, "prepare_video_input", return_value=(["frame1", "frame2"], [0.1, 0.2])) as mock_prepare:
                    harness._generate_single_w_video(
                        system_prompt="system",
                        user_prompt="user",
                        video_path="video.mp4",
                        start_time=0,
                        end_time=10,
                        video_sampling=sampling,
                    )

            mock_get_frame_indices.assert_called_once_with("video.mp4", 0, 10, fps=0.5)
            mock_prepare.assert_called_once_with("video.mp4", [1, 2], 360, max_workers=4)


if __name__ == "__main__":
    unittest.main()
