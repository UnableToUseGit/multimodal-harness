# CaptionedSegment

## 文档目标

本文档用于说明 `CaptionedSegment` 的设计目的、字段定义和使用约束。

## Schema 概览

- 名称：`CaptionedSegment`
- 主要职责：表达已经生成 summary/detail 的片段中间结果
- 实现形式：`dataclass`

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `seg_id` | `str` | 是 | 无 | 片段标识 |
| `start_time` | `float` | 是 | 无 | 起始时间 |
| `end_time` | `float` | 是 | 无 | 结束时间 |
| `summary` | `str` | 是 | 无 | 摘要 |
| `detail` | `str` | 是 | 无 | 详细描述 |
| `subtitles_text` | `str` | 否 | `""` | 对应字幕文本 |
| `token_usage` | `int` | 否 | `0` | 生成开销统计 |

## 字段说明

### `seg_id`

- 语义：片段唯一标识。
- 约束：应在同一结果集中唯一。
- 注意事项：通常由 workflow 统一生成。

### `start_time` / `end_time`

- 语义：定义片段范围。
- 约束：`start_time < end_time`。
- 注意事项：与上游 `FinalizedSegment` 保持一致。

### `summary`

- 语义：面向快速理解的简要摘要。
- 约束：应为非空字符串。
- 注意事项：通常比 `detail` 更短、更抽象。

### `detail`

- 语义：面向细节理解的描述文本。
- 约束：应为非空字符串。
- 注意事项：通常用于后续全局汇总和派生。

### `subtitles_text`

- 语义：片段对应的字幕文本。
- 约束：可为空。
- 注意事项：该字段是附加上下文，不总是存在。

### `token_usage`

- 语义：记录生成该片段描述时的 token 消耗。
- 约束：应为非负整数。
- 注意事项：主要用于统计和调试。

## 校验规则与约束

- `start_time` 必须小于 `end_time`。
- `summary` 和 `detail` 不应为空。
- `token_usage` 不应为负数。

## 示例

```python
CaptionedSegment(
    seg_id="seg_0001",
    start_time=0.0,
    end_time=30.0,
    summary="The video opens with the setup phase.",
    detail="This segment covers the opening setup and introduces the key participants.",
    subtitles_text="...",
    token_usage=128,
)
```
