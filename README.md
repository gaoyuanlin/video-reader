# vreader — 智能视频内容提取

🎬 场景检测抽帧 + 去重 + 语音转文字，输出带时间轴的结构化摘要。

自动跳过相似帧，优先提取画面变化明显的关鍵帧，配合 Whisper 语音转录，快速把视频变成「图文+时间轴」的阅读笔记。

---

## 特性

- **场景检测** — 基于帧间差异自动识别画面切换，只保留关键帧
- **均间隔采样** — 每 N 秒取一帧，适合连续讲座、监控视频
- **语音转文字** — 调用 Whisper CLI 生成带时间轴的转录文本
- **智能降级** — 场景帧不足时自动回退到均间隔采样
- **时间范围裁剪** — 指定起止时间，只处理视频片段
- **零 Python 依赖** — 只依赖 ffmpeg + whisper-cli 两个系统工具

---

## 安装

### 系统依赖

```bash
# macOS
brew install ffmpeg      # 帧提取 + 音频提取
brew install whisper-cpp  # 语音转录（推荐，速度更快）
# 或者
pip install faster-whisper  # 备选方案
```

```bash
# Linux (Ubuntu/Debian)
sudo apt install ffmpeg
# whisper: 参考 https://github.com/ggerganov/whisper.cpp
```

### 安装 vreader

```bash
pip install git+https://github.com/gaoyuanlin/video-reader.git
```

或者本地开发：

```bash
git clone https://github.com/gaoyuanlin/video-reader.git
cd video-reader
pip install -e ".[dev]"
```

---

## 使用方法

### 基础用法

```bash
# 场景检测模式（默认）
vreader lecture.mp4

# 均间隔采样（每 5 秒一帧）
vreader video.mp4 --mode interval

# 切片处理（只处理 1 分到 5 分）
vreader video.mp4 --start 60 --end 300

# 指定语言 + 模型大小
vreader talk.mp4 -l en -m small
```

### 高级选项

```bash
# 降低场景检测敏感度（帧更少）
vreader video.mp4 --threshold 0.5

# 提高敏感度（帧更多）
vreader video.mp4 --threshold 0.15

# 跳过语音转录，只提取帧
vreader video.mp4 --no-audio

# 自定义输出目录
vreader video.mp4 -o ./my-output

# 静默模式
vreader video.mp4 -q
```

### 完整参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `video` | 视频文件路径 | 必填 |
| `--mode` | 抽帧模式：scene / interval | scene |
| `--threshold` | 场景检测灵敏度 0–1 | 0.3 |
| `--interval` | 均间隔采样秒数 | 5 |
| `--min-frames` | 最少场景帧数，不足则降级 | 3 |
| `--start` | 起始时间（秒） | 0 |
| `--end` | 结束时间（秒） | 视频结尾 |
| `--no-audio` | 跳过音频提取和转录 | — |
| `-l, --lang` | 音频语言代码 | zh |
| `-m, --whisper-model` | 模型：tiny/base/small/medium/large | base |
| `-o, --output-dir` | 输出目录 | /tmp/vreader_<时间戳> |
| `-q, --quiet` | 静默模式 | — |

---

## 输出结构

```
/tmp/vreader_1712345678/
├── frame_0001.jpg     # 关键帧截图
├── frame_0042.jpg
├── audio.wav          # 提取的音频（可选）
├── transcript.txt     # 转录文本（可选）
└── summary.json       # 结构化摘要
```

**summary.json 示例：**

```json
{
  "video": "lecture.mp4",
  "duration_seconds": 1847.5,
  "extraction_mode": "scene",
  "frame_count": 23,
  "has_audio": true,
  "has_transcript": true,
  "transcript_path": "/tmp/vreader_xxx/transcript.txt",
  "settings": {
    "start": 0,
    "end": 1800,
    "threshold": 0.3,
    "lang": "zh",
    "whisper_model": "base"
  }
}
```

---

## 如何工作

```
视频文件 → ffmpeg 场景检测 → 去重 → 关键帧
         → ffmpeg 提取音频 → whisper 转录 → 时间轴文本
         → 合并输出 summary.json
```

- **场景检测**：对比相邻帧的画面差异，差异超过阈值标记为新场景
- **去重**：相邻场景帧相似度过高时自动跳过
- **转录**：提取音频 → 调用 whisper CLI 生成带时间戳的转录文本

---

## 开发

```bash
# 运行测试
pytest

# 带覆盖率
pytest --cov=src/vreader --cov-report=html
```

---

## 许可

MIT © [Gao Yuanlin](https://github.com/gaoyuanlin)
