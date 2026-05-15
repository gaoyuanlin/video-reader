#!/usr/bin/env python3
"""vreader — Smart video content extraction with scene detection + speech-to-text.

Usage examples
--------------
    vreader video.mp4                          # Scene detection (default)
    vreader video.mp4 --mode interval          # Uniform interval sampling
    vreader video.mp4 --start 60 --end 300     # Process 1 min – 5 min only
    vreader video.mp4 --no-audio               # Skip audio extraction
    vreader video.mp4 -l en -m medium          # English, medium whisper model
    vreader video.mp4 --threshold 0.4          # Less sensitive scene detection
    vreader video.mp4 -o ./output              # Custom output directory
"""

from __future__ import annotations

import argparse
import json
import glob
import os
import sys
import time

from vreader.extractor import (
    get_duration,
    extract_scene_frames,
    extract_interval_frames,
)
from vreader.transcriber import extract_audio, transcribe


# ──────────────────────────────────────────────
# Argument parsing
# ──────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vreader",
        description="vreader — Smart video content extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  vreader lecture.mp4                        scene detection + Chinese transcription
  vreader talk.mp4 -l en -m small            English, small whisper model
  vreader video.mp4 --mode interval          one frame every 5 seconds
  vreader video.mp4 --start 60 --end 300     only 1 min–5 min, with audio
  vreader video.mp4 --no-audio               frames only, skip transcription
  vreader video.mp4 --threshold 0.2          more sensitive scene detection
        """,
    )

    parser.add_argument("video", help="Path to video file")

    # Extraction mode
    mode_grp = parser.add_argument_group("frame extraction")
    mode_grp.add_argument(
        "--mode",
        choices=["scene", "interval"],
        default="scene",
        help="Extraction mode: 'scene' (default) or 'interval'",
    )
    mode_grp.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        metavar="T",
        help="Scene-change sensitivity 0–1 (default: 0.3). Lower = more frames.",
    )
    mode_grp.add_argument(
        "--interval",
        type=int,
        default=5,
        metavar="N",
        help="Seconds between frames in interval mode (default: 5)",
    )
    mode_grp.add_argument(
        "--min-frames",
        type=int,
        default=3,
        metavar="N",
        help="Min scene frames before falling back to interval mode (default: 3)",
    )

    # Time range
    time_grp = parser.add_argument_group("time range")
    time_grp.add_argument(
        "--start", type=float, default=0.0, metavar="SEC", help="Start time in seconds (default: 0)"
    )
    time_grp.add_argument(
        "--end",
        type=float,
        default=None,   # None = process to end of file; avoids --end 0 ambiguity
        metavar="SEC",
        help="End time in seconds (default: end of file)",
    )

    # Audio / transcription
    audio_grp = parser.add_argument_group("audio & transcription")
    audio_grp.add_argument(
        "--no-audio", action="store_true", help="Skip audio extraction & transcription"
    )
    audio_grp.add_argument(
        "-l", "--lang", default="zh", metavar="LANG", help="Audio language code (default: zh)"
    )
    audio_grp.add_argument(
        "-m",
        "--whisper-model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        metavar="MODEL",
        help="Whisper model size: tiny/base/small/medium/large (default: base)",
    )

    # Output
    out_grp = parser.add_argument_group("output")
    out_grp.add_argument(
        "-o", "--output-dir",
        default=None,
        metavar="DIR",
        help="Output directory (default: /tmp/vreader_<timestamp>)",
    )
    out_grp.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress progress output"
    )

    return parser


# ──────────────────────────────────────────────
# Validation helpers
# ──────────────────────────────────────────────

def _validate_args(args: argparse.Namespace) -> None:
    if not os.path.exists(args.video):
        print(f"❌ File not found: {args.video}", file=sys.stderr)
        sys.exit(1)

    if not (0.0 < args.threshold < 1.0):
        print(
            f"❌ --threshold must be between 0 and 1, got {args.threshold}",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.interval < 1:
        print(f"❌ --interval must be ≥ 1, got {args.interval}", file=sys.stderr)
        sys.exit(1)

    if args.end is not None and args.end <= args.start:
        print(
            f"❌ --end ({args.end}) must be greater than --start ({args.start})",
            file=sys.stderr,
        )
        sys.exit(1)


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    _validate_args(args)

    # Redirect stdout to /dev/null when --quiet
    if args.quiet:
        sys.stdout = open(os.devnull, "w")

    video_name = os.path.basename(args.video)
    outdir = args.output_dir or f"/tmp/vreader_{int(time.time())}"
    os.makedirs(outdir, exist_ok=True)

    duration = get_duration(args.video)
    end: float | None = args.end  # already None if not supplied

    mins, secs = int(duration // 60), int(duration % 60)
    print(f"📹 {video_name} ({mins}:{secs:02d})")
    print(f"📁 Output: {outdir}\n")

    # ── Step 1: Frame extraction ─────────────────────────────
    if args.mode == "scene":
        frame_count = extract_scene_frames(
            args.video, outdir, args.start, end, threshold=args.threshold
        )
        if frame_count < args.min_frames:
            print(
                f"  ⚠️  Only {frame_count} scene frame(s) — "
                f"falling back to uniform sampling (every {args.interval}s)..."
            )
            frame_count = extract_interval_frames(
                args.video, outdir, args.interval, args.start, end
            )
    else:
        frame_count = extract_interval_frames(
            args.video, outdir, args.interval, args.start, end
        )

    # ── Step 2: Audio extraction & transcription ─────────────
    transcript_path: str | None = None
    if not args.no_audio:
        if extract_audio(args.video, outdir):
            transcript_path = transcribe(outdir, args.lang, args.whisper_model)

    # ── Step 3: Write summary.json ───────────────────────────
    frames = sorted(glob.glob(os.path.join(outdir, "frame_*.jpg")))
    summary = {
        "video": video_name,
        "video_path": os.path.abspath(args.video),
        "duration_seconds": duration,
        "extraction_mode": args.mode,
        "frame_count": len(frames),
        "output_dir": outdir,
        "has_audio": os.path.exists(os.path.join(outdir, "audio.wav")),
        "has_transcript": transcript_path is not None,
        "transcript_path": transcript_path,
        "settings": {
            "start": args.start,
            "end": end,
            "threshold": args.threshold if args.mode == "scene" else None,
            "interval": args.interval if args.mode == "interval" else None,
            "lang": args.lang,
            "whisper_model": args.whisper_model,
        },
    }
    summary_path = os.path.join(outdir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # ── Final report ─────────────────────────────────────────
    print(f"\n{'=' * 52}")
    print("📊 Done")
    print(f"  File     : {video_name}")
    print(f"  Duration : {mins}m {secs:02d}s")
    print(f"  Frames   : {len(frames)}")
    if transcript_path:
        print(f"  Transcript: {transcript_path}")
    print(f"  Output   : {outdir}")
    print(f"{'=' * 52}")


if __name__ == "__main__":
    main()
