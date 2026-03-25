# DerivedSegmentDraft

## 文档目标

本文档用于说明 `DerivedSegmentDraft` 的设计目的、字段定义和使用约束。

## Schema 概览

- 名称：`DerivedSegmentDraft`
- 主要职责：表达 derived workflow 在 derivation 阶段产出的中间结果
- 实现形式：`dataclass`

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `derived_segment_id` | `str` | 是 | 无 | 目标 derived 片段标识 |
| `source_segment_id` | `str` | 是 | 无 | 来源 canonical 片段标识 |
| `policy` | `DerivationPolicy` | 是 | 无 | 派生策略 |
| `start_time` | `float` | 是 | 无 | refined 起始时间 |
| `end_time` | `float` | 是 | 无 | refined 结束时间 |
| `title` | `str` | 是 | 无 | 派生标题 |
| `summary` | `str` | 是 | 无 | 派生摘要 |
| `caption` | `str` | 是 | 无 | 派生详细描述 |
| `subtitles_text` | `str` | 是 | 无 | refined 范围内的字幕 |

## 字段说明

### `derived_segment_id`

- 语义：中间结果对应的 derived 片段标识。
- 约束：应在同一批结果中唯一。
- 注意事项：aggregation 会基于它组装最终 `AtlasSegment`。

### `source_segment_id`

- 语义：记录它来自哪个 canonical segment。
- 约束：应为合法的 source `segment_id`。
- 注意事项：用于 source mapping。

### `policy`

- 语义：记录当前 draft 的派生策略。
- 约束：应为有效的 `DerivationPolicy`。
- 注意事项：aggregation 会把它写入 `DerivationResultInfo`。

### `start_time` / `end_time`

- 语义：记录 refined 后的绝对时间范围。
- 约束：`start_time < end_time`。
- 注意事项：该范围已经过 source segment 边界约束。

### `title` / `summary` / `caption`

- 语义：记录派生后的文本结果。
- 约束：应为可读文本。
- 注意事项：这些字段由 caption 阶段生成。

### `subtitles_text`

- 语义：记录 refined 范围内裁剪后的字幕。
- 约束：可为空字符串。
- 注意事项：后续 aggregation 会将其放入最终 `AtlasSegment`。

## 校验规则与约束

- `start_time` 必须小于 `end_time`。
- `policy` 必须存在。
- `source_segment_id` 应能映射回 canonical atlas 中的片段。

## 示例

```python
DerivedSegmentDraft(
    derived_segment_id="derived_seg_0001",
    source_segment_id="seg_0001",
    policy=some_policy,
    start_time=5.0,
    end_time=15.0,
    title="Opening Setup",
    summary="The setup sequence needed for the task.",
    caption="A tighter clip showing the key setup action.",
    subtitles_text="...",
)
```
