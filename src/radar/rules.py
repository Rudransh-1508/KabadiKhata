"""Deterministic fraud rules. Code decides; an LLM may only explain (CLAUDE.md design rule 1).

R1 mass balance   a Recycler certifies more than its Verified inflow can support
R2 duplicate photo the same scale photo (near-identical phash) backs several Receipts
R3 broken chain    a Kabadiwala's Chain no longer verifies

Verified inflow counts only Receipts that come before any break in their Chain:
a tampered Receipt, and everything after it, stops backing certificates.
"""

import os
from collections import defaultdict

from common.models import Certificate, Flag, Receipt
from ledger import chain
from ledger.store import Store

YIELD = 0.85


def r1_threshold() -> float:
    # Honest recyclers sit near 1.0 (±10-15% noise); 1.2x over-claims must still be caught
    return float(os.getenv("KK_R1_THRESHOLD", "1.17"))


def r2_max_distance() -> int:
    return int(os.getenv("KK_R2_MAX_DISTANCE", "6"))


# ---------- shared views ----------

def chain_status(store: Store) -> dict[str, chain.VerifyResult]:
    return {cid: chain.verify(store.receipts_for(cid)) for cid in store.collector_ids()}


def verified_receipts(store: Store, status: dict[str, chain.VerifyResult] | None = None) -> list[Receipt]:
    status = status or chain_status(store)
    out = []
    for cid, result in status.items():
        for r in store.receipts_for(cid):
            if result.broken_at_seq is not None and r.seq >= result.broken_at_seq:
                break
            out.append(r)
    return out


def _key(recycler_id: str, material: str, month: str) -> tuple[str, str, str]:
    return recycler_id, material, month


def verified_inflow_t(receipts: list[Receipt]) -> dict[tuple[str, str, str], float]:
    inflow: dict[tuple[str, str, str], float] = defaultdict(float)
    for r in receipts:
        if r.recycler_id:
            inflow[_key(r.recycler_id, r.material, chain.month_ist(r.ts))] += r.weight_kg / 1000
    return inflow


def certified_t(certs: list[Certificate]) -> dict[tuple[str, str, str], float]:
    total: dict[tuple[str, str, str], float] = defaultdict(float)
    for c in certs:
        total[_key(c.recycler_id, c.material, c.month)] += c.tonnes
    return total


def over_claim_ratio(certified: float, inflow: float) -> float:
    supported = inflow * YIELD
    return certified / supported if supported > 0 else float("inf")


# ---------- rules ----------

def r1_mass_balance(store: Store, verified: list[Receipt], month: str | None = None) -> list[Flag]:
    certs = [c for c in store.list_certificates() if month is None or c.month == month]
    inflow = verified_inflow_t(verified)
    flags = []
    for key, cert_t in sorted(certified_t(certs).items()):
        recycler_id, material, m = key
        ratio = over_claim_ratio(cert_t, inflow.get(key, 0.0))
        if ratio <= r1_threshold():
            continue
        shown = "no verified inflow" if ratio == float("inf") else f"{ratio:.1f}x"
        flags.append(Flag(
            flag_id=f"R1:{recycler_id}:{material}:{m}",
            rule="R1_mass_balance",
            subject_id=recycler_id,
            score=min(ratio, 999.0),
            evidence_ids=sorted(c.certificate_id for c in certs if _key(c.recycler_id, c.material, c.month) == key),
            explanation_en=(
                f"{recycler_id} certified {cert_t:.2f} t of {material} for {m}, but its verified inflow of "
                f"{inflow.get(key, 0.0):.2f} t supports only {inflow.get(key, 0.0) * YIELD:.2f} t ({shown})."
            ),
            explanation_hi=(
                f"{recycler_id} ने {m} में {material} के {cert_t:.2f} टन प्रमाणित किए, लेकिन सत्यापित आवक से "
                f"केवल {inflow.get(key, 0.0) * YIELD:.2f} टन बनता है ({shown})."
            ),
        ))
    return flags


def hamming(a: str, b: str) -> int:
    return (int(a, 16) ^ int(b, 16)).bit_count()


def r2_duplicate_photos(receipts: list[Receipt]) -> list[Flag]:
    """Group Receipts whose photos are within KK_R2_MAX_DISTANCE bits of each other."""
    limit = r2_max_distance()
    items = [r for r in receipts if r.phash]
    parent = list(range(len(items)))

    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    values = [int(r.phash, 16) for r in items]
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if (values[i] ^ values[j]).bit_count() <= limit:
                parent[root(i)] = root(j)
    groups: dict[int, list[Receipt]] = defaultdict(list)
    for i, r in enumerate(items):
        groups[root(i)].append(r)

    flags = []
    for group in groups.values():
        if len(group) < 2:
            continue
        ids = sorted(r.receipt_id for r in group)
        collectors = sorted({r.collector_id for r in group})
        flags.append(Flag(
            flag_id=f"R2:{ids[0]}",
            rule="R2_duplicate_photo",
            subject_id=",".join(collectors),
            score=float(len(group)),
            evidence_ids=ids,
            explanation_en=f"{len(group)} receipts from {len(collectors)} kabadiwala(s) use near-identical scale photos.",
            explanation_hi=f"{len(group)} रसीदों में लगभग एक जैसी तराज़ू की फ़ोटो है.",
        ))
    return flags


def r3_broken_chains(store: Store, status: dict[str, chain.VerifyResult]) -> list[Flag]:
    flags = []
    for cid, result in sorted(status.items()):
        if result.ok:
            continue
        chain_receipts = store.receipts_for(cid)
        evidence = [r.receipt_id for r in chain_receipts if r.seq == result.broken_at_seq]
        flags.append(Flag(
            flag_id=f"R3:{cid}",
            rule="R3_broken_chain",
            subject_id=cid,
            score=1.0,
            evidence_ids=evidence,
            explanation_en=f"{cid}'s receipt chain breaks at #{result.broken_at_seq}: {result.reason}.",
            explanation_hi=f"{cid} की रसीद-श्रृंखला #{result.broken_at_seq} पर टूटी है.",
        ))
    return flags


def run(store: Store, month: str | None = None) -> list[Flag]:
    status = chain_status(store)
    verified = verified_receipts(store, status)
    flags = r1_mass_balance(store, verified, month) + r2_duplicate_photos(verified) + r3_broken_chains(store, status)
    return [_explain(f, store) for f in flags]


def _explain(flag: Flag, store: Store) -> Flag:
    """radar.explain fills only empty explanation text (never the verdict); text the rule already set stays."""
    from radar.explain import with_llm_explanation
    return with_llm_explanation(flag)


# ---------- brand view ----------

def provenance(store: Store, cert: Certificate) -> dict:
    """Where a Certificate's plastic came from, in aggregate: localities and tonnes, never Kabadiwala identities."""
    key = _key(cert.recycler_id, cert.material, cert.month)
    verified = [
        r for r in verified_receipts(store)
        if r.recycler_id and _key(r.recycler_id, r.material, chain.month_ist(r.ts)) == key
    ]
    inflow_t = sum(r.weight_kg for r in verified) / 1000
    group_certified = certified_t(store.list_certificates(recycler_id=cert.recycler_id)).get(key, 0.0)
    ratio = over_claim_ratio(group_certified, inflow_t)
    by_locality: dict[str, dict] = defaultdict(lambda: {"receipts": 0, "tonnes": 0.0})
    for r in verified:
        by_locality[r.locality]["receipts"] += 1
        by_locality[r.locality]["tonnes"] += r.weight_kg / 1000
    return {
        "certificate": cert.model_dump(),
        "verified_inflow_t": round(inflow_t, 3),
        "recycler_certified_t": round(group_certified, 3),
        "verified_backed_pct": round(min(100.0, 100.0 / ratio), 1) if ratio != float("inf") else 0.0,
        "by_locality": [
            {"locality": loc, "receipts": v["receipts"], "tonnes": round(v["tonnes"], 3)}
            for loc, v in sorted(by_locality.items(), key=lambda kv: -kv[1]["tonnes"])
        ],
    }
