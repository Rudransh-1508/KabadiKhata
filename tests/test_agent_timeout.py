"""Agent model timeout, turn cap and retry cap. Offline: no request is ever made."""
import base64
import json

import httpx
import pytest

import agent.agent as agent_mod
from agent.agent import MAX_AGENT_TURNS, _is_timeout, build_model, handle_collection
from agent.fakes import InMemoryReceiptStore
from agent.tools import Session, Perception
from common import config
from common.models import CollectionRequest, Taps


@pytest.fixture(autouse=True)
def keys(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("AGENT_TIMEOUT_S", raising=False)


def b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


def req(kg=12.0, material="PET"):
    return CollectionRequest(collector_id="raju", photo_b64=b64("fixture:12:PET:0.92"),
                             taps=Taps(material=material, kg=kg), locality="Seelampur")


def session():
    return Session(request=req(), store=InMemoryReceiptStore(), perception=Perception())


def test_agent_timeout_default_and_override(monkeypatch):
    assert config.agent_timeout_s() == 6.0
    monkeypatch.setenv("AGENT_TIMEOUT_S", "3.5")
    assert config.agent_timeout_s() == 3.5


@pytest.mark.parametrize("bad", ["abc", "0", "-1", "nan", "inf", ""])
def test_agent_timeout_rejects_bad_values(monkeypatch, bad):
    monkeypatch.setenv("AGENT_TIMEOUT_S", bad)
    assert config.agent_timeout_s() == 6.0


def test_build_model_gemini_passes_timeout_ms(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "0")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("AGENT_TIMEOUT_S", "4")
    m = build_model(session())
    assert m.client_args["http_options"]["timeout"] == 4000
    assert m.client_args["api_key"] == "test-key"
    assert m.config["params"] == {"temperature": 0}
    assert m.config["model_id"] == config.gemini_model_id()


def test_build_model_gemini_timeout_never_zero(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "0")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("AGENT_TIMEOUT_S", "0.0004")
    assert build_model(session()).client_args["http_options"]["timeout"] >= 1


def test_build_model_gemini_client_accepts_options(monkeypatch):
    types = pytest.importorskip("google.genai").types
    monkeypatch.setenv("MOCK_LLM", "0")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    m = build_model(session())
    assert types.HttpOptions(**m.client_args["http_options"]).timeout == 6000


def test_build_model_openai_passes_timeout_s(monkeypatch):
    pytest.importorskip("openai")
    monkeypatch.setenv("MOCK_LLM", "0")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("AGENT_TIMEOUT_S", "4")
    m = build_model(session())
    assert m.client_args["timeout"] == 4.0
    assert m.client_args["max_retries"] == 0


def test_build_model_mock_ignores_timeout(monkeypatch):
    from agent.scripted_model import ScriptedModel
    monkeypatch.setenv("MOCK_LLM", "1")
    monkeypatch.setenv("AGENT_TIMEOUT_S", "0.001")
    assert isinstance(build_model(session()), ScriptedModel)


def test_unknown_provider_still_raises_value_error(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "0")
    monkeypatch.setenv("LLM_PROVIDER", "nope")
    with pytest.raises(ValueError):
        build_model(session())


@pytest.mark.parametrize("provider,mid", [("gemini", "gemini_model_id"), ("openai", "openai_model_id")])
def test_build_model_unchanged_otherwise(monkeypatch, provider, mid):
    if provider == "openai":
        pytest.importorskip("openai")
    monkeypatch.setenv("MOCK_LLM", "0")
    monkeypatch.setenv("LLM_PROVIDER", provider)
    m = build_model(session())
    assert m.client_args["api_key"] == "test-key"
    assert m.config["model_id"] == getattr(config, mid)()
    assert m.config["params"] == {"temperature": 0}


class _Recorder:
    """Stand-in for strands.Agent that records its kwargs and returns a normal-looking result."""
    last_init = None
    last_call = None

    def __init__(self, **kw):
        type(self).last_init = kw

    def __call__(self, prompt, **kw):
        type(self).last_call = kw
        return type("R", (), {"stop_reason": "end_turn"})()


def test_retry_strategy_is_capped(monkeypatch):
    if agent_mod.ModelRetryStrategy is None:
        pytest.skip("strands retry strategy not importable")
    monkeypatch.setattr(agent_mod, "Agent", _Recorder)
    handle_collection(req(), InMemoryReceiptStore())
    strategy = _Recorder.last_init["retry_strategy"]
    assert isinstance(strategy, agent_mod.ModelRetryStrategy)
    assert strategy._max_attempts == 2


def test_turn_cap_is_passed_to_agent(monkeypatch):
    monkeypatch.setattr(agent_mod, "Agent", _Recorder)
    store = InMemoryReceiptStore()
    r = handle_collection(req(), store)
    assert _Recorder.last_call["limits"] == {"turns": MAX_AGENT_TURNS}
    assert r.status == "receipt" and len(store.receipts_for("raju")) == 1
    assert not any(t["tool"] == "llm_error" for t in r.trace)


def test_scripted_happy_path_fits_turn_cap(monkeypatch):
    from agent.scripted_model import ScriptedModel
    monkeypatch.setenv("MOCK_LLM", "1")
    calls = []
    real_stream = ScriptedModel.stream

    async def counting(self, *a, **kw):
        calls.append(1)
        async for ev in real_stream(self, *a, **kw):
            yield ev

    monkeypatch.setattr(ScriptedModel, "stream", counting)
    r = handle_collection(req(), InMemoryReceiptStore())
    assert r.status == "receipt"
    assert not any(t["tool"] == "llm_error" for t in r.trace)
    assert 0 < len(calls) <= MAX_AGENT_TURNS


def test_is_timeout_handles_cyclic_chain():
    a, b = RuntimeError("a"), RuntimeError("b")
    a.__cause__, b.__cause__ = b, a
    assert _is_timeout(a) is False
    try:
        try:
            raise TimeoutError("t")
        except TimeoutError as t:
            raise RuntimeError("wrapped") from t
    except RuntimeError as wrapped:
        assert _is_timeout(wrapped) is True


def _hung(monkeypatch, exc):
    """Make the agent's model call raise `exc`, through a stand-in Agent so the real except path runs."""
    class Hung:
        def __init__(self, **kw):
            pass

        def __call__(self, *a, **kw):
            raise exc

    monkeypatch.setattr(agent_mod, "Agent", Hung)


def llm_error(r):
    return next(t for t in r.trace if t["tool"] == "llm_error")


def test_timeout_exception_finishes_in_code_receipt(monkeypatch):
    _hung(monkeypatch, TimeoutError("hung"))
    store = InMemoryReceiptStore()
    r = handle_collection(req(), store)
    assert r.status == "receipt" and len(store.receipts_for("raju")) == 1
    e = llm_error(r)["result"]
    assert e["error"] == "TimeoutError" and "timed out" in e["note"]
    create = next(t for t in r.trace if t["tool"] == "create_receipt")
    assert "completed by code" in create["result"]["note"]


def test_timeout_exception_finishes_in_code_question(monkeypatch):
    _hung(monkeypatch, TimeoutError("hung"))
    store = InMemoryReceiptStore()
    r = handle_collection(req(kg=20.0), store)
    assert r.status == "question" and r.reasons == ["kg_mismatch"]
    assert store.receipts_for("raju") == []
    assert any(t["tool"] == "llm_error" for t in r.trace)
    assert not any(t["tool"] == "create_receipt" for t in r.trace)


def test_timeout_note_has_no_exception_message(monkeypatch):
    _hung(monkeypatch, TimeoutError("secret-token-123"))
    r = handle_collection(req(), InMemoryReceiptStore())
    assert "secret-token-123" not in json.dumps(r.trace, default=str)


def test_httpx_timeout_is_classified_as_timeout(monkeypatch):
    _hung(monkeypatch, httpx.ReadTimeout("x"))
    r = handle_collection(req(), InMemoryReceiptStore())
    assert "timed out" in llm_error(r)["result"]["note"]


def test_non_timeout_error_keeps_generic_note(monkeypatch):
    _hung(monkeypatch, RuntimeError("boom"))
    store = InMemoryReceiptStore()
    r = handle_collection(req(), store)
    assert llm_error(r)["result"]["note"] == "finished by code"
    assert r.status == "receipt"


def test_real_model_timeout_propagates_through_strands(monkeypatch):
    """A strands Model whose stream raises TimeoutError still reaches the except in handle_collection."""
    from strands.models.model import Model

    class HungModel(Model):
        def update_config(self, **kw):
            pass

        def get_config(self):
            return {}

        async def structured_output(self, *a, **kw):
            raise NotImplementedError
            yield

        async def stream(self, *a, **kw):
            raise TimeoutError("hung")
            yield

    monkeypatch.setattr(agent_mod, "build_model", lambda s: HungModel())
    r = handle_collection(req(), InMemoryReceiptStore())
    assert r.status == "receipt"
    assert any(t["tool"] == "llm_error" for t in r.trace)
