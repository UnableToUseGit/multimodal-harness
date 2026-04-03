---
name: mm-harness
description: >
  Build a text-first canonical atlas from supported video, audio, subtitle, or URL inputs.
  Use when the user wants a long-form media asset converted into a structured atlas workspace.
  Current release supports video-absent and video-present + text-led inputs.
triggers:
  - mm-harness
  - canonical atlas
  - youtube url
  - xiaoyuzhou
  - long video parsing
  - subtitle atlas
  - audio atlas
---

# MM Harness

Use `MM Harness` when the user wants to turn long-form media into a canonical atlas workspace.

## When To Use

- user provides a supported URL and wants a canonical atlas
- user provides a local video/audio/subtitle file and wants a canonical atlas
- user wants a structured workspace instead of a plain summary

## Supported Inputs

- standard YouTube video page URL
- Xiaoyuzhou episode URL
- local video file
- local audio file
- local subtitle file

## Current Boundaries

- supported:
  - `video-absent`
  - `video-present + text-led`
- unsupported:
  - `video-present + visual-led`

If planning resolves to a `multimodal` route, do not try to force a degraded result. Report that the current release does not support that route.

## Commands

Check installation:

```bash
mm-harness info
mm-harness doctor
```

Create from URL:

```bash
mm-harness create \
  --url "https://www.youtube.com/watch?v=..." \
  --output-dir ./local/outputs
```

Create from local video:

```bash
mm-harness create \
  --video-file ./local/inputs/example.mp4 \
  --output-dir ./local/outputs
```

Create from local audio:

```bash
mm-harness create \
  --audio-file ./local/inputs/example.wav \
  --output-dir ./local/outputs
```

Create from local subtitle:

```bash
mm-harness create \
  --subtitle-file ./local/inputs/example.srt \
  --output-dir ./local/outputs
```

## Required Environment

```bash
export VIDEO_ATLAS_API_BASE=...
export VIDEO_ATLAS_API_KEY=...
export GROQ_API_KEY=...
```

Optional YouTube cookies:

```bash
export YOUTUBE_COOKIES_FILE=/path/to/cookies.txt
# or
export YOUTUBE_COOKIES_FROM_BROWSER=chrome
```

## Operational Rules

- run `mm-harness doctor` before debugging environment issues
- prefer `--url` for supported remote sources
- prefer local file inputs when the user already has prepared assets
- inspect the generated atlas workspace under the returned `atlas_dir`
- do not assume visual-led video content is supported in this release

## Troubleshooting

If environment setup is broken, read:

- [docs/install.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/install.md)
- [docs/troubleshooting.md](/share/project/minghao/Proj/VideoAFS/VideoEdit/development/docs/troubleshooting.md)
