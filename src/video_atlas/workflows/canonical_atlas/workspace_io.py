from __future__ import annotations

import re
import shlex
from pathlib import Path


class WorkspaceIOMixin:
    def _workspace_root(self) -> Path:
        return Path(self.workspace.root_path)
