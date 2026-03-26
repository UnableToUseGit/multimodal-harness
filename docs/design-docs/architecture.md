# VideoAtlas 架构设计

## 文档目标

本文档用于描述 `VideoAtlas` 的整体架构设计，帮助开发者从系统层面理解该项目的目标、边界、核心概念、主要模块与主流程。

本文档不负责展开具体模块实现细节，也不替代模块设计文档、数据模式文档或产品规格文档。它的主要作用是提供一张全局地图，使后续开发、重构和扩展能够在统一的系统认知下进行。

## 系统目标与边界

`VideoAtlas` 的目标，是将原始、难以直接消费的长视频，转换为结构化、可导航、可复用的 atlas 表示，使语言模型、下游应用和人工协作都能够稳定使用这些结果。

当前系统的核心能力包括：

- 将原始视频解析为 canonical atlas
- 基于 canonical atlas 按具体任务生成 derived atlas
- 将内部结果对象转换为稳定的 atlas 目录表示
- 为本地检查和人工评审提供 review 支撑能力

当前系统不直接承担以下职责：

- 完整的视频编辑与时间轴编排
- 面向终端用户的 Web 产品层或 API 服务层
- 与 atlas 无关的通用媒体管理系统能力

因此，`VideoAtlas` 当前应被理解为一个“视频理解与结构化资产生成系统”，而不是完整的视频编辑产品本身。

## 核心概念

### Atlas

`Atlas` 在本项目中指一种围绕视频内容构建的结构化表示。它不是对原始视频的简单摘要，而是一组便于查询、导航、复用和下游消费的组织化结果。

在当前实现中，atlas 既是内存中的结果对象，也是最终写入 atlas 目录后的外部表示。

### Canonical Atlas

面向视频内容结构的标准 atlas 表示。它以视频内容本身的语义结构为锚点，对视频进行全局概览、分段、总结和目录化组织，是后续派生与复用的基础。

### Derived Atlas

面向具体任务场景的派生 atlas 表示。它建立在 canonical atlas 之上，根据特定任务的需求，保留、删除、调整和重新组织片段，使结果更接近具体业务目标。

### Frame Sampling / Segmentation / Caption Profile

`Frame Sampling / Segmentation / Caption Profile` 指系统中用于约束视频采样、片段切分和描述生成方式的一组稳定策略定义。它不直接等同于某一次具体执行参数，而是用于描述某类处理任务应采用什么样的观察粒度、切分原则和文本表达方式。

### 数据模式

`VideoAtlas` 中的数据模式用于定义系统里的稳定数据结构、结果对象和输入输出契约。它们不是某个流程的附属细节，而是 workflow、持久化、review、测试和其他下游能力共同依赖的共享语义基础。

数据模式的主要价值包括：

- 为系统中的核心概念提供显式、稳定的结构化表示
- 为不同模块之间的数据协作建立统一契约
- 将内部语义与外部表示分离，降低隐式结构带来的漂移风险
- 为持久化格式、测试保护和后续演进提供稳定锚点

具体数据模式设计可见 [docs/design-docs/data-shemas](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/data-shemas)。

### Atlas 目录格式

`VideoAtlas` 的 atlas 目录格式用于定义 canonical atlas 和 derived atlas 在落盘后的外部表示。它描述根目录结构、片段目录结构、关键文件、必需项与可选项，以及这些目录和文件应如何被下游模块稳定消费。

具体 atlas 目录格式设计可见 [docs/design-docs/atlas-layout](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/atlas-layout)。

### 配置设计

`VideoAtlas` 的配置设计用于定义运行时配置对象、配置项语义、默认值、来源和约束。它既服务于 generator、transcriber 等基础能力的实例化，也服务于流程级运行参数的统一管理。

具体配置设计可见 [docs/design-docs/config-design](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/config-design)。

## 模块介绍

本节只描述系统中的主要模块类型及其职责，不展开具体实现细节。具体模块设计请查阅 [docs/design-docs/module-design](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design) 下的对应文档。

### 核心流程模块

- Canonical Atlas Workflow 模块：
  负责将原始视频、字幕与模型能力编排为 canonical atlas 生成流程，是整个系统的基础内容生成链路。
  参考文档：
  [canonical-atlas-workflow.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/canonical-atlas-workflow.md)
- Derived Atlas Workflow 模块：
  负责基于 canonical atlas 和任务请求生成 derived atlas，是面向具体任务的派生链路。
  参考文档：
  [derived-atlas-workflow.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/derived-atlas-workflow.md)

### 模型交互支撑模块

- `prompts` 模块：
  负责提供稳定的 prompt 模板，支撑不同阶段的模型交互。
- `generators` 模块：
  负责提供统一的模型调用抽象与具体实现。
  参考文档：
  [generators.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/generators.md)
- `message_builder` 模块：
  负责构造 generator 可消费的文本与视频消息。
  参考文档：
  [message-builder.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/message-builder.md)
- `parsing` 模块：
  负责对模型输出进行结构化清洗、提取和解析。
  参考文档：
  [parsing.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/parsing.md)

### 媒体与辅助处理模块

- `transcription` 模块：
  负责提供音频抽取、音频转写和字幕生成能力。
  参考文档：
  [transcription.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/transcription.md)
- `utils` 模块：
  负责承载被多个流程和模块复用的基础视频、字幕和元数据辅助能力。
  参考文档：
  [utils.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/utils.md)

### 外部表示与消费模块

- `persistence` 模块：
  负责将结果对象转换为稳定的 atlas 目录表示。
  参考文档：
  [persistence.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/persistence.md)
- `review` 模块：
  负责加载 atlas 目录并提供本地检查、人工评审和结果可视化支撑能力。
  参考文档：
  [review.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/review.md)

### Atlas 目录格式与配置设计文档

- `atlas-layout` 文档族：
  负责定义 canonical atlas 与 derived atlas 的目录结构、关键文件和稳定外部表示。
  参考文档：
  [docs/design-docs/atlas-layout](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/atlas-layout)
- `config-design` 文档族：
  负责定义 generator、transcriber 及其他运行时配置的结构与约束。
  参考文档：
  [docs/design-docs/config-design](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/config-design)

## 主流程

### Canonical Atlas 生成流程

1. 接收原始视频、可选字幕和目标 atlas 目录。
2. 在必要时补全字幕，并读取视频与字幕相关基础信息。
3. 对视频进行探测与规划，生成 `CanonicalExecutionPlan`。
4. 根据执行计划完成分段解析、边界整理和局部 caption 生成。
5. 将片段级中间结果组装为完整 `CanonicalAtlas`。
6. 将 `CanonicalAtlas` 写入稳定的 atlas 目录表示。

### Derived Atlas 生成流程

1. 接收任务请求、既有 `CanonicalAtlas` 和目标 atlas 目录。
2. 根据任务请求从 canonical atlas 中选择候选片段，并生成 `DerivationPolicy`。
3. 对候选片段执行 re-grounding、字幕裁剪和 re-caption，形成 `DerivedSegmentDraft`。
4. 将 draft 结果统一聚合为完整 `DerivedAtlas`。
5. 将 `DerivedAtlas` 写入稳定的 atlas 目录表示。

### 输出检查与人工评审流程

1. 使用 review 模块或本地脚本加载已生成的 atlas 目录。
2. 对片段、文本说明、字幕、source mapping 和 metadata 进行人工确认。
3. 在需要时继续推动后续修订、补充或重新生成。

当前主流程以“原始视频 -> canonical atlas -> derived atlas -> atlas 目录/review”为主线展开。未来若引入 `AssetProvisionAgent` 或上层编辑系统，也应建立在这一主线之上，而不是绕开 atlas 层重新组织核心语义。

## 外部契约

从系统架构角度看，以下内容都应被视为重要的外部契约：

- atlas 目录的组织方式与文件结构
- canonical atlas 与 derived atlas 的目录格式定义
- 根级说明文件、分段说明文件及相关 metadata 的格式
- 稳定 schema 的字段语义与结果对象定义
- generator、transcriber 等关键能力的配置结构、默认值与来源约定
- 配置文件的基本结构与运行入口约定
- review 和其他下游消费者依赖的输出表示

这些契约一旦形成，就不应被随意静默修改。若发生变化，应同步更新模块文档、数据模式文档、测试和相关说明，以确保系统能够持续演进而不失去稳定性。
