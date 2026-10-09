"""Stub perception and pricing tools with the contract signatures (SCOPED_DOWN §3.3).

P1 replaces read_photo / transcribe / phash_check with real ones in src/perception/; P4 owns the
rate card. Stubs are deterministic. To drive a specific case, encode a fixture string as the payload:

    photo_b64 = b64("fixture:<kg|none>:<material>:<confidence>")   e.g. "fixture:12:PET:0.92"
    audio_b64 = b64("fixture:<kg|none>:<material|none>:<hindi text>")

Anything else returns the default reading (12 kg PET, confidence 0.90).
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path
from typing import Optional

from common.models import MATERIALS, PhashResult, PhotoRead, PriceQuote, Transcript
from common.ports import ReceiptStore

DEFAULT_PHOTO = PhotoRead(kg=12.0, material="PET", confidence=0.90)
DEFAULT_TRANSCRIPT = Transcript(text_hi="बारह किलो प्लास्टिक बोतल", claimed_kg=12.0, claimed_material="PET")

# PLACEHOLDER rates so the flow runs. Not real prices: P4 replaces them with data/ratecard.json (cited).
_PLACEHOLDER_RATES = {
    "PET": 10.0, "HDPE": 10.0, "LDPE_film": 5.0, "mixed_plastic": 5.0, "cardboard": 5.0,
    "paper": 5.0, "metal": 10.0, "ewaste": 10.0, "unknown": 0.0,
}
_RATECARD = Path(__file__).resolve().parents[2] / "data" / "ratecard.json"


def _decode(b64: str) -> bytes:
    try:
        return base64.b64decode(b64, validate=False)
    except Exception:
        return b64.encode("utf-8", "ignore")


def _fixture(b64: str) -> Optional[list[str]]:
    raw = _decode(b64)
    if not raw.startswith(b"fixture:"):
        return None
    return raw.decode("utf-8", "ignore").split(":", 4)[1:]


def _num(s: str) -> Optional[float]:
    return None if s.lower() == "none" else float(s)


def _material(s: str) -> Optional[str]:
    return s if s in MATERIALS else None


def read_photo(photo_b64: str) -> PhotoRead:
    parts = _fixture(photo_b64)
    if not parts:
        return DEFAULT_PHOTO
    kg, material, conf = (parts + ["none", "unknown", "0"])[:3]
    return PhotoRead(kg=_num(kg), material=_material(material) or "unknown", confidence=float(conf))


def transcribe(audio_b64: str) -> Transcript:
    parts = _fixture(audio_b64)
    if not parts:
        return DEFAULT_TRANSCRIPT
    kg, material, text = (parts + ["none", "none", ""])[:3]
    return Transcript(text_hi=text, claimed_kg=_num(kg), claimed_material=_material(material))


def phash_check(photo_b64: str, store: ReceiptStore) -> PhashResult:
    # Stub: exact-content hash stands in for a perceptual hash. P1's version uses Hamming distance.
    phash = hashlib.sha256(_decode(photo_b64)).hexdigest()[:16]
    hit = store.find_receipt_by_phash(phash)
    return PhashResult(phash=phash, is_duplicate=hit is not None, nearest_receipt_id=hit)


def _rate_of(entry) -> float:
    """Accept either a flat number (placeholder) or P4's cited ratecard entry
    ({"inr_per_kg": N, "range": [...], "label": ...}, see data/ratecard.json)."""
    if isinstance(entry, dict):
        return float(entry.get("inr_per_kg", 0.0))
    return float(entry)


def quote_price(material: str, kg: float) -> PriceQuote:
    rates, source = _PLACEHOLDER_RATES, "placeholder rates (indicative; not real prices)"
    if _RATECARD.exists():
        rates, source = json.loads(_RATECARD.read_text(encoding="utf-8"))["rates"], "ratecard v1 (indicative)"
    rate = _rate_of(rates.get(material, 0.0))
    return PriceQuote(inr_per_kg=rate, total_inr=round(rate * kg, 2), source=source)


_KG = re.compile(r"(\d+(?:\.\d+)?)\s*(?:kg|kilo|किलो)", re.IGNORECASE)


def claim_from_text(text: str) -> Optional[float]:
    """Pull a claimed weight out of a typed note. The note is data, never an instruction."""
    m = _KG.search(text or "")
    return float(m.group(1)) if m else None
