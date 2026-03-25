# DerivationResultInfo

## 文档目标

本文档用于说明 `DerivationResultInfo` 的设计目的、字段定义和使用约束。

## Schema 概览

- 名称：`DerivationResultInfo`
- 主要职责：记录 derived atlas 的来源映射与派生原因
- 实现形式：`dataclass`

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `derived_atlas_segment_count` | `int` | 否 | `0` | derived 片段数量 |
| `derivation_reason` | `dict[str, DerivationPolicy]` | 否 | `{}` | 每个 derived 片段对应的派生策略 |
| `derivation_source` | `dict[str, str]` | 否 | `{}` | 每个 derived 片段对应的 source segment id |

## 字段说明

### `derived_atlas_segment_count`

- 语义：记录最终生成的 derived 片段数量。
- 约束：应为非负整数。
- 注意事项：通常与 `len(derived_atlas.segments)` 一致。

### `derivation_reason`

- 语义：记录每个 derived 片段的派生策略。
- 约束：key 应为 `derived_segment_id`。
- 注意事项：用于解释片段为什么被这样派生。

### `derivation_source`

- 语义：记录每个 derived 片段对应的 source segment。
- 约束：key 应为 `derived_segment_id`，value 应为 source `segment_id`。
- 注意事项：用于 source mapping 和 review。

## 校验规则与约束

- 两个映射字段的 key 应与 derived segment 标识保持一致。
- `derived_atlas_segment_count` 应与映射规模和结果规模保持一致。

## 示例

```python
DerivationResultInfo(
    derived_atlas_segment_count=1,
    derivation_reason={"derived_seg_0001": some_policy},
    derivation_source={"derived_seg_0001": "seg_0001"},
)
```
