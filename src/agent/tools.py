"""The agent's tools, bound to one collection request (a Session).

Tools take no arguments from the model: they read the evidence from the session. The model chooses
which tool to call next, but it can never supply a weight, material or price. `create_receipt` is the
only write path, and it re-checks consistency and asks the policy layer before writing.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

from strands import tool

from agent import stub_tools
from agent.consistency import MATERIAL_GROUP, check_consistency as _check
from common.models import (
    CollectionRequest, ConsistencyResult, PhashResult, PhotoRead, PriceQuote, Receipt, Transcript,
)
from common.ports import ReceiptStore
from policy.authz import AGENT, is_allowed


@dataclass
class Perception:
    """Swap in P1's real functions here; signatures follow SCOPED_DOWN §3.3."""
    read_photo: Callable[[str], PhotoRead] = stub_tools.read_photo
    transcribe: Callable[[str], Transcript] = stub_tools.transcribe
    phash_check: Callable[[str, ReceiptStore], PhashResult] = stub_tools.phash_check
    quote_price: Callable[[str, float], PriceQuote] = stub_tools.quote_price


@dataclass
class Session:
    request: CollectionRequest
    store: ReceiptStore
    perception: Perception = field(default_factory=Perception)
    photo: Optional[PhotoRead] = None
    transcript: Optional[Transcript] = None
    phash: Optional[PhashResult] = None
    consistency: Optional[ConsistencyResult] = None
    price: Optional[PriceQuote] = None
    receipt: Optional[Receipt] = None
    trace: list[dict] = field(default_factory=list)

    def called(self) -> set[str]:
        return {t["tool"] for t in self.trace}

    def claim(self) -> tuple[Optional[float], Optional[str], str]:
        """(claimed_kg, claimed_material, source). Precedence: taps > voice > typed note."""
        req = self.request
        if req.taps and (req.taps.kg is not None or req.taps.material):
            return req.taps.kg, req.taps.material, "taps"
        if self.transcript:
            return self.transcript.claimed_kg, self.transcript.claimed_material, "voice"
        if req.text:
            return stub_tools.claim_from_text(req.text), None, "text"
        return None, None, "none"


def _record(session: Session, name: str, started: float, result: dict) -> None:
    session.trace.append({
        "step": len(session.trace) + 1,
        "tool": name,
        "ms": round((time.perf_counter() - started) * 1000, 1),
        "result": result,
    })


# ---------- plain functions (used by the tools and by the code-only fallback) ----------

def do_read_photo(s: Session) -> PhotoRead:
    if s.photo is None:
        t = time.perf_counter()
        s.photo = s.perception.read_photo(s.request.photo_b64)
        _record(s, "read_photo", t, s.photo.model_dump())
    return s.photo


def do_transcribe(s: Session) -> Optional[Transcript]:
    if s.transcript is None and s.request.audio_b64:
        t = time.perf_counter()
        s.transcript = s.perception.transcribe(s.request.audio_b64)
        _record(s, "transcribe", t, s.transcript.model_dump())
    return s.transcript


def do_phash_check(s: Session) -> PhashResult:
    if s.phash is None:
        t = time.perf_counter()
        s.phash = s.perception.phash_check(s.request.photo_b64, s.store)
        _record(s, "phash_check", t, s.phash.model_dump())
    return s.phash


def evaluate(s: Session) -> ConsistencyResult:
    """Recompute consistency from the evidence. Never cached for the write decision."""
    photo, phash = do_read_photo(s), do_phash_check(s)
    do_transcribe(s)
    kg, material, _ = s.claim()
    return _check(photo, phash, kg, material)


def do_check_consistency(s: Session) -> ConsistencyResult:
    t = time.perf_counter()
    s.consistency = evaluate(s)
    _record(s, "check_consistency", t, s.consistency.model_dump())
    return s.consistency


def do_quote_price(s: Session) -> PriceQuote:
    photo = do_read_photo(s)
    t = time.perf_counter()
    s.price = s.perception.quote_price(_final_material(s), photo.kg or 0.0)
    _record(s, "quote_price", t, s.price.model_dump())
    return s.price


def _final_material(s: Session) -> str:
    photo = do_read_photo(s)
    _, claimed, _ = s.claim()
    if claimed and (photo.material == "unknown" or MATERIAL_GROUP[claimed] == MATERIAL_GROUP[photo.material]):
        return claimed
    return photo.material


def guarded_create_receipt(s: Session) -> dict:
    """The ONLY write path. Writes iff consistency passes (in code) AND policy allows the agent."""
    t = time.perf_counter()
    if s.receipt is not None:
        result = {"written": True, "receipt_id": s.receipt.receipt_id, "note": "already written"}
        _record(s, "create_receipt", t, result)
        return result

    check = evaluate(s)
    decision = is_allowed(
        AGENT, "create_receipt",
        {"type": "Receipt", "collector": f'Actor::"{s.request.collector_id}"'},
        {"consistency_ok": check.ok},
    )
    if not (check.ok and decision.allowed):
        result = {"written": False, "refused": True, "reasons": check.reasons, "policy": decision.reason}
        _record(s, "create_receipt", t, result)
        return result

    photo = s.photo
    price = s.price or s.perception.quote_price(_final_material(s), photo.kg)
    kg, claimed_material, source = s.claim()
    fields = {
        "collector_id": s.request.collector_id,
        "material": _final_material(s),
        "weight_kg": photo.kg,
        "price_inr_per_kg": price.inr_per_kg,
        "locality": s.request.locality,
        "ts": datetime.now(timezone.utc),
        "photo_sha256": hashlib.sha256(s.request.photo_b64.encode("utf-8")).hexdigest(),
        "phash": s.phash.phash,
        "voice_text": s.transcript.text_hi if s.transcript else None,
        "evidence": {
            "photo": photo.model_dump(),
            "claim": {"kg": kg, "material": claimed_material, "source": source},
            "consistency": check.model_dump(),
            "price": price.model_dump(),
        },
        "synthetic": False,
    }
    s.receipt = s.store.append_receipt(fields)
    result = {"written": True, "receipt_id": s.receipt.receipt_id, "seq": s.receipt.seq,
              "hash": s.receipt.hash[:12]}
    _record(s, "create_receipt", t, result)
    return result


# ---------- Strands tools ----------

def build_tools(s: Session) -> list:
    @tool
    def read_photo() -> dict:
        """Read the weight (kg) and the material from the collector's scale photo."""
        return do_read_photo(s).model_dump()

    @tool
    def transcribe() -> dict:
        """Transcribe the collector's Hindi voice note and extract the weight and material they said."""
        tr = do_transcribe(s)
        return tr.model_dump() if tr else {"note": "no voice note in this collection"}

    @tool
    def phash_check() -> dict:
        """Check whether this photo was already used for an earlier receipt."""
        return do_phash_check(s).model_dump()

    @tool
    def check_consistency() -> dict:
        """Check the photo against the collector's claim. Returns ok, reasons and one Hindi question."""
        return do_check_consistency(s).model_dump()

    @tool
    def quote_price() -> dict:
        """Indicative price for this collection. Call only after check_consistency returned ok=true."""
        return do_quote_price(s).model_dump()

    @tool
    def create_receipt() -> dict:
        """Write the receipt. Refuses unless check_consistency passes; never call it after ok=false."""
        return guarded_create_receipt(s)

    return [read_photo, transcribe, phash_check, check_consistency, quote_price, create_receipt]


def format_trace(trace: list[dict]) -> str:
    """Tool-call table for the terminal (shown in the demo video)."""
    rows = [("#", "tool", "ms", "result")]
    for t in trace:
        r = t["result"]
        summary = ", ".join(f"{k}={v}" for k, v in r.items() if k not in {"evidence"})
        rows.append((str(t["step"]), t["tool"], f'{t["ms"]:.0f}', summary[:90]))
    w = [max(len(row[i]) for row in rows) for i in range(3)]
    lines = [f"{a:<{w[0]}}  {b:<{w[1]}}  {c:>{w[2]}}  {d}" for a, b, c, d in rows]
    lines.insert(1, "-" * max(len(line) for line in lines))
    return "\n".join(lines)
