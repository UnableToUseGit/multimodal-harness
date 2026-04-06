# 参数参考文档

## 渲染脚本（render_xhs.py）

```bash
python scripts/render_xhs.py <markdown_file> [options]
```

### 参数列表

| 参数 | 简写 | 说明 | 默认值 |
|---|---|---|---|
| `--output-dir` | `-o` | 输出目录 | 当前工作目录 |
| `--width` | `-w` | 图片宽度（px） | `1080` |
| `--height` | | 单页图片高度（px） | `1440` |
| `--dpr` | | 设备像素比（清晰度） | `2` |

### 输入约定

- Markdown 文件开头可包含 YAML frontmatter
- frontmatter 之后先写引导页
- 引导页之后使用一个 `---` 分隔正文主体
- 如果 frontmatter 中包含 `intro_image`，脚本会默认将该图片作为封面图
- 正文主体内部不再手动分页，而是由渲染脚本自动分页

### 封面图来源约定

`intro_image` 应按以下优先级选择：

1. 视频播客中的高质量画面
2. 播客的 thumbnail
3. 与主题相关的外部图片

推荐要求：

- 图片清晰
- 构图稳定
- 与播客主题相关
- 适合做首图

### 输出结果

渲染脚本会输出：

- `intro.png`
- `page_1.png`
- `page_2.png`
- ...

### 常用命令示例

```bash
# 基础用法
python scripts/render_xhs.py article.md

# 指定输出目录
python scripts/render_xhs.py article.md -o ./rendered

# 自定义尺寸
python scripts/render_xhs.py article.md --width 1080 --height 1440 --dpr 2
```

---

## 发布脚本（publish_xhs.py）

```bash
python scripts/publish_xhs.py --title "标题" --desc "描述" --images img1.png img2.png
```

### 参数列表

| 参数 | 简写 | 说明 | 默认值 |
|---|---|---|---|
| `--title` | `-t` | 笔记标题（不超过 20 字） | 必填 |
| `--desc` | `-d` | 笔记描述/正文内容 | `""` |
| `--images` | `-i` | 图片文件路径（可多个） | 必填 |
| `--public` | | 公开发布（默认仅自己可见） | `False` |
| `--post-time` | | 定时发布（格式：`2024-01-01 12:00:00`） | 立即发布 |
| `--api-mode` | | 通过 xhs-api 服务发布 | 本地模式 |
| `--api-url` | | API 服务地址 | `http://localhost:5005` |
| `--dry-run` | | 仅验证，不实际发布 | `False` |

> **注意**：默认以「仅自己可见」发布，确认内容无误后再用 `--public` 公开。

### 常用命令示例

```bash
# 默认（仅自己可见，用于预览确认）
python scripts/publish_xhs.py --title "标题" --desc "描述" --images cover.png card_1.png card_2.png

# 公开发布
python scripts/publish_xhs.py --title "标题" --desc "描述" --images cover.png card_1.png --public

# 定时发布
python scripts/publish_xhs.py --title "标题" --desc "描述" --images *.png --post-time "2024-12-01 10:00:00" --public

# API 模式
python scripts/publish_xhs.py --title "标题" --desc "描述" --images *.png --api-mode

# 仅验证不发布
python scripts/publish_xhs.py --title "标题" --desc "描述" --images *.png --dry-run
```

### 环境变量配置（.env）

```bash
cp env.example.txt .env
```

编辑 `.env`：

```env
# 必需：小红书 Cookie
XHS_COOKIE=your_cookie_string_here

# 可选：API 模式服务地址
XHS_API_URL=http://localhost:5005
```

**Cookie 获取方式**：浏览器登录小红书 → F12 → Network → 任意请求的 Cookie 头，复制完整字符串。

---

## Markdown 文档格式

### YAML 头部元数据

```yaml
---
title: "笔记标题"
source: "播客来源"
intro_image: "./cover.png"  # 必填。用于封面图
---
```

### 分页分隔符

使用一个 `---` 将引导页与正文主体分开：

```markdown
---
title: "工具推荐"
source: "播客来源"
intro_image: "./scover.png"
---

"封面页的文本介绍内容"

---

# 第一个核心观点

这里开始是正文主体。
```
