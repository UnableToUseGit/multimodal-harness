[English](README_en.md) | [中文](../README.md)

# MM Harness

`MM Harness` gives AI agents a more effective and lightweight way to process multimodal data.
With `MM Harness`, agents can turn heavy inputs such as long videos and long audio recordings into data that is easier to understand, retrieve, and reuse.
This significantly expands what agents can do with multimodal content, including video-to-notes, meeting summaries, and video editing workflows.

## What Already Works

- Supported video sources: YouTube, local video files
- Supported audio sources: Xiaoyuzhou, local audio files
- Supported video types: weakly visual narratives such as video podcasts, lectures, and explanatory content
- Supported audio types: podcasts, discussions, meetings

## Not Yet Implemented

- More video/audio sources: Bilibili, Apple Podcasts, ...
- More modalities: long documents such as PDFs
- More video types: movies, sports, vlogs, ...
- More audio types: music
- More built-in `SKILL.md` workflows: video editing, note generation, ...

## Quick Start

Copy this to your AI agent (`Claude Code`, `OpenClaw`, `Cursor`, etc.):

```text
Help me install MM Harness:
```

The agent can handle the rest.

## Out of the Box

Tell your agent what you want:

- "What is this podcast about? (https://www.xiaoyuzhoufm.com/episode/69cbd0d3b977fb2c47c1ff80)"
- "Turn my recording (`/path/your_recording`) into a 10-minute vlog."
- "Write lecture notes for this class (https://www.youtube.com/watch?v=aircAruvnKk)."

**You do not need to remember commands.** Once the agent has read `SKILL.md`, it should know how to handle these requests.
