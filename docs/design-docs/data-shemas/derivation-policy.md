# DerivationPolicy

## 文档目标

本文档用于说明 `DerivationPolicy` 的设计目的、字段定义和使用约束。

## Schema 概览

- 名称：`DerivationPolicy`
- 主要职责：表达某个 derived 片段的派生意图与 re-grounding 指令
- 实现形式：`dataclass`

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `intent` | `str` | 是 | 无 | 该片段应贡献的信息意图 |
| `grounding_instruction` | `str` | 是 | 无 | 如何在 source segment 内细化片段 |

## 字段说明

### `intent`

- 语义：描述这个派生片段在任务中的作用。
- 约束：应为清晰、可解释的自然语言。
- 注意事项：后续 aggregation 和 writer 会用它生成说明信息。

### `grounding_instruction`

- 语义：描述如何在 source segment 内进一步收紧范围。
- 约束：应为清晰、可执行的自然语言。
- 注意事项：segmentor 会直接消费该字段。

## 校验规则与约束

- 两个字段都应为非空字符串。
- 语义应稳定，能被模型和人工同时理解。

## 示例

```python
DerivationPolicy(
    intent="Find the opening setup relevant to the task",
    grounding_instruction="Focus on the first important action within the segment",
)
```
