from __future__ import annotations

import concurrent.futures
import json
import time

from ...prompts import BOUNDARY_DETECTION_PROMPT, CAPTION_GENERATION_PROMPT, TEXT_BOUNDARY_DETECTION_PROMPT
from ...schemas import ALLOWED_EVIDENCE
from ...schemas import CandidateBoundary, CaptionedSegment, FinalizedSegment
from ...utils import get_subtitle_in_segment


class VideoParsingMixin:
    def _resolve_segmentation_route(self, execution_plan, subtitle_items: list | None = None) -> str:
        subtitle_items = subtitle_items or []
        profile = execution_plan.segmentation_specification.profile
        route = getattr(profile, "segmentation_route", "multimodal_local")
        if route == "text_llm" and subtitle_items:
            return "text_llm"
        return "multimodal_local"

    def _clamp_confidence(self, value: float, default: float = 0.0) -> float:
        try:
            numeric = float(value)
        except Exception:
            return default
        return max(0.0, min(1.0, numeric))

    def _get_segmentation_chunk_settings(
        self,
        segmentation_route: str,
        execution_plan=None,
    ) -> tuple[int, int]:
        default_chunk_size = int(
            getattr(self, "chunk_size_sec", getattr(execution_plan, "chunk_size_sec", 600))
        )
        default_chunk_overlap = int(
            getattr(self, "chunk_overlap_sec", getattr(execution_plan, "chunk_overlap_sec", 20))
        )
        if segmentation_route == "text_llm":
            return (
                int(getattr(self, "text_chunk_size_sec", default_chunk_size)),
                int(getattr(self, "text_chunk_overlap_sec", default_chunk_overlap)),
            )
        return (
            int(getattr(self, "multimodal_chunk_size_sec", default_chunk_size)),
            int(getattr(self, "multimodal_chunk_overlap_sec", default_chunk_overlap)),
        )

    def _get_segmentation_generator(self, segmentation_route: str):
        if segmentation_route == "text_llm":
            generator = getattr(self, "text_segmentor", None)
            if generator is None:
                raise RuntimeError("text_segmentor is not configured for text_llm segmentation route")
            return generator
        generator = getattr(self, "multimodal_segmentor", None) or getattr(self, "segmentor", None)
        if generator is None:
            raise RuntimeError("multimodal_segmentor is not configured for multimodal_local segmentation route")
        return generator

    def _merge_short_segments(self, segments: list[FinalizedSegment], merge_below_sec: int) -> list[FinalizedSegment]:
        if merge_below_sec <= 0:
            return segments
        merged: list[FinalizedSegment] = []
        for segment in segments:
            duration = segment.end_time - segment.start_time
            if merged and duration < merge_below_sec:
                previous = merged[-1]
                merged[-1] = FinalizedSegment(
                    start_time=previous.start_time,
                    end_time=segment.end_time,
                    boundary_rationale=segment.boundary_rationale or previous.boundary_rationale,
                    boundary_confidence=max(previous.boundary_confidence, segment.boundary_confidence),
                    evidence=sorted(set(previous.evidence + segment.evidence)),
                    refinement_needed=previous.refinement_needed or segment.refinement_needed,
                )
                continue
            merged.append(segment)
        return merged

    def _mark_refinement_needed(
        self,
        segments: list[FinalizedSegment],
        target_segment_length_sec: list[int],
    ) -> list[FinalizedSegment]:
        if not target_segment_length_sec or len(target_segment_length_sec) != 2:
            return segments
        _, max_target = target_segment_length_sec
        if max_target <= 0:
            return segments
        annotated = []
        for segment in segments:
            duration = segment.end_time - segment.start_time
            annotated.append(
                FinalizedSegment(
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    boundary_rationale=segment.boundary_rationale,
                    boundary_confidence=segment.boundary_confidence,
                    evidence=list(segment.evidence),
                    refinement_needed=duration > max_target,
                )
            )
        return annotated

    def _genres_str(self, genres: list[str]) -> str:
        normalized = [genre.strip() for genre in genres if isinstance(genre, str) and genre.strip()]
        return ", ".join(normalized) if normalized else "other"

    def _truncate_prompt_subtitles(self, subtitles: str, max_chars: int) -> str:
        if max_chars <= 0 or len(subtitles) <= max_chars:
            return subtitles
        marker = "\n[TRUNCATED]"
        budget = max(0, max_chars - len(marker))
        return subtitles[:budget] + marker

    def _generate_local_caption(
        self,
        video_path: str,
        segment: FinalizedSegment,
        seg_id: int,
        subtitle_items: list,
        execution_plan,
    ) -> CaptionedSegment:
        try:
            caption_spec = execution_plan.caption_specification
            description_sampling = caption_spec.frame_sampling_profile

            if self.caption_with_subtitles:
                _, subtitles_str_in_seg = get_subtitle_in_segment(subtitle_items, segment.start_time, segment.end_time)
            else:
                subtitles_str_in_seg = ""

            system_prompt = CAPTION_GENERATION_PROMPT.render_system()
            user_prompt = CAPTION_GENERATION_PROMPT.render_user(
                genres=self._genres_str(execution_plan.genres),
                concise_description=execution_plan.concise_description,
                segmentation_profile=execution_plan.segmentation_specification.profile_name,
                signal_priority=execution_plan.segmentation_specification.profile.signal_priority,
                caption_policy=caption_spec.profile.caption_policy,
                subtitles=subtitles_str_in_seg,
            )

            output = self.captioner.generate_single(
                messages=self._build_video_messages_from_path(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    video_path=video_path,
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    video_sampling=description_sampling
                )
            )

            context = self.parse_response(output["text"])
            summary = context.get("summary") or f"No summary for segment {segment.start_time} to {segment.end_time}"
            detail = context.get("caption") or f"No detail description for segment {segment.start_time} to {segment.end_time}"

            return CaptionedSegment(
                seg_id=f"seg_{seg_id:04d}",
                start_time=segment.start_time,
                end_time=segment.end_time,
                summary=summary,
                detail=detail,
                subtitles_text=subtitles_str_in_seg,
                token_usage=output["response"]["usage"]["total_tokens"],
            )
        except Exception as exc:
            self._log_error("Error generating caption for segment %s (%.2f-%.2f): %s", seg_id, segment.start_time, segment.end_time, exc)
            return CaptionedSegment(
                seg_id=f"seg_{seg_id:04d}",
                start_time=segment.start_time,
                end_time=segment.end_time,
                summary=f"Error: {exc}",
                detail=f"Error: {exc}",
                subtitles_text="",
                token_usage=0,
            )

    def _check_candidate_boundaries(
        self,
        raw_boundary_output,
        chunk_start_time: float,
        chunk_end_time: float,
        min_confidence: float,
    ) -> list[CandidateBoundary]:
        candidate_boundaries: list[CandidateBoundary] = []
        last_boundary_time = chunk_start_time
        for raw_item in raw_boundary_output or []:
            if not isinstance(raw_item, dict):
                continue
            raw_timestamp = raw_item.get("timestamp", 0)
            try:
                boundary_time = float(raw_timestamp)
            except Exception:
                continue
            if boundary_time >= chunk_end_time or boundary_time <= chunk_start_time or boundary_time <= last_boundary_time:
                continue

            raw_evidence = raw_item.get("evidence", [])
            if not isinstance(raw_evidence, list):
                raw_evidence = []
            evidence = [value for value in raw_evidence if value in ALLOWED_EVIDENCE]
            confidence = self._clamp_confidence(raw_item.get("confidence", 0.0))
            if confidence < min_confidence:
                continue

            boundary_rationale = raw_item.get("boundary_rationale", "")
            if not isinstance(boundary_rationale, str):
                boundary_rationale = ""

            candidate_boundaries.append(
                CandidateBoundary(
                    timestamp=boundary_time,
                    boundary_rationale=boundary_rationale.strip(),
                    evidence=evidence,
                    confidence=confidence,
                )
            )
            last_boundary_time = boundary_time
        return candidate_boundaries

    def _build_raw_segments_from_candidates(
        self,
        segment_start_time: float,
        segment_end_time: float,
        candidate_boundaries: list[CandidateBoundary],
    ) -> list[FinalizedSegment]:
        segments: list[FinalizedSegment] = []
        current_start = segment_start_time
        for boundary in candidate_boundaries:
            if boundary.timestamp <= current_start or boundary.timestamp >= segment_end_time:
                continue
            segments.append(
                FinalizedSegment(
                    start_time=current_start,
                    end_time=boundary.timestamp,
                    boundary_rationale=boundary.boundary_rationale,
                    boundary_confidence=boundary.confidence,
                    evidence=list(boundary.evidence),
                )
            )
            current_start = boundary.timestamp
        if segment_end_time > current_start:
            segments.append(FinalizedSegment(start_time=current_start, end_time=segment_end_time))
        return segments

    def _postprocess_segments(
        self,
        segments: list[FinalizedSegment],
        execution_plan,
    ) -> list[FinalizedSegment]:
        min_target = execution_plan.segmentation_specification.profile.target_segment_length_sec[0]
        merge_below_sec = max(10, int(min_target * 0.5))
        merged_segments = self._merge_short_segments(segments, merge_below_sec)
        return self._mark_refinement_needed(
            merged_segments,
            list(execution_plan.segmentation_specification.profile.target_segment_length_sec),
        )

    def _detect_candidate_boundaries_for_chunk_multimodal(
        self,
        video_path: str,
        subtitle_items: list,
        execution_plan,
        core_start_time: float,
        core_end_time: float,
        window_start_time: float,
        window_end_time: float,
        last_detection_point: float | None = None,
        min_confidence: float = 0.35,
    ) -> list[CandidateBoundary]:
        _, subtitles_str_in_seg = get_subtitle_in_segment(subtitle_items, window_start_time, window_end_time)
        
        segmentation_profile = execution_plan.segmentation_specification.profile
        system_prompt = BOUNDARY_DETECTION_PROMPT.render_system()
        user_prompt = BOUNDARY_DETECTION_PROMPT.render_user(
            t_start=window_start_time,
            t_end=window_end_time,
            core_start=core_start_time,
            core_end=core_end_time,
            subtitles=subtitles_str_in_seg,
            concise_description=execution_plan.concise_description,
            segmentation_profile=execution_plan.segmentation_specification.profile_name,
            segmentation_policy=segmentation_profile.segmentation_policy,
            last_detection_point="None" if last_detection_point is None else str(last_detection_point),
        )

        output = self._get_segmentation_generator("multimodal_local").generate_single(
            messages=self._build_video_messages_from_path(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                video_path=video_path,
                start_time=window_start_time,
                end_time=window_end_time,
                video_sampling=execution_plan.segmentation_specification.frame_sampling_profile,
            )
        )
        
        raw_boundary_output = self.parse_response(output["text"])
        return self._check_candidate_boundaries(
            raw_boundary_output=raw_boundary_output,
            chunk_start_time=core_start_time,
            chunk_end_time=core_end_time,
            min_confidence=min_confidence,
        )

    def _detect_candidate_boundaries_for_chunk_text(
        self,
        subtitle_items: list,
        execution_plan,
        core_start_time: float,
        core_end_time: float,
        window_start_time: float,
        window_end_time: float,
        last_detection_point: float | None = None,
        min_confidence: float = 0.35,
    ) -> list[CandidateBoundary]:
        _, subtitles_str_in_seg = get_subtitle_in_segment(subtitle_items, window_start_time, window_end_time)
        segmentation_profile = execution_plan.segmentation_specification.profile
        system_prompt = TEXT_BOUNDARY_DETECTION_PROMPT.render_system()
        user_prompt = TEXT_BOUNDARY_DETECTION_PROMPT.render_user(
            subtitles=subtitles_str_in_seg,
            core_start=core_start_time,
            core_end=core_end_time,
            concise_description=execution_plan.concise_description,
            segmentation_profile=execution_plan.segmentation_specification.profile_name,
            segmentation_policy=segmentation_profile.segmentation_policy,
            last_detection_point="None" if last_detection_point is None else str(last_detection_point),
        )

        output = self._get_segmentation_generator("text_llm").generate_single(
            messages=self._prepare_messages(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        )
        raw_boundary_output = self.parse_response(output["text"])
        return self._check_candidate_boundaries(
            raw_boundary_output=raw_boundary_output,
            chunk_start_time=core_start_time,
            chunk_end_time=core_end_time,
            min_confidence=min_confidence,
        )

    def _detect_candidate_boundaries_for_chunk(
        self,
        video_path: str,
        subtitle_items: list,
        execution_plan,
        core_start_time: float,
        core_end_time: float,
        window_start_time: float,
        window_end_time: float,
        last_detection_point: float | None = None,
        min_confidence: float = 0.35,
        segmentation_route: str = "multimodal_local",
    ) -> list[CandidateBoundary]:
        if segmentation_route == "text_llm":
            return self._detect_candidate_boundaries_for_chunk_text(
                subtitle_items=subtitle_items,
                execution_plan=execution_plan,
                core_start_time=core_start_time,
                core_end_time=core_end_time,
                window_start_time=window_start_time,
                window_end_time=window_end_time,
                last_detection_point=last_detection_point,
                min_confidence=min_confidence,
            )
        return self._detect_candidate_boundaries_for_chunk_multimodal(
            video_path=video_path,
            subtitle_items=subtitle_items,
            execution_plan=execution_plan,
            core_start_time=core_start_time,
            core_end_time=core_end_time,
            window_start_time=window_start_time,
            window_end_time=window_end_time,
            last_detection_point=last_detection_point,
            min_confidence=min_confidence,
        )

    def _refine_segment(
        self,
        video_path: str,
        subtitle_items: list,
        segment: FinalizedSegment,
        execution_plan,
        segmentation_route: str | None = None,
    ) -> list[FinalizedSegment]:
        if not segment.refinement_needed:
            return [segment]
        resolved_route = segmentation_route or self._resolve_segmentation_route(execution_plan, subtitle_items=subtitle_items)
        try:
            refined_boundaries = self._detect_candidate_boundaries_for_chunk(
                video_path=video_path,
                subtitle_items=subtitle_items,
                execution_plan=execution_plan,
                core_start_time=segment.start_time,
                core_end_time=segment.end_time,
                window_start_time=segment.start_time,
                window_end_time=segment.end_time,
                min_confidence=0.35,
                segmentation_route=resolved_route,
            )
        except Exception as exc:
            self._log_error("Refine failed for segment %.2f-%.2f: %s", segment.start_time, segment.end_time, exc)
            return [segment]
        if not refined_boundaries:
            return [segment]
        refined_segments = self._build_raw_segments_from_candidates(
            segment_start_time=segment.start_time,
            segment_end_time=segment.end_time,
            candidate_boundaries=refined_boundaries,
        )
        refined_segments = self._postprocess_segments(refined_segments, execution_plan)
        for item in refined_segments:
            item.refinement_needed = False
        return refined_segments or [segment]

    def _refine_segments(
        self,
        video_path: str,
        subtitle_items: list,
        segments: list[FinalizedSegment],
        execution_plan,
        segmentation_route: str | None = None,
    ) -> list[FinalizedSegment]:
        finalized_segments: list[FinalizedSegment] = []
        for segment in segments:
            finalized_segments.extend(
                self._refine_segment(
                    video_path=video_path,
                    subtitle_items=subtitle_items,
                    segment=segment,
                    execution_plan=execution_plan,
                    segmentation_route=segmentation_route,
                )
            )
        return finalized_segments

    def _materialize_committed_segments(
        self,
        video_path: str,
        subtitle_items: list,
        execution_plan,
        open_segment_start: float,
        candidate_boundaries: list[CandidateBoundary],
        segment_end_time: float | None = None,
    ) -> tuple[list[FinalizedSegment], float]:
        committed_end = candidate_boundaries[-1].timestamp if candidate_boundaries else segment_end_time
        if committed_end is None or committed_end <= open_segment_start:
            return [], open_segment_start

        committed_segments = self._build_raw_segments_from_candidates(
            segment_start_time=open_segment_start,
            segment_end_time=committed_end,
            candidate_boundaries=candidate_boundaries,
        )
        # NOTE: 后处理功能还需要优化，暂时不使用
        # committed_segments = self._postprocess_segments(committed_segments, execution_plan)
        # committed_segments = self._refine_segments(
        #     video_path=video_path,
        #     subtitle_items=subtitle_items,
        #     segments=committed_segments,
        #     execution_plan=execution_plan,
        # )
        return committed_segments, committed_end

    def _submit_caption_tasks(
        self,
        executor,
        caption_futures: list,
        segments: list[FinalizedSegment],
        video_path: str,
        subtitle_items: list,
        execution_plan,
        next_segment_id: int,
    ) -> int:
        for segment in segments:
            future = executor.submit(
                self._generate_local_caption,
                video_path=video_path,
                segment=segment,
                seg_id=next_segment_id,
                subtitle_items=subtitle_items,
                execution_plan=execution_plan,
            )
            caption_futures.append(future)
            next_segment_id += 1
        return next_segment_id

    def _parse_video_into_segments(self, video_path: str, duration: float, subtitle_items: list, execution_plan, verbose: bool = False):
        parsed_segments = []
        caption_futures = []
        record_generated_boundaries = []
        open_segment_start = 0.0
        chunk_start_time = 0.0
        next_segment_id = 1
        chunk_index = 0
        segmentation_route = self._resolve_segmentation_route(execution_plan, subtitle_items=subtitle_items)
        chunk_size_sec, chunk_overlap_sec = self._get_segmentation_chunk_settings(
            segmentation_route,
            execution_plan=execution_plan,
        )

        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            while chunk_start_time < duration:
                core_start_time = chunk_start_time
                core_end_time = min(chunk_start_time + chunk_size_sec, duration)
                window_start_time = max(0.0, core_start_time - chunk_overlap_sec)
                window_end_time = min(float(duration), core_end_time + chunk_overlap_sec)
                started_at = time.time()
                last_detection_point = open_segment_start

                try:
                    candidate_boundaries = self._detect_candidate_boundaries_for_chunk(
                        video_path=video_path,
                        subtitle_items=subtitle_items,
                        execution_plan=execution_plan,
                        core_start_time=core_start_time,
                        core_end_time=core_end_time,
                        window_start_time=window_start_time,
                        window_end_time=window_end_time,
                        last_detection_point=last_detection_point,
                        segmentation_route=segmentation_route,
                    )
                except Exception as exc:
                    self._log_error("[Chunk %.0f-%.0f] Failed to detect candidate boundaries: %s", core_start_time, core_end_time, exc)
                    candidate_boundaries = []

                record_generated_boundaries.append({
                    'chunk_index': chunk_index,
                    'core_start_time': core_start_time,
                    'core_end_time': core_end_time,
                    'window_start_time': window_start_time,
                    'window_end_time': window_end_time,
                    'last_detection_point': last_detection_point,
                    'candidate_boundaries': candidate_boundaries,
                })

                committed_segments, open_segment_start = self._materialize_committed_segments(
                    video_path=video_path,
                    subtitle_items=subtitle_items,
                    execution_plan=execution_plan,
                    open_segment_start=open_segment_start,
                    candidate_boundaries=candidate_boundaries,
                )

                if committed_segments:
                    next_segment_id = self._submit_caption_tasks(
                        executor=executor,
                        caption_futures=caption_futures,
                        segments=committed_segments,
                        video_path=video_path,
                        subtitle_items=subtitle_items,
                        execution_plan=execution_plan,
                        next_segment_id=next_segment_id,
                    )

                if verbose:
                    self._log_info(
                        "[Chunk %.0f-%.0f] Candidate boundary detection completed in %.2fs | Boundaries kept: %d",
                        core_start_time,
                        core_end_time,
                        time.time() - started_at,
                        len(candidate_boundaries),
                    )

                if core_end_time >= duration:
                    break

                next_chunk_start = candidate_boundaries[-1].timestamp if candidate_boundaries else core_end_time
                chunk_start_time = next_chunk_start if next_chunk_start > chunk_start_time else core_end_time
                chunk_index += 1

            tail_segments, open_segment_start = self._materialize_committed_segments(
                video_path=video_path,
                subtitle_items=subtitle_items,
                execution_plan=execution_plan,
                open_segment_start=open_segment_start,
                candidate_boundaries=[],
                segment_end_time=float(duration),
            )
            next_segment_id = self._submit_caption_tasks(
                executor=executor,
                caption_futures=caption_futures,
                segments=tail_segments,
                video_path=video_path,
                subtitle_items=subtitle_items,
                execution_plan=execution_plan,
                next_segment_id=next_segment_id,
            )

            for future in concurrent.futures.as_completed(caption_futures):
                try:
                    caption_object = future.result()
                    parsed_segments.append(
                        {
                            "seg_id": caption_object.seg_id,
                            "start_time": caption_object.start_time,
                            "end_time": caption_object.end_time,
                            "summary": caption_object.summary,
                            "detail": caption_object.detail,
                            "subtitles_text": caption_object.subtitles_text,
                            "token_usage": caption_object.token_usage,
                        }
                    )
                except Exception as exc:
                    self._log_error("Segment processing failed: %s", exc)

        parsed_segments.sort(key=lambda item: item["start_time"])
        return parsed_segments, record_generated_boundaries
