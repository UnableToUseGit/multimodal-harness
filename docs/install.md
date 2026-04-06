# MM Harness Installation Guide

## For AI Agents

### Goal

Install `MM Harness`, verify that the environment is runnable, and leave the user with a working CLI.

Current repository:

```text
https://github.com/UnableToUseGit/multimodal-harness.git
```

Current install artifact:

```text
https://github.com/UnableToUseGit/multimodal-harness/archive/refs/heads/main.zip
```

Current CLI command:

```text
mm-harness
```

### Boundaries

- Do not run `sudo` unless the user explicitly approves.
- Do not modify files outside the user-approved environment.
- Do not create unrelated files in the current workspace.
- If something requires elevated permissions, **tell the user** what's needed and let them decide

### Directory Rules

- package installation is handled by `pipx`
- install `SKILL.md` into the current agent's own skill directory

### Step 1: Install the package

Install with `pipx`:

```bash
pipx install https://github.com/UnableToUseGit/multimodal-harness/archive/refs/heads/main.zip
pipx ensurepath
mm-harness install
```

If `mm-harness` is still not found after `pipx ensurepath`, ask the user to restart their shell.

Common fallback location:

```text
~/.local/bin/mm-harness
```

### Step 2: Check runtime dependencies

Run:

```bash
mm-harness doctor
```

Expected required items:

- `ffmpeg`
- `yt-dlp`
- `deno`
- `LLM_API_BASE_URL`
- `LLM_API_KEY`
- `GROQ_API_KEY`

Explain these items to the user in human terms before you mention environment variable names:

- `ffmpeg`
  Required for audio/video preprocessing and transcription preparation.
- `yt-dlp`
  Required for YouTube video and subtitle acquisition.
- `deno`
  Required for more reliable YouTube extraction in some environments.
- an LLM service
  MM Harness needs access to a remote OpenAI-compatible LLM service for planning, parsing, captioning, and structure composition.
  The user must provide:
  - the service base URL → `LLM_API_BASE_URL`
  - the service API key → `LLM_API_KEY`
- a Groq transcription key
  MM Harness uses Groq for speech-to-text transcription.
  The user must provide:
  - a Groq API key → `GROQ_API_KEY`

Optional items:

- `YOUTUBE_COOKIES_FILE`
- `YOUTUBE_COOKIES_FROM_BROWSER`

These optional YouTube cookie variables are only needed when YouTube requires authenticated access.
Explain them to the user as:

- a YouTube cookies file exported from a logged-in browser → `YOUTUBE_COOKIES_FILE`
- or the name of a browser that is already logged into YouTube → `YOUTUBE_COOKIES_FROM_BROWSER`

What you may do directly as the agent:

- install the package itself with `pipx`
- run `mm-harness doctor`
- read the doctor output
- install missing Python-side dependencies when no elevated permissions are required

What requires human user input:

- the base URL of their OpenAI-compatible LLM service
- the API key for that LLM service
- a Groq API key for transcription
- optionally, a YouTube cookies file or browser name for authenticated YouTube access

You must ask the human user for these values. Do not invent them.
When asking, mention both the plain-language meaning and the matching environment variable name.

What requires human permission first:

- installing system-level dependencies such as `ffmpeg`
- installing runtimes such as `deno`
- modifying shell startup files or persistent environment configuration
- any action that needs elevated permissions on the user's device

Decision rule:

- if `doctor` reports a missing Python package dependency, you may try to install it directly
- if `doctor` reports a missing system dependency, ask the user for permission before installing it
- if `doctor` reports a missing API key or YouTube cookie setting, ask the user to provide it
- if `doctor` shows only optional warnings, you may continue unless the current task explicitly needs that capability

How to ask the human user for these values:

- For the LLM service:
  ask the user which OpenAI-compatible LLM service they want to use, then ask for:
  - the service base URL → `LLM_API_BASE_URL`
  - the API key for that service → `LLM_API_KEY`
- For Groq transcription:
  ask the user to create a Groq API key at `https://console.groq.com`, then send you the key value → `GROQ_API_KEY`
- For YouTube authenticated access:
  if needed, ask the user for either:
  - an exported `cookies.txt` file path → `YOUTUBE_COOKIES_FILE`
  - or the name of a browser already logged into YouTube, such as `chrome`, `chromium`, `edge`, or `firefox` → `YOUTUBE_COOKIES_FROM_BROWSER`

Suggested message to the user:

```text
MM Harness is installed, but it still needs two services from you before it can run:

1. An LLM service
   I need:
   - the base URL of your OpenAI-compatible LLM service (LLM_API_BASE_URL)
   - the API key for that service (LLM_API_KEY)

2. A Groq API key for transcription
   I need:
   - your Groq API key (GROQ_API_KEY)

Optional, only if YouTube requires authenticated access:
- YOUTUBE_COOKIES_FILE: path to an exported cookies.txt file
or
- YOUTUBE_COOKIES_FROM_BROWSER: the browser name to read cookies from
```

### Step 3: Verify CLI availability

Run:

```bash
mm-harness info
mm-harness doctor
mm-harness create --help
```
