# Repository Guidelines

## 仓库定位

`MM Harness` 是一个面向 agent 的长视频/长音频预处理工具。

它当前的目标不是直接完成所有下游任务，而是把原始媒体转换成更适合语言模型理解、检索、总结和复用的结构化 workspace。

当前 release 主线聚焦于：

- 从 YouTube、小宇宙或本地文件获取长视频/长音频输入
- 执行 text-first canonical workflow
- 生成稳定的 canonical workspace，供 agent 后续继续处理

当前仓库不再把以下内容视为主线：

- legacy canonical workflow
- derived atlas workflow
- 强视觉内容理解主线

## 文档分层

当前文档分为两类：

- 面向用户和 agent 的产品文档：`docs/`
- 面向开发的设计与规范文档：`develop_docs/`

### 用户文档

优先阅读：

- [README.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/README.md)
- [docs/install.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/install.md)
- [docs/README_en.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/README_en.md)

### 开发文档

当前开发文档入口：

- [develop_docs/index.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/develop_docs/index.md)

其中：

- `develop_docs/design-docs/`
  存放当前仍与代码现状一致的设计文档
- `develop_docs/decision-making/`
  存放历史决策记录
- `develop_docs/exec-plans/`
  存放历史执行计划
- `develop_docs/project-spec/`
  存放项目规范

## 当前代码主线

当前仍在维护的核心代码主线包括：

- `src/video_atlas/cli/`
  - `mm-harness` CLI
- `src/video_atlas/application/`
  - 输入整理与 workflow 装配
- `src/video_atlas/workflows/text_first_canonical_atlas_workflow.py`
  - 当前唯一 canonical 主线
- `src/video_atlas/workflows/text_first_canonical/`
  - planning / parsing / composition / subtitle preparation
- `src/video_atlas/source_acquisition/`
  - YouTube / Xiaoyuzhou acquisition
- `src/video_atlas/transcription/`
  - 默认 `groq_whisper`
- `src/video_atlas/persistence/`
  - workspace 写盘
- `src/video_atlas/review/`
  - workspace 读取与 review app

当前已删除或不再作为主线维护的部分，不应再被当作当前设计基线：

- `src/video_atlas/workflows/canonical_atlas_workflow.py`
- `src/video_atlas/workflows/canonical_atlas/`

## 当前目录结构

当前仓库的主要目录结构如下：

```text
development/
├── AGENTS.md
├── README.md
├── configs/
│   └── canonical/
├── develop_docs/
│   ├── decision-making/
│   ├── design-docs/
│   ├── doc-templates/
│   ├── exec-plans/
│   ├── project-spec/
│   └── index.md
├── docs/
│   ├── install.md
│   └── README_en.md
├── local/
│   └── inputs/
├── scripts/
│   ├── run_eval.sh
│   └── run_review_app.py
├── src/
│   └── video_atlas/
│       ├── application/
│       ├── cli/
│       ├── config/
│       ├── generators/
│       ├── message_builder/
│       ├── parsing/
│       ├── persistence/
│       ├── prompts/
│       ├── review/
│       ├── schemas/
│       ├── skill/
│       ├── source_acquisition/
│       ├── transcription/
│       ├── utils/
│       └── workflows/
└── tests/
```

## 开发工作方式

### 新功能开发

- 开发前先明确设计边界。
- 若已有设计文档，先基于文档对齐实现边界与验收标准。
- 若没有设计文档，应先补充简要设计，再开始实现。
- 功能完成后应进行必要测试与验证。
- 用户验收通过后，再更新相关文档并提交。

### 既有功能改进

- 默认与新功能开发同样处理。
- 若改动涉及接口、行为或模块职责变化，应先补简要说明。
- 改进完成后，仍需做必要验证与文档同步。

### Bug 修复

- 明确、局部、低风险的 bug 可以直接修。
- 若修复涉及公共契约变化、较大范围重构或架构调整，仍应先补充说明。
- 修复完成后应做必要验证。

## 环境准备

- `conda activate /share/project/minghao/Envs/videoatlas`

推荐顺序：

1. `conda activate /share/project/minghao/Envs/videoatlas`
2. `proxy_status`
3. 如需外网访问，执行 `proxy_on`
4. 如需下载依赖，可执行 `set_mirror`
5. 安装或更新依赖
6. 运行验证命令

## 网络辅助命令

针对中国大陆网络环境限制，可使用 `.bashrc` 中的辅助命令：

- `proxy_status`
- `proxy_on`
- `proxy_off`
- `set_mirror`
- `test_mirror`
- `unset_mirror`
