# CanonicalExecutionPlan 数据模式

## 模块位置

- `src/video_atlas/schemas/canonical_atlas.py`

## 作用

`CanonicalExecutionPlan` 是 planner 输出经过程序约束后的正式执行计划。

它的职责是：

- 固定本次 canonical 处理的 profile
- 携带全局描述信息
- 为 parsing / composition 提供稳定输入

## 当前字段

- `planner_confidence`
- `genres`
- `concise_description`
- `profile_name`
- `profile`
- `output_language`
- `chunk_size_sec`
- `chunk_overlap_sec`
- `planner_reasoning_content`

## 关键设计点

### `profile`

当前使用统一 `Profile`：

- `route`
- `segmentation_policy`
- `caption_policy`

不再以旧的 `SegmentationProfile` / `CaptionProfile` 作为 execution plan 主结构。

### `output_language`

用于统一控制 planner、caption、structure composition 的输出语言。

### `chunk_size_sec` / `chunk_overlap_sec`

直接驱动 text-first parsing 的滑动窗口策略。

## 当前来源

由：

- `text_first_canonical/plan.py`
- `text_first_canonical/execution_plan_builder.py`

共同构造。
