"""Record real voice notes for the transcribe eval, one scripted line at a time.

    uv run python eval/record_voice.py            # 8 lines, 5 s each, MacBook microphone

Shows a line, waits for Enter, records it through ffmpeg, and saves data/eval_voice/real/real_XX.wav
(16 kHz mono, gitignored) plus a `real` row in data/eval_voice/labels.csv with the same true
weight and material as the scripted line. Say it the way a kabadiwala would; small changes in
wording are fine as long as the number and the material stay the same. Re-running skips clips
already recorded. macOS asks once for microphone access for the terminal.
"""
import argparse
import csv
import subprocess
import sys
from pathlib import Path

from _voice_uploads import import_uploads

LABELS = Path("data/eval_voice/labels.csv")
OUT = Path("data/eval_voice/real")
# A spread of numbers (fractions, tens, 40), materials and the injection line
LINES = ["tts_02.wav", "tts_07.wav", "tts_09.wav", "tts_13.wav",
         "tts_19.wav", "tts_23.wav", "tts_24.wav", "tts_28.wav"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=5)
    ap.add_argument("--mic", default="MacBook Air Microphone", help="avfoundation audio device name")
    args = ap.parse_args()

    rows = list(csv.DictReader(LABELS.open(encoding="utf-8")))
    fields = list(rows[0].keys())
    by_file = {r["file"]: r for r in rows}
    OUT.mkdir(parents=True, exist_ok=True)
    import_uploads()  # lines someone already uploaded are not recorded again

    for n, src in enumerate(LINES, 1):
        name = f"real_{n:02d}.wav"
        if (OUT / name).exists():
            continue
        line = by_file[src]
        print(f"\n[{n}/{len(LINES)}] Say:  {line['text']}\n         ({line['speak_hi']})")
        input("Press Enter, then speak... ")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "avfoundation",
                        "-i", f":{args.mic}", "-t", str(args.seconds), "-ac", "1", "-ar", "16000",
                        str(OUT / name)], check=True)
        print(f"  saved {OUT / name}")
        if name not in by_file:
            row = {**line, "file": name, "set": "real", "synthetic": "false",
                   "notes": "real recording by the team"}
            rows.append(row)
            by_file[name] = row
            with LABELS.open("w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=fields)
                w.writeheader()
                w.writerows(rows)
    print("\nDone. Score them with: uv run python eval/voice_eval.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
