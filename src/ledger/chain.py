"""Hash chain over one Kabadiwala's Receipts. Source of truth for hashing (CLAUDE.md).

The hash covers every Receipt field except `hash` and `receipt_id`; the ID is
derived from the hash, so it is checked separately. Floats are hashed at a
fixed 3 decimals and timestamps as UTC to the second, so the same Receipt
hashes the same on every machine. Editing any field, or rewriting one
Receipt's hash, breaks the chain at that Receipt or the next.
"""

import base64
import hashlib
import json
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel

from common.models import Receipt

GENESIS = "GENESIS"
IST = timezone(timedelta(hours=5, minutes=30), "IST")
_NOT_HASHED = {"hash", "receipt_id"}


class VerifyResult(BaseModel):
    ok: bool
    length: int
    broken_at_seq: int | None = None
    reason: str | None = None


def format_ts(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def month_ist(ts: datetime) -> str:
    """The calendar month a moment falls in, in India time ("YYYY-MM")."""
    return ts.astimezone(IST).strftime("%Y-%m")


def _canonical(value):
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, datetime):
        return format_ts(value)
    if isinstance(value, dict):
        return {k: _canonical(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_canonical(v) for v in value]
    return value


def compute_hash(receipt: Receipt) -> str:
    body = {k: v for k, v in receipt.model_dump().items() if k not in _NOT_HASHED}
    payload = json.dumps(_canonical(body), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def receipt_id_for(hash_hex: str) -> str:
    # 7 base32 characters = 35 bits, so IDs stay unique across thousands of Receipts
    return "KK-" + base64.b32encode(bytes.fromhex(hash_hex)).decode()[:7]


def seal(fields: dict, seq: int, prev_hash: str) -> Receipt:
    """Turn writer-supplied fields into a Receipt at position `seq`. Any chain fields passed in are replaced."""
    ts = fields["ts"]
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if ts.tzinfo is None:
        raise ValueError("ts must be timezone-aware")
    body = {
        **fields,
        "ts": ts.astimezone(timezone.utc).replace(microsecond=0),
        # Round-trip through JSON now so the stored evidence hashes the same when read back
        "evidence": json.loads(json.dumps(fields.get("evidence") or {}, default=str)),
        "seq": seq,
        "prev_hash": prev_hash,
        "hash": "",
        "receipt_id": "",
    }
    draft = Receipt(**body)
    h = compute_hash(draft)
    return draft.model_copy(update={"hash": h, "receipt_id": receipt_id_for(h)})


def verify(receipts: Iterable[Receipt]) -> VerifyResult:
    """Check a Chain given in seq order. Reports the first Receipt that doesn't hold."""
    expected_prev = GENESIS
    length = 0
    for expected_seq, r in enumerate(receipts):
        length += 1
        if r.seq != expected_seq:
            return VerifyResult(ok=False, length=length, broken_at_seq=expected_seq, reason="missing or reordered receipt")
        if r.prev_hash != expected_prev:
            return VerifyResult(ok=False, length=length, broken_at_seq=r.seq, reason="link to previous receipt broken")
        if compute_hash(r) != r.hash:
            return VerifyResult(ok=False, length=length, broken_at_seq=r.seq, reason="contents changed after writing")
        if receipt_id_for(r.hash) != r.receipt_id:
            return VerifyResult(ok=False, length=length, broken_at_seq=r.seq, reason="receipt ID does not match contents")
        expected_prev = r.hash
    return VerifyResult(ok=True, length=length)
