from __future__ import annotations

from pathlib import Path

from ...schemas import CreateTaskDerivationResult
from .loader import load_canonical_atlas


class TaskDerivationPipelineMixin:
    def add(
        self,
        source_workspace: str | Path,
        task_description: str,
        verbose: bool = False,
    ) -> CreateTaskDerivationResult:
        atlas = load_canonical_atlas(source_workspace)
        if verbose:
            self._log_info("Loaded canonical atlas from: %s", atlas.root_path)
            self._log_info("Canonical segments available: %d", len(atlas.segments))

        plan = self._plan_task_derivation(atlas, task_description)
        if verbose:
            kept = len([item for item in plan.derived_segments if item.action == 'keep'])
            self._log_info("Derived task plan with %d kept segments", kept)

        self._write_task_workspace(atlas, plan, task_description)
        return CreateTaskDerivationResult(
            success=True,
            derived_segment_num=len([item for item in plan.derived_segments if item.action == "keep"]),
            task_title=plan.task_title,
            source_workspace=str(atlas.root_path),
            task_description=task_description,
        )
