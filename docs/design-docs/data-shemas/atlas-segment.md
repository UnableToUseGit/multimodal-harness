# AtlasSegment

## 文档目标

本文档用于说明 `AtlasSegment` 的设计目的、字段定义和使用约束。

## Schema 概览

- 名称：`AtlasSegment`
- 主要职责：表达 atlas 中的标准片段对象
- 实现形式：`dataclass`

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `segment_id` | `str` | 是 | 无 | 片段标识 |
| `title` | `str` | 是 | 无 | 片段标题 |
| `start_time` | `float` | 是 | 无 | 起始时间 |
| `end_time` | `float` | 是 | 无 | 结束时间 |
| `summary` | `str` | 是 | 无 | 摘要 |
| `caption` | `str` | 是 | 无 | 详细描述 |
| `subtitles_text` | `str` | 是 | 无 | 片段字幕 |
| `folder_name` | `str` | 是 | 无 | 片段目录名 |
| `relative_clip_path` | `Path \| None` | 否 | `None` | 相对 clip 路径 |
| `relative_subtitles_path` | `Path \| None` | 否 | `None` | 相对字幕路径 |

## 字段说明

### `segment_id`

- 语义：片段在 atlas 中的稳定标识。
- 约束：应在同一 atlas 内唯一。
- 注意事项：下游映射和衍生通常依赖该字段。

### `title`

- 语义：片段的可读标题。
- 约束：应为非空字符串。
- 注意事项：用于展示和人工理解。

### `start_time` / `end_time`

- 语义：定义片段的时间范围。
- 约束：`start_time < end_time`。
- 注意事项：`duration` 由两者推导，不单独存储。

### `summary`

- 语义：片段的简要摘要。
- 约束：应为可读文本。
- 注意事项：用于快速浏览和全局汇总。

### `caption`

- 语义：片段的详细描述。
- 约束：应为可读文本。
- 注意事项：通常比 `summary` 更细。

### `subtitles_text`

- 语义：片段对应的字幕文本。
- 约束：可为空字符串。
- 注意事项：现在作为正式字段存在，不再依赖额外 artifacts。

### `folder_name`

- 语义：片段在 atlas 目录中的目录名。
- 约束：应适合作为稳定目录名使用。
- 注意事项：通常由 `segment_id`、标题和 `HH:MM:SS-HH:MM:SS` 形式的时间范围组合生成。

### `relative_clip_path`

- 语义：片段 clip 的相对路径。
- 约束：可为空。
- 注意事项：当未落盘时可为空。

### `relative_subtitles_path`

- 语义：片段字幕文件的相对路径。
- 约束：可为空。
- 注意事项：当无字幕或未落盘时可为空。

## 校验规则与约束

- `segment_id` 应唯一。
- `start_time` 必须小于 `end_time`。
- `folder_name` 应与 atlas 目录约定兼容。

## 示例

```python
AtlasSegment(
    segment_id="seg_0001",
    title="Opening",
    start_time=0.0,
    end_time=30.0,
    summary="Opening summary",
    caption="Opening detail",
    subtitles_text="...",
    folder_name="seg0001-opening-00:00:00-00:00:30",
)
```
