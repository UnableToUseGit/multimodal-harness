from __future__ import annotations

from ...message_builder import build_text_messages, build_video_messages, build_video_messages_from_path
from ...schemas import FrameSamplingProfile


class MessageGenerationMixin:
    def _prepare_messages_w_video(self, system_prompt, user_prompt, frame_base64_list, timestamps):
        return build_video_messages(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            frame_base64_list=frame_base64_list,
            timestamps=timestamps,
        )

    def _prepare_messages(self, system_prompt, user_prompt):
        return build_text_messages(system_prompt=system_prompt, user_prompt=user_prompt)

    def _generate_single_w_video(
        self,
        system_prompt: str = "",
        user_prompt: str = "",
        video_path: str = "",
        start_time: float = 0.0,
        end_time: float = 0.0,
        video_sampling: FrameSamplingProfile | None = None,
        messages: list[dict] | None = None,
        generator=None,
    ):
        if not generator:
            generator = self.planner

        if not messages:
            sampling = video_sampling or FrameSamplingProfile(fps=1.0, max_resolution=480)
            messages = build_video_messages_from_path(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                video_path=video_path,
                start_time=start_time,
                end_time=end_time,
                video_sampling=sampling,
            )

        return generator.generate_single(messages=messages)
