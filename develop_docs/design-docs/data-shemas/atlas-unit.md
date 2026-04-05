# AtlasUnit 数据模式

## 模块位置

- `src/video_atlas/schemas/canonical_atlas.py`

## 作用

`AtlasUnit` 表示 Stage 1 text-first parsing 产出的稳定基本单元。

它是：

- 后续 structure composition 的直接输入
- workspace `units/` 的内容来源

## 当前字段

- `unit_id`
- `title`
- `start_time`
- `end_time`
- `summary`
- `caption`
- `subtitles_text`
- `folder_name`
- `relative_clip_path`
- `relative_subtitles_path`

## 语义说明

- `title`
  - 当前 unit 的简短标题
- `summary`
  - 当前 unit 的高层概述
- `caption`
  - 当前 unit 的更完整文字说明
- `subtitles_text`
  - unit 对应的字幕文本

## 当前来源

由 `text_first_canonical/parsing.py` 构造。
