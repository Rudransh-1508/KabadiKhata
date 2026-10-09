"""Generate the synthetic voice clips in data/eval_voice/labels.csv.

    uv run python eval/gen_voice_clips.py               # Gemini TTS, 6 voices (needs GEMINI_API_KEY)
    uv run python eval/gen_voice_clips.py --engine say  # macOS "Lekha" Hindi voice: offline, no quota
    uv run python eval/gen_voice_clips.py --engine sarvam  # Sarvam Bulbul, 6 Indian voices (needs SARVAM_API_KEY)

The Gemini free tier allows only a few TTS clips a day; the macOS voice has no limit. Each engine
writes its own set (`tts`, `say`, `sarvam` -> data/eval_voice/<set>/), scored apart.

Writes data/eval_voice/tts/tts_XX.wav (gitignored), 16-bit mono WAV. Rows already on disk are
skipped, so a rate-limited run can be resumed. Empty replies are retried, per-minute rate limits
are waited out, and a used-up daily quota stops the run cleanly. Voices rotate so the eval isn't one speaker.
These clips are Synthetic (CLAUDE.md rule 3): report them apart from real recordings.
"""
import argparse
import csv
import os
import re
import subprocess
import sys
import time
import wave
from pathlib import Path

from _env import load_env

LABELS = Path("data/eval_voice/labels.csv")
OUT = Path("data/eval_voice/tts")
SAY_OUT = Path("data/eval_voice/say")
SAY_VOICE = "Lekha"
SARVAM_OUT = Path("data/eval_voice/sarvam")
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
SARVAM_TTS_MODEL = os.getenv("SARVAM_TTS_MODEL_ID", "bulbul:v3")
SARVAM_SPEAKERS = ("shubh", "ritu", "aditya", "priya", "rahul", "neha")
MODEL = os.getenv("GEMINI_TTS_MODEL_ID", "gemini-2.5-flash-preview-tts")
PAUSE_S = float(os.getenv("TTS_PAUSE_S", "7"))
VOICES = ("Kore", "Puck", "Charon", "Aoede", "Fenrir", "Leda")
STYLE = ("Say this the way a scrap collector in a Delhi lane would, casually, in Hindi, "
         "as a quick voice note on a phone: ")


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


def say_main() -> int:
    """macOS text-to-speech with the Hindi voice; converted to 16 kHz mono WAV like the bot sends."""
    SAY_OUT.mkdir(parents=True, exist_ok=True)
    rows = [r for r in csv.DictReader(LABELS.open(encoding="utf-8")) if r["set"] == "say"]
    for r in rows:
        path = SAY_OUT / r["file"]
        if path.exists():
            continue
        aiff = path.with_suffix(".aiff")
        subprocess.run(["say", "-v", SAY_VOICE, "-o", str(aiff), r["speak_hi"]], check=True)
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@16000", "-c", "1", str(aiff), str(path)], check=True)
        aiff.unlink()
        print(f"{r['file']}: {r['speak_hi']}")
    print(f"{len(rows)} clips in {SAY_OUT}")
    return 0


def sarvam_main() -> int:
    """Sarvam Bulbul text-to-speech: 16 kHz WAV, speakers rotate so the eval isn't one voice."""
    import base64

    import httpx

    load_env()
    key = os.getenv("SARVAM_API_KEY", "")
    if not key or key.startswith("your-"):
        print("Set SARVAM_API_KEY in .env first (dashboard.sarvam.ai).")
        return 1
    SARVAM_OUT.mkdir(parents=True, exist_ok=True)
    rows = [r for r in csv.DictReader(LABELS.open(encoding="utf-8")) if r["set"] == "sarvam"]
    for i, r in enumerate(rows):
        path = SARVAM_OUT / r["file"]
        if path.exists():
            continue
        resp = httpx.post(
            SARVAM_TTS_URL,
            headers={"api-subscription-key": key},
            json={"text": r["speak_hi"], "language_code": "hi-IN", "model": SARVAM_TTS_MODEL,
                  "speaker": SARVAM_SPEAKERS[i % len(SARVAM_SPEAKERS)], "speech_sample_rate": 16000},
            timeout=60,
        )
        if resp.status_code != 200:
            print(f"{r['file']}: HTTP {resp.status_code}: {resp.text[:300]}")
            return 1
        path.write_bytes(base64.b64decode("".join(resp.json()["audios"])))
        print(f"{r['file']}: {r['speak_hi']}")
    print(f"{len(rows)} clips in {SARVAM_OUT}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["gemini", "say", "sarvam"], default="gemini")
    engine = ap.parse_args().engine
    if engine == "say":
        return say_main()
    if engine == "sarvam":
        return sarvam_main()
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
            pcm = speak_with_retries(client, types, r["speak_hi"] or r["text"], VOICES[i % len(VOICES)])
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
        print(f"{r['file']}: {r['speak_hi'] or r['text']}")
        time.sleep(PAUSE_S)  # stay under free-tier rate limits
    done = sum((OUT / r["file"]).exists() for r in rows)
    print(f"{done}/{len(rows)} clips in {OUT}")
    if done < len(rows):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
