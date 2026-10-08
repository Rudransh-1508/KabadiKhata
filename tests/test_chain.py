import sqlite3
import threading
from datetime import datetime, timedelta, timezone

import pytest

from ledger import chain
from ledger.chain import month_ist
from ledger.store import Store

T0 = datetime(2026, 10, 9, 6, 0, tzinfo=timezone.utc)


def draft(collector="kw-raju", i=0, **overrides) -> dict:
    fields = {
        "collector_id": collector,
        "material": "PET",
        "weight_kg": 12.0 + i / 1000,
        "price_inr_per_kg": 18.0,
        "locality": "Lajpat Nagar",
        "ts": T0 + timedelta(minutes=i, microseconds=123),
        "photo_sha256": f"{i:064x}",
        "phash": "",
        "evidence": {"photo_kg": 12.0, "confidence": 0.93, "read_at": T0},
    }
    return fields | overrides


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "kk.db")


def tamper(store: Store, sql: str, params: tuple) -> None:
    con = sqlite3.connect(store.path)
    con.execute(sql, params)
    con.commit()
    con.close()


def test_append_100_then_verify(store):
    for i in range(100):
        store.append_receipt(draft(i=i))
    result = chain.verify(store.receipts_for("kw-raju"))
    assert result.ok and result.length == 100


def test_first_receipt_links_to_genesis(store):
    r = store.append_receipt(draft())
    assert r.seq == 0 and r.prev_hash == chain.GENESIS
    assert r.receipt_id == chain.receipt_id_for(r.hash)


def test_chains_are_per_kabadiwala(store):
    store.append_receipt(draft("kw-raju"))
    other = store.append_receipt(draft("kw-sunita"))
    assert other.seq == 0


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE receipts SET weight_kg = 99.0 WHERE seq = ?",
        "UPDATE receipts SET evidence = '{\"photo_kg\": 99}' WHERE seq = ?",
        "UPDATE receipts SET synthetic = 1 WHERE seq = ?",
        "UPDATE receipts SET receipt_id = 'KK-FORGED' WHERE seq = ?",
    ],
)
def test_any_edit_breaks_chain_at_that_seq(store, sql):
    for i in range(100):
        store.append_receipt(draft(i=i))
    tamper(store, sql, (42,))
    result = chain.verify(store.receipts_for("kw-raju"))
    assert not result.ok
    assert result.broken_at_seq == 42


def test_rehashing_an_edited_receipt_breaks_the_next_link(store):
    for i in range(5):
        store.append_receipt(draft(i=i))
    original = store.receipts_for("kw-raju")[2]
    forged = chain.seal(original.model_dump() | {"weight_kg": 99.0}, 2, original.prev_hash)
    tamper(
        store,
        "UPDATE receipts SET weight_kg = ?, hash = ?, receipt_id = ? WHERE seq = 2",
        (forged.weight_kg, forged.hash, forged.receipt_id),
    )
    result = chain.verify(store.receipts_for("kw-raju"))
    assert result.broken_at_seq == 3


def test_deleted_receipt_is_detected(store):
    for i in range(5):
        store.append_receipt(draft(i=i))
    tamper(store, "DELETE FROM receipts WHERE seq = ?", (2,))
    assert chain.verify(store.receipts_for("kw-raju")).broken_at_seq == 2


def test_concurrent_appends_never_share_a_seq(store):
    errors = []

    def worker(n):
        try:
            for i in range(10):
                store.append_receipt(draft(i=n * 100 + i))
        except Exception as e:  # noqa: BLE001 - surfaced by the assert below
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    result = chain.verify(store.receipts_for("kw-raju"))
    assert result.ok and result.length == 50


def test_naive_timestamp_rejected(store):
    with pytest.raises(ValueError):
        store.append_receipt(draft(ts=datetime(2026, 10, 9, 6, 0)))  # noqa: DTZ001 - naive on purpose


def test_chain_fields_from_the_writer_are_ignored(store):
    r = store.append_receipt(draft(seq=99, prev_hash="x", hash="y", receipt_id="KK-MINE"))
    assert r.seq == 0 and r.prev_hash == chain.GENESIS and r.receipt_id != "KK-MINE"


def test_find_receipt_by_phash(store):
    r = store.append_receipt(draft(phash="abcd"))
    assert store.find_receipt_by_phash("abcd") == r.receipt_id
    assert store.find_receipt_by_phash("") is None


def test_month_is_decided_in_india_time():
    # 00:30 on Nov 1 in India is still Oct 31 in UTC
    assert month_ist(datetime(2026, 10, 31, 19, 0, tzinfo=timezone.utc)) == "2026-11"
