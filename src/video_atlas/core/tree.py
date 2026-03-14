# -*- coding: utf-8 -*-
"""Read-only tree structures used by VideoAtlasAgent."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from pydantic import BaseModel, Field

from .node import FSNode

if TYPE_CHECKING:
    from ..workspaces.base import BaseWorkspace


class BaseTree(ABC):
    """Minimal tree interface for the generated workspace."""

    @property
    @abstractmethod
    def root_path(self) -> Path:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_disk(cls, root_path: Path, workspace: "BaseWorkspace") -> "BaseTree":
        raise NotImplementedError


class VideoAtlasTree(BaseModel, BaseTree):
    """Read-only tree view over the generated video workspace."""

    root_path_: Path = Field(..., alias="root_path")
    root: FSNode = Field(...)
    meta: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

    @property
    def root_path(self) -> Path:
        return self.root_path_

    @property
    def is_empty(self) -> bool:
        return len(self.root.children) == 0

    def get_node(self, path: str) -> Optional[FSNode]:
        path = path.strip()
        if path in ("", "/", "."):
            return self.root
        if path.startswith("/"):
            path = path[1:]
        return self.root.find_node([p for p in path.split("/") if p])

    def tree_view(self, path: str = "/", depth: int = -1) -> str:
        node = self.get_node(path)
        if node is None:
            return f"Path not found: {path}"
        return node.to_tree_str(depth=depth)

    def reload(self, workspace: "BaseWorkspace") -> "VideoAtlasTree":
        return self.from_disk(self.root_path_, workspace)

    @classmethod
    def from_disk(cls, root_path: Path, workspace: "BaseWorkspace") -> "VideoAtlasTree":
        root_path = Path(root_path)
        output, _ = workspace.run(f"test -d '{root_path}' && echo 'exists' || echo 'not_found'")
        if "not_found" in output:
            raise FileNotFoundError(f"Workspace root path not found: {root_path}")

        meta_file = root_path / ".video_atlas_meta.json"
        meta: Dict[str, Any] = {}
        root_name = root_path.name

        output, exit_info = workspace.run(f"cat '{meta_file}' 2>/dev/null || echo ''")
        if output.strip() and not exit_info.startswith("Error"):
            try:
                meta_data = json.loads(output.strip())
                meta = meta_data.get("meta", {})
                root_name = meta_data.get("root_name", root_path.name)
            except json.JSONDecodeError:
                pass

        root = cls._read_node_from_disk(root_path, root_name, workspace)
        return cls(root_path=root_path, root=root, meta=meta)

    @classmethod
    def _read_node_from_disk(cls, path: Path, name: str, workspace: "BaseWorkspace") -> FSNode:
        output, _ = workspace.run(f"test -d '{path}' && echo 'dir' || echo 'file'")
        is_dir = "dir" in output

        if is_dir:
            readme_path = path / "README.md"
            output, exit_info = workspace.run(f"cat '{readme_path}' 2>/dev/null || echo ''")
            summary = output if not exit_info.startswith("Error") and "No such file" not in output else ""

            node = FSNode.create_dir(name, summary=summary)
            output, exit_info = workspace.run(f"ls -1 '{path}' 2>/dev/null | grep -v '^\\..*' | sort")
            if output.strip() and not exit_info.startswith("Error"):
                for child_name in output.strip().split("\n"):
                    child_name = child_name.strip()
                    if child_name:
                        child_path = path / child_name
                        node.children.append(cls._read_node_from_disk(child_path, child_name, workspace))
            return node

        output, exit_info = workspace.run(f"cat '{path}'")
        content = output if not exit_info.startswith("Error") else ""
        return FSNode.create_file(name, content=content)

    @classmethod
    def create_empty(cls, root_path: Path, name: str = "video_atlas", meta: Dict[str, Any] | None = None) -> "VideoAtlasTree":
        root = FSNode.create_dir(name, summary="# VideoAtlas\n\nThis is the root of the generated video context workspace.")
        return cls(root_path=Path(root_path), root=root, meta=meta or {"created_at": datetime.now().isoformat()})

    def check_video_workspace(self, workspace: "BaseWorkspace") -> bool:
        try:
            _, exit_info = workspace.run("test -e 'README.md'")
            assert not exit_info.startswith("Error")

            _, exit_info = workspace.run("test -e 'segments/'")
            assert not exit_info.startswith("Error")

            output, exit_info = workspace.run("ls -1 'segments/'")
            assert not exit_info.startswith("Error")
            assert len([x for x in output.strip().split("\n") if x]) > 0
        except Exception:
            return False
        return True

    def organize_video_workspace(self, workspace: "BaseWorkspace") -> None:
        workspace.run("mkdir -p '.agentignore'")

        _, exit_info = workspace.run("test -e 'subtitles.srt'")
        if not exit_info.startswith("Error"):
            workspace.run("mv subtitles.srt '.agentignore/'")

        _, exit_info = workspace.run("test -e 'PROBE_RESULT.json'")
        if not exit_info.startswith("Error"):
            workspace.run("mv PROBE_RESULT.json '.agentignore/'")
