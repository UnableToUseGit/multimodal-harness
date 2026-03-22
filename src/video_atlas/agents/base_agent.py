from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from ..workspaces.base import get_logger

if TYPE_CHECKING:
    from ..generators.base import BaseGenerator
    from ..workspaces.base import BaseWorkspace


class BaseAtlasAgent(ABC):
    """
    Base agent abstraction for the VideoAtlas pipeline.

    Holds generator (LLM/API client) and workspace (command executor).
    
    Architecture:
    - workspace: Executes Linux commands (mkdir, touch, echo, etc.) to modify the file system
    - generator: LLM for intelligent decision making
    
    Usage:
        When the agent wants to create a directory:
            workspace.run("mkdir -p /path/to/dir")
        
        When the agent wants to create a file:
            workspace.run("echo 'content' > /path/to/file.md")
        
    Public interface:
        add() - The single unified entry point.
    """

    def __init__(
        self,
        generator: Any,
        workspace: Optional[Any],
    ):
        self.generator = generator
        self.workspace = workspace
        self.logger = workspace.logger if workspace is not None and hasattr(workspace, "logger") else get_logger(self.__class__.__name__)

    def run_command(self, command: str, workdir: str = None) -> tuple[str, str]:
        """
        Execute a Linux command through the workspace.
        
        Args:
            command: Linux command to execute (e.g., "mkdir -p /dir", "echo 'text' > file.md")
            workdir: Working directory for the command
            
        Returns:
            Tuple of (output, exit_code_or_error)
        """
        if self.workspace is None:
            raise RuntimeError("No workspace configured. Cannot execute commands.")
        return self.workspace.run(command, workdir=workdir)
    
    def _log_info(self, message: str, *args: Any) -> None:
        self.logger.info(message, *args)

    def _log_warning(self, message: str, *args: Any) -> None:
        self.logger.warning(message, *args)

    def _log_error(self, message: str, *args: Any) -> None:
        self.logger.error(message, *args)

    @abstractmethod
    def add(
        self,
        input_file: Path,
        segmentation_request: str = "",
    ) -> Any:
        """
        Process an input video into a structured workspace.
        
        Args:
            input_file: Path to input file
            segmentation_request: Optional context/instruction for segmentation
            
        Returns:
            Result of the operation
        """
        raise NotImplementedError
