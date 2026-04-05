# MM Harness 架构设计

## 文档目标

本文档描述当前 `MM Harness` 的系统级架构。它只覆盖当前仍在维护的 release 主线，不描述已经删除或暂停维护的 legacy canonical workflow、derived atlas workflow，或其他实验性方案。

## 当前系统定位

`MM Harness` 是一个面向 agent 的长视频/长音频预处理工具。

它的目标不是直接完成所有下游任务，而是把原始媒体转换成一个更适合语言模型消费的结构化 workspace，使 agent 能继续完成总结、笔记、检索、审阅和二次处理等任务。

当前 release 的核心产品能力是：

- 读取长视频、长音频或字幕输入
- 自动完成 source acquisition、字幕准备、planning、text-first parsing 和结构组合
- 输出一个稳定的 canonical workspace

当前 release 不把以下内容作为正式能力：

- derived atlas
- 强视觉内容理解
- 完整多模态视频理解主线
- 面向普通终端用户的 GUI / Web 产品

## 系统主线

当前唯一受支持并持续维护的业务主线是：

`application layer -> TextFirstCanonicalAtlasWorkflow -> persistence/review`

其中：

- `application`
  负责把 URL 或本地文件输入整理为 `CanonicalCreateRequest`
- `TextFirstCanonicalAtlasWorkflow`
  负责执行字幕准备、planning、text-first parsing、structure composition 和 atlas 组装
- `persistence`
  负责将结果写为稳定 workspace
- `review`
  负责读取 workspace 并支撑人工检查

## 分层结构

### Interface Layer

当前主要是 CLI：

- 入口：`mm-harness`
- 命令：
  - `info`
  - `doctor`
  - `install`
  - `skill --install/--uninstall`
  - `create`

Interface Layer 负责：

- 接收用户或 agent 的命令
- 打印终端信息
- 调用 application layer

它不负责业务决策，不直接处理 planning、parsing 或转录。

### Application Layer

核心入口位于：

- `src/video_atlas/application/canonical_create.py`

它负责：

- 解析 URL 输入与本地文件输入
- 将输入资产 materialize 到 `atlas_dir/input/`
- 组装 `CanonicalCreateRequest`
- 基于配置实例化 workflow

它不负责具体的 planning、segment detection 或 composition 逻辑。

### Business Layer

核心实现位于：

- `src/video_atlas/workflows/text_first_canonical_atlas_workflow.py`
- `src/video_atlas/workflows/text_first_canonical/`

当前业务层只维护一条 text-first canonical workflow：

- 先准备字幕
- 再构造 `CanonicalExecutionPlan`
- 再执行 text-first parsing
- 再执行 structure composition
- 最后写出 canonical workspace

当前支持边界：

- 支持：`video-absent`
- 支持：`video-present + text-led`
- 不支持：`video-present + visual-led`

### Infrastructure Layer

当前核心基础设施能力包括：

- `source_acquisition`
  - YouTube
  - Xiaoyuzhou
- `transcription`
  - 默认 `groq_whisper`
- `generators`
  - 统一远端 OpenAI-compatible LLM 调用
- `persistence`
  - workspace 写盘
- `review`
  - workspace 读取

## 核心对象

当前主线围绕以下共享对象组织：

- `CanonicalCreateRequest`
  - application layer 传给 business layer 的统一输入
- `CanonicalExecutionPlan`
  - planner 输出被程序解析后的正式执行计划
- `AtlasUnit`
  - Stage 1 的稳定基本单元
- `AtlasSegment`
  - Stage 2 的最终结构单元
- `CanonicalAtlas`
  - 最终 canonical workspace 的内存表示

## 输入到输出的主流程

1. CLI 接收 URL 或本地文件输入
2. application layer 将输入资产 materialize 到 `atlas_dir/input/`
3. workflow 准备字幕：
   - 直接使用字幕
   - 或从音频/视频转录
4. workflow 根据字幕与可选视觉 probe 构造 `CanonicalExecutionPlan`
5. 若 execution plan 的 profile route 为 `text_first`，执行 text-first parsing
6. 将 units 送入 structure composition
7. 组装 `CanonicalAtlas`
8. 将 atlas 写到目标目录，供 agent 和 review 使用

## 当前稳定外部契约

当前值得视为稳定契约的内容包括：

- CLI 命令面
- 环境变量：
  - `LLM_API_BASE_URL`
  - `LLM_API_KEY`
  - `GROQ_API_KEY`
  - `YOUTUBE_COOKIES_FILE`
  - `YOUTUBE_COOKIES_FROM_BROWSER`
- canonical workspace 目录约定
- `CanonicalCreateRequest`
- `CanonicalExecutionPlan`
- `AtlasUnit`
- `AtlasSegment`
- `CanonicalAtlas`

## 当前不再维护的设计

以下设计不再是当前主线的一部分：

- legacy `canonical_atlas_workflow`
- `src/video_atlas/workflows/canonical_atlas/`
- derived atlas workflow 文档体系
- `SegmentationProfile` / `CaptionProfile` 驱动的旧 execution plan 设计
- 多连接 `default/local/remote` LLM 配置设计

这些内容若未来需要恢复，应重新立项，而不是继续将其视为当前设计的一部分。
