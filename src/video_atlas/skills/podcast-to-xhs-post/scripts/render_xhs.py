#!/usr/bin/env python3
"""Render reading-style Xiaohongshu body pages from a podcast-note Markdown file."""

from __future__ import annotations

import argparse
import asyncio
import base64
import html
import mimetypes
import re
import sys
from pathlib import Path

try:
    import markdown
    import yaml
except ImportError:  # pragma: no cover - exercised at runtime, not in unit tests
    markdown = None
    yaml = None


DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1440


def parse_markdown_file(file_path: str) -> dict[str, object]:
    markdown_path = Path(file_path).resolve()
    content = markdown_path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(content)
    metadata = resolve_media_paths(metadata, markdown_path.parent)
    intro, article = split_intro_and_article(body)
    return {
        "metadata": metadata,
        "intro": intro.strip(),
        "article": article.strip(),
    }


def parse_frontmatter(content: str) -> tuple[dict[str, object], str]:
    if not content.startswith("---"):
        return {}, content
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", content, re.DOTALL)
    if not match:
        return {}, content
    metadata = parse_yaml_mapping(match.group(1))
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


def resolve_media_paths(metadata: dict[str, object], base_dir: Path) -> dict[str, object]:
    resolved = dict(metadata)
    for key in ("intro_image", "cover_image", "image"):
        raw_value = resolved.get(key)
        if not raw_value:
            continue
        candidate = Path(str(raw_value)).expanduser()
        if not candidate.is_absolute():
            candidate = (base_dir / candidate).resolve()
        resolved[key] = str(candidate)
    return resolved


def split_intro_and_article(content: str) -> tuple[str, str]:
    parts = re.split(r"^\s*---\s*$", content, maxsplit=1, flags=re.MULTILINE)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def split_markdown_blocks(markdown_text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    in_code_fence = False
    fence_marker = ""

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_code_fence:
                in_code_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_code_fence = False
                fence_marker = ""
            current.append(line)
            continue

        if in_code_fence:
            current.append(line)
            continue

        if not stripped:
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue

        current.append(line)

    if current:
        blocks.append("\n".join(current).strip())
    return [block for block in blocks if block]


def split_oversized_block(block: str, *, max_chars: int = 180) -> list[str]:
    stripped = block.lstrip()
    if (
        stripped.startswith("#")
        or stripped.startswith(">")
        or stripped.startswith("```")
        or stripped.startswith("~~~")
        or stripped.startswith("- ")
        or stripped.startswith("* ")
        or re.match(r"^\d+\.\s", stripped)
        or "!["
        in stripped
    ):
        return [block]

    sentences = re.split(r"(?<=[。！？!?；;])", block)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        candidate = f"{current}{sentence}" if current else sentence
        if current and len(candidate) > max_chars:
            chunks.append(current.strip())
            current = sentence
        else:
            current = candidate
    if current.strip():
        chunks.append(current.strip())
    return chunks or [block]


def convert_markdown_to_html(markdown_text: str) -> str:
    if markdown is not None:
        return markdown.markdown(
            markdown_text,
            extensions=["extra", "tables", "nl2br", "sane_lists"],
        )
    return basic_markdown_to_html(markdown_text)


def basic_markdown_to_html(markdown_text: str) -> str:
    html_parts: list[str] = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("### "):
            html_parts.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("## "):
            html_parts.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("# "):
            html_parts.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("> "):
            html_parts.append(f"<blockquote>{html.escape(line[2:])}</blockquote>")
        else:
            escaped = html.escape(line)
            escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
            escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
            html_parts.append(f"<p>{escaped}</p>")
    return "\n".join(html_parts)


def generate_intro_html(
    intro_markdown: str,
    metadata: dict[str, object],
    *,
    width: int,
    height: int,
) -> str:
    intro_html = convert_markdown_to_html(intro_markdown)
    title = str(metadata.get("title") or "")
    source = str(metadata.get("source") or "")
    intro_image_path = first_existing_intro_image(metadata)
    if intro_image_path is not None:
        return generate_visual_intro_html(
            intro_html,
            metadata,
            intro_image_path,
            width=width,
            height=height,
        )
    return generate_text_intro_html(
        intro_html,
        metadata,
        width=width,
        height=height,
    )


def first_existing_intro_image(metadata: dict[str, object]) -> Path | None:
    for key in ("intro_image", "cover_image", "image"):
        raw_value = metadata.get(key)
        if not raw_value:
            continue
        candidate = Path(str(raw_value))
        if candidate.is_file():
            return candidate
    return None


def generate_text_intro_html(
    intro_html: str,
    metadata: dict[str, object],
    *,
    width: int,
    height: int,
) -> str:
    title = str(metadata.get("title") or "")
    source = str(metadata.get("source") or "")
    kicker = f'<div class="kicker">{title}</div>' if title else ""
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
      background: #f3efe8;
      color: #111827;
      font-family: "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
    }}
    .canvas {{
      width: 100%;
      height: 100%;
      padding: 44px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .paper {{
      width: 100%;
      height: 100%;
      background: #fffdf9;
      border-radius: 26px;
      padding: 72px 72px 64px;
      box-shadow: 0 16px 48px rgba(31, 41, 55, 0.10);
      display: flex;
      flex-direction: column;
    }}
    .kicker {{
      font-size: 28px;
      letter-spacing: 2px;
      text-transform: uppercase;
      color: #9a6b36;
      margin-bottom: 28px;
      font-weight: 700;
    }}
    .intro {{
      font-family: "Noto Serif SC", "Source Han Serif SC", "Songti SC", "STSong", "SimSun", serif;
      font-size: 37px;
      line-height: 1.82;
      color: #1f2937;
      flex: 1;
    }}
    .intro h1, .intro h2, .intro h3 {{
      font-size: 60px;
      line-height: 1.22;
      margin: 0 0 28px;
      color: #111827;
    }}
    .intro p {{
      margin: 0 0 26px;
    }}
    .source {{
      margin-top: 28px;
      font-size: 26px;
      color: #6b7280;
    }}
  </style>
</head>
<body>
  <div class="canvas">
    <div class="paper">
      {kicker}
      <div class="intro">{intro_html}</div>
      {source_line}
    </div>
  </div>
</body>
</html>"""


def generate_visual_intro_html(
    intro_html: str,
    metadata: dict[str, object],
    intro_image_path: Path,
    *,
    width: int,
    height: int,
) -> str:
    title = str(metadata.get("title") or "")
    source = str(metadata.get("source") or "")
    subtitle = str(metadata.get("subtitle") or "")
    kicker = f'<div class="kicker">{title}</div>' if title else ""
    subtitle_line = f'<div class="subtitle">{subtitle}</div>' if subtitle else ""
    source_line = f'<div class="source">From: {source}</div>' if source else ""
    image_uri = image_path_to_data_uri(intro_image_path)
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
      background: #f3efe8;
      color: #111827;
      font-family: "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
    }}
    .canvas {{
      width: 100%;
      height: 100%;
      padding: 44px;
    }}
    .paper {{
      width: 100%;
      height: 100%;
      background: #fffdf9;
      border-radius: 26px;
      box-shadow: 0 16px 48px rgba(31, 41, 55, 0.10);
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }}
    .hero {{
      height: 56%;
      background: #ddd;
    }}
    .hero img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }}
    .intro-copy {{
      flex: 1;
      padding: 34px 52px 42px;
      display: flex;
      flex-direction: column;
      min-height: 0;
    }}
    .kicker {{
      font-size: 24px;
      letter-spacing: 1.8px;
      text-transform: uppercase;
      color: #9a6b36;
      margin-bottom: 16px;
      font-weight: 700;
    }}
    .subtitle {{
      margin: 12px 0 20px;
      font-size: 24px;
      color: #6b7280;
      line-height: 1.5;
    }}
    .intro {{
      font-family: "Noto Serif SC", "Source Han Serif SC", "Songti SC", "STSong", "SimSun", serif;
      font-size: 27px;
      line-height: 1.7;
      color: #1f2937;
      flex: 1;
      overflow: hidden;
    }}
    .intro h1, .intro h2, .intro h3 {{
      font-size: 54px;
      line-height: 1.2;
      margin: 0 0 18px;
      color: #111827;
    }}
    .intro p {{
      margin: 0 0 18px;
    }}
    .source {{
      margin-top: 12px;
      font-size: 22px;
      color: #6b7280;
    }}
  </style>
</head>
<body>
  <div class="canvas">
    <div class="paper">
      <div class="hero"><img src="{image_uri}" alt=""></div>
      <div class="intro-copy">
        {kicker}
        <div class="intro">{intro_html}</div>
        {subtitle_line}
        {source_line}
      </div>
    </div>
  </div>
</body>
</html>"""


def image_path_to_data_uri(path: Path) -> str:
    mime_type, _encoding = mimetypes.guess_type(path.name)
    mime_type = mime_type or "image/jpeg"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{payload}"


def generate_body_page_html(
    blocks: list[str],
    *,
    page_number: int,
    width: int,
    height: int,
) -> str:
    article_html = "\n".join(convert_markdown_to_html(block) for block in blocks)
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
      background: #f3efe8;
      color: #111827;
      font-family: "Noto Serif SC", "Source Han Serif SC", "Songti SC", "STSong", "SimSun", serif;
    }}
    .canvas {{
      width: 100%;
      height: 100%;
      padding: 44px;
    }}
    .paper {{
      width: 100%;
      height: 100%;
      background: #fffdf9;
      border-radius: 26px;
      box-shadow: 0 16px 48px rgba(31, 41, 55, 0.10);
      overflow: hidden;
      position: relative;
    }}
    .page-body {{
      position: absolute;
      inset: 0;
      padding: 74px 76px 118px;
      overflow: hidden;
    }}
    .page-body-inner {{
      width: 100%;
    }}
    .page-body-inner h1,
    .page-body-inner h2,
    .page-body-inner h3 {{
      font-family: "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
      color: #111827;
      font-weight: 800;
      letter-spacing: 0.3px;
      margin: 28px 0 20px;
      line-height: 1.3;
    }}
    .page-body-inner h1 {{ font-size: 54px; }}
    .page-body-inner h2 {{ font-size: 44px; }}
    .page-body-inner h3 {{ font-size: 36px; }}
    .page-body-inner p,
    .page-body-inner li,
    .page-body-inner blockquote {{
      font-size: 36px;
      line-height: 1.82;
      color: #1f2937;
    }}
    .page-body-inner p {{
      margin: 0 0 24px;
    }}
    .page-body-inner ul,
    .page-body-inner ol {{
      margin: 0 0 24px 34px;
    }}
    .page-body-inner strong {{
      font-family: "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
      color: #111827;
      font-weight: 800;
    }}
    .page-body-inner em {{
      color: #7c2d12;
      font-style: normal;
    }}
    .page-body-inner blockquote {{
      margin: 26px 0;
      padding: 18px 22px;
      border-left: 6px solid #d97706;
      background: #fff8eb;
      border-radius: 0 12px 12px 0;
    }}
    .page-body-inner img {{
      display: block;
      max-width: 100%;
      margin: 28px auto;
      border-radius: 18px;
    }}
    .page-number {{
      position: absolute;
      right: 74px;
      bottom: 44px;
      font-family: "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
      font-size: 28px;
      color: #9ca3af;
      letter-spacing: 1px;
    }}
  </style>
</head>
<body>
  <div class="canvas">
    <div class="paper">
      <div class="page-body">
        <div class="page-body-inner">{article_html}</div>
      </div>
      <div class="page-number">{page_number:02d}</div>
    </div>
  </div>
</body>
</html>"""


async def _new_page(width: int, height: int, dpr: int):
    from playwright.async_api import async_playwright

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch()
    page = await browser.new_page(
        viewport={"width": width, "height": height},
        device_scale_factor=dpr,
    )
    return playwright, browser, page


async def page_blocks_fit(
    page,
    blocks: list[str],
    *,
    width: int,
    height: int,
) -> bool:
    html = generate_body_page_html(blocks, page_number=1, width=width, height=height)
    await page.set_content(html, wait_until="load")
    await page.wait_for_timeout(50)
    return await page.evaluate(
        """() => {
            const viewport = document.querySelector('.page-body');
            const inner = document.querySelector('.page-body-inner');
            if (!viewport || !inner) return false;
            return inner.scrollHeight <= viewport.clientHeight + 2;
        }"""
    )


async def screenshot_html(
    page,
    html: str,
    output_path: Path,
    *,
    width: int,
    height: int,
) -> None:
    await page.set_content(html, wait_until="load")
    await page.wait_for_timeout(80)
    await page.screenshot(path=str(output_path), clip={"x": 0, "y": 0, "width": width, "height": height})


async def paginate_body(
    page,
    blocks: list[str],
    *,
    width: int,
    height: int,
) -> list[list[str]]:
    pages: list[list[str]] = []
    current: list[str] = []

    pending = list(blocks)
    while pending:
        block = pending.pop(0)
        candidate = current + [block]
        fits = await page_blocks_fit(page, candidate, width=width, height=height)
        if fits:
            current = candidate
            continue

        if current:
            pages.append(current)
            current = []
            pending.insert(0, block)
            continue

        split_blocks = split_oversized_block(block)
        if len(split_blocks) == 1:
            current = [block]
            pages.append(current)
            current = []
        else:
            pending = split_blocks + pending

    if current:
        pages.append(current)
    return pages


async def run(args: argparse.Namespace) -> int:
    parsed = parse_markdown_file(args.markdown_file)
    intro = str(parsed["intro"])
    article = str(parsed["article"])
    if not intro:
        raise RuntimeError("未找到引导页内容。请在 frontmatter 之后先写引导页，再用 --- 分隔正文主体。")
    if not article:
        raise RuntimeError("未找到正文主体内容。请在引导页之后用 --- 分隔正文主体。")

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    playwright, browser, page = await _new_page(args.width, args.height, args.dpr)
    try:
        intro_html = generate_intro_html(
            intro,
            parsed["metadata"],  # type: ignore[arg-type]
            width=args.width,
            height=args.height,
        )
        await screenshot_html(
            page,
            intro_html,
            output_dir / "intro.png",
            width=args.width,
            height=args.height,
        )

        blocks = split_markdown_blocks(article)
        pages = await paginate_body(page, blocks, width=args.width, height=args.height)
        for index, page_blocks in enumerate(pages, start=1):
            html = generate_body_page_html(
                page_blocks,
                page_number=index,
                width=args.width,
                height=args.height,
            )
            await screenshot_html(
                page,
                html,
                output_dir / f"page_{index}.png",
                width=args.width,
                height=args.height,
            )
    finally:
        await browser.close()
        await playwright.stop()

    print(f"Rendered intro.png and {len(pages)} body pages -> {output_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render reading-style Xiaohongshu body pages for podcast notes.")
    parser.add_argument("markdown_file")
    parser.add_argument("-o", "--output-dir", default=".")
    parser.add_argument("-w", "--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--dpr", type=int, default=2)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return asyncio.run(run(args))
    except RuntimeError as exc:
        print(f"渲染失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
