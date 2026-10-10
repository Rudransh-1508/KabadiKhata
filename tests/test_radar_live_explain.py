import json
import socket
from datetime import datetime, timezone

import pytest

from common.models import Certificate, Flag
from ledger.store import Store
from ledger.world import load_world, sample_world, tamper
from policy.directory import register  # noqa: F401  (conftest registers auditor-1)
from radar import explain, rules
from radar.decisions import decide_flag
from radar.explain import with_llm_explanation

SEP = datetime(2026, 9, 10, 6, 0, tzinfo=timezone.utc)
AUDITOR = 'Actor::"auditor-1"'

GOOD_EN = ("Recycler A issued Certificates for 5.00 tonnes of PET in 2026-09 against 0.50 tonnes of Verified inflow. "
           "The Over-claim ratio is 11.8x, see Certificate C1. "
           "Receipts from Kabadiwala kw-raju were left out because their Chain is broken, so check the R3 Flag first. This is synthetic demo data.")
GOOD_HI = ("रीसाइक्लर Recycler A ने 2026-09 में PET के 5.00 टन के प्रमाणपत्र जारी किए, जबकि सत्यापित आवक 0.50 टन है। "
           "ओवर-क्लेम अनुपात 11.8 गुना है, प्रमाण C1। "
           "कबाड़ीवाला kw-raju की रसीदें, जिनकी चेन टूटी है, छोड़ी गईं, इसलिए पहले R3 फ़्लैग देखें। यह सिंथेटिक डेमो डेटा है।")


@pytest.fixture(autouse=True)
def mock_mode(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "1")


def make_store(tmp_path, break_chain=False):
    from common.models import Actor
    store = Store(tmp_path / "kk.db")
    store.put_actor(Actor(actor_id="rc-a", role="recycler", name="Recycler A"))
    for i in range(10):
        store.append_receipt({
            "collector_id": "kw-raju", "material": "PET", "weight_kg": 100.0, "price_inr_per_kg": 18.0,
            "locality": "Seelampur", "ts": SEP.replace(minute=i), "photo_sha256": f"{i:064x}",
            "phash": "", "recycler_id": "rc-a", "synthetic": True,
        })
    store.put_certificate(Certificate(certificate_id="C1", recycler_id="rc-a", brand_id="br-1",
                                      month="2026-09", material="PET", tonnes=5.0))
    if break_chain:
        tamper(store, "kw-raju", 5, {"weight_kg": 101.0})
    return store


def raw_r1(store):
    (flag,) = rules.r1_mass_balance(store, rules.verified_receipts(store))
    return flag


def verdict(f):
    return (f.rule, f.subject_id, f.score, f.evidence_ids, f.status)


def fake(en, hi):
    return lambda system, user: json.dumps({"en": en, "hi": hi}, ensure_ascii=False)


def test_accepted_llm_gives_source_llm_and_same_verdict(tmp_path):
    store = make_store(tmp_path, break_chain=True)
    raw = raw_r1(store)
    out = with_llm_explanation(raw, store=store, complete=fake(GOOD_EN, GOOD_HI), cache_dir=str(tmp_path / "c"))
    assert out.explanation_source == "llm" and out.explanation_en == GOOD_EN
    assert verdict(out) == verdict(raw) and out.facts["excluded_collector_ids"] == ["kw-raju"]


def test_rejected_llm_keeps_rule_text(tmp_path):
    store = make_store(tmp_path)
    raw = raw_r1(store)
    out = with_llm_explanation(raw, store=store, cache_dir=str(tmp_path / "c"),
                               complete=fake(GOOD_EN.replace("11.8", "77.7"), GOOD_HI))
    assert out.explanation_source == "rule"
    assert (out.explanation_en, out.explanation_hi) == (raw.explanation_en, raw.explanation_hi)
    assert out.facts["excluded_tonnes"] == 0.0


def test_rejected_llm_with_chain_break_uses_template_with_note(tmp_path):
    store = make_store(tmp_path, break_chain=True)
    out = with_llm_explanation(raw_r1(store), store=store, cache_dir=str(tmp_path / "c"),
                               complete=fake(GOOD_EN.replace("11.8", "77.7"), GOOD_HI))
    assert out.explanation_source == "template"
    assert "0.50 tonnes" in out.explanation_en and "kw-raju" in out.explanation_en
    assert "R3 Flag" in out.explanation_en and "Chain is broken" in out.explanation_en
    assert "R3 फ़्लैग" in out.explanation_hi and "kw-raju" in out.explanation_hi and "चेन टूटी" in out.explanation_hi


def test_llm_without_broken_chain_note_is_rejected_when_excluded(tmp_path):
    store = make_store(tmp_path, break_chain=True)
    flag = raw_r1(store)
    facts_flag = flag.model_copy(update={"facts": explain_facts(flag, store)})
    en = ("Recycler A issued Certificates for 5.00 tonnes of PET in 2026-09 against 0.50 tonnes of Verified inflow. "
          "The Over-claim ratio is 11.8x, see Certificate C1. This is synthetic demo data.")
    assert explain._validate(facts_flag, en, GOOD_HI) == "broken-chain note missing"


def explain_facts(flag, store):
    from radar.facts import derive_facts
    return derive_facts(flag, store)


def test_llm_text_with_r3_token_passes_number_check(tmp_path):
    store = make_store(tmp_path, break_chain=True)
    flag = raw_r1(store)
    f2 = flag.model_copy(update={"facts": explain_facts(flag, store)})
    assert explain._validate(f2, GOOD_EN, GOOD_HI) is None
    assert explain._validate(f2, GOOD_EN.replace("first.", "first, see page 7.", 1), GOOD_HI) == "number not in facts"


def test_broken_chain_without_llm_uses_template_note(tmp_path):
    store = make_store(tmp_path, break_chain=True)
    out = with_llm_explanation(raw_r1(store), store=store)
    assert out.explanation_source == "template"
    assert "R3 Flag" in out.explanation_en and "kw-raju" in out.explanation_en


def test_mock_llm_keeps_rule_text_without_chain_break(tmp_path):
    store = make_store(tmp_path)
    raw = raw_r1(store)
    out = with_llm_explanation(raw, store=store)
    assert out.explanation_source == "rule" and out.explanation_en == raw.explanation_en
    assert out.facts and verdict(out) == verdict(raw)


def test_mock_llm_makes_no_network_call(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network used")
    monkeypatch.setattr(socket.socket, "connect", boom)
    monkeypatch.setattr(explain, "_default_completer", boom)
    store = make_store(tmp_path, break_chain=True)
    flags = rules.run(store)
    assert flags and all(f.explanation_source for f in flags)


def test_facts_failure_keeps_rule_text(tmp_path):
    store = make_store(tmp_path)
    raw = raw_r1(store)

    class Boom:
        def list_certificates(self, **kw):
            raise RuntimeError("closed")

    out = with_llm_explanation(raw, store=Boom())
    assert out.facts == {} and out.explanation_source == "rule" and out.explanation_en == raw.explanation_en


def test_rules_run_end_to_end_sets_facts_and_source(tmp_path):
    store = make_store(tmp_path, break_chain=True)
    status = rules.chain_status(store)
    raw = (rules.r1_mass_balance(store, rules.verified_receipts(store, status))
           + rules.r2_duplicate_photos(rules.verified_receipts(store, status))
           + rules.r3_broken_chains(store, status))
    flags = rules.run(store)
    assert [verdict(f) for f in flags] == [verdict(f) for f in raw]
    assert all(f.facts and f.explanation_source for f in flags)


def test_rules_run_on_sample_world(tmp_path):
    store = Store(tmp_path / "w.db")
    load_world(store, sample_world())
    flags = rules.run(store)
    assert {"R1_mass_balance", "R2_duplicate_photo", "R3_broken_chain"} <= {f.rule for f in flags}
    assert all(f.facts and f.explanation_source for f in flags)


def test_r1_facts_empty_when_score_disagrees(tmp_path):
    store = make_store(tmp_path)
    raw = raw_r1(store).model_copy(update={"score": 2.0})
    out = with_llm_explanation(raw, store=store)
    assert out.facts == {} and out.explanation_source == "rule" and out.explanation_en == raw.explanation_en


def test_excluded_uses_stored_values_after_recycler_edit(tmp_path):
    store = make_store(tmp_path)
    tamper(store, "kw-raju", 6, {"recycler_id": "rc-b"})
    out = with_llm_explanation(raw_r1(store), store=store)
    # seq 6 is stored under rc-b now, so only seq 7..9 count as excluded for rc-a
    assert out.facts["excluded_tonnes"] == pytest.approx(0.3)


def test_legacy_call_without_store_unchanged():
    kept = Flag(flag_id="F", rule="R3_broken_chain", subject_id="kw-x", score=1.0, explanation_en="a", explanation_hi="b")
    out = with_llm_explanation(kept)
    assert (out.explanation_en, out.explanation_hi, out.facts) == ("a", "b", {})
    empty = Flag(flag_id="F", rule="R3_broken_chain", subject_id="kw-x", score=1.0)
    assert with_llm_explanation(empty).explanation_source == "template"


def test_decide_flag_keeps_facts_and_source(tmp_path):
    store = make_store(tmp_path, break_chain=True)
    out = with_llm_explanation(raw_r1(store), store=store)
    decided = decide_flag(out, AUDITOR, "inspect")
    assert decided.facts == out.facts and decided.explanation_source == out.explanation_source
    assert decided.status == "inspection_requested"


def test_template_unchanged_without_excluded_keys():
    flag = Flag(flag_id="F", rule="R1_mass_balance", subject_id="rc-a", score=2.0, evidence_ids=["C1"],
                facts={"recycler_id": "rc-a", "month": "2026-09", "material": "PET", "certificate_tonnes": 5.0,
                       "verified_inflow_tonnes": 1.0, "ratio": 5.9})
    en, _ = explain.explain(flag)
    assert en == ("rc-a issued Certificates for 5.00 tonnes of PET in 2026-09, but its Verified inflow is 1.00 tonnes. "
                  "Over-claim ratio: 5.9x (Certificate tonnes divided by Verified inflow x 0.85). Evidence: C1. "
                  "An Auditor can request an inspection.")
