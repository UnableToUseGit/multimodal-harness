# Multimodal Messages Module

## Purpose

`src/video_atlas/multimodal/messages.py` centralizes multimodal message construction for model calls that need video content. It sits between prompt templates and generator execution.

This module is responsible for building model input payloads. It does not send requests to the model and it does not parse model responses.

## Why This Module Exists

Canonical and derived atlas pipelines both need to convert video content into multimodal messages that a model can read. Keeping this logic inside a single agent module would make it hard to reuse and easy to misalign across pipelines.

The module is intentionally separate from `Generator` because:

- `Generator` should focus on transport and model invocation
- multimodal message construction is orchestration-side payload building
- video sampling and frame encoding are upstream of generation, not part of the low-level client

## Public Functions

### `build_text_messages(system_prompt, user_prompt)`

**Purpose**

Builds a plain text two-message chat payload.

**Inputs**

- `system_prompt: str`
- `user_prompt: str`

**Output**

- `list[dict]`
- shape:
  - system message
  - user message

### `build_video_messages(system_prompt, user_prompt, frame_base64_list, timestamps)`

**Purpose**

Builds a multimodal chat payload from already-prepared video frames.

**Inputs**

- `system_prompt: str`
- `user_prompt: str`
- `frame_base64_list: list[str]`
- `timestamps: list[float]`

**Output**

- `list[dict]`
- user content contains interleaved:
  - image items
  - timestamp text items
  - final task/user text prompt

### `build_video_messages_from_path(system_prompt, user_prompt, video_path, start_time, end_time, video_sampling=None)`

**Purpose**

Builds a multimodal chat payload directly from a video path and time range.

**Inputs**

- `system_prompt: str`
- `user_prompt: str`
- `video_path: str`
- `start_time: float`
- `end_time: float`
- `video_sampling: FrameSamplingProfile | None`

**Output**

- `list[dict]`

**Internal Behavior**

- computes frame indices for the requested range
- prepares base64-encoded frame inputs
- delegates final payload assembly to `build_video_messages(...)`

## Boundaries

This module does:

- sample frames from a requested video range
- prepare multimodal message payloads
- return message objects ready for `generator.generate_single(...)`

This module does not:

- choose prompts
- choose which generator to call
- send requests to the model
- parse model outputs
- make agent-level business decisions

## Current Usage

- canonical atlas message generation uses this module as a shared backend
- derived atlas can reuse the same builder once its derivation stages move to multimodal inputs
