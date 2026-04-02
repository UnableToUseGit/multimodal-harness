# YouTube Source Acquisition CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 canonical atlas 增加标准 YouTube 视频页面 URL 输入能力，使 agent 只需传入 URL，即可由 CLI 内部完成视频下载、元数据抓取、字幕优先复用与本地转写回退。

**Architecture:** 新增独立的 `source_acquisition` 层，将外部 URL 输入标准化为本地视频、可选字幕和 source metadata，再由现有 canonical workflow 消费这些标准化输入。第一阶段默认使用 `yt-dlp` 作为 YouTube acquisition backend，但 acquisition 层接口保持可替换，不把具体下载器能力泄漏到 CLI 或 workflow。CLI 负责接线，persistence 负责稳定落盘 `SOURCE_INFO.json` / `SOURCE_METADATA.json`，测试分为稳定单测/集成测试和受环境约束的联网 E2E acquisition 测试。

**Tech Stack:** Python 3.10+, dataclasses, unittest, pathlib, `yt-dlp`, existing canonical workflow, existing persistence helpers

---

## 文件结构

### 新增文件

- `src/video_atlas/source_acquisition/__init__.py`
  - 导出 acquisition 公共入口与 schema
- `src/video_atlas/source_acquisition/models.py`
  - 定义 `SourceAcquisitionResult`、`SourceInfoRecord` 等稳定 schema
- `src/video_atlas/source_acquisition/youtube.py`
  - 实现标准 YouTube 视频页面 URL 校验、基于 `yt-dlp` 的下载、metadata 抓取和字幕获取
- `tests/test_source_acquisition_models.py`
  - acquisition schema 与序列化单测
- `tests/test_youtube_acquisition.py`
  - YouTube 获取逻辑单测与回退逻辑测试
- `tests/test_source_acquisition_e2e.py`
  - 真实联网 acquisition 验证测试

### 重点修改文件

- `pyproject.toml`
  - 增加 `yt-dlp` 依赖
- `src/video_atlas/schemas/canonical_atlas.py`
  - 给 `CanonicalAtlas` 增加 source metadata 字段
- `src/video_atlas/schemas/__init__.py`
  - 导出新增 schema
- `src/video_atlas/persistence/writers.py`
  - 写出 `SOURCE_INFO.json` / `SOURCE_METADATA.json`
- `src/video_atlas/persistence/__init__.py`
  - 导出新增 source metadata 写出 helper
- `src/video_atlas/review/workspace_loader.py`
  - 读取根目录 source metadata 文件
- `src/video_atlas/cli/main.py`
  - 增加 `canonical create` 命令与 `--youtube-url`
- `src/video_atlas/config/models.py`
  - 增加 acquisition runtime config 与 loader
- `src/video_atlas/config/__init__.py`
  - 导出新增 config 类型与 loader
- `tests/test_cli.py`
  - 扩展 CLI 行为测试
- `tests/test_config_loading.py`
  - 覆盖 acquisition 配置加载
- `tests/test_review_loader.py`
  - 验证 source metadata 读取
- `docs/design-docs/atlas-layout/canonical-atlas-directory.md`
  - 更新 canonical 根目录 source metadata 契约
- `docs/design-docs/module-design/persistence.md`
  - 补充 source metadata 写出职责
- `docs/design-docs/module-design/review.md`
  - 补充 source metadata 读取职责
- `docs/index.md`
  - 若新增正式文档入口，补全索引

---

### Task 1: 定义 source acquisition schema 与 canonical source metadata 契约

**Files:**
- Create: `src/video_atlas/source_acquisition/models.py`
- Create: `src/video_atlas/source_acquisition/__init__.py`
- Modify: `src/video_atlas/schemas/canonical_atlas.py`
- Modify: `src/video_atlas/schemas/__init__.py`
- Test: `tests/test_source_acquisition_models.py`

- [ ] **Step 1: 写失败测试，固定 acquisition schema 与 canonical source metadata 字段**

```python
from pathlib import Path
import tempfile
import unittest

from video_atlas.schemas import CanonicalAtlas, CanonicalExecutionPlan
from video_atlas.source_acquisition import SourceAcquisitionResult, SourceInfoRecord


class SourceAcquisitionModelsTest(unittest.TestCase):
    def test_source_info_record_exposes_expected_fields(self) -> None:
        record = SourceInfoRecord(
            source_type="youtube",
            source_url="https://www.youtube.com/watch?v=abc123",
            canonical_source_url="https://www.youtube.com/watch?v=abc123",
            subtitle_source="youtube_caption",
            subtitle_fallback_required=False,
            acquisition_timestamp="2026-04-01T00:00:00Z",
        )

        self.assertEqual(record.source_type, "youtube")
        self.assertEqual(record.subtitle_source, "youtube_caption")
        self.assertFalse(record.subtitle_fallback_required)

    def test_source_acquisition_result_tracks_local_assets_and_metadata(self) -> None:
        result = SourceAcquisitionResult(
            source_info=SourceInfoRecord(
                source_type="youtube",
                source_url="https://www.youtube.com/watch?v=abc123",
                canonical_source_url="https://www.youtube.com/watch?v=abc123",
                subtitle_source="youtube_caption",
                subtitle_fallback_required=False,
                acquisition_timestamp="2026-04-01T00:00:00Z",
            ),
            local_video_path=Path("/tmp/video.mp4"),
            local_subtitles_path=Path("/tmp/subtitles.srt"),
            source_metadata={"title": "Sample Title", "channel": "Sample Channel"},
            artifacts={"info_json": "source/info.json"},
        )

        self.assertEqual(result.local_video_path.name, "video.mp4")
        self.assertEqual(result.source_metadata["title"], "Sample Title")

    def test_canonical_atlas_accepts_optional_source_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            atlas = CanonicalAtlas(
                title="Example",
                duration=12.0,
                abstract="Summary",
                segments=[],
                execution_plan=CanonicalExecutionPlan(),
                atlas_dir=Path(tmpdir),
                relative_video_path=Path("video.mp4"),
                source_info={"source_type": "youtube"},
                source_metadata={"title": "Example"},
            )

        self.assertEqual(atlas.source_info["source_type"], "youtube")
        self.assertEqual(atlas.source_metadata["title"], "Example")
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_source_acquisition_models -v
```

Expected:
- `ImportError` 或 `TypeError`，因为 `source_acquisition` schema 或 `CanonicalAtlas.source_info` / `source_metadata` 尚不存在

- [ ] **Step 3: 实现最小 schema 与导出**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SourceInfoRecord:
    source_type: str
    source_url: str
    subtitle_source: str | None = None
    acquisition_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class SourceAcquisitionResult:
    source_info: SourceInfoRecord
    local_video_path: Path
    local_subtitles_path: Path | None = None
    source_metadata: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
```

```python
@dataclass
class CanonicalAtlas:
    ...
    units: list[AtlasUnit] = field(default_factory=list)
    source_info: dict[str, str] = field(default_factory=dict)
    source_metadata: dict[str, object] = field(default_factory=dict)
```

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_source_acquisition_models -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_atlas/source_acquisition/__init__.py src/video_atlas/source_acquisition/models.py src/video_atlas/schemas/canonical_atlas.py src/video_atlas/schemas/__init__.py tests/test_source_acquisition_models.py
git commit -m "feat: add source acquisition schemas"
```

---

### Task 2: 增加 acquisition 配置与 YouTube URL 校验/字幕优先级逻辑

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/video_atlas/config/models.py`
- Modify: `src/video_atlas/config/__init__.py`
- Create: `src/video_atlas/source_acquisition/youtube.py`
- Test: `tests/test_config_loading.py`
- Test: `tests/test_youtube_acquisition.py`

- [ ] **Step 1: 写失败测试，固定 config 加载与 URL 校验行为**

```python
import json
import tempfile
import unittest
from pathlib import Path

from video_atlas.config import load_canonical_pipeline_config
from video_atlas.source_acquisition.youtube import (
    YouTubeVideoAcquirer,
    is_supported_youtube_watch_url,
    choose_subtitle_candidate,
)


class YouTubeAcquisitionLogicTest(unittest.TestCase):
    def test_load_canonical_pipeline_config_reads_acquisition_runtime(self) -> None:
        payload = {
            "planner": {"provider": "openai_compatible", "model_name": "planner"},
            "runtime": {},
            "acquisition": {
                "enabled": True,
                "prefer_youtube_subtitles": True,
                "youtube_output_template": "%(id)s.%(ext)s",
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "canonical.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            config = load_canonical_pipeline_config(path)

        self.assertTrue(config.acquisition.enabled)
        self.assertTrue(config.acquisition.prefer_youtube_subtitles)
        self.assertEqual(config.acquisition.youtube_output_template, "%(id)s.%(ext)s")

    def test_supports_only_standard_watch_urls(self) -> None:
        self.assertTrue(is_supported_youtube_watch_url("https://www.youtube.com/watch?v=abc123xyz89"))
        self.assertFalse(is_supported_youtube_watch_url("https://youtu.be/abc123xyz89"))
        self.assertFalse(is_supported_youtube_watch_url("https://www.youtube.com/playlist?list=demo"))

    def test_choose_subtitle_candidate_prefers_manual_then_auto(self) -> None:
        subtitles = [
            {"kind": "automatic", "ext": "vtt", "language": "en"},
            {"kind": "manual", "ext": "vtt", "language": "en"},
        ]

        selected = choose_subtitle_candidate(subtitles)

        self.assertEqual(selected["kind"], "manual")
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_config_loading tests.test_youtube_acquisition -v
```

Expected:
- acquisition config 缺失或 YouTube helper 不存在

- [ ] **Step 3: 实现 acquisition config、依赖与 helper**

```toml
[project]
dependencies = [
    "json-repair>=0.30.0",
    "numpy>=1.24",
    "opencv-python>=4.8",
    "pydantic>=2,<3",
    "yt-dlp>=2025.3.31",
]
```

```python
@dataclass
class AcquisitionRuntimeConfig:
    enabled: bool = True
    prefer_youtube_subtitles: bool = True
    youtube_output_template: str = "%(id)s.%(ext)s"


@dataclass
class CanonicalPipelineConfig:
    ...
    acquisition: AcquisitionRuntimeConfig = field(default_factory=AcquisitionRuntimeConfig)
```

```python
from urllib.parse import parse_qs, urlparse


def is_supported_youtube_watch_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc not in {"www.youtube.com", "youtube.com"}:
        return False
    if parsed.path != "/watch":
        return False
    return bool(parse_qs(parsed.query).get("v"))


def choose_subtitle_candidate(candidates: list[dict[str, str]]) -> dict[str, str] | None:
    if not candidates:
        return None
    manual = [item for item in candidates if item.get("kind") == "manual"]
    automatic = [item for item in candidates if item.get("kind") == "automatic"]
    ordered = manual or automatic or candidates
    return ordered[0]
```

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_config_loading tests.test_youtube_acquisition -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/video_atlas/config/models.py src/video_atlas/config/__init__.py src/video_atlas/source_acquisition/youtube.py tests/test_config_loading.py tests/test_youtube_acquisition.py
git commit -m "feat: add youtube acquisition config and helpers"
```

---

### Task 3: 实现 YouTube acquisition 主体与本地字幕回退信号

**Files:**
- Modify: `src/video_atlas/source_acquisition/youtube.py`
- Test: `tests/test_youtube_acquisition.py`

- [ ] **Step 1: 写失败测试，固定下载器调用与回退语义**

```python
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from video_atlas.source_acquisition.youtube import YouTubeVideoAcquirer


class YouTubeVideoAcquirerTest(unittest.TestCase):
    @patch("video_atlas.source_acquisition.youtube.YoutubeDL")
    def test_acquire_uses_downloaded_subtitles_when_available(self, youtube_dl_cls) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "video.mp4").write_bytes(b"video")
            (root / "captions.en.vtt").write_text("WEBVTT", encoding="utf-8")
            downloader = youtube_dl_cls.return_value.__enter__.return_value
            downloader.extract_info.return_value = {
                "id": "abc123xyz89",
                "title": "Example",
                "webpage_url": "https://www.youtube.com/watch?v=abc123xyz89",
                "requested_downloads": [{"filepath": str(root / "video.mp4")}],
                "subtitles": {"en": [{"ext": "vtt", "filepath": str(root / "captions.en.vtt")}]},
                "automatic_captions": {},
            }

            acquirer = YouTubeVideoAcquirer()
            result = acquirer.acquire("https://www.youtube.com/watch?v=abc123xyz89", root)

        self.assertEqual(result.local_video_path.name, "video.mp4")
        self.assertIsNotNone(result.local_subtitles_path)
        self.assertEqual(result.source_info.subtitle_source, "youtube_caption")
        self.assertFalse(result.source_info.subtitle_fallback_required)

    @patch("video_atlas.source_acquisition.youtube.YoutubeDL")
    def test_acquire_requests_transcriber_fallback_when_no_subtitles(self, youtube_dl_cls) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "video.mp4").write_bytes(b"video")
            downloader = youtube_dl_cls.return_value.__enter__.return_value
            downloader.extract_info.return_value = {
                "id": "abc123xyz89",
                "title": "Example",
                "webpage_url": "https://www.youtube.com/watch?v=abc123xyz89",
                "requested_downloads": [{"filepath": str(root / "video.mp4")}],
                "subtitles": {},
                "automatic_captions": {},
            }

            acquirer = YouTubeVideoAcquirer()
            result = acquirer.acquire("https://www.youtube.com/watch?v=abc123xyz89", root)

        self.assertIsNone(result.local_subtitles_path)
        self.assertEqual(result.source_info.subtitle_source, "missing")
        self.assertTrue(result.source_info.subtitle_fallback_required)
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_youtube_acquisition -v
```

Expected:
- `YouTubeVideoAcquirer.acquire` 不存在或行为不符合预期

- [ ] **Step 3: 实现最小 acquisition 主体**

```python
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL

from .models import SourceAcquisitionResult, SourceInfoRecord


class YouTubeVideoAcquirer:
    def __init__(self, prefer_youtube_subtitles: bool = True, output_template: str = "%(id)s.%(ext)s") -> None:
        self.prefer_youtube_subtitles = prefer_youtube_subtitles
        self.output_template = output_template

    def acquire(self, youtube_url: str, output_dir: Path) -> SourceAcquisitionResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        options = {
            "outtmpl": str(output_dir / self.output_template),
            "writesubtitles": self.prefer_youtube_subtitles,
            "writeautomaticsub": self.prefer_youtube_subtitles,
            "skip_download": False,
            "quiet": True,
        }
        with YoutubeDL(options) as downloader:
            info = downloader.extract_info(youtube_url, download=True)

        video_path = Path(info["requested_downloads"][0]["filepath"])
        subtitle_path = self._resolve_downloaded_subtitle_path(info)
        subtitle_source = "youtube_caption" if subtitle_path is not None else "missing"

        return SourceAcquisitionResult(
            source_info=SourceInfoRecord(
                source_type="youtube",
                source_url=youtube_url,
                canonical_source_url=info.get("webpage_url", youtube_url),
                subtitle_source=subtitle_source,
                subtitle_fallback_required=subtitle_path is None,
                acquisition_timestamp=datetime.now(timezone.utc).isoformat(),
            ),
            local_video_path=video_path,
            local_subtitles_path=subtitle_path,
            source_metadata=dict(info),
            artifacts={},
        )
```

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_youtube_acquisition -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_atlas/source_acquisition/youtube.py tests/test_youtube_acquisition.py
git commit -m "feat: implement youtube acquisition"
```

---

### Task 4: 写出并加载 canonical source metadata

**Files:**
- Modify: `src/video_atlas/persistence/writers.py`
- Modify: `src/video_atlas/persistence/__init__.py`
- Modify: `src/video_atlas/review/workspace_loader.py`
- Test: `tests/test_review_loader.py`
- Test: `tests/test_workspace_writers.py`

- [ ] **Step 1: 写失败测试，固定 source metadata 文件契约与 review 读取**

```python
import json
import tempfile
import unittest
from pathlib import Path

from video_atlas.review import load_review_workspace


class ReviewWorkspaceSourceMetadataTest(unittest.TestCase):
    def test_load_review_workspace_reads_source_info_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Canonical\n", encoding="utf-8")
            (root / "SOURCE_INFO.json").write_text(
                json.dumps({"source_type": "youtube", "source_url": "https://www.youtube.com/watch?v=abc123"}),
                encoding="utf-8",
            )
            (root / "SOURCE_METADATA.json").write_text(
                json.dumps({"title": "Example Title", "channel": "Example Channel"}),
                encoding="utf-8",
            )

            workspace = load_review_workspace(root, workspace_id="canonical")

        self.assertEqual(workspace.source_info["source_type"], "youtube")
        self.assertEqual(workspace.source_metadata["title"], "Example Title")
```

```python
class CanonicalWriterSourceMetadataTest(unittest.TestCase):
    def test_writer_persists_source_info_and_source_metadata(self) -> None:
        ...
        self.assertTrue((atlas_dir / "SOURCE_INFO.json").exists())
        self.assertTrue((atlas_dir / "SOURCE_METADATA.json").exists())
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_review_loader tests.test_workspace_writers -v
```

Expected:
- `ReviewWorkspace` 缺少 `source_info` / `source_metadata`，或 writer 尚未写出文件

- [ ] **Step 3: 实现 source metadata 写出与加载**

```python
def write_json_to(destination: str | Path, relative_path: str | Path, payload: dict[str, object]) -> Path:
    return write_text_to(destination, relative_path, json.dumps(payload, indent=2, ensure_ascii=False))


class CanonicalAtlasWriter:
    def write(self, atlas: CanonicalAtlas) -> None:
        ...
        if atlas.source_info:
            write_json_to(atlas_dir, "SOURCE_INFO.json", atlas.source_info)
        if atlas.source_metadata:
            write_json_to(atlas_dir, "SOURCE_METADATA.json", atlas.source_metadata)
```

```python
@dataclass
class ReviewWorkspace:
    ...
    source_info: dict[str, Any] = field(default_factory=dict)
    source_metadata: dict[str, Any] = field(default_factory=dict)
```

```python
workspace = ReviewWorkspace(
    ...
    source_info=_read_json_if_exists((root / "SOURCE_INFO.json") if (root / "SOURCE_INFO.json").exists() else None) or {},
    source_metadata=_read_json_if_exists((root / "SOURCE_METADATA.json") if (root / "SOURCE_METADATA.json").exists() else None) or {},
)
```

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_review_loader tests.test_workspace_writers -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_atlas/persistence/writers.py src/video_atlas/persistence/__init__.py src/video_atlas/review/workspace_loader.py tests/test_review_loader.py tests/test_workspace_writers.py
git commit -m "feat: persist canonical source metadata"
```

---

### Task 5: 增加 `canonical create` CLI 并接入 acquisition -> workflow 主链

**Files:**
- Modify: `src/video_atlas/cli/main.py`
- Modify: `src/video_atlas/config/models.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: 写失败测试，固定 CLI 参数与主链调度行为**

```python
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from video_atlas.cli.main import build_parser, main


class CanonicalCreateCliTest(unittest.TestCase):
    def test_build_parser_supports_canonical_create_with_youtube_url(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["canonical", "create", "--youtube-url", "https://www.youtube.com/watch?v=abc123xyz89", "--output-dir", "/tmp/out"]
        )

        self.assertEqual(args.command, "canonical")
        self.assertEqual(args.canonical_command, "create")
        self.assertEqual(args.youtube_url, "https://www.youtube.com/watch?v=abc123xyz89")

    @patch("video_atlas.cli.main.CanonicalAtlasWorkflow")
    @patch("video_atlas.cli.main.YouTubeVideoAcquirer")
    @patch("video_atlas.cli.main.build_generator")
    @patch("video_atlas.cli.main.build_transcriber")
    @patch("video_atlas.cli.main.load_canonical_pipeline_config")
    def test_main_runs_canonical_create_from_youtube_url(
        self,
        load_config,
        build_transcriber,
        build_generator,
        acquirer_cls,
        workflow_cls,
    ) -> None:
        ...
        exit_code = main(
            [
                "canonical",
                "create",
                "--youtube-url",
                "https://www.youtube.com/watch?v=abc123xyz89",
                "--output-dir",
                str(output_dir),
                "--config",
                "configs/canonical/default.json",
            ]
        )

        self.assertEqual(exit_code, 0)
        workflow.create.assert_called_once()
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_cli -v
```

Expected:
- parser 不支持 `canonical create`
- 或主链函数不存在

- [ ] **Step 3: 实现最小 CLI 主链**

```python
canonical_parser = subparsers.add_parser("canonical", help="Canonical atlas commands.")
canonical_subparsers = canonical_parser.add_subparsers(dest="canonical_command")
create_parser = canonical_subparsers.add_parser("create", help="Create a canonical atlas.")
create_parser.add_argument("--youtube-url")
create_parser.add_argument("--output-dir", required=True)
create_parser.add_argument("--config", default="configs/canonical/default.json")
create_parser.add_argument("--structure-request", default="")
```

```python
def _run_canonical_create(args) -> int:
    from pathlib import Path

    from video_atlas.config import build_generator, build_transcriber, load_canonical_pipeline_config
    from video_atlas.source_acquisition.youtube import YouTubeVideoAcquirer
    from video_atlas.workflows.canonical_atlas_workflow import CanonicalAtlasWorkflow

    config = load_canonical_pipeline_config(args.config)
    acquirer = YouTubeVideoAcquirer(
        prefer_youtube_subtitles=config.acquisition.prefer_youtube_subtitles,
        output_template=config.acquisition.youtube_output_template,
    )
    acquisition = acquirer.acquire(args.youtube_url, Path(args.output_dir))
    workflow = CanonicalAtlasWorkflow(
        planner=build_generator(config.planner),
        segmentor=build_generator(config.segmentor) if config.segmentor else None,
        text_segmentor=build_generator(config.text_segmentor) if config.text_segmentor else None,
        multimodal_segmentor=build_generator(config.multimodal_segmentor) if config.multimodal_segmentor else None,
        structure_composer=build_generator(config.structure_composer) if config.structure_composer else None,
        captioner=build_generator(config.captioner) if config.captioner else None,
        transcriber=build_transcriber(config.transcriber),
        generate_subtitles_if_missing=config.runtime.generate_subtitles_if_missing,
        text_chunk_size_sec=config.runtime.text_chunk_size_sec,
        text_chunk_overlap_sec=config.runtime.text_chunk_overlap_sec,
        multimodal_chunk_size_sec=config.runtime.multimodal_chunk_size_sec,
        multimodal_chunk_overlap_sec=config.runtime.multimodal_chunk_overlap_sec,
        caption_with_subtitles=config.runtime.caption_with_subtitles,
    )
    atlas, _ = workflow.create(
        output_dir=Path(args.output_dir),
        source_video_path=acquisition.local_video_path,
        source_srt_file_path=acquisition.local_subtitles_path,
        structure_request=args.structure_request,
    )
    atlas.source_info = acquisition.source_info.__dict__
    atlas.source_metadata = acquisition.source_metadata
    return 0
```

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_cli -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_atlas/cli/main.py src/video_atlas/config/models.py tests/test_cli.py
git commit -m "feat: add canonical create cli for youtube input"
```

---

### Task 6: 把 acquisition 结果正确写回 canonical atlas 对象并固定主流程回归测试

**Files:**
- Modify: `src/video_atlas/workflows/canonical_atlas/pipeline.py`
- Test: `tests/test_canonical_two_stage_pipeline.py`

- [ ] **Step 1: 写失败测试，固定 pipeline 对 source metadata 的透传**

```python
import tempfile
import unittest
from pathlib import Path

from video_atlas.schemas import CanonicalAtlas


class CanonicalPipelineSourceMetadataTest(unittest.TestCase):
    def test_pipeline_preserves_source_info_and_source_metadata(self) -> None:
        ...
        atlas, _ = workflow.create(
            output_dir=output_dir,
            source_video_path=video_path,
            source_srt_file_path=srt_path,
            structure_request="",
            source_info={"source_type": "youtube", "source_url": "https://www.youtube.com/watch?v=abc123xyz89"},
            source_metadata={"title": "Example"},
        )

        self.assertEqual(atlas.source_info["source_type"], "youtube")
        self.assertEqual(atlas.source_metadata["title"], "Example")
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_canonical_two_stage_pipeline -v
```

Expected:
- `create(...)` 不接受 `source_info` / `source_metadata`

- [ ] **Step 3: 实现 pipeline 透传**

```python
def create(
    self,
    output_dir: Path,
    source_video_path: Path,
    source_srt_file_path: Path | None = None,
    structure_request: str | None = None,
    verbose: bool = False,
    source_info: dict[str, object] | None = None,
    source_metadata: dict[str, object] | None = None,
) -> CanonicalAtlas:
    ...
    atlas = CanonicalAtlas(
        ...
        source_info=dict(source_info or {}),
        source_metadata=dict(source_metadata or {}),
    )
```

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_canonical_two_stage_pipeline -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_atlas/workflows/canonical_atlas/pipeline.py tests/test_canonical_two_stage_pipeline.py
git commit -m "feat: thread source metadata through canonical pipeline"
```

---

### Task 7: 增加真实联网 acquisition E2E 测试与使用文档更新

**Files:**
- Create: `tests/test_source_acquisition_e2e.py`
- Modify: `docs/design-docs/atlas-layout/canonical-atlas-directory.md`
- Modify: `docs/design-docs/module-design/persistence.md`
- Modify: `docs/design-docs/module-design/review.md`
- Modify: `docs/index.md`

- [ ] **Step 1: 写 E2E 测试与文档更新**

```python
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from video_atlas.source_acquisition.youtube import YouTubeVideoAcquirer


class SourceAcquisitionE2ETest(unittest.TestCase):
    def test_can_acquire_real_youtube_video_when_enabled(self) -> None:
        youtube_url = os.environ.get("VIDEO_ATLAS_E2E_YOUTUBE_URL")
        if not youtube_url:
            self.skipTest("VIDEO_ATLAS_E2E_YOUTUBE_URL is not set")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = YouTubeVideoAcquirer().acquire(youtube_url, Path(tmpdir))

        self.assertTrue(result.local_video_path.exists())
        self.assertEqual(result.source_info.source_type, "youtube")
        self.assertTrue(result.source_metadata)
```

文档更新要点：

```markdown
- `SOURCE_INFO.json`：记录 URL 来源、字幕来源与回退信息。
- `SOURCE_METADATA.json`：记录尽可能完整的 YouTube 元数据。
- review loader 应在根级读取这两个文件，供后续展示和 agent 消费。
- 联网 E2E acquisition 测试通过 `VIDEO_ATLAS_E2E_YOUTUBE_URL` 显式开启，不作为默认稳定测试的一部分。
```

- [ ] **Step 2: 运行稳定测试，确认文档与测试文件无语法问题**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_source_acquisition_e2e -v
```

Expected:
- 若未设置 `VIDEO_ATLAS_E2E_YOUTUBE_URL`，显示 `skipped`
- 若已设置且网络可用，成功完成 acquisition

- [ ] **Step 3: 运行本阶段相关测试集合**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest \
  tests.test_source_acquisition_models \
  tests.test_youtube_acquisition \
  tests.test_config_loading \
  tests.test_cli \
  tests.test_review_loader \
  tests.test_workspace_writers \
  tests.test_canonical_two_stage_pipeline \
  tests.test_source_acquisition_e2e -v
```

Expected:
- 稳定测试 PASS
- 联网 E2E 在未设置环境变量时 SKIP，在设置后按环境条件执行

- [ ] **Step 4: Commit**

```bash
git add tests/test_source_acquisition_e2e.py docs/design-docs/atlas-layout/canonical-atlas-directory.md docs/design-docs/module-design/persistence.md docs/design-docs/module-design/review.md docs/index.md
git commit -m "docs: describe youtube source acquisition contracts"
```

---

## Self-Review

- Spec coverage:
  - YouTube 单视频页面 URL 支持：Task 2, Task 3, Task 5
  - 字幕优先复用与本地转写回退：Task 2, Task 3, Task 5
  - source metadata 稳定落盘：Task 1, Task 4, Task 6, Task 7
  - 正式 CLI：Task 5
  - 真实联网 E2E acquisition 测试：Task 7
- Placeholder scan:
  - 未保留 `TODO` / `TBD` / “后续补上” 之类占位语
- Type consistency:
  - 计划中的核心命名统一为 `SourceInfoRecord`、`SourceAcquisitionResult`、`source_info`、`source_metadata`
