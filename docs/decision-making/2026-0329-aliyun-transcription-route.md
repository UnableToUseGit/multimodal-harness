# 在 transcription 模块中接入阿里云 ASR 技术路线

## 背景

当前 `transcription` 模块只正式支持本地 `FasterWhisperTranscriber`。这条路线存在两个现实问题：

- 本地模型转写速度较慢，已经成为 canonical atlas workflow 的明显性能瓶颈。
- 在部分中文音频场景中，本地模型的转写质量不稳定，尤其在长视频、多人说话或中英混杂场景下效果一般。

为此，需要在 `transcription` 模块中正式接入一条云端转写路线，使系统可以在本地转写与云端转写之间按配置切换。

当前已经有一份端到端实验脚本：

- [run_aliyun_transcription.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/scripts/run_aliyun_transcription.py)

该脚本验证了如下链路可行：

1. 从视频中抽取音频
2. 将音频上传到阿里云 OSS
3. 通过 DashScope ASR 接口发起异步转写
4. 轮询转写结果
5. 下载转写结果并转换为统一的 `TranscriptSegment`
6. 写出 SRT 文件

下一步需要把这条路线从实验脚本沉淀为 `transcription` 模块中的正式实现。

## 目标

- 在 `transcription` 模块中新增一个与 `FasterWhisperTranscriber` 并列的正式实现。
- 保持上层 workflow 不感知具体转写后端。
- 让 `build_transcriber(...)` 可以根据配置构建本地或阿里云转写实现。
- 将 OSS 上传、ASR 任务提交、结果轮询和结果解析封装在 `transcription` 模块内部。
- 让阿里云返回结果最终仍统一为 `list[TranscriptSegment]`，以保持现有字幕流水线不变。

## 非目标

- 本轮不改 canonical workflow 的字幕主流程接口。
- 本轮不引入多家云厂商统一抽象层；只接入阿里云这一条云端路线。
- 本轮不做大规模的转写后处理优化，例如断句修复、专有名词归一化或实体统一命名。
- 本轮不把 OSS 上传能力抽成跨模块的通用云存储模块。

## 方案结论

采用如下总体方案：

- 在 `transcription` 模块中新增正式实现类：`AliyunAsrTranscriber`
- 该类实现 `BaseTranscriber`
- 上层继续只依赖 `BaseTranscriber.transcribe_audio(...)`
- `build_transcriber(...)` 根据 `TranscriberRuntimeConfig.backend` 构造：
  - `faster_whisper`
  - `aliyun_asr`

同时，在 `AliyunAsrTranscriber` 内部继续拆分出若干明确组件，避免把实验脚本直接搬进单个文件。

## 模块内设计

### 公开接口

新增后，`transcription` 模块的正式转写实现包括：

- `FasterWhisperTranscriber`
- `AliyunAsrTranscriber`

两者都实现：

- `BaseTranscriber.transcribe_audio(audio_path: str | Path) -> list[TranscriptSegment]`

因此，上层模块仍只需要依赖统一抽象接口，而不需要知道具体使用了本地模型还是云端服务。

### 内部组件划分

建议在 `transcription` 模块中新增如下内部组件：

#### 1. `aliyun_types.py`

职责：

- 定义阿里云转写路线所需的配置对象和中间结果结构。

建议至少包含：

- `AliyunOssConfig`
- `AliyunAsrConfig`

这两个对象只服务于阿里云路线，不进入上层 workflow。

#### 2. `aliyun_oss.py`

职责：

- 负责 OSS 上传和签名下载 URL 生成。

边界：

- 只处理 OSS 访问
- 不负责转写任务提交
- 不负责结果解析

建议暴露能力：

- `upload_file(...)`
- `get_signed_download_url(...)`

#### 3. `aliyun_asr.py`

职责：

- 负责调用 DashScope ASR 接口。
- 负责异步任务提交、轮询、结果下载和基础错误检查。

边界：

- 只负责阿里云 ASR 任务生命周期
- 不负责 SRT 写出
- 不负责将结果转换为通用字幕文件

建议暴露能力：

- `submit_transcription_task(...)`
- `wait_transcription_result(...)`
- `download_transcription_result(...)`

#### 4. `aliyun_transcriber.py`

职责：

- 实现 `AliyunAsrTranscriber`
- 串联 OSS、ASR、结果归一化三部分
- 将云端结果统一转换为 `list[TranscriptSegment]`

边界：

- 对外只暴露标准 `BaseTranscriber` 接口
- 不把阿里云原始结果结构泄漏到模块外部

### 推荐文件组织

```text
src/video_atlas/transcription/
├── base.py
├── audio_prep.py
├── pipeline.py
├── srt_writer.py
├── types.py
├── faster_whisper.py
├── aliyun_types.py
├── aliyun_oss.py
├── aliyun_asr.py
└── aliyun_transcriber.py
```

## 配置设计

当前 `TranscriberRuntimeConfig` 只适配 `faster_whisper`。如果要正式接入阿里云路线，配置需要扩展，但仍应保持一个统一入口。

### 配置原则

- 上层仍使用单一 `TranscriberRuntimeConfig`
- `backend` 决定使用哪种具体实现
- 只有阿里云后端需要的字段在 `backend="aliyun_asr"` 时才生效
- 不把云端 provider 特有配置散落到 workflow 或脚本层

### 建议新增字段

在 `TranscriberRuntimeConfig` 中补充：

- `backend: "faster_whisper" | "aliyun_asr"`
- `sample_rate: int = 16000`
- `channels: int = 1`
- `aliyun_api_base: str | None = None`
- `aliyun_model: str = "fun-asr"`
- `aliyun_language_hints: list[str] = field(default_factory=list)`
- `aliyun_diarization_enabled: bool = True`
- `aliyun_oss_endpoint: str | None = None`
- `aliyun_oss_bucket_name: str | None = None`
- `aliyun_oss_access_key_id_env: str = "OSS_ACCESS_KEY_ID"`
- `aliyun_oss_access_key_secret_env: str = "OSS_ACCESS_KEY_SECRET"`
- `aliyun_api_key_env: str = "ALIYUN_API_KEY"`
- `aliyun_oss_prefix: str = "audios/"`
- `aliyun_signed_url_expires_sec: int = 3600`
- `aliyun_poll_interval_sec: float = 2.0`
- `aliyun_poll_timeout_sec: float = 900.0`
- `retain_remote_artifacts: bool = False`

### 配置来源

保持现有约定：

- JSON 配置文件
- 环境变量

其中：

- JSON 配置文件负责声明字段和值
- 环境变量负责存放敏感信息或 provider 凭证

## 关键流程

阿里云路线的主流程如下：

1. 上层通过 `build_transcriber(...)` 构造 `AliyunAsrTranscriber`
2. `generate_subtitles_for_video(...)` 仍先调用 `extract_audio_ffmpeg(...)`
3. `AliyunAsrTranscriber.transcribe_audio(...)` 接收本地音频路径
4. 内部先将音频上传到 OSS
5. 为已上传对象生成带时效的签名下载 URL
6. 将该 URL 交给 DashScope ASR 发起异步转写任务
7. 轮询任务完成状态
8. 下载原始转写结果 JSON
9. 将原始结果解析为统一的 `TranscriptSegment`
10. 现有 `transcript_segments_to_srt(...)` 与 `pipeline.py` 继续完成字幕写出

这意味着：

- 现有字幕流水线无需整体重写
- 变化被限制在 transcriber 的具体实现层

## 错误处理与失败语义

阿里云路线需要显式定义失败语义，避免云端异常直接泄漏为不可解释的错误。

### 需要显式处理的失败类型

- OSS 凭证缺失
- OSS 上传失败
- DashScope API key 缺失
- 任务提交失败
- 任务轮询超时
- 任务状态失败
- 结果下载失败
- 返回 JSON 结构不符合预期

### 统一处理原则

- 所有 provider 特有异常应在 `AliyunAsrTranscriber` 内部转换为可读的 `RuntimeError` 或更明确的模块内异常
- 错误信息应包含：
  - 所处阶段
  - 关键对象标识
  - 失败原因摘要
- 不应将原始 provider 响应结构直接暴露给上层 workflow

## 临时文件与远端对象管理

阿里云路线会新增两类资源：

- 本地抽取的音频文件
- 远端 OSS 对象

需要遵守以下约束：

- 本地音频继续沿用现有字幕流水线的临时文件处理方式
- 远端 OSS 对象默认按前缀组织，例如：
  - `audios/<uuid>/audio.wav`
- 默认不长期保留远端对象，除非配置显式要求
- 若启用保留远端对象，应主要用于调试与排障

## 与现有脚本的关系

[run_aliyun_transcription.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/scripts/run_aliyun_transcription.py) 当前的定位应从“未来实现本体”转为：

- 验证脚本
- 对接示例
- 排障脚本

正式实现落地后，不应让上层模块依赖该脚本。

## 测试设计

实现阶段至少需要补以下测试：

### 单元测试

- 阿里云原始 JSON 到 `TranscriptSegment` 的解析
- OSS object key 构造逻辑
- 轮询超时与失败状态处理
- 配置校验与缺失凭证报错

### 集成风格测试

- `build_transcriber(...)` 能根据 `backend="aliyun_asr"` 正确返回实现类
- `generate_subtitles_for_video(...)` 在 mock 掉云端依赖后能跑通完整流水线

### 回归测试

- `faster_whisper` 路线不受新后端影响
- `backend` 非法值仍能清晰报错

## 风险与取舍

### 收益

- 提升长视频字幕生成速度
- 提升中文或混合语言场景下的转写质量
- 将云端转写纳入正式模块边界，而不是依赖临时脚本

### 新风险

- 引入外部服务依赖和网络失败模式
- 配置复杂度上升
- 增加 OSS 临时对象清理责任
- provider SDK 与环境依赖需要单独管理

## 实施建议

建议实现顺序如下：

1. 先新增 `AliyunAsrTranscriber` 所需的内部组件与结果归一化逻辑
2. 扩展 `TranscriberRuntimeConfig`
3. 更新 `build_transcriber(...)`
4. 补单元测试和集成测试
5. 最后再更新 `transcription` 模块设计文档与 `transcriber-config` 文档，将该路线从“规划”切换为“当前实现”

