# CanonicalCompositionResult

## 文档目标

本文档用于说明 `CanonicalCompositionResult` 的设计目的、字段定义和使用约束。

## Schema 概览

- 名称：`CanonicalCompositionResult`
- 主要职责：表达 canonical 两阶段结构中 Stage 2 的最终组合结果
- 实现形式：`dataclass`

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `title` | `str` | 是 | 无 | 最终 canonical atlas 标题 |
| `abstract` | `str` | 是 | 无 | 最终 canonical atlas 摘要 |
| `segments` | `list[AtlasSegment]` | 是 | 无 | 最终组合段列表 |
| `composition_rationale` | `str` | 否 | `""` | 全局组合说明 |
| `structure_request` | `str` | 否 | `""` | 用户对最终结构的显式要求 |

## 字段说明

### `title`

- 语义：最终 atlas 的全局标题。
- 约束：应适合目录浏览和人工 review。
- 注意事项：由 Stage 2 composer 依据 `units` 文本信息生成。

### `abstract`

- 语义：最终 atlas 的全局摘要。
- 约束：应概括整份 atlas 的总体结构和内容。
- 注意事项：应尽量与最终 `segments` 的组织方式保持一致。

### `segments`

- 语义：Stage 2 输出的最终组合段。
- 约束：每个 `AtlasSegment` 必须由若干 `AtlasUnit` 组成。
- 注意事项：实验期 `segments/` 目录会直接对应这里的结果。

### `composition_rationale`

- 语义：对最终结构选择的全局解释。
- 约束：应尽量简洁、可追踪。
- 注意事项：有助于 debug composer 为什么做出当前分组。

### `structure_request`

- 语义：用户对最终结构粒度或章节组织方式的显式要求。
- 约束：可为空字符串。
- 注意事项：Stage 2 应优先尊重该字段，但不应破坏 unit 顺序和完整性。

## 校验规则与约束

- `segments` 必须按 `AtlasUnit` 的原始顺序组合。
- 每个 `AtlasUnit` 必须恰好出现一次。
- 最终结构不应跳过、重复或重排 units。

## 示例

```python
CanonicalCompositionResult(
    title="A Lecture on Video Models",
    abstract="A structured explainer composed from several coherent units.",
    composition_rationale="Merged adjacent explanation blocks into stable chapters.",
    structure_request="Please keep the structure coarse.",
    segments=[...],
)
```
