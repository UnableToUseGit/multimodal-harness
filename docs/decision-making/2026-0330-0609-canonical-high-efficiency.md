# Canonical Atlas 高效率分割工程优化计划

## 背景

当前 `canonical atlas` 的分割实现主要以“统一多模态分割流程”为中心。无论视频类型如何，系统都会默认使用多模态 `segmentor`，并采用一套相对固定的 chunk 策略完成候选边界检测。

这一实现方式在算法上是成立的，但在工程效率上存在明显浪费。视频的异质性很强，不同类型视频对分割证据的依赖程度差异很大：

- `podcast_interview`
- `lecture_talk`
- `explanatory_commentary`
- 很多 `tutorial_howto`

这类视频以文本叙事为主，语义结构主要体现在字幕/口语内容中。对于它们，只要字幕可用，系统通常不需要依赖视频帧即可完成较高质量的粗粒度分割。

与之相对：

- `narrative_film`
- `sports_broadcast`
- `esports_match_broadcast`
- `vlog_lifestyle`
- 一部分 `documentary`

这类视频更依赖画面叙事、场景变化、镜头组织、回放块、动作过程或视觉结构，因此必须继续保留多模态分割路径。

此外，两类路径在运行时资源形态上也完全不同：

- 文本分割路径适合使用远程大语言模型，允许更大的 chunk
- 多模态分割路径适合使用本地部署的视觉模型，需要更保守的 chunk 参数

这意味着“是否走文本分割”不只是一个 prompt 层问题，而是一个完整的运行时工程优化问题。

## 优化目的

本轮工程优化的目标是：

- 让 `canonical atlas` 在保持现有分割质量目标不变的前提下，对不同视频类型选择更合适的分割执行路线。
- 对文本叙事型视频引入更高效率的文本分割路径，减少不必要的视频帧处理和多模态模型调用。
- 保持视觉叙事型视频继续走现有多模态分割路径，不牺牲这类视频的分割质量。
- 将“分割路线选择”正式沉淀为系统级工程设计，而不是散落在 workflow 中的临时分支。

## 本轮要完成的大体内容

本轮优化聚焦 `canonical atlas` 的 segmentation 阶段，不扩展到 derived atlas。

需要完成的内容包括：

1. 在 segmentation profile 中正式引入“分割执行路线”概念。
2. 让系统根据 profile 自动推导应走的 segmentation route，而不是由 planner 显式控制。
3. 在 `canonical atlas workflow` 中拆出两条候选边界检测路径：
   - 文本分割路径
   - 多模态分割路径
4. 让不同路径绑定不同的：
   - `segmentor`
   - `chunk_size_sec`
   - `chunk_overlap_sec`
5. 明确文本路径的回退规则：
   - 当字幕缺失且转写失败时，自动回退到多模态路径
6. 保持 caption 阶段不变，仍然统一使用多模态 caption。

## 本轮不做的内容

为了保持边界清晰，本轮不包含以下内容：

- 不让 planner 直接输出 segmentation route。
- 不让 planner 控制 `segmentor` 选择或 chunk 参数。
- 不同时优化 caption 路径。
- 不引入“字幕过稀时自动回退”的启发式规则。
- 不扩展到 derived atlas workflow。
- 不在本轮中引入新的 planner schema 变更。

## 核心设计

### 1. 引入 Segmentation Route

建议在 `SegmentationProfile` 中新增字段：

- `segmentation_route`

其含义是：该 profile 在工程执行层默认应采用哪一种分割路线。

本轮先只定义两类 route：

- `text_llm`
- `multimodal_local`

这个字段的职责不是表达内容语义，而是表达运行时执行策略。

### 2. Route 由系统自动推导，不由 planner 输出

本轮不增加 planner 的控制面。route 由系统自动根据 `segmentation_profile` 推导。

原因：

- 这是工程优化问题，不是 planner 智能增强问题。
- 若把 route 放进 planner 输出，会扩大 planner 的不稳定面和调试成本。
- 对于绝大多数视频类型，route 与 profile 的映射关系是稳定的。

因此，推荐使用如下策略：

- 文本叙事型 profile 默认对应 `text_llm`
- 视觉叙事型 profile 默认对应 `multimodal_local`

### 3. Route 决定的不只是输入模态

本轮需要明确：route 不只是决定是否使用视频帧。

它还同时决定：

- 使用哪个 `segmentor`
- 使用什么 `chunk_size_sec`
- 使用什么 `chunk_overlap_sec`
- 使用哪条 boundary detection 路径

因此，route 本质上是一个 segmentation runtime strategy。

### 4. 两条 Boundary Detection 路径

建议在 canonical parsing 中拆成两条明确的候选边界检测路径：

- `_detect_candidate_boundaries_for_chunk_text(...)`
- `_detect_candidate_boundaries_for_chunk_multimodal(...)`

其中：

#### 文本分割路径

- 输入：字幕文本 + segmentation policy + concise description 等文本上下文
- 不读取视频帧
- 使用远程文本 LLM 作为 `text_segmentor`
- 可使用更大的 chunk

适用前提：

- 当前 profile 对应 `text_llm`
- 且存在可用字幕（包括原始 `subtitles.srt` 或成功生成的字幕）

#### 多模态分割路径

- 输入：视频帧 + 字幕 + segmentation policy + concise description
- 使用本地多模态模型作为 `multimodal_segmentor`
- 保持当前较保守的 chunk 设置

适用前提：

- 当前 profile 对应 `multimodal_local`
- 或文本路线所需字幕不可用

### 5. 字幕回退规则

本轮只采用一个清晰、可判定的回退规则：

- 若 `text_llm` 路线所需的字幕不可用，则回退到 `multimodal_local`

这里的“字幕不可用”指：

- 没有现成 `subtitles.srt`
- 并且转写流程也未能成功产出可解析字幕

本轮不引入“字幕过稀”“字幕质量较低”这类启发式回退条件。

### 6. Workflow 接口调整

当前 `CanonicalAtlasWorkflow` 中只有一个 `segmentor`，这已经不足以表达新的运行时设计。

建议升级为显式接收两类 segmentor：

- `text_segmentor`
- `multimodal_segmentor`

同时保留：

- `planner`
- `captioner`
- `transcriber`

其中：

- 文本分割路径使用 `text_segmentor`
- 多模态分割路径使用 `multimodal_segmentor`
- caption 继续统一使用 `captioner`

### 7. Chunk 参数从统一值改为按 Route 绑定

当前 workflow 的 chunk 参数是统一值：

- `chunk_size_sec`
- `chunk_overlap_sec`

本轮建议将其拆为 route 级配置，例如：

- `text_chunk_size_sec`
- `text_chunk_overlap_sec`
- `multimodal_chunk_size_sec`
- `multimodal_chunk_overlap_sec`

原因：

- 文本分割路径可承受更大 chunk，例如 30 分钟到 1 小时
- 多模态分割路径仍需要保守控制窗口大小

这部分不应继续通过一套统一参数管理。

### 8. Caption 阶段暂不优化

本轮明确不调整 caption 的执行路线。

即使 segmentation 走文本路径：

- caption 仍然保持多模态
- 这样可以避免本轮同时引入“分割变更 + 描述变更”的混合变量

这能使实验边界更清楚，也更有利于评估 segmentation 工程优化本身的收益。

## 推荐的实现顺序

### 里程碑 1：引入 route 概念并完成配置建模

目标：

- 在 profile/schema/config 层正式表达 segmentation route
- 明确文本型与多模态型 profile 的 route 映射

应完成：

- `SegmentationProfile` 扩展
- canonical registry 补充 route
- canonical 配置支持双 segmentor 和双 chunk 配置
- 相关数据模式文档与配置文档更新

### 里程碑 2：实现 route 推导与两条分割路径

目标：

- workflow 能根据 profile 和字幕可用性自动选择 route

应完成：

- 运行时 route 推导逻辑
- 文本分割路径实现
- 多模态分割路径保留并显式化
- 字幕缺失回退逻辑

### 里程碑 3：将 route 与不同 segmentor / chunk 参数绑定

目标：

- 让 text route 和 multimodal route 真正走不同的 runtime 资源组合

应完成：

- `CanonicalAtlasWorkflow` 接口升级
- 工厂或构造逻辑支持两个 segmentor
- 不同 route 使用不同 chunk 参数

### 里程碑 4：验证与基准评估

目标：

- 证明工程优化确实带来效率收益，且不会显著损害质量

应完成：

- 选取文本叙事型视频进行前后对比
- 选取视觉叙事型视频确认无回归
- 比较：
  - 总耗时
  - segmentation 阶段耗时
  - segment 数量与粒度稳定性
  - 关键 case 的人工主观质量

## 验收标准

本轮优化完成后，应满足以下标准：

### 1. 功能正确性

- 文本叙事型视频在字幕可用时，能够走文本分割路径完成分割。
- 视觉叙事型视频仍然走多模态分割路径。
- 文本叙事型视频在字幕不可用时，能够自动回退到多模态路径。
- caption 阶段行为与当前保持一致。

### 2. 工程结构

- route 不通过 planner 输出控制。
- route 规则集中定义，不散落在 workflow 的硬编码分支中。
- `segmentor`、chunk 参数和输入模态的选择都能由 route 清晰解释。

### 3. 性能收益

- 对文本叙事型视频，segmentation 阶段耗时应明显下降。
- 整体 canonical atlas 构建耗时应出现可观察的工程优化收益。

### 4. 质量要求

- 文本叙事型视频的 segment 粒度不应明显劣化。
- 视觉叙事型视频的现有 segmentation 效果不应出现明显回归。
- 回退机制应在字幕缺失场景下稳定工作。

## 建议的下一步

本计划确认后，建议先写一份更细的实现计划，重点覆盖：

- schema / config 变更
- workflow 接口调整
- 两条分割路径的测试设计
- evaluation case 如何分组验证

该实现计划应严格限定范围，只覆盖本轮 canonical atlas segmentation 的工程优化，不并入 caption、derived atlas 或 planner schema 的其他实验性改动。
