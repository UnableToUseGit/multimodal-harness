# review 模块设计

## 文档目标

本文档用于说明 `review` 模块的设计目标、职责边界、核心接口、依赖关系和关键流程。本文档面向开发者，目标是帮助读者快速理解该模块在系统中的位置以及它应如何被使用和维护。

## 模块概览

- 名称：`review`
- 路径：`src/video_atlas/review`
- 主要职责：为 atlas 结果提供本地检查与人工评审支撑能力

## 职责与边界

### 职责

- 负责读取已落盘的 atlas 结果目录。
- 负责将结果组织为便于检查和展示的结构。
- 负责提供本地 review 服务与静态页面支撑。
- 在 canonical 两阶段实验期，负责同时暴露顶层 `units/` 与 composed `segments/` 的检查信息。
- 在来源 metadata 存在时，负责读取根目录 `SOURCE_INFO.json` 与 `SOURCE_METADATA.json`。

### 不负责的内容

- 不负责 atlas 生成。
- 不负责结果持久化写入。
- 不负责业务流程决策。

## 核心接口

### `load_review_workspace`

- 类型：`function`
- 作用：读取 atlas 结果目录并组织为 review 数据结构。
- 输入：
  - 待评审的 atlas 目录
- 输出：
  - 供服务层或前端消费的结构化 review 数据
- 说明：
  - 该接口建立在稳定的外部目录契约之上。
  - 在 canonical 两阶段实验期，该接口需要同时识别顶层 `units/` 与 `segments/` 下复制的 unit 视图。
  - 当根目录存在 source metadata 文件时，该接口也应将其读入结构化 review 数据。

### 具体实现类接口：`ReviewAppServer`

- 类型：`concrete class`
- 作用：提供本地 review 服务入口。
- 初始化输入：
  - `server`
  - `host`
  - `port`
  - `workspaces`
- 对外暴露的方法：
  - `serve_forever(...)`：启动本地 review 服务。
  - `shutdown(...)`：关闭本地 review 服务。
  - `url`：返回当前服务地址。
- 关键方法的输入与输出：
  - `serve_forever(...)`
    - 输入：
      - 无额外输入
    - 输出：
      - 长时间运行的本地服务进程
- 说明：
  - 该实现类负责连接目录加载层与前端展示层。

### 静态前端资源

- 类型：`static assets`
- 作用：渲染并展示 review 内容。
- 输入：
  - 服务层提供的 review 数据
- 输出：
  - 可供人工检查的页面表现
- 说明：
  - 该部分不直接参与目录解析。

## 依赖关系

### 上游依赖

- `persistence` 产出的目录结果
- 启动 review 的脚本或本地入口

### 下游依赖

- 本地文件系统
- HTTP 服务能力
- 静态前端页面

## 内部组成

### 目录加载部分

- 角色：识别并读取 atlas 结果目录。
- 边界：
  - 负责目录解析和数据组织
  - 不负责 HTTP 服务和前端呈现
- 输入：
  - atlas 目录中的说明文件、unit 文件、segment 文件和 metadata
- 输出：
  - 结构化 review 数据

### 服务层部分

- 角色：向本地前端提供数据与静态资源。
- 边界：
  - 负责服务启动和数据输出
  - 不负责底层目录解析规则定义
- 输入：
  - 结构化 review 数据
  - 服务启动参数
- 输出：
  - 本地接口与静态资源响应

### 静态前端部分

- 角色：呈现片段、units、字幕、文本说明和映射信息。
- 边界：
  - 负责页面展示和交互
  - 不负责业务结果生成
- 输入：
  - 服务层返回的数据和资源地址
- 输出：
  - 可供人工检查的 review 页面

## 关键流程

1. 用户指定待检查的 atlas 目录。
2. 模块解析目录中的 README、unit 文件、segment 文件和 metadata。
3. 模块将结果组织为 review 所需的数据结构。
4. 本地服务与静态页面共同完成结果展示。

## 设计约束

- 该模块只消费结果目录，不参与结果生成。
- review 逻辑应建立在稳定外部契约之上，而不是依赖内部 workflow 细节。
- 前端展示层与目录解析层应保持职责分离。
- 对来源信息的读取应优先依赖根级结构化 JSON 文件，而不是解析 README 中的自由文本。

## 当前实现

- [__init__.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/review/__init__.py)：导出 review 相关公共入口。
- [workspace_loader.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/review/workspace_loader.py)：负责读取 atlas 目录并转为 review 数据结构。
- [server.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/review/server.py)：负责本地服务与 review 数据输出。
- [static/index.html](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/review/static/index.html)：review 前端页面入口。
- [static/app.js](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/review/static/app.js)：review 前端交互逻辑。
- [static/styles.css](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/review/static/styles.css)：review 前端样式定义。
