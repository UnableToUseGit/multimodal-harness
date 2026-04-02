# Canonical High Efficiency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `canonical atlas` 引入按视频类型自动切换的高效率 segmentation route，让文本叙事型视频在字幕可用时走文本分割路径，视觉叙事型视频继续走多模态分割路径。

**Architecture:** 本轮改动围绕 `SegmentationProfile -> runtime route -> boundary detection path` 这一链路展开。planner 不新增控制面，系统根据 profile 自动推导 route；route 决定使用哪个 segmentor、哪组 chunk 参数、哪条候选边界检测路径。caption 阶段保持现状，只优化 segmentation 阶段。

**Tech Stack:** Python 3.12, dataclasses, existing `CanonicalAtlasWorkflow`, OpenAI-compatible generators, current prompt system, unittest

---

## 文件结构与职责

### 需要修改的文件

- `src/video_atlas/schemas/canonical_atlas.py`
  - 扩展 `SegmentationProfile`
- `src/video_atlas/schemas/canonical_registry.py`
  - 为各 segmentation profile 声明 route
- `src/video_atlas/workflows/canonical_atlas_workflow.py`
  - workflow 接口升级为双 segmentor + route 级 chunk 参数
- `src/video_atlas/workflows/canonical_atlas/video_parsing.py`
  - 增加 route 推导、文本/多模态两条 boundary detection 路径、字幕回退逻辑
- `src/video_atlas/config/models.py`
  - canonical 运行时配置扩展为双 segmentor / 双 chunk 配置
- `src/video_atlas/config/factories.py`
  - 支持构造 text/multimodal 两个 segmentor
- `configs/canonical/default.json`
  - 默认配置结构对齐新 runtime 设计
- `docs/design-docs/module-design/canonical-atlas-workflow.md`
  - 同步 workflow 设计变化
- `docs/design-docs/data-shemas/segmentation-profile.md`
  - 同步 route 字段
- `docs/design-docs/config-design/generator-config.md`
  - 同步 text / multimodal segmentor 配置用法
- `docs/design-docs/config-design/transcriber-config.md`
  - 若字幕回退逻辑描述需要补充，则同步更新
- `docs/index.md`
  - 补充当前 active exec plan 索引

### 需要新增的文件

- `tests/test_canonical_high_efficiency.py`
  - 覆盖 route 推导、字幕回退、不同 route 使用不同 segmentor 和 chunk 参数

### 需要重点参考的现有文件

- `docs/decision-making/2026-0330-0609-canonical-high-efficiency.md`
- `src/video_atlas/workflows/canonical_atlas/plan.py`
- `src/video_atlas/prompts/canonical_prompts.py`
- `tests/test_segmentation_streaming.py`
- `tests/test_strategy_builder.py`

---

### Task 1: 为 SegmentationProfile 引入 route 字段

**Files:**
- Modify: `src/video_atlas/schemas/canonical_atlas.py`
- Modify: `src/video_atlas/schemas/canonical_registry.py`
- Test: `tests/test_canonical_high_efficiency.py`
- Docs: `docs/design-docs/data-shemas/segmentation-profile.md`

- [ ] **Step 1: Write the failing test**

在 `tests/test_canonical_high_efficiency.py` 中新增：

```python
import unittest

from video_atlas.schemas.canonical_registry import SEGMENTATION_PROFILES


class CanonicalHighEfficiencyRouteRegistryTest(unittest.TestCase):
    def test_text_narrative_profiles_use_text_llm_route(self):
        self.assertEqual(SEGMENTATION_PROFILES["podcast_topic_conversation"].segmentation_route, "text_llm")
        self.assertEqual(SEGMENTATION_PROFILES["lecture_slide_driven"].segmentation_route, "text_llm")
        self.assertEqual(SEGMENTATION_PROFILES["explanatory_commentary"].segmentation_route, "text_llm")

    def test_visual_profiles_use_multimodal_local_route(self):
        self.assertEqual(SEGMENTATION_PROFILES["narrative_film"].segmentation_route, "multimodal_local")
        self.assertEqual(SEGMENTATION_PROFILES["sports_broadcast"].segmentation_route, "multimodal_local")
        self.assertEqual(SEGMENTATION_PROFILES["vlog_lifestyle"].segmentation_route, "multimodal_local")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_canonical_high_efficiency.CanonicalHighEfficiencyRouteRegistryTest -v
```

Expected:
- FAIL，提示 `SegmentationProfile` 无 `segmentation_route` 字段或 registry 未声明该字段

- [ ] **Step 3: Write minimal implementation**

在 `src/video_atlas/schemas/canonical_atlas.py` 中为 `SegmentationProfile` 增加：

```python
segmentation_route: str
```

在 `src/video_atlas/schemas/canonical_registry.py` 中为所有 profile 补充 route，至少满足：

- 文本叙事型：
  - `podcast_topic_conversation` -> `text_llm`
  - `lecture_slide_driven` -> `text_llm`
  - `explanatory_commentary` -> `text_llm`
- 视觉叙事型：
  - `narrative_film` -> `multimodal_local`
  - `sports_broadcast` -> `multimodal_local`
  - `esports_match_broadcast` -> `multimodal_local`
  - `vlog_lifestyle` -> `multimodal_local`
  - `documentary` -> `multimodal_local`
  - fallback -> `multimodal_local`

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_canonical_high_efficiency.CanonicalHighEfficiencyRouteRegistryTest -v
```

Expected:
- PASS

- [ ] **Step 5: Update schema documentation**

在 `docs/design-docs/data-shemas/segmentation-profile.md` 中补充：
- `segmentation_route`
- 字段语义
- 当前允许值：`text_llm` / `multimodal_local`

- [ ] **Step 6: Commit**

```bash
git add src/video_atlas/schemas/canonical_atlas.py src/video_atlas/schemas/canonical_registry.py tests/test_canonical_high_efficiency.py docs/design-docs/data-shemas/segmentation-profile.md
git commit -m "feat: add segmentation route to canonical profiles"
```

---

### Task 2: 扩展 canonical runtime 配置为双 segmentor / 双 chunk 参数

**Files:**
- Modify: `src/video_atlas/config/models.py`
- Modify: `src/video_atlas/config/factories.py`
- Modify: `configs/canonical/default.json`
- Test: `tests/test_config_loading.py`
- Docs: `docs/design-docs/config-design/generator-config.md`

- [ ] **Step 1: Write the failing test**

在 `tests/test_config_loading.py` 中新增或扩展：

```python
def test_canonical_config_supports_dual_segmentors_and_dual_chunk_settings(self):
    config = load_canonical_config(...)
    self.assertEqual(config.text_segmentor.model_name, "...")
    self.assertEqual(config.multimodal_segmentor.model_name, "...")
    self.assertEqual(config.runtime.text_chunk_size_sec, 1800)
    self.assertEqual(config.runtime.multimodal_chunk_size_sec, 600)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_config_loading -v
```

Expected:
- FAIL，提示 canonical config 模型尚不支持双 segmentor / 双 chunk

- [ ] **Step 3: Write minimal implementation**

在 `src/video_atlas/config/models.py` 中：
- 将 canonical workflow 所需配置升级为：
  - `text_segmentor`
  - `multimodal_segmentor`
  - `captioner`
  - `planner`
- runtime 增加：
  - `text_chunk_size_sec`
  - `text_chunk_overlap_sec`
  - `multimodal_chunk_size_sec`
  - `multimodal_chunk_overlap_sec`

在 `src/video_atlas/config/factories.py` 中：
- 新增构造 text / multimodal segmentor 的工厂路径

在 `configs/canonical/default.json` 中：
- 迁移旧 `segmentor` 为：
  - `text_segmentor`
  - `multimodal_segmentor`
- 写入两组 chunk 参数

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_config_loading -v
```

Expected:
- PASS

- [ ] **Step 5: Update configuration documentation**

在 `docs/design-docs/config-design/generator-config.md` 中补充：
- canonical workflow 现在存在两个 segmentor 配置位
- route 与 segmentor 的绑定关系
- route 级 chunk 参数

- [ ] **Step 6: Commit**

```bash
git add src/video_atlas/config/models.py src/video_atlas/config/factories.py configs/canonical/default.json tests/test_config_loading.py docs/design-docs/config-design/generator-config.md
git commit -m "feat: add dual segmentor canonical config"
```

---

### Task 3: 升级 CanonicalAtlasWorkflow 接口

**Files:**
- Modify: `src/video_atlas/workflows/canonical_atlas_workflow.py`
- Test: `tests/test_prompts.py`
- Test: `tests/test_import.py`
- Docs: `docs/design-docs/module-design/canonical-atlas-workflow.md`

- [ ] **Step 1: Write the failing test**

在 `tests/test_prompts.py` 或新增小测试中验证：

```python
workflow = CanonicalAtlasWorkflow(
    planner=planner,
    text_segmentor=text_segmentor,
    multimodal_segmentor=multimodal_segmentor,
    captioner=captioner,
)
assert workflow.text_segmentor is text_segmentor
assert workflow.multimodal_segmentor is multimodal_segmentor
```

并在 `tests/test_import.py` 保证新的 workflow 构造路径仍可导入。

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_prompts tests.test_import -v
```

Expected:
- FAIL，提示构造参数不匹配

- [ ] **Step 3: Write minimal implementation**

在 `src/video_atlas/workflows/canonical_atlas_workflow.py` 中：
- `__init__` 改为接收：
  - `planner`
  - `text_segmentor`
  - `multimodal_segmentor`
  - `captioner`
  - `transcriber`
- 保存 route 级 chunk 配置

注意：
- 本轮不要为了兼容历史接口保留太多旁路逻辑
- 但要保证调用面清晰可解释

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_prompts tests.test_import -v
```

Expected:
- PASS

- [ ] **Step 5: Update module design documentation**

在 `docs/design-docs/module-design/canonical-atlas-workflow.md` 中同步：
- 双 segmentor 接口
- route 级运行时策略

- [ ] **Step 6: Commit**

```bash
git add src/video_atlas/workflows/canonical_atlas_workflow.py tests/test_prompts.py tests/test_import.py docs/design-docs/module-design/canonical-atlas-workflow.md
git commit -m "refactor: split canonical segmentation backends"
```

---

### Task 4: 实现 route 推导与字幕回退逻辑

**Files:**
- Modify: `src/video_atlas/workflows/canonical_atlas/video_parsing.py`
- Test: `tests/test_canonical_high_efficiency.py`

- [ ] **Step 1: Write the failing test**

在 `tests/test_canonical_high_efficiency.py` 中新增：

```python
class CanonicalHighEfficiencyRouteDecisionTest(unittest.TestCase):
    def test_text_route_is_used_when_profile_is_text_and_subtitles_are_available(self): ...
    def test_text_route_falls_back_to_multimodal_when_subtitles_are_missing(self): ...
    def test_visual_profile_always_uses_multimodal_route(self): ...
```

测试目标：
- profile=`text_llm` + 字幕存在 -> route=`text_llm`
- profile=`text_llm` + 字幕缺失 -> route=`multimodal_local`
- profile=`multimodal_local` -> route=`multimodal_local`

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_canonical_high_efficiency.CanonicalHighEfficiencyRouteDecisionTest -v
```

Expected:
- FAIL，当前尚无 route 推导逻辑

- [ ] **Step 3: Write minimal implementation**

在 `src/video_atlas/workflows/canonical_atlas/video_parsing.py` 中增加一个小而清晰的内部入口，例如：

```python
def _resolve_segmentation_route(self, execution_plan, subtitle_items) -> str:
    ...
```

规则：
- 若 profile.route == `text_llm`
  - 且 `subtitle_items` 非空 -> `text_llm`
  - 否则 -> `multimodal_local`
- 若 profile.route == `multimodal_local`
  - 直接返回 `multimodal_local`

不要在这一步引入“字幕过稀”规则。

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_canonical_high_efficiency.CanonicalHighEfficiencyRouteDecisionTest -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_atlas/workflows/canonical_atlas/video_parsing.py tests/test_canonical_high_efficiency.py
git commit -m "feat: add canonical segmentation route resolution"
```

---

### Task 5: 拆分文本与多模态两条 boundary detection 路径

**Files:**
- Modify: `src/video_atlas/workflows/canonical_atlas/video_parsing.py`
- Modify: `src/video_atlas/prompts/canonical_prompts.py`
- Test: `tests/test_canonical_high_efficiency.py`
- Test: `tests/test_segmentation_streaming.py`

- [ ] **Step 1: Write the failing test**

在 `tests/test_canonical_high_efficiency.py` 中新增：

```python
def test_text_route_uses_text_segmentor_and_text_messages(self): ...
def test_multimodal_route_uses_multimodal_segmentor_and_video_messages(self): ...
```

断言重点：
- 文本路径不调用 `_build_video_messages_from_path`
- 文本路径使用 `build_text_messages` 等价产物
- 多模态路径继续调用 `_build_video_messages_from_path`
- 两条路径调用的 segmentor 不同

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_canonical_high_efficiency tests.test_segmentation_streaming -v
```

Expected:
- FAIL

- [ ] **Step 3: Write minimal implementation**

在 `src/video_atlas/workflows/canonical_atlas/video_parsing.py` 中拆出：

- `_detect_candidate_boundaries_for_chunk_text(...)`
- `_detect_candidate_boundaries_for_chunk_multimodal(...)`

在 `src/video_atlas/prompts/canonical_prompts.py` 中新增一个文本分割专用 prompt，例如：

- `TEXT_BOUNDARY_DETECTION_PROMPT`

文本路径：
- 只构造 text messages
- 只使用 subtitles + concise description + segmentation policy
- 使用 `text_segmentor`
- 使用 `TEXT_BOUNDARY_DETECTION_PROMPT`

多模态路径：
- 保持现有逻辑
- 使用 `multimodal_segmentor`
- 继续使用现有 `BOUNDARY_DETECTION_PROMPT`

在 `src/video_atlas/prompts/canonical_prompts.py` 中：
- 文本分割 prompt 必须避免复用“Frames”导向过强的多模态 prompt 文案
- prompt 文档与模块设计文档如有必要同步补充

注意：
- 不要改 caption prompt
- 不要把两条路径重新塞回一个臃肿函数里

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_canonical_high_efficiency tests.test_segmentation_streaming -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_atlas/workflows/canonical_atlas/video_parsing.py src/video_atlas/prompts/canonical_prompts.py tests/test_canonical_high_efficiency.py tests/test_segmentation_streaming.py
git commit -m "feat: add text and multimodal segmentation paths"
```

---

### Task 6: 让不同 route 使用不同的 chunk 参数

**Files:**
- Modify: `src/video_atlas/workflows/canonical_atlas/video_parsing.py`
- Test: `tests/test_canonical_high_efficiency.py`

- [ ] **Step 1: Write the failing test**

在 `tests/test_canonical_high_efficiency.py` 中新增：

```python
def test_text_route_uses_text_chunk_settings(self): ...
def test_multimodal_route_uses_multimodal_chunk_settings(self): ...
```

断言：
- 文本路径使用 `text_chunk_size_sec` / `text_chunk_overlap_sec`
- 多模态路径使用 `multimodal_chunk_size_sec` / `multimodal_chunk_overlap_sec`

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_canonical_high_efficiency -v
```

Expected:
- FAIL

- [ ] **Step 3: Write minimal implementation**

在 `src/video_atlas/workflows/canonical_atlas/video_parsing.py` 中：
- 让 `_parse_video_into_segments(...)` 在循环前先确定 route
- 根据 route 选择 chunk_size / overlap

要求：
- 不把 route 判定写进循环体的多个位置
- route 和 route config 选择尽量集中在一个小的 helper 中

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_canonical_high_efficiency -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_atlas/workflows/canonical_atlas/video_parsing.py tests/test_canonical_high_efficiency.py
git commit -m "feat: bind canonical chunk strategy to segmentation route"
```

---

### Task 7: 更新文档与索引

**Files:**
- Modify: `docs/design-docs/module-design/canonical-atlas-workflow.md`
- Modify: `docs/design-docs/data-shemas/segmentation-profile.md`
- Modify: `docs/design-docs/config-design/generator-config.md`
- Modify: `docs/index.md`

- [ ] **Step 1: Update canonical workflow documentation**

补充：
- segmentation route 概念
- 双 segmentor
- 文本路径与多模态路径
- 字幕缺失回退逻辑

- [ ] **Step 2: Update schema/config documentation**

补充：
- `SegmentationProfile.segmentation_route`
- text / multimodal segmentor 配置位
- route 级 chunk 参数

- [ ] **Step 3: Update docs index**

在 `docs/index.md` 的执行计划部分补充当前 active plan：

- `2026-03-30-canonical-high-efficiency-implementation.md`

- [ ] **Step 4: Commit**

```bash
git add docs/design-docs/module-design/canonical-atlas-workflow.md docs/design-docs/data-shemas/segmentation-profile.md docs/design-docs/config-design/generator-config.md docs/index.md
git commit -m "docs: update canonical high efficiency design docs"
```

---

### Task 8: 全量验证与基准检查

**Files:**
- Modify: none unless verification exposes issues
- Test: existing test suite + selected evaluation config

- [ ] **Step 1: Run focused unit tests**

Run:

```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest \
  tests.test_canonical_high_efficiency \
  tests.test_config_loading \
  tests.test_segmentation_streaming \
  tests.test_prompts \
  tests.test_import -v
```

Expected:
- PASS

- [ ] **Step 2: Run regression tests for canonical persistence / review chain**

Run:

```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest \
  tests.test_workspace_writers \
  tests.test_review_loader \
  tests.test_global_atlas_generation -v
```

Expected:
- PASS

- [ ] **Step 3: Run compile check**

Run:

```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m compileall src/video_atlas
```

Expected:
- compileall completes without syntax errors

- [ ] **Step 4: Run selected evaluation cases**

在目标服务器环境上选两组 case：

- 文本叙事型：
  - `podcast`
  - `lecture`
  - `explanatory_commentary`
- 视觉叙事型：
  - `sports_broadcast`
  - `narrative_film`
  - `vlog`

Run:

```bash
PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python scripts/run_evaluation.py --config <evaluation-config>
```

Expected:
- 文本型 case 的 canonical segmentation 耗时显著下降
- 视觉型 case 不出现明显 segmentation 回归

- [ ] **Step 5: Final commit if verification uncovered minor fixes**

```bash
git add -A
git commit -m "test: verify canonical high efficiency optimization"
```

---

## 环境与配置前提

- 本轮优化默认 `text_segmentor` 与 `multimodal_segmentor` 来自不同服务端点。
- `multimodal_segmentor` 使用本地部署服务，对应本地 API 环境变量。
- `text_segmentor` 使用远程部署服务，对应远程 API 环境变量。

建议在配置与 settings 层明确分离两套连接信息：

- `LOCAL_API_BASE`
- `LOCAL_API_KEY`
- `REMOTE_API_BASE`
- `REMOTE_API_KEY`

实现时需要确保：

- `multimodal_segmentor` 绑定 `LOCAL_API_*`
- `text_segmentor` 绑定 `REMOTE_API_*`
- 不再假设所有 generator 共用同一组 `api_base` 与 `api_key`

对应实现落点预计包括：

- `src/video_atlas/settings.py`
- `src/video_atlas/generators/openai_compatible.py`
- `src/video_atlas/config/factories.py`
- `docs/design-docs/config-design/generator-config.md`

若现有 `OpenAICompatibleGenerator` 只支持读取单一 `VIDEO_ATLAS_API_BASE` / `VIDEO_ATLAS_API_KEY`，则需在本轮中补足“按 generator 配置选择连接信息”的能力。
