import importlib.util
import unittest
from pathlib import Path


ROOT = Path("/share/project/minghao/Proj/VideoAFS/VideoEdit/development")
SCRIPT_DIR = ROOT / "src/video_atlas/skills/podcast-to-xhs-post/scripts"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


RENDER = _load_module("render_xhs", SCRIPT_DIR / "render_xhs.py")


class PodcastToXhsRenderScriptTest(unittest.TestCase):
    def test_parser_splits_intro_and_article_after_frontmatter(self):
        markdown_text = """---
title: "测试标题"
---

# 这是引导页

这里是引导页正文。

---

# 第一节

这里是正文。
"""
        metadata, body = RENDER.parse_frontmatter(markdown_text)
        intro, article = RENDER.split_intro_and_article(body)

        self.assertEqual(metadata["title"], "测试标题")
        self.assertIn("这是引导页", intro)
        self.assertIn("第一节", article)

    def test_parser_splits_blocks_without_cutting_paragraphs(self):
        article = """# 第一节

第一段内容。

第二段内容。

> 一段引用。
"""
        blocks = RENDER.split_markdown_blocks(article)
        self.assertEqual(
            blocks,
            ["# 第一节", "第一段内容。", "第二段内容。", "> 一段引用。"],
        )

    def test_generate_body_page_html_includes_page_number(self):
        html = RENDER.generate_body_page_html(
            ["# 标题", "这里是正文。"],
            page_number=3,
            width=1080,
            height=1440,
        )
        self.assertIn("03", html)
        self.assertIn("这里是正文", html)

    def test_generate_intro_html_strips_heading_and_omits_metadata_lines(self):
        html = RENDER.generate_intro_html(
            "# 为什么这期播客值得看\n\n导语第一段。\n\n导语第二段。",
            {
                "title": "播客封面",
                "subtitle": "副标题",
                "source": "测试来源",
            },
            width=1080,
            height=1440,
        )
        self.assertNotIn("为什么这期播客值得看", html)
        self.assertIn("播客封面", html)
        self.assertNotIn("副标题", html)
        self.assertNotIn("测试来源", html)
        self.assertIn("导语第一段", html)

    def test_generate_text_intro_html_renders_plain_intro_copy(self):
        html = RENDER.generate_text_intro_html(
            "<p>导语</p>",
            {},
            width=1080,
            height=1440,
        )
        self.assertIn("导语", html)
        self.assertNotIn("From:", html)

    def test_is_unsplittable_block_marks_quotes_as_unsplittable(self):
        self.assertTrue(
            RENDER.is_unsplittable_block("> 一段很长的引用。即使很长也不应拆开。")
        )


class PodcastToXhsPaginationTest(unittest.IsolatedAsyncioTestCase):
    async def test_paginate_body_splits_paragraph_when_page_tail_cannot_fit(self):
        paragraph = "一个很长的段落。"

        original_measure = RENDER.measure_block_height

        async def fake_measure_block_height(_page, block, *, width, height):
            if block.startswith("# "):
                return 300
            if block == paragraph:
                return 1200
            return len(block) * 150

        try:
            RENDER.measure_block_height = fake_measure_block_height

            pages = await RENDER.paginate_body(
                page=None,
                blocks=["# 第一节", paragraph],
                width=1080,
                height=1440,
            )
        finally:
            RENDER.measure_block_height = original_measure

        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0][0], "# 第一节")
        self.assertEqual("".join(pages[0][1:]) + "".join(pages[1]), paragraph)
        self.assertNotEqual(pages[0][1], paragraph)

    async def test_paginate_body_keeps_title_and_carries_paragraph_across_pages(self):
        paragraph = "甲" * 160

        original_measure = RENDER.measure_block_height

        async def fake_measure_block_height(_page, block, *, width, height):
            if block.startswith("# "):
                return 300
            return len(block) * 10

        try:
            RENDER.measure_block_height = fake_measure_block_height

            pages = await RENDER.paginate_body(
                page=None,
                blocks=["# 第一节", paragraph],
                width=1080,
                height=1440,
            )
        finally:
            RENDER.measure_block_height = original_measure

        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0][0], "# 第一节")
        self.assertEqual("".join(pages[0][1:]) + "".join(pages[1]), paragraph)
        self.assertNotEqual(pages[0][1], paragraph)


if __name__ == "__main__":
    unittest.main()
