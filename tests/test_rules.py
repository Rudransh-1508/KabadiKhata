from datetime import datetime, timezone

import pytest

from common.models import Actor, Certificate
from ledger.store import Store
from ledger.world import load_world, sample_world, tamper
from radar import rules

SEP = datetime(2026, 9, 10, 6, 0, tzinfo=timezone.utc)


def receipt(collector, kg, recycler="rc-a", material="PET", phash="", day=10, i=0):
    return {
        "collector_id": collector, "material": material, "weight_kg": kg, "price_inr_per_kg": 18.0,
        "locality": "Seelampur", "ts": SEP.replace(day=day, minute=i), "photo_sha256": f"{i:064x}",
        "phash": phash, "recycler_id": recycler,
    }


def cert(cid, tonnes, recycler="rc-a", material="PET", month="2026-09", brand="br-1"):
    return Certificate(certificate_id=cid, recycler_id=recycler, brand_id=brand, month=month,
                       material=material, tonnes=tonnes)


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "kk.db")


def by_rule(flags, rule):
    return [f for f in flags if f.rule == rule]


def test_honest_recycler_is_not_flagged(store):
    for i in range(10):
        store.append_receipt(receipt("kw-raju", 100.0, i=i))  # 1 t in, supports 0.85 t
    store.put_certificate(cert("C1", 0.9))  # ratio 1.06
    assert rules.run(store) == []


@pytest.mark.parametrize("factor", [1.2, 1.5, 3.0, 38.0])
def test_over_claims_from_1_2x_are_flagged(store, factor):
    for i in range(10):
        store.append_receipt(receipt("kw-raju", 100.0, i=i))
    store.put_certificate(cert("C1", 0.85 * factor))
    (flag,) = by_rule(rules.run(store), "R1_mass_balance")
    assert flag.subject_id == "rc-a" and flag.score == pytest.approx(factor)
    assert flag.evidence_ids == ["C1"]


def test_certificates_for_one_recycler_material_month_are_added_up(store):
    store.append_receipt(receipt("kw-raju", 1000.0))
    store.put_certificate(cert("C1", 0.6, brand="br-1"))
    store.put_certificate(cert("C2", 0.6, brand="br-2"))  # 1.2 t against 0.85 t supported
    (flag,) = by_rule(rules.run(store), "R1_mass_balance")
    assert flag.evidence_ids == ["C1", "C2"]


def test_no_inflow_at_all_is_flagged(store):
    store.put_certificate(cert("C1", 5.0, recycler="rc-ghost"))
    (flag,) = by_rule(rules.run(store), "R1_mass_balance")
    assert flag.subject_id == "rc-ghost" and "no verified inflow" in flag.explanation_en


def test_receipts_after_a_break_stop_counting_as_inflow(store):
    for i in range(10):
        store.append_receipt(receipt("kw-raju", 100.0, i=i))
    store.put_certificate(cert("C1", 0.85))  # exactly backed
    assert by_rule(rules.run(store), "R1_mass_balance") == []
    tamper(store, "kw-raju", 5, {"weight_kg": 100.5})
    flags = rules.run(store)
    assert by_rule(flags, "R3_broken_chain")[0].subject_id == "kw-raju"
    assert by_rule(flags, "R1_mass_balance")[0].score == pytest.approx(2.0)  # only 5 of 10 still count


def test_month_is_india_time(store):
    # 19:00 UTC on Sep 30 is 00:30 on Oct 1 in India: not September inflow
    store.append_receipt(receipt("kw-raju", 1000.0) | {"ts": datetime(2026, 9, 30, 19, 0, tzinfo=timezone.utc)})
    store.put_certificate(cert("C1", 0.85, month="2026-09"))
    (flag,) = by_rule(rules.run(store), "R1_mass_balance")
    assert flag.explanation_en.endswith("(no verified inflow).")


def test_near_identical_photos_are_grouped(store):
    store.append_receipt(receipt("kw-raju", 10.0, phash="ffffffffffffffff", i=1))
    store.append_receipt(receipt("kw-sunita", 10.0, phash="fffffffffffffff0", i=2))  # 4 bits apart
    store.append_receipt(receipt("kw-imran", 10.0, phash="0000000000000000", i=3))
    (flag,) = by_rule(rules.run(store), "R2_duplicate_photo")
    assert flag.subject_id == "kw-raju,kw-sunita" and len(flag.evidence_ids) == 2


def test_hamming():
    assert rules.hamming("ff", "f0") == 4


def test_provenance_hides_identities_and_reports_backing(store):
    store.put_actor(Actor(actor_id="kw-raju", role="kabadiwala", name="Raju"))
    store.append_receipt(receipt("kw-raju", 1000.0))
    c = cert("C1", 1.7)  # 2x what 1 t can back
    store.put_certificate(c)
    p = rules.provenance(store, c)
    assert p["verified_backed_pct"] == 50.0
    assert p["by_locality"] == [{"locality": "Seelampur", "receipts": 1, "tonnes": 1.0}]
    assert "kw-raju" not in str(p) and "Raju" not in str(p)


def test_sample_world_flags_exactly_what_was_planted(store):
    counts = load_world(store, sample_world())
    assert counts["receipts"] > 1000 and counts["tampered"] == 1
    flags = rules.run(store)
    assert [f.subject_id for f in by_rule(flags, "R1_mass_balance")] == ["rc-c"]
    assert [f.subject_id for f in by_rule(flags, "R3_broken_chain")] == ["kw-sunita"]
    assert sum(len(f.evidence_ids) for f in by_rule(flags, "R2_duplicate_photo")) == 10
