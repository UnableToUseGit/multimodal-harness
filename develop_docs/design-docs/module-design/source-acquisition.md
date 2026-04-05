# Source Acquisition 模块设计

## 文档目标

本文档描述当前 `MM Harness` 的 source acquisition 设计。该模块负责把外部 URL 输入标准化为本地输入资产，供 application layer 和 workflow 消费。

## 模块位置

- `src/video_atlas/source_acquisition/acquire.py`
- `src/video_atlas/source_acquisition/youtube.py`
- `src/video_atlas/source_acquisition/xiaoyuzhou.py`

## 模块职责

source acquisition 负责：

- 识别受支持的 URL 来源
- 下载或提取媒体资产
- 生成 `SourceInfoRecord`
- 生成归一化 `SourceMetadata`
- 将 acquisition 产物写入 `atlas_dir/input/`

它不负责：

- canonical workflow planning
- 字幕缺失时的转录
- workspace 结构组合

## 当前支持的来源

### YouTube

支持：

- 标准 `youtube.com/watch?v=...` 视频页面

不支持：

- `youtu.be`
- playlist
- channel page

YouTube acquisition 当前流程：

1. 先 probe metadata
2. 根据时长阈值决定是否下载视频
3. 尽量复用 YouTube 字幕
4. 写出：
   - 视频文件（若下载）
   - 字幕文件（若获取到）
   - `SOURCE_INFO.json`
   - `SOURCE_METADATA.json`

默认阈值为：

- `max_youtube_video_duration_sec = 1500`

即约 25 分钟。

### Xiaoyuzhou

支持：

- 标准 episode URL

当前流程：

1. 拉取页面 HTML
2. 解析页面中的 episode 数据
3. 提取音频直链和基础 metadata
4. 下载音频
5. 写出：
   - 音频文件
   - `SOURCE_INFO.json`
   - `SOURCE_METADATA.json`

## URL 检测与分发

`acquire.py` 中的 `detect_source_from_url(...)` 负责：

- 校验 URL 基本合法性
- 判断是 YouTube 还是 Xiaoyuzhou
- 对不支持的 URL 抛出：
  - `InvalidSourceUrlError`
  - `UnsupportedSourceError`

## 输出对象

统一输出为：

- `SourceAcquisitionResult`

其核心字段为：

- `source_info`
- `source_metadata`
- `video_path`
- `audio_path`
- `subtitles_path`

application layer 再基于该结果构造 `CanonicalCreateRequest`。

## 当前稳定设计点

- source acquisition 只负责把 URL 变成本地资产
- 所有产物写入 `atlas_dir/input/`
- 归一化 metadata 单独保留
- 字幕优先复用来源本身已有字幕
- 字幕缺失时由 workflow 再决定是否转录
