# Derived Atlas 目录格式

## 文档目标

本文档用于说明 `Derived Atlas` 的目录结构、文件组织方式和外部表示约定。本文档面向开发者、评审者和下游消费者，目标是帮助读者理解 derived atlas 在落盘后应呈现为什么样的目录形式，以及哪些内容属于稳定契约。

## 适用对象

- atlas 类型：`Derived`
- 输出目标：面向 review、人工检查、任务级消费和后续上层应用
- 维护模块：`persistence` 与 `derived_atlas_workflow`

## 根目录结构

```text
<derived-atlas-root>/
├── README.md
├── TASK.md
├── derivation.json
├── .agentignore/
│   └── DERIVATION_RESULT.json
└── segments/
    ├── <segment-folder-1>/
    │   ├── README.md
    │   ├── video_clip.mp4
    │   ├── SUBTITLES.md         # 可选
    │   └── SOURCE_MAP.json
    └── <segment-folder-2>/
        ├── README.md
        ├── video_clip.mp4
        ├── SUBTITLES.md         # 可选
        └── SOURCE_MAP.json
```

## 根目录项说明

### `README.md`

- 类型：`file`
- 作用：提供 derived atlas 的根级概览。
- 是否必需：`是`
- 说明：
  - 该文件用于表达任务请求、全局摘要和分段细分说明。

### `TASK.md`

- 类型：`file`
- 作用：保存原始任务请求文本。
- 是否必需：`是`
- 说明：
  - 该文件用于保留派生流程的直接任务输入。

### `derivation.json`

- 类型：`file`
- 作用：保存 derived atlas 的根级 metadata。
- 是否必需：`是`
- 说明：
  - 该文件应覆盖 task request、summary、breakdown、片段数量与 source canonical atlas 路径。

### `.agentignore/DERIVATION_RESULT.json`

- 类型：`file`
- 作用：保存派生来源映射与策略信息。
- 是否必需：`是`
- 说明：
  - 内容应与 `DerivationResultInfo` 对齐。
  - 该文件服务于解释性输出与调试。

### `segments/`

- 类型：`directory`
- 作用：保存 derived atlas 的片段级结果。
- 是否必需：`是`
- 说明：
  - 每个派生片段对应一个稳定子目录。

## 子目录与文件说明

### `segments/<segment-folder>/`

- 目录结构：

```text
segments/<segment-folder>/
├── README.md
├── video_clip.mp4
├── SUBTITLES.md      # 可选
└── SOURCE_MAP.json
```

- 作用：表达单个 derived 片段的完整外部表示。
- 文件约定：
  - `README.md`：记录派生片段标识、来源片段、时间范围、标题、摘要、详细描述与派生意图。
  - `video_clip.mp4`：该派生片段对应的视频片段。
  - `SUBTITLES.md`：该派生片段裁剪后的字幕文本。
  - `SOURCE_MAP.json`：记录该派生片段与 source segment 的映射关系，以及对应策略。

## 必需项与可选项

### 必需项

- 根目录 `README.md`
- 根目录 `TASK.md`
- 根目录 `derivation.json`
- `.agentignore/DERIVATION_RESULT.json`
- `segments/` 目录
- 每个片段目录中的 `README.md`
- 每个片段目录中的 `video_clip.mp4`
- 每个片段目录中的 `SOURCE_MAP.json`

### 可选项

- 片段目录中的 `SUBTITLES.md`

## 文件内容约定

### 根目录 `README.md`

- 内容类型：`Markdown`
- 主要字段或内容：
  - `Task Request`
  - `Global Summary`
  - `Detailed Breakdown`
- 说明：
  - 该文件用于表达 derived atlas 的任务级视角。

### 根目录 `derivation.json`

- 内容类型：`JSON`
- 主要字段或内容：
  - `task_request`
  - `global_summary`
  - `detailed_breakdown`
  - `derived_segment_count`
  - `source_canonical_atlas_path`
- 说明：
  - 该文件承担根级 metadata 角色。

### `.agentignore/DERIVATION_RESULT.json`

- 内容类型：`JSON`
- 主要字段或内容：
  - `derived_atlas_segment_count`
  - `derivation_reason`
  - `derivation_source`
- 说明：
  - 其内容应与 `DerivationResultInfo` 对齐。

### 片段目录 `README.md`

- 内容类型：`Markdown`
- 主要字段或内容：
  - `DerivedSegID`
  - `SourceSegID`
  - `Start Time`
  - `End Time`
  - `Duration`
  - `Title`
  - `Summary`
  - `Detail Description`
  - `Intent`
- 说明：
  - 该文件同时表达片段自身信息和任务导向信息。

### 片段目录 `SOURCE_MAP.json`

- 内容类型：`JSON`
- 主要字段或内容：
  - `source_segment_id`
  - `derivation_policy`
- 说明：
  - 用于保存片段级来源映射和策略解释。

## 稳定契约

- 根目录 `README.md`、`TASK.md`、`derivation.json` 和 `.agentignore/DERIVATION_RESULT.json` 的角色应保持稳定。
- 片段目录中的 `README.md` 与 `SOURCE_MAP.json` 的关键字段不应静默变更。
- `segments/` 目录和单片段目录结构应被视为稳定契约。
- 可选字幕文件的有无不应影响其他必需项的解释。

## 示例目录树

```text
derived-atlas/
├── README.md
├── TASK.md
├── derivation.json
├── .agentignore/
│   └── DERIVATION_RESULT.json
└── segments/
    ├── derived-seg-0001-opening-5.00-15.00s/
    │   ├── README.md
    │   ├── video_clip.mp4
    │   ├── SUBTITLES.md
    │   └── SOURCE_MAP.json
    └── derived-seg-0002-transition-61.20-72.50s/
        ├── README.md
        ├── video_clip.mp4
        └── SOURCE_MAP.json
```
