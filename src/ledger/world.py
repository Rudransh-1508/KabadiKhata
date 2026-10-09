"""Loading a synthetic world into the store, and a small built-in one.

World format (P1's `data/synth/world.json` follows it; everything is synthetic):

    {
      "actors":       [Actor, ...],
      "certificates": [Certificate, ...],
      "receipts":     [receipt fields without seq/prev_hash/hash/receipt_id, ts as ISO-8601 with offset],
      "tamper":       [{"collector_id": "...", "seq": 3, "set": {"weight_kg": 40.0}}, ...]
    }

Receipts go through `Store.append_receipt` in time order, so seeded hashes are
computed exactly like live ones. `tamper` edits are applied afterwards with raw
SQL, the same way an attacker with database access would.
"""

import random
import sqlite3
from datetime import datetime, timedelta

from common.models import Actor, Certificate
from ledger.chain import IST
from ledger.store import Store

TAMPERABLE = {"weight_kg", "price_inr_per_kg", "material", "locality", "recycler_id"}


def load_world(store: Store, world: dict) -> dict:
    for a in world.get("actors", []):
        store.put_actor(Actor(**a))
    receipts = sorted(world.get("receipts", []), key=lambda r: r["ts"])
    for fields in receipts:
        store.append_receipt({**fields, "synthetic": True})
    for c in world.get("certificates", []):
        store.put_certificate(Certificate(**c))
    tampered = 0
    for t in world.get("tamper", []):
        tamper(store, t["collector_id"], t["seq"], t["set"])
        tampered += 1
    return {
        "actors": len(world.get("actors", [])),
        "receipts": len(receipts),
        "certificates": len(world.get("certificates", [])),
        "tampered": tampered,
    }


def tamper(store: Store, collector_id: str, seq: int, changes: dict) -> None:
    """Edit a stored Receipt in place, bypassing the ledger. For demos and tests only."""
    bad = set(changes) - TAMPERABLE
    if bad:
        raise ValueError(f"can't tamper with {sorted(bad)}; allowed: {sorted(TAMPERABLE)}")
    sets = ", ".join(f"{k} = ?" for k in changes)
    con = sqlite3.connect(store.path)
    try:
        cur = con.execute(
            f"UPDATE receipts SET {sets} WHERE collector_id = ? AND seq = ?",
            (*changes.values(), collector_id, seq),
        )
        if cur.rowcount != 1:
            raise ValueError(f"no receipt {collector_id}#{seq}")
        con.commit()
    finally:
        con.close()


# ---------- built-in sample world ----------
# Used by `make seed` until P1's generator writes data/synth/world.json.

LOCALITIES = [
    "Seelampur", "Lajpat Nagar", "Okhla", "Shahdara", "Karol Bagh",
    "Mustafabad", "Govindpuri", "Narela", "Tughlakabad", "Mayapuri",
]
NAMES = [
    "Raju", "Sunita", "Imran", "Kamla", "Ramesh", "Shabnam", "Mohan", "Rekha", "Salim", "Geeta",
    "Arjun", "Nasreen", "Vijay", "Pooja", "Babloo", "Farida", "Dinesh", "Meena", "Aslam", "Savitri",
]
PLASTICS = {"PET": 18.0, "HDPE": 22.0, "LDPE_film": 8.0, "mixed_plastic": 6.0}
OTHER = {"cardboard": 9.0, "paper": 11.0, "metal": 28.0}
YIELD = 0.85
FRAUD_RATIO = 38.0


def sample_world(seed: int = 7, month_start: datetime = datetime(2026, 9, 1, tzinfo=IST)) -> dict:
    """20 Kabadiwalas over one month. Recyclers A and B are honest (certificates within
    about 10% of what their Verified inflow supports); Recycler C over-claims PET ~38x.
    One receipt is tampered and one ring of 10 receipts reuses 3 photos."""
    rng = random.Random(seed)
    actors = [
        {"actor_id": "rc-a", "role": "recycler", "name": "Recycler A", "locality": "Narela"},
        {"actor_id": "rc-b", "role": "recycler", "name": "Recycler B", "locality": "Mayapuri"},
        {"actor_id": "rc-c", "role": "recycler", "name": "Recycler C", "locality": "Bawana"},
        {"actor_id": "br-1", "role": "brand", "name": "Brand One"},
        {"actor_id": "br-2", "role": "brand", "name": "Brand Two"},
        {"actor_id": "au-1", "role": "auditor", "name": "Auditor"},
    ]
    collectors = []
    for i, name in enumerate(NAMES):
        cid = "kw-raju" if name == "Raju" else f"kw-{name.lower()}"
        actors.append({"actor_id": cid, "role": "kabadiwala", "name": name, "locality": LOCALITIES[i % 10]})
        collectors.append((cid, LOCALITIES[i % 10]))

    receipts = []
    days = 30
    for cid, locality in collectors:
        for day in range(days):
            for _ in range(rng.randint(1, 3)):
                ts = month_start + timedelta(days=day, hours=rng.randint(8, 19), minutes=rng.randint(0, 59))
                if rng.random() < 0.8:
                    material = rng.choice(list(PLASTICS))
                    price = PLASTICS[material]
                    recycler = rng.choices(["rc-a", "rc-b", "rc-c"], weights=[55, 40, 5])[0]
                else:
                    material = rng.choice(list(OTHER))
                    price = OTHER[material]
                    recycler = None
                receipts.append({
                    "collector_id": cid,
                    "material": material,
                    "weight_kg": round(rng.uniform(4, 40), 1),
                    "price_inr_per_kg": price,
                    "locality": locality,
                    "ts": ts.isoformat(),
                    "photo_sha256": f"{rng.getrandbits(256):064x}",
                    "phash": f"{rng.getrandbits(64):016x}",
                    "evidence": {"source": "synthetic"},
                    "recycler_id": recycler,
                })

    # Duplicate-photo ring: 10 receipts reuse 3 photos with 1-3 bits changed
    bases = [rng.getrandbits(64) for _ in range(3)]
    for k, r in enumerate(rng.sample(receipts, 10)):
        flipped = bases[k % 3]
        for _ in range(rng.randint(0, 3)):
            flipped ^= 1 << rng.randrange(64)
        r["phash"] = f"{flipped:016x}"

    month = month_start.strftime("%Y-%m")
    certificates = []
    for recycler in ("rc-a", "rc-b", "rc-c"):
        for material in PLASTICS:
            inflow_t = sum(
                r["weight_kg"] for r in receipts if r["recycler_id"] == recycler and r["material"] == material
            ) / 1000
            if inflow_t == 0:
                continue
            factor = FRAUD_RATIO if (recycler == "rc-c" and material == "PET") else rng.uniform(0.9, 1.1)
            total_t = inflow_t * YIELD * factor
            share = rng.uniform(0.4, 0.6)
            for n, (brand, part) in enumerate((("br-1", share), ("br-2", 1 - share))):
                certificates.append({
                    "certificate_id": f"CERT-{recycler[-1].upper()}-{material}-{n + 1}",
                    "recycler_id": recycler,
                    "brand_id": brand,
                    "month": month,
                    "material": material,
                    "tonnes": round(total_t * part, 3),
                })

    sunita_count = sum(1 for r in receipts if r["collector_id"] == "kw-sunita")
    return {
        "actors": actors,
        "certificates": certificates,
        "receipts": receipts,
        "tamper": [{"collector_id": "kw-sunita", "seq": sunita_count // 2, "set": {"weight_kg": 95.0}}],
    }
