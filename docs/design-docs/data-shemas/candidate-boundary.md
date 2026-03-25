# CandidateBoundary

## 文档目标

本文档用于说明 `CandidateBoundary` 的设计目的、字段定义和使用约束。

## Schema 概览

- 名称：`CandidateBoundary`
- 主要职责：表达边界检测阶段得到的候选切分点
- 实现形式：`dataclass`

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `timestamp` | `float` | 是 | 无 | 候选边界时间点 |
| `boundary_rationale` | `str` | 否 | `""` | 边界理由 |
| `evidence` | `list[str]` | 否 | `[]` | 支撑证据 |
| `confidence` | `float` | 否 | `0.0` | 置信度 |

## 字段说明

### `timestamp`

- 语义：表示候选边界在视频时间线上的位置。
- 约束：应为非负时间戳。
- 注意事项：这是候选点，不保证最终会被采纳。

### `boundary_rationale`

- 语义：解释为什么在该位置可能存在边界。
- 约束：可为空。
- 注意事项：主要用于调试、审查和后处理。

### `evidence`

- 语义：记录支撑该边界判断的证据类型。
- 约束：元素应来自允许的证据集合。
- 注意事项：可用于后续过滤和排序。

### `confidence`

- 语义：表达该候选边界的置信度。
- 约束：通常应在 `0.0` 到 `1.0` 之间。
- 注意事项：低置信度候选通常会被过滤。

## 校验规则与约束

- `timestamp` 必须是合法时间点。
- `confidence` 应在合理范围内。
- `evidence` 应只包含允许值。

## 示例

```python
CandidateBoundary(
    timestamp=124.5,
    boundary_rationale="A clear scene transition appears here.",
    evidence=["scene_change", "subtitle_shift"],
    confidence=0.82,
)
```
