from __future__ import annotations

import copy
from typing import Any

from ...schemas import (
    ALLOWED_EVIDENCE,
    ALLOWED_GENRES,
    ALLOWED_SIGNAL_PRIORITIES,
    BoundaryCandidate,
    BoundaryPostProcessSpec,
    CaptionSpec,
    DEFAULT_STRATEGY_PACKAGE,
    DESCRIPTION_SLOTS,
    DetectionWindowSpec,
    SamplingConfig,
    SegmentDraft,
    SegmentSpec,
    TitleSpec,
    VideoProcessSpec,
)
from ...schemas.segmentation_profiles import resolve_sampling_profile, resolve_segmentation_profile


class StrategyBuilderMixin:
    def check_segmentation_info(self, segmentation_info, chunk_start_time=0, chunk_end_time=float("inf")):
        assert type(segmentation_info) == list and len(segmentation_info) > 0, f"empty segmentation_info: {segmentation_info}"
        last_break = chunk_start_time
        for item in segmentation_info:
            assert type(item) == dict, f"segment item is not dict: {item}"
            break_timepoint = item.get("timestamp", 0)
            assert break_timepoint >= chunk_start_time, f"break_timepoint {break_timepoint} is not in chunk [{chunk_start_time}, {chunk_end_time}]"
            assert break_timepoint < chunk_end_time, f"break_timepoint {break_timepoint} is not in chunk [{chunk_start_time}, {chunk_end_time}]"
            assert break_timepoint > last_break, f"break_timepoint {break_timepoint} is not after the last timepoint {last_break}"
            last_break = break_timepoint

    def revise_segmentation_info(self, segmentation_info, chunk_start_time=0, chunk_end_time=float("inf")):
        revised_info: list[BoundaryCandidate] = []
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
            confidence = self._clamp(item.get("confidence", 0.0), 0.0, 1.0)
            title_hint = item.get("title_hint", item.get("segment_title", ""))
            if not isinstance(title_hint, str):
                title_hint = ""
            rationale = item.get("boundary_rationale", "")
            if not isinstance(rationale, str):
                rationale = ""
            revised_info.append(
                BoundaryCandidate(
                    timestamp=break_timepoint,
                    boundary_rationale=rationale.strip(),
                    evidence=evidence,
                    confidence=confidence,
                    title_hint=title_hint.strip(),
                )
            )
            last_break = break_timepoint
        return revised_info

    def merge_short_segments(self, segments: list[SegmentDraft], merge_below_sec: int) -> list[SegmentDraft]:
        if merge_below_sec <= 0:
            return segments
        merged: list[SegmentDraft] = []
        for segment in segments:
            duration = segment.end_time - segment.start_time
            if merged and duration < merge_below_sec:
                previous = merged[-1]
                merged[-1] = SegmentDraft(
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

    def annotate_refinement_need(self, segments: list[SegmentDraft], target_segment_length_sec: list[int]) -> list[SegmentDraft]:
        if not target_segment_length_sec or len(target_segment_length_sec) != 2:
            return segments
        _, max_target = target_segment_length_sec
        if max_target <= 0:
            return segments
        annotated = []
        for segment in segments:
            duration = segment.end_time - segment.start_time
            annotated.append(
                SegmentDraft(
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

    def check_probe_result(self, probe_result):
        assert type(probe_result) == dict, f"probe_result is not dict: {probe_result}"
        assert "genre_distribution" in probe_result and type(probe_result["genre_distribution"]) == dict, f"correct genre_distribution not in probe_result: {probe_result}"
        assert "segmentation_profile" in probe_result, f"segmentation_profile not in probe_result: {probe_result}"
        assert "segmentation" in probe_result, f"segmentation not in probe_result: {probe_result}"
        assert "title" in probe_result, f"title not in probe_result: {probe_result}"
        assert "description" in probe_result, f"description not in probe_result: {probe_result}"

    def _clamp(self, x: float, lo: float, hi: float) -> float:
        try:
            x = float(x)
        except Exception:
            return lo
        return max(lo, min(hi, x))

    def _as_bool(self, x: Any, default: bool = True) -> bool:
        if isinstance(x, bool):
            return x
        if isinstance(x, (int, float)):
            return bool(x)
        if isinstance(x, str):
            value = x.strip().lower()
            if value in {"true", "1", "yes", "y"}:
                return True
            if value in {"false", "0", "no", "n"}:
                return False
        return default

    def _normalize_dist(self, value: dict[str, Any], allowed: set[str], fallback_key: str = "other", topk: int = 2) -> dict[str, float]:
        if not isinstance(value, dict):
            return {fallback_key: 1.0}

        items: list[tuple[str, float]] = []
        for key, raw_weight in value.items():
            if key in allowed:
                weight = float(raw_weight) if isinstance(raw_weight, (int, float)) else 0.0
                if weight > 0:
                    items.append((key, weight))

        if not items:
            return {fallback_key: 1.0}

        items.sort(key=lambda item: item[1], reverse=True)
        items = items[: max(1, min(topk, len(items)))]
        total = sum(weight for _, weight in items)
        if total <= 0:
            return {fallback_key: 1.0}
        return {key: weight / total for key, weight in items}

    def _normalize_weights(self, value: dict[str, Any], keys: list[str]) -> dict[str, float]:
        normalized = {}
        total = 0.0
        for key in keys:
            raw_value = value.get(key, 0.0) if isinstance(value, dict) else 0.0
            weight = float(raw_value) if isinstance(raw_value, (int, float)) else 0.0
            weight = max(0.0, weight)
            normalized[key] = weight
            total += weight

        if total <= 0:
            uniform = 1.0 / len(keys)
            return {key: uniform for key in keys}
        return {key: normalized[key] / total for key in keys}

    def _merge_defaults(self, user_strategy: dict[str, Any], default_strategy: dict[str, Any]) -> dict[str, Any]:
        merged = copy.deepcopy(default_strategy)

        def rec(dst: dict[str, Any], src: dict[str, Any]):
            for key, value in (src or {}).items():
                if isinstance(value, dict) and isinstance(dst.get(key), dict):
                    rec(dst[key], value)
                else:
                    dst[key] = value

        if isinstance(user_strategy, dict):
            rec(merged, user_strategy)
        return merged

    def _merge_policy_text(self, base_text: str, override_text: str) -> str:
        base = (base_text or "").strip()
        override = (override_text or "").strip()
        if base and override:
            return f"{base} Additional video-specific guidance: {override}"
        return override or base

    def _build_spec_from_strategy_pkg(self, strategy_pkg: dict[str, Any]) -> VideoProcessSpec:
        strategy = self._merge_defaults(strategy_pkg, DEFAULT_STRATEGY_PACKAGE)
        strategy["planner_confidence"] = self._clamp(strategy.get("planner_confidence", 0.25), 0.0, 1.0)
        strategy["genre_distribution"] = self._normalize_dist(
            strategy.get("genre_distribution", {}),
            allowed=ALLOWED_GENRES,
            fallback_key="other",
            topk=2,
        )

        profile_name, profile = resolve_segmentation_profile(str(strategy.get("segmentation_profile", "")).strip())
        strategy["segmentation_profile"] = profile_name

        segmentation = strategy.get("segmentation", {})
        t0, t1 = profile.target_segment_length_sec
        seg_sampling_profile_name, seg_sampling_profile = resolve_sampling_profile(
            str(segmentation.get("sampling_profile", "")).strip(),
            profile.segmentation_sampling_profile,
        )
        seg_fps = self._clamp(seg_sampling_profile.get("fps", 0.5), 0.05, 4.0)
        seg_res = int(max(128, min(1536, int(seg_sampling_profile.get("max_resolution", 384)))))
        seg_use_subtitles = self._as_bool(segmentation.get("use_subtitles", True), default=True)
        policy_notes = segmentation.get("policy_notes", "")
        if not isinstance(policy_notes, str):
            policy_notes = ""
        strategy["segmentation"] = {
            "sampling_profile": seg_sampling_profile_name,
            "sampling": {"fps": seg_fps, "max_resolution": seg_res, "use_subtitles": seg_use_subtitles},
            "policy_notes": policy_notes.strip(),
        }

        title = strategy.get("title", {})
        title_notes = title.get("notes", "")
        if not isinstance(title_notes, str) or not title_notes.strip():
            title_notes = DEFAULT_STRATEGY_PACKAGE["title"]["notes"]
        strategy["title"] = {"notes": title_notes.strip()}

        description = strategy.get("description", {})
        slot_weights = self._normalize_weights(description.get("slots_weight", {}), DESCRIPTION_SLOTS)
        desc_sampling_profile_name, desc_sampling_profile = resolve_sampling_profile(
            str(description.get("sampling_profile", "")).strip(),
            profile.description_sampling_profile,
        )
        desc_fps = self._clamp(desc_sampling_profile.get("fps", 0.2), 0.05, 4.0)
        desc_res = int(max(128, min(1536, int(desc_sampling_profile.get("max_resolution", 384)))))
        desc_use_subtitles = self._as_bool(description.get("use_subtitles", True), default=True)
        desc_notes = description.get("notes", "")
        if not isinstance(desc_notes, str) or not desc_notes.strip():
            desc_notes = DEFAULT_STRATEGY_PACKAGE["description"]["notes"]
        strategy["description"] = {
            "slots_weight": slot_weights,
            "sampling_profile": desc_sampling_profile_name,
            "sampling": {"fps": desc_fps, "max_resolution": desc_res, "use_subtitles": desc_use_subtitles},
            "notes": desc_notes.strip(),
        }

        genre_top = sorted(strategy["genre_distribution"].items(), key=lambda item: item[1], reverse=True)
        genre_str = ", ".join([f"{key}:{value:.2f}" for key, value in genre_top])
        signal_priority = profile.signal_priority if profile.signal_priority in ALLOWED_SIGNAL_PRIORITIES else "balanced"

        seg_cfg = strategy["segmentation"]
        segment_spec = SegmentSpec(
            segmentation_profile=profile_name,
            genre_str=genre_str,
            signal_priority=signal_priority,
            boundary_evidence_primary=", ".join(profile.boundary_evidence_primary),
            boundary_evidence_secondary=", ".join(profile.boundary_evidence_secondary),
            segmentation_policy=self._merge_policy_text(profile.segmentation_policy, seg_cfg["policy_notes"]),
        )
        title_spec = TitleSpec(
            segmentation_profile=profile_name,
            genre_str=genre_str,
            title_policy=profile.title_policy,
            notes=strategy["title"]["notes"],
        )

        desc_cfg = strategy["description"]
        weight_str = ", ".join([f"{slot}:{desc_cfg['slots_weight'][slot]:.2f}" for slot in DESCRIPTION_SLOTS])
        caption_spec = CaptionSpec(
            genre_str=genre_str,
            segmentation_profile=profile_name,
            signal_priority=signal_priority,
            slots_weight=weight_str,
            notes=desc_cfg["notes"],
        )

        segmentation_sampling = SamplingConfig(
            fps=float(seg_cfg["sampling"]["fps"]),
            max_resolution=int(seg_cfg["sampling"]["max_resolution"]),
            use_subtitles=bool(seg_cfg["sampling"]["use_subtitles"]),
        )
        detection_window_spec = DetectionWindowSpec(chunk_size_sec=600, chunk_overlap_sec=20)
        boundary_postprocess_spec = BoundaryPostProcessSpec(
            target_segment_length_sec=[int(t0), int(t1)],
            min_boundary_confidence=0.35,
            merge_short_segment_below_sec=max(10, int(t0 * 0.5)),
        )
        description_sampling = SamplingConfig(
            fps=float(desc_cfg["sampling"]["fps"]),
            max_resolution=int(desc_cfg["sampling"]["max_resolution"]),
            use_subtitles=bool(desc_cfg["sampling"]["use_subtitles"]),
        )
        return VideoProcessSpec(
            segment_spec=segment_spec,
            title_spec=title_spec,
            caption_spec=caption_spec,
            detection_window_spec=detection_window_spec,
            boundary_postprocess_spec=boundary_postprocess_spec,
            segmentation_sampling=segmentation_sampling,
            description_sampling=description_sampling,
            normalized_strategy=strategy,
        )
