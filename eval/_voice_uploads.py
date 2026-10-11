"""Uploaded real voice notes (data/eval_voice/uploads/real_XX.<any audio>) -> data/eval_voice/real/real_XX.wav.

The real/ WAVs are gitignored; the uploads are committed. voice_eval, record_voice and
gen_voice_clips --engine clone all call import_uploads() first, so a fresh clone scores the
uploaded notes and record_voice never records over a line someone already uploaded.
"""
import subprocess
from pathlib import Path

REAL_OUT = Path("data/eval_voice/real")
UPLOADS = Path("data/eval_voice/uploads")


def import_uploads() -> list[Path]:
    """Convert each upload with no WAV yet to 16 kHz mono WAV like the bot sends; returns the WAVs made."""
    made = []
    for src in sorted(UPLOADS.glob("real_*.*")) if UPLOADS.exists() else []:
        wav = REAL_OUT / f"{src.stem}.wav"
        if wav.exists():
            continue
        REAL_OUT.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
                        "-ac", "1", "-ar", "16000", str(wav)], check=True)
        made.append(wav)
    return made
