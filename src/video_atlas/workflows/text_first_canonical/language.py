from __future__ import annotations

import re


_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_HIRAGANA_KATAKANA_RE = re.compile(r"[\u3040-\u30ff]")
_LATIN_RE = re.compile(r"[A-Za-z]")
_EN_STOPWORDS = {
    "the",
    "and",
    "is",
    "are",
    "of",
    "to",
    "in",
    "for",
    "that",
    "with",
    "this",
    "it",
    "on",
    "as",
    "be",
}


def _clean_text(text: str) -> str:
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_language(text: str) -> str:
    normalized = _clean_text(str(text or ""))
    if not normalized:
        return "unknown"

    zh_count = len(_CJK_RE.findall(normalized))
    ja_count = len(_HIRAGANA_KATAKANA_RE.findall(normalized))
    latin_count = len(_LATIN_RE.findall(normalized))

    if ja_count >= 2:
        return "ja"
    if zh_count >= 2 and ja_count == 0:
        return "zh"
    if latin_count >= 6:
        words = re.findall(r"[A-Za-z]+", normalized.lower())
        stopword_hits = sum(1 for word in words if word in _EN_STOPWORDS)
        if stopword_hits >= 2 or len(words) >= 4:
            return "en"
    return "unknown"


def _metadata_text(source_metadata) -> str:
    if source_metadata is None:
        return ""
    if hasattr(source_metadata, "to_dict"):
        payload = source_metadata.to_dict()
    elif isinstance(source_metadata, dict):
        payload = source_metadata
    else:
        payload = {}
    title = str(payload.get("title", "") or "")
    description = str(payload.get("introduction", "") or payload.get("description", "") or "")
    return "\n".join(part for part in (title, description) if part.strip())


def resolve_atlas_language(
    *,
    structure_request: str,
    source_metadata,
    subtitles_text: str,
) -> str:
    for candidate in (
        structure_request,
        _metadata_text(source_metadata),
        subtitles_text,
    ):
        detected = detect_language(candidate)
        if detected != "unknown":
            return detected
    return "en"


def render_output_language_instruction(language: str) -> str:
    normalized = (language or "en").strip().lower()
    if normalized == "zh":
        return "所有生成文本必须使用中文。"
    if normalized == "ja":
        return "すべての生成テキストは日本語で出力すること。"
    return "All generated text must be in English."
