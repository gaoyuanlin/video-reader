"""Frame extraction — scene detection & interval-based.

Scene-change detection uses ffmpeg's ``select=gt(scene,T)`` filter.
Timestamps are parsed from ffprobe rather than a fragile shell pipeline.
"""

from __future__ import annotations

import glob
import os

from vreader.utils import get_duration, run, run_lines  # noqa: F401 (re-exported)


# ──────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────

def _time_range_flags(start: float, end: float | None) -> tuple[str, str]:
    """Return (input_seek_flag, duration_flag) for ffmpeg."""
    seek = f"-ss {start}" if start > 0 else ""
    dur = f"-t {end - start}" if end is not None else ""
    return seek, dur


def _extract_timestamps_ffprobe(
    video: str, start: float, end: float | None, threshold: float
) -> list[float]:
    """Use ffprobe select filter to extract timestamps without a shell pipe.

    This avoids the unreliable ``2>&1 | grep`` approach used previously.

    Returns:
        Sorted list of timestamps in seconds.
    """
    seek, dur = _time_range_flags(start, end)

    select = f"gt(scene,{threshold})"
    if end is not None:
        select = f"between(t,{start},{end})*gt(scene,{threshold})"

    cmd = (
        f'ffprobe -v error {seek} {dur} -i "{video}" '
        f'-vf "select=\'{select}\'" '
        f'-show_entries frame=best_effort_timestamp_time '
        f'-of csv=p=0'
    )
    lines = run_lines(cmd, timeout=600)
    timestamps: list[float] = []
    for ln in lines:
        try:
            timestamps.append(float(ln.strip()))
        except ValueError:
            continue
    return sorted(timestamps)


def _write_timestamps(timestamps: list[float], outdir: str) -> None:
    ts_path = os.path.join(outdir, "timestamps.txt")
    with open(ts_path, "w", encoding="utf-8") as f:
        for ts in timestamps:
            f.write(f"{ts:.3f}\n")


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def extract_scene_frames(
    video: str,
    outdir: str,
    start: float = 0,
    end: float | None = None,
    threshold: float = 0.3,
) -> int:
    """Scene-change detection: capture a frame when visual change exceeds *threshold*.

    Args:
        video: Path to video file.
        outdir: Output directory for frames.
        start: Start time in seconds.
        end: End time in seconds (``None`` = to end of file).
        threshold: Scene-change sensitivity (0–1). Lower = more frames.

    Returns:
        Number of extracted frames.
    """
    print(f"🎬 Scene detection (threshold={threshold})...")

    seek, dur = _time_range_flags(start, end)

    select = f"gt(scene,{threshold})"
    if end is not None:
        select = f"between(t,{start},{end})*gt(scene,{threshold})"

    frame_pattern = os.path.join(outdir, "frame_%04d.jpg")
    cmd = (
        f'ffmpeg -hide_banner -loglevel warning '
        f'{seek} {dur} -i "{video}" '
        f'-vf "select=\'{select}\'" '
        f'-vsync vfr -q:v 2 "{frame_pattern}" -y'
    )
    run(cmd, timeout=600)

    # Timestamps extracted separately via ffprobe (no shell pipe needed)
    timestamps = _extract_timestamps_ffprobe(video, start, end, threshold)
    _write_timestamps(timestamps, outdir)

    frames = sorted(glob.glob(os.path.join(outdir, "frame_*.jpg")))
    print(f"  ✅ {len(frames)} frames (scene detection)")
    return len(frames)


def extract_interval_frames(
    video: str,
    outdir: str,
    interval: int = 5,
    start: float = 0,
    end: float | None = None,
) -> int:
    """Uniform-interval frame extraction.

    Args:
        video: Path to video file.
        outdir: Output directory for frames.
        interval: Seconds between frames (must be ≥ 1).
        start: Start time in seconds.
        end: End time in seconds (``None`` = to end of file).

    Returns:
        Number of extracted frames.
    """
    if interval < 1:
        raise ValueError(f"interval must be >= 1, got {interval}")

    print(f"🎬 Uniform sampling (every {interval}s)...")

    seek, dur = _time_range_flags(start, end)
    frame_pattern = os.path.join(outdir, "frame_%04d.jpg")

    cmd = (
        f'ffmpeg -hide_banner -loglevel warning '
        f'{seek} {dur} -i "{video}" '
        f'-vf "fps=1/{interval}" -q:v 2 "{frame_pattern}" -y'
    )
    run(cmd, timeout=600)

    frames = sorted(glob.glob(os.path.join(outdir, "frame_*.jpg")))

    # Generate synthetic timestamps for interval mode
    timestamps = [start + i * interval for i in range(len(frames))]
    _write_timestamps(timestamps, outdir)

    print(f"  ✅ {len(frames)} frames (uniform sampling)")
    return len(frames)
