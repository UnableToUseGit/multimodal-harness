# release/version2_onlytext 发行准备计划

## 目标

为当前 `text-first canonical workflow v1` 准备一个可发行版本，使其能够以低门槛 CLI 工具的形式被普通用户以及 `Claude Code`、`Codex`、`OpenClaw` 等 agent 使用。

本轮工作的重点不是继续扩展算法能力，而是将当前可用能力收口为稳定、清晰、可安装、可诊断、可说明的产品形态。

## 本轮发行范围

### 保留的正式能力

- `video-atlas create`
- `video-atlas info`
- `video-atlas doctor`

### 从正式发行入口中移除的内容

- `video-atlas fetch`
- `--config`

说明：

- `fetch` 只作为开发期调试工具存在过，不再作为正式用户能力保留。
- 默认配置文件继续作为内部实现默认值存在，但不再作为发行版公开接口暴露给用户。

## 正式配置契约

### 必需环境变量

- `VIDEO_ATLAS_API_BASE`
- `VIDEO_ATLAS_API_KEY`
- `GROQ_API_KEY`

### 可选环境变量

- `YOUTUBE_COOKIES_FILE`
- `YOUTUBE_COOKIES_FROM_BROWSER`

### 设计原则

- 正式发行版只暴露最少必要配置。
- 模型初始化参数、provider 低层参数、runtime 细粒度参数不进入正式用户接口。
- 高级参数保留在默认配置文件中，作为内部实现默认值，而不是面向普通用户的操作面。

## CLI 收口目标

### `video-atlas create`

正式支持输入：

- `--url`
- `--video-file`
- `--audio-file`
- `--subtitle-file`
- `--output-dir`
- `--structure-request`

说明：

- `create` 继续支持 URL 输入和本地文件输入。
- 不再暴露 `--config`。

### `video-atlas info`

作用：

- 用于确认命令可用、版本正确、Python 可执行路径正确。

### `video-atlas doctor`

作用：

- 提供发行版可运行性诊断。
- 帮助用户和 agent 在运行前快速定位环境缺失项。

建议检查项：

- Python package import
- `ffmpeg`
- `yt-dlp`
- `deno`
- `VIDEO_ATLAS_API_BASE`
- `VIDEO_ATLAS_API_KEY`
- `GROQ_API_KEY`
- 可选提示 YouTube cookies 是否已配置

输出形式建议为：

- `OK`
- `WARN`
- `FAIL`

并在失败或警告时给出一句修复建议。

## 面向 agent 的发行材料

### 1. `README.md`

应明确说明：

- 项目定位
- 当前支持边界
- 最小安装方式
- 最小使用方式
- 环境变量要求
- 当前不支持 `visual-led` 视频

### 2. `docs/install.md`

面向 agent 编写，而不是面向纯人类说明。用户应能够直接把该文档链接发给 agent。

至少应包含：

- 安装方式
- 环境变量配置方式
- `doctor` 使用方式
- 最小 `create` 示例

### 3. `docs/update.md`

说明如何更新到新版本。

### 4. `docs/troubleshooting.md`

至少覆盖：

- `ffmpeg` 缺失
- `yt-dlp` 缺失
- `deno` 缺失
- `GROQ_API_KEY` 缺失
- YouTube cookies 缺失或受限
- `visual-led` 不支持

### 5. `SKILL.md`

这是让 `Claude Code` / `Codex` / `OpenClaw` 真正“会用” `VideoAtlas` 的关键文件。

应明确：

- 什么时候调用 `video-atlas create`
- 如何选择 URL 输入还是本地文件输入
- 输出目录如何查看
- 哪些错误属于环境问题
- 哪些内容类型当前不支持

## Smoke Tests

本轮发行需要新增最小 smoke tests，用于保证“发行版没死”。

最小建议覆盖：

- `video-atlas info`
- `video-atlas doctor`
- `video-atlas create --help`

必要时可再加一条 mock 条件下的最小 `create` 路径。

说明：

- smoke tests 只验证发行版入口是否可用
- 不承担真实联网下载、真实模型调用、真实长音频转录验证职责

## 实施顺序

1. 收口 CLI
   - 去掉 `fetch`
   - 去掉 `--config`
   - 保留 `create/info/doctor`

2. 实现 `doctor`
   - 完成环境依赖检查和环境变量检查

3. 补齐发行文档
   - `README.md`
   - `docs/install.md`
   - `docs/update.md`
   - `docs/troubleshooting.md`

4. 编写 `SKILL.md`
   - 面向 `Claude Code` / `Codex` / `OpenClaw`

5. 新增 smoke tests
   - 覆盖正式 CLI 入口

6. 最终回归与发行前检查
   - 核对 CLI 契约
   - 核对环境变量契约
   - 核对文档索引和安装路径

## 当前已知能力边界

- 支持 `video-absent`
- 支持 `video-present + text-led`
- `video-present + visual-led` 显式不支持
- 默认转录 backend 已切到 `groq_whisper`

这些边界需要在发行版 README、install guide、skill 和 troubleshooting 中保持一致。
