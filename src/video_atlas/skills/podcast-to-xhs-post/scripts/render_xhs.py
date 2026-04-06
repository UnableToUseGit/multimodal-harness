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
CANVAS_PADDING = 44
BODY_PADDING_TOP = 74
BODY_PADDING_RIGHT = 76
BODY_PADDING_BOTTOM = 118
BODY_PADDING_LEFT = 76
SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = SCRIPT_DIR.parent / "assets"


def load_asset(name: str) -> str:
    return (ASSETS_DIR / name).read_text(encoding="utf-8")


def render_asset_template(name: str, **values: object) -> str:
    template = load_asset(name)
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"__{key.upper()}__", str(value))
    return rendered


def render_style_asset(name: str, **values: object) -> str:
    return render_asset_template(name, **values)


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


def is_unsplittable_block(block: str) -> bool:
    stripped = block.lstrip()
    return (
        stripped.startswith("#")
        or stripped.startswith(">")
        or stripped.startswith("```")
        or stripped.startswith("~~~")
        or stripped.startswith("- ")
        or stripped.startswith("* ")
        or re.match(r"^\d+\.\s", stripped) is not None
        or "![" in stripped
    )


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
    normalized_intro = normalize_intro_markdown(intro_markdown)
    intro_html = convert_markdown_to_html(normalized_intro)
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


def normalize_intro_markdown(intro_markdown: str) -> str:
    lines = intro_markdown.splitlines()
    normalized: list[str] = []
    heading_removed = False
    for line in lines:
        stripped = line.strip()
        if not heading_removed and re.match(r"^#{1,6}\s+", stripped):
            heading_removed = True
            continue
        normalized.append(line)
    return "\n".join(normalized).strip()


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
    title_html = f'<div class="cover-title">{html.escape(title)}</div>' if title else ""
    return render_asset_template(
        "intro_text.html",
        width=width,
        height=height,
        css=render_style_asset("intro_text.css", width=width, height=height),
        title_html=title_html,
        intro_html=intro_html,
    )


def generate_visual_intro_html(
    intro_html: str,
    metadata: dict[str, object],
    intro_image_path: Path,
    *,
    width: int,
    height: int,
) -> str:
    title = str(metadata.get("title") or "")
    title_html = f'<div class="cover-title">{html.escape(title)}</div>' if title else ""
    image_uri = image_path_to_data_uri(intro_image_path)
    return render_asset_template(
        "intro_visual.html",
        width=width,
        height=height,
        css=render_style_asset("intro_visual.css", width=width, height=height),
        image_uri=image_uri,
        title_html=title_html,
        intro_html=intro_html,
    )


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
    return render_asset_template(
        "body_page.html",
        width=width,
        height=height,
        css=render_style_asset(
            "body_page.css",
            width=width,
            height=height,
            body_padding_top=BODY_PADDING_TOP,
            body_padding_right=BODY_PADDING_RIGHT,
            body_padding_bottom=BODY_PADDING_BOTTOM,
            body_padding_left=BODY_PADDING_LEFT,
        ),
        article_html=article_html,
        page_number=f"{page_number:02d}",
    )


async def _new_page(width: int, height: int, dpr: int):
    from playwright.async_api import async_playwright

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch()
    page = await browser.new_page(
        viewport={"width": width, "height": height},
        device_scale_factor=dpr,
    )
    return playwright, browser, page


def body_content_width(width: int) -> int:
    return width - CANVAS_PADDING * 2 - BODY_PADDING_LEFT - BODY_PADDING_RIGHT


def body_content_height(height: int) -> int:
    return height - CANVAS_PADDING * 2 - BODY_PADDING_TOP - BODY_PADDING_BOTTOM


def generate_measure_block_html(
    block: str,
    *,
    width: int,
) -> str:
    block_html = convert_markdown_to_html(block)
    content_width = body_content_width(width)
    return render_asset_template(
        "measure_block.html",
        width=content_width,
        css=render_style_asset("measure_block.css", width=content_width),
        block_html=block_html,
    )


async def measure_block_height(
    page,
    block: str,
    *,
    width: int,
    height: int,
) -> int:
    html = generate_measure_block_html(block, width=width)
    await page.set_content(html, wait_until="load")
    await page.wait_for_timeout(50)
    return await page.evaluate(
        """() => {
            const inner = document.querySelector('.measure-inner');
            if (!inner) return 0;
            const rect = inner.getBoundingClientRect();
            return Math.ceil(rect.height);
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
    current_height = 0
    available_height = body_content_height(height)
    block_height_cache: dict[str, int] = {}

    async def get_block_height(block: str) -> int:
        cached = block_height_cache.get(block)
        if cached is not None:
            return cached
        measured = await measure_block_height(page, block, width=width, height=height)
        block_height_cache[block] = measured
        return measured

    def refine_split_index(block: str, index: int) -> int:
        lower_bound = max(1, index - 24)
        for probe in range(index, lower_bound - 1, -1):
            if block[probe - 1] in "，。！？；：,.!?;:、）)】]」』 ":
                return probe
        return index

    async def split_block_for_available_height(
        block: str,
        remaining_height: int,
    ) -> tuple[str, str] | None:
        if remaining_height <= 0 or is_unsplittable_block(block) or len(block) < 2:
            return None

        full_height = await get_block_height(block)
        if full_height <= remaining_height:
            return None

        low = 1
        high = len(block) - 1
        best = 0
        while low <= high:
            mid = (low + high) // 2
            candidate = block[:mid]
            candidate_height = await get_block_height(candidate)
            if candidate_height <= remaining_height:
                best = mid
                low = mid + 1
            else:
                high = mid - 1

        if best <= 0:
            return None

        split_index = refine_split_index(block, best)
        if split_index <= 0 or split_index >= len(block):
            split_index = best

        prefix = block[:split_index]
        suffix = block[split_index:]
        if not prefix or not suffix:
            return None
        return prefix, suffix

    pending = list(blocks)
    while pending:
        block = pending.pop(0)
        block_height = await get_block_height(block)
        if current_height + block_height <= available_height:
            current.append(block)
            current_height += block_height
            continue

        if current:
            if not is_unsplittable_block(block):
                split_result = await split_block_for_available_height(
                    block,
                    available_height - current_height,
                )
                if split_result is not None:
                    prefix, suffix = split_result
                    pages.append(current + [prefix])
                    current = []
                    current_height = 0
                    pending = [suffix] + pending
                    continue
            pages.append(current)
            current = []
            current_height = 0
            pending.insert(0, block)
            continue

        if is_unsplittable_block(block):
            current = [block]
            current_height = block_height
            pages.append(current)
            current = []
            current_height = 0
        else:
            split_result = await split_block_for_available_height(block, available_height)
            if split_result is None:
                current = [block]
                current_height = block_height
                pages.append(current)
                current = []
                current_height = 0
            else:
                prefix, suffix = split_result
                pages.append([prefix])
                pending = [suffix] + pending

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
