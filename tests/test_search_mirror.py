"""The OpenSearch copy. Live tests run only when OpenSearch is up (`make up`); the rest always run."""
import base64
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from api.app import app
from ledger.store import Store
from ledger.world import load_world, sample_world
from policy import directory
from search.mirror import Mirror, SearchUnavailable

URL = "http://localhost:9200"


def opensearch_up() -> bool:
    try:
        return Mirror(URL).client.ping()
    except Exception:  # noqa: BLE001 - any failure means "not up"
        return False


live = pytest.mark.skipif(not opensearch_up(), reason="OpenSearch not running (make up)")


def receipt_fields(i=0, collector="kw-raju"):
    return {
        "collector_id": collector, "material": "PET", "weight_kg": 10.0, "price_inr_per_kg": 18.0,
        "locality": "Seelampur", "ts": "2026-09-10T06:00:00+00:00", "photo_sha256": f"{i:064x}",
        "phash": "", "recycler_id": "rc-a",
    }


def test_ledger_writes_survive_opensearch_being_down(tmp_path):
    store = Store(tmp_path / "kk.db", mirror=Mirror("http://127.0.0.1:1"))
    started = time.monotonic()
    for i in range(5):
        store.append_receipt(receipt_fields(i))
    assert len(store.receipts_for("kw-raju")) == 5
    assert time.monotonic() - started < 5  # one failed attempt, then paused


def test_search_endpoints_answer_503_when_the_copy_is_off(tmp_path, monkeypatch):
    directory.register("au-1", "auditor")  # Cedar fails closed for unknown principals
    monkeypatch.setenv("KK_DB_PATH", str(tmp_path / "kk.db"))
    monkeypatch.setenv("KK_OPENSEARCH_URL", "")
    client = TestClient(app)
    assert client.get("/search/receipts", headers={"X-Principal": "au-1"}).status_code == 503
    assert client.get("/health").json()["search_copy"] is None


def test_unreachable_search_is_503_not_500(tmp_path, monkeypatch):
    directory.register("au-1", "auditor")  # Cedar fails closed for unknown principals
    monkeypatch.setenv("KK_DB_PATH", str(tmp_path / "kk.db"))
    monkeypatch.setenv("KK_OPENSEARCH_URL", "http://127.0.0.1:1")
    client = TestClient(app)
    assert client.get("/analytics/tonnage", headers={"X-Principal": "au-1"}).status_code == 503


@pytest.fixture
def mirror():
    m = Mirror(URL, index=f"receipts-test-{uuid.uuid4().hex[:8]}")
    yield m
    m.client.indices.delete(index=m.index, ignore_unavailable=True)


@live
def test_reindex_search_and_tonnage(tmp_path, mirror):
    store = Store(tmp_path / "kk.db")
    load_world(store, sample_world())
    assert mirror.reindex(store.all_receipts()) == len(store.all_receipts())
    hits = mirror.search_receipts("kw-raju")
    assert hits["total"] > 0 and all(r["collector_id"] == "kw-raju" for r in hits["receipts"])
    by_recycler = {}
    for row in mirror.tonnage("2026-09"):
        by_recycler[row["recycler_id"]] = by_recycler.get(row["recycler_id"], 0) + row["tonnes"]
    assert set(by_recycler) == {"rc-a", "rc-b", "rc-c"} and by_recycler["rc-a"] > by_recycler["rc-c"]


@live
def test_new_receipts_are_copied_and_searchable(tmp_path, mirror):
    store = Store(tmp_path / "kk.db", mirror=mirror)
    mirror.reindex([])
    r = store.append_receipt(receipt_fields(collector="kw-new"))
    mirror.client.indices.refresh(index=mirror.index)
    assert mirror.search_receipts(r.receipt_id)["receipts"][0]["receipt_id"] == r.receipt_id


@live
def test_search_api_through_a_live_collection(tmp_path, monkeypatch, mirror):
    directory.register("au-1", "auditor")  # Cedar fails closed for unknown principals
    directory.register("kw-raju", "kabadiwala")
    monkeypatch.setenv("MOCK_LLM", "1")
    monkeypatch.setenv("KK_DB_PATH", str(tmp_path / "kk.db"))
    monkeypatch.setenv("KK_PHOTO_DIR", str(tmp_path / "photos"))
    monkeypatch.setenv("KK_OPENSEARCH_URL", URL)
    monkeypatch.setenv("KK_OPENSEARCH_INDEX", mirror.index)
    mirror.reindex([])
    client = TestClient(app)
    photo = base64.b64encode(b"fixture:12:PET:0.92:search").decode()
    body = client.post("/collections", headers={"X-Principal": "kw-raju"}, json={
        "collector_id": "kw-raju", "photo_b64": photo, "taps": {"material": "PET", "kg": 12}, "locality": "Seelampur",
    }).json()
    assert body["status"] == "receipt", body
    mirror.client.indices.refresh(index=mirror.index)
    found = client.get("/search/receipts", params={"q": "seelampur"}, headers={"X-Principal": "au-1"}).json()
    assert [r["receipt_id"] for r in found["receipts"]] == [body["receipt"]["receipt_id"]]


def test_reindex_raises_when_down():
    with pytest.raises(SearchUnavailable):
        Mirror("http://127.0.0.1:1").reindex([])
