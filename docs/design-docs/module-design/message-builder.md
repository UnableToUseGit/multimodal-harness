# message_builder 模块设计

## 文档目标

本文档用于说明 `message_builder` 模块的设计目标、职责边界、核心接口、依赖关系和关键流程。本文档面向开发者，目标是帮助读者快速理解该模块在系统中的位置以及它应如何被使用和维护。

## 模块概览

- 名称：`message_builder`
- 路径：`src/video_atlas/message_builder`
- 主要职责：为上层 workflow 构造统一的模型输入消息，尤其是文本与视频相关消息结构

## 职责与边界

### 职责

- 负责构造文本消息与视频消息的统一结构。
- 负责将视频路径与采样结果转化为模型可消费的消息载荷。
- 为上层 workflow 提供稳定、可复用的 message 构造入口。

### 不负责的内容

- 不负责 prompt 模板设计。
- 不负责模型请求发送。
- 不负责模型输出解析或业务语义解释。

## 核心接口

### `build_text_messages`

- 类型：`function`
- 作用：构造纯文本形式的模型输入消息。
- 输入：
  - `system_prompt`
  - `user_prompt`
- 输出：
  - 标准化的文本 `messages`
- 说明：
  - 适用于不需要视频内容参与的调用场景。

### `build_video_messages`

- 类型：`function`
- 作用：基于已准备好的帧数据构造视频消息。
- 输入：
  - `system_prompt`
  - `user_prompt`
  - 已编码的帧数据
  - 时间戳信息
  - 可选的字幕文本
- 输出：
  - 可直接传入 generator 的视频 `messages`
- 说明：
  - 适用于上层已经完成采样或帧准备的场景。

### `build_video_messages_from_path`

- 类型：`function`
- 作用：从视频路径出发，完成采样并构造视频消息。
- 输入：
  - `system_prompt`
  - `user_prompt`
  - 视频路径
  - 时间范围
  - 采样配置
  - 可选的字幕文本
- 输出：
  - 经过采样和编码后的标准化视频 `messages`
- 说明：
  - 该接口同时覆盖视频预处理与消息构造，是 workflow 中最常用的视频消息入口。

## 依赖关系

### 上游依赖

- canonical workflow
- derived workflow
- 其他需要构造模型消息的上层模块

### 下游依赖

- `schemas` 中与采样配置相关的 schema
- `utils` 中与视频帧提取相关的辅助能力

## 内部组成

### 文本消息构造部分

- 角色：构造纯文本形式的模型输入。
- 边界：
  - 负责组织 system/user 两类文本消息
  - 不负责视频采样和模型请求发送
- 输入：
  - `system_prompt`
  - `user_prompt`
- 输出：
  - 纯文本 `messages`

### 视频消息构造部分

- 角色：将帧数据、时间信息和可选字幕组织成统一视频消息。
- 边界：
  - 负责消息载荷组织
  - 不负责视频路径读取和采样策略决策
- 输入：
  - 已编码帧数据
  - 时间戳
  - prompt 文本
  - 可选字幕文本
- 输出：
  - 视频 `messages`

### 路径驱动构造部分

- 角色：从视频路径出发完成采样准备并生成最终消息。
- 边界：
  - 负责调用底层视频辅助能力完成采样准备
  - 不负责下游模型调用
- 输入：
  - 视频路径
  - 时间范围
  - 采样配置
  - prompt 文本
  - 可选字幕文本
- 输出：
  - 标准化视频 `messages`

## 关键流程

1. 上层模块提供 prompt、视频路径或帧数据。
2. 模块根据输入类型选择文本或视频消息构造路径。
3. 若输入为视频路径，则先完成帧采样与帧编码准备。
4. 模块输出统一的 `messages` 结构供 generator 使用。

## 设计约束

- 该模块只负责消息构造，不负责模型调用。
- 该模块应保持与具体业务流程解耦。
- 上层 workflow 应通过该模块构造消息，而不是重复内联消息结构。

## 当前实现

- [__init__.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/message_builder/__init__.py)：导出模块对外可用的消息构造接口。
- [messages.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/message_builder/messages.py)：实现文本消息、视频消息以及基于视频路径的消息构造逻辑。
