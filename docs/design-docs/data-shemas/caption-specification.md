# CaptionSpecification

## 文档目标

本文档用于说明 `CaptionSpecification` 的设计目的、字段定义和使用约束。

## Schema 概览

- 名称：`CaptionSpecification`
- 主要职责：将 caption 配置名、caption 策略对象与采样策略对象绑定在一起
- 实现形式：`dataclass`

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `profile_name` | `str` | 否 | 工厂默认值 | caption 配置名 |
| `profile` | `CaptionProfile` | 否 | 工厂默认值 | caption 策略对象 |
| `frame_sampling_profile` | `FrameSamplingProfile` | 否 | `FrameSamplingProfile()` | caption 阶段使用的采样策略 |

## 字段说明

### `profile_name`

- 语义：标识当前使用的 caption 配置名称。
- 约束：应与 `profile` 保持一致语义。
- 注意事项：该字段主要用于配置管理和记录。

### `profile`

- 语义：描述 caption 生成的完整策略。
- 约束：应为有效的 `CaptionProfile` 实例。
- 注意事项：这是标题与描述生成行为的核心策略对象。

### `frame_sampling_profile`

- 语义：描述 caption 生成时的视频采样方式。
- 约束：应为有效的 `FrameSamplingProfile` 实例。
- 注意事项：用于支持 caption 阶段的多模态输入构造。

## 校验规则与约束

- `profile_name` 与 `profile` 应保持一致语义。
- `frame_sampling_profile` 必须是可执行的采样配置。

## 示例

```python
CaptionSpecification(
    profile_name="default",
    profile=some_caption_profile,
    frame_sampling_profile=FrameSamplingProfile(fps=0.5, max_resolution=480),
)
```
