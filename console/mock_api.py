"""Offline mock of the backend, so the console runs (and AppTest passes) with no
live API. Same surface and SAME return shapes as console.api_client; selected by
default, or when KK_USE_MOCK != "0".

All data here is SYNTHETIC (CLAUDE.md #3): every record carries ``synthetic: True``
and the console watermarks it. The numbers mirror the seeded world closely enough
for the demo narrative — Recycler C (rc-c) over-claims PET ~38x — but the live
figures always come from the real API.
"""
from __future__ import annotations

import copy

try:  # `streamlit run console/app.py` puts console/ on the path; tests import as a package
    from console.api_client import CedarDenied  # same exception the real client raises
except ImportError:  # pragma: no cover
    from api_client import CedarDenied

THRESHOLD_PCT = 80

# The R1 subject's certificate id; its evidence_ids[0] points here (as the real radar does).
_R1_CERT = "C-rc-c-PET-2026-09"

_FLAGS: list[dict] = [
    {
        "flag_id": "R1:rc-c:PET:2026-09",
        "rule": "R1_mass_balance",
        "subject_id": "rc-c",
        "score": 38.0,
        "evidence_ids": [_R1_CERT],
        "explanation_en": ("rc-c certified 190.00 t of PET for 2026-09, but its verified "
                           "inflow of 5.00 t supports only 4.25 t (38.0x)."),
        "explanation_hi": "rc-c ने 2026-09 में PET के 190.00 टन प्रमाणित किए, लेकिन सत्यापित आवक से केवल 4.25 टन बनता है (38.0x).",
        "status": "open",
        "decided_by": None,
        "decided_ts": None,
        "facts": {"certified_t": 190.0, "verified_inflow_t": 5.0, "ratio": 38.0},
        "synthetic": True,
    },
    {
        "flag_id": "R2:KK-AAA111",
        "rule": "R2_duplicate_photo",
        "subject_id": "kb-07,kb-12",
        "score": 3.0,
        "evidence_ids": ["KK-AAA111", "KK-BBB222", "KK-CCC333"],
        "explanation_en": "3 receipts from 2 kabadiwala(s) use near-identical scale photos.",
        "explanation_hi": "3 रसीदों में लगभग एक जैसी तराज़ू की फ़ोटो है.",
        "status": "open",
        "decided_by": None,
        "decided_ts": None,
        "facts": {"cluster_size": 3, "collectors": 2},
        "synthetic": True,
    },
    {
        "flag_id": "R3:kb-03",
        "rule": "R3_broken_chain",
        "subject_id": "kb-03",
        "score": 1.0,
        "evidence_ids": ["KK-DDD444"],
        "explanation_en": "kb-03's receipt chain breaks at #7: prev_hash does not match.",
        "explanation_hi": "kb-03 की रसीद-श्रृंखला #7 पर टूटी है.",
        "status": "open",
        "decided_by": None,
        "decided_ts": None,
        "facts": {"broken_at_seq": 7},
        "synthetic": True,
    },
]

# Certificates by brand. `tonnes` (not tonnes_claimed); no recycler_name.
_CERTS: list[dict] = [
    {"certificate_id": _R1_CERT, "recycler_id": "rc-c", "brand_id": "br-1",
     "month": "2026-09", "material": "PET", "tonnes": 190.0,
     "verified_backed_pct": 2.6, "synthetic": True},
    {"certificate_id": "C-rc-a-PET-2026-09", "recycler_id": "rc-a", "brand_id": "br-1",
     "month": "2026-09", "material": "PET", "tonnes": 42.0,
     "verified_backed_pct": 94.0, "synthetic": True},
    {"certificate_id": "C-rc-b-HDPE-2026-09", "recycler_id": "rc-b", "brand_id": "br-2",
     "month": "2026-09", "material": "HDPE", "tonnes": 30.0,
     "verified_backed_pct": 88.0, "synthetic": True},
]

# Provenance by certificate_id (aggregate localities only, never identities).
_PROVENANCE: dict[str, dict] = {
    _R1_CERT: {
        "certificate": {"certificate_id": _R1_CERT, "recycler_id": "rc-c", "brand_id": "br-1",
                        "month": "2026-09", "material": "PET", "tonnes": 190.0},
        "verified_inflow_t": 5.0,
        "recycler_certified_t": 190.0,
        "verified_backed_pct": 2.6,
        "by_locality": [
            {"locality": "bawana", "receipts": 41, "tonnes": 3.2},
            {"locality": "narela", "receipts": 23, "tonnes": 1.8},
        ],
        "synthetic": True,
    },
    "C-rc-a-PET-2026-09": {
        "certificate": {"certificate_id": "C-rc-a-PET-2026-09", "recycler_id": "rc-a", "brand_id": "br-1",
                        "month": "2026-09", "material": "PET", "tonnes": 42.0},
        "verified_inflow_t": 52.6,
        "recycler_certified_t": 42.0,
        "verified_backed_pct": 94.0,
        "by_locality": [
            {"locality": "narela", "receipts": 310, "tonnes": 33.1},
            {"locality": "mayapuri", "receipts": 180, "tonnes": 19.5},
        ],
        "synthetic": True,
    },
    "C-rc-b-HDPE-2026-09": {
        "certificate": {"certificate_id": "C-rc-b-HDPE-2026-09", "recycler_id": "rc-b", "brand_id": "br-2",
                        "month": "2026-09", "material": "HDPE", "tonnes": 30.0},
        "verified_inflow_t": 40.1,
        "recycler_certified_t": 30.0,
        "verified_backed_pct": 88.0,
        "by_locality": [{"locality": "mayapuri", "receipts": 240, "tonnes": 34.0}],
        "synthetic": True,
    },
}

_DECIDED: dict[str, dict] = {}  # flag_id -> {status, decided_by, decided_ts}


def _flags_now() -> list[dict]:
    out = []
    for f in _FLAGS:
        g = copy.deepcopy(f)
        if g["flag_id"] in _DECIDED:
            g.update(_DECIDED[g["flag_id"]])
        out.append(g)
    return out


# ---------- auditor ----------

def run_radar(principal: str) -> list[dict]:
    return _flags_now()


def list_flags(principal: str) -> list[dict]:
    return _flags_now()


def decide_flag(flag_id: str, decision: str, principal: str) -> dict:
    status = "inspection_requested" if decision == "inspect" else "dismissed"
    who = principal.removeprefix('Actor::"').removesuffix('"') if principal else "au-1"
    _DECIDED[flag_id] = {"status": status, "decided_by": who, "decided_ts": "2026-10-09T10:00:00+00:00"}
    return next(f for f in _flags_now() if f["flag_id"] == flag_id)


# ---------- brand ----------

def list_certificates(brand_id: str, principal: str) -> list[dict]:
    return [copy.deepcopy(c) for c in _CERTS if c["brand_id"] == brand_id]


def provenance(certificate_id: str, principal: str) -> dict:
    return copy.deepcopy(_PROVENANCE[certificate_id])


# ---------- identity access (Cedar demo, beat #4) ----------

def list_actors(principal: str, role: str | None = None) -> list[dict]:
    """A Brand is denied; only the Auditor may list actors (mirrors policies.cedar)."""
    actor_id = principal.removeprefix('Actor::"').removesuffix('"') if principal else ""
    if actor_id.startswith("br-"):
        raise CedarDenied({"denied_by": "cedar", "action": "list_actors",
                           "reason": "a brand may not read kabadiwala identities"})
    return [{"actor_id": "kb-01", "role": "kabadiwala", "name": "Raju", "locality": "bawana", "synthetic": True}]
