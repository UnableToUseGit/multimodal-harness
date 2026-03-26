# generators 模块设计

## 文档目标

本文档用于说明 `generators` 模块的设计目标、职责边界、核心接口、依赖关系和关键流程。本文档面向开发者，目标是帮助读者快速理解该模块在系统中的位置以及它应如何被使用和维护。

## 模块概览

- 名称：`generators`
- 路径：`src/video_atlas/generators`
- 主要职责：为上层 workflow 提供统一的模型调用抽象与具体生成实现

## 职责与边界

### 职责

- 定义统一的生成器抽象接口，使上层模块能够以一致方式调用模型。
- 将上层提供的 `prompt`、`messages`、`schema` 和额外参数转换为底层模型请求。
- 对模型响应进行最基本的归一化封装，使上层获得稳定的返回结构。

### 不负责的内容

- 不负责 prompt 模板设计。
- 不负责 message builder 或多模态输入预处理。
- 不负责业务语义解析、领域结果构造或持久化写入。

## 核心接口

### 抽象基类接口：`BaseGenerator`

- 类型：`abstract class`
- 作用：定义生成器的统一协议，约束上层模块如何发起模型调用。
- 初始化输入：
  - 可选的 `config`
- 对外暴露的方法：
  - `generate_single(...)`：执行单次模型生成请求。
  - `generate_batch(...)`：执行多条请求的批量生成。
- 关键方法的输入与输出：
  - `generate_single(...)`
    - 输入：
      - 纯文本 `prompt` 或结构化 `messages`
      - 可选的 `schema`
      - 可选的 `extra_body`
    - 输出：
      - 标准化结果字典
      - 生成文本 `text`
      - 原始响应 `response`
  - `generate_batch(...)`
    - 输入：
      - 多组 `prompt` 或 `messages`
      - 可选的批量配置参数
    - 输出：
      - 与输入顺序对应的一组标准化结果
- 说明：
  - 上层模块应优先依赖该抽象，而不是直接依赖具体实现。
  - 具体实现可以对批量行为做内部优化，但对上层应保持统一接口语义。

### 具体实现类接口：`OpenAICompatibleGenerator`

- 类型：`concrete class`
- 作用：提供当前的 OpenAI-compatible 模型调用实现。
- 初始化输入：
  - `config`
    - 至少应包含 `model_name`
    - 可选包含 `temperature`、`top_p`、`max_tokens`、`extra_body`
  - 运行环境中的 API 配置
    - `VIDEO_ATLAS_API_BASE`
    - `VIDEO_ATLAS_API_KEY`
- 对外暴露的方法：
  - `generate_single(...)`：将单次请求映射为底层服务调用。
  - `generate_batch(...)`：将批量请求映射为底层服务调用。
- 关键方法的输入与输出：
  - `generate_single(...)`
    - 输入：
      - 纯文本 `prompt` 或结构化 `messages`
      - 可选的 `schema`
      - 可选的 `extra_body`
      - 运行时配置
    - 输出：
      - 标准化结果字典
      - 生成文本 `text`
      - 原始响应 `response`
- 说明：
  - 该实现类依赖具体模型服务配置与网络调用能力。
  - 它是 `BaseGenerator` 的当前实现，而不是新的上层协议。

## 依赖关系

### 上游依赖

- canonical workflow、derived workflow 等上层业务流程模块
- 配置构建与工厂逻辑

### 下游依赖

- 运行时配置与环境设置
- 外部模型服务接口
- Python 标准库中的网络与序列化能力

## 内部组成

### 抽象接口部分

- 角色：定义统一生成器协议，约束上层如何发起模型调用。
- 边界：
  - 负责声明单次生成与批量生成的统一调用方式
  - 不负责任何具体模型服务请求发送
- 输入：
  - 上层定义的生成需求
- 输出：
  - 稳定的抽象接口约束

### 具体实现部分

- 角色：将统一接口映射到具体模型服务。
- 边界：
  - 负责请求载荷组装、调用发送和基础异常处理
  - 不负责业务语义解析和领域对象构造
- 输入：
  - `prompt`、`messages`、`schema`、附加参数
- 输出：
  - 外部模型服务响应

### 响应归一化部分

- 角色：从底层响应中提取统一可消费结果。
- 边界：
  - 负责最小归一化封装
  - 不负责领域级结构化解析
- 输入：
  - 底层模型服务原始响应
- 输出：
  - 标准化结果字典

## 关键流程

1. 上层模块准备 `prompt` 或 `messages` 并调用生成器。
2. 生成器根据统一接口组装底层请求载荷。
3. 具体实现向外部模型服务发送请求并接收响应。
4. 模块将底层响应归一化为统一输出结构并返回给上层。

## 设计约束

- 上层模块应通过统一的 `BaseGenerator` 抽象与该模块交互，而不是直接依赖具体实现。
- 该模块只负责模型调用与最小响应归一化，不应承担业务语义解释。
- 新增生成器实现时，应保持 `generate_single` 和 `generate_batch` 的接口一致性。

## 当前实现

- [base.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/generators/base.py)：定义 `BaseGenerator` 抽象接口，约束单次生成与批量生成的统一调用方式。
- [openai_compatible.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/generators/openai_compatible.py)：提供当前的 OpenAI-compatible chat completions 生成器实现，并负责请求构造、调用发送与响应归一化。
