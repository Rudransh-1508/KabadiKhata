"""Freeze the demo inputs, so demo day doesn't depend on Gemini, OpenAI or Sarvam answering.

    1. Rehearse the demo once through Telegram with real models (MOCK_LLM=0 make api + make bot).
       The API saves every photo it receives as data/photos/<sha256>.jpg: the exact bytes
       read_photo sees (Telegram re-compresses photos, so the original file would not match).
    2. uv run python eval/freeze_demo.py --latest [--audio note.wav]
       Reads the photo (and voice note) live once if not cached yet, then replays them with
       MOCK_LLM=1 and checks the answers are identical and come from the cache, not the stub.
       Exports those cache entries to data/demo/cache/ (commit them) and writes data/demo/frozen.json.
    3. On the demo laptop: uv run python eval/freeze_demo.py --install
       Copies data/demo/cache/ into the local cache, so MOCK_LLM=1 replays the real readings.

--photo PATH uses a specific file as-is; add --as-bot for a file that did not come through the API
(it is resized the way the bot does, but Telegram's own re-compression is not reproduced).
"""
import argparse
import base64
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
from _env import load_env  # noqa: E402
from common import config  # noqa: E402
from perception import photo, voice  # noqa: E402

DEMO = ROOT / "data" / "demo"
EXPORT = DEMO / "cache"


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


def _photo_cache_file(raw: bytes) -> Path | None:
    path = photo.cache_file(raw)
    return Path(path) if path else None


def _voice_cache_file(raw: bytes) -> Path | None:
    path = voice.cache_file(raw)
    return Path(path) if path else None


def _with_mock(flag: str, fn, *args):
    old = os.environ.get("MOCK_LLM")
    os.environ["MOCK_LLM"] = flag
    try:
        return fn(*args)
    finally:
        if old is None:
            os.environ.pop("MOCK_LLM", None)
        else:
            os.environ["MOCK_LLM"] = old


def install() -> int:
    if not EXPORT.exists():
        print(f"Nothing to install: {EXPORT} is missing. Run --latest or --photo first.")
        return 1
    n = 0
    for src in EXPORT.rglob("*.json"):
        dst = Path(config.cache_dir()) / src.relative_to(EXPORT)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    print(f"Installed {n} frozen answers into {config.cache_dir()}. MOCK_LLM=1 now replays the demo inputs.")
    return 0


def freeze(photo_path: Path, audio_path: Path | None, as_bot: bool) -> int:
    raw = photo_path.read_bytes()
    if as_bot:
        from bot.telegram_bot import resize_for_upload
        raw = resize_for_upload(raw)
    ok = True

    live = _with_mock("0", photo.read_photo, _b64(raw))
    replay = _with_mock("1", photo.read_photo, _b64(raw))
    cache_file = _photo_cache_file(raw)
    print(f"Photo {photo_path.name}: kg={live.kg} material={live.material} confidence={live.confidence:.2f}")
    if live.kg is None:
        print("  ! no Scale reading: this photo would get the retake question. Pick a clearer one.")
        ok = False
    if cache_file is None or replay != live:
        print(f"  ! replay differs or isn't cached (replay: {replay}). Run again when the model answers.")
        ok = False

    entry = {"photo": photo_path.name, "photo_sha256": hashlib.sha256(raw).hexdigest(),
             "photo_read": live.model_dump(), "photo_models": photo.model_tags(),
             "photo_prompt": photo.PROMPT_VERSION, "files": []}
    if cache_file:
        entry["files"].append(cache_file)

    if audio_path:
        araw = audio_path.read_bytes()
        heard, status = _with_mock("0", voice.transcribe_with_status, _b64(araw))
        again, again_status = _with_mock("1", voice.transcribe_with_status, _b64(araw))
        vfile = _voice_cache_file(araw)
        print(f"Voice {audio_path.name}: heard {heard.text_hi!r} -> kg={heard.claimed_kg} material={heard.claimed_material}")
        if status == "error" or vfile is None or again != heard or again_status != "cached":
            print(f"  ! voice not frozen (status {status}, replay {again_status}). Run again when the service answers.")
            ok = False
        entry.update(audio=audio_path.name, voice=heard.model_dump(), voice_model=voice._model_tag())
        if vfile:
            entry["files"].append(vfile)

    if not ok:
        return 1
    for f in entry.pop("files"):
        dst = EXPORT / f.relative_to(config.cache_dir())
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
    entry["frozen_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    DEMO.mkdir(parents=True, exist_ok=True)
    (DEMO / "frozen.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Frozen. Commit {EXPORT}/ and {DEMO / 'frozen.json'}; "
          "on the demo laptop run: uv run python eval/freeze_demo.py --install")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--latest", action="store_true", help="newest photo the API received (data/photos)")
    src.add_argument("--photo", type=Path, help="a specific photo file")
    src.add_argument("--install", action="store_true", help="copy data/demo/cache into the local cache")
    ap.add_argument("--audio", type=Path, help="the demo voice note (WAV/OGG/MP3 as sent to the API)")
    ap.add_argument("--as-bot", action="store_true", help="resize --photo the way the bot does")
    args = ap.parse_args()
    load_env()

    if args.install:
        return install()
    if args.latest:
        photos = sorted(Path(os.getenv("KK_PHOTO_DIR", ROOT / "data" / "photos")).glob("*.jpg"),
                        key=lambda p: p.stat().st_mtime)
        if not photos:
            print("No photos in data/photos yet: send the demo photo through the bot once (MOCK_LLM=0).")
            return 1
        path = photos[-1]
    else:
        path = args.photo
    return freeze(path, args.audio, args.as_bot)


if __name__ == "__main__":
    sys.exit(main())
