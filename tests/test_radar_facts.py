from datetime import datetime, timezone

import pytest

from common.models import Actor, Certificate, Flag
from ledger.store import Store
from ledger.world import tamper
from radar import rules
from radar.facts import derive_facts

SEP = datetime(2026, 9, 10, 6, 0, tzinfo=timezone.utc)


def receipt(collector, kg, recycler="rc-a", material="PET", phash="", i=0, synthetic=True):
    return {
        "collector_id": collector, "material": material, "weight_kg": kg, "price_inr_per_kg": 18.0,
        "locality": "Seelampur", "ts": SEP.replace(minute=i), "photo_sha256": f"{i:064x}",
        "phash": phash, "recycler_id": recycler, "synthetic": synthetic,
    }


def cert(cid, tonnes, recycler="rc-a", material="PET", month="2026-09", brand="br-1"):
    return Certificate(certificate_id=cid, recycler_id=recycler, brand_id=brand, month=month,
                       material=material, tonnes=tonnes)


@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path / "kk.db")
    s.put_actor(Actor(actor_id="rc-a", role="recycler", name="Recycler A"))
    return s


def fill(store, collector="kw-raju", n=10, kg=100.0, offset=0, **kw):
    for i in range(n):
        store.append_receipt(receipt(collector, kg, i=offset + i, **kw))


def r1(store):
    (flag,) = [f for f in rules.r1_mass_balance(store, rules.verified_receipts(store))]
    return flag


def test_r1_facts_match_rule_numbers(store):
    fill(store)
    store.put_certificate(cert("C1", 2.0))
    f = derive_facts(r1(store), store)
    assert f["recycler_id"] == "rc-a" and f["recycler_name"] == "Recycler A"
    assert f["month"] == "2026-09" and f["material"] == "PET"
    assert f["certificate_tonnes"] == pytest.approx(2.0)
    assert f["verified_inflow_tonnes"] == pytest.approx(1.0)
    assert f["ratio"] == pytest.approx(2.0 / 0.85)


@pytest.mark.parametrize("factor", [1.2, 1.5, 3.0, 38.0])
def test_r1_ratio_equals_flag_score(store, factor):
    fill(store)
    store.put_certificate(cert("C1", 0.85 * factor))
    flag = r1(store)
    assert derive_facts(flag, store)["ratio"] == pytest.approx(flag.score)


def test_r1_no_inflow_gives_ratio_none(store):
    store.put_certificate(cert("C1", 5.0))
    f = derive_facts(r1(store), store)
    assert f["ratio"] is None and f["verified_inflow_tonnes"] == 0.0
    assert "synthetic" not in f  # no Receipts behind the key, so nothing to label


def test_r1_excluded_tonnes_and_collectors_after_chain_break(store):
    fill(store)                                      # kw-raju: 10 x 100 kg to rc-a
    fill(store, "kw-sita", n=4, kg=50.0, offset=20)  # intact Chain
    fill(store, "kw-raju", n=1, kg=70.0, offset=40, recycler="rc-b")  # other Recycler, seq 10
    store.put_certificate(cert("C1", 5.0))
    tamper(store, "kw-raju", 6, {"weight_kg": 101.0})
    f = derive_facts(r1(store), store)
    # seq 6..9 of kw-raju sold to rc-a (the tampered one is stored as 101 kg); seq 10 went elsewhere
    assert f["excluded_tonnes"] == pytest.approx((101.0 + 3 * 100.0) / 1000)
    assert f["excluded_collector_ids"] == ["kw-raju"]
    assert f["verified_inflow_tonnes"] == pytest.approx((600.0 + 200.0) / 1000)


def test_r1_excluded_zero_when_chains_intact(store):
    fill(store)
    store.put_certificate(cert("C1", 5.0))
    f = derive_facts(r1(store), store)
    assert f["excluded_tonnes"] == 0.0 and f["excluded_collector_ids"] == []


def test_r2_facts_ids_collectors_max_hamming(store):
    store.append_receipt(receipt("kw-raju", 10.0, phash="0" * 16, i=0))
    store.append_receipt(receipt("kw-sita", 10.0, phash="0" * 15 + "3", i=1))
    store.append_receipt(receipt("kw-sita", 10.0, phash="0" * 15 + "1", i=2))
    (flag,) = rules.r2_duplicate_photos(store.all_receipts())
    f = derive_facts(flag, store)
    assert f["receipt_ids"] == sorted(flag.evidence_ids)
    assert f["collector_ids"] == ["kw-raju", "kw-sita"]
    assert f["max_hamming"] == 2 and f["synthetic"] is True


def test_r3_facts_collector_and_broken_seq(store):
    fill(store)
    tamper(store, "kw-raju", 4, {"weight_kg": 101.0})
    (flag,) = rules.r3_broken_chains(store, rules.chain_status(store))
    f = derive_facts(flag, store)
    assert f["collector_id"] == "kw-raju" and f["broken_seq"] == 4
    assert f["receipt_id"] == flag.evidence_ids[0] and f["synthetic"] is True


def test_facts_empty_when_evidence_missing(store):
    fill(store)
    store.put_certificate(cert("C1", 5.0))
    bad_r1 = r1(store).model_copy(update={"evidence_ids": ["C1", "C-NOPE"]})
    assert derive_facts(bad_r1, store) == {}
    bad_r2 = Flag(flag_id="R2:x", rule="R2_duplicate_photo", subject_id="kw-raju", score=2.0,
                  evidence_ids=["KK-NOPE1", "KK-NOPE2"])
    assert derive_facts(bad_r2, store) == {}


def test_derive_facts_does_not_write(store):
    fill(store)
    store.put_certificate(cert("C1", 5.0))
    flag = r1(store)
    before = ([r.model_dump() for r in store.all_receipts()], store.list_certificates())
    derive_facts(flag, store)
    assert before == ([r.model_dump() for r in store.all_receipts()], store.list_certificates())


def test_synthetic_only_when_all_receipts_synthetic(store):
    fill(store, n=5)
    fill(store, "kw-sita", n=1, offset=30, synthetic=False)
    store.put_certificate(cert("C1", 5.0))
    assert "synthetic" not in derive_facts(r1(store), store)
