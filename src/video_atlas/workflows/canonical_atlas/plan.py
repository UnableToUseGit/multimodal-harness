from __future__ import annotations

import concurrent.futures

from ...prompts import PLANNER_PROMPT
from ...utils import get_frame_indices, get_subtitle_in_segment, prepare_video_input


class PlanMixin:
    def _collect_probe_inputs(self, video_path: str, duration: float, subtitle_items: list | None = None, frame_sampling_params: dict | None = None):
        subtitle_items = subtitle_items or []
        frame_sampling_params = frame_sampling_params or {}

        segments = []
        clip_duration = 30
        if duration <= clip_duration:
            segments.append((0, 0, duration))
        else:
            for ratio in [0.0, 0.25, 0.50, 0.75]:
                start = int(duration * ratio)
                if start + clip_duration > duration:
                    start = duration - clip_duration
                segments.append((int(ratio * 100), start, start + clip_duration))
            segments = sorted(list(set(segments)))

        def _process_segment(segment):
            ratio, start, end = segment
            _, subtitles_str_in_seg = get_subtitle_in_segment(subtitle_items, start, end)
            fps = frame_sampling_params.get("fps", 1)
            max_resolution = frame_sampling_params.get("max_resolution", 480)
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
                    self._log_warning("Probe failed for segment %s: %s", future_to_segment[future], exc)

        return sorted(prepared_inputs, key=lambda item: item[0])

    def _run_plan_planner(self, prepared_probe_inputs, duration: float, subtitle_items: list | None = None):
        subtitle_items = subtitle_items or []
        system_prompt, user_prompt = PLANNER_PROMPT.render()
        user_content = [
            {"type": "text", "text": user_prompt},
            {"type": "text", "text": "[GLOBAL_STATS]"},
            {
                "type": "text",
                "text": (
                    f"- Duration: {duration} seconds.\n"
                    f"- Subtitle word count: {len(' '.join([item['text'] for item in subtitle_items]).split())}.\n"
                ),
            },
        ]

        for ratio, frame_base64_list, timestamps, subtitles_str_in_seg in prepared_probe_inputs:
            user_content.extend(
                [
                    {"type": "text", "text": f"[PROBE_{ratio}%]"},
                    {"type": "text", "text": "Frames:\n"},
                ]
            )
            for frame_base64, timestamp in zip(frame_base64_list, timestamps):
                user_content.extend(
                    [
                        {"type": "text", "text": f"<{timestamp:.1f} seconds>"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{frame_base64}"}},
                    ]
                )
            user_content.append({"type": "text", "text": f"Subtitles: \n{subtitles_str_in_seg}"})

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        output = self.planner.generate_single(messages=messages) 
        try:
            planner_reasoning_content = output['response']['choices'][0]['message']['reasoning']      
        except:
            planner_reasoning_content = ''
        planner_output = self.parse_response(output["text"])
        return planner_output, planner_reasoning_content

    def _plan_video_execution(
        self,
        video_path: str,
        duration: float,
        subtitle_items: list | None = None,
        frame_sampling_params: dict | None = None,
    ):
        prepared_probe_inputs = self._collect_probe_inputs(
            video_path=video_path,
            duration=duration,
            subtitle_items=subtitle_items,
            frame_sampling_params=frame_sampling_params,
        )
        planner_output, planner_reasoning_content = self._run_plan_planner(
            prepared_probe_inputs=prepared_probe_inputs,
            duration=duration,
            subtitle_items=subtitle_items,
        )
        return self._construct_execution_plan(planner_output, planner_reasoning_content)
