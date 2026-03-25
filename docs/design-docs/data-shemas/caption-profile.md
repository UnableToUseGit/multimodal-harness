# CaptionProfile

## 文档目标

本文档用于说明 `CaptionProfile` 的设计目的、字段定义和使用约束。

## Schema 概览

- 名称：`CaptionProfile`
- 主要职责：定义片段标题与描述生成策略
- 实现形式：`dataclass`

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `caption_policy` | `str` | 是 | 无 | 描述生成策略 |
| `title_policy` | `str` | 是 | 无 | 标题生成策略 |

## 字段说明

### `caption_policy`

- 语义：定义 caption/detail 的表达粒度与写作方向。
- 约束：应为稳定、可复用的策略说明。
- 注意事项：它描述生成规则，而不是具体生成结果。

### `title_policy`

- 语义：定义标题生成时的命名原则。
- 约束：应为稳定、可复用的策略说明。
- 注意事项：通常用于控制标题长度、风格和信息密度。

## 校验规则与约束

- 两个字段都应为非空字符串。
- 该 schema 只描述生成策略，不直接保存生成内容。

## 示例

```python
CaptionProfile(
    caption_policy="Generate concise but informative segment descriptions.",
    title_policy="Generate short and task-relevant titles.",
)
```
