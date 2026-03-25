# FrameSamplingProfile

## 文档目标

本文档用于说明 `FrameSamplingProfile` 的设计目的、字段定义和使用约束。

## Schema 概览

- 名称：`FrameSamplingProfile`
- 主要职责：定义视频帧采样时使用的基本采样密度与分辨率约束
- 实现形式：`dataclass`

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `fps` | `float` | 否 | `0.5` | 采样帧率 |
| `max_resolution` | `int` | 否 | `480` | 单帧最大分辨率约束 |

## 字段说明

### `fps`

- 语义：控制每秒采样多少帧。
- 约束：应为正数。
- 注意事项：值越大，输入帧数越多，模型成本也越高。

### `max_resolution`

- 语义：控制采样帧在进入模型前允许的最大边长。
- 约束：应为正整数。
- 注意事项：该字段用于限制多模态输入体积，而不是改变原视频本身。

## 校验规则与约束

- `fps` 必须大于 `0`。
- `max_resolution` 必须大于 `0`。
- 该 schema 用于描述采样策略，不直接描述具体帧内容。

## 示例

```python
FrameSamplingProfile(
    fps=1.0,
    max_resolution=480,
)
```
