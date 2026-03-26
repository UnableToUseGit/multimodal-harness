# Derived Atlas Prompts

本文档记录 derived atlas workflow 当前使用的 prompt 契约。对应代码位于 [derived_prompts.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/prompts/derived_prompts.py)，运行时统一以 `PromptSpec` 形式导出，并通过 [prompts/__init__.py](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/src/video_atlas/prompts/__init__.py) 注册到 `PROMPT_REGISTRY`。

## `DERIVED_CANDIDATE_PROMPT`

**目的 / 作用**

用于 `CandidateGeneration` 阶段，从 canonical atlas 中选出应参与衍生的源片段。

**PromptSpec 元信息**

- `name`: `DERIVED_CANDIDATE_PROMPT`
- `tags`: `("derived", "candidate")`
- `output_contract`: `strict JSON object with candidates array`

**输入字段**

- `task_request`
- `canonical_segments`

**输出**

严格 JSON 对象，包含 `candidates` 数组。每个候选项包含：

- `segment_id`
- `intent`
- `grounding_instruction`

## `DERIVED_GROUNDING_PROMPT`

**目的 / 作用**

用于 `Derivation` 阶段，对单个源 canonical segment 做 task-aware re-grounding，产出更精细的子片段时间范围。

**PromptSpec 元信息**

- `name`: `DERIVED_GROUNDING_PROMPT`
- `tags`: `("derived", "grounding")`
- `output_contract`: `strict JSON object with start_time and end_time`

**输入字段**

- `segment_id`
- `segment_start_time`
- `segment_end_time`
- `intent`
- `grounding_instruction`
- `summary`
- `detail`
- `subtitles`

**输出**

严格 JSON 对象，包含：

- `start_time`
- `end_time`

返回时间范围可能是绝对时间，也可能是相对于源 segment 的局部时间。workflow 负责做解析、换算和边界裁剪。

## `DERIVED_CAPTION_PROMPT`

**目的 / 作用**

用于 `Derivation` 阶段，在 re-grounding 后为 refined sub-clip 生成 task-aware 文本元数据。

**PromptSpec 元信息**

- `name`: `DERIVED_CAPTION_PROMPT`
- `tags`: `("derived", "caption")`
- `output_contract`: `strict JSON object with title, summary, and caption`

**输入字段**

- `task_request`
- `segment_id`
- `start_time`
- `end_time`
- `intent`
- `grounding_instruction`
- `summary`
- `detail`
- `subtitles`

**输出**

严格 JSON 对象，包含：

- `title`
- `summary`
- `caption`

## 说明

- 这些 prompt 现在都以 `PromptSpec` 对象定义，而不再以裸字典常量作为主形态。
- workflow 当前推荐通过 `render_system(...)`、`render_user(...)` 或 `render(...)` 使用这些 prompt。
- prompt 文案修改、输入字段变更和输出契约变更，应同步更新代码、测试和本文档。
