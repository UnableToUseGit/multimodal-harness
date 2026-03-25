# FinalizedSegment

## 文档目标

本文档用于说明 `FinalizedSegment` 的设计目的、字段定义和使用约束。

## Schema 概览

- 名称：`FinalizedSegment`
- 主要职责：表达经过边界后处理后的最终切分片段
- 实现形式：`dataclass`

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `start_time` | `float` | 是 | 无 | 片段起始时间 |
| `end_time` | `float` | 是 | 无 | 片段结束时间 |
| `boundary_rationale` | `str` | 否 | `""` | 边界理由 |
| `boundary_confidence` | `float` | 否 | `0.0` | 边界置信度 |
| `evidence` | `list[str]` | 否 | `[]` | 支撑证据 |
| `refinement_needed` | `bool` | 否 | `False` | 是否需要进一步细化 |

## 字段说明

### `start_time`

- 语义：片段在时间线上的起点。
- 约束：应小于 `end_time`。
- 注意事项：由边界检测与后处理共同决定。

### `end_time`

- 语义：片段在时间线上的终点。
- 约束：应大于 `start_time`。
- 注意事项：与 `start_time` 一起定义最终片段范围。

### `boundary_rationale`

- 语义：描述该片段边界形成的原因。
- 约束：可为空。
- 注意事项：主要用于解释性输出和调试。

### `boundary_confidence`

- 语义：描述该片段边界可信度。
- 约束：通常应在 `0.0` 到 `1.0` 之间。
- 注意事项：反映边界质量，而不是 caption 质量。

### `evidence`

- 语义：列出支撑该边界的证据。
- 约束：元素应来自允许集合。
- 注意事项：可能同时包含主证据和次证据。

### `refinement_needed`

- 语义：标识该片段是否需要进一步细化。
- 约束：布尔值。
- 注意事项：通常由片段长度和策略阈值决定。

## 校验规则与约束

- `start_time` 必须小于 `end_time`。
- `boundary_confidence` 应在合理范围内。

## 示例

```python
FinalizedSegment(
    start_time=30.0,
    end_time=75.0,
    boundary_rationale="The action shifts into a new stage.",
    boundary_confidence=0.73,
    evidence=["action_shift"],
    refinement_needed=False,
)
```
