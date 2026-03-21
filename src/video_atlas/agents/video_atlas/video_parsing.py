from __future__ import annotations

import concurrent.futures
import json
import time

from ...prompts import BOUNDARY_DETECTION_PROMPT, CONTEXT_GENERATION_PROMPT
from ...schemas import ALLOWED_EVIDENCE
from ...schemas import CandidateBoundary, CaptionedSegment, FinalizedSegment
from ...utils import get_subtitle_in_segment


class VideoParsingMixin:
    def _write_candidate_boundaries_debug(
        self,
        chunk_index: int,
        core_start_time: float,
        core_end_time: float,
        window_start_time: float,
        window_end_time: float,
        last_detection_point: float | None,
        candidate_boundaries: list[CandidateBoundary],
    ) -> None:
        payload = {
            "chunk_index": chunk_index,
            "core_start": core_start_time,
            "core_end": core_end_time,
            "window_start": window_start_time,
            "window_end": window_end_time,
            "last_detection_point": last_detection_point,
            "candidate_boundaries": [
                {
                    "timestamp": item.timestamp,
                    "boundary_rationale": item.boundary_rationale,
                    "evidence": list(item.evidence),
                    "confidence": item.confidence,
                }
                for item in candidate_boundaries
            ],
        }
        relative_path = (
            f".agentignore/boundary_debug/"
            f"chunk_{chunk_index:04d}_core_{core_start_time:.2f}_{core_end_time:.2f}.json"
        )
        self._write_workspace_text(relative_path, json.dumps(payload, indent=2, ensure_ascii=False))

    def _clamp_confidence(self, value: float, default: float = 0.0) -> float:
        try:
            numeric = float(value)
        except Exception:
            return default
        return max(0.0, min(1.0, numeric))

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

    def _genre_distribution_str(self, genre_distribution: dict[str, float]) -> str:
        genre_top = sorted(genre_distribution.items(), key=lambda item: item[1], reverse=True)
        return ", ".join([f"{key}:{value:.2f}" for key, value in genre_top])

    def _slots_weight_str(self, slots_weight: dict[str, float]) -> str:
        return ", ".join([f"{slot}:{slots_weight[slot]:.2f}" for slot in sorted(slots_weight.keys())])

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

            user_prompt = CONTEXT_GENERATION_PROMPT["USER"].format(
                genre_str=self._genre_distribution_str(execution_plan.genre_distribution),
                segmentation_profile=execution_plan.segmentation_specification.profile_name,
                signal_priority=execution_plan.segmentation_specification.profile.signal_priority,
                caption_policy=caption_spec.profile.caption_policy,
                slots_weight=self._slots_weight_str(caption_spec.profile.slots_weight),
                subtitles=subtitles_str_in_seg,
            )
            output = self._generate_single_w_video(
                system_prompt=CONTEXT_GENERATION_PROMPT["SYSTEM"],
                user_prompt=user_prompt,
                video_path=video_path,
                start_time=segment.start_time,
                end_time=segment.end_time,
                video_sampling=description_sampling,
                generator=self.captioner,
            )

            context = self.parse_response(output["text"])
            summary = context.get("summary") or f"No summary for segment {segment.start_time} to {segment.end_time}"
            detail = context.get("final_caption") or f"No detail description for segment {segment.start_time} to {segment.end_time}"

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
    ) -> list[CandidateBoundary]:
        _, subtitles_str_in_seg = get_subtitle_in_segment(subtitle_items, window_start_time, window_end_time)
        segmentation_profile = execution_plan.segmentation_specification.profile
        user_prompt = BOUNDARY_DETECTION_PROMPT["USER"].format(
            t_start=window_start_time,
            t_end=window_end_time,
            core_start=core_start_time,
            core_end=core_end_time,
            subtitles=subtitles_str_in_seg,
            segmentation_profile=execution_plan.segmentation_specification.profile_name,
            segmentation_policy=segmentation_profile.segmentation_policy,
            last_detection_point="None" if last_detection_point is None else str(last_detection_point),
        )
        output = self._generate_single_w_video(
            system_prompt=BOUNDARY_DETECTION_PROMPT["SYSTEM"],
            user_prompt=user_prompt,
            video_path=video_path,
            start_time=window_start_time,
            end_time=window_end_time,
            video_sampling=execution_plan.segmentation_specification.frame_sampling_profile,
            generator=self.segmentor,
        )
        raw_boundary_output = self.parse_response(output["text"])
        return self._check_candidate_boundaries(
            raw_boundary_output=raw_boundary_output,
            chunk_start_time=core_start_time,
            chunk_end_time=core_end_time,
            min_confidence=min_confidence,
        )

    def _refine_segment(
        self,
        video_path: str,
        subtitle_items: list,
        segment: FinalizedSegment,
        execution_plan,
    ) -> list[FinalizedSegment]:
        if not segment.refinement_needed:
            return [segment]
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
    ) -> list[FinalizedSegment]:
        finalized_segments: list[FinalizedSegment] = []
        for segment in segments:
            finalized_segments.extend(
                self._refine_segment(
                    video_path=video_path,
                    subtitle_items=subtitle_items,
                    segment=segment,
                    execution_plan=execution_plan,
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
        # NOTE: 暂时注释用于本地测试
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

    def _parse_video_into_segments(self, video_path: str, duration_int: int, subtitle_items: list, execution_plan, verbose: bool = False):
        parsed_segments = []
        caption_futures = []
        open_segment_start = 0.0
        chunk_start_time = 0.0
        next_segment_id = 1
        chunk_index = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            while chunk_start_time < duration_int:
                core_start_time = chunk_start_time
                core_end_time = min(chunk_start_time + execution_plan.chunk_size_sec, duration_int)
                window_start_time = max(0.0, core_start_time - execution_plan.chunk_overlap_sec)
                window_end_time = min(float(duration_int), core_end_time + execution_plan.chunk_overlap_sec)
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
                    )
                except Exception as exc:
                    self._log_error("[Chunk %.0f-%.0f] Failed to detect candidate boundaries: %s", core_start_time, core_end_time, exc)
                    candidate_boundaries = []

                self._write_candidate_boundaries_debug(
                    chunk_index=chunk_index,
                    core_start_time=core_start_time,
                    core_end_time=core_end_time,
                    window_start_time=window_start_time,
                    window_end_time=window_end_time,
                    last_detection_point=last_detection_point,
                    candidate_boundaries=candidate_boundaries,
                )

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

                if core_end_time >= duration_int:
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
                segment_end_time=float(duration_int),
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
        return parsed_segments
