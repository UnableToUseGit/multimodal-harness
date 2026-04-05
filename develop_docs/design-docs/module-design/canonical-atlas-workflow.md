# Text-First Canonical Workflow 模块设计

## 文档目标

本文档说明当前 `MM Harness` 中唯一仍在维护的 canonical workflow：`TextFirstCanonicalAtlasWorkflow`。

## 模块位置

- `src/video_atlas/workflows/text_first_canonical_atlas_workflow.py`
- `src/video_atlas/workflows/text_first_canonical/`

## 模块职责

该 workflow 的职责是：

- 接收 `CanonicalCreateRequest`
- 准备字幕资产
- 构造 `CanonicalExecutionPlan`
- 执行 text-first parsing
- 执行 structure composition
- 组装 `CanonicalAtlas`
- 写出 canonical workspace

它不负责：

- 输入 acquisition 或本地文件 materialization
- CLI 输出
- skill 安装

## 支持边界

当前 workflow 支持：

- `video-absent`
- `video-present + text-led`

当前 workflow 不支持：

- `video-present + visual-led`

当 planning 解析出的 `profile.route != "text_first"` 时，当前实现显式抛出 `NotImplementedError`。

## 对外接口

### `TextFirstCanonicalAtlasWorkflow.__init__(...)`

主要依赖：

- `planner`
- `text_segmentor`
- `structure_composer`
- `captioner`
- 可选 `transcriber`

运行参数：

- `generate_subtitles_if_missing`
- `chunk_size_sec`
- `chunk_overlap_sec`
- `caption_with_subtitles`
- `verbose`

### `create(request, on_progress=None)`

输入：

- `CanonicalCreateRequest`
- 可选 `on_progress` callback

输出：

- `(CanonicalAtlas, dict)`

其中返回的 cost dict 当前包括：

- `parsing_cost_time`
- `composition_cost_time`
- `persistence_cost_time`

## 内部阶段

### 1. Subtitle Preparation

由 `subtitle_preparation.py` 完成。

规则：

- 若 request 已提供字幕，直接使用
- 否则若有音频，优先转录音频
- 否则若有视频且允许生成字幕，则从视频转录
- 若都不可用，则失败

输出：

- 规范化 `subtitles.srt`
- `subtitle_items`
- `subtitles_text`

### 2. Output Language Resolution

由 `language.py` 完成。

优先级：

1. `structure_request`
2. `source_metadata`
3. 字幕文本
4. 识别失败时回退到英文

输出：

- `execution_plan.output_language`

### 3. Planning

由 `plan.py` 与 `execution_plan_builder.py` 完成。

planner 输入形态统一为：

- 有视觉采样时：`frames + subtitle probes + metadata summary`
- 无视觉采样时：`subtitle probes + metadata summary`

planner 输出被程序收敛为：

- `profile_name`
- `profile`
- `genres`
- `concise_description`
- `planner_confidence`
- `planner_reasoning_content`

这些字段共同构成 `CanonicalExecutionPlan`。

### 4. Text-First Parsing

由 `parsing.py` 完成。

当前实现特征：

- 基于字幕时间轴做 chunk + overlap 滑动窗口
- 每个 chunk 由 `text_segmentor` 产出 candidate boundaries
- 程序做边界去重、提交和 unit 构造
- caption 生成与后续 boundary detection 采用 overlapped streaming 方式

输出：

- `list[AtlasUnit]`

### 5. Structure Composition

由 `structure_composition.py` 完成。

输入：

- `units`
- `execution_plan.concise_description`
- `execution_plan.genres`
- 可选 `structure_request`
- `output_language`

输出：

- `CanonicalCompositionResult`

### 6. Atlas Assembly and Persistence

在 `pipeline.py` 中完成 atlas 组装，并根据是否有视频走两种写盘路径：

- 有视频：使用 `CanonicalAtlasWriter`
- 无视频：写 text-only workspace

## 关键依赖

- `schemas`
- `prompts`
- `parsing`
- `transcription`
- `persistence`
- `utils`

## 当前设计原则

- canonical 主线是 text-first，不再维护 legacy video-first workflow
- planning 负责决定 profile，不直接决定 CLI 行为
- route 来自 resolved profile，而不是模型直接输出的自由字段
- parsing 必须消费 `CanonicalExecutionPlan`
- 当前 release 不做弱多模态补丁路线
