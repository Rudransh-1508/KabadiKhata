"""Generate the synthetic voice clips in data/eval_voice/labels.csv with Gemini text-to-speech.

    uv run python eval/gen_voice_clips.py        # needs GEMINI_API_KEY in .env or the environment

Writes data/eval_voice/tts/tts_XX.wav (gitignored), 16-bit mono WAV. Rows already on disk are
skipped, so a rate-limited run can be resumed. Empty replies are retried, per-minute rate limits
are waited out, and a used-up daily quota stops the run cleanly. Voices rotate so the eval isn't one speaker.
These clips are Synthetic (CLAUDE.md rule 3): report them apart from real recordings.
"""
import csv
import os
import re
import sys
import time
import wave
from pathlib import Path

LABELS = Path("data/eval_voice/labels.csv")
OUT = Path("data/eval_voice/tts")
MODEL = os.getenv("GEMINI_TTS_MODEL_ID", "gemini-2.5-flash-preview-tts")
PAUSE_S = float(os.getenv("TTS_PAUSE_S", "7"))
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


def speak(client, types, text: str, voice: str) -> bytes | None:
    """24 kHz 16-bit mono PCM, or None if the model returned no audio (it sometimes does)."""
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
    cand = resp.candidates[0] if resp.candidates else None
    if not (cand and cand.content and cand.content.parts and cand.content.parts[0].inline_data):
        return None
    return cand.content.parts[0].inline_data.data


class QuotaExhausted(Exception):
    pass


def speak_with_retries(client, types, text: str, voice: str) -> bytes | None:
    from google.genai import errors

    for attempt in range(6):
        try:
            pcm = speak(client, types, text, voice)
        except errors.ClientError as exc:
            if exc.code != 429:
                raise
            msg = str(exc)
            if "PerDay" in msg or "per day" in msg.lower():
                raise QuotaExhausted(msg) from exc
            m = re.search(r"retry(?:Delay)?['\"]?:?\s*['\"]?(\d+)", msg, re.IGNORECASE)
            wait = int(m.group(1)) + 2 if m else 30
            print(f"  rate limited, waiting {wait}s")
            time.sleep(wait)
            continue
        if pcm:
            return pcm
        time.sleep(3 * (attempt + 1))  # empty reply: try again
    return None


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
        try:
            pcm = speak_with_retries(client, types, r["text"], VOICES[i % len(VOICES)])
        except QuotaExhausted:
            print("Daily TTS quota used up. Run this again tomorrow (or with a paid key); finished clips are kept.")
            return 1
        if pcm is None:
            print(f"{r['file']}: no audio after retries, skipped (run again to retry)")
            continue
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(24000)
            w.writeframes(pcm)
        print(f"{r['file']}: {r['text']}")
        time.sleep(PAUSE_S)  # stay under free-tier rate limits
    done = sum((OUT / r["file"]).exists() for r in rows)
    print(f"{done}/{len(rows)} clips in {OUT}")
    if done < len(rows):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
