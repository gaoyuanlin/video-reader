"""Audio extraction & speech-to-text transcription via whisper-cli.

Requirements
------------
- ``ffmpeg`` — audio extraction
- ``whisper-cli`` — transcription (whisper.cpp)
  - macOS: ``brew install whisper-cpp``
  - Model: ``whisper-cli download base``
"""

from __future__ import annotations

import os
import sys

from vreader.utils import check_tool, run


# Default search paths for whisper model files
_MODEL_SEARCH_DIRS = [
    "~/.whisper/models",
    "~/.local/share/whisper/models",
    "/usr/local/share/whisper/models",
]


def _find_model(model: str) -> str | None:
    """Locate the ggml model binary for *model*.

    Searches common install directories.  Returns the first match or ``None``.
    """
    filename = f"ggml-{model}.bin"
    for directory in _MODEL_SEARCH_DIRS:
        candidate = os.path.expanduser(os.path.join(directory, filename))
        if os.path.exists(candidate):
            return candidate
    return None


def extract_audio(video: str, outdir: str) -> bool:
    """Extract audio track to a 16 kHz mono WAV file.

    Args:
        video: Path to video file.
        outdir: Output directory.

    Returns:
        ``True`` if extraction succeeded.
    """
    print("🎤 Extracting audio...")

    if not check_tool("ffmpeg"):
        print("  ❌ ffmpeg not found on PATH", file=sys.stderr)
        return False

    wav_path = os.path.join(outdir, "audio.wav")
    cmd = (
        f'ffmpeg -hide_banner -loglevel warning '
        f'-i "{video}" -vn -acodec pcm_s16le -ar 16000 -ac 1 '
        f'"{wav_path}" -y'
    )
    _, code = run(cmd, silent=True)

    if code == 0 and os.path.exists(wav_path):
        size_mb = os.path.getsize(wav_path) / 1024 / 1024
        print(f"  ✅ {size_mb:.1f} MB WAV")
        return True

    print("  ❌ Audio extraction failed", file=sys.stderr)
    return False


def transcribe(
    outdir: str,
    lang: str = "zh",
    model: str = "base",
) -> str | None:
    """Transcribe ``audio.wav`` inside *outdir* with whisper-cli.

    Args:
        outdir: Directory that contains ``audio.wav``.
        lang: BCP-47 language code (``zh``, ``en``, ``ja``, …).
        model: Whisper model size: tiny / base / small / medium / large.

    Returns:
        Absolute path to ``transcript.txt``, or ``None`` on failure.
    """
    print(f"📝 Transcribing (model={model}, lang={lang})...")

    if not check_tool("whisper-cli"):
        print("  ❌ whisper-cli not found on PATH", file=sys.stderr)
        print("     macOS: brew install whisper-cpp", file=sys.stderr)
        return None

    model_path = _find_model(model)
    if model_path is None:
        print(f"  ⚠️  Model '{model}' not found in any of:", file=sys.stderr)
        for d in _MODEL_SEARCH_DIRS:
            print(f"       {os.path.expanduser(d)}", file=sys.stderr)
        print(f"     Download with: whisper-cli download {model}", file=sys.stderr)
        return None

    wav_path = os.path.join(outdir, "audio.wav")
    if not os.path.exists(wav_path):
        print(f"  ❌ audio.wav not found in {outdir}", file=sys.stderr)
        return None

    transcript_base = os.path.join(outdir, "transcript")
    cmd = (
        f'whisper-cli -m "{model_path}" -f "{wav_path}" '
        f'-l {lang} -otxt -of "{transcript_base}"'
    )
    _, code = run(cmd)

    txt_path = f"{transcript_base}.txt"
    if os.path.exists(txt_path):
        with open(txt_path, encoding="utf-8") as fh:
            line_count = sum(1 for _ in fh)
        print(f"  ✅ {line_count} lines transcribed → {txt_path}")
        return txt_path

    print("  ❌ Transcription failed (whisper-cli exit code: {code})", file=sys.stderr)
    return None
