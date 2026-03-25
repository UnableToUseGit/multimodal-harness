from __future__ import annotations

from ...parsing import parse_json_response


class ResponseParsingMixin:
    def parse_response(self, generated_text: str) -> dict | list:
        return parse_json_response(generated_text)
