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

    def test_generate_text_intro_html_contains_source_and_title(self):
        html = RENDER.generate_text_intro_html(
            "<h1>为什么这期播客值得看</h1><p>导语</p>",
            {
                "title": "播客封面",
                "subtitle": "副标题",
                "source": "测试来源",
            },
            width=1080,
            height=1440,
        )
        self.assertIn("播客封面", html)
        self.assertIn("From: 测试来源", html)


if __name__ == "__main__":
    unittest.main()
