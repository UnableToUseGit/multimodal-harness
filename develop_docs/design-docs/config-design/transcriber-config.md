# Transcriber 配置设计

## 文档目标

本文档说明 `MM Harness` 当前转录配置结构。

## 配置对象

- 名称：`TranscriberRuntimeConfig`
- 模块：`src/video_atlas/config/models.py`

## 当前主要字段

### 通用字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `enabled` | `bool` | 是否启用转录 |
| `backend` | `str` | 当前默认 `groq_whisper` |
| `sample_rate` | `int` | 音频抽取采样率 |
| `channels` | `int` | 音频抽取声道数 |
| `language` | `str \| None` | 可选语言提示 |

### Groq 相关字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `groq_api_base` | `str` | API 基础地址 |
| `groq_model` | `str` | Whisper 模型名 |
| `groq_api_key_env` | `str` | API key 环境变量名 |
| `groq_response_format` | `str` | 当前默认 `verbose_json` |
| `groq_timestamp_granularities` | `list[str]` | 当前默认 `["segment"]` |
| `groq_max_chunk_size_mb` | `int` | chunking 阈值 |
| `groq_audio_bitrate` | `str` | 上传前转码码率 |

## 当前推荐路径

当前 release 推荐：

- `backend = "groq_whisper"`

原因：

- 普通用户不需要本地部署大型 ASR 模型
- 不需要复杂云存储前置依赖
- 直接获得带时间戳的结构化结果

## 兼容保留字段

配置对象中仍保留了 `faster_whisper` 和 `aliyun_asr` 所需字段，但它们属于兼容性保留，不是当前 release 文档的主推荐路径。

## 当前关键环境变量

- `GROQ_API_KEY`

## 当前设计原则

- 转录默认使用远端轻量服务
- 转录配置属于内部默认配置，不作为用户主要接口
- release 面只要求用户知道 `GROQ_API_KEY`
