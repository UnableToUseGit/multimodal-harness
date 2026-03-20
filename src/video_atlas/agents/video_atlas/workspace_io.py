from __future__ import annotations

import re
import shlex
from pathlib import Path


class WorkspaceIOMixin:
    def _workspace_root(self) -> Path:
        return Path(self.workspace.root_path)

    def _write_workspace_text(self, relative_path: str | Path, content: str) -> None:
        target_path = self._workspace_root() / Path(relative_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")

    def _slugify_segment_title(self, title: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        return normalized or "untitled"

    def _segment_save_name(self, seg_id: int, seg_title: str, seg_start_time: float, seg_end_time: float) -> str:
        return f"seg{seg_id:04d}-{self._slugify_segment_title(seg_title)}-{seg_start_time:.2f}-{seg_end_time:.2f}s"

    def _clip_exists(self, relative_path: str | Path) -> bool:
        return (self._workspace_root() / Path(relative_path)).exists()

    def _extract_clip(self, video_path: str, seg_start_time: float, seg_end_time: float, relative_output_path: str | Path) -> None:
        output_path = self._workspace_root() / Path(relative_output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = (
            "ffmpeg -y -loglevel quiet "
            f"-ss {seg_start_time} -to {seg_end_time} "
            f"-i {shlex.quote(Path(video_path).name)} "
            f"-c copy {shlex.quote(str(output_path.relative_to(self._workspace_root())))}"
        )
        output, exit_code = self.workspace.run(command)
        if not exit_code.endswith("0"):
            raise RuntimeError(f"ffmpeg failed with exit code {exit_code}: {output}")

    def _check_video_workspace(self) -> bool:
        try:
            _, exit_info = self.workspace.run("test -e 'README.md'")
            assert not exit_info.startswith("Error")

            _, exit_info = self.workspace.run("test -e 'segments/'")
            assert not exit_info.startswith("Error")

            output, exit_info = self.workspace.run("ls -1 'segments/'")
            assert not exit_info.startswith("Error")
            assert len([item for item in output.strip().split("\n") if item]) > 0
        except Exception:
            return False
        return True

    def _organize_video_workspace(self) -> None:
        self.workspace.run("mkdir -p '.agentignore'")

        _, exit_info = self.workspace.run("test -e 'subtitles.srt'")
        if not exit_info.startswith("Error"):
            self.workspace.run("mv subtitles.srt '.agentignore/'")

        _, exit_info = self.workspace.run("test -e 'EXECUTION_PLAN.json'")
        if not exit_info.startswith("Error"):
            self.workspace.run("mv EXECUTION_PLAN.json '.agentignore/'")

        _, exit_info = self.workspace.run("test -e 'PROBE_RESULT.json'")
        if not exit_info.startswith("Error"):
            self.workspace.run("mv PROBE_RESULT.json '.agentignore/'")
