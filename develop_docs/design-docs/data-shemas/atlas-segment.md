# AtlasSegment 数据模式

## 模块位置

- `src/video_atlas/schemas/canonical_atlas.py`

## 作用

`AtlasSegment` 表示 Stage 2 structure composition 之后的最终结构单元。

它是：

- `CanonicalAtlas.segments` 的核心元素
- workspace `segments/` 的内容来源

## 当前字段

- `segment_id`
- `unit_ids`
- `title`
- `start_time`
- `end_time`
- `summary`
- `composition_rationale`
- `folder_name`
- `caption`
- `subtitles_text`
- `relative_clip_path`
- `relative_subtitles_path`

## 语义说明

- `unit_ids`
  - 当前 segment 由哪些 units 组成
- `composition_rationale`
  - structure composer 给出的组合理由
- `summary`
  - 当前 segment 的整体概述

## 当前来源

由 `text_first_canonical/structure_composition.py` 生成。
