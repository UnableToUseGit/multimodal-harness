from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseGenerator(ABC):
    """
    Base generator for text or multimodal models.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = dict(config or {})

    @abstractmethod
    def generate_single(
        self,
        prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
        schema: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Return: {"text": str, "json": dict|None, "response": dict}
        """
        raise NotImplementedError

    @abstractmethod
    def generate_batch(
        self,
        prompts: list[str] | None = None,
        messages_list: list[list[dict[str, str]]] | None = None,
        schema: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Return: [{"text": str, "json": dict|None, "response": dict}, ...]
        """
        raise NotImplementedError
