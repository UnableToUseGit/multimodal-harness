import unittest
from unittest.mock import patch

from video_atlas.schemas import FrameSamplingProfile


class MultimodalMessagesTest(unittest.TestCase):
    def test_build_text_messages_returns_two_message_roles(self) -> None:
        from video_atlas.message_builder.messages import build_text_messages

        messages = build_text_messages(system_prompt="system", user_prompt="user")

        self.assertEqual(
            messages,
            [
                {"role": "system", "content": "system"},
                {"role": "user", "content": "user"},
            ],
        )

    def test_build_video_messages_appends_frames_timestamps_and_user_prompt(self) -> None:
        from video_atlas.message_builder.messages import build_video_messages

        messages = build_video_messages(
            system_prompt="system",
            user_prompt="user",
            frame_base64_list=["frame1", "frame2"],
            timestamps=[0.1, 0.2],
        )

        self.assertEqual(messages[0], {"role": "system", "content": "system"})
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"][0]["type"], "text")
        self.assertEqual(messages[1]["content"][0]["text"], "<0.1 seconds>")
        self.assertEqual(messages[1]["content"][1]["type"], "image_url")
        self.assertEqual(messages[1]["content"][2]["text"], "<0.2 seconds>")
        self.assertEqual(messages[1]["content"][-1], {"type": "text", "text": "user"})

    def test_build_video_messages_from_path_uses_sampling_but_only_returns_messages(self) -> None:
        from video_atlas.message_builder.messages import build_video_messages_from_path

        sampling = FrameSamplingProfile(fps=0.5, max_resolution=360)
        helper_calls = []

        def _fake_get_frame_indices(*args, **kwargs):
            helper_calls.append(kwargs)
            return [1, 2]

        with patch(
            "video_atlas.message_builder.messages._load_video_helpers",
            return_value=(
                _fake_get_frame_indices,
                lambda *args, **kwargs: (["frame1", "frame2"], [0.1, 0.2]),
            ),
        ) as mock_helpers:
            with patch("video_atlas.message_builder.messages.build_video_messages") as mock_build_video_messages:
                mock_build_video_messages.return_value = [
                    {"role": "system", "content": "system"},
                    {"role": "user", "content": "user"},
                ]
                messages = build_video_messages_from_path(
                    system_prompt="system",
                    user_prompt="user",
                    video_path="video.mp4",
                    start_time=0,
                    end_time=10,
                    video_sampling=sampling,
                )

        mock_helpers.assert_called_once()
        self.assertEqual(helper_calls[0]["max_frames"], 48)
        mock_build_video_messages.assert_called_once_with(
            system_prompt="system",
            user_prompt="user",
            frame_base64_list=["frame1", "frame2"],
            timestamps=[0.1, 0.2],
        )
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")


if __name__ == "__main__":
    unittest.main()
