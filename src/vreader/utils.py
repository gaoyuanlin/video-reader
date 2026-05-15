"""Shared utilities: shell execution, ffprobe helpers."""

from __future__ import annotations

import subprocess
import sys


def run(cmd: str, silent: bool = False, timeout: int = 300) -> tuple[str, int]:
    """Execute a shell command, return (stdout, exit_code).

    Args:
        cmd: Shell command string.
        silent: If True, suppress stderr output on failure.
        timeout: Max seconds to wait (default: 300).

    Returns:
        Tuple of (stdout stripped, return code).
    """
    try:
        r = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        print(f"  ⚠️  Command timed out after {timeout}s", file=sys.stderr)
        return "", 1

    if not silent and r.returncode != 0 and r.stderr:
        print(f"  ⚠️  {r.stderr[:300]}", file=sys.stderr)
    return r.stdout.strip(), r.returncode


def run_lines(cmd: str, timeout: int = 300) -> list[str]:
    """Run a command and return non-empty stdout lines."""
    out, _ = run(cmd, silent=True, timeout=timeout)
    return [ln for ln in out.splitlines() if ln.strip()]


def get_duration(video: str) -> float:
    """Get video duration in seconds via ffprobe.

    Returns:
        Duration in seconds, or 0.0 if the file is missing / unreadable.
    """
    out, code = run(
        f'ffprobe -v error -show_entries format=duration '
        f'-of csv=p=0 "{video}"',
        silent=True,
    )
    if code != 0:
        return 0.0
    try:
        return float(out)
    except (ValueError, TypeError):
        return 0.0


def check_tool(name: str) -> bool:
    """Return True if *name* is available on PATH."""
    _, code = run(f"which {name}", silent=True)
    return code == 0
