from __future__ import annotations

import concurrent.futures
import time
from dataclasses import asdict
from pathlib import Path

from ...prompts import CONTEXT_GENERATION_PROMPT, VIDEO_GLOBAL_PROMPT, VIDEO_SEGMENT_PROMPT
from ...schemas import VideoGlobal, VideoSeg
from ...utils import get_subtitle_in_segment


class SegmentationMixin:
    def _process_segment_task(
        self,
        video_path: str,
        seg_start_time: float,
        seg_end_time: float,
        seg_title: str,
        seg_id: int,
        subtitle_items: list,
        video_process_spec,
    ) -> dict:
        try:
            description_sampling = asdict(video_process_spec.description_sampling)
            caption_with_subtitles = description_sampling.get("use_subtitles", True)
            caption_spec = video_process_spec.caption_spec

            if caption_with_subtitles:
                _, subtitles_str_in_seg = get_subtitle_in_segment(subtitle_items, seg_start_time, seg_end_time)
            else:
                subtitles_str_in_seg = ""

            format_args = {**asdict(caption_spec), "segment_title": seg_title}
            user_prompt = CONTEXT_GENERATION_PROMPT["USER"].format(subtitles=subtitles_str_in_seg, **format_args)
            output = self._generate_single_w_video(
                system_prompt=CONTEXT_GENERATION_PROMPT["SYSTEM"],
                user_prompt=user_prompt,
                video_path=video_path,
                start_time=seg_start_time,
                end_time=seg_end_time,
                video_sampling=description_sampling,
                generator=self.captioner,
            )

            context = self.parse_response(output["text"])
            if "summary" not in context or context["summary"] == "":
                context["summary"] = f"No summary for segment {seg_start_time} to {seg_end_time}"
            if "final_caption" not in context or context["final_caption"] == "":
                context["detail"] = f"No detail description for segment {seg_start_time} to {seg_end_time}"
            else:
                context["detail"] = context["final_caption"]

            video_seg = VideoSeg(
                seg_id=f"seg_{seg_id:04d}",
                seg_title=seg_title,
                summary=context.get("summary", ""),
                start_time=seg_start_time,
                end_time=seg_end_time,
                duration=seg_end_time - seg_start_time,
                detail=context.get("detail", ""),
            )
            save_name = self._segment_save_name(seg_id, seg_title, seg_start_time, seg_end_time)
            self._write_workspace_text(Path("segments") / save_name / "README.md", video_seg.to_markdown(with_subtitles=caption_with_subtitles))
            if subtitles_str_in_seg:
                self._write_workspace_text(Path("segments") / save_name / "SUBTITLES.md", subtitles_str_in_seg)

            clip_relative_path = Path("segments") / save_name / "video_clip.mp4"
            if not self._clip_exists(clip_relative_path):
                self._extract_clip(video_path, seg_start_time, seg_end_time, clip_relative_path)

            return {
                "start_time": seg_start_time,
                "end_time": seg_end_time,
                "seg_title": seg_title,
                **context,
                "token_usage": output["response"]["usage"]["total_tokens"],
            }
        except Exception as exc:
            self._log_error("Error processing segment %s (%.2f-%.2f): %s", seg_id, seg_start_time, seg_end_time, exc)
            return {
                "start_time": seg_start_time,
                "end_time": seg_end_time,
                "seg_title": f"Error: {exc}",
                "summary": f"Error: {exc}",
                "detail": f"Error: {exc}",
                "token_usage": 0,
            }

    def _generate_segments_and_context(self, video_path: str, duration_int: int, subtitle_items: list, verbose: bool = False, chunk_size: int = 600, video_process_spec=None):
        segment_spec = video_process_spec.segment_spec
        segmentation_sampling = asdict(video_process_spec.segmentation_sampling)
        all_contexts = []
        futures = []
        chunk_start_time = 0
        total_segments_count = 0
        chunk_index = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            while True:
                chunk_end_time = min(chunk_start_time + chunk_size, duration_int)
                started_at = time.time()

                try:
                    _, subtitles_str_in_seg = get_subtitle_in_segment(subtitle_items, chunk_start_time, chunk_end_time)
                    user_prompt = VIDEO_SEGMENT_PROMPT["USER"].format(
                        t_start=chunk_start_time,
                        t_end=chunk_end_time,
                        subtitles=subtitles_str_in_seg,
                        **asdict(segment_spec),
                    )
                    output = self._generate_single_w_video(
                        system_prompt=VIDEO_SEGMENT_PROMPT["SYSTEM"],
                        user_prompt=user_prompt,
                        video_path=video_path,
                        start_time=chunk_start_time,
                        end_time=chunk_end_time,
                        video_sampling=segmentation_sampling,
                        generator=self.segmentor,
                    )
                    segmentation_info = self.parse_response(output["text"])
                    segmentation_info = self.revise_segmentation_info(
                        segmentation_info,
                        chunk_start_time=chunk_start_time,
                        chunk_end_time=chunk_end_time,
                    )
                except (AssertionError, Exception) as exc:
                    self._log_error("[Chunk %03d] Failed to generate valid segmentation info: %s", chunk_index, exc)
                    break

                if verbose:
                    self._log_info(
                        "[Chunk %03d] Segmentation generated in %.2fs | Segments found: %d | Token usage: %s",
                        chunk_index,
                        time.time() - started_at,
                        len(segmentation_info),
                        output["response"]["usage"]["total_tokens"],
                    )

                if chunk_end_time >= duration_int:
                    segmentation_info.append({"timestamp": chunk_end_time, "segment_title": "ending"})

                seg_start_time = chunk_start_time
                for index, item in enumerate(segmentation_info):
                    seg_end_time = item["timestamp"]
                    future = executor.submit(
                        self._process_segment_task,
                        video_path=video_path,
                        seg_start_time=seg_start_time,
                        seg_end_time=seg_end_time,
                        seg_title=item["segment_title"],
                        seg_id=total_segments_count + 1 + index,
                        subtitle_items=subtitle_items,
                        video_process_spec=video_process_spec,
                    )
                    futures.append(future)
                    seg_start_time = seg_end_time

                total_segments_count += len(segmentation_info)
                chunk_start_time = segmentation_info[-1]["timestamp"]
                chunk_index += 1
                if chunk_end_time >= duration_int:
                    break

            for future in concurrent.futures.as_completed(futures):
                try:
                    all_contexts.append(future.result())
                except Exception as exc:
                    self._log_error("Segment processing failed: %s", exc)

        all_contexts.sort(key=lambda item: item["start_time"])
        return all_contexts

    def _generate_global_context(self, all_contexts, duration_int, verbose, caption_with_subtitles: bool = True):
        started_at = time.time()
        segments_description = "\n".join(
            [
                f'- segments{seg_id + 1:04d}: {seg["start_time"]:.1f} - {seg["end_time"]:.1f} seconds\n'
                f'Title: {seg["seg_title"]}\nDetail Description: {seg["detail"]}\n'
                for seg_id, seg in enumerate(all_contexts)
            ]
        )
        user_prompt = VIDEO_GLOBAL_PROMPT["USER"].format(segments_description=segments_description)
        output = self.captioner.generate_single(
            messages=self._prepare_messages(system_prompt=VIDEO_GLOBAL_PROMPT["SYSTEM"], user_prompt=user_prompt)
        )
        global_context = self.parse_response(output["text"])

        if verbose:
            self._log_info(
                "[Global] Context generation completed in %.2fs | Token usage: %s",
                time.time() - started_at,
                output["response"]["usage"]["total_tokens"],
            )

        segments_quickview = "\n".join(
            [
                f'- segments{seg_id + 1:04d}: {seg["start_time"]:.1f} - {seg["end_time"]:.1f} seconds: {seg["summary"]}'
                for seg_id, seg in enumerate(all_contexts)
            ]
        )
        video_global = VideoGlobal(
            title=global_context.get("title", ""),
            abstract=global_context.get("abstract", ""),
            duration=duration_int,
            num_segments=len(all_contexts),
            segments_quickview=segments_quickview,
        )
        self._write_workspace_text("README.md", video_global.to_markdown(with_subtitles=caption_with_subtitles))
