import base64
import json

import pytest

from perception import photo
from perception.photo import parse_answer


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("KK_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("LLM_PROVIDER", "gemini")


def answer(**kw) -> str:
    base = {"scale_type": "hanging_dial", "reading": 12, "unit": "kg", "material": "PET",
            "confidence": 0.9, "notes": ""}
    return json.dumps({**base, **kw})


def test_parses_a_clean_reading():
    r = parse_answer(answer())
    assert (r.kg, r.material, r.confidence) == (12.0, "PET", 0.9)


def test_converts_pounds_and_grams():
    assert parse_answer(answer(reading=20.16, unit="lb")).kg == pytest.approx(9.14, abs=0.01)
    assert parse_answer(answer(reading=500, unit="g")).kg == 0.5


@pytest.mark.parametrize("bad", [{"reading": None}, {"reading": 0}, {"reading": 900},
                                 {"reading": -3}, {"unit": "stone"}, {"reading": "twelve"}])
def test_no_reading_means_kg_none_and_low_confidence(bad):
    r = parse_answer(answer(**bad))
    assert r.kg is None and r.confidence <= 0.4


def test_unknown_material_and_bad_confidence_are_cleaned():
    r = parse_answer(answer(material="glass", confidence=7))
    assert r.material == "unknown" and r.confidence == 1.0


@pytest.mark.parametrize("text", ["", "not json", "[1, 2]", "```json\n{oops\n```"])
def test_garbage_fails_closed(text):
    assert parse_answer(text) == photo.FAILED


def test_accepts_json_in_code_fences():
    assert parse_answer("```json\n" + answer(reading=7.5) + "\n```").kg == 7.5


def test_fixture_payloads_use_the_stub():
    r = photo.read_photo(b64(b"fixture:8:paper:0.95"))
    assert (r.kg, r.material) == (8.0, "paper")


def test_mock_mode_never_calls_the_model(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "1")
    monkeypatch.setattr(photo, "_ask_gemini", lambda raw: pytest.fail("model called in MOCK_LLM mode"))
    assert photo.read_photo(b64(b"\x89PNG some image")).kg == 12.0  # stub default


def test_model_answer_is_cached_and_replayed(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "0")
    calls = []
    monkeypatch.setattr(photo, "_ask_gemini", lambda raw: calls.append(raw) or answer(reading=5.5))
    img = b64(b"\xff\xd8 jpeg bytes")
    assert photo.read_photo(img).kg == 5.5
    monkeypatch.setenv("MOCK_LLM", "1")  # replay works without a key
    assert photo.read_photo(img).kg == 5.5
    assert len(calls) == 1


def test_model_failure_fails_closed(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "0")

    def boom(raw):
        raise ConnectionError("no network")

    monkeypatch.setattr(photo, "_ask_gemini", boom)
    assert photo.read_photo(b64(b"\xff\xd8 other")) == photo.FAILED


@pytest.mark.parametrize("scale_type", ["none", None, "watch", "pressure_gauge", ""])
def test_a_number_without_a_weighing_scale_is_not_a_reading(scale_type):
    r = parse_answer(answer(scale_type=scale_type, reading=10.1, confidence=0.95))
    assert r.kg is None and r.confidence <= 0.4


def test_every_scale_type_in_the_prompt_is_accepted():
    for t in photo.SCALE_TYPES:
        assert t in photo.SYSTEM_PROMPT
        assert parse_answer(answer(scale_type=t)).kg == 12.0


def test_gemini_call_has_a_timeout(monkeypatch):
    seen = {}

    class FakeModels:
        def generate_content(self, **kw):
            return type("R", (), {"text": answer()})()

    class FakeClient:
        def __init__(self, api_key, http_options):
            seen["timeout_ms"] = http_options.timeout
            self.models = FakeModels()

    from google import genai
    monkeypatch.setattr(genai, "Client", FakeClient)
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    monkeypatch.setenv("PERCEPTION_TIMEOUT_S", "15")
    photo._ask_gemini(b"\xff\xd8 jpeg")
    assert seen["timeout_ms"] == 15000
