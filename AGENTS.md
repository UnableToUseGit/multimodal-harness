# Repository Guidelines

## 仓库定位

`VideoAtlas` 是一个面向长视频理解与重组的系统。它的目标不是简单生成摘要，而是把原始视频转换成结构化、可检索、可复用的 atlas，使后续应用、代理系统和人工协作都能稳定消费这些结果。

项目当前主要围绕两类能力展开：

- 将原始视频解析为内容稳定、目录结构清晰的 canonical atlas
- 在 canonical atlas 基础上，根据具体任务进一步提炼和组织轻量化资产

该仓库同时承载实现、规范、文档和工作流约定，因此所有开发活动都应以“结构清晰、契约稳定、可持续演进”为目标。

## 最高规范索引

本文件只提供一层轻量索引。各类详细规范请直接查阅 `docs/project-spec/` 下的对应文档：

- 基础编码规范：
  [docs/project-spec/basic-coding.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/project-spec/basic-coding.md)
- 架构与设计规范：
  [docs/project-spec/architecture-and-design.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/project-spec/architecture-and-design.md)
- 工程化与运维规范：
  [docs/project-spec/engineering-and-operations.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/project-spec/engineering-and-operations.md)
- 测试规范：
  [docs/project-spec/testing.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/project-spec/testing.md)
- 质量保障规范：
  [docs/project-spec/quality-assurance.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/project-spec/quality-assurance.md)
- 协作与交付规范：
  [docs/project-spec/collaboration-and-delivery.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/project-spec/collaboration-and-delivery.md)

如后续新增领域特定规范，应继续放在 `docs/project-spec/` 下，并在本文件中补充入口索引。

## 架构和模块设计

当前项目可以粗略分成四类内容：

- 核心流程模块：
  `canonical_atlas_workflow` 与 `derived_atlas_workflow` 负责系统的两条主流程。
- 共享基础模块：
  `generators`、`message_builder`、`parsing`、`prompts`、`transcription`、`utils` 等模块为核心流程提供可复用能力。
- 数据与外部表示：
  `schemas` 定义共享数据模式，`persistence` 负责将 atlas 结果写成稳定目录形式，`review` 负责结果查看与人工检查。
- 文档与规范：
  `docs/project-spec/` 存放顶层规范，`docs/design-docs/` 存放架构、模块、数据模式、目录格式和配置设计文档。

如需了解系统全局设计，优先阅读：

- [docs/design-docs/architecture.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/design-docs/architecture.md)
- [docs/index.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/index.md)

## 文档撰写约定

- 新增架构设计、模块设计、数据模式、目录格式或配置设计文档时，应优先参考 `docs/doc-templates/` 下对应模板。
- 新增或修改文档后，应同步更新相关联文档，避免术语、接口或契约描述漂移。
- 新增正式文档后，应在 [docs/index.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/index.md) 中补充入口索引。

## 当前目录结构

当前仓库的主要目录结构如下：

```text
development/
├── AGENTS.md
├── configs/
│   ├── canonical/
│   └── task_derivation/
├── docs/
│   ├── design-docs/
│   ├── doc-templates/
│   ├── exec-plans/
│   ├── project-spec/
│   ├── references/
│   └── index.md
├── local/
│   └── inputs/
├── scripts/
├── src/
│   └── video_atlas/
│       ├── cli/
│       ├── config/
│       ├── generators/
│       ├── message_builder/
│       ├── parsing/
│       ├── persistence/
│       ├── prompts/
│       ├── review/
│       ├── schemas/
│       ├── transcription/
│       ├── utils/
│       └── workflows/
└── tests/
```


## 开发工作方式

### 新功能开发

- 开发任何新功能前，应先明确设计方案。
- 若用户已经提供完整设计文档，应先基于该文档确认实现边界与验收标准。
- 若用户未提供设计文档，开发者应先补一版简要设计说明，并在正式开发前征求用户意见。
- 设计确认后，应新建独立分支开展开发工作。
- 开发过程中，应同时遵循本仓库的相关规范文档，包括编码规范、架构规范、测试规范和质量保障规范。
- 功能开发完成后，应按规范执行测试与验证。
- 测试通过后，应等待用户验收。
- 若验收未通过，应根据用户反馈继续修改，直到满足预期。
- 若验收通过，应补充或修订相关文档，随后再进行正式提交。

### 既有功能改进

- 对既有功能的改进，默认遵循与新功能开发相同的流程。
- 在开始实现前，应先明确改动目标、影响范围和验收标准。
- 若改动涉及行为调整、接口变化或模块职责变化，应先形成简要设计说明，再进入开发。
- 改进完成后，同样需要经过规范测试、用户验收、文档更新和最终提交。

### Bug 修复

- 对明确、局部、低风险的 bug 修复，可以直接在当前分支上修改，不强制要求先写设计文档。
- 若 bug 修复会引起公共行为变化、稳定契约变化、较大范围重构或架构调整，则仍应先补充简要说明，再开始修改。
- bug 修复完成后，仍应进行必要验证。
- 若修复内容会影响用户可见行为、接口契约或使用方式，也应同步更新相关文档。

## 环境准备

- `conda activate /share/project/minghao/Envs/videoatlas`：进入专用开发环境。
- 所需 Python 包应通过 `pip` 在该环境内手动安装。

推荐在一个全新的 shell 中按以下顺序操作：

1. `conda activate /share/project/minghao/Envs/videoatlas`
2. `proxy_status`
3. 若需要访问外部网络，执行 `proxy_on`
4. 在下载包或模型前执行 `set_mirror`
5. 安装依赖
6. 运行验证命令

## 网络辅助命令

针对中国大陆网络环境限制，请使用 `.bashrc` 中已定义的以下 shell 辅助命令：

- `proxy_status`：检查当前是否已启用外部代理。
- `proxy_on`：在安装依赖或下载外部资源前启用代理访问。
- `proxy_off`：关闭代理访问。
- `set_mirror`：为 `pip`、`conda`、`npm` 和 Hugging Face 下载配置镜像。
- `test_mirror`：检查当前镜像配置状态。
- `unset_mirror`：在不再需要时清除镜像配置。
