# Canonical Workspace 目录格式

## 文档目标

本文档描述当前 canonical workspace 的稳定目录约定。

## 顶层结构

当前 canonical workspace 的根目录是：

```text
<output-dir>/<uid>/
```

其中：

- `<uid>` 由 application layer 生成
- 单次运行的所有输入与输出都收敛到这个目录下

## 当前目录结构

```text
<atlas-dir>/
├── README.md
├── SUBTITLES.md                  # 可选
├── input/
│   ├── SOURCE_INFO.json          # 可选
│   ├── SOURCE_METADATA.json      # 可选
│   ├── subtitles.srt             # 可选
│   ├── <video file>              # 可选
│   └── <audio file>              # 可选
├── units/
│   └── <unit-folder>/
│       ├── README.md
│       ├── SUBTITLES.md          # 可选
│       └── video_clip.mp4        # 仅视频场景
└── segments/
    └── <segment-folder>/
        ├── README.md
        ├── SUBTITLES.md          # 可选
        └── <unit-folder>/        # 复制视图
```

## `input/` 的语义

`input/` 用于保存单次运行的输入资产，不属于最终结构解释的一部分。

可能出现的文件包括：

- acquisition 或本地复制得到的视频文件
- acquisition 或本地复制得到的音频文件
- 规范化后的 `subtitles.srt`
- `SOURCE_INFO.json`
- `SOURCE_METADATA.json`

文件名不保证完全固定，除了：

- `subtitles.srt`
- `SOURCE_INFO.json`
- `SOURCE_METADATA.json`

## `units/`

`units/` 保存 Stage 1 的稳定基本单元。

每个 unit 目录至少包含：

- `README.md`

可选包含：

- `SUBTITLES.md`
- `video_clip.mp4`

## `segments/`

`segments/` 保存 Stage 2 组合后的最终结构。

每个 segment 目录至少包含：

- `README.md`

可选包含：

- `SUBTITLES.md`
- 复制进去的 unit 子目录

## Text-only 与 Video-backed 的差异

### Text-only

- 没有 clip
- workspace 主要由 README、SUBTITLES、units、segments 构成

### Video-backed

- unit 目录中会有 `video_clip.mp4`
- segment 目录下复制视图中的 unit 也会带 clip

## 当前稳定约定

- `atlas_dir/input/` 是输入资产目录
- root README 是 workspace 总览入口
- `units/` 保存 Stage 1 结果
- `segments/` 保存最终结构结果
- `SOURCE_INFO.json` 和 `SOURCE_METADATA.json` 都位于 `input/`
