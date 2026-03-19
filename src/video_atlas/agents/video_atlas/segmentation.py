from __future__ import annotations

import concurrent.futures
import time
from pathlib import Path

from ...prompts import CONTEXT_GENERATION_PROMPT, TITLE_GENERATION_PROMPT, VIDEO_GLOBAL_PROMPT, VIDEO_SEGMENT_PROMPT
from ...schemas import ALLOWED_EVIDENCE
from ...schemas import CandidateBoundary, CaptionedSegment, FinalizedSegment, VideoGlobal, VideoSeg
from ...utils import get_subtitle_in_segment


class SegmentationMixin:
    def _segmentation_profile(self, execution_plan):
        return execution_plan.segmentation_specification.profile

    def _segmentation_policy_text(self, execution_plan) -> str:
        profile = self._segmentation_profile(execution_plan)
        policy_notes = (execution_plan.segmentation_specification.policy_notes or "").strip()
        if policy_notes:
            return f"{profile.segmentation_policy} Additional video-specific guidance: {policy_notes}"
        return profile.segmentation_policy

    def _clamp_confidence(self, value: float, default: float = 0.0) -> float:
        try:
            numeric = float(value)
        except Exception:
            return default
        return max(0.0, min(1.0, numeric))

    def revise_segmentation_info(self, segmentation_info, chunk_start_time=0, chunk_end_time=float("inf")):
        revised_info: list[CandidateBoundary] = []
        last_break = chunk_start_time
        for item in segmentation_info or []:
            if not isinstance(item, dict):
                continue
            break_timepoint = item.get("timestamp", 0)
            try:
                break_timepoint = float(break_timepoint)
            except Exception:
                continue
            if break_timepoint >= chunk_end_time or break_timepoint <= chunk_start_time or break_timepoint <= last_break:
                continue
            evidence = item.get("evidence", [])
            if not isinstance(evidence, list):
                evidence = []
            evidence = [value for value in evidence if value in ALLOWED_EVIDENCE]
            confidence = self._clamp_confidence(item.get("confidence", 0.0))
            title_hint = item.get("title_hint", item.get("segment_title", ""))
            if not isinstance(title_hint, str):
                title_hint = ""
            rationale = item.get("boundary_rationale", "")
            if not isinstance(rationale, str):
                rationale = ""
            revised_info.append(
                CandidateBoundary(
                    timestamp=break_timepoint,
                    boundary_rationale=rationale.strip(),
                    evidence=evidence,
                    confidence=confidence,
                    title_hint=title_hint.strip(),
                )
            )
            last_break = break_timepoint
        return revised_info

    def merge_short_segments(self, segments: list[FinalizedSegment], merge_below_sec: int) -> list[FinalizedSegment]:
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
                    title_hint=previous.title_hint or segment.title_hint,
                    boundary_rationale=segment.boundary_rationale or previous.boundary_rationale,
                    boundary_confidence=max(previous.boundary_confidence, segment.boundary_confidence),
                    evidence=sorted(set(previous.evidence + segment.evidence)),
                    refinement_needed=previous.refinement_needed or segment.refinement_needed,
                )
                continue
            merged.append(segment)
        return merged

    def annotate_refinement_need(self, segments: list[FinalizedSegment], target_segment_length_sec: list[int]) -> list[FinalizedSegment]:
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
                    title_hint=segment.title_hint,
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

    def _generate_final_title(
        self,
        video_path: str,
        seg_start_time: float,
        seg_end_time: float,
        subtitle_items: list,
        execution_plan,
        title_hint: str = "",
        previous_title_hint: str = "",
        next_title_hint: str = "",
    ) -> str:
        _, subtitles_str_in_seg = get_subtitle_in_segment(subtitle_items, seg_start_time, seg_end_time)
        profile = self._segmentation_profile(execution_plan)
        user_prompt = TITLE_GENERATION_PROMPT["USER"].format(
            start_time=seg_start_time,
            end_time=seg_end_time,
            title_hint=title_hint,
            previous_title_hint=previous_title_hint,
            next_title_hint=next_title_hint,
            subtitles=subtitles_str_in_seg,
            genre_str=self._genre_distribution_str(execution_plan.genre_distribution),
            segmentation_profile=execution_plan.segmentation_specification.profile_name,
            title_policy=profile.title_policy,
            notes="",
        )
        output = self._generate_single_w_video(
            system_prompt=TITLE_GENERATION_PROMPT["SYSTEM"],
            user_prompt=user_prompt,
            video_path=video_path,
            start_time=seg_start_time,
            end_time=seg_end_time,
            video_sampling={
                "fps": execution_plan.caption_specification.frame_sampling_profile.fps,
                "max_resolution": execution_plan.caption_specification.frame_sampling_profile.max_resolution,
                "use_subtitles": execution_plan.caption_specification.frame_sampling_profile.use_subtitles,
            },
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
        segment: FinalizedSegment,
        seg_id: int,
        subtitle_items: list,
        execution_plan,
        previous_title_hint: str = "",
        next_title_hint: str = "",
    ) -> CaptionedSegment:
        try:
            caption_spec = execution_plan.caption_specification
            description_sampling = {
                "fps": caption_spec.frame_sampling_profile.fps,
                "max_resolution": caption_spec.frame_sampling_profile.max_resolution,
                "use_subtitles": caption_spec.frame_sampling_profile.use_subtitles,
            }
            caption_with_subtitles = caption_spec.frame_sampling_profile.use_subtitles
            final_title = self._generate_final_title(
                video_path=video_path,
                seg_start_time=segment.start_time,
                seg_end_time=segment.end_time,
                subtitle_items=subtitle_items,
                execution_plan=execution_plan,
                title_hint=segment.title_hint,
                previous_title_hint=previous_title_hint,
                next_title_hint=next_title_hint,
            )

            if caption_with_subtitles:
                _, subtitles_str_in_seg = get_subtitle_in_segment(subtitle_items, segment.start_time, segment.end_time)
            else:
                subtitles_str_in_seg = ""

            user_prompt = CONTEXT_GENERATION_PROMPT["USER"].format(
                segment_title=final_title,
                genre_str=self._genre_distribution_str(execution_plan.genre_distribution),
                segmentation_profile=execution_plan.segmentation_specification.profile_name,
                signal_priority=execution_plan.segmentation_specification.profile.signal_priority,
                caption_policy=caption_spec.profile.caption_policy,
                slots_weight=self._slots_weight_str(caption_spec.profile.slots_weight),
                notes=caption_spec.notes,
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

            video_seg = VideoSeg(
                seg_id=f"seg_{seg_id:04d}",
                seg_title=final_title,
                summary=summary,
                start_time=segment.start_time,
                end_time=segment.end_time,
                duration=segment.end_time - segment.start_time,
                detail=detail,
            )
            save_name = self._segment_save_name(seg_id, final_title, segment.start_time, segment.end_time)
            self._write_workspace_text(Path("segments") / save_name / "README.md", video_seg.to_markdown(with_subtitles=caption_with_subtitles))
            if subtitles_str_in_seg:
                self._write_workspace_text(Path("segments") / save_name / "SUBTITLES.md", subtitles_str_in_seg)

            clip_relative_path = Path("segments") / save_name / "video_clip.mp4"
            if not self._clip_exists(clip_relative_path):
                self._extract_clip(video_path, segment.start_time, segment.end_time, clip_relative_path)

            return CaptionedSegment(
                start_time=segment.start_time,
                end_time=segment.end_time,
                seg_title=final_title,
                title_hint=segment.title_hint,
                summary=summary,
                detail=detail,
                token_usage=output["response"]["usage"]["total_tokens"],
            )
        except Exception as exc:
            self._log_error("Error processing segment %s (%.2f-%.2f): %s", seg_id, segment.start_time, segment.end_time, exc)
            return CaptionedSegment(
                start_time=segment.start_time,
                end_time=segment.end_time,
                seg_title=f"Error: {exc}",
                title_hint=segment.title_hint,
                summary=f"Error: {exc}",
                detail=f"Error: {exc}",
                token_usage=0,
            )

    def _check_candidate_boundaries(
        self,
        segmentation_info,
        chunk_start_time: float,
        chunk_end_time: float,
        min_confidence: float,
    ) -> list[CandidateBoundary]:
        revised_info = self.revise_segmentation_info(
            segmentation_info,
            chunk_start_time=chunk_start_time,
            chunk_end_time=chunk_end_time,
        )
        return [item for item in revised_info if item.confidence >= min_confidence]

    def _update_chunk_start(self, core_end_time: float, candidate_boundaries: list[CandidateBoundary]) -> float:
        if candidate_boundaries:
            return candidate_boundaries[-1].timestamp
        return core_end_time

    def _build_segments_from_candidates(
        self,
        segment_start_time: float,
        segment_end_time: float,
        candidate_boundaries: list[CandidateBoundary],
        execution_plan,
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
                    title_hint=boundary.title_hint,
                    boundary_rationale=boundary.boundary_rationale,
                    boundary_confidence=boundary.confidence,
                    evidence=list(boundary.evidence),
                )
            )
            current_start = boundary.timestamp
        if segment_end_time > current_start:
            segments.append(FinalizedSegment(start_time=current_start, end_time=segment_end_time))

        min_target = execution_plan.segmentation_specification.profile.target_segment_length_sec[0]
        merge_below_sec = max(10, int(min_target * 0.5))
        segments = self.merge_short_segments(segments, merge_below_sec)
        return self.annotate_refinement_need(segments, list(execution_plan.segmentation_specification.profile.target_segment_length_sec))

    def _detect_candidate_boundaries_for_chunk(
        self,
        video_path: str,
        subtitle_items: list,
        execution_plan,
        core_start_time: float,
        core_end_time: float,
        window_start_time: float,
        window_end_time: float,
        min_confidence: float = 0.35,
    ) -> list[CandidateBoundary]:
        _, subtitles_str_in_seg = get_subtitle_in_segment(subtitle_items, window_start_time, window_end_time)
        profile = self._segmentation_profile(execution_plan)
        user_prompt = VIDEO_SEGMENT_PROMPT["USER"].format(
            t_start=window_start_time,
            t_end=window_end_time,
            core_start=core_start_time,
            core_end=core_end_time,
            subtitles=subtitles_str_in_seg,
            segmentation_profile=execution_plan.segmentation_specification.profile_name,
            signal_priority=profile.signal_priority,
            boundary_evidence_primary=", ".join(profile.boundary_evidence_primary),
            boundary_evidence_secondary=", ".join(profile.boundary_evidence_secondary),
            segmentation_policy=self._segmentation_policy_text(execution_plan),
        )
        output = self._generate_single_w_video(
            system_prompt=VIDEO_SEGMENT_PROMPT["SYSTEM"],
            user_prompt=user_prompt,
            video_path=video_path,
            start_time=window_start_time,
            end_time=window_end_time,
            video_sampling={
                "fps": execution_plan.segmentation_specification.frame_sampling_profile.fps,
                "max_resolution": execution_plan.segmentation_specification.frame_sampling_profile.max_resolution,
                "use_subtitles": execution_plan.segmentation_specification.frame_sampling_profile.use_subtitles,
            },
            generator=self.segmentor,
        )
        segmentation_info = self.parse_response(output["text"])
        return self._check_candidate_boundaries(
            segmentation_info=segmentation_info,
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
        refined_segments = self._build_segments_from_candidates(
            segment_start_time=segment.start_time,
            segment_end_time=segment.end_time,
            candidate_boundaries=refined_boundaries,
            execution_plan=execution_plan,
        )
        for item in refined_segments:
            item.refinement_needed = False
        return refined_segments or [segment]

    def _merge_and_refine_segments(
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
        for index, segment in enumerate(segments):
            previous_hint = segments[index - 1].title_hint if index > 0 else ""
            next_hint = segments[index + 1].title_hint if index + 1 < len(segments) else ""
            future = executor.submit(
                self._process_segment_task,
                video_path=video_path,
                segment=segment,
                seg_id=next_segment_id,
                subtitle_items=subtitle_items,
                execution_plan=execution_plan,
                previous_title_hint=previous_hint,
                next_title_hint=next_hint,
            )
            caption_futures.append(future)
            next_segment_id += 1
        return next_segment_id

    def _generate_local_atlas(self, video_path: str, duration_int: int, subtitle_items: list, execution_plan, verbose: bool = False):
        all_contexts = []
        caption_futures = []
        pending_boundaries: list[CandidateBoundary] = []
        pending_segment_start = 0.0
        chunk_start_time = 0.0
        next_segment_id = 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            while chunk_start_time < duration_int:
                core_start_time = chunk_start_time
                core_end_time = min(chunk_start_time + execution_plan.chunk_size_sec, duration_int)
                window_start_time = max(0.0, core_start_time - execution_plan.chunk_overlap_sec)
                window_end_time = min(float(duration_int), core_end_time + execution_plan.chunk_overlap_sec)
                started_at = time.time()

                try:
                    candidate_boundaries = self._detect_candidate_boundaries_for_chunk(
                        video_path=video_path,
                        subtitle_items=subtitle_items,
                        execution_plan=execution_plan,
                        core_start_time=core_start_time,
                        core_end_time=core_end_time,
                        window_start_time=window_start_time,
                        window_end_time=window_end_time,
                    )
                except Exception as exc:
                    self._log_error("[Chunk %.0f-%.0f] Failed to detect candidate boundaries: %s", core_start_time, core_end_time, exc)
                    candidate_boundaries = []

                pending_boundaries.extend(candidate_boundaries)
                committed_end = candidate_boundaries[-1].timestamp if candidate_boundaries else None

                if committed_end is not None and committed_end > pending_segment_start:
                    committed_boundaries = [item for item in pending_boundaries if item.timestamp <= committed_end]
                    pending_boundaries = [item for item in pending_boundaries if item.timestamp > committed_end]
                    segments = self._build_segments_from_candidates(
                        segment_start_time=pending_segment_start,
                        segment_end_time=committed_end,
                        candidate_boundaries=committed_boundaries,
                        execution_plan=execution_plan,
                    )
                    segments = self._merge_and_refine_segments(
                        video_path=video_path,
                        subtitle_items=subtitle_items,
                        segments=segments,
                        execution_plan=execution_plan,
                    )
                    next_segment_id = self._submit_caption_tasks(
                        executor=executor,
                        caption_futures=caption_futures,
                        segments=segments,
                        video_path=video_path,
                        subtitle_items=subtitle_items,
                        execution_plan=execution_plan,
                        next_segment_id=next_segment_id,
                    )
                    pending_segment_start = committed_end

                if verbose:
                    self._log_info(
                        "[Chunk %.0f-%.0f] Candidate boundary detection completed in %.2fs | Boundaries kept: %d",
                        core_start_time,
                        core_end_time,
                        time.time() - started_at,
                        len(candidate_boundaries),
                    )

                next_chunk_start = self._update_chunk_start(core_end_time, candidate_boundaries)
                chunk_start_time = next_chunk_start if next_chunk_start > chunk_start_time else core_end_time

            tail_segments = self._build_segments_from_candidates(
                segment_start_time=pending_segment_start,
                segment_end_time=float(duration_int),
                candidate_boundaries=pending_boundaries,
                execution_plan=execution_plan,
            )
            tail_segments = self._merge_and_refine_segments(
                video_path=video_path,
                subtitle_items=subtitle_items,
                segments=tail_segments,
                execution_plan=execution_plan,
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
                    all_contexts.append(
                        {
                            "start_time": caption_object.start_time,
                            "end_time": caption_object.end_time,
                            "seg_title": caption_object.seg_title,
                            "title_hint": caption_object.title_hint,
                            "summary": caption_object.summary,
                            "detail": caption_object.detail,
                            "token_usage": caption_object.token_usage,
                        }
                    )
                except Exception as exc:
                    self._log_error("Segment processing failed: %s", exc)

        all_contexts.sort(key=lambda item: item["start_time"])
        return all_contexts

    def _generate_segments_and_context(self, video_path: str, duration_int: int, subtitle_items: list, verbose: bool = False, execution_plan=None):
        return self._generate_local_atlas(
            video_path=video_path,
            duration_int=duration_int,
            subtitle_items=subtitle_items,
            execution_plan=execution_plan,
            verbose=verbose,
        )

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
