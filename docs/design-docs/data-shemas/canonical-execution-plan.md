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
| `genres` | `list[str]` | 否 | `["other"]` | planner 输出的原始有序视频类型列表 |
| `concise_description` | `str` | 否 | `""` | 对整个视频的简要介绍 |
| `segmentation_specification` | `SegmentationSpecification` | 否 | 工厂默认值 | 切分规范 |
| `caption_specification` | `CaptionSpecification` | 否 | 工厂默认值 | caption 规范 |
| `chunk_size_sec` | `int` | 否 | `600` | chunk 长度 |
| `chunk_overlap_sec` | `int` | 否 | `20` | chunk 重叠长度 |

## 字段说明

### `planner_confidence`

- 语义：表达规划阶段输出的整体置信度。
- 约束：通常应在 `0.0` 到 `1.0` 之间。
- 注意事项：该值反映规划可靠性，不是单段边界置信度。

### `genres`

- 语义：表达 planner 判断出的主要视频类型列表。
- 约束：为按重要性排序的 genre 字符串列表。
- 注意事项：保留 planner 原始有序列表，不再转换为权重分布。

### `concise_description`

- 语义：提供对整个视频的简要介绍。
- 约束：应为简短、可读的描述性文本。
- 注意事项：主要作为后续分割和 caption 过程的先验信息。

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
    genres=["sports_event", "other"],
    concise_description="A sports broadcast that follows the live match, replays, and post-match analysis.",
    segmentation_specification=some_segmentation_specification,
    caption_specification=some_caption_specification,
    chunk_size_sec=600,
    chunk_overlap_sec=20,
)
```
