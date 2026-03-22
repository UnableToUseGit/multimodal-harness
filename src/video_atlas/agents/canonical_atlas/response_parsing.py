from __future__ import annotations

import json
import re

try:
    import json_repair
except ImportError:
    json_repair = None


class ResponseParsingMixin:
    def parse_response(self, generated_text: str) -> dict | list:
        if generated_text is None:
            return {}

        text = generated_text.strip()
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

        pattern = r"```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            text = match.group(1)
        else:
            first_brace = text.find("{")
            first_bracket = text.find("[")
            if first_bracket != -1 and (first_brace == -1 or first_bracket < first_brace):
                last_bracket = text.rfind("]")
                if last_bracket != -1:
                    text = text[first_bracket : last_bracket + 1]
            elif first_brace != -1:
                last_brace = text.rfind("}")
                if last_brace != -1:
                    text = text[first_brace : last_brace + 1]

        try:
            return json.loads(text)
        except Exception:
            if json_repair is None:
                return {}
            try:
                return json_repair.loads(text)
            except Exception:
                return {}
