"""Interfaces between owners. P3's store (SQLite / OpenSearch) must satisfy ReceiptStore."""
from __future__ import annotations

from typing import Optional, Protocol

from common.models import Receipt


class ReceiptStore(Protocol):
    def append_receipt(self, fields: dict) -> Receipt:
        """Append to `fields["collector_id"]`'s chain. The store assigns seq, prev_hash and hash."""
        ...

    def receipts_for(self, collector_id: str) -> list[Receipt]:
        """All receipts for one collector, ordered by seq."""
        ...

    def find_receipt_by_phash(self, phash: str) -> Optional[str]:
        """receipt_id of a receipt with this exact phash, or None. (P1's real check uses Hamming distance.)"""
        ...
