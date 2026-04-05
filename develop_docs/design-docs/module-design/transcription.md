# Transcription 模块设计

## 文档目标

本文档描述 `MM Harness` 当前的转录模块设计，以及字幕在 canonical workflow 中的职责位置。

## 模块位置

- `src/video_atlas/transcription/`

## 模块职责

transcription 模块负责：

- 从音频生成结构化转录片段
- 将转录片段写为 SRT
- 为 workflow 提供统一 `BaseTranscriber` 抽象

它不负责：

- 选择是否应当转录
- URL acquisition
- canonical parsing 或 structure composition

“是否需要转录”属于 workflow 决策；“如何执行转录”属于 transcription 模块职责。

## 当前后端

### 默认后端：`groq_whisper`

当前 release 的默认转录后端。

特点：

- 使用远端 Groq Whisper API
- 返回 `verbose_json`
- 保留 segment timestamps
- 模块内部自动转码和 chunking

### 兼容保留后端

代码中仍保留：

- `faster_whisper`
- `aliyun_asr`

但它们不是当前正式 release 的推荐主路径。

## 当前工作方式

以 `groq_whisper` 为例，转录流程为：

1. 使用 `ffmpeg` 转码为低码率单声道音频
2. 若文件过大，按大小阈值做 chunking
3. 逐 chunk 调用 Groq transcription API
4. 解析带时间戳的 segment 结果
5. 合并为统一 `TranscriptSegment` 列表
6. 交由上层生成 SRT

## 与 workflow 的关系

在 text-first canonical workflow 中：

- 如果已有字幕，则不经过转录
- 如果没有字幕但存在音频/视频，则 workflow 触发转录
- workflow 使用转录结果生成 `subtitles.srt`

所以字幕是 planning 之前的公共资产，而不是 route 之后的附属产物。

## 当前关键依赖

- `ffmpeg`
- `ffprobe`
- `GROQ_API_KEY`

## 当前 release 关注点

当前转录模块的设计重点不是本地部署，而是：

- 降低普通用户使用门槛
- 保持时间戳可用
- 保持长音频可切片处理
