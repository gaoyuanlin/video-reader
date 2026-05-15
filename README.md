# 🎬 vreader — Smart Video Content Extraction
> 智能视频内容提取：场景检测抽帧 + 语音转文字，一键读懂视频。

[English](#english) | [中文](#中文)

---
## English

**vreader** extracts the full content of any video: smart frame capture (scene-change detection, skipping duplicate frames) + speech-to-text transcription. Outputs a timestamped summary you can feed to an LLM for analysis.

### ✨ Features

- **🎯 Scene-change detection** — only captures frames when the visual content changes >30%, automatically skipping static/repeated screens
- **⏱️ Uniform interval fallback** — switches to fixed-interval sampling when scene detection yields too few frames
- **🎤 Speech-to-text** — extracts audio and transcribes with [whisper-cli](https://github.com/ggerganov/whisper.cpp) (supports 100+ languages)
- **📦 pip-installable** — `pip install vreader`
- **⚡ Fast & local** — runs entirely offline on your machine, no cloud API calls

### 📋 Requirements

| Tool | Install |
|------|---------|
| Python 3.9+ | — |
| ffmpeg | `brew install ffmpeg` (macOS) / `apt install ffmpeg` (Linux) |
| whisper-cli | `brew install whisper-cpp` |
| whisper model | `whisper-cli download base` |

### 🚀 Install

```bash
pip install vreader
```

Or from source:

```bash
git clone https://github.com/gaoyuanlin/video-reader.git
cd video-reader
pip install -e .
```

### 📖 Usage

```bash
# Basic: scene detection + Chinese transcription (default)
vreader lecture.mp4

# English video with medium whisper model
vreader talk.mp4 -l en -m medium

# Uniform interval (every 5 seconds)
vreader video.mp4 --mode interval

# Process only a segment
vreader video.mp4 --start 60 --end 300

# Skip audio transcription
vreader video.mp4 --no-audio

# Custom interval
vreader video.mp4 --mode interval --interval 10
```

### 📤 Output

```
/tmp/vreader_1712345678/
├── frame_0001.jpg    # Extracted frames
├── frame_0002.jpg
├── ...
├── timestamps.txt    # Frame timestamps
├── audio.wav         # Extracted audio (16kHz mono)
├── transcript.txt    # Speech-to-text transcript
└── summary.json      # Processing summary
```

### 🤖 LLM Integration

After extraction, pipe the output to any vision-capable LLM for analysis:

```python
import os, glob
frames = sorted(glob.glob("/tmp/vreader_*/frame_*.jpg"))
transcript = open("/tmp/vreader_*/transcript.txt").read()
# Send frames + transcript to your LLM...
```

### 🔧 Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| Scene threshold | `gt(scene,0.3)` | 0.2 = sensitive, 0.4 = only large changes |
| Interval | 5s | Seconds between frames in interval mode |
| Whisper model | `base` | tiny / base / small / medium / large |
| Language | `zh` | Audio language code |

### 📄 License

MIT © 2026 [Gao Yuanlin](https://github.com/gaoyuanlin)

---
## 中文

**vreader** 从视频中提取完整内容：智能抽帧（场景检测，自动跳过重复画面）+ 语音转文字，输出带时间轴的结构化数据，方便喂给 LLM 分析。

### ✨ 特性

- **🎯 场景检测抽帧** — 画面变化超过 30% 才截取，自动跳过静态/重复画面
- **⏱️ 等间隔兜底** — 场景检测帧数太少时自动切换到固定间隔采样
- **🎤 语音转文字** — 提取音频，用 [whisper-cli](https://github.com/ggerganov/whisper.cpp) 转录（支持 100+ 语言）
- **📦 pip 安装** — `pip install vreader`
- **⚡ 本地离线** — 全程在你自己的机器上运行，无需云端 API

### 📋 环境要求

| 工具 | 安装方式 |
|------|----------|
| Python 3.9+ | — |
| ffmpeg | `brew install ffmpeg` (macOS) / `apt install ffmpeg` (Linux) |
| whisper-cli | `brew install whisper-cpp` |
| whisper 模型 | `whisper-cli download base` |

### 🚀 安装

```bash
pip install vreader
```

或从源码安装：

```bash
git clone https://github.com/gaoyuanlin/video-reader.git
cd video-reader
pip install -e .
```

### 📖 使用

```bash
# 基本用法：场景检测 + 中文转录（默认）
vreader lecture.mp4

# 英文视频 + medium 模型
vreader talk.mp4 -l en -m medium

# 等间隔抽帧（每 5 秒）
vreader video.mp4 --mode interval

# 只处理片段
vreader video.mp4 --start 60 --end 300

# 只抽帧，不转录
vreader video.mp4 --no-audio

# 自定义间隔
vreader video.mp4 --mode interval --interval 10
```

### 📤 输出结构

```
/tmp/vreader_1712345678/
├── frame_0001.jpg    # 抽帧图片
├── frame_0002.jpg
├── ...
├── timestamps.txt    # 帧时间戳
├── audio.wav         # 提取的音频 (16kHz mono)
├── transcript.txt    # 语音转录文本
└── summary.json      # 处理摘要
```

### 🤖 LLM 集成

提取完成后，将输出喂给任意支持视觉的 LLM：

```python
import os, glob
frames = sorted(glob.glob("/tmp/vreader_*/frame_*.jpg"))
transcript = open("/tmp/vreader_*/transcript.txt").read()
# 把帧 + 转录文本发给 LLM 分析...
```

### 🔧 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 场景检测阈值 | `gt(scene,0.3)` | 0.2 = 灵敏，0.4 = 仅大变 |
| 等间隔 | 5 秒 | 间隔模式下的帧间隔 |
| Whisper 模型 | `base` | tiny / base / small / medium / large |
| 语言 | `zh` | 音频语言代码 |

### 📄 许可证

MIT © 2026 [Gao Yuanlin](https://github.com/gaoyuanlin)
