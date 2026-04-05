# Persistence 模块设计

## 文档目标

本文档说明当前 canonical workspace 的写盘逻辑和模块职责。

## 模块位置

- `src/video_atlas/persistence/writers.py`

## 模块职责

persistence 模块负责：

- 将 `CanonicalAtlas` 写为稳定目录结构
- 写出根级 README、units、segments
- 在有视频时裁剪 unit 对应的视频 clip
- 提供基础的文本 / JSON 写盘函数

它不负责：

- 生成 atlas 语义内容
- source acquisition
- workflow planning

## 当前两种写盘路径

### 1. Video-backed canonical workspace

当 request 中有视频资产时，workflow 使用 `CanonicalAtlasWriter`。

其行为包括：

- 写根级 `README.md`
- 写 `units/<unit>/README.md`
- 写 `segments/<segment>/README.md`
- 提取 `video_clip.mp4`
- 可选写 `SUBTITLES.md`

### 2. Text-only canonical workspace

当 request 中没有视频资产时，workflow 走 text-only workspace 写盘分支。

其行为包括：

- 写根级 `README.md`
- 写根级 `SUBTITLES.md`
- 写 `units/`
- 写 `segments/`
- 不生成 clip

## 关键辅助能力

模块还提供：

- `write_text_to(...)`
- `write_json_to(...)`
- `copy_to(...)`
- `extract_clip(...)`
- `slugify_segment_title(...)`

## 当前稳定约定

- workspace 是当前主要外部表示
- `slugify_segment_title` 应支持 Unicode，不只支持英文
- persistence 写盘应与 `atlas-layout/canonical-atlas-directory.md` 保持一致
