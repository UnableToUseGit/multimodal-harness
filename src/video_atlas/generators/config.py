from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class GeneratorConfig(BaseModel):
    """Base configuration for custom generator implementations."""

    model_name: str = Field(..., description="Name of the model to use")
    temperature: float = Field(0.0, description="Sampling temperature")
    top_p: float = Field(1.0, description="Top-p sampling parameter")
    max_tokens: int = Field(512, description="Maximum number of tokens to generate")
    system_prompt: Optional[str] = Field(None, description="Default system prompt")
    extra_params: dict[str, Any] = Field(default_factory=dict, description="Additional generator parameters")
