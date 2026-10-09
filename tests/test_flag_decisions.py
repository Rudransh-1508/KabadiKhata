from datetime import datetime, timedelta, timezone

import pytest

from common.models import Flag
from ledger.store import Store
from radar.decisions import (FlagAlreadyDecided, FlagDecisionError, FlagDenied, InvalidDecision,
                             decide_flag)

AUDITOR = 'Actor::"auditor-1"'
NOW = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)


def make_flag(**kw) -> Flag:
    base = dict(flag_id="F-1", rule="R1_mass_balance", subject_id="rec-c", score=38.0,
                evidence_ids=["CERT-1"], facts={"month": "2026-09", "nested": {"a": 1}},
                explanation_en="en", explanation_hi="hi")
    base.update(kw)
    return Flag(**base)


def test_inspect_sets_inspection_requested():
    assert decide_flag(make_flag(), AUDITOR, "inspect", now=NOW).status == "inspection_requested"


def test_dismiss_sets_dismissed():
    assert decide_flag(make_flag(), AUDITOR, "dismiss", now=NOW).status == "dismissed"


def test_records_decided_by_ts_and_note():
    out = decide_flag(make_flag(), AUDITOR, "inspect", note="  visit Monday ", now=NOW)
    assert out.decided_by == "auditor-1"
    assert out.decided_ts == NOW
    assert out.decision_note == "visit Monday"


def test_naive_now_treated_as_utc():
    out = decide_flag(make_flag(), AUDITOR, "inspect", now=datetime(2026, 10, 9, 12, 0))
    assert out.decided_ts == NOW
    assert out.decided_ts.utcoffset() == timedelta(0)


def test_default_now_is_utc_aware():
    out = decide_flag(make_flag(), AUDITOR, "dismiss")
    assert out.decided_ts.utcoffset() == timedelta(0)


def test_input_flag_not_mutated():
    flag = make_flag()
    before = flag.model_copy(deep=True)
    decide_flag(flag, AUDITOR, "inspect", note="x", now=NOW)
    assert flag == before


def test_other_fields_preserved():
    flag = make_flag()
    out = decide_flag(flag, AUDITOR, "inspect", now=NOW)
    for field in ("flag_id", "rule", "subject_id", "score", "evidence_ids", "facts",
                  "explanation_en", "explanation_hi"):
        assert getattr(out, field) == getattr(flag, field)


@pytest.mark.parametrize("note", [None, "", "   \n\t"])
def test_blank_note_becomes_none(note):
    assert decide_flag(make_flag(), AUDITOR, "inspect", note=note, now=NOW).decision_note is None


def test_long_note_truncated():
    out = decide_flag(make_flag(), AUDITOR, "inspect", note="a" * 900, now=NOW)
    assert out.decision_note == "a" * 500


@pytest.mark.parametrize("first,pick", [("inspect", "inspect"), ("dismiss", "dismiss")])
def test_double_decision_same_raises_already_decided(first, pick):
    decided = decide_flag(make_flag(), AUDITOR, first, now=NOW)
    with pytest.raises(FlagAlreadyDecided) as exc:
        decide_flag(decided, AUDITOR, pick, now=NOW)
    assert exc.value.status == decided.status


def test_double_decision_opposite_raises():
    decided = decide_flag(make_flag(), AUDITOR, "dismiss", now=NOW)
    with pytest.raises(FlagAlreadyDecided):
        decide_flag(decided, AUDITOR, "inspect", now=NOW)
    decided = decide_flag(make_flag(), AUDITOR, "inspect", now=NOW)
    with pytest.raises(FlagAlreadyDecided):
        decide_flag(decided, AUDITOR, "dismiss", now=NOW)


@pytest.mark.parametrize("bad", ["approve", "", None, "INSPECT"])
def test_invalid_decision_raises(bad):
    flag = make_flag()
    with pytest.raises(InvalidDecision):
        decide_flag(flag, AUDITOR, bad, now=NOW)
    assert flag.status == "open"


def test_brand_denied_with_cedar_body():
    flag = make_flag()
    with pytest.raises(FlagDenied) as exc:
        decide_flag(flag, 'Actor::"brand-1"', "inspect", now=NOW)
    body = exc.value.decision.to_denial("approve_flag")
    assert body["denied_by"] == "cedar" and body["action"] == "approve_flag" and body["reason"]
    assert isinstance(exc.value, FlagDecisionError)
    assert flag.status == "open" and flag.decided_by is None


@pytest.mark.parametrize("who", [
    'Actor::"kw-raju"', 'Actor::"rec-a"', 'Agent::"kabadi-agent"',
    'Actor::"nobody"', "garbage", "",
])
def test_kabadiwala_recycler_agent_unknown_denied(who):
    with pytest.raises(FlagDenied):
        decide_flag(make_flag(), who, "dismiss", now=NOW)


def test_denied_before_status_check():
    decided = decide_flag(make_flag(), AUDITOR, "inspect", now=NOW)
    with pytest.raises(FlagDenied):
        decide_flag(decided, 'Actor::"brand-1"', "inspect", now=NOW)


def test_invalid_decision_checked_before_cedar():
    with pytest.raises(InvalidDecision):
        decide_flag(make_flag(), 'Actor::"brand-1"', "approve", now=NOW)


def test_flag_defaults_backward_compatible():
    flag = Flag(flag_id="F", rule="R3_broken_chain", subject_id="kw-raju", score=1.0)
    assert flag.facts == {} and flag.decision_note is None


def test_facts_not_shared_with_input():
    flag = make_flag()
    out = decide_flag(flag, AUDITOR, "inspect", now=NOW)
    out.facts["nested"]["a"] = 99
    out.facts["month"] = "changed"
    assert flag.facts == {"month": "2026-09", "nested": {"a": 1}}


def test_decision_persists_via_store(tmp_path):
    store = Store(tmp_path / "kk.db")
    flag = make_flag()
    store.replace_flags([flag])
    new = decide_flag(store.get_flag(flag.flag_id), AUDITOR, "inspect", note="n", now=NOW)
    stored = store.decide_flag(new.flag_id, new.status, new.decided_by)
    assert stored.status == new.status == "inspection_requested"
    assert stored.decided_by == new.decided_by == "auditor-1"
