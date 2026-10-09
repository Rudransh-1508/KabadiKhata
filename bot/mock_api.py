"""Mock of the backend API, so the bot and console can be built before P3's
real API exists.

The functions here mirror the real endpoint contract from
KABADI_KHATA_SCOPED_DOWN.md §3.2. At M1 we swap this module for a thin HTTP
client that hits `sam local` (same return shapes) by flipping KK_USE_MOCK.

    POST /collections -> collect(payload)
    GET  /receipts?collector_id= (summary) -> hisaab(collector_id)
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import random
from pathlib import Path

_DATA = Path(__file__).resolve().parent.parent / "data"
_RATES = json.loads((_DATA / "ratecard.json").read_text(encoding="utf-8"))["rates"]


def _price(material: str, kg: float) -> tuple[float, float]:
    entry = _RATES.get(material, _RATES["unknown"])
    rate = float(entry["inr_per_kg"])
    return rate, round(rate * kg, 2)


def _new_receipt_id() -> str:
    return "KK-" + hashlib.sha256(os.urandom(8)).hexdigest()[:6].upper()


def collect(payload: dict) -> dict:
    """Mock POST /collections.

    Returns either:
        {"status": "receipt", "receipt": {...}}
        {"status": "question", "question_hi": "..."}

    Demo control: pass payload["simulate"] = "mismatch" to exercise the refusal
    path (the agent asks one Hinglish question and writes nothing). Otherwise a
    receipt is built from the taps/voice so the happy path looks real.
    """
    if payload.get("simulate") == "mismatch":
        # Pretend the photo read 12 kg and compare to what the user actually
        # entered, so the refusal uses the REAL tapped weight (not a fixed "20").
        taps = payload.get("taps") or {}
        claimed = taps.get("kg") if taps.get("kg") is not None else payload.get("kg")
        claimed_str = f"{float(claimed):g}" if isinstance(claimed, (int, float)) else "?"
        return {
            "status": "question",
            "question_hi": f"Taraazu 12 kilo dikha raha hai, aapne {claimed_str} kilo bola. Kaun sa sahi hai?",
        }

    taps = payload.get("taps") or {}
    material = taps.get("material") or payload.get("material") or "unknown"
    kg = float(taps.get("kg") or payload.get("kg") or 0)
    rate, total = _price(material, kg)
    rid = _new_receipt_id()
    receipt = {
        "receipt_id": rid,
        "collector_id": payload.get("collector_id", "kab_demo"),
        "seq": random.randint(1, 50),
        "material": material,
        "weight_kg": kg,
        "price_inr_per_kg": rate,
        "total_inr": total,  # convenience field for the card; real receipt recomputes
        "locality": payload.get("locality", "lajpat_nagar"),
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "photo_sha256": "mock",
        "phash": "0f0f0f0f0f0f0f0f",
        "voice_text": payload.get("voice_text"),
        "evidence": {
            "consistency": {"ok": True, "reasons": []},
            "confidence": 0.9,
            "mock": True,
        },
        "recycler_id": None,
        "prev_hash": "GENESIS",
        "hash": hashlib.sha256(rid.encode()).hexdigest(),
        "synthetic": True,
    }
    return {"status": "receipt", "receipt": receipt}


def register(collector_id: str, name: str, locality: str | None = None) -> dict:
    """Mock PUT /actors/{id}: no backend, just echo the actor (parity with api_client)."""
    return {"actor_id": collector_id, "role": "kabadiwala", "name": name, "locality": locality}


def hisaab(collector_id: str) -> dict:
    """Mock GET /receipts?collector_id= summary (for the 'Mera Hisaab' button)."""
    return {
        "collector_id": collector_id,
        "name": "Raju",
        "today_kg": 37.0,
        "today_inr": 505.0,
        "month_kg": 842.0,
        "month_inr": 11230.0,
        "count": 63,
        "chain_verified": True,
        "synthetic": True,
    }
