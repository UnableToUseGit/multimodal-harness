# 在 transcription 模块中接入 Groq Whisper 技术路线

## 背景

当前 `transcription` 模块正式支持两条转录路线：

- 本地 `FasterWhisperTranscriber`
- 云端 `AliyunAsrTranscriber`

这两条路线都存在明显的普通用户接入门槛：

- `faster_whisper` 依赖本地模型、运行环境和算力，不适合作为面向普通用户与 agent 的默认方案
- `aliyun_asr` 依赖 OSS 上传与签名 URL，配置复杂，接入成本较高

当前项目的产品方向是让普通用户在本地配合 agent 直接使用 `VideoAtlas`。在这个目标下，`transcription` 需要一条更轻量的默认云端路线。

## 结论

建议在 `transcription` 模块中新增正式 backend：

- `groq_whisper`

该 backend 的定位是：

- 作为面向普通用户的轻量远程转录方案
- 直接上传本地音频文件到 Groq Speech-to-Text API
- 在模块内部完成转码、分片、API 调用和结果合并
- 对上层继续暴露统一的 `BaseTranscriber` 接口

## 关键依据

### 1. Groq 可返回时间戳

Groq Speech-to-Text 同步接口支持 `response_format="verbose_json"`，并支持：

- `timestamp_granularities=["segment"]`
- `timestamp_granularities=["word"]`

这意味着它可以返回带时间戳的结构化结果，能够自然映射到 `TranscriptSegment`，适合当前系统的 SRT 生成链路。

### 2. Groq 单次上传大小有限，需要模块内 chunking

Groq 文档当前显示：

- 免费层最大文件大小为 `25 MB`
- 开发层最大文件大小为 `100 MB`
- 但直接附件上传上限仍为 `25 MB`

因此不能假设一次请求可以处理任意长音频。`transcription` 模块内部应内置：

- 音频转码
- 降码率
- 大文件切片
- 分片结果合并

### 3. Groq 同步接口是单文件接口

同步转录接口参数形态是：

- 单个 `file`
- 或单个 `url`

它不是“一次请求上传多个音频文件”的接口。若需要并行处理多个音频，只能由客户端发起多个请求；若需要服务端批量任务，可后续再评估 Groq Batch API。

对当前 `VideoAtlas` 来说，第一阶段不需要 Batch API，内置分片串行上传已足够。

## 设计原则

### 统一接口

`GroqWhisperTranscriber` 必须实现：

- `BaseTranscriber.transcribe_audio(...) -> list[TranscriptSegment]`

上层 workflow 不应感知：

- Groq API 请求格式
- 文件大小限制
- 分片细节
- 速率限制重试逻辑

### 不输出纯文本，必须输出时间轴结果

虽然外部脚本可通过 `response_format=text` 获取纯文本，但这不适合 `VideoAtlas`。

正式实现必须请求：

- `verbose_json`

并优先使用：

- `segment` 级时间戳

这样才能稳定生成 SRT，并支撑后续的 text-first parsing。

### 模块内部完成音频规范化

模块内应默认完成：

- 转为单声道
- 降低码率
- 必要时切片

这与外部脚本中的处理思路一致，但应内聚在 `transcription` 模块内部，而不是要求用户或 application layer 预处理。

## 建议实现

### 配置层

在 `TranscriberRuntimeConfig` 中新增 `groq_whisper` 所需字段：

- `groq_api_base`
- `groq_model`
- `groq_api_key_env`
- `groq_language`
- `groq_response_format`
- `groq_timestamp_granularities`
- `groq_max_chunk_size_mb`
- `groq_audio_bitrate`
- `groq_retry_on_rate_limit`

### provider 实现层

新增：

- `src/video_atlas/transcription/groq_whisper.py`

建议职责包括：

- 初始化配置与 API 凭证
- 将输入音频转码为低码率单声道文件
- 按大小阈值切片
- 调 Groq API 获取结构化转录结果
- 解析并合并为统一 `TranscriptSegment`

### 工厂与导出

需要同步更新：

- `src/video_atlas/config/factories.py`
- `src/video_atlas/config/models.py`
- `src/video_atlas/transcription/__init__.py`

## 第一阶段范围

第一阶段只做：

- `groq_whisper` 同步接口
- 单音频输入
- 模块内部 chunking
- `segment` 级时间戳
- 统一 `TranscriptSegment` 输出

第一阶段不做：

- Groq Batch API
- 单请求多文件上传
- provider 级并发调度
- 复杂语言自动推断策略

## 后续默认策略建议

待实现稳定后，建议将 `groq_whisper` 作为面向普通用户的默认转录 backend。

保留：

- `faster_whisper` 作为本地高级用户可选项
- `aliyun_asr` 作为已部署阿里云资源用户的可选项

## 参考资料

- Groq Speech-to-Text 文档：
  <https://console.groq.com/docs/speech-to-text>
- Groq Batch API 文档：
  <https://console.groq.com/docs/batch>
