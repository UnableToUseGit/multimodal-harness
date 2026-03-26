# Prompts Registry Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `src/video_atlas/prompts` 从裸字典常量集合升级为 `PromptSpec + PromptRegistry` 的可管理 prompt 模块，并保持 canonical/derived workflow 正常工作。

**Architecture:** 新增轻量 `PromptSpec` 和 `PromptRegistry` 作为 prompt 的核心定义与统一入口；现有 canonical/derived prompt 文件继续保留，但导出对象改为 `PromptSpec`。workflow 侧只做最小适配，继续通过统一字段获取 `system` / `user` 模板，并补测试覆盖注册、渲染和兼容调用路径。

**Tech Stack:** Python dataclasses, existing unittest suite, current `video_atlas.prompts` package

---

### Task 1: 定义 PromptSpec 与 PromptRegistry

**Files:**
- Create: `src/video_atlas/prompts/specs.py`
- Test: `tests/test_prompts.py`

- [ ] **Step 1: 写出失败测试**

覆盖这些行为：
- `PromptSpec` 保存 name、purpose、templates、input_fields、output_contract
- `PromptSpec.render(...)` 能渲染 system/user
- 缺失必填输入字段时抛错
- `PromptRegistry` 能注册、查询、列举 prompt
- 重复注册同名 prompt 时抛错

- [ ] **Step 2: 运行测试确认失败**

Run: `PYTHONPATH=src python3 -m unittest tests.test_prompts -v`
Expected: FAIL，提示缺少 `specs.py` 或对应对象

- [ ] **Step 3: 写最小实现**

在 `src/video_atlas/prompts/specs.py` 中实现：
- `PromptSpec`
- `PromptRegistry`
- 轻量渲染与输入字段校验能力

- [ ] **Step 4: 运行测试确认通过**

Run: `PYTHONPATH=src python3 -m unittest tests.test_prompts -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/video_atlas/prompts/specs.py tests/test_prompts.py
git commit -m "feat: add prompt spec and registry"
```

### Task 2: 将现有 prompts 迁移到 PromptSpec

**Files:**
- Modify: `src/video_atlas/prompts/canonical_prompts.py`
- Modify: `src/video_atlas/prompts/derived_prompts.py`
- Modify: `src/video_atlas/prompts/__init__.py`
- Test: `tests/test_prompts.py`

- [ ] **Step 1: 扩展失败测试**

补充覆盖：
- canonical/derived prompt 导出对象变为 `PromptSpec`
- 现有 prompt 名称可通过 registry 获取
- prompt 的关键 `input_fields` 已声明

- [ ] **Step 2: 运行测试确认失败**

Run: `PYTHONPATH=src python3 -m unittest tests.test_prompts -v`
Expected: FAIL，提示现有 prompt 仍为 dict

- [ ] **Step 3: 写最小实现**

修改 prompt 文件：
- 将现有 prompt 常量从 dict 升级为 `PromptSpec`
- 保留现有 prompt 文本内容
- 在 `__init__.py` 中提供 registry 或等价统一查询入口

- [ ] **Step 4: 运行测试确认通过**

Run: `PYTHONPATH=src python3 -m unittest tests.test_prompts -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/video_atlas/prompts/canonical_prompts.py src/video_atlas/prompts/derived_prompts.py src/video_atlas/prompts/__init__.py tests/test_prompts.py
git commit -m "refactor: migrate prompts to prompt specs"
```

### Task 3: 适配 workflow 调用链

**Files:**
- Modify: `src/video_atlas/workflows/canonical_atlas_workflow.py`
- Modify: `src/video_atlas/workflows/canonical_atlas/plan.py`
- Modify: `src/video_atlas/workflows/canonical_atlas/video_parsing.py`
- Modify: `src/video_atlas/workflows/canonical_atlas/atlas_assembly.py`
- Modify: `src/video_atlas/workflows/derived_atlas_workflow.py`
- Modify: `src/video_atlas/workflows/derived_atlas/candidate_generation.py`
- Modify: `src/video_atlas/workflows/derived_atlas/derivation.py`
- Test: `tests/test_derived_pipeline.py`
- Test: `tests/test_import.py`
- Test: `tests/test_prompts.py`

- [ ] **Step 1: 扩展失败测试**

补充覆盖：
- workflow 仍能从 prompt 对象中取出 `system` / `user`
- canonical / derived 关键流程的 prompt 使用路径不回退为裸 dict

- [ ] **Step 2: 运行测试确认失败**

Run: `PYTHONPATH=src python3 -m unittest tests.test_prompts tests.test_derived_pipeline tests.test_import -v`
Expected: FAIL，提示 workflow 仍假设 prompt 是 dict

- [ ] **Step 3: 写最小实现**

调整 workflow 调用：
- 统一通过 `PromptSpec` 访问模板
- 在需要格式化时显式调用渲染能力或等价 helper
- 保持现有行为与输出不变

- [ ] **Step 4: 运行测试确认通过**

Run: `PYTHONPATH=src python3 -m unittest tests.test_prompts tests.test_derived_pipeline tests.test_import -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/video_atlas/workflows/canonical_atlas_workflow.py src/video_atlas/workflows/canonical_atlas/plan.py src/video_atlas/workflows/canonical_atlas/video_parsing.py src/video_atlas/workflows/canonical_atlas/atlas_assembly.py src/video_atlas/workflows/derived_atlas_workflow.py src/video_atlas/workflows/derived_atlas/candidate_generation.py src/video_atlas/workflows/derived_atlas/derivation.py tests/test_prompts.py tests/test_derived_pipeline.py tests/test_import.py
git commit -m "refactor: switch workflows to prompt specs"
```

### Task 4: 更新 prompt 文档与模块文档

**Files:**
- Modify: `docs/design-docs/module-design/prompts.md`
- Modify: `docs/design-docs/prompts/derived-atlas-prompts.md`
- Test: none

- [ ] **Step 1: 更新设计文档**

将文档中的“目标形态”部分收窄为“当前实现形态”，写清：
- `PromptSpec`
- `PromptRegistry`
- 当前 registry 入口
- prompt 文档与代码的对应关系

- [ ] **Step 2: 自检文档一致性**

检查 prompt 名称、输入字段、输出契约与代码一致。

- [ ] **Step 3: 提交**

```bash
git add docs/design-docs/module-design/prompts.md docs/design-docs/prompts/derived-atlas-prompts.md
git commit -m "docs: update prompt module design"
```

### Task 5: 全量验证

**Files:**
- Modify: none
- Test: `tests/test_prompts.py`
- Test: `tests/test_derived_pipeline.py`
- Test: `tests/test_import.py`

- [ ] **Step 1: 运行目标测试**

Run: `PYTHONPATH=src python3 -m unittest tests.test_prompts tests.test_derived_pipeline tests.test_import -v`
Expected: PASS

- [ ] **Step 2: 运行导入与编译验证**

Run: `PYTHONPATH=src python3 -m compileall src/video_atlas`
Expected: PASS

- [ ] **Step 3: 如无问题，准备交付说明**

说明：
- 新增了哪些 prompt 基础对象
- workflow 适配点在哪
- 文档如何更新
