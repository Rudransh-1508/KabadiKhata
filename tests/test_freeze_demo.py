import base64
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
import freeze_demo  # noqa: E402
from perception import photo, voice  # noqa: E402

WAV = b"RIFF\x00\x00\x00\x00WAVEfmt demo note"


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("KK_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("SARVAM_API_KEY", "test-sarvam-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("VISION_PROVIDER", raising=False)
    monkeypatch.setenv("VOICE_PROVIDER", "sarvam")
    monkeypatch.setattr(freeze_demo, "DEMO", tmp_path / "demo")
    monkeypatch.setattr(freeze_demo, "EXPORT", tmp_path / "demo" / "cache")
    return tmp_path


def reading(kg):
    return json.dumps({"scale_type": "hanging_dial", "reading": kg, "unit": "kg", "material": "PET",
                       "confidence": 0.9, "dial_numbers": [0, 10, 20, 30, 40], "other_column": None})


def test_freeze_exports_answers_that_replay_on_another_machine(isolated, monkeypatch):
    img = isolated / "demo.jpg"
    img.write_bytes(b"\xff\xd8 the demo photo")
    note = isolated / "note.wav"
    note.write_bytes(WAV)
    monkeypatch.setattr(photo, "_ask_gemini", lambda raw: reading(12))
    monkeypatch.setattr(voice, "_ask_sarvam", lambda raw: "बारह किलो बोतल")

    assert freeze_demo.freeze(img, note, as_bot=False) == 0
    frozen = json.loads((isolated / "demo" / "frozen.json").read_text())
    assert frozen["photo_read"]["kg"] == 12.0 and frozen["voice"]["claimed_kg"] == 12.0
    assert len(list((isolated / "demo" / "cache").rglob("*.json"))) == 2

    # The demo laptop: empty cache, models unreachable, MOCK_LLM=1
    monkeypatch.setenv("KK_CACHE_DIR", str(isolated / "laptop-cache"))
    monkeypatch.setenv("MOCK_LLM", "1")
    assert freeze_demo.install() == 0
    assert photo.read_photo(base64.b64encode(img.read_bytes()).decode()).kg == 12.0
    assert voice.transcribe(base64.b64encode(WAV).decode()).claimed_kg == 12.0


def test_an_unreadable_demo_photo_is_not_frozen(isolated, monkeypatch):
    img = isolated / "blurry.jpg"
    img.write_bytes(b"\xff\xd8 blurry")
    monkeypatch.setattr(photo, "_ask_gemini", lambda raw: reading(None))
    assert freeze_demo.freeze(img, None, as_bot=False) == 1
    assert not (isolated / "demo" / "frozen.json").exists()


def test_nothing_is_frozen_while_the_model_is_down(isolated, monkeypatch):
    img = isolated / "demo.jpg"
    img.write_bytes(b"\xff\xd8 the demo photo")

    def down(raw):
        raise ConnectionError("503")

    monkeypatch.setattr(photo, "_ask_gemini", down)
    assert freeze_demo.freeze(img, None, as_bot=False) == 1
    assert not (isolated / "demo" / "cache").exists()
