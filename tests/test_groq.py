"""Groq for the agent and the radar explainer: fallback across keys on 429/5xx, and the wiring."""
import asyncio
import base64

import httpx
import pytest

from common import groq


@pytest.fixture(autouse=True)
def clean_groq_env(monkeypatch):
    import os
    for name in list(os.environ):
        if name.startswith("GROQ_"):
            monkeypatch.delenv(name)
    groq._ring.cache_clear()
    yield
    groq._ring.cache_clear()


def send(ring, statuses: dict, n: int = 1) -> tuple[list, list]:
    """Send n requests through the fallback transport to a fake Groq that answers each key with
    its scripted status. Returns the responses and the (key, body) pairs Groq saw."""
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        key = request.headers["Authorization"].removeprefix("Bearer ")
        seen.append((key, request.content))
        return httpx.Response(statuses.get(key, 200), json={"key": key})

    async def run():
        transport = groq.FallbackTransport(ring, httpx.MockTransport(handler))
        async with httpx.AsyncClient(transport=transport) as http:
            return [await http.post("https://groq.test/", json={"n": i}) for i in range(n)]

    return asyncio.run(run()), seen


def test_no_keys_is_a_key_error():
    with pytest.raises(KeyError):
        groq.key_ring()


def test_keys_come_from_groq_api_keys_then_groq_api_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEYS", "k1, k2,your-groq-key")
    monkeypatch.setenv("GROQ_API_KEY", "k3")
    assert groq.key_ring().keys == ("k1", "k2", "k3")


def test_429_moves_to_the_next_key_and_resends_the_body():
    responses, seen = send(groq.KeyRing(("a", "b", "c")), {"a": 429})
    assert responses[0].json() == {"key": "b"}
    assert [k for k, _ in seen] == ["a", "b"]
    assert seen[0][1] == seen[1][1] == b'{"n":0}'


def test_the_working_key_stays_current():
    _, seen = send(groq.KeyRing(("a", "b")), {"a": 429}, n=2)
    assert [k for k, _ in seen] == ["a", "b", "b"]


def test_5xx_falls_back_but_400_does_not():
    responses, _ = send(groq.KeyRing(("a", "b")), {"a": 503})
    assert responses[0].status_code == 200
    responses, seen = send(groq.KeyRing(("a", "b")), {"a": 400})
    assert responses[0].status_code == 400 and [k for k, _ in seen] == ["a"]


def test_every_key_limited_tries_each_once_and_returns_the_429():
    responses, seen = send(groq.KeyRing(("a", "b", "c")), {"a": 429, "b": 429, "c": 429})
    assert responses[0].status_code == 429
    assert [k for k, _ in seen] == ["a", "b", "c"]


def test_a_switch_is_logged_by_key_number_never_by_key(caplog):
    send(groq.KeyRing(("secret-a", "secret-b")), {"secret-a": 429})
    assert "Groq key #1 returned 429; switching to key #2" in caplog.text
    assert "secret" not in caplog.text


def test_agent_model_is_groq_with_temperature_0_and_no_reasoning(monkeypatch):
    from agent.agent import build_model
    from agent.tools import Perception, Session
    from common.models import CollectionRequest

    monkeypatch.setenv("MOCK_LLM", "0")
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEYS", "k1")
    monkeypatch.setenv("GROQ_MODEL_ID", "qwen/test")
    monkeypatch.setenv("AGENT_TIMEOUT_S", "7")
    req = CollectionRequest(collector_id="kw-raju", locality="Seelampur",
                            photo_b64=base64.b64encode(b"fixture:1:PET:0.9").decode())
    m = build_model(Session(request=req, store=None, perception=Perception()))
    assert m.config["model_id"] == "qwen/test"
    assert m.config["params"] == {"temperature": 0, "reasoning_effort": "none"}
    args1, args2 = m._resolve_client_args(), m._resolve_client_args()
    assert args1["base_url"] == groq.BASE_URL and args1["timeout"] == 7 and args1["max_retries"] == 0
    assert args1["http_client"] is not args2["http_client"]  # Strands closes it after each request


def test_explainer_label_names_the_groq_model(monkeypatch):
    from radar import explain
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_MODEL_ID", "qwen/test")
    assert explain._model_label() == "groq:qwen/test"
