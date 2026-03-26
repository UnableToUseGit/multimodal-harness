# Transcriber 配置设计

## 文档目标

本文档用于说明 `Transcriber` 相关配置的结构、字段定义、默认值、来源和约束。本文档面向开发者与维护者，目标是帮助读者理解 transcriber 配置控制什么、应如何提供，以及它如何影响字幕生成行为。

## 配置对象概览

- 名称：`TranscriberRuntimeConfig`
- 作用：描述字幕生成阶段的转写器运行时配置
- 实现形式：`dataclass`
- 所属模块：`src/video_atlas/config/models.py`

## 配置项定义

| 配置项 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `enabled` | `bool` | 否 | `True` | 是否启用转写器 |
| `backend` | `str` | 否 | `"faster_whisper"` | 转写后端 |
| `model_size_or_path` | `str` | 否 | `"small"` | Faster Whisper 模型标识或路径 |
| `device` | `str` | 否 | `"cpu"` | 运行设备 |
| `compute_type` | `str` | 否 | `"int8"` | 推理精度类型 |
| `language` | `str \| None` | 否 | `None` | 目标语言 |
| `vad_filter` | `bool` | 否 | `True` | 是否启用 VAD 过滤 |
| `min_silence_duration_ms` | `int` | 否 | `500` | 最小静音时长 |
| `use_batched_inference` | `bool` | 否 | `False` | 是否启用 batched inference |
| `batch_size` | `int` | 否 | `8` | batched inference 的 batch 大小 |

## 配置项说明

### `enabled`

- 语义：决定系统是否启用自动字幕生成能力。
- 约束：布尔值。
- 对行为的影响：为 `False` 时，`build_transcriber(...)` 返回 `None`。

### `backend`

- 语义：标识转写后端类型。
- 约束：当前仅支持 `faster_whisper`。
- 对行为的影响：决定使用哪一种具体转写实现。

### `model_size_or_path`

- 语义：指定 Faster Whisper 模型名称或本地路径。
- 约束：应为合法模型标识或可访问路径。
- 对行为的影响：决定转写模型体量与精度。

### `device`

- 语义：指定推理设备。
- 约束：应与运行环境匹配。
- 对行为的影响：决定 CPU/GPU 推理路径。

### `compute_type`

- 语义：指定推理精度类型。
- 约束：应为后端支持的值。
- 对行为的影响：决定速度、显存与精度之间的平衡。

### `language`

- 语义：指定转写语言。
- 约束：可为空。
- 对行为的影响：为空时由后端自行推断。

### `vad_filter`

- 语义：决定是否启用语音活动检测。
- 约束：布尔值。
- 对行为的影响：影响空白段过滤和转写鲁棒性。

### `min_silence_duration_ms`

- 语义：控制 VAD 中最小静音时长。
- 约束：应为非负整数。
- 对行为的影响：通过 `vad_parameters` 传递到底层实现。

### `use_batched_inference`

- 语义：决定是否启用批量推理模式。
- 约束：布尔值。
- 对行为的影响：为 `True` 时使用 `BatchedInferencePipeline`。

### `batch_size`

- 语义：控制批量推理的 batch 大小。
- 约束：应为正整数。
- 对行为的影响：只在 `use_batched_inference=True` 时生效。

## 默认值与必填项

### 默认值策略

- 若未显式提供配置，系统会使用 `TranscriberRuntimeConfig` 的默认值
- `build_transcriber(...)` 会将该配置映射到 `FasterWhisperTranscriber`
- `FasterWhisperTranscriber` 在未提供 config 时，也会回退到自身默认 `FasterWhisperConfig`

### 必填项

- 当前没有绝对必填字段
- 但若启用转写能力，运行环境必须已安装 `faster-whisper` 及其依赖

## 配置来源

- 代码内默认值
- JSON 配置文件

### 优先级约定

1. JSON 配置文件中的 `transcriber`
2. dataclass 默认值

## 校验规则与约束

- `backend` 当前只能为 `faster_whisper`
- `batch_size` 必须为正整数
- `min_silence_duration_ms` 不应为负数
- 若 `enabled=False`，下游不应假定转写器实例存在

## 使用位置

- `build_transcriber(...)` 会消费该配置并实例化具体 transcriber
- canonical workflow 会在字幕缺失且允许自动补全时消费该 transcriber
- 当前 derived workflow 不直接依赖该配置

## 示例

```python
TranscriberRuntimeConfig(
    enabled=True,
    backend="faster_whisper",
    model_size_or_path="small",
    device="cpu",
    compute_type="int8",
    language=None,
    vad_filter=True,
    min_silence_duration_ms=500,
    use_batched_inference=True,
    batch_size=24,
)
```
