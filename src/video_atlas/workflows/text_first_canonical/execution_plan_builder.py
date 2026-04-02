from __future__ import annotations

import copy
from typing import Any

from ...schemas import (
    ALLOWED_GENRES,
    CanonicalExecutionPlan,
    resolve_profile,
)


class ExecutionPlanBuilderMixin:
    def _clamp(self, x: float, lo: float, hi: float) -> float:
        try:
            x = float(x)
        except Exception:
            return lo
        return max(lo, min(hi, x))

    def _normalize_genres(self, value: Any, allowed: set[str], fallback_key: str = "other", topk: int = 2) -> list[str]:
        if not isinstance(value, list):
            return [fallback_key]

        normalized: list[str] = []
        for item in value:
            if not isinstance(item, str):
                continue
            genre = item.strip()
            if not genre or genre not in allowed or genre in normalized:
                continue
            normalized.append(genre)
            if len(normalized) >= max(1, topk):
                break

        return normalized or [fallback_key]

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

    def _construct_execution_plan(self, planner_output: dict[str, Any], planner_reasoning_content: str) -> CanonicalExecutionPlan:
        planner_confidence = self._clamp(planner_output.get("planner_confidence", 0.25), 0.0, 1.0)

        genres = self._normalize_genres(
            planner_output.get("genres", []),
            allowed=ALLOWED_GENRES,
            fallback_key="other",
            topk=2,
        )

        concise_description = planner_output.get("concise_description", "")
        if not isinstance(concise_description, str):
            concise_description = ""
        concise_description = concise_description.strip()

        profile_name, profile = resolve_profile(str(planner_output.get("profile", "")).strip())

        return CanonicalExecutionPlan(
            planner_confidence=planner_confidence,
            genres=genres,
            concise_description=concise_description,
            profile_name=profile_name,
            profile=profile,
            output_language=str(planner_output.get("output_language", "en") or "en"),
            chunk_size_sec=max(60, int(getattr(self, "chunk_size_sec", 600))),
            chunk_overlap_sec=max(0, int(getattr(self, "chunk_overlap_sec", 20))),
            planner_reasoning_content=planner_reasoning_content,
        )
