# LLM Response Parsing Module

## Purpose

`src/video_atlas/parsing/llm_responses.py` centralizes tolerant parsing for structured model outputs.

It is responsible for taking raw model text and extracting JSON-like payloads that the pipeline expects to be objects or arrays.

## Why This Module Exists

Canonical and derived atlas pipelines both rely on structured LLM outputs. Keeping JSON extraction logic under `agents/canonical_atlas/` would incorrectly imply that the behavior is canonical-specific.

This module is separate from `Generator` because:

- `Generator` is responsible for request transport
- response parsing is a post-generation cleanup step
- parsing policy should be reusable across agents and workflows

## Public Functions

### `strip_think_blocks(text)`

**Purpose**

Removes `<think>...</think>` wrapper content from model outputs before downstream parsing.

**Input**

- `text: str | None`

**Output**

- cleaned `str`

### `extract_json_payload(text)`

**Purpose**

Finds the most likely JSON payload inside a model output string.

**Input**

- `text: str | None`

**Output**

- extracted `str`

**Behavior**

- strips think blocks
- prefers fenced ```json blocks
- otherwise extracts the outermost object or array when present
- falls back to the cleaned text when no obvious wrapper exists

### `parse_json_response(generated_text)`

**Purpose**

Parses the extracted JSON payload into `dict | list`.

**Input**

- `generated_text: str | None`

**Output**

- parsed `dict | list`
- returns `{}` on failure

**Behavior**

- attempts `json.loads(...)`
- optionally falls back to `json_repair.loads(...)` when available

## Current Usage

- canonical atlas response parsing compatibility layer
- derived atlas response parsing directly from the agent
