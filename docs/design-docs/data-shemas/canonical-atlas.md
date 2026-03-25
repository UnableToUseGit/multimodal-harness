# CanonicalAtlas

## 文档目标

本文档用于说明 `CanonicalAtlas` 的设计目的、字段定义和使用约束。

## Schema 概览

- 名称：`CanonicalAtlas`
- 主要职责：表达 canonical workflow 的标准输出结果
- 实现形式：`dataclass`

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `title` | `str` | 是 | 无 | atlas 标题 |
| `duration` | `float` | 是 | 无 | 视频总时长 |
| `abstract` | `str` | 是 | 无 | 全局摘要 |
| `segments` | `list[AtlasSegment]` | 是 | 无 | 片段列表 |
| `execution_plan` | `CanonicalExecutionPlan` | 是 | 无 | 执行计划 |
| `atlas_dir` | `Path` | 是 | 无 | atlas 根目录 |
| `relative_video_path` | `Path` | 是 | 无 | 原视频相对路径 |
| `relative_audio_path` | `Path \| None` | 否 | `None` | 音频相对路径 |
| `relative_subtitles_path` | `Path \| None` | 否 | `None` | 字幕 markdown 相对路径 |
| `relative_srt_file_path` | `Path \| None` | 否 | `None` | 原始 srt 相对路径 |

## 字段说明

### `title`

- 语义：整个 canonical atlas 的标题。
- 约束：应为可读文本。
- 注意事项：通常来自全局聚合阶段。

### `duration`

- 语义：原视频总时长。
- 约束：应为非负数。
- 注意事项：通常与 `segments` 的覆盖范围保持一致。

### `abstract`

- 语义：对整个视频内容的全局概述。
- 约束：应为可读文本。
- 注意事项：服务于上层快速理解。

### `segments`

- 语义：atlas 中的标准片段列表。
- 约束：元素应为有效的 `AtlasSegment`。
- 注意事项：这是 atlas 的主体内容。

### `execution_plan`

- 语义：记录 canonical workflow 的执行规划。
- 约束：应为有效的 `CanonicalExecutionPlan`。
- 注意事项：用于解释 atlas 是如何生成的。

### `atlas_dir`

- 语义：该 atlas 对应的根目录。
- 约束：应为目录路径而非文件路径。
- 注意事项：writer 与 review 都依赖这个字段。

### `relative_video_path`

- 语义：原视频在 atlas 根目录下的相对路径。
- 约束：应为相对路径。
- 注意事项：用于后续 clip 裁剪和 review。

### `relative_audio_path` / `relative_subtitles_path` / `relative_srt_file_path`

- 语义：记录相关辅助文件的相对路径。
- 约束：可为空。
- 注意事项：并非所有 canonical atlas 都会包含这些文件。

## 校验规则与约束

- `segments` 中每个 `segment_id` 应唯一。
- `relative_*` 路径应相对于 `atlas_dir`。
- `execution_plan` 应与 atlas 生成方式保持一致。

## 示例

```python
CanonicalAtlas(
    title="Match Overview",
    duration=3600.0,
    abstract="A structured overview of the full video.",
    segments=[...],
    execution_plan=some_execution_plan,
    atlas_dir=Path("/tmp/canonical"),
    relative_video_path=Path("video.mp4"),
)
```
