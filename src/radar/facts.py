"""Facts for the radar explainer, derived from the store with the rules' own helpers (read-only).

The shape follows the facts contract at the top of `radar.explain`. Nothing here decides a verdict:
if a number cannot be recomputed to match the Flag the rule produced, the facts are empty and the
Flag keeps the rule's own text.
"""
from __future__ import annotations

import math
from typing import Any

from common.models import Flag
from ledger import chain


def _all_synthetic(receipts) -> bool:
    return bool(receipts) and all(r.synthetic for r in receipts)


def _r1(flag: Flag, store: Any) -> dict:
    from radar import rules

    ids = list(flag.evidence_ids or [])
    if not ids:
        return {}
    by_id = {c.certificate_id: c for c in store.list_certificates()}
    certs = [by_id[i] for i in ids if i in by_id]
    if len(certs) != len(ids):
        return {}
    keys = {(c.recycler_id, c.material, c.month) for c in certs}
    if len(keys) != 1:
        return {}
    key = next(iter(keys))
    recycler_id, material, month = key
    if flag.subject_id != recycler_id:
        return {}

    status = rules.chain_status(store)
    inflow = rules.verified_inflow_t(rules.verified_receipts(store, status)).get(key, 0.0)
    certified = rules.certified_t(store.list_certificates(recycler_id=recycler_id)).get(key, 0.0)
    ratio = rules.over_claim_ratio(certified, inflow)
    if math.isinf(ratio):
        if flag.score != 999.0:
            return {}
        shown = None
    else:
        if not math.isclose(flag.score, min(ratio, 999.0), rel_tol=1e-9, abs_tol=1e-9):
            return {}
        shown = float(ratio)

    excluded = 0.0
    excluded_by: dict = {}
    behind = []
    for cid, res in status.items():
        for r in store.receipts_for(cid):
            if not r.recycler_id or (r.recycler_id, r.material, chain.month_ist(r.ts)) != key:
                continue
            behind.append(r)
            if res.broken_at_seq is not None and r.seq >= res.broken_at_seq:
                excluded += r.weight_kg / 1000
                excluded_by[cid] = excluded_by.get(cid, 0.0) + r.weight_kg / 1000
    facts: dict = {
        "recycler_id": recycler_id,
        "month": month,
        "material": material,
        "certificate_tonnes": float(certified),
        "verified_inflow_tonnes": float(inflow),
        "ratio": shown,
        "excluded_tonnes": round(excluded, 6),
        "excluded_collector_ids": sorted(c for c, t in excluded_by.items() if t > 0),
    }
    actor = store.get_actor(recycler_id)
    if actor is not None and actor.name:
        facts["recycler_name"] = actor.name
    if _all_synthetic(behind):
        facts["synthetic"] = True
    return facts


def _r2(flag: Flag, store: Any) -> dict:
    from radar import rules

    ids = list(flag.evidence_ids or [])
    receipts = [store.get_receipt(i) for i in ids]
    if len(receipts) < 2 or any(r is None or not r.phash for r in receipts):
        return {}
    collectors = sorted({r.collector_id for r in receipts})
    if flag.subject_id != ",".join(collectors):
        return {}
    dist = max(rules.hamming(a.phash, b.phash) for a in receipts for b in receipts)
    facts: dict = {"receipt_ids": sorted(ids), "collector_ids": collectors, "max_hamming": int(dist)}
    if _all_synthetic(receipts):
        facts["synthetic"] = True
    return facts


def _r3(flag: Flag, store: Any) -> dict:
    receipts = store.receipts_for(flag.subject_id)
    seq = chain.verify(receipts).broken_at_seq
    if seq is None:
        return {}
    facts: dict = {"collector_id": flag.subject_id, "broken_seq": int(seq)}
    if flag.evidence_ids:
        facts["receipt_id"] = flag.evidence_ids[0]
    if _all_synthetic(receipts):
        facts["synthetic"] = True
    return facts


_DERIVE = {"R1_mass_balance": _r1, "R2_duplicate_photo": _r2, "R3_broken_chain": _r3}


def derive_facts(flag: Flag, store: Any) -> dict:
    """JSON-safe facts per the contract at the top of explain.py; {} when the Flag or store does not support them."""
    fn = _DERIVE.get(flag.rule)
    return fn(flag, store) if fn else {}
