from __future__ import annotations

from ...prompts import DERIVED_CANDIDATE_PROMPT
from ...schemas import AtlasSegment, DerivationPolicy


class CandidateGenerationMixin:
    def _candidate_prompt(self, task_request: str, canonical_atlas) -> str:
        canonical_segments = "\n".join(
            [
                f"- {segment.segment_id}: {segment.start_time:.1f}-{segment.end_time:.1f}s | "
                f"title={segment.title} | detail={segment.caption}"
                for segment in canonical_atlas.segments
            ]
        )
        return DERIVED_CANDIDATE_PROMPT.render_user(
            task_request=task_request,
            canonical_segments=canonical_segments,
        )

    def _build_candidate_work_items(self, task_request: str, canonical_atlas) -> list[tuple[int, AtlasSegment, DerivationPolicy]]:
        system_prompt = DERIVED_CANDIDATE_PROMPT.render_system()
        planner_output = self.planner.generate_single(
            messages=self._prepare_messages(
                system_prompt=system_prompt,
                user_prompt=self._candidate_prompt(task_request, canonical_atlas),
            )
        )
        planner_data = self.parse_response(planner_output["text"])
        candidates = planner_data.get("candidates", []) if isinstance(planner_data, dict) else []
        segment_map = {segment.segment_id: segment for segment in canonical_atlas.segments}
        work_items: list[tuple[int, AtlasSegment, DerivationPolicy]] = []
        for index, candidate in enumerate(candidates, start=1):
            if not isinstance(candidate, dict):
                continue
            segment_id = str(candidate.get("segment_id", "")).strip()
            segment = segment_map.get(segment_id)
            if segment is None:
                continue
            work_items.append(
                (
                    index,
                    segment,
                    DerivationPolicy(
                        intent=str(candidate.get("intent", "")).strip(),
                        grounding_instruction=str(candidate.get("grounding_instruction", "")).strip(),
                    ),
                )
            )
        return work_items
