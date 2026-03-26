# utils 模块设计

## 文档目标

本文档用于说明 `utils` 模块的设计目标、职责边界、核心接口、依赖关系和关键流程。本文档面向开发者，目标是帮助读者快速理解该模块在系统中的位置以及它应如何被使用和维护。

## 模块概览

- 名称：`utils`
- 路径：`src/video_atlas/utils`
- 主要职责：提供跨 workflow 复用的通用视频、字幕与元数据辅助能力

## 职责与边界

### 职责

- 提供视频帧采样与输入准备辅助能力。
- 提供字幕解析与片段字幕裁剪辅助能力。
- 提供视频元数据读取等通用能力。

### 不负责的内容

- 不负责业务流程编排。
- 不负责 prompt、message builder 或模型调用。
- 不负责领域结果对象的构造与持久化写入。

## 核心接口

### `get_frame_indices`

- 类型：`function`
- 作用：计算视频采样帧位置。
- 输入：
  - 视频长度或时间范围
  - 采样配置
- 输出：
  - 帧索引列表
- 说明：
  - 该接口只负责采样位置计算，不负责帧读取。

### `prepare_video_input`

- 类型：`function`
- 作用：读取并编码采样帧。
- 输入：
  - 视频路径
  - 帧索引
  - 可选的时间范围参数
- 输出：
  - 编码后的帧数据
  - 对应时间信息
- 说明：
  - 该接口常被 message builder 复用。

### `parse_srt`

- 类型：`function`
- 作用：解析 SRT 字幕文件。
- 输入：
  - 字幕路径或字幕文本
- 输出：
  - 结构化字幕片段集合
- 说明：
  - 该接口负责基础解析，不负责业务筛选。

### `get_subtitle_in_segment`

- 类型：`function`
- 作用：获取给定片段范围内的字幕。
- 输入：
  - 结构化字幕集合或字幕路径
  - 片段时间范围
- 输出：
  - 片段范围内的字幕文本或字幕片段
- 说明：
  - 该接口用于字幕裁剪和片段级字幕提取。

### `get_video_property`

- 类型：`function`
- 作用：读取视频元数据。
- 输入：
  - 视频路径
  - 目标属性名
- 输出：
  - 目标视频属性值
- 说明：
  - 该接口用于获取时长、帧率等基础属性。

## 依赖关系

### 上游依赖

- message_builder
- canonical workflow
- derived workflow
- 其他需要基础视频/字幕辅助能力的模块

### 下游依赖

- 本地文件系统
- 视频解码相关依赖
- Python 标准库

## 内部组成

### 帧处理部分

- 角色：负责帧采样索引计算和帧输入准备。
- 边界：
  - 负责底层视频帧相关辅助能力
  - 不负责上层消息构造和模型调用
- 输入：
  - 视频路径
  - 采样配置
  - 时间范围
- 输出：
  - 帧索引
  - 编码后的帧数据

### 字幕处理部分

- 角色：负责 SRT 解析和片段字幕筛选。
- 边界：
  - 负责基础字幕处理
  - 不负责字幕的业务语义解释
- 输入：
  - 字幕路径或字幕文本
  - 片段时间范围
- 输出：
  - 结构化字幕集合
  - 片段范围内字幕

### 元数据部分

- 角色：负责读取视频基础属性。
- 边界：
  - 负责提供通用元数据访问能力
  - 不负责上层业务决策
- 输入：
  - 视频路径
  - 目标属性名
- 输出：
  - 视频属性值

## 关键流程

1. 上层模块传入视频路径、字幕路径或时间范围。
2. 模块根据需求选择帧、字幕或元数据相关辅助逻辑。
3. 模块输出基础处理结果供上层进一步使用。
4. 上层模块在更高层语义中消费这些结果。

## 设计约束

- 该模块应保持通用性，不承载业务语义。
- 该模块应优先提供可复用的基础能力，而不是工作流级逻辑。
- 若某项能力开始承担稳定上层语义，应考虑迁移到更合适的模块。

## 当前实现

- [__init__.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/utils/__init__.py)：统一导出公共辅助函数。
- [frames.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/utils/frames.py)：实现视频帧采样索引与视频输入准备能力。
- [subtitles.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/utils/subtitles.py)：实现字幕解析与片段字幕裁剪能力。
- [video_metadata.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/utils/video_metadata.py)：实现视频元数据读取能力。
- [video_utils.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/utils/video_utils.py)：提供向后兼容的统一工具导出。
