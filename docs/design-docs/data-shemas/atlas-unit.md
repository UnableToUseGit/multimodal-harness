# AtlasUnit

## 文档目标

本文档用于说明 `AtlasUnit` 的设计目的、字段定义和使用约束。

## Schema 概览

- 名称：`AtlasUnit`
- 主要职责：表达 canonical 两阶段结构中的 Stage 1 基本单元
- 实现形式：`dataclass`

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `unit_id` | `str` | 是 | 无 | unit 标识 |
| `title` | `str` | 是 | 无 | unit 标题 |
| `start_time` | `float` | 是 | 无 | unit 起始时间 |
| `end_time` | `float` | 是 | 无 | unit 结束时间 |
| `summary` | `str` | 否 | `""` | unit 摘要 |
| `caption` | `str` | 否 | `""` | unit 详细描述 |
| `subtitles_text` | `str` | 否 | `""` | unit 范围内字幕文本 |
| `folder_name` | `str` | 否 | `""` | unit 落盘目录名 |
| `relative_clip_path` | `Path \| None` | 否 | `None` | 相对视频片段路径 |
| `relative_subtitles_path` | `Path \| None` | 否 | `None` | 相对字幕路径 |

## 字段说明

### `unit_id`

- 语义：Stage 1 基本单元的稳定标识。
- 约束：在同一 atlas 内应唯一。
- 注意事项：Stage 2 composer 会根据顺序和 `unit_id` 组合最终 segment。

### `title`

- 语义：unit 的局部标题。
- 约束：应尽量简短、稳定、可导航。
- 注意事项：这个标题是 Stage 1 的局部标题，不等同于最终 segment 标题。

### `start_time` / `end_time`

- 语义：unit 在原视频中的时间范围。
- 约束：`start_time < end_time`。
- 注意事项：writer 会根据时间范围生成目录和 README 信息。

### `summary` / `caption`

- 语义：描述 unit 的局部含义。
- 约束：应保留 unit 级别语义，不要上升为整段视频摘要。
- 注意事项：Stage 2 主要依赖这些文本信息做结构组合。

### `subtitles_text`

- 语义：unit 范围内的字幕文本。
- 约束：可为空字符串。
- 注意事项：文本叙事视频在 Stage 2 中会高度依赖该字段。

### `folder_name`

- 语义：unit 落盘目录名。
- 约束：应稳定、可读、可由 writer 再现。
- 注意事项：实验期目录通常会在 `units/` 下保存该目录。

## 校验规则与约束

- `unit_id` 必须唯一。
- `start_time` 必须小于 `end_time`.
- `folder_name` 若生成，应保持与 writer 约定一致。

## 示例

```python
AtlasUnit(
    unit_id="unit_0001",
    title="Opening Setup",
    start_time=0.0,
    end_time=18.0,
    summary="The opening setup and first topic introduction.",
    caption="A short opening block that introduces the topic.",
    subtitles_text="...",
    folder_name="unit-0001-opening-setup-00:00:00-00:00:18",
)
```
