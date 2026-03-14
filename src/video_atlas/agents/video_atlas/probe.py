from __future__ import annotations

import concurrent.futures

from ...prompts import VIDEO_PROBE_PROMPT
from ...utils import get_frame_indices, get_subtitle_in_segment, prepare_video_input


class ProbeMixin:
    def _probe_video_content(self, video_path: str, duration_int: int, subtitle_items: list | None = None, video_sampling: dict | None = None):
        subtitle_items = subtitle_items or []
        video_sampling = video_sampling or {}

        segments = []
        clip_duration = 30
        if duration_int <= clip_duration:
            segments.append((0, 0, duration_int))
        else:
            for ratio in [0.25, 0.50, 0.75]:
                start = int(duration_int * ratio)
                if start + clip_duration > duration_int:
                    start = duration_int - clip_duration
                segments.append((int(ratio * 100), start, start + clip_duration))
            segments = sorted(list(set(segments)))

        def _process_segment(segment):
            ratio, start, end = segment
            _, subtitles_str_in_seg = get_subtitle_in_segment(subtitle_items, start, end)
            fps = video_sampling.get("fps", 1)
            max_resolution = video_sampling.get("max_resolution", 480)
            frame_indices = get_frame_indices(video_path, start, end, fps=fps)
            frame_base64_list, timestamps = prepare_video_input(video_path, frame_indices, max_resolution, max_workers=4)
            return ratio, frame_base64_list, timestamps, subtitles_str_in_seg

        prepared_inputs = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(segments), 3)) as executor:
            future_to_segment = {executor.submit(_process_segment, segment): segment for segment in segments}
            for future in concurrent.futures.as_completed(future_to_segment):
                try:
                    result = future.result()
                    if result:
                        prepared_inputs.append(result)
                except Exception as exc:
                    print(f"⚠️ Warning: Probe failed for segment {future_to_segment[future]}: {exc}")

        prepared_inputs = sorted(prepared_inputs, key=lambda item: item[0])
        user_content = [
            {"type": "text", "text": VIDEO_PROBE_PROMPT["USER"]},
            {"type": "text", "text": "[GLOBAL_STATS]"},
            {
                "type": "text",
                "text": (
                    f"- Duration: {duration_int} seconds.\n"
                    f"- Subtitle word count: {len(' '.join([item['text'] for item in subtitle_items]).split())}.\n"
                ),
            },
        ]

        for ratio, frame_base64_list, timestamps, subtitles_str_in_seg in prepared_inputs:
            user_content.extend(
                [
                    {"type": "text", "text": f"[PROBE_{ratio}%]"},
                    {"type": "text", "text": "Frames:\n"},
                ]
            )
            for frame_base64, timestamp in zip(frame_base64_list, timestamps):
                user_content.extend(
                    [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{frame_base64}"}},
                        {"type": "text", "text": f"<{timestamp:.1f} seconds>"},
                    ]
                )
            user_content.append({"type": "text", "text": f"Subtitles: \n{subtitles_str_in_seg}"})

        messages = [
            {"role": "system", "content": VIDEO_PROBE_PROMPT["SYSTEM"]},
            {"role": "user", "content": user_content},
        ]
        output = self._generate_single_w_video(messages=messages, generator=self.planner)
        strategy_pkg = self.parse_response(output["text"])
        return self._build_spec_from_strategy_pkg(strategy_pkg)
