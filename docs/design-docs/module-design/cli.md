# cli 模块设计

## 文档目标

本文档用于说明 `cli` 模块在当前阶段的设计目标、职责边界、命令结构和与 `source_acquisition`、`canonical_atlas_workflow` 的协作方式。本文档面向开发者，目标是帮助读者理解 `VideoAtlas` 如何作为 agent 可直接消费的命令行工具被使用。

本文档聚焦本轮 CLI 重构目标：

- 取消 `canonical` 子命令层级，使 `create` 默认表示 canonical atlas create
- 增加统一的 URL 输入分发能力
- 增加 `fetch` 命令用于单独验证 acquisition 阶段

## 模块概览

- 名称：`cli`
- 路径：`src/video_atlas/cli/`
- 主要职责：提供稳定、可组合、适合 agent 调用的命令行入口，并将用户输入分发到 acquisition 或 atlas workflow

## 职责与边界

### 职责

- 定义清晰、稳定的命令结构和参数约定。
- 将 `--url` 形式的外部输入交给 `source_acquisition` 层识别和分发。
- 在 `create` 命令中协调 acquisition 结果与 canonical workflow。
- 在 `fetch` 命令中输出 acquisition workspace，用于单独验证视频、字幕和 source metadata 获取。

### 不负责的内容

- 不负责具体来源站点的下载实现。
- 不负责 canonical atlas 的规划、unit 检测或结构组合。
- 不负责 review 展示逻辑。

## 命令结构设计

当前阶段的 CLI 结构应收敛为：

```bash
video-atlas create --url <url> --output-dir <dir> [--config ...] [--structure-request ...]
video-atlas fetch --url <url> --output-dir <dir>
video-atlas info
video-atlas check-import
video-atlas config
```

### `create`

- 语义：默认表示 canonical atlas create
- 输入：
  - `--url`
  - `--output-dir`
  - 可选 `--config`
  - 可选 `--structure-request`
- 行为：
  - 先执行来源识别与 acquisition
  - 再将 acquisition 结果送入 canonical workflow
- 说明：
  - 当前不再要求 `video-atlas canonical create ...`
  - derived atlas 当前不纳入 CLI 结构

### `fetch`

- 语义：只做 acquisition，不生成 atlas
- 输入：
  - `--url`
  - `--output-dir`
- 行为：
  - 执行来源识别与 acquisition
  - 将 acquisition 产物写入输出目录后退出
- 说明：
  - 该命令主要用于验证下载、字幕和 source metadata 获取能力

## URL 输入设计

CLI 不再暴露来源站点特化参数，例如 `--youtube-url`，统一改为：

- `--url`

CLI 在收到 URL 后，不直接写站点判断逻辑，而是调用 `source_acquisition` 的统一入口：

- `detect_source_from_url(...)`
- `acquire_from_url(...)`

这样 CLI 只关心：

1. URL 是否被识别为受支持来源
2. acquisition 是否成功
3. 成功后是进入 `fetch` 输出，还是继续进入 canonical workflow

## 来源识别与分发设计

建议在 `src/video_atlas/source_acquisition/` 中新增两层薄封装：

### `detection.py`

- 角色：识别 URL 所属来源
- 当前范围：
  - 只识别标准 YouTube 视频页面 URL
- 输出：
  - 标准来源类型，例如 `youtube`

### `acquire.py`

- 角色：作为统一 acquisition 入口
- 行为：
  - 先调用 detection
  - 再根据来源类型分发到具体 acquirer
- 当前范围：
  - 只分发到 `YouTubeVideoAcquirer`

当前阶段虽然只有 YouTube 一个来源，但该层必须存在，以避免 CLI 直接耦合站点判断逻辑。

## 错误处理语义

CLI 对 URL 输入的错误处理应区分为三类：

### 非法 URL

- 含义：输入不构成合法 URL，或根本不满足最基本解析要求
- 建议提示：
  - `invalid url`

### 合法但不支持的来源

- 含义：URL 是合法的，但当前来源识别结果不属于已支持范围
- 建议提示：
  - `unsupported source`

### acquisition 失败

- 含义：来源已识别且已支持，但下载、字幕抓取或 metadata 获取失败
- 建议提示：
  - `acquisition failed`

这种区分可以帮助 agent 明确判断问题发生在输入层、来源支持层，还是执行层。

## `fetch` 输出契约

`fetch` 命令的输出目录应被定义为轻量但稳定的 acquisition workspace，而不是临时散乱下载目录。

最小建议结构如下：

```text
<fetch-output-dir>/
├── SOURCE_INFO.json
├── SOURCE_METADATA.json
├── video.mp4
├── subtitles.srt          # 可选
└── source/
    └── ...                # 可选原始字幕或辅助产物
```

### 关键文件说明

- `video.mp4`
  - acquisition 下载到的本地视频文件
- `subtitles.srt`
  - 抓到并标准化后的字幕文件，若无可用字幕则可缺失
- `SOURCE_INFO.json`
  - 来源类型、原始 URL、规范化 URL、字幕来源、是否需要 fallback 等信息
- `SOURCE_METADATA.json`
  - 输入来源的完整或近完整 metadata
- `source/`
  - 可选保存原始字幕、原始 metadata 或其他 acquisition 辅助产物

## `create` 与 `fetch` 的关系

- 两者共享同一套来源识别与 acquisition 逻辑
- `fetch` 到 acquisition workspace 为止
- `create` 在 acquisition 完成后继续进入 canonical workflow

因此，两者的区别不在 acquisition 本身，而在 acquisition 之后是否继续生成 atlas。

## 设计约束

- CLI 不应直接写站点判断逻辑，应通过 `source_acquisition` 统一入口调用。
- `create` 默认表示 canonical atlas create，不再保留 `canonical` 子命令层级。
- 当前只识别并支持 YouTube；其他 URL 一律明确报错，不做隐式尝试。
- `fetch` 必须保留视频、字幕和 source metadata，而不是只下载视频文件。
- 不应因为未来可能支持 derived atlas，而在当前阶段提前引入多余 CLI 层级。

## 当前实现规划

- `src/video_atlas/cli/main.py`
  - 重构命令结构，增加 `create` / `fetch`
- `src/video_atlas/source_acquisition/detection.py`
  - 新增 URL 来源识别
- `src/video_atlas/source_acquisition/acquire.py`
  - 新增统一 acquisition 分发入口
- `src/video_atlas/source_acquisition/youtube.py`
  - 继续承载 YouTube acquisition 本体
- `tests/test_cli.py`
  - 覆盖新的命令结构与错误提示
- `tests/test_source_acquisition_*.py`
  - 覆盖 detection、dispatch 和 fetch 行为
