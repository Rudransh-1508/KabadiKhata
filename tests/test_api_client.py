"""Unit tests for the real backend client (bot/api_client.py).

The pure adapter is tested directly; the HTTP methods are tested against an
httpx.MockTransport, so no server is needed. A live end-to-end check runs
separately against `uv run uvicorn` with MOCK_LLM=1."""
from datetime import datetime

import httpx
import pytest

import bot.api_client as ac
from bot.api_client import IST, adapt_hisaab


def _mock_client(handler):
    """Return a drop-in for httpx.Client that routes through a MockTransport."""
    transport = httpx.MockTransport(handler)
    real = httpx.Client

    def factory(*args, **kwargs):
        kwargs.pop("timeout", None)
        return real(transport=transport)

    return factory


# ---------- pure adapter ----------

def test_adapt_hisaab_folds_latest_month_and_today():
    today_iso = datetime.now(IST).isoformat()
    data = {
        "receipts": [
            {"ts": today_iso, "weight_kg": 10.0, "price_inr_per_kg": 14.0, "synthetic": True},
            {"ts": "2026-01-01T00:00:00+05:30", "weight_kg": 99.0, "price_inr_per_kg": 10.0},
        ],
        "monthly": [
            {"month": "2026-09", "count": 1, "weight_kg": 5.0, "total_inr": 50.0},
            {"month": "2026-10", "count": 3, "weight_kg": 30.0, "total_inr": 420.0},
        ],
        "chain": {"ok": True, "length": 4},
    }
    out = adapt_hisaab(data, "kab_7")
    assert out["month"] == "2026-10"            # latest month, not the first
    assert out["month_inr"] == 420.0 and out["count"] == 3
    assert out["today_kg"] == 10.0 and out["today_inr"] == 140.0   # only today's receipt
    assert out["chain_verified"] is True
    assert out["synthetic"] is True
    assert out["name"] == ""                    # bot overrides with the registered name


def test_adapt_hisaab_empty_is_safe():
    out = adapt_hisaab({"receipts": [], "monthly": [], "chain": {}}, "kab_7")
    assert out["month_inr"] == 0 and out["count"] == 0 and out["today_kg"] == 0
    assert out["chain_verified"] is True        # nothing to break


# ---------- HTTP methods ----------

def test_collect_posts_with_principal_and_passes_result_through(monkeypatch):
    seen = {}

    def handler(request):
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["principal"] = request.headers.get("x-principal")
        return httpx.Response(200, json={"status": "receipt",
                                         "receipt": {"receipt_id": "KK-ABC123"}, "question_hi": None})

    monkeypatch.setattr(ac.httpx, "Client", _mock_client(handler))
    out = ac.collect({"collector_id": "kab_7", "photo_b64": "eA==", "locality": "okhla",
                      "taps": {"material": "PET", "kg": 5.0}})
    assert out["status"] == "receipt" and out["receipt"]["receipt_id"] == "KK-ABC123"
    assert seen == {"method": "POST", "path": "/collections", "principal": "kab_7"}


def test_hisaab_gets_receipts_and_adapts(monkeypatch):
    def handler(request):
        assert request.method == "GET" and request.url.path == "/receipts"
        assert request.url.params["collector_id"] == "kab_7"
        return httpx.Response(200, json={"receipts": [], "chain": {"ok": True},
                                         "monthly": [{"month": "2026-10", "count": 2,
                                                      "weight_kg": 20.0, "total_inr": 280.0}]})

    monkeypatch.setattr(ac.httpx, "Client", _mock_client(handler))
    out = ac.hisaab("kab_7")
    assert out["month_inr"] == 280.0 and out["count"] == 2 and out["chain_verified"] is True


def test_register_puts_actor(monkeypatch):
    def handler(request):
        assert request.method == "PUT" and request.url.path == "/actors/kab_7"
        return httpx.Response(200, json={"actor_id": "kab_7", "role": "kabadiwala", "name": "Raju"})

    monkeypatch.setattr(ac.httpx, "Client", _mock_client(handler))
    assert ac.register("kab_7", "Raju", "okhla")["actor_id"] == "kab_7"


def test_http_error_raises(monkeypatch):
    monkeypatch.setattr(ac.httpx, "Client",
                        _mock_client(lambda r: httpx.Response(403, json={"denied_by": "cedar"})))
    with pytest.raises(httpx.HTTPStatusError):
        ac.collect({"collector_id": "kab_7", "photo_b64": "", "locality": "okhla",
                    "taps": {"material": "PET", "kg": 5.0}})
