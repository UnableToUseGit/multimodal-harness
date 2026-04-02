# Canonical Two-Stage Composition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 canonical atlas 从“单阶段直接切出最终 segment”的流程，重构为“Stage 1 产出 units，Stage 2 组合 units 成最终 segments”的两阶段流程。

**Architecture:** Stage 1 继续负责 boundary detection 和 unit 级语义产出，输出稳定的 `units`。Stage 2 新增一个 text-only structure composer，读取全体 `units` 的文本信息和可选的 `structure_request`，输出最终 `segments`。实验期 atlas 目录同时保留 `units/` 与 `segments/`，且在 `segments/<segment>/` 下复制完整 unit 媒体文件以方便人工验证。

**Tech Stack:** Python dataclasses, canonical workflow mixins, PromptSpec/PromptRegistry, persistence writers, review loader, unittest

---

## 文件结构

### 新增文件

- `src/video_atlas/workflows/canonical_atlas/structure_composition.py`
  - Stage 2 组合逻辑
  - unit 文本载荷准备
  - composer 输出解析与校验
- `tests/test_canonical_structure_composition.py`
  - Stage 2 独立测试
- `docs/design-docs/data-shemas/atlas-unit.md`
  - `AtlasUnit` schema 文档
- `docs/design-docs/data-shemas/canonical-composition-result.md`
  - Stage 2 composition result schema 文档

### 重点修改文件

- `src/video_atlas/schemas/canonical_atlas.py`
  - 新增 `AtlasUnit`
  - 扩展 `CanonicalAtlas`
  - 新增 Stage 2 相关 schema
- `src/video_atlas/prompts/canonical_prompts.py`
  - 新增 structure composition prompt
- `src/video_atlas/prompts/__init__.py`
  - 导出新 prompt
- `src/video_atlas/workflows/canonical_atlas_workflow.py`
  - 新增 `structure_composer`
  - `create(...)` 新增 `structure_request`
- `src/video_atlas/workflows/canonical_atlas/video_parsing.py`
  - Stage 1 输出从“最终 segment 草稿”调整为 `units`
  - 两条 route 都补齐 title 生成
- `src/video_atlas/workflows/canonical_atlas/pipeline.py`
  - 主链改为：plan -> units -> compose -> finalize -> write
  - 负责从 units、composition result 与路径信息直接打包最终 `CanonicalAtlas`
- `src/video_atlas/persistence/writers.py`
  - canonical writer 写出 `units/` 与 `segments/`
- `src/video_atlas/review/workspace_loader.py`
  - 读取新的实验期 canonical atlas 目录结构
- `src/video_atlas/review/static/app.js`
  - review UI 支持 units / composed segments
- `src/video_atlas/config/models.py`
  - canonical pipeline 配置增加 `structure_composer`
- `src/video_atlas/config/factories.py`
  - 构造 `structure_composer`
- `configs/canonical/default.json`
  - 增加 `structure_composer`
- `scripts/run_evaluation.py`
  - canonical workflow 构造新增 `structure_composer`
  - evaluation case 透传 `structure_request`
- `tests/test_workspace_writers.py`
  - 验证新的 canonical 目录结构
- `tests/test_review_loader.py`
  - 验证 loader 对新结构的读取
- `tests/test_prompts.py`
  - 覆盖新 composition prompt
- `docs/design-docs/module-design/canonical-atlas-workflow.md`
- `docs/design-docs/data-shemas/canonical-atlas.md`
- `docs/design-docs/data-shemas/atlas-segment.md`
- `docs/design-docs/atlas-layout/canonical-atlas-directory.md`
- `docs/design-docs/config-design/generator-config.md`
- `docs/index.md`

---

### Task 1: 定义两阶段数据模式

**Files:**
- Modify: `src/video_atlas/schemas/canonical_atlas.py`
- Test: `tests/test_canonical_schemes.py`
- Doc: `docs/design-docs/data-shemas/atlas-unit.md`
- Doc: `docs/design-docs/data-shemas/canonical-composition-result.md`

- [ ] **Step 1: 写失败测试，固定两阶段 schema**

在 `tests/test_canonical_schemes.py` 新增断言：
- `AtlasUnit` 存在，并至少包含：
  - `unit_id`
  - `title`
  - `start_time`
  - `end_time`
  - `summary`
  - `caption`
  - `subtitles_text`
  - `folder_name`
- `CanonicalAtlas` 增加：
  - `units`
  - `segments`
- Stage 2 输出 schema 至少能表达：
  - `segment_id`
  - `unit_ids`
  - `title`
  - `summary`
  - `composition_rationale`

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_canonical_schemes -v
```

Expected:
- 缺少新 schema 或断言失败

- [ ] **Step 3: 实现最小 schema**

在 `src/video_atlas/schemas/canonical_atlas.py` 中：
- 新增 `AtlasUnit`
- 新增 composition result 相关 dataclass
- 扩展 `CanonicalAtlas`

要求：
- `AtlasSegment` 调整为 Stage 2 最终结构段，而不是继续与 `AtlasUnit` 语义重叠
- `units` 与 `segments` 都是显式字段

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_canonical_schemes -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_atlas/schemas/canonical_atlas.py tests/test_canonical_schemes.py docs/design-docs/data-shemas/atlas-unit.md docs/design-docs/data-shemas/canonical-composition-result.md
git commit -m "feat: add canonical two-stage schemas"
```

---

### Task 2: 为 Stage 2 新增 composition prompt

**Files:**
- Modify: `src/video_atlas/prompts/canonical_prompts.py`
- Modify: `src/video_atlas/prompts/__init__.py`
- Test: `tests/test_prompts.py`

- [ ] **Step 1: 写失败测试**

在 `tests/test_prompts.py` 新增断言：
- 新 prompt 已注册
- 支持输入字段：
  - `units_description`
  - `concise_description`
  - `genres`
  - `structure_request`
- render 成功

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_prompts -v
```

Expected:
- prompt 缺失或未注册

- [ ] **Step 3: 实现 prompt**

新增 `CANONICAL_STRUCTURE_COMPOSITION_PROMPT`：
- system: 说明 Stage 2 只做结构组合
- user: 输入所有 units 的文本表示和 `structure_request`
- 输出：严格 JSON，包含 composed segments

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_prompts -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_atlas/prompts/canonical_prompts.py src/video_atlas/prompts/__init__.py tests/test_prompts.py
git commit -m "feat: add canonical structure composition prompt"
```

---

### Task 3: 实现 Stage 2 structure composer

**Files:**
- Create: `src/video_atlas/workflows/canonical_atlas/structure_composition.py`
- Test: `tests/test_canonical_structure_composition.py`

- [ ] **Step 1: 写失败测试**

在 `tests/test_canonical_structure_composition.py` 增加测试：
- 能把 units 序列转换为 prompt 输入文本
- 能解析 composer 返回的 segment grouping result
- 能拒绝：
  - 空 `unit_ids`
  - 非相邻 unit 乱序组合
  - 重复引用 unit

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_canonical_structure_composition -v
```

Expected:
- 模块不存在或断言失败

- [ ] **Step 3: 实现最小结构组合模块**

在 `structure_composition.py` 中实现：
- unit 文本序列化
- 调用 `structure_composer`
- 响应解析
- 最小校验逻辑

边界：
- 当前只处理“全量 units 一次性送入”
- 不处理超长分块组合

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_canonical_structure_composition -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_atlas/workflows/canonical_atlas/structure_composition.py tests/test_canonical_structure_composition.py
git commit -m "feat: add canonical structure composer stage"
```

---

### Task 4: 让 Stage 1 输出 units，并补齐两条 route 的 unit title 生成

**Files:**
- Modify: `src/video_atlas/workflows/canonical_atlas/video_parsing.py`
- Test: `tests/test_segmentation_streaming.py`
- Test: `tests/test_canonical_high_efficiency.py`

- [ ] **Step 1: 写失败测试**

补测试覆盖：
- Stage 1 输出 unit 列表而不是最终 segment 列表
- text route 和 multimodal route 都生成 unit title
- `video_parsing` 输出的 unit 包含完整文本字段

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_segmentation_streaming tests.test_canonical_high_efficiency -v
```

Expected:
- 输出结构不匹配或 title 缺失

- [ ] **Step 3: 修改 Stage 1 输出**

要求：
- `video_parsing.py` 负责生成 `AtlasUnit` 所需中间信息
- text route 和 multimodal route 统一产生 unit-level title / summary / caption
- Stage 1 不再假设自己直接生成最终 `segments`

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_segmentation_streaming tests.test_canonical_high_efficiency -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_atlas/workflows/canonical_atlas/video_parsing.py tests/test_segmentation_streaming.py tests/test_canonical_high_efficiency.py
git commit -m "refactor: emit canonical units from stage one parsing"
```

---

### Task 5: 接入 Stage 2 到 canonical workflow 主链

**Files:**
- Modify: `src/video_atlas/workflows/canonical_atlas_workflow.py`
- Modify: `src/video_atlas/workflows/canonical_atlas/pipeline.py`
- Modify: `scripts/run_evaluation.py`
- Test: `tests/test_canonical_two_stage_pipeline.py`
- Test: `tests/test_canonical_workflow_logging.py`
- Test: `tests/test_evaluation_script.py`

- [ ] **Step 1: 写失败测试**

补测试覆盖：
- `CanonicalAtlasWorkflow.create(...)` 新增 `structure_request`
- workflow 构造新增 `structure_composer`
- 主链从 `units` 走到 `segments`
- `structure_request` 只传给 Stage 2，不进入 Stage 1
- evaluation case 可向 canonical workflow 透传 `structure_request`

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_canonical_two_stage_pipeline tests.test_canonical_workflow_logging tests.test_evaluation_script -v
```

Expected:
- 接口断言失败或主链结果不匹配

- [ ] **Step 3: 实现主链接入**

要求：
- `CanonicalAtlasWorkflow.__init__` 新增 `structure_composer`
- `create(...)` 新增 `structure_request`
- `pipeline.py` 执行顺序改为：
  1. plan
  2. parse into units
  3. compose into segments
  4. finalize and package `CanonicalAtlas`
  5. write
- `video_parsing.py` 直接返回 `AtlasUnit`
- `pipeline.py` 从 units + composition result 直接打包最终 `CanonicalAtlas`
- `run_evaluation.py` 支持 case 级 `structure_request` 并透传到 canonical workflow

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_canonical_two_stage_pipeline tests.test_canonical_workflow_logging tests.test_evaluation_script -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_atlas/workflows/canonical_atlas_workflow.py src/video_atlas/workflows/canonical_atlas/pipeline.py src/video_atlas/workflows/canonical_atlas/video_parsing.py scripts/run_evaluation.py tests/test_canonical_two_stage_pipeline.py tests/test_canonical_workflow_logging.py tests/test_evaluation_script.py
git commit -m "feat: wire canonical stage two composition into workflow"
```

---

### Task 6: 扩展配置与默认配置，支持 `structure_composer`

**Files:**
- Modify: `src/video_atlas/config/models.py`
- Modify: `src/video_atlas/config/factories.py`
- Modify: `configs/canonical/default.json`
- Test: `tests/test_config_loading.py`

- [ ] **Step 1: 写失败测试**

在 `tests/test_config_loading.py` 中补：
- `CanonicalPipelineConfig` 支持 `structure_composer`
- 默认 canonical 配置包含 `structure_composer`

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_config_loading -v
```

Expected:
- 配置字段缺失

- [ ] **Step 3: 实现配置扩展**

要求：
- `CanonicalPipelineConfig` 增加 `structure_composer`
- loader 支持加载
- default config 给出合理默认模型与 connection

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_config_loading -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_atlas/config/models.py src/video_atlas/config/factories.py configs/canonical/default.json tests/test_config_loading.py
git commit -m "feat: add canonical structure composer config"
```

---

### Task 7: 实验期 canonical writer、loader 最小兼容与目录格式升级

**Files:**
- Modify: `src/video_atlas/persistence/writers.py`
- Modify: `src/video_atlas/review/workspace_loader.py`
- Test: `tests/test_workspace_writers.py`
- Test: `tests/test_review_loader.py`

- [ ] **Step 1: 写失败测试**

补测试覆盖：
- canonical atlas 根目录写出 `units/` 与 `segments/`
- `segments/<segment>/` 下复制完整 unit 媒体文件
- segment README 包含：
  - `unit_ids`
  - `composition_rationale`
- review loader 对新 canonical 目录结构具备最小读取能力，避免 writer 修改后出现中间状态断链

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_workspace_writers tests.test_review_loader -v
```

Expected:
- 目录结构或 README 断言失败

- [ ] **Step 3: 修改 writer**

要求：
- canonical writer 支持实验期目录结构
- `units/` 写 Stage 1 原始产物
- `segments/` 写最终结果并复制其包含的 units
- `workspace_loader.py` 在本任务内同步做最小适配，保证新目录结构一落地就可被读取

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_workspace_writers tests.test_review_loader -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_atlas/persistence/writers.py src/video_atlas/review/workspace_loader.py tests/test_workspace_writers.py tests/test_review_loader.py
git commit -m "feat: write experimental canonical units and segments layout"
```

---

### Task 8: review UI 与 evaluation 深度适配两阶段 canonical 输出

**Files:**
- Modify: `src/video_atlas/review/static/app.js`
- Modify: `scripts/run_evaluation.py`
- Test: `tests/test_evaluation_script.py`

- [ ] **Step 1: 写失败测试**

补测试覆盖：
- evaluation 脚本能构造 `structure_composer`
- review 以 `segments/` 为主入口，但保留 units 视图数据
- evaluation case 中的 `structure_request` 可被传递到 canonical workflow

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_evaluation_script -v
```

Expected:
- loader 或 evaluation orchestration 断言失败

- [ ] **Step 3: 实现适配**

要求：
- `run_evaluation.py` 构造 `structure_composer`
- UI 最小支持：
  - 查看最终 segments
  - 查看 segment 由哪些 units 组成

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_evaluation_script -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_atlas/review/static/app.js scripts/run_evaluation.py tests/test_evaluation_script.py
git commit -m "feat: support canonical two-stage outputs in review and evaluation"
```

---

### Task 9: 文档收口

**Files:**
- Modify: `docs/design-docs/module-design/canonical-atlas-workflow.md`
- Modify: `docs/design-docs/data-shemas/canonical-atlas.md`
- Modify: `docs/design-docs/data-shemas/atlas-segment.md`
- Modify: `docs/design-docs/data-shemas/atlas-unit.md`
- Modify: `docs/design-docs/data-shemas/canonical-composition-result.md`
- Modify: `docs/design-docs/atlas-layout/canonical-atlas-directory.md`
- Modify: `docs/design-docs/config-design/generator-config.md`
- Modify: `docs/index.md`

- [ ] **Step 1: 补文档测试清单**

人工检查清单：
- canonical workflow 文档写明两阶段结构
- canonical atlas / segment schema 文档写明 units 与 segments
- 新 schema 文档补齐：
  - `atlas-unit.md`
  - `canonical-composition-result.md`
- atlas layout 文档写明实验期目录结构
- config 文档写明 `structure_composer`
- `docs/index.md` 新增或更新索引

- [ ] **Step 2: 更新文档**

要求：
- 与最终实现严格一致
- 明确“当前是实验期目录结构”
- 不提前承诺最终正式产品目录形态

- [ ] **Step 3: 执行文档检查**

Run:
```bash
git diff --check -- docs
```

Expected:
- 无格式错误

- [ ] **Step 4: Commit**

```bash
git add docs/design-docs/module-design/canonical-atlas-workflow.md docs/design-docs/data-shemas/canonical-atlas.md docs/design-docs/data-shemas/atlas-segment.md docs/design-docs/data-shemas/atlas-unit.md docs/design-docs/data-shemas/canonical-composition-result.md docs/design-docs/atlas-layout/canonical-atlas-directory.md docs/design-docs/config-design/generator-config.md docs/index.md
git commit -m "docs: document canonical two-stage composition design"
```

---

### Task 10: 最终回归验证

**Files:**
- 无新增实现文件

- [ ] **Step 1: 运行 targeted test suite**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest \
  tests.test_canonical_schemes \
  tests.test_canonical_structure_composition \
  tests.test_canonical_two_stage_pipeline \
  tests.test_canonical_high_efficiency \
  tests.test_strategy_builder \
  tests.test_segmentation_streaming \
  tests.test_workspace_writers \
  tests.test_review_loader \
  tests.test_evaluation_script \
  tests.test_prompts \
  tests.test_config_loading \
  tests.test_import -v
```

Expected:
- PASS

- [ ] **Step 2: 运行编译检查**

Run:
```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m compileall src/video_atlas scripts/run_evaluation.py
```

Expected:
- compileall 成功

- [ ] **Step 3: 提交最终整合 commit**

```bash
git add .
git commit -m "feat: add canonical two-stage composition pipeline"
```

- [ ] **Step 4: 准备人工验收**

人工验收重点：
- podcast case 是否能形成更接近用户预期的 discussion/chapter 结构
- `units/` 与 `segments/` 的目录内容是否便于 review
- `structure_request` 是否确实只影响 Stage 2
