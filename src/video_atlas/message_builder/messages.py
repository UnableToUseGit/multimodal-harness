from __future__ import annotations

from ..schemas import FrameSamplingProfile
from pathlib import Path


def _load_video_helpers():
    from ..utils import get_frame_indices, prepare_video_input

    return get_frame_indices, prepare_video_input


def build_text_messages(system_prompt: str, user_prompt: str) -> list[dict]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_video_messages(
    system_prompt: str,
    user_prompt: str,
    frame_base64_list: list[str],
    timestamps: list[float],
) -> list[dict]:
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


def build_video_messages_from_path(
    system_prompt: str,
    user_prompt: str,
    video_path: Path | str,
    start_time: float,
    end_time: float,
    video_sampling: FrameSamplingProfile | None = None,
) -> list[dict]:
    sampling = video_sampling or FrameSamplingProfile(fps=1.0, max_resolution=480)
    get_frame_indices, prepare_video_input = _load_video_helpers()
    frame_indices = get_frame_indices(video_path, start_time, end_time, fps=sampling.fps)
    frame_base64_list, timestamps = prepare_video_input(
        video_path,
        frame_indices,
        sampling.max_resolution,
        max_workers=4,
    )
    return build_video_messages(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        frame_base64_list=frame_base64_list,
        timestamps=timestamps,
    )
