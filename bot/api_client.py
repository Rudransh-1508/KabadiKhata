"""Real backend HTTP client — the Phase 2 swap for bot.mock_api.

Exposes the SAME surface as bot.mock_api (``collect``, ``hisaab``, ``register``)
and the SAME return shapes, so bot.telegram_bot swaps backends by rebinding its
module-level ``api`` (see telegram_bot.main). Selected when ``KK_USE_MOCK=0``.

Endpoint: ``KK_API_URL`` (default http://localhost:3000). Every call names the
caller in the ``X-Principal`` header (the API's stand-in for auth). Calls are
synchronous; the bot wraps them in ``asyncio.to_thread`` so the event loop is
never blocked.

The real API returns ``CollectionResult`` ({"status": "receipt"|"question",
"receipt", "question_hi", ...}) directly — the same shape the bot already
expects — so ``collect`` needs no reshaping. Only ``hisaab`` is adapted from
GET /receipts ({receipts, monthly, chain}) into the flat dict the income card
reads.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import httpx

BASE_URL = os.environ.get("KK_API_URL", "http://localhost:3000").rstrip("/")
TIMEOUT = float(os.environ.get("KK_API_TIMEOUT", "60"))  # CLAUDE.md #2: vision/audio need > 3s
IST = timezone(timedelta(hours=5, minutes=30))


def _headers(principal: str) -> dict:
    return {"X-Principal": principal}


def _today_ist_totals(receipts: list[dict]) -> tuple[float, float]:
    """Sum today's (India time) kg and ₹ from the receipt list."""
    today = datetime.now(IST).date().isoformat()
    kg_sum = inr_sum = 0.0
    for r in receipts:
        ts = str(r.get("ts", ""))
        try:
            d = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(IST).date().isoformat()
        except Exception:
            continue
        if d == today:
            kg = float(r.get("weight_kg", 0) or 0)
            kg_sum += kg
            inr_sum += kg * float(r.get("price_inr_per_kg", 0) or 0)
    return round(kg_sum, 2), round(inr_sum, 2)


def adapt_hisaab(data: dict, collector_id: str) -> dict:
    """GET /receipts payload -> the flat dict bot.cards.make_hisaab_card reads.

    ``name`` is left blank: the bot overrides it with the registered name."""
    receipts = data.get("receipts", []) or []
    monthly = data.get("monthly", []) or []
    chain = data.get("chain", {}) or {}
    latest = monthly[-1] if monthly else {"month": "This month", "count": 0, "weight_kg": 0.0, "total_inr": 0.0}
    today_kg, today_inr = _today_ist_totals(receipts)
    return {
        "collector_id": collector_id,
        "name": "",  # bot fills this from the registered name
        "month": latest.get("month", "This month"),
        "month_kg": round(float(latest.get("weight_kg", 0) or 0), 2),
        "month_inr": round(float(latest.get("total_inr", 0) or 0), 2),
        "count": latest.get("count", 0),
        "today_kg": today_kg,
        "today_inr": today_inr,
        "chain_verified": bool(chain.get("ok", True)),
        "synthetic": any(r.get("synthetic") for r in receipts),
    }


def register(collector_id: str, name: str, locality: str | None = None) -> dict:
    """The bot's /start: PUT /actors/{id} registers (or renames) a kabadiwala."""
    with httpx.Client(timeout=TIMEOUT) as c:
        resp = c.put(f"{BASE_URL}/actors/{collector_id}", headers=_headers(collector_id),
                     json={"name": name, "locality": locality})
        resp.raise_for_status()
        return resp.json()


def collect(payload: dict) -> dict:
    """POST /collections. Returns the CollectionResult unchanged
    ({"status": "receipt"|"question", ...}) — the shape the bot already expects.

    The mock's ``simulate`` key is ignored here: the bot drives the demo-refusal
    by sending a fixture photo (see telegram_bot.DEMO_FIXTURE_PHOTO), which the
    backend's deterministic read_photo decodes — the MOCK_LLM fallback path."""
    collector_id = payload["collector_id"]
    body = {
        "collector_id": collector_id,
        "photo_b64": payload.get("photo_b64") or "",
        "locality": payload.get("locality", ""),
        "taps": payload.get("taps"),
    }
    if payload.get("text"):
        body["text"] = payload["text"]
    if payload.get("audio_b64"):
        body["audio_b64"] = payload["audio_b64"]
    with httpx.Client(timeout=TIMEOUT) as c:
        resp = c.post(f"{BASE_URL}/collections", headers=_headers(collector_id), json=body)
        resp.raise_for_status()
        return resp.json()


def hisaab(collector_id: str) -> dict:
    """GET /receipts?collector_id=, adapted to the income-card shape."""
    with httpx.Client(timeout=TIMEOUT) as c:
        resp = c.get(f"{BASE_URL}/receipts", params={"collector_id": collector_id},
                     headers=_headers(collector_id))
        resp.raise_for_status()
        return adapt_hisaab(resp.json(), collector_id)
