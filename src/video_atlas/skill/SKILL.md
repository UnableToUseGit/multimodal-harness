---
name: mm-harness
description: >
  Build an LLM-friendly workspace from long-form video or audio, including content from YouTube,
  Xiaoyuzhou, and local files.
  Use MM Harness when the user asks you to work on tasks involving long videos or audio recordings.
  MM Harness converts raw media into a structured workspace so you can understand, search, and
  process it more effectively.
triggers:
  - mm-harness
  - long video
  - long audio
  - youtube url
  - xiaoyuzhou
  - podcast
  - lecture video
  - meeting recording
---

# MM Harness

Use `MM Harness` when the user gives you a long video or audio source and wants you to turn it into a form that is easier to read, search, summarize, and reuse.

## What It Does

MM Harness takes long-form media and converts it into a structured workspace on disk.

After it runs, you get an output directory that is much easier to work with than the original raw media. You can then use that workspace for follow-up tasks such as:

- understanding what the content is about
- writing notes or summaries
- reviewing lectures, podcasts, or meetings
- extracting key sections for later downstream work

MM Harness is a preprocessing and structuring tool. It does not directly finish every downstream task for you.

## When To Use It

Use MM Harness when:

- the user gives you a long YouTube video
- the user gives you a Xiaoyuzhou episode
- the user gives you a local video file
- the user gives you a local audio file
- the user gives you a local subtitle file
- the user wants help with long-form content, not a short clip

Do not use MM Harness when the task is unrelated to long-form media processing.

## What It Supports

Supported inputs:

- YouTube video URLs
- Xiaoyuzhou episode URLs
- local video files
- local audio files
- local subtitle files

Well-supported content types in the current release:

- lectures
- podcasts
- interviews or discussions
- explanatory or commentary-style content

## What It Does Not Support Well

Do not rely on MM Harness for strongly visual content, such as:

- movies
- sports broadcasts
- drama
- Vlogs or content where meaning depends heavily on visuals

If the input mainly depends on visual storytelling rather than spoken language, the current release may fail or produce an unsatisfactory result. In that case, tell the user that this version of MM Harness is intended for speech-led content.

## How To Use It

Check installation first if needed:

```bash
mm-harness info
mm-harness doctor
```

Create from a URL:

```bash
mm-harness create \
  --url "https://www.youtube.com/watch?v=..." \
  --output-dir ./outputs
```

Create from a local video file:

```bash
mm-harness create \
  --video-file ./input/example.mp4 \
  --output-dir ./outputs
```

Create from a local audio file:

```bash
mm-harness create \
  --audio-file ./input/example.wav \
  --output-dir ./outputs
```

Create from a local subtitle file:

```bash
mm-harness create \
  --subtitle-file ./input/example.srt \
  --output-dir ./outputs
```

If the user gives you a specific output requirement, add it with `--structure-request`.

## What You Get After Running It

MM Harness writes a structured output directory to the user-provided `--output-dir`.

Use that output directory as the basis for the next step of work.

The result is not just a plain transcript. It is a structured workspace intended to make the original media easier for you to inspect and process.

## Required Environment

```bash
export LLM_API_BASE_URL=...
export LLM_API_KEY=...
export GROQ_API_KEY=...
```

Optional YouTube cookies:

```bash
export YOUTUBE_COOKIES_FILE=/path/to/cookies.txt
# or
export YOUTUBE_COOKIES_FROM_BROWSER=chrome
```

## Common Failures

If something fails:

- run `mm-harness doctor` first
- if YouTube access fails, the user may need to provide cookies
- if transcription fails, check `GROQ_API_KEY`
- if the content is strongly visual, tell the user the current release may not support it well
- if the environment is missing tools like `ffmpeg`, `yt-dlp`, or `deno`, explain that to the user before continuing
