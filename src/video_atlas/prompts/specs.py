"""Lightweight prompt specification and registry helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from string import Formatter
from typing import Any


class PromptRenderError(ValueError):
    """Raised when a prompt cannot be rendered because required fields are missing."""


def _template_fields(template: str) -> set[str]:
    fields: set[str] = set()
    for _, field_name, _, _ in Formatter().parse(template):
        if not field_name:
            continue
        root_name = field_name.split(".", 1)[0].split("[", 1)[0]
        if root_name:
            fields.add(root_name)
    return fields


@dataclass(frozen=True, slots=True)
class PromptSpec:
    """Description of a prompt pair and its expected input/output contract."""

    name: str
    purpose: str
    system_template: str
    user_template: str
    input_fields: tuple[str, ...]
    output_contract: str
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_fields", tuple(self.input_fields))
        object.__setattr__(self, "tags", tuple(self.tags))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def __getitem__(self, key: str) -> str:
        if key == "SYSTEM":
            return self.system_template
        if key == "USER":
            return self.user_template
        raise KeyError(key)

    def _validate(self, template: str, kwargs: dict[str, Any]) -> None:
        required_fields = tuple(sorted(_template_fields(template)))
        missing = [field for field in required_fields if field not in kwargs]
        if missing:
            raise PromptRenderError(
                f"PromptSpec '{self.name}' is missing required fields: {', '.join(missing)}"
            )

    def render_system(self, **kwargs: Any) -> str:
        self._validate(self.system_template, kwargs)
        try:
            return self.system_template.format(**kwargs)
        except (AttributeError, IndexError, KeyError, ValueError, TypeError) as exc:
            raise PromptRenderError(
                f"PromptSpec '{self.name}' could not render system template: {exc}"
            ) from exc

    def render_user(self, **kwargs: Any) -> str:
        self._validate(self.user_template, kwargs)
        try:
            return self.user_template.format(**kwargs)
        except (AttributeError, IndexError, KeyError, ValueError, TypeError) as exc:
            raise PromptRenderError(
                f"PromptSpec '{self.name}' could not render user template: {exc}"
            ) from exc

    def render(self, **kwargs: Any) -> tuple[str, str]:
        return self.render_system(**kwargs), self.render_user(**kwargs)


class PromptRegistry:
    """Ordered registry of prompt specifications."""

    def __init__(self) -> None:
        self._prompts: dict[str, PromptSpec] = {}

    def register(self, prompt: PromptSpec) -> None:
        if prompt.name in self._prompts:
            raise ValueError(f"PromptSpec '{prompt.name}' is already registered")
        self._prompts[prompt.name] = prompt

    def get(self, name: str) -> PromptSpec:
        return self._prompts[name]

    def list_prompts(self) -> list[PromptSpec]:
        return list(self._prompts.values())
