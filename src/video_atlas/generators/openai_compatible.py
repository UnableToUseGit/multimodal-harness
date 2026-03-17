from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from ..settings import get_settings
from .base import BaseGenerator


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
                elif "text" in item:
                    parts.append(str(item.get("text", "")))
            elif item is not None:
                parts.append(str(item))
        return "\n".join([part for part in parts if part])
    return "" if content is None else str(content)


class OpenAICompatibleGenerator(BaseGenerator):
    """Minimal OpenAI-compatible chat-completions client."""

    def __init__(self, config):
        super().__init__(config)
        settings = get_settings()
        if not settings.api_base:
            raise ValueError("VIDEO_ATLAS_API_BASE is required for OpenAICompatibleGenerator")
        if not settings.api_key:
            raise ValueError("VIDEO_ATLAS_API_KEY is required for OpenAICompatibleGenerator")
        self.api_base = settings.api_base.rstrip("/")
        self.api_key = settings.api_key

    def _chat_completions_url(self) -> str:
        if self.api_base.endswith("/chat/completions"):
            return self.api_base
        return f"{self.api_base}/chat/completions"

    def _build_payload(
        self,
        prompt: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        schema: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config["model_name"],
            "temperature": self.config.get("temperature", 0.0),
            "top_p": self.config.get("top_p", 1.0),
            "max_tokens": self.config.get("max_tokens", 512),
        }

        if messages is not None:
            payload["messages"] = messages
        else:
            payload["messages"] = [{"role": "user", "content": prompt or ""}]

        if schema is not None:
            payload["response_format"] = schema

        merged_extra = dict(self.config.get("extra_body", {}))
        if extra_body:
            merged_extra.update(extra_body)
        payload.update(merged_extra)
        return payload

    def generate_single(
        self,
        prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
        schema: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = self._build_payload(prompt=prompt, messages=messages, schema=schema, extra_body=extra_body)
        request = urllib.request.Request(
            self._chat_completions_url(),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request) as response:
                raw_response = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Generator request failed with status {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Generator request failed: {exc}") from exc

        response_json = json.loads(raw_response)
        choice = response_json["choices"][0]["message"]
        text = _extract_text(choice.get("content"))
        return {
            "text": text,
            "json": None,
            "response": response_json,
        }

    def generate_batch(
        self,
        prompts: list[str] | None = None,
        messages_list: list[list[dict[str, str]]] | None = None,
        schema: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if messages_list is not None:
            return [
                self.generate_single(messages=messages, schema=schema, extra_body=extra_body)
                for messages in messages_list
            ]
        return [
            self.generate_single(prompt=prompt, schema=schema, extra_body=extra_body)
            for prompt in (prompts or [])
        ]
