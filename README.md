[中文](README.md) | [English](docs/README_en.md)

# MM Harness

`MM Harness` 为 Agent 提供更有效且便捷的多模态数据处理方案。
通过 `MM Harness`, Agent 可将原本繁重的多模态数据（如长视频，长音频）转化为易于理解，检索，复用的数据形式。
从而极大扩宽了 Agent 处理多模态数据的能力边界，可轻松完成视频转笔记，会议纪要生成，视频剪辑等任务。


## 当前已实现

- 可处理的视频来源：Youtube, 本地视频文件
- 可处理的音频来源：小宇宙，本地音频文件
- 可处理的视频类型：弱视觉叙事的视频，如视频播客，课程，科普
- 可处理的音频类型：播客，讨论，会议

## 暂未实现

- 更多的视频/音频来源：Bilibili, Apple Podcast ...
- 更多的模态：长文档（PDF）
- 更多的视频类型：电影，比赛，Vlog ...
- 更多的音频类型：音乐
- 附带更多的 SKILL.md: 视频剪辑，笔记生成 ...

## 快速上手

复制这句话给你的 AI Agent（Claude Code、OpenClaw、Cursor 等）：

```
帮我安装 MM Harness：https://raw.githubusercontent.com/UnableToUseGit/multimodal-harness/main/docs/install.md
```

Agent 会自己完成剩下的所有事情。

Agent 安装后通常需要你提供这些环境变量：

```bash
export LLM_API_BASE_URL=...
export LLM_API_KEY=...
export GROQ_API_KEY=...
```

如果 YouTube 需要认证访问，还可能需要：

```bash
export YOUTUBE_COOKIES_FILE=/path/to/cookies.txt
# 或
export YOUTUBE_COOKIES_FROM_BROWSER=chrome
```


## 开箱即用

告诉 Agent 你想做什么：

- "这个播客 (https://www.xiaoyuzhoufm.com/episode/69cbd0d3b977fb2c47c1ff80) 在讲什么？"
- "把我今天的录像 (`/path/your_recording`) 剪辑成一个 10min 的 Vlog。"
- "帮我为这节课（https://www.youtube.com/watch?v=aircAruvnKk），写一个课堂笔记。"

**不需要记命令。** Agent 读了 SKILL.md 之后自己知道该怎么处理。
