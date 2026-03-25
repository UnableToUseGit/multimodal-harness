# CanonicalExecutionPlan

## 文档目标

本文档用于说明 `CanonicalExecutionPlan` 的设计目的、字段定义和使用约束。

## Schema 概览

- 名称：`CanonicalExecutionPlan`
- 主要职责：表达 canonical workflow 的整体执行计划
- 实现形式：`dataclass`

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `planner_confidence` | `float` | 否 | `0.25` | 规划阶段置信度 |
| `genre_distribution` | `dict[str, float]` | 否 | `{"other": 1.0}` | 内容类型分布 |
| `segmentation_specification` | `SegmentationSpecification` | 否 | 工厂默认值 | 切分规范 |
| `caption_specification` | `CaptionSpecification` | 否 | 工厂默认值 | caption 规范 |
| `chunk_size_sec` | `int` | 否 | `600` | chunk 长度 |
| `chunk_overlap_sec` | `int` | 否 | `20` | chunk 重叠长度 |

## 字段说明

### `planner_confidence`

- 语义：表达规划阶段输出的整体置信度。
- 约束：通常应在 `0.0` 到 `1.0` 之间。
- 注意事项：该值反映规划可靠性，不是单段边界置信度。

### `genre_distribution`

- 语义：表达视频内容类型分布。
- 约束：键为 genre 名称，值为对应权重或概率。
- 注意事项：主要用于指导后续切分与 caption 行为。

### `segmentation_specification`

- 语义：定义切分阶段的完整策略。
- 约束：应为有效的 `SegmentationSpecification`。
- 注意事项：决定 canonical 切分方式。

### `caption_specification`

- 语义：定义 caption 阶段的完整策略。
- 约束：应为有效的 `CaptionSpecification`。
- 注意事项：决定标题与描述生成方式。

### `chunk_size_sec`

- 语义：定义长视频分块处理时的 chunk 长度。
- 约束：应为正整数。
- 注意事项：值过大可能提高单次处理成本。

### `chunk_overlap_sec`

- 语义：定义相邻 chunk 间的重叠长度。
- 约束：应为非负整数。
- 注意事项：用于降低跨 chunk 边界信息丢失风险。

## 校验规则与约束

- `planner_confidence` 应在合理范围内。
- `chunk_size_sec` 必须大于 `0`。
- `chunk_overlap_sec` 不应为负数，且通常小于 `chunk_size_sec`。

## 示例

```python
CanonicalExecutionPlan(
    planner_confidence=0.6,
    genre_distribution={"sports": 0.8, "other": 0.2},
    segmentation_specification=some_segmentation_specification,
    caption_specification=some_caption_specification,
    chunk_size_sec=600,
    chunk_overlap_sec=20,
)
```
