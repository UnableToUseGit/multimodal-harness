#!/usr/bin/env python3
"""Render a Xiaohongshu podcast-note cover image from Markdown frontmatter."""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - exercised at runtime, not in unit tests
    yaml = None


DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1440

THEME_BACKGROUNDS = {
    "default": "linear-gradient(180deg, #efe7db 0%, #f8f4ed 100%)",
    "playful-geometric": "linear-gradient(180deg, #8b5cf6 0%, #f472b6 100%)",
    "neo-brutalism": "linear-gradient(180deg, #ff4757 0%, #feca57 100%)",
    "botanical": "linear-gradient(180deg, #4a7c59 0%, #8fbc8f 100%)",
    "professional": "linear-gradient(180deg, #1f4ed8 0%, #4f7cff 100%)",
    "retro": "linear-gradient(180deg, #b45309 0%, #f59e0b 100%)",
    "terminal": "linear-gradient(180deg, #0d1117 0%, #21262d 100%)",
    "sketch": "linear-gradient(180deg, #555555 0%, #999999 100%)",
}

TITLE_GRADIENTS = {
    "default": "linear-gradient(180deg, #1f2937 0%, #6b7280 100%)",
    "playful-geometric": "linear-gradient(180deg, #6d28d9 0%, #ec4899 100%)",
    "neo-brutalism": "linear-gradient(180deg, #111827 0%, #ff4757 100%)",
    "botanical": "linear-gradient(180deg, #1f2937 0%, #4a7c59 100%)",
    "professional": "linear-gradient(180deg, #172554 0%, #1d4ed8 100%)",
    "retro": "linear-gradient(180deg, #78350f 0%, #d97706 100%)",
    "terminal": "linear-gradient(180deg, #39d353 0%, #58a6ff 100%)",
    "sketch": "linear-gradient(180deg, #111827 0%, #6b7280 100%)",
}


def parse_markdown_file(file_path: str) -> dict[str, object]:
    content = Path(file_path).read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(content)
    return {"metadata": metadata, "body": body.strip()}


def parse_frontmatter(content: str) -> tuple[dict[str, object], str]:
    if not content.startswith("---"):
        return {}, content
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", content, re.DOTALL)
    if not match:
        return {}, content
    metadata_block = match.group(1)
    metadata = parse_yaml_mapping(metadata_block)
    return metadata, content[match.end() :]


def parse_yaml_mapping(metadata_block: str) -> dict[str, object]:
    if yaml is not None:
        try:
            return yaml.safe_load(metadata_block) or {}
        except yaml.YAMLError:
            return {}

    metadata: dict[str, object] = {}
    for raw_line in metadata_block.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("\"'")
    return metadata


def _title_font_size(title: str, width: int) -> int:
    title_len = len(title)
    if title_len <= 8:
        return int(width * 0.118)
    if title_len <= 14:
        return int(width * 0.098)
    if title_len <= 22:
        return int(width * 0.082)
    return int(width * 0.067)


def generate_cover_html(
    metadata: dict[str, object],
    *,
    theme: str,
    width: int,
    height: int,
) -> str:
    emoji = str(metadata.get("emoji") or "🎧")
    title = str(metadata.get("title") or "播客笔记")
    subtitle = str(metadata.get("subtitle") or "")
    source = str(metadata.get("source") or "")
    background = THEME_BACKGROUNDS.get(theme, THEME_BACKGROUNDS["default"])
    title_gradient = TITLE_GRADIENTS.get(theme, TITLE_GRADIENTS["default"])
    title_size = _title_font_size(title, width)
    source_line = f'<div class="source">From: {source}</div>' if source else ""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width={width}, height={height}">
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      width: {width}px;
      height: {height}px;
      overflow: hidden;
      font-family: "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
    }}
    .canvas {{
      width: 100%;
      height: 100%;
      background: {background};
      padding: {int(width * 0.055)}px;
    }}
    .paper {{
      width: 100%;
      height: 100%;
      background: #f7f4ef;
      border-radius: 28px;
      padding: {int(width * 0.08)}px;
      display: flex;
      flex-direction: column;
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.12);
    }}
    .emoji {{
      font-size: {int(width * 0.15)}px;
      line-height: 1;
      margin-bottom: {int(height * 0.035)}px;
    }}
    .title {{
      font-family: "Noto Serif SC", "Source Han Serif SC", "Songti SC", "STSong", "SimSun", serif;
      font-size: {title_size}px;
      line-height: 1.28;
      font-weight: 700;
      letter-spacing: 0.5px;
      background: {title_gradient};
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: {int(height * 0.045)}px;
      word-break: break-word;
    }}
    .subtitle {{
      font-size: {int(width * 0.05)}px;
      line-height: 1.5;
      color: #4b5563;
      margin-top: auto;
    }}
    .source {{
      margin-top: {int(height * 0.018)}px;
      font-size: {int(width * 0.042)}px;
      color: #374151;
    }}
  </style>
</head>
<body>
  <div class="canvas">
    <div class="paper">
      <div class="emoji">{emoji}</div>
      <div class="title">{title}</div>
      <div class="subtitle">{subtitle}</div>
      {source_line}
    </div>
  </div>
</body>
</html>"""


async def render_html_to_png(
    html: str,
    output_path: Path,
    *,
    width: int,
    height: int,
    dpr: int,
) -> None:
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=dpr,
        )
        await page.set_content(html, wait_until="load")
        await page.screenshot(path=str(output_path), clip={"x": 0, "y": 0, "width": width, "height": height})
        await browser.close()


async def run(args: argparse.Namespace) -> int:
    parsed = parse_markdown_file(args.markdown_file)
    html = generate_cover_html(
        parsed["metadata"],  # type: ignore[arg-type]
        theme=args.theme,
        width=args.width,
        height=args.height,
    )
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    await render_html_to_png(
        html,
        output_dir / "cover.png",
        width=args.width,
        height=args.height,
        dpr=args.dpr,
    )
    print(f"Rendered cover.png -> {output_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render Xiaohongshu cover image for podcast notes.")
    parser.add_argument("markdown_file")
    parser.add_argument("-o", "--output-dir", default=".")
    parser.add_argument(
        "-t",
        "--theme",
        default="default",
        choices=sorted(THEME_BACKGROUNDS.keys()),
    )
    parser.add_argument("-w", "--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--dpr", type=int, default=2)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return asyncio.run(run(args))
    except RuntimeError as exc:
        print(f"渲染失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
