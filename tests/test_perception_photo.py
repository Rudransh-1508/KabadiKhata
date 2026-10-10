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
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("VISION_PROVIDER", raising=False)
    photo._gemini_client.cache_clear()
    yield
    photo._gemini_client.cache_clear()


def answer(**kw) -> str:
    base = {"scale_type": "hanging_dial", "reading": 12, "unit": "kg", "material": "PET",
            "confidence": 0.9, "notes": "", "dial_numbers": [0, 10, 20, 30, 40], "other_column": None}
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


def test_a_bad_reply_is_not_cached(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "0")
    replies = ["", answer(reading=6)]
    monkeypatch.setattr(photo, "_ask_gemini", lambda raw: replies.pop(0))
    img = b64(b"\xff\xd8 flaky")
    assert photo.read_photo(img) == photo.FAILED
    assert photo.read_photo(img).kg == 6.0  # asked again, not replayed


@pytest.mark.parametrize("payload", ["", "not base64 at all!", "   "])
def test_empty_or_garbage_payload_never_reaches_the_model(monkeypatch, payload):
    monkeypatch.setenv("MOCK_LLM", "0")
    monkeypatch.setattr(photo, "_ask_gemini", lambda raw: pytest.fail("model called"))
    assert photo.read_photo(payload) == photo.FAILED


def test_cached_answers_go_through_todays_checks(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "1")
    raw = b"\xff\xd8 cached before a rule change"
    from common import jsoncache
    jsoncache.write_json(photo._cache_path(photo._cache_key(raw)),
                         {"raw_answer": answer(scale_type="none", reading=10)})
    assert photo.read_photo(b64(raw)).kg is None


def test_vision_uses_gemini_even_when_the_agent_uses_openai(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "0")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setattr(photo, "_ask_gemini", lambda raw: answer(reading=4))
    assert photo.read_photo(b64(b"\xff\xd8 openai team")).kg == 4.0


def test_missing_gemini_key_fails_closed(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert photo.read_photo(b64(b"\xff\xd8 no key")) == photo.FAILED


def test_client_is_reused(monkeypatch):
    made = []

    class FakeModels:
        def generate_content(self, **kw):
            return type("R", (), {"text": answer()})()

    class FakeClient:
        def __init__(self, api_key, http_options):
            made.append(1)
            self.models = FakeModels()

    from google import genai
    monkeypatch.setattr(genai, "Client", FakeClient)
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    photo._ask_gemini(b"\xff\xd8 one")
    photo._ask_gemini(b"\xff\xd8 two")
    assert len(made) == 1


@pytest.mark.parametrize("numbers, other, ok", [
    ([0, 10, 20, 30, 40, 50], None, True),
    ([0, 10, 20, 30, 40, 50, 60, 70, 90, 100], None, True),   # a gap is still in order
    ([50, 10, 20, 30, 40], None, True),                       # max printed at the top of a round dial
    ([0, 5, 10, 15, 5], None, False),                         # repeats
    ([0, 10, 30, 50, 40, 50], None, False),                   # goes backwards
    ([0, 10, 15, 20, 30, 50], [0, 13, 15, 20, 40, 50], False),  # the two columns disagree
    ([0, 10, 20, 30, 40, 50], [0, 10, 20, 30, 40, 50], True),
    ([0, 10], None, False),                                   # too few to check
    ("0 10 20", None, False),
    ([0, "ten", 20], None, False),
])
def test_dial_markings_check(numbers, other, ok):
    assert photo.markings_consistent(numbers, other) is ok


def test_a_garbled_dial_gives_no_reading():
    r = parse_answer(answer(dial_numbers=[0, 10, 20, 20, 30, 40, 50], reading=12, confidence=0.9))
    assert r.kg is None and r.confidence <= 0.4


def test_digital_and_beam_scales_skip_the_dial_check():
    assert parse_answer(answer(scale_type="digital", dial_numbers=[], reading=7.5)).kg == 7.5
    assert parse_answer(answer(scale_type="beam_balance", dial_numbers=[], reading=3)).kg == 3.0



# ---------- OpenAI vision and fallback ----------

def test_openai_reads_the_photo_when_it_is_the_only_key(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "0")
    monkeypatch.delenv("GEMINI_API_KEY")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setattr(photo, "_ask_gemini", lambda raw: pytest.fail("gemini has no key"))
    monkeypatch.setattr(photo, "_ask_openai", lambda raw: answer(reading=9))
    assert photo.read_photo(b64(b"\xff\xd8 openai only")).kg == 9.0


def test_falls_back_to_openai_when_gemini_is_down(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "0")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    def busy(raw):
        raise ConnectionError("503")

    monkeypatch.setattr(photo, "_ask_gemini", busy)
    monkeypatch.setattr(photo, "_ask_openai", lambda raw: answer(reading=11))
    img = b64(b"\xff\xd8 gemini down")
    assert photo.read_photo(img).kg == 11.0
    monkeypatch.setenv("MOCK_LLM", "1")  # the fallback's answer replays offline too
    assert photo.read_photo(img).kg == 11.0


def test_vision_provider_setting_picks_the_first(monkeypatch):
    from common import config
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    assert config.vision_providers() == ["gemini", "openai"]
    monkeypatch.setenv("VISION_PROVIDER", "openai")
    assert config.vision_providers() == ["openai", "gemini"]
    monkeypatch.delenv("OPENAI_API_KEY")
    monkeypatch.setenv("GEMINI_API_KEY", "your-gemini-key")
    assert config.vision_providers() == ["openai"]  # chosen explicitly; placeholder keys don't count


def test_openai_request_shape_and_timeout(monkeypatch):
    import httpx
    seen = {}

    def fake_post(url, **kw):
        seen.update(url=url, **kw)
        return httpx.Response(200, json={"choices": [{"message": {"content": answer(reading=5)}}]},
                              request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("PERCEPTION_TIMEOUT_S", "9")
    assert parse_answer(photo._ask_openai(b"\xff\xd8 jpeg")).kg == 5.0
    body = seen["json"]
    assert seen["timeout"] == 9.0 and body["temperature"] == 0
    assert body["response_format"] == {"type": "json_object"}
    assert body["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/jpeg;base64,")



def test_grok_reads_the_photo_and_is_a_fallback(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "0")
    monkeypatch.setenv("XAI_API_KEY", "test-xai-key")
    from common import config
    assert config.vision_providers() == ["gemini", "xai"]

    def busy(raw):
        raise ConnectionError("503")

    monkeypatch.setattr(photo, "_ask_gemini", busy)
    monkeypatch.setattr(photo, "_ask_xai", lambda raw: "```json\n" + answer(reading=14) + "\n```")
    assert photo.read_photo(b64(b"\xff\xd8 grok")).kg == 14.0
    monkeypatch.setenv("VISION_PROVIDER", "xai")
    assert config.vision_providers()[0] == "xai"


def test_grok_request_goes_to_xai_without_json_mode(monkeypatch):
    import httpx
    seen = {}

    def fake_post(url, **kw):
        seen.update(url=url, **kw)
        return httpx.Response(200, json={"choices": [{"message": {"content": answer(reading=3)}}]},
                              request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setenv("XAI_API_KEY", "test-xai-key")
    assert parse_answer(photo._ask_xai(b"\xff\xd8 jpeg")).kg == 3.0
    assert seen["url"] == "https://api.x.ai/v1/chat/completions"
    assert "response_format" not in seen["json"] and seen["json"]["model"] == "grok-4.7"



def test_groq_request_shape(monkeypatch):
    import httpx
    seen = {}

    def fake_post(url, **kw):
        seen.update(url=url, **kw)
        return httpx.Response(200, json={"choices": [{"message": {"content": answer(reading=6)}}]},
                              request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    assert parse_answer(photo._ask_groq(b"\xff\xd8 jpeg")).kg == 6.0
    assert seen["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert seen["json"]["response_format"] == {"type": "json_object"}
    from common import config
    assert config.vision_providers() == ["gemini", "groq"]
