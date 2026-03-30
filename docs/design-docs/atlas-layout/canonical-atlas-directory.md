# Canonical Atlas 目录格式

## 文档目标

本文档用于说明 `Canonical Atlas` 的目录结构、文件组织方式和外部表示约定。本文档面向开发者、评审者和下游消费者，目标是帮助读者理解 canonical atlas 在落盘后应呈现为什么样的目录形式，以及哪些内容属于稳定契约。

## 适用对象

- atlas 类型：`Canonical`
- 输出目标：面向 review、人工检查、后续 derived atlas 生成与其他下游消费者
- 维护模块：`persistence` 与 `canonical_atlas_workflow`

## 根目录结构

```text
<canonical-atlas-root>/
├── README.md
├── EXECUTION_PLAN.json
├── video.mp4
├── subtitles.srt                # 可选
├── SUBTITLES.md                 # 可选
└── segments/
    ├── <segment-folder-1>/
    │   ├── README.md
    │   ├── video_clip.mp4
    │   └── SUBTITLES.md         # 可选
    └── <segment-folder-2>/
        ├── README.md
        ├── video_clip.mp4
        └── SUBTITLES.md         # 可选
```

## 根目录项说明

### `README.md`

- 类型：`file`
- 作用：提供 canonical atlas 的根级概览。
- 是否必需：`是`
- 说明：
  - 该文件用于表达 atlas 标题、总时长、全局摘要和 segments 组织方式。
  - 它是人工检查和 review 的重要入口。

### `EXECUTION_PLAN.json`

- 类型：`file`
- 作用：记录 canonical workflow 生成该 atlas 时的执行计划。
- 是否必需：`是`
- 说明：
  - 内容应与 `CanonicalExecutionPlan` 保持一致。
  - 该文件主要服务于调试、解释和流程复现。

### `video.mp4`

- 类型：`file`
- 作用：保存 canonical atlas 的源视频副本。
- 是否必需：`是`
- 说明：
  - 后续 clip 提取与 review 都可能依赖该文件。

### `subtitles.srt`

- 类型：`file`
- 作用：保存原始或自动生成的 SRT 字幕文件。
- 是否必需：`否`
- 说明：
  - 当输入未提供字幕且系统未能生成字幕时，该文件可以不存在。

### `SUBTITLES.md`

- 类型：`file`
- 作用：保存整个视频的 Markdown 字幕文本。
- 是否必需：`否`
- 说明：
  - 其存在受 `caption_with_subtitles` 等运行时选项影响。

### `segments/`

- 类型：`directory`
- 作用：保存 canonical atlas 的片段级结果。
- 是否必需：`是`
- 说明：
  - 每个片段对应一个稳定子目录。
  - 子目录名通常由 `segment_id`、标题 slug 和时间范围组合生成。

## 子目录与文件说明

### `segments/<segment-folder>/`

- 目录结构：

```text
segments/<segment-folder>/
├── README.md
├── video_clip.mp4
└── SUBTITLES.md     # 可选
```

- 作用：表达单个 canonical 片段的完整外部表示。
- 文件约定：
  - `README.md`：记录片段标识、时间范围、标题、摘要与详细描述。
  - `video_clip.mp4`：该片段对应的视频片段。
  - `SUBTITLES.md`：该片段对应的字幕文本。

## 必需项与可选项

### 必需项

- 根目录 `README.md`
- 根目录 `EXECUTION_PLAN.json`
- 根目录源视频文件
- `segments/` 目录
- 每个片段目录中的 `README.md`
- 每个片段目录中的 `video_clip.mp4`

### 可选项

- 根目录 `subtitles.srt`
- 根目录 `SUBTITLES.md`
- 片段目录中的 `SUBTITLES.md`

## 文件内容约定

### 根目录 `README.md`

- 内容类型：`Markdown`
- 主要字段或内容：
  - `Title`
  - `Duration`
  - `Abstract`
  - Segmentation Context
- 说明：
  - 应提供整个 canonical atlas 的全局概览。
  - 该文件是人工检查的第一入口之一。

### 根目录 `EXECUTION_PLAN.json`

- 内容类型：`JSON`
- 主要字段或内容：
  - `planner_confidence`
  - `genres`
  - `concise_description`
  - `segmentation_specification`
  - `caption_specification`
  - `chunk_size_sec`
  - `chunk_overlap_sec`
- 说明：
  - 其内容应与 `CanonicalExecutionPlan` 对齐。

### 片段目录 `README.md`

- 内容类型：`Markdown`
- 主要字段或内容：
  - `SegID`
  - `Start Time`
  - `End Time`
  - `Duration`
  - `Title`
  - `Summary`
  - `Detail Description`
- 说明：
  - 片段时间字段当前由 persistence 层写出。
  - 当前 `Start Time`、`End Time` 和 `Duration` 统一使用 `HH:MM:SS` 格式。

## 稳定契约

- `segments/` 目录及每个片段子目录的存在方式应被视为稳定契约。
- 根级与片段级 `README.md` 的关键字段命名不应静默变更。
- `EXECUTION_PLAN.json` 的整体角色与主要字段语义应保持稳定。
- 可选项可以在保持兼容的前提下增减，但不应影响必需项的解释方式。

## 示例目录树

```text
canonical-atlas/
├── README.md
├── EXECUTION_PLAN.json
├── video.mp4
├── subtitles.srt
├── SUBTITLES.md
└── segments/
    ├── seg-0001-opening-00:00:00-00:00:24/
    │   ├── README.md
    │   ├── video_clip.mp4
    │   └── SUBTITLES.md
    └── seg-0002-transition-00:00:24-00:01:01/
        ├── README.md
        ├── video_clip.mp4
        └── SUBTITLES.md
```
