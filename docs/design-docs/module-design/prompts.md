# prompts 模块设计

## 文档目标

本文档用于说明 `prompts` 模块的当前实现形态，包括模块职责、边界、核心接口、依赖关系和内部组成。本文档面向开发者，目标是帮助读者理解系统如何定义、注册、查询和渲染 prompt。

## 模块概览

- 名称：`prompts`
- 路径：`src/video_atlas/prompts`
- 主要职责：为系统提供稳定的 prompt 定义对象、统一注册入口和 prompt 渲染能力

## 职责与边界

### 职责

- 定义系统中的稳定 prompt 契约。
- 显式表达每个 prompt 的用途、输入字段和输出契约。
- 为 canonical/derived workflow 提供统一的 prompt 查询与渲染入口。
- 统一管理系统当前已注册的 prompt 集合。

### 不负责的内容

- 不负责 message 构造。
- 不负责模型调用。
- 不负责模型输出解析。
- 不负责 workflow 编排逻辑。

## 核心接口

### 具体实现类接口：`PromptSpec`

- 类型：`concrete class`
- 作用：表达单个 prompt 的稳定定义。
- 初始化输入：
  - `name`
  - `purpose`
  - `system_template`
  - `user_template`
  - `input_fields`
  - `output_contract`
  - 可选的 `metadata`
  - 可选的 `tags`
- 对外暴露的方法：
  - `render_system(...)`
  - `render_user(...)`
  - `render(...)`
  - `__getitem__(...)`
- 关键方法的输入与输出：
  - `render_system(...)`
    - 输入：
      - 该 `system_template` 所需字段值
    - 输出：
      - 渲染后的 `system` prompt 文本
  - `render_user(...)`
    - 输入：
      - 该 `user_template` 所需字段值
    - 输出：
      - 渲染后的 `user` prompt 文本
  - `render(...)`
    - 输入：
      - 该 prompt 所需字段值
    - 输出：
      - `(system_prompt, user_prompt)` 二元组
  - `__getitem__(...)`
    - 输入：
      - `"SYSTEM"` 或 `"USER"`
    - 输出：
      - 原始模板文本
- 说明：
  - `PromptSpec` 是 prompt 模块的核心定义对象。
  - `render*` 接口是当前推荐调用路径。
  - `__getitem__` 仅保留兼容访问能力，不应作为新的长期主调用方式。

### 具体实现类接口：`PromptRegistry`

- 类型：`concrete class`
- 作用：集中管理系统中所有已注册的 prompt。
- 初始化输入：
  - 无特殊要求；实例创建后通过 `register(...)` 累积 prompt
- 对外暴露的方法：
  - `register(...)`
  - `get(...)`
  - `list_prompts(...)`
- 关键方法的输入与输出：
  - `register(...)`
    - 输入：
      - 一个 `PromptSpec`
    - 输出：
      - 无返回值；将 prompt 纳入 registry
  - `get(...)`
    - 输入：
      - prompt 名称
    - 输出：
      - 对应 `PromptSpec`
  - `list_prompts(...)`
    - 输入：
      - 无
    - 输出：
      - 当前已注册 prompt 列表
- 说明：
  - `PromptRegistry` 是 prompt 查询与集中管理的统一入口。
  - 它负责收敛重名冲突和缺失 prompt 的问题。

### 函数接口：`get_prompt(...)`

- 类型：`function`
- 作用：提供轻量 prompt 查询入口。
- 输入：
  - prompt 名称
- 输出：
  - 对应 `PromptSpec`
- 说明：
  - 当调用方不需要直接操作 registry 时，可通过该入口读取 prompt。

### 函数接口：`list_prompts(...)`

- 类型：`function`
- 作用：列出当前模块公开注册的全部 prompt。
- 输入：
  - 无
- 输出：
  - `tuple[PromptSpec, ...]`
- 说明：
  - 该接口主要服务调试、文档核对和集中检查。

### 函数接口：`prompt_names(...)`

- 类型：`function`
- 作用：返回当前公开注册 prompt 的名称集合。
- 输入：
  - 无
- 输出：
  - `tuple[str, ...]`
- 说明：
  - 该接口主要用于测试、调试和文档自检。

## 依赖关系

### 上游依赖

- canonical atlas workflow
- derived atlas workflow
- 其他需要使用稳定 prompt 的上层模块

### 下游依赖

- Python 标准库中的 `dataclasses`
- Python 标准库中的 `string.Formatter`
- prompt 文本片段与共享渲染逻辑

## 内部组成

### Prompt 定义组件

- 角色：定义单个 prompt 的稳定契约。
- 边界：
  - 负责保存 prompt 模板文本与元信息
  - 不负责生成 `messages`
- 输入：
  - prompt 名称、用途、模板文本、输入字段、输出契约
- 输出：
  - `PromptSpec`

### Prompt 注册组件

- 角色：集中管理 prompt 的注册、查询和列举。
- 边界：
  - 负责统一收敛 prompt 名称与检索逻辑
  - 不负责 workflow 级调用策略
- 输入：
  - `PromptSpec` 集合
- 输出：
  - 可查询的 `PromptRegistry`

### Prompt 分组组件

- 角色：按流程域组织 prompt 定义。
- 边界：
  - 负责将 canonical、derived 等 prompt 分文件管理
  - 不负责 message 拼装或模型调用
- 输入：
  - 同类 `PromptSpec`
- 输出：
  - 结构清晰的 prompt 定义文件

### Prompt 共享片段组件

- 角色：为较复杂 prompt 提供可复用片段与动态插值内容。
- 边界：
  - 负责 canonical prompt 的共享文本片段与 profile 选项渲染
  - 不负责 prompt 注册和渲染接口
- 输入：
  - profile 数据和共享片段定义
- 输出：
  - 可供具体 `PromptSpec` 组装的文本内容

## 关键流程

1. 开发者定义新的 `PromptSpec`，显式声明其用途、输入字段和输出契约。
2. `prompts.__init__` 将公开 prompt 收敛为 `PROMPT_SPECS` 并注册到 `PROMPT_REGISTRY`。
3. 上层 workflow 通过直接引用 prompt 常量或通过 `get_prompt(...)` 获取 `PromptSpec`。
4. workflow 在调用前通过 `render_system(...)`、`render_user(...)` 或 `render(...)` 生成最终 prompt 文本。
5. 渲染后的 prompt 文本再交给 `message-builder` 进入后续模型调用流程。

## 设计约束

- prompt 的用途、输入字段和输出契约应显式表达，不应只散落在调用代码和文档中。
- prompt 注册与查询应有统一入口，避免不同模块维护私有 prompt 集合。
- `prompts` 模块只负责 prompt 定义与管理，不应越界承担消息构造或模型调用职责。
- 新增 prompt 时，应同时更新对应 prompt 文档与必要测试。
- 新代码应优先通过 `render*` 接口使用 prompt，不应继续扩散裸模板访问路径。

## 当前实现

- [specs.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/prompts/specs.py)：定义 `PromptSpec`、`PromptRegistry` 和渲染/校验能力。
- [__init__.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/prompts/__init__.py)：统一导出 prompt 常量、registry 及查询入口。
- [canonical_prompts.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/prompts/canonical_prompts.py)：定义 canonical atlas 相关 `PromptSpec`。
- [canonical_prompt_parts.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/prompts/canonical_prompt_parts.py)：定义 canonical prompt 的共享片段和动态文本渲染逻辑。
- [derived_prompts.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/prompts/derived_prompts.py)：定义 derived atlas 相关 `PromptSpec`。

当前实现已经正式采用 `PromptSpec + PromptRegistry` 形态，并由 workflow 通过 `render*` 接口消费 prompt。
