# derived_atlas_workflow 模块设计

## 文档目标

本文档用于说明 `derived_atlas_workflow` 的设计目标、职责边界、核心接口、依赖关系和关键流程。本文档面向开发者，目标是帮助读者理解该模块如何基于 canonical atlas 生成面向任务的 derived atlas，以及它如何协调候选选择、片段派生、结果聚合和最终写出。

## 模块概览

- 名称：`derived_atlas_workflow`
- 路径：`src/video_atlas/workflows/derived_atlas_workflow.py` 与 `src/video_atlas/workflows/derived_atlas/`
- 主要职责：基于 canonical atlas 和任务请求，编排生成 derived atlas 的完整流程

## 职责与边界

### 职责

- 根据任务请求从 canonical atlas 中选择候选片段。
- 对候选片段执行 re-grounding 与 re-caption，得到适合任务使用的派生片段。
- 将派生结果聚合为完整 `DerivedAtlas`，并完成最终写入。

### 不负责的内容

- 不负责 canonical atlas 的生成。
- 不负责底层 prompt 模板、消息构造、模型调用协议和响应解析实现。
- 不负责 review 展示或上层编辑逻辑。

## 核心接口

### 具体实现类接口：`DerivedAtlasWorkflow`

- 类型：`concrete class`
- 作用：提供 derived atlas 生成流程的统一入口，并协调候选选择、派生和聚合阶段。
- 初始化输入：
  - `planner`
  - `segmentor`
  - `captioner`
  - 可选的 `num_workers`
- 对外暴露的方法：
  - `create(...)`：执行 derived atlas 生成流程。
  - `_prepare_messages(...)`：构造纯文本消息。
  - `_build_video_messages_from_path(...)`：构造视频消息。
  - `parse_response(...)`：解析模型输出。
- 关键方法的输入与输出：
  - `create(...)`
    - 输入：
      - `task_request`
      - `canonical_atlas`
      - `output_dir`
      - 可选的 `verbose`
    - 输出：
      - `DerivedAtlas`
- 说明：
  - 该类是 derived atlas 流程的统一入口。
  - 上层应通过该入口驱动 derivation，而不是直接跨阶段调用内部能力。

## 依赖关系

### 上游依赖

- 触发 derived atlas 生成的脚本、CLI 或其他上层入口
- 已存在的 `CanonicalAtlas`
- 构造 `planner`、`segmentor`、`captioner` 的配置与工厂逻辑

### 下游依赖

- `generators`
- `message_builder`
- `parsing`
- `schemas`
- `persistence`
- `prompts`

## 内部组成

### 流程入口部分

- 角色：对外暴露 derived atlas 生成入口，并持有流程运行依赖。
- 边界：
  - 负责流程级协调和并发控制
  - 不负责底层派生逻辑和落盘规则实现
- 输入：
  - 模型能力实例
  - 并发参数
- 输出：
  - 可执行的 derived atlas workflow 实例

### 候选选择部分

- 角色：根据任务请求从 canonical atlas 中选择需要进入派生流程的片段。
- 边界：
  - 负责 planner 调用和 `DerivationPolicy` 构造
  - 不负责具体 re-grounding 与 re-caption
- 输入：
  - `task_request`
  - `CanonicalAtlas`
- 输出：
  - 候选 work item 列表

### 派生执行部分

- 角色：对单个候选片段执行 re-grounding、字幕裁剪和 re-caption。
- 边界：
  - 负责构造 `DerivedSegmentDraft`
  - 不负责最终 `AtlasSegment` 初始化和 atlas 级聚合
- 输入：
  - 单个候选 work item
  - `task_request`
  - 源视频路径
- 输出：
  - `DerivedSegmentDraft`
  - 或在无法形成合法片段时返回空结果

### 结果聚合部分

- 角色：将 draft 结果统一组织为完整 `DerivedAtlas`。
- 边界：
  - 负责初始化最终 `AtlasSegment`、生成全局 summary 和 `DerivationResultInfo`
  - 不负责候选选择和底层 re-grounding
- 输入：
  - `task_request`
  - `CanonicalAtlas`
  - `DerivedSegmentDraft` 列表
  - 输出目录
- 输出：
  - `DerivedAtlas`

### 流程落盘部分

- 角色：驱动 derived atlas 的最终写出。
- 边界：
  - 负责在流程末尾调用 writer
  - 不负责目录规则实现
- 输入：
  - `DerivedAtlas`
- 输出：
  - 已写入 atlas 目录的 derived atlas 结果

## 关键流程

1. 入口接收任务请求、canonical atlas 和目标 atlas 目录。
2. 候选选择阶段根据任务请求从 canonical atlas 中选择派生对象，并生成 `DerivationPolicy`。
3. 派生执行阶段对每个候选片段执行 re-grounding、字幕裁剪和 re-caption，得到 `DerivedSegmentDraft`。
4. 聚合阶段将所有 draft 结果统一转换为 `DerivedAtlas`。
5. 流程调用 `DerivedAtlasWriter` 完成最终写入。

## 设计约束

- 该模块是核心流程模块，不应退化为编辑逻辑或资产调度逻辑。
- draft 与最终 atlas 结果应分离，避免派生阶段直接初始化最终表示。
- re-grounding 与 re-caption 应始终围绕源视频内容和字幕上下文进行，而不是仅依赖摘要文本。

## 当前实现

- [derived_atlas_workflow.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/workflows/derived_atlas_workflow.py)：定义 `DerivedAtlasWorkflow` 对外入口，并聚合各阶段 mixin。
- [derived_atlas/pipeline.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/workflows/derived_atlas/pipeline.py)：实现流程主链，包括候选选择、并发派生、聚合与最终写出。
- [derived_atlas/candidate_generation.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/workflows/derived_atlas/candidate_generation.py)：实现候选片段选择与 `DerivationPolicy` 构造。
- [derived_atlas/derivation.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/workflows/derived_atlas/derivation.py)：实现单片段 re-grounding、字幕裁剪、re-caption 与 `DerivedSegmentDraft` 生成。
- [derived_atlas/aggregation.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/workflows/derived_atlas/aggregation.py)：实现 `DerivedAtlas` 组装与聚合结果生成。
- [derived_atlas/loader.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/workflows/derived_atlas/loader.py)：提供从已存在 canonical atlas 目录加载 canonical 结果的辅助能力。
