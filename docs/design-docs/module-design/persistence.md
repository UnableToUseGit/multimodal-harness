# persistence 模块设计

## 文档目标

本文档用于说明 `persistence` 模块的设计目标、职责边界、核心接口、依赖关系和关键流程。本文档面向开发者，目标是帮助读者快速理解该模块在系统中的位置以及它应如何被使用和维护。

## 模块概览

- 名称：`persistence`
- 路径：`src/video_atlas/persistence`
- 主要职责：将内存中的 atlas 结果对象转换为稳定的目录与文件表示，并在实验期支持 canonical 的 `units + segments` 双层结果写出

## 职责与边界

### 职责

- 负责结果对象到目录结构的外部化写入。
- 负责文本文件写入、文件复制、clip 提取等持久化辅助操作。
- 为 canonical 与 derived 两类结果提供专门 writer。
- 在 canonical atlas 包含来源信息时，负责将 source metadata 写为稳定根级 JSON 文件。

### 不负责的内容

- 不负责业务流程编排。
- 不负责模型调用与响应解析。
- 不负责业务策略决策。

## 核心接口

### 具体实现类接口：`CanonicalAtlasWriter`

- 类型：`concrete class`
- 作用：负责 canonical atlas 结果的整体外部化写入。
- 初始化输入：
  - 可选的 `caption_with_subtitles`
- 对外暴露的方法：
  - `write(...)`：将 `CanonicalAtlas` 写成稳定的目录与文件表示。
- 关键方法的输入与输出：
  - `write(...)`
    - 输入：
      - `CanonicalAtlas`
      - 目标 atlas 目录
    - 输出：
      - canonical atlas 对应的目录结构、说明文件、unit 文件和 segment 文件
- 说明：
  - 该实现类只消费完整结果对象，不参与结果生成。

### 具体实现类接口：`DerivedAtlasWriter`

- 类型：`concrete class`
- 作用：负责 derived atlas 结果的整体外部化写入。
- 初始化输入：
  - 可选的 `caption_with_subtitles`
- 对外暴露的方法：
  - `write(...)`：将 `DerivedAtlas` 写成稳定的目录与文件表示。
- 关键方法的输入与输出：
  - `write(...)`
    - 输入：
      - `DerivedAtlas`
      - 目标 atlas 目录
    - 输出：
      - derived atlas 对应的目录结构、说明文件和片段文件
- 说明：
  - 该实现类只消费完整的 derived 结果对象，不参与 derivation 流程。

### `copy_to`

- 类型：`function`
- 作用：将文件或目录复制到目标目录中。
- 输入：
  - 源路径
  - 目标目录
- 输出：
  - 复制后的目标路径
- 说明：
  - 适用于复用已有文件或目录资产。

### `write_text_to`

- 类型：`function`
- 作用：将文本写入目标目录下的指定相对路径。
- 输入：
  - 目标目录
  - 相对路径
  - 文本内容
- 输出：
  - 写入后的目标路径
- 说明：
  - 适用于 README、字幕文本和 metadata 文件写出。

### `write_json_to`

- 类型：`function`
- 作用：将 JSON payload 写入目标目录下的指定相对路径。
- 输入：
  - 目标目录
  - 相对路径
  - JSON 对象
- 输出：
  - 写入后的目标路径
- 说明：
  - 适用于 `SOURCE_INFO.json`、`SOURCE_METADATA.json` 等结构化 metadata 写出。

### `extract_clip`

- 类型：`function`
- 作用：从源视频中提取片段并写入目标目录。
- 输入：
  - 源视频路径
  - 起止时间
  - 目标目录或目标相对路径
- 输出：
  - 提取后的 clip 路径
- 说明：
  - 该接口依赖底层视频工具，不负责决定提取策略。

## 依赖关系

### 上游依赖

- canonical workflow
- derived workflow
- 其他需要将结果对象写入目录的模块

### 下游依赖

- `schemas` 中的 atlas 结果对象
- 本地文件系统
- `ffmpeg`

## 内部组成

### 基础持久化函数

- 角色：提供文本写入、文件复制和 clip 提取等通用持久化能力。
- 边界：
  - 负责底层文件与片段写出
  - 不负责 atlas 级目录组织策略
- 输入：
  - 路径、文本内容、时间范围等基础写入参数
- 输出：
  - 写出的文件路径或目录路径

### canonical writer

- 角色：负责 canonical atlas 的整体外部化写入。
- 边界：
  - 负责 canonical 结果到目录表示的转换
  - 负责实验期 `units/` 与 `segments/` 的双层写出
  - 负责根目录 source metadata 文件写出
  - 不负责 canonical 结果对象的生成
- 输入：
  - `CanonicalAtlas`
  - 目标 atlas 目录
- 输出：
  - 完整的 canonical atlas 目录结果

### derived writer

- 角色：负责 derived atlas 的整体外部化写入。
- 边界：
  - 负责 derived 结果到目录表示的转换
  - 不负责 derivation 流程中的任何业务决策
- 输入：
  - `DerivedAtlas`
  - 目标 atlas 目录
- 输出：
  - 完整的 derived atlas 目录结果

## 关键流程

1. 上层 workflow 产出标准结果对象。
2. writer 读取结果对象及相关路径信息。
3. 模块写出根级说明文件、unit 文件、segment 文件和辅助 metadata。
4. 模块在需要时提取 unit 视频，并在实验期复制到 segment 目录中完成目录组织。

## 设计约束

- 该模块只消费结果对象，不负责生成这些结果对象。
- writer 应以稳定契约写出结果，不应内联业务推理。
- 目录结构、文件名和 metadata 格式应保持可追踪和可验证。
- 内部时间字段使用数值时间范围表达。
- 当这些信息被写入 atlas 目录中的 README 或 metadata 时，应由持久化层统一转换为 ISO 8601 格式
- canonical 两阶段实验期允许存在冗余目录与媒体复制，以换取更高的可验证性和可解释性。
- 对 YouTube URL 等外部来源输入，应优先通过根级 `SOURCE_INFO.json` 和 `SOURCE_METADATA.json` 暴露来源信息，而不是要求下游从 README 推断。

## 当前实现

- [__init__.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/persistence/__init__.py)：导出模块对外可用的 writer 与辅助函数。
- [writers.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/persistence/writers.py)：实现文本写入、文件复制、clip 提取以及 canonical/derived writer。
