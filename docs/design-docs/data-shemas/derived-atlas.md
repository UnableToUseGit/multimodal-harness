# DerivedAtlas

## 文档目标

本文档用于说明 `DerivedAtlas` 的设计目的、字段定义和使用约束。

## Schema 概览

- 名称：`DerivedAtlas`
- 主要职责：表达 derived workflow 的标准输出结果
- 实现形式：`dataclass`

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `task_request` | `str` | 是 | 无 | 派生任务请求 |
| `global_summary` | `str` | 是 | 无 | 全局摘要 |
| `detailed_breakdown` | `str` | 是 | 无 | 分段细分说明 |
| `segments` | `list[AtlasSegment]` | 是 | 无 | 最终 derived 片段列表 |
| `derivation_result_info` | `DerivationResultInfo` | 是 | 无 | 来源映射与策略信息 |
| `atlas_dir` | `Path` | 是 | 无 | derived atlas 根目录 |
| `source_canonical_atlas_dir` | `Path` | 是 | 无 | source canonical atlas 根目录 |
| `source_video_path` | `Path` | 是 | 无 | source 视频路径 |

## 字段说明

### `task_request`

- 语义：驱动当前 derived atlas 生成的任务请求。
- 约束：应为非空字符串。
- 注意事项：这是 derived atlas 与 canonical atlas 的核心区分之一。

### `global_summary`

- 语义：对整个 derived atlas 的全局总结。
- 约束：应为可读文本。
- 注意事项：通常由 aggregation 阶段代码生成。

### `detailed_breakdown`

- 语义：对各 derived 片段的进一步拆解说明。
- 约束：应为可读文本。
- 注意事项：常用于根级 README 和 review。

### `segments`

- 语义：derived atlas 中的最终片段列表。
- 约束：元素应为有效的 `AtlasSegment`。
- 注意事项：这是 writer 直接消费的主体内容。

### `derivation_result_info`

- 语义：记录来源映射与派生原因。
- 约束：应为有效的 `DerivationResultInfo`。
- 注意事项：用于解释 derived atlas 的形成过程。

### `atlas_dir`

- 语义：derived atlas 的根目录。
- 约束：应指向目标 workspace 根路径。
- 注意事项：writer 会直接使用该字段落盘。

### `source_canonical_atlas_dir`

- 语义：source canonical atlas 的根目录。
- 约束：应为合法路径。
- 注意事项：用于记录 derived atlas 的来源。

### `source_video_path`

- 语义：用于裁剪 derived clip 的 source 视频路径。
- 约束：应为合法路径。
- 注意事项：writer 会基于它抽取最终片段视频。

## 校验规则与约束

- `segments` 中的 `segment_id` 应唯一。
- `derivation_result_info` 应与 `segments` 保持一致。
- `source_video_path` 应能被 writer 用于 clip 提取。

## 示例

```python
DerivedAtlas(
    task_request="Find the opening setup needed for my edit",
    global_summary="Derived 1 segment for the task.",
    detailed_breakdown="- derived_seg_0001: ...",
    segments=[...],
    derivation_result_info=some_result_info,
    atlas_dir=Path("/tmp/derived"),
    source_canonical_atlas_dir=Path("/tmp/canonical"),
    source_video_path=Path("/tmp/canonical/video.mp4"),
)
```
