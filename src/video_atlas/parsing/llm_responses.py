from __future__ import annotations

import json
import re

try:
    import json_repair
except ImportError:
    json_repair = None


def strip_think_blocks(text: str | None) -> str:
    if text is None:
        return ""
    return re.sub(r"<think>.*?</think>", "", text.strip(), flags=re.DOTALL).strip()


def extract_json_payload(text: str | None) -> str:
    cleaned = strip_think_blocks(text)
    if not cleaned:
        return ""

    fenced_pattern = r"```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```"
    match = re.search(fenced_pattern, cleaned, re.DOTALL)
    if match:
        return match.group(1)

    first_brace = cleaned.find("{")
    first_bracket = cleaned.find("[")
    if first_bracket != -1 and (first_brace == -1 or first_bracket < first_brace):
        last_bracket = cleaned.rfind("]")
        if last_bracket != -1:
            return cleaned[first_bracket : last_bracket + 1]
    elif first_brace != -1:
        last_brace = cleaned.rfind("}")
        if last_brace != -1:
            return cleaned[first_brace : last_brace + 1]
    return cleaned


def parse_json_response(generated_text: str | None) -> dict | list:
    payload = extract_json_payload(generated_text)
    if not payload:
        return {}

    try:
        return json.loads(payload)
    except Exception:
        if json_repair is None:
            return {}
        try:
            return json_repair.loads(payload)
        except Exception:
            return {}
