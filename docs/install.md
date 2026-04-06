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

What these items mean:

- `ffmpeg`
  Required for audio/video preprocessing and transcription preparation.
- `yt-dlp`
  Required for YouTube video and subtitle acquisition.
- `deno`
  Required for more reliable YouTube extraction in some environments.
- `LLM_API_BASE_URL`
  The base URL of the remote OpenAI-compatible LLM service used by planning, parsing, captioning, and structure composition.
- `LLM_API_KEY`
  The API key for that remote LLM service.
- `GROQ_API_KEY`
  The API key for Groq speech-to-text transcription.

Optional items:

- `YOUTUBE_COOKIES_FILE`
- `YOUTUBE_COOKIES_FROM_BROWSER`

These optional YouTube cookie variables are only needed when YouTube requires authenticated access.

What you may do directly as the agent:

- install the package itself with `pipx`
- run `mm-harness doctor`
- read the doctor output
- install missing Python-side dependencies when no elevated permissions are required

What requires human user input:

- `LLM_API_BASE_URL`
- `LLM_API_KEY`
- `GROQ_API_KEY`
- `YOUTUBE_COOKIES_FILE`
- `YOUTUBE_COOKIES_FROM_BROWSER`

You must ask the human user for these values. Do not invent them.

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

- For `LLM_API_BASE_URL` and `LLM_API_KEY`:
  ask the user which OpenAI-compatible LLM service they want to use, and ask them to provide the service base URL and API key.
- For `GROQ_API_KEY`:
  ask the user to create a Groq API key at `https://console.groq.com`, then send you the key value.
- For `YOUTUBE_COOKIES_FILE`:
  ask the user to export a `cookies.txt` file from a browser already logged into YouTube, then give you the local file path.
- For `YOUTUBE_COOKIES_FROM_BROWSER`:
  ask the user which browser is already logged into YouTube, for example `chrome`, `chromium`, `edge`, or `firefox`.

Suggested message to the user:

```text
I need these values from you before MM Harness can run:
1. LLM_API_BASE_URL: the base URL of your OpenAI-compatible LLM service
2. LLM_API_KEY: the API key for that LLM service
3. GROQ_API_KEY: a Groq API key for transcription

Optional, only if YouTube requires authenticated access:
4. YOUTUBE_COOKIES_FILE: path to an exported cookies.txt file
or
5. YOUTUBE_COOKIES_FROM_BROWSER: the browser name to read cookies from
```

### Step 3: Verify CLI availability

Run:

```bash
mm-harness info
mm-harness doctor
mm-harness create --help
```
