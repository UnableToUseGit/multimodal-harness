from __future__ import annotations

import concurrent.futures
import time
from dataclasses import asdict
from pathlib import Path

from ...prompts import CONTEXT_GENERATION_PROMPT, TITLE_GENERATION_PROMPT, VIDEO_GLOBAL_PROMPT, VIDEO_SEGMENT_PROMPT
from ...schemas import SegmentDraft, VideoGlobal, VideoSeg
from ...utils import get_subtitle_in_segment


class SegmentationMixin:
    def _generate_final_title(
        self,
        video_path: str,
        seg_start_time: float,
        seg_end_time: float,
        subtitle_items: list,
        video_process_spec,
        title_hint: str = "",
        previous_title_hint: str = "",
        next_title_hint: str = "",
    ) -> str:
        title_spec = asdict(video_process_spec.title_spec)
        _, subtitles_str_in_seg = get_subtitle_in_segment(subtitle_items, seg_start_time, seg_end_time)
        user_prompt = TITLE_GENERATION_PROMPT["USER"].format(
            start_time=seg_start_time,
            end_time=seg_end_time,
            title_hint=title_hint,
            previous_title_hint=previous_title_hint,
            next_title_hint=next_title_hint,
            subtitles=subtitles_str_in_seg,
            **title_spec,
        )
        output = self._generate_single_w_video(
            system_prompt=TITLE_GENERATION_PROMPT["SYSTEM"],
            user_prompt=user_prompt,
            video_path=video_path,
            start_time=seg_start_time,
            end_time=seg_end_time,
            video_sampling=asdict(video_process_spec.description_sampling),
            generator=self.captioner,
        )
        response = self.parse_response(output["text"])
        final_title = response.get("final_title", "") if isinstance(response, dict) else ""
        if not isinstance(final_title, str) or not final_title.strip():
            final_title = title_hint.strip() or f"Segment {seg_start_time:.0f}-{seg_end_time:.0f}s"
        return final_title.strip()

    def _process_segment_task(
        self,
        video_path: str,
        seg_start_time: float,
        seg_end_time: float,
        title_hint: str,
        seg_id: int,
        subtitle_items: list,
        video_process_spec,
        previous_title_hint: str = "",
        next_title_hint: str = "",
    ) -> dict:
        try:
            description_sampling = asdict(video_process_spec.description_sampling)
            caption_with_subtitles = description_sampling.get("use_subtitles", True)
            caption_spec = video_process_spec.caption_spec
            final_title = self._generate_final_title(
                video_path=video_path,
                seg_start_time=seg_start_time,
                seg_end_time=seg_end_time,
                subtitle_items=subtitle_items,
                video_process_spec=video_process_spec,
                title_hint=title_hint,
                previous_title_hint=previous_title_hint,
                next_title_hint=next_title_hint,
            )

            if caption_with_subtitles:
                _, subtitles_str_in_seg = get_subtitle_in_segment(subtitle_items, seg_start_time, seg_end_time)
            else:
                subtitles_str_in_seg = ""

            format_args = {**asdict(caption_spec), "segment_title": final_title}
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
                seg_title=final_title,
                summary=context.get("summary", ""),
                start_time=seg_start_time,
                end_time=seg_end_time,
                duration=seg_end_time - seg_start_time,
                detail=context.get("detail", ""),
            )
            save_name = self._segment_save_name(seg_id, final_title, seg_start_time, seg_end_time)
            self._write_workspace_text(Path("segments") / save_name / "README.md", video_seg.to_markdown(with_subtitles=caption_with_subtitles))
            if subtitles_str_in_seg:
                self._write_workspace_text(Path("segments") / save_name / "SUBTITLES.md", subtitles_str_in_seg)

            clip_relative_path = Path("segments") / save_name / "video_clip.mp4"
            if not self._clip_exists(clip_relative_path):
                self._extract_clip(video_path, seg_start_time, seg_end_time, clip_relative_path)

            return {
                "start_time": seg_start_time,
                "end_time": seg_end_time,
                "seg_title": final_title,
                "title_hint": title_hint,
                **context,
                "token_usage": output["response"]["usage"]["total_tokens"],
            }
        except Exception as exc:
            self._log_error("Error processing segment %s (%.2f-%.2f): %s", seg_id, seg_start_time, seg_end_time, exc)
            return {
                "start_time": seg_start_time,
                "end_time": seg_end_time,
                "seg_title": f"Error: {exc}",
                "title_hint": title_hint,
                "summary": f"Error: {exc}",
                "detail": f"Error: {exc}",
                "token_usage": 0,
            }

    def _build_segment_drafts(self, duration_int: int, boundaries, video_process_spec) -> list[SegmentDraft]:
        segments: list[SegmentDraft] = []
        seg_start_time = 0.0
        for boundary in boundaries:
            if boundary.timestamp <= seg_start_time:
                continue
            segments.append(
                SegmentDraft(
                    start_time=seg_start_time,
                    end_time=boundary.timestamp,
                    title_hint=boundary.title_hint,
                    boundary_rationale=boundary.boundary_rationale,
                    boundary_confidence=boundary.confidence,
                    evidence=list(boundary.evidence),
                )
            )
            seg_start_time = boundary.timestamp
        if duration_int > seg_start_time:
            segments.append(SegmentDraft(start_time=seg_start_time, end_time=float(duration_int)))
        postprocess_spec = video_process_spec.boundary_postprocess_spec
        segments = self.merge_short_segments(segments, postprocess_spec.merge_short_segment_below_sec)
        return self.annotate_refinement_need(segments, postprocess_spec.target_segment_length_sec)

    def _detect_boundaries(self, video_path: str, duration_int: int, subtitle_items: list, video_process_spec=None, verbose: bool = False):
        segment_spec = video_process_spec.segment_spec
        segmentation_sampling = asdict(video_process_spec.segmentation_sampling)
        detection_window_spec = video_process_spec.detection_window_spec
        postprocess_spec = video_process_spec.boundary_postprocess_spec
        chunk_size = max(60, int(detection_window_spec.chunk_size_sec))
        overlap = max(0, int(detection_window_spec.chunk_overlap_sec))
        min_confidence = float(postprocess_spec.min_boundary_confidence)
        boundaries = []
        chunk_start_time = 0
        chunk_index = 0
        while chunk_start_time < duration_int:
            core_start_time = chunk_start_time
            core_end_time = min(chunk_start_time + chunk_size, duration_int)
            window_start_time = max(0, core_start_time - overlap)
            window_end_time = min(duration_int, core_end_time + overlap)
            started_at = time.time()

            try:
                _, subtitles_str_in_seg = get_subtitle_in_segment(subtitle_items, window_start_time, window_end_time)
                user_prompt = VIDEO_SEGMENT_PROMPT["USER"].format(
                    t_start=window_start_time,
                    t_end=window_end_time,
                    core_start=core_start_time,
                    core_end=core_end_time,
                    subtitles=subtitles_str_in_seg,
                    **asdict(segment_spec),
                )
                output = self._generate_single_w_video(
                    system_prompt=VIDEO_SEGMENT_PROMPT["SYSTEM"],
                    user_prompt=user_prompt,
                    video_path=video_path,
                    start_time=window_start_time,
                    end_time=window_end_time,
                    video_sampling=segmentation_sampling,
                    generator=self.segmentor,
                )
                segmentation_info = self.parse_response(output["text"])
                revised_info = self.revise_segmentation_info(
                    segmentation_info,
                    chunk_start_time=core_start_time,
                    chunk_end_time=core_end_time,
                )
                revised_info = [item for item in revised_info if item.confidence >= min_confidence]
            except (AssertionError, Exception) as exc:
                self._log_error("[Chunk %03d] Failed to generate valid segmentation info: %s", chunk_index, exc)
                revised_info = []

            boundaries.extend(revised_info)
            if verbose:
                self._log_info(
                    "[Chunk %03d] Boundary detection completed in %.2fs | Boundaries kept: %d",
                    chunk_index,
                    time.time() - started_at,
                    len(revised_info),
                )
            chunk_start_time = core_end_time
            chunk_index += 1
        return boundaries

    def _generate_segments_and_context(self, video_path: str, duration_int: int, subtitle_items: list, verbose: bool = False, chunk_size: int = 600, video_process_spec=None):
        all_contexts = []
        futures = []
        detected_boundaries = self._detect_boundaries(
            video_path=video_path,
            duration_int=duration_int,
            subtitle_items=subtitle_items,
            video_process_spec=video_process_spec,
            verbose=verbose,
        )
        segment_drafts = self._build_segment_drafts(duration_int, detected_boundaries, video_process_spec)

        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            for seg_index, draft in enumerate(segment_drafts, start=1):
                previous_hint = segment_drafts[seg_index - 2].title_hint if seg_index > 1 else ""
                next_hint = segment_drafts[seg_index].title_hint if seg_index < len(segment_drafts) else ""
                future = executor.submit(
                    self._process_segment_task,
                    video_path=video_path,
                    seg_start_time=draft.start_time,
                    seg_end_time=draft.end_time,
                    title_hint=draft.title_hint,
                    seg_id=seg_index,
                    subtitle_items=subtitle_items,
                    video_process_spec=video_process_spec,
                    previous_title_hint=previous_hint,
                    next_title_hint=next_hint,
                )
                futures.append(future)

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
