# SegmentationProfile

## 文档目标

本文档用于说明 `SegmentationProfile` 的设计目的、字段定义和使用约束。

## Schema 概览

- 名称：`SegmentationProfile`
- 主要职责：定义视频切分阶段的高层策略
- 实现形式：`dataclass`

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `segmentation_route` | `str` | 是 | 无 | 决定切分阶段使用哪条执行路线 |
| `signal_priority` | `str` | 是 | 无 | 切分时优先关注的信号类型 |
| `target_segment_length_sec` | `tuple[int, int]` | 是 | 无 | 目标片段时长范围 |
| `default_sampling_profile` | `str` | 是 | 无 | 默认采样配置名 |
| `boundary_evidence_primary` | `tuple[str, ...]` | 是 | 无 | 主证据类型 |
| `boundary_evidence_secondary` | `tuple[str, ...]` | 是 | 无 | 次证据类型 |
| `segmentation_policy` | `str` | 是 | 无 | 切分策略说明 |

## 字段说明

### `segmentation_route`

- 语义：定义该切分 profile 默认应走哪条工程执行路线。
- 约束：当前应为 `text_llm` 或 `multimodal_local`。
- 注意事项：该字段不仅影响输入模态，还会联动选择使用哪个 `segmentor`、哪组 chunk 参数，以及字幕缺失时是否需要回退。

### `signal_priority`

- 语义：标识切分时优先依赖的信号类别。
- 约束：应来自允许的信号优先级集合。
- 注意事项：该字段影响边界判断偏好，而不是直接决定边界位置。

### `target_segment_length_sec`

- 语义：定义片段期望长度的最小值与最大值。
- 约束：应为长度为 2 的整数元组，且最小值不大于最大值。
- 注意事项：这是目标范围，不等同于硬性截断规则。

### `default_sampling_profile`

- 语义：关联默认的视频采样配置名。
- 约束：应能在采样配置注册表中解析到。
- 注意事项：它本身不是完整采样配置对象。

### `boundary_evidence_primary`

- 语义：定义边界判断时优先参考的证据类型。
- 约束：元素应来自允许的证据集合。
- 注意事项：主证据通常具有更高权重。

### `boundary_evidence_secondary`

- 语义：定义边界判断时次级参考的证据类型。
- 约束：元素应来自允许的证据集合。
- 注意事项：次证据通常用于补充而不是主导决策。

### `segmentation_policy`

- 语义：对切分原则的自然语言说明。
- 约束：应为可解释的稳定策略描述。
- 注意事项：该字段主要服务于 prompt 与执行解释。

## 校验规则与约束

- `target_segment_length_sec` 必须满足最小值不大于最大值。
- 证据类型字段应只包含允许值。
- `default_sampling_profile` 应可被解析。

## 示例

```python
SegmentationProfile(
    segmentation_route="multimodal_local",
    signal_priority="visual_first",
    target_segment_length_sec=(30, 90),
    default_sampling_profile="default",
    boundary_evidence_primary=("scene_change", "action_shift"),
    boundary_evidence_secondary=("subtitle_shift",),
    segmentation_policy="Prefer semantically complete segments.",
)
```
