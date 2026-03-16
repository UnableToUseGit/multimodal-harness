from __future__ import annotations

from ...prompts import TASK_DERIVATION_PROMPT
from ...schemas import CanonicalAtlas, SegmentDerivationDecision, TaskDerivationPlan


class TaskDerivationPlanningMixin:
    def _build_segments_description(self, atlas: CanonicalAtlas) -> str:
        lines = []
        for segment in atlas.segments:
            lines.append(
                "\n".join(
                    [
                        f"- source_segment_id: {segment.source_segment_id}",
                        f"  source_folder: {segment.source_folder}",
                        f"  time_range: {segment.start_time:.1f} - {segment.end_time:.1f}",
                        f"  title: {segment.seg_title}",
                        f"  summary: {segment.summary}",
                        f"  detail: {segment.detail}",
                    ]
                )
            )
        return "\n".join(lines)

    def _fallback_plan(self, atlas: CanonicalAtlas, task_description: str) -> TaskDerivationPlan:
        decisions = []
        for index, segment in enumerate(atlas.segments, start=1):
            decisions.append(
                SegmentDerivationDecision(
                    source_segment_id=segment.source_segment_id,
                    source_folder=segment.source_folder,
                    relevance_score=1.0,
                    action="keep",
                    derived_title=segment.seg_title,
                    derived_summary=segment.summary,
                    order=index,
                    rationale="Fallback plan: keep canonical ordering because no task-specific planner output was available.",
                )
            )
        return TaskDerivationPlan(
            task_title=task_description.strip() or "Task-Aware Video Atlas",
            task_abstract="Fallback derivation based on canonical atlas ordering.",
            selection_strategy="Fallback strategy: keep all canonical segments in source order.",
            derived_segments=decisions,
        )

    def _normalize_plan(self, raw_plan: dict, atlas: CanonicalAtlas, task_description: str) -> TaskDerivationPlan:
        segments_by_id = {segment.source_segment_id: segment for segment in atlas.segments}
        normalized: list[SegmentDerivationDecision] = []

        for item in raw_plan.get("derived_segments", []):
            source_segment_id = item.get("source_segment_id")
            segment = segments_by_id.get(source_segment_id)
            if segment is None:
                continue
            action = item.get("action", "drop")
            if action not in {"keep", "drop"}:
                action = "drop"
            order = int(item.get("order", 0) or 0)
            if action == "keep" and order <= 0:
                order = len([decision for decision in normalized if decision.action == "keep"]) + 1
            if action == "drop":
                order = 0
            normalized.append(
                SegmentDerivationDecision(
                    source_segment_id=source_segment_id,
                    source_folder=item.get("source_folder", segment.source_folder),
                    relevance_score=max(0.0, min(1.0, float(item.get("relevance_score", 0.0) or 0.0))),
                    action=action,
                    derived_title=(item.get("derived_title") or segment.seg_title).strip(),
                    derived_summary=(item.get("derived_summary") or segment.summary).strip(),
                    order=order,
                    rationale=(item.get("rationale") or "").strip(),
                )
            )

        if not normalized:
            return self._fallback_plan(atlas, task_description)

        keep_count = len([item for item in normalized if item.action == "keep"])
        if keep_count == 0:
            return self._fallback_plan(atlas, task_description)

        normalized.sort(key=lambda item: (item.order if item.action == "keep" else 10**9, item.source_segment_id))
        next_order = 1
        for item in normalized:
            if item.action == "keep":
                item.order = next_order
                next_order += 1
            else:
                item.order = 0

        return TaskDerivationPlan(
            task_title=(raw_plan.get("task_title") or task_description or "Task-Aware Video Atlas").strip(),
            task_abstract=(raw_plan.get("task_abstract") or "").strip(),
            selection_strategy=(raw_plan.get("selection_strategy") or "").strip(),
            derived_segments=normalized,
        )

    def _plan_task_derivation(self, atlas: CanonicalAtlas, task_description: str) -> TaskDerivationPlan:
        messages = self._prepare_messages(
            system_prompt=TASK_DERIVATION_PROMPT["SYSTEM"],
            user_prompt=TASK_DERIVATION_PROMPT["USER"].format(
                task_description=task_description,
                root_readme=atlas.root_readme,
                segments_description=self._build_segments_description(atlas),
            ),
        )

        output = self.generator.generate_single(messages=messages)
        raw_plan = self.parse_response(output.get("text"))
        if not isinstance(raw_plan, dict):
            return self._fallback_plan(atlas, task_description)
        return self._normalize_plan(raw_plan, atlas, task_description)
