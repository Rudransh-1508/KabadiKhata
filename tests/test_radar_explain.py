import ast
import re
from pathlib import Path

import pytest

from common.models import Flag
from radar import decisions, explain as explain_mod
from radar.explain import HI_TERMS, explain, with_explanation

R1_FACTS = {"recycler_id": "rec-c", "recycler_name": "Recycler C", "month": "2026-09", "material": "PET",
            "certificate_tonnes": 38.0, "verified_inflow_tonnes": 1.0, "ratio": 44.7, "synthetic": True}
R2_FACTS = {"receipt_ids": ["KK-AAA111", "KK-BBB222"], "collector_ids": ["kw-raju", "kw-sita"],
            "max_hamming": 3}
R3_FACTS = {"collector_id": "kw-raju", "broken_seq": 4, "receipt_id": "KK-CCC333"}


def r1(**kw):
    facts = dict(R1_FACTS)
    facts.update(kw.pop("facts", {}))
    return Flag(flag_id="F-1", rule="R1_mass_balance", subject_id="rec-c", score=44.7,
                evidence_ids=kw.pop("evidence_ids", ["CERT-9"]), facts=facts, **kw)


def r2(**kw):
    return Flag(flag_id="F-2", rule="R2_duplicate_photo", subject_id="kw-raju", score=2.0,
                evidence_ids=["KK-AAA111", "KK-BBB222"], facts=dict(R2_FACTS), **kw)


def r3(**kw):
    return Flag(flag_id="F-3", rule="R3_broken_chain", subject_id="kw-raju", score=1.0,
                evidence_ids=["KK-CCC333"], facts=dict(R3_FACTS), **kw)


def test_r1_english_contains_numbers_ids_vocab():
    en, _ = explain(r1())
    for needle in ("38.00", "1.00", "2026-09", "PET", "CERT-9", "44.7x", "Certificates",
                   "Verified inflow", "Over-claim ratio", "Recycler C"):
        assert needle in en


def test_r1_hindi_contains_numbers_ids_terms():
    _, hi = explain(r1())
    for needle in ("38.00", "1.00", "2026-09", "PET", "CERT-9", "44.7 गुना",
                   HI_TERMS["Certificate"], HI_TERMS["Verified inflow"], HI_TERMS["Over-claim ratio"]):
        assert needle in hi


def test_r2_english_and_hindi():
    en, hi = explain(r2())
    assert "2 Receipts from 2 Kabadiwalas" in en and "distance 3" in en and "KK-AAA111" in en
    assert "2 कबाड़ीवाला की 2 रसीदों" in hi and "दूरी 3" in hi and "KK-BBB222" in hi


def test_r3_english_and_hindi():
    en, hi = explain(r3())
    assert "seq 4" in en and "KK-CCC333" in en and "kw-raju" in en
    assert "seq 4" in hi and "KK-CCC333" in hi and HI_TERMS["Chain"] in hi


def _runs(text):
    return re.findall(r"\d+", text)


def _allowed_from(strings):
    allowed = set()
    for s in strings:
        allowed.update(_runs(s))
    return allowed


@pytest.mark.parametrize("flag,formatted", [
    (r1(), ["38.00", "1.00", "44.7", "2026-09", "CERT-9", "0.85"]),
    (r2(), ["2", "3", "KK-AAA111", "KK-BBB222"]),
    (r3(), ["4", "KK-CCC333"]),
    (r1(evidence_ids=[f"CERT-{i}" for i in range(10, 18)]),
     ["38.00", "1.00", "44.7", "2026-09", "0.85", "3"] + [f"CERT-{i}" for i in range(10, 15)]),
])
def test_numbers_only_from_facts(flag, formatted):
    allowed = _allowed_from(formatted)
    for text in explain(flag):
        assert set(_runs(text)) <= allowed


FORBIDDEN = ["claim", "claims", "collector", "alert", "supply", "fraud", "fake", "mock"]


def test_no_forbidden_words():
    texts = [explain(f)[0] for f in (r1(), r2(), r3(), r1(facts={"ratio": None, "verified_inflow_tonnes": 0}))]
    texts += [explain(Flag(flag_id="G", rule=rule, subject_id="x", score=0.0))[0]
              for rule in ("R1_mass_balance", "R2_duplicate_photo", "R3_broken_chain")]
    for text in texts:
        text = text.replace("Over-claim ratio", "")
        words = {w.lower() for w in re.findall(r"[A-Za-z]+", text)}
        assert not words & set(FORBIDDEN), text


@pytest.mark.parametrize("facts", [
    {"certificate_tonnes": "38"},
    {"certificate_tonnes": True},
    {"certificate_tonnes": float("nan")},
    {"certificate_tonnes": -1.0},
    {"verified_inflow_tonnes": float("inf")},
    {"month": "2026-13"},
    {"material": "gold"},
    {"ratio": None},  # undefined ratio with non-zero inflow
    None,
])
def test_invalid_fact_types_give_generic_text(facts):
    if facts is None:
        flag = r1()
        flag = flag.model_copy(update={"facts": None})
    else:
        flag = r1(facts=facts)
    en, hi = explain(flag)
    assert en.startswith("Rule R1_mass_balance flagged rec-c.")
    assert "38.00" not in en and "44.7" not in en
    assert "R1_mass_balance" in hi


def test_ratio_key_absent_gives_generic_text():
    flag = r1()
    del flag.facts["ratio"]
    assert explain(flag)[0].startswith("Rule R1_mass_balance flagged")


def test_hindi_templates_use_fixed_terms():
    assert set(HI_TERMS) == {"Certificate", "Verified inflow", "Over-claim ratio", "Chain", "Receipt",
                             "Kabadiwala", "Recycler"}
    assert HI_TERMS["Kabadiwala"] == "कबाड़ीवाला" and HI_TERMS["Recycler"] == "रीसाइक्लर"
    assert HI_TERMS["Receipt"] in explain(r2())[1]
    assert HI_TERMS["Kabadiwala"] in explain(r2())[1]
    assert HI_TERMS["Verified inflow"] in explain(r3())[1]


def test_explanation_mentions_inspection_option():
    for flag in (r1(), r2(), r3(), r1(facts={"material": "gold"})):
        en, hi = explain(flag)
        assert "An Auditor can request an inspection." in en
        assert "ऑडिटर निरीक्षण का अनुरोध कर सकता है।" in hi


def test_synthetic_label_present_when_fact_true():
    en, hi = explain(r1())
    assert en.endswith(" (Synthetic demo data.)") and hi.endswith(" (सिंथेटिक डेमो डेटा।)")
    # also on the generic fallback
    en, _ = explain(r1(facts={"material": "gold"}))
    assert en.endswith("(Synthetic demo data.)")


def test_synthetic_label_absent_when_false():
    for facts in ({"synthetic": False}, {"synthetic": "yes"}):
        en, hi = explain(r1(facts=facts))
        assert "Synthetic" not in en and "सिंथेटिक" not in hi
    en, _ = explain(r3())
    assert "Synthetic" not in en


@pytest.mark.parametrize("make", [r1, r2, r3])
def test_missing_fact_gives_generic_text_without_numbers(make):
    flag = make()
    flag = flag.model_copy(update={"facts": {}})
    en, hi = explain(flag)
    assert en.startswith(f"Rule {flag.rule} flagged {flag.subject_id}.")
    assert hi.startswith("नियम ")
    assert not re.search(r"\d+\.\d+", en)


def test_zero_inflow_ratio_none_says_undefined():
    en, hi = explain(r1(facts={"ratio": None, "verified_inflow_tonnes": 0}))
    assert "Verified inflow is 0 tonnes" in en and "undefined" in en
    assert "x (" not in en
    assert "अपरिभाषित" in hi and "गुना" not in hi


def test_evidence_truncation_over_five():
    ids = [f"E-{i}" for i in range(8)]
    en, hi = explain(r1(evidence_ids=ids))
    assert "E-4" in en and "E-5" not in en and "and 3 more" in en
    assert "E-4" in hi and "E-5" not in hi and "और 3" in hi


def test_empty_evidence_text():
    en, hi = explain(r1(evidence_ids=[]))
    assert "Evidence: none recorded" in en and "प्रमाण: कोई दर्ज नहीं" in hi


def test_deterministic():
    assert explain(r1()) == explain(r1())


def test_with_explanation_fills_and_keeps_existing():
    filled = with_explanation(r1())
    assert filled.explanation_en and filled.explanation_hi
    kept = with_explanation(r1(explanation_en="LLM text", explanation_hi=None))
    assert kept.explanation_en == "LLM text"
    assert kept.explanation_hi == explain(r1())[1]


def test_explain_is_offline():
    banned = {"strands", "requests", "httpx", "urllib", "socket"}
    for mod in (explain_mod, decisions):
        tree = ast.parse(Path(mod.__file__).read_text(encoding="utf-8"))
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                found.add(node.module.split(".")[0])
        assert not found & banned
