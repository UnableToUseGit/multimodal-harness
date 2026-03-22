from __future__ import annotations

import copy
from typing import Any

from ...schemas import (
    ALLOWED_GENRES,
    CanonicalExecutionPlan,
    CaptionSpecification,
    SegmentationSpecification,
    resolve_caption_profile,
    resolve_sampling_profile,
    resolve_segmentation_profile,
)


DEFAULT_PLANNER_OUTPUT: dict[str, Any] = {
    "planner_confidence": 0.25,
    "genre_distribution": {"other": 1.0},
    "segmentation_profile": "generic_longform_continuous",
    "sampling_profile": "balanced"
}


class ExecutionPlanBuilderMixin:
    
    def _clamp(self, x: float, lo: float, hi: float) -> float:
        try:
            x = float(x)
        except Exception:
            return lo
        return max(lo, min(hi, x))

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

    def _merge_defaults(self, user_plan: dict[str, Any], default_plan: dict[str, Any]) -> dict[str, Any]:
        merged = copy.deepcopy(default_plan)

        def rec(dst: dict[str, Any], src: dict[str, Any]):
            for key, value in (src or {}).items():
                if isinstance(value, dict) and isinstance(dst.get(key), dict):
                    rec(dst[key], value)
                else:
                    dst[key] = value

        if isinstance(user_plan, dict):
            rec(merged, user_plan)
        return merged

    def _construct_execution_plan(self, planner_output: dict[str, Any]) -> CanonicalExecutionPlan:
        planner_confidence = self._clamp(planner_output.get("planner_confidence", 0.25), 0.0, 1.0)
        genre_distribution = self._normalize_dist(
            planner_output.get("genre_distribution", {}),
            allowed=ALLOWED_GENRES,
            fallback_key="other",
            topk=2,
        )

        profile_name, profile = resolve_segmentation_profile(str(planner_output.get("segmentation_profile", "")).strip())
        caption_profile_name, caption_profile = resolve_caption_profile(profile_name)

        _, shared_sampling = resolve_sampling_profile(str(planner_output.get("sampling_profile", "")).strip())

        return CanonicalExecutionPlan(
            planner_confidence=planner_confidence,
            genre_distribution=genre_distribution,
            segmentation_specification=SegmentationSpecification(
                profile_name=profile_name,
                profile=profile,
                frame_sampling_profile=shared_sampling,
            ),
            caption_specification=CaptionSpecification(
                profile_name=caption_profile_name,
                profile=caption_profile,
                frame_sampling_profile=shared_sampling,
            ),
            chunk_size_sec=max(60, int(getattr(self, "chunk_size_sec", 600))),
            chunk_overlap_sec=max(0, int(getattr(self, "chunk_overlap_sec", 20))),
        )
