from __future__ import annotations

from ...schemas import FrameSamplingProfile

from ...utils import get_frame_indices, prepare_video_input


class MessageGenerationMixin:
    def _prepare_messages_w_video(self, system_prompt, user_prompt, frame_base64_list, timestamps):
        user_content = []
        for frame_base64, timestamp in zip(frame_base64_list, timestamps):
            user_content.extend(
                [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{frame_base64}",
                        },
                    },
                    {
                        "type": "text",
                        "text": f"<{timestamp:.1f} seconds>",
                    },
                ]
            )
        user_content.append({"type": "text", "text": user_prompt})
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

    def _prepare_messages(self, system_prompt, user_prompt):
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

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
            fps = sampling.fps
            max_resolution = sampling.max_resolution
            frame_indices = get_frame_indices(video_path, start_time, end_time, fps=fps)
            frame_base64_list, timestamps = prepare_video_input(video_path, frame_indices, max_resolution, max_workers=4)
            messages = self._prepare_messages_w_video(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                frame_base64_list=frame_base64_list,
                timestamps=timestamps,
            )

        return generator.generate_single(messages=messages)
