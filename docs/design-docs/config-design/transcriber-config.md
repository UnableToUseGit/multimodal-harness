# Transcriber 配置设计

## 文档目标

本文档用于说明 `Transcriber` 相关配置的结构、字段定义、默认值、来源和约束。本文档面向开发者与维护者，目标是帮助读者理解 transcriber 配置控制什么、应如何提供，以及它如何影响字幕生成行为。

## 配置对象概览

- 名称：`TranscriberRuntimeConfig`
- 作用：描述字幕生成阶段的转写器运行时配置
- 实现形式：`dataclass`
- 所属模块：`src/video_atlas/config/models.py`

## 配置项定义

| 配置项 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `enabled` | `bool` | 否 | `True` | 是否启用转写器 |
| `backend` | `str` | 否 | `"groq_whisper"` | 转写后端，当前支持 `groq_whisper`、`faster_whisper` 与 `aliyun_asr` |
| `sample_rate` | `int` | 否 | `16000` | 音频抽取采样率 |
| `channels` | `int` | 否 | `1` | 音频抽取声道数 |
| `model_size_or_path` | `str` | 否 | `"small"` | Faster Whisper 模型标识或路径 |
| `device` | `str` | 否 | `"cpu"` | 运行设备 |
| `compute_type` | `str` | 否 | `"int8"` | 推理精度类型 |
| `language` | `str \| None` | 否 | `None` | 目标语言 |
| `vad_filter` | `bool` | 否 | `True` | 是否启用 VAD 过滤 |
| `min_silence_duration_ms` | `int` | 否 | `500` | 最小静音时长 |
| `use_batched_inference` | `bool` | 否 | `False` | 是否启用 batched inference |
| `batch_size` | `int` | 否 | `8` | batched inference 的 batch 大小 |
| `aliyun_api_base` | `str` | 否 | `"https://dashscope.aliyuncs.com/api/v1"` | 阿里云 DashScope API 基础地址 |
| `aliyun_model` | `str` | 否 | `"fun-asr"` | 阿里云 ASR 模型标识 |
| `aliyun_language_hints` | `list[str]` | 否 | `[]` | 阿里云语言提示 |
| `aliyun_diarization_enabled` | `bool` | 否 | `True` | 是否启用说话人分离 |
| `aliyun_oss_endpoint` | `str \| None` | 否 | `None` | 阿里云 OSS endpoint |
| `aliyun_oss_bucket_name` | `str \| None` | 否 | `None` | 阿里云 OSS bucket 名称 |
| `aliyun_oss_access_key_id_env` | `str` | 否 | `"OSS_ACCESS_KEY_ID"` | OSS Access Key ID 环境变量名 |
| `aliyun_oss_access_key_secret_env` | `str` | 否 | `"OSS_ACCESS_KEY_SECRET"` | OSS Access Key Secret 环境变量名 |
| `aliyun_api_key_env` | `str` | 否 | `"ALIYUN_API_KEY"` | DashScope API Key 环境变量名 |
| `aliyun_oss_prefix` | `str` | 否 | `"audios/"` | OSS 对象前缀 |
| `aliyun_signed_url_expires_sec` | `int` | 否 | `3600` | 签名下载 URL 过期时间 |
| `aliyun_poll_interval_sec` | `float` | 否 | `2.0` | 轮询间隔 |
| `aliyun_poll_timeout_sec` | `float` | 否 | `900.0` | 轮询超时时间 |
| `groq_api_base` | `str` | 否 | `"https://api.groq.com/openai/v1"` | Groq Speech-to-Text API 基础地址 |
| `groq_model` | `str` | 否 | `"whisper-large-v3"` | Groq 转写模型标识 |
| `groq_api_key_env` | `str` | 否 | `"GROQ_API_KEY"` | Groq API Key 环境变量名 |
| `groq_language` | `str \| None` | 否 | `None` | Groq 转写语言提示 |
| `groq_response_format` | `str` | 否 | `"verbose_json"` | Groq 返回格式 |
| `groq_timestamp_granularities` | `list[str]` | 否 | `["segment"]` | Groq 时间戳粒度 |
| `groq_max_chunk_size_mb` | `int` | 否 | `20` | 模块内切片阈值 |
| `groq_audio_bitrate` | `str` | 否 | `"64k"` | 上传前转码码率 |
| `groq_retry_on_rate_limit` | `bool` | 否 | `True` | 遇到 429 是否重试 |
| `groq_request_timeout_sec` | `float` | 否 | `300.0` | 单请求超时时间 |
| `retain_remote_artifacts` | `bool` | 否 | `False` | 是否保留远端 OSS 临时对象 |

## 配置项说明

### `enabled`

- 语义：决定系统是否启用自动字幕生成能力。
- 约束：布尔值。
- 对行为的影响：为 `False` 时，`build_transcriber(...)` 返回 `None`。

### `backend`

- 语义：标识转写后端类型。
- 约束：当前支持 `groq_whisper`、`faster_whisper` 和 `aliyun_asr`。
- 对行为的影响：决定使用哪一种具体转写实现。

### `sample_rate`

- 语义：控制音频抽取阶段的采样率。
- 约束：应为正整数。
- 对行为的影响：在音频抽取阶段传递给 `extract_audio_ffmpeg(...)`。

### `channels`

- 语义：控制音频抽取阶段的声道数。
- 约束：应为正整数。
- 对行为的影响：在音频抽取阶段传递给 `extract_audio_ffmpeg(...)`。

### `model_size_or_path`

- 语义：指定 Faster Whisper 模型名称或本地路径。
- 约束：应为合法模型标识或可访问路径。
- 对行为的影响：决定转写模型体量与精度。

### `device`

- 语义：指定推理设备。
- 约束：应与运行环境匹配。
- 对行为的影响：决定 CPU/GPU 推理路径。

### `compute_type`

- 语义：指定推理精度类型。
- 约束：应为后端支持的值。
- 对行为的影响：决定速度、显存与精度之间的平衡。

### `language`

- 语义：指定转写语言。
- 约束：可为空。
- 对行为的影响：为空时由后端自行推断。

### `vad_filter`

- 语义：决定是否启用语音活动检测。
- 约束：布尔值。
- 对行为的影响：影响空白段过滤和转写鲁棒性。

### `min_silence_duration_ms`

- 语义：控制 VAD 中最小静音时长。
- 约束：应为非负整数。
- 对行为的影响：通过 `vad_parameters` 传递到底层实现。

### `use_batched_inference`

- 语义：决定是否启用批量推理模式。
- 约束：布尔值。
- 对行为的影响：为 `True` 时使用 `BatchedInferencePipeline`。

### `batch_size`

- 语义：控制批量推理的 batch 大小。
- 约束：应为正整数。
- 对行为的影响：只在 `use_batched_inference=True` 时生效。

### `aliyun_api_base` ~ `retain_remote_artifacts`

- 语义：控制阿里云 OSS 与 DashScope ASR 路线的 provider 配置、凭证来源、轮询行为和远端对象管理。
- 约束：
  - 这些字段只在 `backend="aliyun_asr"` 时生效。
  - `aliyun_oss_endpoint` 和 `aliyun_oss_bucket_name` 在阿里云路线下应显式提供。
  - `aliyun_api_key_env`、`aliyun_oss_access_key_id_env` 和 `aliyun_oss_access_key_secret_env` 应指向有效环境变量。
- 对行为的影响：
  - 决定阿里云转写请求的提交方式、OSS 临时对象组织方式与结果轮询行为。

### `groq_api_base` ~ `groq_request_timeout_sec`

- 语义：控制 Groq Whisper 路线的 provider 配置、认证方式、响应格式和模块内 chunking 行为。
- 约束：
  - 这些字段只在 `backend="groq_whisper"` 时生效。
  - `groq_api_key_env` 应指向有效环境变量。
  - `groq_response_format` 当前应为结构化格式，推荐 `verbose_json`。
  - `groq_timestamp_granularities` 当前推荐使用 `["segment"]`。
- 对行为的影响：
  - 决定 Groq API 调用方式、返回结果结构以及大文件是否需要切片上传。

## 默认值与必填项

### 默认值策略

- 若未显式提供配置，系统会使用 `TranscriberRuntimeConfig` 的默认值
- `build_transcriber(...)` 会将该配置映射到：
  - `GroqWhisperTranscriber`
  - `FasterWhisperTranscriber`
  - `AliyunAsrTranscriber`
- 具体实现类在未显式提供 config 时，也会回退到各自默认配置

### 必填项

- 当前没有绝对必填字段
- 但若启用转写能力且使用 `groq_whisper`，必须提供可用的 Groq API Key
- 若使用 `faster_whisper`，运行环境必须已安装 `faster-whisper` 及其依赖
- 若 `backend="aliyun_asr"`，还必须提供可用的阿里云 OSS 与 DashScope 凭证

## 配置来源

- 代码内默认值
- JSON 配置文件

### 优先级约定

1. JSON 配置文件中的 `transcriber`
2. dataclass 默认值

## 校验规则与约束

- `backend` 当前只能为 `groq_whisper`、`faster_whisper` 或 `aliyun_asr`
- `batch_size` 必须为正整数
- `min_silence_duration_ms` 不应为负数
- 若 `enabled=False`，下游不应假定转写器实例存在
- 若 `backend="aliyun_asr"`，`aliyun_oss_endpoint` 与 `aliyun_oss_bucket_name` 不应为空

## 使用位置

- `build_transcriber(...)` 会消费该配置并实例化具体 transcriber
- canonical workflow 会在字幕缺失且允许自动补全时消费该 transcriber
- 当前 derived workflow 不直接依赖该配置

## 示例

```python
TranscriberRuntimeConfig(
    enabled=True,
    backend="groq_whisper",
    groq_model="whisper-large-v3",
    groq_language="zh",
    groq_response_format="verbose_json",
    groq_timestamp_granularities=["segment"],
    groq_max_chunk_size_mb=20,
    groq_audio_bitrate="64k",
)
```

```python
TranscriberRuntimeConfig(
    enabled=True,
    backend="aliyun_asr",
    sample_rate=16000,
    channels=1,
    aliyun_model="fun-asr",
    aliyun_language_hints=["zh", "en"],
    aliyun_diarization_enabled=True,
    aliyun_oss_endpoint="https://oss-cn-beijing.aliyuncs.com",
    aliyun_oss_bucket_name="videoatlas-audio",
    aliyun_api_key_env="ALIYUN_API_KEY",
)
```
