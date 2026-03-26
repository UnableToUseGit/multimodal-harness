# canonical_atlas_workflow 模块设计

## 文档目标

本文档用于说明 `canonical_atlas_workflow` 的设计目标、职责边界、核心接口、依赖关系和关键流程。本文档面向开发者，目标是帮助读者理解该模块如何将原始视频组织为 canonical atlas，以及它如何协调下游能力完成这一核心流程。

## 模块概览

- 名称：`canonical_atlas_workflow`
- 路径：`src/video_atlas/workflows/canonical_atlas_workflow.py` 与 `src/video_atlas/workflows/canonical_atlas/`
- 主要职责：将原始视频、字幕和模型能力编排为 canonical atlas 生成流程

## 职责与边界

### 职责

- 组织 canonical atlas 生成所需的完整流程，包括规划、分段解析、全局组装和结果写出。
- 协调 `generators`、`message_builder`、`parsing`、`transcription`、`utils`、`persistence` 和 `schemas` 等模块。
- 产出结构化的 `CanonicalAtlas` 结果对象，并将其写入 atlas 目录。

### 不负责的内容

- 不负责定义底层 prompt 模板。
- 不负责实现具体模型调用协议。
- 不负责封装通用消息构造、响应解析、字幕生成或持久化写入逻辑。

## 核心接口

### 具体实现类接口：`CanonicalAtlasWorkflow`

- 类型：`concrete class`
- 作用：提供 canonical atlas 生成流程的统一入口，并负责协调内部各阶段。
- 初始化输入：
  - `planner`
  - `segmentor`
  - `captioner`
  - 可选的 `transcriber`
  - 可选的流程参数
    - `generate_subtitles_if_missing`
    - `chunk_size_sec`
    - `chunk_overlap_sec`
    - `caption_with_subtitles`
- 对外暴露的方法：
  - `create(...)`：执行 canonical atlas 生成流程。
  - `_prepare_messages(...)`：构造纯文本消息。
  - `_build_video_messages_from_path(...)`：构造基于视频路径的视频消息。
  - `parse_response(...)`：解析模型输出。
- 关键方法的输入与输出：
  - `create(...)`
    - 输入：
      - `output_dir`
      - `source_video_path`
      - 可选的 `source_srt_file_path`
      - 可选的 `verbose`
    - 输出：
      - `CanonicalAtlas`
- 说明：
  - 该类是 canonical atlas 流程的对外入口。
  - 上层应通过该入口发起流程，而不是直接拼接内部 mixin 能力。

## 依赖关系

### 上游依赖

- 触发 canonical atlas 生成的脚本、CLI 或其他上层入口
- 构造 `planner`、`segmentor`、`captioner`、`transcriber` 的配置与工厂逻辑

### 下游依赖

- `generators`
- `message_builder`
- `parsing`
- `transcription`
- `utils`
- `schemas`
- `persistence`
- `prompts`

## 内部组成

### 流程入口部分

- 角色：对外暴露 canonical atlas 生成入口，并保存流程运行所需依赖。
- 边界：
  - 负责流程级编排和依赖协调
  - 不负责实现各阶段底层能力
- 输入：
  - 模型能力实例
  - 转写能力实例
  - 流程级配置
- 输出：
  - 可执行的 canonical atlas workflow 实例

### 视频规划部分

- 角色：对原始视频进行探测，并构造 canonical 生成所需执行计划。
- 边界：
  - 负责 probe 输入准备、planner 调用与执行计划构建
  - 不负责实际分段解析和结果落盘
- 输入：
  - 视频路径
  - 视频时长
  - 字幕片段
  - 采样参数
- 输出：
  - `CanonicalExecutionPlan`

### 视频解析部分

- 角色：根据执行计划将视频解析为候选边界、稳定片段和局部 caption 结果。
- 边界：
  - 负责局部分段、边界清洗、片段合并和局部描述生成
  - 不负责全局 atlas 组装和目录写入
- 输入：
  - 视频路径
  - 字幕片段
  - `CanonicalExecutionPlan`
- 输出：
  - 片段级中间结果集合

### Atlas 组装部分

- 角色：将片段级中间结果组织为完整 `CanonicalAtlas`。
- 边界：
  - 负责调用全局 caption 生成并初始化 `AtlasSegment`
  - 不负责目录写入细节
- 输入：
  - 分段解析结果
  - 视频与字幕相关路径
  - `CanonicalExecutionPlan`
- 输出：
  - `CanonicalAtlas`

### 流程落盘部分

- 角色：驱动 canonical atlas 的最终写出。
- 边界：
  - 负责在流程末尾调用 writer
  - 不负责持久化规则实现
- 输入：
  - `CanonicalAtlas`
- 输出：
  - 已写入 atlas 目录的 canonical atlas 结果

## 关键流程

1. 入口接收原始视频路径、可选字幕路径和目标 atlas 目录。
2. 流程复制输入文件，并在必要时自动补生成字幕。
3. 流程读取视频时长、字幕内容并构建执行计划。
4. 流程按照执行计划完成视频分段与局部 caption 生成。
5. 流程将分段结果组装为完整 `CanonicalAtlas`。
6. 流程调用 `CanonicalAtlasWriter` 完成结果写入。

## 设计约束

- 该模块是核心流程模块，不应退化为底层工具集合。
- 该模块应编排公共能力，而不应重新实现 message builder、parsing 或 persistence 逻辑。
- 片段级中间结果与最终 atlas 结果应分离，避免在流程早期过早固定最终表示。

## 当前实现

- [canonical_atlas_workflow.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/workflows/canonical_atlas_workflow.py)：定义 `CanonicalAtlasWorkflow` 对外入口，并聚合各阶段 mixin。
- [canonical_atlas/pipeline.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/workflows/canonical_atlas/pipeline.py)：实现流程主链，包括输入准备、字幕解析、执行计划调用、atlas 组装与最终写出。
- [canonical_atlas/plan.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/workflows/canonical_atlas/plan.py)：实现视频探测与 planner 调用。
- [canonical_atlas/execution_plan_builder.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/workflows/canonical_atlas/execution_plan_builder.py)：将 planner 输出构造成 `CanonicalExecutionPlan`。
- [canonical_atlas/video_parsing.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/workflows/canonical_atlas/video_parsing.py)：实现边界检测、片段整理与局部 caption 生成。
- [canonical_atlas/atlas_assembly.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/workflows/canonical_atlas/atlas_assembly.py)：实现最终 `CanonicalAtlas` 组装。
