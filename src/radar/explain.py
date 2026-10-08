"""Deterministic template explanations (English and Hindi) for Flags.

The LLM explainer, when added, falls back to this. Numbers come only from `Flag.facts`;
nothing is computed or defaulted here.

Facts contract (required unless marked optional; values are JSON-safe):
  R1_mass_balance:    recycler_id str, recycler_name str (optional), month "YYYY-MM", material (a Material),
                      certificate_tonnes float, verified_inflow_tonnes float,
                      ratio float | None (Over-claim ratio = certificate_tonnes / (verified_inflow_tonnes x 0.85);
                      key must be present; None only when verified_inflow_tonnes is 0), synthetic bool (optional)
  R2_duplicate_photo: receipt_ids list[str], collector_ids list[str], max_hamming int, synthetic bool (optional)
  R3_broken_chain:    collector_id str, broken_seq int >= 0, receipt_id str (optional), synthetic bool (optional)
The text is plain Unicode; the console must render it as text, not HTML.
"""
from __future__ import annotations

import logging
import math
import re

from common.models import MATERIALS, Flag

log = logging.getLogger("kk.explain")

HI_TERMS = {
    "Certificate": "प्रमाणपत्र",
    "Verified inflow": "सत्यापित आवक",
    "Over-claim ratio": "ओवर-क्लेम अनुपात",
    "Chain": "चेन",
    "Receipt": "रसीद",
    "Kabadiwala": "कबाड़ीवाला",
    "Recycler": "रीसाइक्लर",
}

EVIDENCE_LIMIT = 5
_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

_INSPECT_EN = " An Auditor can request an inspection."
_INSPECT_HI = " ऑडिटर निरीक्षण का अनुरोध कर सकता है।"
_SYNTH_EN = " (Synthetic demo data.)"
_SYNTH_HI = " (सिंथेटिक डेमो डेटा।)"


# ---------- validation ----------

def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v >= 0


def _str(v) -> bool:
    return isinstance(v, str) and bool(v)


def _strs(v) -> bool:
    return isinstance(v, list) and all(_str(x) for x in v)


def _int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


class _Missing(Exception):
    pass


def _need(ok: bool) -> None:
    if not ok:
        raise _Missing


# ---------- evidence ----------

def _evidence(ids: list[str], lang: str) -> str:
    if not ids:
        return "none recorded" if lang == "en" else "कोई दर्ज नहीं"
    shown = ", ".join(ids[:EVIDENCE_LIMIT])
    extra = len(ids) - EVIDENCE_LIMIT
    if extra > 0:
        shown += f", and {extra} more" if lang == "en" else f", और {extra}"
    return shown


# ---------- per-rule templates ----------

def _r1(flag: Flag, f: dict, ev_en: str, ev_hi: str) -> tuple[str, str]:
    _need(_str(f.get("recycler_id")))
    _need(isinstance(f.get("month"), str) and _MONTH_RE.match(f["month"]) is not None)
    _need(f.get("material") in MATERIALS)
    _need(_num(f.get("certificate_tonnes")) and _num(f.get("verified_inflow_tonnes")))
    _need("ratio" in f)
    ratio = f["ratio"]
    if ratio is None:
        _need(f["verified_inflow_tonnes"] == 0)
    else:
        _need(_num(ratio))
    name = f["recycler_name"] if _str(f.get("recycler_name")) else flag.subject_id
    t, v, m, mat = f["certificate_tonnes"], f["verified_inflow_tonnes"], f["month"], f["material"]
    if ratio is None:
        en = (f"{name} issued Certificates for {t:.2f} tonnes of {mat} in {m}, but its Verified inflow is 0 tonnes, "
              f"so the Over-claim ratio is undefined. Evidence: {ev_en}.")
        hi = (f"{name} ने {m} में {mat} के {t:.2f} टन के प्रमाणपत्र जारी किए, लेकिन उसकी सत्यापित आवक 0 टन है, "
              f"इसलिए ओवर-क्लेम अनुपात अपरिभाषित है। प्रमाण: {ev_hi}।")
    else:
        en = (f"{name} issued Certificates for {t:.2f} tonnes of {mat} in {m}, but its Verified inflow is {v:.2f} tonnes. "
              f"Over-claim ratio: {ratio:.1f}x (Certificate tonnes divided by Verified inflow x 0.85). Evidence: {ev_en}.")
        hi = (f"{name} ने {m} में {mat} के {t:.2f} टन के प्रमाणपत्र जारी किए, लेकिन उसकी सत्यापित आवक {v:.2f} टन है। "
              f"ओवर-क्लेम अनुपात: {ratio:.1f} गुना (प्रमाणपत्र टन ÷ (सत्यापित आवक × 0.85))। प्रमाण: {ev_hi}।")
    return en, hi


def _r2(flag: Flag, f: dict, ev_en: str, ev_hi: str) -> tuple[str, str]:
    _need(_strs(f.get("receipt_ids")) and _strs(f.get("collector_ids")))
    _need(_int(f.get("max_hamming")))
    n, k, d = len(f["receipt_ids"]), len(set(f["collector_ids"])), f["max_hamming"]
    en = (f"{n} Receipts from {k} Kabadiwalas use near-identical photos "
          f"(largest perceptual-hash distance {d}). Evidence: {ev_en}.")
    hi = f"{k} कबाड़ीवाला की {n} रसीदों में लगभग एक जैसी फ़ोटो है (सबसे बड़ी फ़ोटो-हैश दूरी {d})। प्रमाण: {ev_hi}।"
    return en, hi


def _r3(flag: Flag, f: dict, ev_en: str, ev_hi: str) -> tuple[str, str]:
    _need(_str(f.get("collector_id")) and _int(f.get("broken_seq")))
    c, n = f["collector_id"], f["broken_seq"]
    en = (f"The Chain of Kabadiwala {c} breaks at seq {n}: that Receipt no longer matches its hash, "
          f"so none of this Kabadiwala's Receipts count towards Verified inflow. Evidence: {ev_en}.")
    hi = (f"कबाड़ीवाला {c} की चेन seq {n} पर टूटती है: वह रसीद अपने हैश से मेल नहीं खाती, "
          f"इसलिए इस कबाड़ीवाला की कोई भी रसीद सत्यापित आवक में नहीं गिनी जाती। प्रमाण: {ev_hi}।")
    return en, hi


_RULES = {"R1_mass_balance": _r1, "R2_duplicate_photo": _r2, "R3_broken_chain": _r3}


def explain(flag: Flag) -> tuple[str, str]:
    """(english, hindi) explanation of a Flag, built only from rule, subject, evidence ids and facts."""
    facts = flag.facts if isinstance(flag.facts, dict) else {}
    ids = list(flag.evidence_ids or [])
    ev_en, ev_hi = _evidence(ids, "en"), _evidence(ids, "hi")
    try:
        en, hi = _RULES[flag.rule](flag, facts, ev_en, ev_hi)
    except (_Missing, KeyError):
        log.warning("explanation facts missing or invalid: rule=%s flag_id=%s", flag.rule, flag.flag_id)
        en = f"Rule {flag.rule} flagged {flag.subject_id}. Evidence: {ev_en}."
        hi = f"नियम {flag.rule} ने {flag.subject_id} को चिह्नित किया। प्रमाण: {ev_hi}।"
    en += _INSPECT_EN
    hi += _INSPECT_HI
    if facts.get("synthetic") is True:
        en += _SYNTH_EN
        hi += _SYNTH_HI
    return en, hi


def with_explanation(flag: Flag) -> Flag:
    """Copy of the Flag with explanation_en / explanation_hi filled; existing text is kept."""
    en, hi = explain(flag)
    return flag.model_copy(
        update={"explanation_en": flag.explanation_en or en, "explanation_hi": flag.explanation_hi or hi},
        deep=True,
    )
