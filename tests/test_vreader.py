"""Tests for vreader.

Run with:  pytest tests/
"""

from __future__ import annotations

import os
import subprocess
import tempfile

import pytest

from vreader.extractor import get_duration, extract_interval_frames
from vreader.utils import run, check_tool


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture(scope="session")
def tiny_video(tmp_path_factory) -> str:
    """Create a 2-second silent test video with ffmpeg."""
    tmpdir = tmp_path_factory.mktemp("video")
    video = str(tmpdir / "test.mp4")
    result = subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=duration=2:size=320x240:rate=10",
            "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono",
            "-t", "2",
            video,
        ],
        capture_output=True,
    )
    if result.returncode != 0:
        pytest.skip("ffmpeg not available or video creation failed")
    return video


# ──────────────────────────────────────────────
# utils
# ──────────────────────────────────────────────

class TestRun:
    def test_successful_command(self):
        out, code = run("echo hello")
        assert code == 0
        assert out == "hello"

    def test_failed_command(self):
        _, code = run("false", silent=True)
        assert code != 0

    def test_nonexistent_command(self):
        _, code = run("__nonexistent_cmd__", silent=True)
        assert code != 0


class TestCheckTool:
    def test_existing_tool(self):
        assert check_tool("echo") is True

    def test_missing_tool(self):
        assert check_tool("__no_such_tool_xyz__") is False


# ──────────────────────────────────────────────
# get_duration
# ──────────────────────────────────────────────

class TestGetDuration:
    def test_nonexistent_returns_zero(self):
        assert get_duration("/nonexistent/video.mp4") == 0.0

    def test_real_video(self, tiny_video):
        dur = get_duration(tiny_video)
        assert 1.5 < dur < 3.0, f"Expected ~2s, got {dur}"


# ──────────────────────────────────────────────
# extract_interval_frames
# ──────────────────────────────────────────────

class TestExtractIntervalFrames:
    def test_basic_extraction(self, tiny_video, tmp_path):
        count = extract_interval_frames(tiny_video, str(tmp_path), interval=1)
        assert count >= 1

    def test_timestamps_written(self, tiny_video, tmp_path):
        extract_interval_frames(tiny_video, str(tmp_path), interval=1)
        ts_file = tmp_path / "timestamps.txt"
        assert ts_file.exists()
        lines = ts_file.read_text().strip().splitlines()
        assert len(lines) >= 1

    def test_invalid_interval_raises(self, tiny_video, tmp_path):
        with pytest.raises(ValueError):
            extract_interval_frames(tiny_video, str(tmp_path), interval=0)

    def test_time_range(self, tiny_video, tmp_path):
        # Only extract from 0-1s of a 2s video — should get fewer frames
        count_full = extract_interval_frames(tiny_video, str(tmp_path / "full"), interval=1)
        outdir_half = tmp_path / "half"
        outdir_half.mkdir()
        count_half = extract_interval_frames(
            tiny_video, str(outdir_half), interval=1, start=0, end=1
        )
        assert count_half <= count_full
