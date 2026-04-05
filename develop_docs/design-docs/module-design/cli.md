# CLI 模块设计

## 文档目标

本文档说明当前 `MM Harness` CLI 的正式命令面，以及 CLI 与 application / workflow 的职责边界。

## 模块位置

- `src/video_atlas/cli/main.py`

## CLI 定位

CLI 是当前产品的唯一正式用户入口，面向：

- 人类用户
- Claude Code / Codex / OpenClaw 等 agent

CLI 负责：

- 解析命令行参数
- 打印终端输出
- 调用 application layer
- 暴露安装、健康检查和 skill 注册能力

CLI 不负责：

- source acquisition
- workflow planning / parsing / composition
- workspace 读写细节

## 当前正式命令

### `mm-harness info`

显示：

- 产品名
- 版本号
- Python 版本
- 当前解释器路径

### `mm-harness doctor`

检查当前环境是否可运行。

当前检查项包括：

- `ffmpeg`
- `yt-dlp`
- `deno`
- `LLM_API_BASE_URL`
- `LLM_API_KEY`
- `GROQ_API_KEY`
- 可选 YouTube cookies

### `mm-harness install`

当前作用：

- 安装包内 `SKILL.md` 到检测到的 skill 目录

### `mm-harness skill --install`

显式安装 skill。

### `mm-harness skill --uninstall`

从已知 skill 目录中移除 skill。

### `mm-harness create`

正式 canonical 生成入口。

支持两类输入：

- `--url`
- 或本地文件组合：
  - `--video-file`
  - `--audio-file`
  - `--subtitle-file`
  - 可选 `--metadata-file`

必需参数：

- `--output-dir`

可选参数：

- `--structure-request`

## 运行时输出

CLI 默认打印结构化 plain-text 进度，而不是隐藏执行过程。

`create` 的典型里程碑包括：

- `Creating canonical atlas...`
- `Acquiring source assets from URL...` 或 `Preparing local input assets...`
- `Preparing subtitles...`
- `Resolving atlas output language...`
- `Planning canonical atlas...`
- `Parsing units...`
- `Composing final structure...`
- `Writing atlas workspace...`

结束时打印摘要：

- `Done`
- `atlas_dir`
- `title`
- `output_language`
- `segments`
- `cost_time`

## 与 application layer 的关系

CLI 不直接操作 workflow。

当前固定调用：

- `create_canonical_from_url(...)`
- `create_canonical_from_local(...)`

`install` / `skill` 命令则调用：

- `skill_install.install_skill()`
- `skill_install.uninstall_skill()`

## 当前发布边界

以下内容不在当前正式 CLI 契约中：

- `fetch`
- `--config`
- 旧 `video-atlas` 命令名

CLI 主入口现在以 `mm-harness` 为准。
