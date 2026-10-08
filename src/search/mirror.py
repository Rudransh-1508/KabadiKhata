"""A read-only copy of the Receipts in OpenSearch, for the auditor's search and tonnage charts.

SQLite is the ledger: the chain, the tamper check and the fraud rules read only
SQLite. This copy is best effort. If OpenSearch is down, writes skip it with a
warning and searches answer 503; `make reindex` rebuilds it from SQLite.
"""

import logging
import os
import time

from opensearchpy import OpenSearch, helpers
from opensearchpy.exceptions import OpenSearchException

from common.models import Receipt
from ledger import chain

log = logging.getLogger("kk.search")

INDEX = "receipts"
RETRY_AFTER_S = 30

MAPPING = {
    "settings": {"number_of_shards": 1, "number_of_replicas": 0},
    "mappings": {
        "properties": {
            "receipt_id": {"type": "keyword"},
            "collector_id": {"type": "keyword"},
            "seq": {"type": "integer"},
            "material": {"type": "keyword"},
            "weight_kg": {"type": "float"},
            "price_inr_per_kg": {"type": "float"},
            "locality": {"type": "keyword"},
            "ts": {"type": "date"},
            "month": {"type": "keyword"},
            "recycler_id": {"type": "keyword"},
            "synthetic": {"type": "boolean"},
            "phash": {"type": "keyword"},
            "photo_sha256": {"type": "keyword"},
        },
        # Evidence and hashes stay in SQLite; the copy only needs what the console searches and charts
        "dynamic": False,
    },
}


class SearchUnavailable(Exception):
    pass


def _doc(r: Receipt) -> dict:
    return {**r.model_dump(mode="json"), "month": chain.month_ist(r.ts)}


class Mirror:
    def __init__(self, url: str, index: str = INDEX):
        self.url = url
        self.index = index
        self.client = OpenSearch(hosts=[url], timeout=2, max_retries=0)
        self._down_until = 0.0

    def _skip(self) -> bool:
        return time.monotonic() < self._down_until

    def _mark_down(self, exc: Exception) -> None:
        log.warning("OpenSearch at %s unavailable (%s); search copy paused for %ss", self.url, exc, RETRY_AFTER_S)
        self._down_until = time.monotonic() + RETRY_AFTER_S

    def index_receipt(self, r: Receipt) -> None:
        """Copy one Receipt. Never raises: the ledger write has already succeeded."""
        if self._skip():
            return
        try:
            self.client.index(index=self.index, id=r.receipt_id, body=_doc(r))
        except (OpenSearchException, OSError) as exc:
            self._mark_down(exc)

    def reindex(self, receipts: list[Receipt]) -> int:
        """Rebuild the copy from the ledger. Raises if OpenSearch is unreachable."""
        try:
            if self.client.indices.exists(index=self.index):
                self.client.indices.delete(index=self.index)
            self.client.indices.create(index=self.index, body=MAPPING)
            ok, _ = helpers.bulk(
                self.client,
                ({"_index": self.index, "_id": r.receipt_id, "_source": _doc(r)} for r in receipts),
                refresh=True,
            )
        except (OpenSearchException, OSError) as exc:
            raise SearchUnavailable(str(exc)) from exc
        self._down_until = 0.0
        return ok

    def _search(self, body: dict) -> dict:
        if self._skip():
            raise SearchUnavailable(f"OpenSearch at {self.url} is paused after a failure")
        try:
            return self.client.search(index=self.index, body=body)
        except (OpenSearchException, OSError) as exc:
            self._mark_down(exc)
            raise SearchUnavailable(str(exc)) from exc

    def search_receipts(self, q: str | None = None, *, recycler_id: str | None = None,
                        material: str | None = None, month: str | None = None, size: int = 50) -> dict:
        filters = [
            {"term": {field: value}}
            for field, value in (("recycler_id", recycler_id), ("material", material), ("month", month))
            if value
        ]
        must = []
        if q:
            # Wildcard per keyword field: IDs like "kw-raju" would be split by query_string
            must.append({"bool": {"minimum_should_match": 1, "should": [
                {"wildcard": {field: {"value": f"*{q}*", "case_insensitive": True}}}
                for field in ("receipt_id", "collector_id", "locality", "material", "recycler_id")
            ]}})
        res = self._search({
            "size": size,
            "sort": [{"ts": "desc"}],
            "query": {"bool": {"must": must or [{"match_all": {}}], "filter": filters}},
        })
        return {"total": res["hits"]["total"]["value"], "receipts": [h["_source"] for h in res["hits"]["hits"]]}

    def tonnage(self, month: str | None = None) -> list[dict]:
        """Recorded tonnes by recycler and material. Recorded, not verified: R1 uses the ledger."""
        res = self._search({
            "size": 0,
            "query": {"bool": {"filter": [{"term": {"month": month}}] if month else []}},
            "aggs": {"recycler": {
                "terms": {"field": "recycler_id", "size": 100},
                "aggs": {"material": {
                    "terms": {"field": "material", "size": 20},
                    "aggs": {"kg": {"sum": {"field": "weight_kg"}}},
                }},
            }},
        })
        return [
            {"recycler_id": rb["key"], "material": mb["key"], "receipts": mb["doc_count"],
             "tonnes": round(mb["kg"]["value"] / 1000, 3)}
            for rb in res["aggregations"]["recycler"]["buckets"]
            for mb in rb["material"]["buckets"]
        ]


def mirror_from_env() -> Mirror | None:
    url = os.getenv("KK_OPENSEARCH_URL", "").strip()
    return Mirror(url, os.getenv("KK_OPENSEARCH_INDEX", INDEX)) if url else None
