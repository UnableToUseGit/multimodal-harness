# source_acquisition 模块设计

## 文档目标

本文档用于说明 `source_acquisition` 模块的设计目标、职责边界、核心接口、依赖关系和关键流程。本文档面向开发者，目标是帮助读者理解系统如何将外部输入，尤其是 YouTube 视频页面 URL，转换为 application layer 可消费的标准本地输入。

本文档聚焦当前阶段目标：为 application layer 提供可扩展的 URL acquisition 能力。当前已支持单个标准 YouTube 视频页面 URL 与小宇宙单集 URL，不覆盖 playlist、短链、频道页或 derived atlas 链路改造。

## 模块概览

- 名称：`source_acquisition`
- 路径：`src/video_atlas/source_acquisition/`
- 主要职责：将外部来源输入标准化为本地视频、本地音频、可选字幕和源元数据，并为 application layer 提供统一 acquisition 能力

## 职责与边界

### 职责

- 识别并校验受支持的外部输入类型。
- 对标准 YouTube 视频页面 URL 执行视频下载、元数据抓取和字幕抓取。
- 对小宇宙单集 URL 执行页面解析、音频下载与基础 metadata 抽取。
- 将 acquisition 结果整理为稳定的数据对象，并直接落盘到上层指定的目标目录。

### 不负责的内容

- 不负责 canonical atlas 的规划、unit 检测、结构组合和结果组装。
- 不负责 derived atlas 生成。
- 不负责 review 展示逻辑。
- 不负责定义 transcriber 的具体实现。
- 不负责 `CanonicalCreateRequest` 的组装与业务路径选择。

## 核心接口

### 函数接口：`acquire_from_url(...)`

- 类型：`function`
- 作用：根据输入 URL 识别来源类型并执行 acquisition。
- 输入：
  - 外部 URL
  - 输出目录
  - acquisition 配置
- 输出：
  - `SourceAcquisitionResult`
- 说明：
  - 当前阶段支持 YouTube 与小宇宙两类 URL。
  - 该接口负责统一封装 acquisition 入口，不把上层 CLI 或 application layer 绑定到具体来源实现。

### 具体实现类接口：`YouTubeVideoAcquirer`

- 类型：`concrete class`
- 作用：处理标准 YouTube 视频页面 URL 的下载、元数据抓取和字幕获取。
- 初始化输入：
  - 下载工具配置
  - 工作目录策略
  - 日志或运行参数
- 对外暴露的方法：
  - `acquire(...)`：执行单个 YouTube 视频来源的输入准备。
- 关键方法的输入与输出：
  - `acquire(...)`
    - 输入：
      - `youtube_url`
      - `output_dir`
    - 输出：
      - `SourceAcquisitionResult`
- 说明：
  - 该实现类只负责“获取和标准化输入”，不直接调用 canonical workflow。
  - 该实现类先执行 metadata probe，再根据时长策略决定是否下载视频。
  - 当前默认策略是：视频时长不超过 `25` 分钟时下载视频与字幕；超过 `25` 分钟时只抓取字幕，不下载视频文件。
  - 该实现类应优先复用 YouTube 已有字幕或自动字幕；仅当字幕不可用时，才把后续本地转写留给上层 workflow。

### 具体实现类接口：`XiaoyuzhouAudioAcquirer`

- 类型：`concrete class`
- 作用：处理小宇宙单集页面 URL 的页面解析、音频下载和 metadata 抽取。
- 关键行为：
  - 解析页面中的 `__NEXT_DATA__` 与 `ld+json`
  - 提取音频直链
  - 提取标题、描述、发布时间、时长、节目作者和封面图等字段
- 输出：
  - `SourceAcquisitionResult`
    - 其中 `audio_path` 为主媒体文件路径

### 数据对象接口：`SourceAcquisitionResult`

- 类型：`data structure`
- 作用：表达 acquisition 阶段的标准输出契约。
- 主要字段建议包括：
  - `source_info`
  - `source_metadata`
  - `video_path`
  - `audio_path`
  - `subtitles_path`
  - `artifacts`
- 说明：
  - `video_path`、`audio_path`、`subtitles_path` 均为可选项，具体由来源类型决定。
  - `source_info` 用于表达稳定、跨来源的来源摘要。
  - `source_metadata` 使用归一化 schema，供业务层稳定消费。

## 依赖关系

### 上游依赖

- CLI 入口
- 后续可能的 agent skill 或脚本入口
- canonical workflow 的上层编排逻辑

### 下游依赖

- 外部下载工具或其 Python 封装
- 本地文件系统
- `persistence` 中的基础写文件能力

## 内部组成

### 输入识别部分

- 角色：识别来源类型并校验 URL 是否属于受支持的单视频页面。
- 边界：
  - 负责来源判断和参数校验
  - 不负责下载和 workflow 调度
- 输入：
  - CLI 或 application layer 传入的 URL
- 输出：
  - 规范化来源描述

### YouTube 获取部分

- 角色：抓取视频、字幕与元数据，并产出本地资产。
- 边界：
  - 负责调用下载工具和组织 acquisition 产物
  - 不负责 atlas 生成
- 输入：
  - 标准 YouTube 视频页面 URL
  - acquisition 工作目录
- 输出：
  - 本地视频文件或本地音频文件
  - 可选的本地字幕文件
  - 归一化后的来源元数据

### 小宇宙获取部分

- 角色：抓取页面、解析音频直链和 metadata，并产出本地音频资产。
- 边界：
  - 负责页面解析和音频下载
  - 不负责 atlas 生成或转写触发
- 输入：
  - 小宇宙单集 URL
  - acquisition 工作目录
- 输出：
  - 本地音频文件
  - 归一化后的来源元数据

### 结果标准化部分

- 角色：将各类原始抓取结果整理为统一 schema。
- 边界：
  - 负责形成稳定输出契约
  - 不负责业务流程推理
- 输入：
  - 下载工具原始输出
  - 本地文件路径
  - 字幕可用性信息
- 输出：
  - `SourceAcquisitionResult`

## 关键流程

1. CLI 接收 `--url` 和 `--output-dir`。
2. `source_acquisition` 先识别 URL 来源类型；当前支持标准 YouTube 视频页面和小宇宙单集页面。
3. acquisition 执行来源特定抓取：
   - YouTube：先抓取 metadata，再根据时长阈值决定是下载视频+字幕还是只抓取字幕。
   - 小宇宙：抓取页面、提取音频直链并下载音频文件。
4. acquisition 抓取并整理来源 metadata。
5. acquisition 将结果标准化为 `SourceAcquisitionResult`。
6. `fetch` 到 acquisition 为止；`create` 则由 application layer 把 acquisition 结果组装为 `CanonicalCreateRequest`。
7. 若缺失可用字幕，则 canonical workflow 按既有策略回退到转写。
8. canonical workflow 消费 `CanonicalCreateRequest`，生成 atlas 结果。

## CLI 集成设计

第一阶段建议提供正式 CLI 入口，而不是临时脚本。最小目标形态如下：

```bash
video-atlas create \
  --url "https://www.youtube.com/watch?v=..." \
  --output-dir /path/to/atlas
```

```bash
video-atlas fetch \
  --url "https://www.youtube.com/watch?v=..." \
  --output-dir /path/to/fetch-output
```

```bash
video-atlas create \
  --video-file /path/to/video.mp4 \
  --subtitle-file /path/to/subtitles.srt \
  --output-dir /path/to/atlas
```

该入口的行为约束如下：

- 用户或 agent 提供 URL 时，CLI 会先识别来源类型；当前支持标准 YouTube 视频页面和小宇宙单集页面。
- CLI 内部自动完成 acquisition，不要求用户预先下载视频或字幕。
- 当 YouTube 字幕可用时，优先将其作为 canonical workflow 输入。
- 当 YouTube 字幕不可用时，自动回退到现有 transcriber 路径。
- 下载失败应直接报错退出，不应进入后续 workflow。

## 输出契约

当输入来源为 URL 时，acquisition 输出目录应包含稳定 source metadata 文件：

- `SOURCE_INFO.json`
  - 来源类型
  - 原始 URL
  - acquisition 时间
  - 字幕来源类型
- `SOURCE_METADATA.json`
  - 归一化后的来源 metadata
  - 例如标题、作者、发布时间、时长、缩略图等

对于 `create` 命令，这些文件会位于 `run_dir/input/` 中。

对于 `fetch` 命令，当前实现直接将 acquisition 结果写到 `--output-dir` 指定目录，而不再额外创建 `<uid>/input/` 包装层。

## 失败处理与回退策略

- 当视频下载失败时，CLI 应直接失败并返回清晰错误。
- 当 metadata 仅部分缺失时，不应阻断流程；应保留已获取字段继续执行。
- 当 YouTube 字幕可用时，应优先复用，不额外触发本地转写。
- 当 YouTube 字幕不可用时，应由上层 workflow 决定是否回退到既有 transcriber。
- 当 YouTube 视频时长超过 acquisition 阈值时，允许只抓取字幕而不下载视频文件。
- 当小宇宙 URL 只提供音频文件时，应由上层 workflow 决定是否执行转写。
- 当下载成功但字幕抓取与本地转写均失败时，应整体失败，并清楚区分失败阶段。

## 测试与验证策略

### 单元与集成测试

- 校验 URL 识别和标准 YouTube 视频页面约束。
- 校验 acquisition 结果 schema 与 source metadata 写出。
- 校验字幕优先级逻辑：YouTube 字幕优先，本地转写回退次之。
- 通过 mock 下载器验证 CLI 到 canonical workflow 的参数流转。

### 联网 E2E 测试

- 第一阶段允许并建议增加真实联网 acquisition 测试。
- 该测试重点验证：给定真实 YouTube 视频页面 URL，系统是否能够成功完成视频下载、元数据抓取与字幕获取。
- 该测试应被明确标记为受网络、外部站点和环境依赖影响的验证层。
- 联网 E2E 测试不能替代稳定单元测试，但可作为“URL in, local assets out”能力是否真实可用的重要补充。

## 设计约束

- acquisition 层必须与 canonical workflow 职责分离，不能把 URL 下载逻辑直接塞入 `CanonicalAtlasWorkflow`。
- 当前只支持单个标准 YouTube 视频页面 URL 与小宇宙单集 URL，不支持 `youtu.be`、playlist、频道页或批量任务。
- acquisition 结果必须通过显式 schema 传递，不能长期依赖隐式字典。
- source metadata 应使用稳定 schema，对外提供统一消费接口。
- 当前 YouTube 的视频下载阈值通过 acquisition config 配置，默认值为 `1500` 秒。
- derived atlas 链路不是当前设计范围的一部分。
- 更轻量的 `mm_segmentor` 方案不纳入本阶段。

## 当前实现规划

- `src/video_atlas/source_acquisition/`
  - 新增 acquisition 相关模块与 schema
- `src/video_atlas/cli/`
  - 扩展正式 CLI，支持 `--url`
- `src/video_atlas/application/`
  - 增加 input preparation 与 request 组装入口
- `tests/`
  - 增加 acquisition、CLI、source metadata 与联网 E2E 测试
- `docs/`
  - 补充 CLI 和输入来源相关设计与说明
