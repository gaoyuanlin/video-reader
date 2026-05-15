"""vreader — Smart video content extraction with scene detection + speech-to-text.

一键视频内容提取：场景检测抽帧（自动跳过重复画面）+ 语音转文字。
"""

from __future__ import annotations

__version__ = "1.1.0"
__author__ = "Gao Yuanlin"

from vreader.extractor import extract_interval_frames, extract_scene_frames, get_duration
from vreader.transcriber import extract_audio, transcribe

__all__ = [
    "get_duration",
    "extract_scene_frames",
    "extract_interval_frames",
    "extract_audio",
    "transcribe",
]
