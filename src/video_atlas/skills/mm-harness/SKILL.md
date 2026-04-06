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

Create from a URL with a readable run name:

```bash
mm-harness create \
  --url "https://www.youtube.com/watch?v=..." \
  --output-dir ./outputs \
  --name naval-ai-podcast
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

Useful create parameters:

- `--output-dir`
  - the parent directory where MM Harness will write the result
  - MM Harness will create one subdirectory inside it for this run
- `--name`
  - optional
  - use this when you want a stable, human-readable result directory name
  - if omitted, MM Harness will generate a readable name automatically
- `--structure-request`
  - optional
  - use this when the user has a specific goal for how the output should be organized
  - examples:
    - "keep the structure coarse"
    - "organize it as lecture notes"
    - "make the structure suitable for writing a Xiaohongshu post"
  - this does not replace the source content; it only guides how MM Harness structures the output

## What You Get After Running It

MM Harness writes one structured result directory under the user-provided `--output-dir`.

The result is not just a plain transcript. It is a structured workspace intended to make the original media easier to inspect and process.

Typical contents include:

- `input/`
  - source assets and acquisition metadata
  - may include the original video or audio file, prepared subtitles, thumbnails, `SOURCE_INFO.json`, and `SOURCE_METADATA.json`
- `units/`
  - the smallest content units extracted from the source
  - useful when you need a fine-grained breakdown
- `segments/`
  - higher-level grouped results built from one or more units
  - usually the best place to start reading
- `README.md`
  - the overview page for the whole workspace
- `SUBTITLES.md`
  - the prepared full subtitles when subtitle export is enabled

## How To Read The Output

Recommended reading order:

1. Start with `README.md`
   - it explains what this run contains
2. Then go to `segments/`
   - this is the quickest way to understand the content at a chapter-like level
3. Then go to `units/` if you need more detail
   - this is where you inspect finer-grained evidence and local content spans
4. Use `input/` when you need raw assets
   - source files
   - metadata
   - subtitles
   - thumbnails for cover selection or creative tasks

## What To Do Next

After MM Harness finishes:

- for summaries, notes, and quick understanding:
  - start from `segments/`
- for content creation tasks:
  - use `segments/` for overall structure
  - use `units/` for detail, quotes, and supporting evidence
- for source validation:
  - check `input/SOURCE_INFO.json` and `input/SOURCE_METADATA.json`

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
