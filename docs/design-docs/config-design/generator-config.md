# Generator 配置设计

## 文档目标

本文档用于说明 `Generator` 相关配置的结构、字段定义、默认值、来源和约束。本文档面向开发者与维护者，目标是帮助读者理解 generator 配置控制什么、应如何提供，以及它如何影响模型调用行为。

## 配置对象概览

- 名称：`ModelRuntimeConfig`
- 作用：描述单个 generator 实例的运行时配置
- 实现形式：`dataclass`
- 所属模块：`src/video_atlas/config/models.py`

## 配置项定义

| 配置项 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `provider` | `str` | 否 | `"openai_compatible"` | generator 提供方 |
| `model_name` | `str` | 是 | `""` | 模型名称 |
| `connection` | `str` | 否 | `"default"` | 选择使用哪套 API 连接配置 |
| `temperature` | `float` | 否 | `0.0` | 采样温度 |
| `top_p` | `float` | 否 | `1.0` | nucleus sampling 参数 |
| `max_tokens` | `int` | 否 | `1600` | 最大生成 token 数 |
| `extra_body` | `dict[str, Any]` | 否 | `{}` | 附加到底层请求体的扩展字段 |

## 配置项说明

### `provider`

- 语义：标识 generator 后端类型。
- 约束：当前仅支持 `openai_compatible`。
- 对行为的影响：决定 `build_generator(...)` 选择哪一种具体实现。

### `model_name`

- 语义：底层模型服务使用的模型名称。
- 约束：不能为空。
- 对行为的影响：直接决定请求发送到哪个模型。

### `connection`

- 语义：标识当前 generator 应使用哪套环境连接配置。
- 约束：当前支持 `default`、`local`、`remote`。
- 对行为的影响：`OpenAICompatibleGenerator` 会据此从环境变量中选择对应的 `API_BASE` 与 `API_KEY`。

### `temperature`

- 语义：控制生成随机性。
- 约束：应为非负数。
- 对行为的影响：值越高，生成结果通常越发散。

### `top_p`

- 语义：控制 nucleus sampling 的概率截断范围。
- 约束：通常应在 `0.0` 到 `1.0` 之间。
- 对行为的影响：影响生成分布裁剪方式。

### `max_tokens`

- 语义：控制单次生成的最大 token 数。
- 约束：应为正整数。
- 对行为的影响：直接影响响应长度上限。

### `extra_body`

- 语义：保存底层提供方专属的请求扩展字段。
- 约束：应为可 JSON 序列化的字典。
- 对行为的影响：允许调用方透传特定服务扩展参数。

## 默认值与必填项

### 默认值策略

- `provider` 默认使用 `openai_compatible`
- `temperature` 默认值为 `0.0`
- `connection` 默认值为 `default`
- `top_p` 默认值为 `1.0`
- `max_tokens` 默认值为 `1600`
- `extra_body` 默认值为空字典

### 必填项

- `model_name` 必须显式提供
- 对 `OpenAICompatibleGenerator` 而言，运行环境还必须提供：
  - `VIDEO_ATLAS_API_BASE` / `VIDEO_ATLAS_API_KEY`
  - 或按 `connection` 提供：
    - `LOCAL_API_BASE` / `LOCAL_API_KEY`
    - `REMOTE_API_BASE` / `REMOTE_API_KEY`

## 配置来源

- 代码内默认值
- JSON 配置文件
- 环境变量

### 优先级约定

1. 运行环境中的 API 配置
2. JSON 配置文件中的 `ModelRuntimeConfig`
3. dataclass 默认值

## 校验规则与约束

- `provider` 当前只能为 `openai_compatible`
- `connection` 当前只能为 `default`、`local` 或 `remote`
- `model_name` 必须是非空字符串
- `max_tokens` 必须为正整数
- `extra_body` 应能够被安全合并到最终请求体中

## 使用位置

- `build_generator(...)` 会消费该配置并实例化具体 generator
- canonical workflow 与 derived workflow 都会消费由该配置构造出的 generator 实例
- 配置文件中的 `planner`、`segmentor`、`text_segmentor`、`multimodal_segmentor`、`structure_composer`、`captioner` 均使用这一配置结构

## 示例

```python
ModelRuntimeConfig(
    provider="openai_compatible",
    model_name="Qwen/Qwen3.5-122B-A10B",
    connection="remote",
    temperature=0.6,
    top_p=1.0,
    max_tokens=4800,
    extra_body={"chat_template_kwargs": {"enable_thinking": True}},
)
```
