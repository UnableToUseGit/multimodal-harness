# 文档索引

本文档用于提供 `VideoAtlas` 文档体系的统一入口，帮助读者快速定位规范、设计、模板和执行类文档。

## 项目规范

- [AGENTS.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/AGENTS.md)
  仓库级开发入口与规范索引。
- [basic-coding.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/project-spec/basic-coding.md)
  基础编码规范。
- [architecture-and-design.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/project-spec/architecture-and-design.md)
  架构与设计规范。
- [engineering-and-operations.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/project-spec/engineering-and-operations.md)
  工程化与运维规范。
- [testing.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/project-spec/testing.md)
  测试规范。
- [quality-assurance.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/project-spec/quality-assurance.md)
  质量保障规范。
- [collaboration-and-delivery.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/project-spec/collaboration-and-delivery.md)
  协作与交付规范。

## 架构与设计

- [architecture.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/architecture.md)
  系统级架构设计文档。

### 模块设计

- 目录：
  [docs/design-docs/module-design](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design)
- 当前主要模块文档：
  - [cli.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/cli.md)
  - [canonical-atlas-workflow.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/canonical-atlas-workflow.md)
  - [derived-atlas-workflow.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/derived-atlas-workflow.md)
  - [generators.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/generators.md)
  - [message-builder.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/message-builder.md)
  - [parsing.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/parsing.md)
  - [persistence.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/persistence.md)
  - [review.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/review.md)
  - [source-acquisition.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/source-acquisition.md)
  - [transcription.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/transcription.md)
  - [utils.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/utils.md)
  - [prompts](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/module-design/prompts.md)

### 数据模式

- 目录：
  [docs/design-docs/data-shemas](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/data-shemas)
- 内容：
  系统中各个 dataclass / schema 的设计文档。
- 当前新增：
  - [atlas-unit.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/data-shemas/atlas-unit.md)
  - [canonical-composition-result.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/data-shemas/canonical-composition-result.md)

### Atlas 目录格式

- 目录：
  [docs/design-docs/atlas-layout](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/atlas-layout)
- 当前文档：
  - [canonical-atlas-directory.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/atlas-layout/canonical-atlas-directory.md)
  - [derived-atlas-directory.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/atlas-layout/derived-atlas-directory.md)

### 配置设计

- 目录：
  [docs/design-docs/config-design](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/config-design)
- 当前文档：
  - [generator-config.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/config-design/generator-config.md)
  - [transcriber-config.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/config-design/transcriber-config.md)

### Prompt 设计

- 目录：
  [docs/design-docs/prompts](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/prompts)
- 当前文档：
  - [derived-atlas-prompts.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/prompts/derived-atlas-prompts.md)
  
## 模板

- 目录：
  [docs/doc-templates](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/doc-templates)
- 当前模板：
  - [data-schema-template.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/doc-templates/data-schema-template.md)
  - [module-design-template.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/doc-templates/module-design-template.md)
  - [atlas-layout-template.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/doc-templates/atlas-layout-template.md)
  - [config-design-template.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/doc-templates/config-design-template.md)

## 执行计划

- 目录：
  [docs/exec-plans](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/exec-plans)
- 子目录：
  - [active](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/exec-plans/active)
  - [completed](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/exec-plans/completed)
- 当前 active plan：
  - [2026-04-01-canonical-two-stage-composition.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/exec-plans/active/2026-04-01-canonical-two-stage-composition.md)

## 决策记录

- 目录：
  [docs/decision-making](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/decision-making)
- 用途：
  保存关键设计取舍、命名调整、边界变化和其他需要长期追踪的决策记录。
- 当前文档：
  - [2026-0327-1751.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/decision-making/2026-0327-1751.md)
  - [2026-0329-aliyun-transcription-route.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/decision-making/2026-0329-aliyun-transcription-route.md)
  - [2026-0330-0609-canonical-high-efficiency.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/decision-making/2026-0330-0609-canonical-high-efficiency.md)
  - [2026-0331.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/decision-making/2026-0331.md)

## 参考资料

- 目录：
  [docs/references](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/references)
- 用途：
  保存调研资料、参考依据、历史方案和其他不直接构成正式规范或设计契约的文档。
