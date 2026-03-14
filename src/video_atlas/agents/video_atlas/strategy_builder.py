from __future__ import annotations

import copy
from typing import Any

from ...schemas import (
    ALLOWED_EVIDENCE,
    ALLOWED_GENRES,
    ALLOWED_GRANULARITY,
    ALLOWED_STRUCTURE_MODES,
    CaptionSpec,
    DEFAULT_STRATEGY_PACKAGE,
    DESCRIPTION_SLOTS,
    SamplingConfig,
    SegmentSpec,
    VideoProcessSpec,
)


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
        revised_info = []
        last_break = chunk_start_time
        for item in segmentation_info:
            break_timepoint = item.get("timestamp", 0)
            if break_timepoint >= chunk_end_time or break_timepoint <= chunk_start_time or break_timepoint <= last_break:
                continue
            revised_info.append(item)
            last_break = break_timepoint
        return revised_info

    def check_probe_result(self, probe_result):
        assert type(probe_result) == dict, f"probe_result is not dict: {probe_result}"
        assert "genre_distribution" in probe_result and type(probe_result["genre_distribution"]) == dict, f"correct genre_distribution not in probe_result: {probe_result}"
        assert "structure_mode" in probe_result, f"structure_mode not in probe_result: {probe_result}"
        assert "signal_priority" in probe_result, f"signal_priority not in probe_result: {probe_result}"
        assert "segmentation" in probe_result, f"segmentation not in probe_result: {probe_result}"
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

    def _normalize_dist(self, value: dict[str, Any], allowed: set[str], fallback_key: str = "other", topk: int = 4) -> dict[str, float]:
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

    def _build_spec_from_strategy_pkg(self, strategy_pkg: dict[str, Any]) -> VideoProcessSpec:
        strategy = self._merge_defaults(strategy_pkg, DEFAULT_STRATEGY_PACKAGE)
        strategy["planner_confidence"] = self._clamp(strategy.get("planner_confidence", 0.25), 0.0, 1.0)
        strategy["genre_distribution"] = self._normalize_dist(
            strategy.get("genre_distribution", {}),
            allowed=ALLOWED_GENRES,
            fallback_key="other",
            topk=4,
        )

        structure_mode = strategy.get("structure_mode", {})
        primary = structure_mode.get("primary", "other")
        if primary not in ALLOWED_STRUCTURE_MODES:
            primary = "other"
        secondary = structure_mode.get("secondary", [])
        if not isinstance(secondary, list):
            secondary = []
        secondary = [mode for mode in secondary if mode in ALLOWED_STRUCTURE_MODES and mode != primary][:2]
        strategy["structure_mode"] = {"primary": primary, "secondary": secondary}

        signal_priority = strategy.get("signal_priority", {})
        audio_weight = self._clamp(signal_priority.get("audio_text", 0.6), 0.0, 1.0)
        visual_weight = self._clamp(signal_priority.get("visual", 0.4), 0.0, 1.0)
        total = audio_weight + visual_weight
        if total <= 0:
            audio_weight, visual_weight, total = 0.6, 0.4, 1.0
        audio_weight /= total
        visual_weight /= total
        rationale = signal_priority.get("rationale", "")
        if not isinstance(rationale, str) or not rationale.strip():
            rationale = "Use a conservative hybrid strategy based on available evidence."
        strategy["signal_priority"] = {
            "audio_text": audio_weight,
            "visual": visual_weight,
            "rationale": rationale.strip(),
        }

        segmentation = strategy.get("segmentation", {})
        granularity = segmentation.get("granularity", "hybrid")
        if granularity not in ALLOWED_GRANULARITY:
            granularity = "hybrid"
        target_segment_length = segmentation.get("target_segment_length_sec", [90, 480])
        if not (isinstance(target_segment_length, list) and len(target_segment_length) == 2):
            target_segment_length = [90, 480]
        t0 = int(max(10, min(3600, int(target_segment_length[0]))))
        t1 = int(max(t0 + 10, min(7200, int(target_segment_length[1]))))
        primary_evidence = segmentation.get("boundary_evidence_primary", [])
        secondary_evidence = segmentation.get("boundary_evidence_secondary", [])
        if not isinstance(primary_evidence, list):
            primary_evidence = []
        if not isinstance(secondary_evidence, list):
            secondary_evidence = []
        primary_evidence = [item for item in primary_evidence if item in ALLOWED_EVIDENCE][:3]
        secondary_evidence = [item for item in secondary_evidence if item in ALLOWED_EVIDENCE and item not in primary_evidence][:3]
        if not primary_evidence:
            primary_evidence = ["topic_shift_in_subtitles", "scene_location_change"]

        seg_sampling = segmentation.get("sampling", {})
        seg_fps = self._clamp(seg_sampling.get("fps", 0.5), 0.05, 4.0)
        seg_res = int(max(128, min(1536, int(seg_sampling.get("max_resolution", 384)))))
        seg_use_subtitles = self._as_bool(seg_sampling.get("use_subtitles", True), default=True)
        seg_notes = segmentation.get("notes", "")
        if not isinstance(seg_notes, str) or not seg_notes.strip():
            seg_notes = "Prefer self-contained segments; avoid over-segmentation on weak boundaries."
        strategy["segmentation"] = {
            "granularity": granularity,
            "target_segment_length_sec": [t0, t1],
            "boundary_evidence_primary": primary_evidence,
            "boundary_evidence_secondary": secondary_evidence,
            "sampling": {"fps": seg_fps, "max_resolution": seg_res, "use_subtitles": seg_use_subtitles},
            "notes": seg_notes.strip(),
        }

        description = strategy.get("description", {})
        slot_weights = self._normalize_weights(description.get("slots_weight", {}), DESCRIPTION_SLOTS)
        desc_sampling = description.get("sampling", {})
        desc_fps = self._clamp(desc_sampling.get("fps", 0.2), 0.05, 4.0)
        desc_res = int(max(128, min(1536, int(desc_sampling.get("max_resolution", 384)))))
        desc_use_subtitles = self._as_bool(desc_sampling.get("use_subtitles", True), default=True)
        desc_notes = description.get("notes", "")
        if not isinstance(desc_notes, str) or not desc_notes.strip():
            desc_notes = "Fill all slots; focus on high-level segment summary rather than frame-by-frame narration."
        strategy["description"] = {
            "slots_weight": slot_weights,
            "sampling": {"fps": desc_fps, "max_resolution": desc_res, "use_subtitles": desc_use_subtitles},
            "notes": desc_notes.strip(),
        }

        genre_top = sorted(strategy["genre_distribution"].items(), key=lambda item: item[1], reverse=True)
        genre_str = ", ".join([f"{key}:{value:.2f}" for key, value in genre_top])
        modes = [strategy["structure_mode"]["primary"], *strategy["structure_mode"]["secondary"]]
        mode_str = ", ".join(modes)

        seg_cfg = strategy["segmentation"]
        segment_spec = SegmentSpec(
            genre_str=genre_str,
            mode_str=mode_str,
            signal_audio_priority=f'{strategy["signal_priority"]["audio_text"]:.2f}',
            signal_visual_priority=f'{strategy["signal_priority"]["visual"]:.2f}',
            target_segment_length_sec=f'[{seg_cfg["target_segment_length_sec"][0]}, {seg_cfg["target_segment_length_sec"][1]}]',
            boundary_evidence_primary=", ".join(seg_cfg["boundary_evidence_primary"]),
            boundary_evidence_secondary=", ".join(seg_cfg["boundary_evidence_secondary"]),
        )

        desc_cfg = strategy["description"]
        weight_str = ", ".join([f"{slot}:{desc_cfg['slots_weight'][slot]:.2f}" for slot in DESCRIPTION_SLOTS])
        caption_spec = CaptionSpec(
            genre_str=genre_str,
            mode_str=mode_str,
            signal_audio_priority=f'{strategy["signal_priority"]["audio_text"]:.2f}',
            signal_visual_priority=f'{strategy["signal_priority"]["visual"]:.2f}',
            slots_weight=weight_str,
            notes=desc_cfg["notes"],
        )

        segmentation_sampling = SamplingConfig(
            fps=float(seg_cfg["sampling"]["fps"]),
            max_resolution=int(seg_cfg["sampling"]["max_resolution"]),
            use_subtitles=bool(seg_cfg["sampling"]["use_subtitles"]),
        )
        description_sampling = SamplingConfig(
            fps=float(desc_cfg["sampling"]["fps"]),
            max_resolution=int(desc_cfg["sampling"]["max_resolution"]),
            use_subtitles=bool(desc_cfg["sampling"]["use_subtitles"]),
        )
        return VideoProcessSpec(
            segment_spec=segment_spec,
            caption_spec=caption_spec,
            segmentation_sampling=segmentation_sampling,
            description_sampling=description_sampling,
            normalized_strategy=strategy,
        )
