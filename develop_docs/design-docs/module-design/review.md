# Review 模块设计

## 文档目标

本文档说明当前 review 模块如何读取 canonical workspace，并为人工检查或后续工具消费提供统一访问方式。

## 模块位置

- `src/video_atlas/review/workspace_loader.py`
- `src/video_atlas/review/server.py`

## 模块职责

review 模块负责：

- 从磁盘加载 canonical workspace
- 解析 root README、segment README、unit README
- 读取 `SOURCE_INFO.json` / `SOURCE_METADATA.json`
- 将 workspace 转换为 review 友好的结构化对象

它不负责：

- 生成 atlas
- 修改 atlas
- source acquisition

## 核心对象

当前主要对象包括：

- `ReviewWorkspace`
- `ReviewSegment`
- `ReviewUnit`

这些对象是 review 侧的数据表示，不等同于业务层 `CanonicalAtlas`。

## 当前加载方式

`load_review_workspace(...)` 的基本流程为：

1. 判断 workspace kind
2. 读取根级 README
3. 扫描 `units/`
4. 扫描 `segments/`
5. 读取输入资产和 source metadata
6. 组装 `ReviewWorkspace`

## 当前主要用途

- 人工审阅输出结构
- 本地 review app 展示
- 调试 atlas 是否按预期写盘
