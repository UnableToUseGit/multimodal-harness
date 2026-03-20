# Core Beliefs

## Keep the surface area small

This repo exists to support the VideoAtlas pipeline only. New code should strengthen that path instead of diluting it with unrelated product layers.

## Favor explicit contracts

Prompts, schemas, and workspace outputs are part of the system contract. When one changes, update the others.

## Separate orchestration from integration

`CanonicalVideoAtlasAgent` should coordinate work, not absorb provider-specific logic or low-level video utilities.

## Optimize for inspectability

Generated artifacts such as `README.md`, `SUBTITLES.md`, segment folders, and `EXECUTION_PLAN.json` should stay easy to inspect by humans.
