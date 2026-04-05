# CanonicalAtlas 数据模式

## 模块位置

- `src/video_atlas/schemas/canonical_atlas.py`

## 作用

`CanonicalAtlas` 是当前 canonical workflow 的最终结果对象。

它同时承担：

- 内存中的业务结果表示
- workspace 写盘的输入对象

## 当前核心字段

- `title`
- `duration`
- `abstract`
- `segments`
- `execution_plan`
- `atlas_dir`
- `relative_video_path`
- `relative_audio_path`
- `relative_subtitles_path`
- `relative_srt_file_path`
- `units`
- `source_info`
- `source_metadata`

## 语义说明

- `segments`
  - 最终结构结果
- `units`
  - Stage 1 基本单元
- `execution_plan`
  - 生成该 atlas 时使用的正式 plan
- `atlas_dir`
  - 当前 atlas 的落盘根目录
- `source_info` / `source_metadata`
  - 来源摘要与归一化来源元数据

## 当前设计特征

- `CanonicalAtlas` 同时适用于 text-only 和 video-backed 两类 workspace
- 当前 release 的 canonical 主线只维护 text-first 版本
