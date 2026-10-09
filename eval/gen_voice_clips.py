"""Generate the synthetic voice clips in data/eval_voice/labels.csv with Gemini text-to-speech.

    uv run python eval/gen_voice_clips.py        # needs GEMINI_API_KEY in .env or the environment

Writes data/eval_voice/tts/tts_XX.wav (gitignored), 16-bit mono WAV. Rows already on disk are
skipped, so a rate-limited run can be resumed. Voices rotate so the eval isn't one speaker.
These clips are Synthetic (CLAUDE.md rule 3): report them apart from real recordings.
"""
import csv
import os
import sys
import time
import wave
from pathlib import Path

LABELS = Path("data/eval_voice/labels.csv")
OUT = Path("data/eval_voice/tts")
MODEL = os.getenv("GEMINI_TTS_MODEL_ID", "gemini-2.5-flash-preview-tts")
VOICES = ("Kore", "Puck", "Charon", "Aoede", "Fenrir", "Leda")
STYLE = ("Say this the way a scrap collector in a Delhi lane would, casually, in Hindi, "
         "as a quick voice note on a phone: ")


def load_env() -> None:
    env = Path(".env")
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() and not key.startswith("#"):
                os.environ.setdefault(key.strip(), value.split("#", 1)[0].strip())


def speak(client, types, text: str, voice: str) -> bytes:
    resp = client.models.generate_content(
        model=MODEL,
        contents=STYLE + text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice))
            ),
        ),
    )
    return resp.candidates[0].content.parts[0].inline_data.data  # 24 kHz 16-bit mono PCM


def main() -> int:
    load_env()
    if not os.getenv("GEMINI_API_KEY") or os.environ["GEMINI_API_KEY"].startswith("your-"):
        print("Set GEMINI_API_KEY in .env first.")
        return 1
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [r for r in csv.DictReader(LABELS.open(encoding="utf-8")) if r["set"] == "tts"]
    for i, r in enumerate(rows):
        path = OUT / r["file"]
        if path.exists():
            continue
        pcm = speak(client, types, r["text"], VOICES[i % len(VOICES)])
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(24000)
            w.writeframes(pcm)
        print(f"{r['file']}: {r['text']}")
        time.sleep(2)  # stay under free-tier rate limits
    print(f"{len(rows)} clips in {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
