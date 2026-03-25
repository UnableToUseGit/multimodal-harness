# SegmentationSpecification

## 文档目标

本文档用于说明 `SegmentationSpecification` 的设计目的、字段定义和使用约束。

## Schema 概览

- 名称：`SegmentationSpecification`
- 主要职责：将切分配置名、切分策略对象与采样策略对象绑定在一起
- 实现形式：`dataclass`

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `profile_name` | `str` | 否 | 工厂默认值 | 切分配置名 |
| `profile` | `SegmentationProfile` | 否 | 工厂默认值 | 切分策略对象 |
| `frame_sampling_profile` | `FrameSamplingProfile` | 否 | `FrameSamplingProfile()` | 切分阶段使用的采样策略 |

## 字段说明

### `profile_name`

- 语义：标识当前使用的切分配置名称。
- 约束：应与 `profile` 语义一致。
- 注意事项：主要用于配置选择与记录。

### `profile`

- 语义：描述切分阶段的完整策略。
- 约束：应为有效的 `SegmentationProfile` 实例。
- 注意事项：这是切分行为的核心策略对象。

### `frame_sampling_profile`

- 语义：描述切分阶段的视频采样方式。
- 约束：应为有效的 `FrameSamplingProfile` 实例。
- 注意事项：用于支持边界检测阶段的多模态输入准备。

## 校验规则与约束

- `profile_name` 与 `profile` 应保持一致语义。
- `frame_sampling_profile` 必须是可执行的采样配置。

## 示例

```python
SegmentationSpecification(
    profile_name="default",
    profile=some_segmentation_profile,
    frame_sampling_profile=FrameSamplingProfile(fps=1.0, max_resolution=480),
)
```
