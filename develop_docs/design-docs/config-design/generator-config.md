# Generator 配置设计

## 文档目标

本文档说明当前 `MM Harness` 中 generator 配置的正式结构。

## 配置对象

- 名称：`ModelRuntimeConfig`
- 模块：`src/video_atlas/config/models.py`

## 当前字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `provider` | `str` | 当前仅支持 `openai_compatible` |
| `model_name` | `str` | 模型名称 |
| `temperature` | `float` | 采样温度 |
| `top_p` | `float` | nucleus sampling |
| `max_tokens` | `int` | 最大生成 token 数 |
| `extra_body` | `dict[str, Any]` | 附加请求体参数 |

## 已废弃设计

当前 release 已不再维护：

- `connection=default/local/remote`
- 多套 API_BASE / API_KEY 路由

现在所有 generator 都统一使用：

- `LLM_API_BASE_URL`
- `LLM_API_KEY`

## 当前环境依赖

若 `provider="openai_compatible"`，运行时必须提供：

- `LLM_API_BASE_URL`
- `LLM_API_KEY`

## 使用位置

当前 canonical pipeline 中这些能力都由 `ModelRuntimeConfig` 驱动：

- planner
- text_segmentor
- structure_composer
- captioner

## 当前设计原则

- 用户面不直接暴露复杂 generator 配置
- generator 配置主要由内部默认配置文件维护
- release 面只保留一套远端 LLM 连接语义
