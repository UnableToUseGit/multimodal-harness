# transcription 模块设计

## 文档目标

本文档用于说明 `transcription` 模块的设计目标、职责边界、核心接口、依赖关系和关键流程。本文档面向开发者，目标是帮助读者快速理解该模块在系统中的位置以及它应如何被使用和维护。

## 模块概览

- 名称：`transcription`
- 路径：`src/video_atlas/transcription`
- 主要职责：提供音频抽取、音频转写和字幕文件生成能力

## 职责与边界

### 职责

- 负责从视频中抽取音频。
- 负责定义统一的转写抽象接口与具体实现。
- 负责将转写结果写出为标准字幕文件。

### 不负责的内容

- 不负责视频切分或 atlas 生成。
- 不负责字幕在业务流程中的消费逻辑。
- 不负责 review 与持久化目录组织。

## 核心接口

### 抽象基类接口：`BaseTranscriber`

- 类型：`abstract class`
- 作用：定义统一的转写协议。
- 初始化输入：
  - 无特殊要求
- 对外暴露的方法：
  - `transcribe_audio(...)`：接收音频输入并返回统一的转写片段集合。
- 关键方法的输入与输出：
  - `transcribe_audio(...)`
    - 输入：
      - 音频路径或等价音频输入
    - 输出：
      - 统一的转写片段集合
- 说明：
  - 具体转写实现应通过该抽象接入系统。
  - 抽象基类本身不负责具体引擎调用。

### `generate_subtitles_for_video`

- 类型：`function`
- 作用：完成从视频到字幕文件的主流程。
- 输入：
  - 视频路径
  - 目标字幕路径
  - 转写器实例
- 输出：
  - 标准字幕文件路径
  - 必要时返回中间转写结果
- 说明：
  - 该接口是上层 workflow 最常用的字幕生成入口。

### 具体实现类接口：`FasterWhisperTranscriber`

- 类型：`concrete class`
- 作用：提供当前的 Faster Whisper 转写实现。
- 初始化输入：
  - 可选的 `config`
    - `FasterWhisperConfig`
    - 或等价 `dict`
    - 未提供时使用默认配置
- 对外暴露的方法：
  - `transcribe_audio(...)`：调用 Faster Whisper 完成音频转写。
- 关键方法的输入与输出：
  - `transcribe_audio(...)`
    - 输入：
      - 音频路径
    - 输出：
      - 统一的转写片段集合
- 说明：
  - 该实现类依赖具体转写引擎与运行环境。
  - 它实现 `BaseTranscriber` 定义的统一转写协议。

### `extract_audio_ffmpeg`

- 类型：`function`
- 作用：从视频中抽取规范化音频。
- 输入：
  - 视频路径
  - 目标音频路径
- 输出：
  - 可供转写使用的音频文件
- 说明：
  - 该接口仅负责音频准备，不负责转写。

### `transcript_segments_to_srt`

- 类型：`function`
- 作用：将转写结果转换为 SRT 文本。
- 输入：
  - 转写片段集合
- 输出：
  - SRT 格式文本
- 说明：
  - 该接口负责字幕格式化，不负责转写片段生成。

## 依赖关系

### 上游依赖

- canonical workflow
- 其他需要字幕生成的上层模块

### 下游依赖

- 音频抽取工具
- 具体转写引擎
- 字幕格式写出逻辑

## 内部组成

### 抽象接口部分

- 角色：定义统一转写协议。
- 边界：
  - 负责声明统一调用方式
  - 不负责具体引擎实现
- 输入：
  - 转写请求
- 输出：
  - 统一的转写接口约束

### 音频准备部分

- 角色：从视频中抽取可转写音频。
- 边界：
  - 负责音频抽取和格式准备
  - 不负责转写和字幕写出
- 输入：
  - 视频路径
  - 目标音频路径
- 输出：
  - 音频文件

### 转写流程部分

- 角色：驱动转写与字幕写出的主流程。
- 边界：
  - 负责串联音频准备、转写调用和字幕生成
  - 不负责上层业务语义消费
- 输入：
  - 视频路径
  - 转写器实例
  - 目标字幕路径
- 输出：
  - 转写片段集合
  - 字幕文件路径

### 字幕写出部分

- 角色：将转写结果转换为 SRT。
- 边界：
  - 负责字幕格式化
  - 不负责音频抽取和转写执行
- 输入：
  - 转写片段集合
- 输出：
  - SRT 文本或字幕文件内容

## 关键流程

1. 上层模块提供视频路径和转写器。
2. 模块先抽取规范化音频。
3. 模块调用具体转写实现获取转写片段。
4. 模块将转写片段转换为字幕文件并返回结果路径。

## 设计约束

- 该模块应通过统一转写抽象接入具体引擎。
- 字幕生成流程应与主 workflow 解耦。
- 该模块只负责转写与字幕生成，不负责字幕在上层的使用语义。

## 当前实现

- [__init__.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/transcription/__init__.py)：导出转写模块的公共接口。
- [base.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/transcription/base.py)：定义转写器抽象接口。
- [audio_prep.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/transcription/audio_prep.py)：实现音频抽取逻辑。
- [pipeline.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/transcription/pipeline.py)：实现从视频到字幕文件的主流程。
- [srt_writer.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/transcription/srt_writer.py)：实现 SRT 文本生成逻辑。
- [types.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/transcription/types.py)：定义转写结果片段类型。
- [faster_whisper.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/transcription/faster_whisper.py)：提供当前的 Faster Whisper 转写实现。
