"""In-memory ReceiptStore so the agent runs before P3's store lands.

Hashing follows CLAUDE.md (canonical JSON, sorted keys, fixed float format, UTC ISO timestamps,
"GENESIS" for seq 0). P3's `ledger/chain.py` is the source of truth; delete this once it exists.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from common.models import Receipt

GENESIS = "GENESIS"


def _canonical(value):
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, dict):
        return {k: _canonical(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_canonical(v) for v in value]
    return value


def compute_hash(fields: dict, prev_hash: str) -> str:
    body = {k: v for k, v in fields.items() if k != "hash"}
    payload = json.dumps(_canonical(body), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256((payload + prev_hash).encode("utf-8")).hexdigest()


class InMemoryReceiptStore:
    def __init__(self) -> None:
        self._chains: dict[str, list[Receipt]] = {}

    def append_receipt(self, fields: dict) -> Receipt:
        chain = self._chains.setdefault(fields["collector_id"], [])
        seq = len(chain)
        prev_hash = chain[-1].hash if chain else GENESIS
        body = {**fields, "seq": seq, "prev_hash": prev_hash}
        if not body.get("receipt_id"):
            seed = f'{body["collector_id"]}:{seq}:{body.get("photo_sha256", "")}'
            body["receipt_id"] = "KK-" + hashlib.sha256(seed.encode()).hexdigest()[:6].upper()
        # Hash the full normalized record (defaults included), exactly what verify() will see later.
        draft = Receipt(**{**body, "hash": ""})
        receipt = draft.model_copy(update={"hash": compute_hash(draft.model_dump(), prev_hash)})
        chain.append(receipt)
        return receipt

    def receipts_for(self, collector_id: str) -> list[Receipt]:
        return list(self._chains.get(collector_id, []))

    def find_receipt_by_phash(self, phash: str) -> Optional[str]:
        for chain in self._chains.values():
            for r in chain:
                if r.phash == phash:
                    return r.receipt_id
        return None
