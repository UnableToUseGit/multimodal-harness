from __future__ import annotations

import unittest

from video_atlas.schemas.acquisition import SourceMetadata
from video_atlas.workflows.text_first_canonical.language import (
    detect_language,
    resolve_atlas_language,
)


class TextFirstLanguageResolutionTest(unittest.TestCase):
    def test_detect_language_supports_chinese(self) -> None:
        self.assertEqual(detect_language("这是一个中文标题，介绍一个概念。"), "zh")

    def test_detect_language_supports_japanese(self) -> None:
        self.assertEqual(detect_language("これは日本語の解説です。"), "ja")

    def test_detect_language_supports_english(self) -> None:
        self.assertEqual(detect_language("This is a technical explanation about systems and design."), "en")

    def test_detect_language_returns_unknown_for_weak_signal(self) -> None:
        self.assertEqual(detect_language("12345 -- ..."), "unknown")

    def test_structure_request_has_highest_priority(self) -> None:
        metadata = SourceMetadata(title="English title", introduction="English description")

        resolved = resolve_atlas_language(
            structure_request="请按章节组织输出",
            source_metadata=metadata,
            subtitles_text="This is still English.",
        )

        self.assertEqual(resolved, "zh")

    def test_source_metadata_used_when_request_missing(self) -> None:
        metadata = SourceMetadata(title="日本語タイトル", introduction="これは説明です。")

        resolved = resolve_atlas_language(
            structure_request="",
            source_metadata=metadata,
            subtitles_text="This subtitle should not win.",
        )

        self.assertEqual(resolved, "ja")

    def test_subtitles_used_as_last_signal(self) -> None:
        resolved = resolve_atlas_language(
            structure_request="",
            source_metadata=None,
            subtitles_text="This subtitle text should determine the atlas language.",
        )

        self.assertEqual(resolved, "en")

    def test_unknown_falls_back_to_english(self) -> None:
        resolved = resolve_atlas_language(
            structure_request="",
            source_metadata=None,
            subtitles_text="1234 ---",
        )

        self.assertEqual(resolved, "en")
