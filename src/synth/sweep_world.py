"""Sweep worlds for the radar sensitivity eval (CLAUDE.md #5). Everything here is Synthetic.

A sweep world is three months of Receipts with honest Recyclers whose Certificates wobble by
±noise month to month, plus one fraudulent Recycler per over-claim ratio in RATIOS. It also plants
a duplicate-photo ring (R2) and one tampered Receipt (R3), and records the ground truth for all
three, so eval/radar_eval.py can score P3's real rules against it.

The format matches ledger.world.load_world, plus a "ground_truth" key the loader ignores.
The demo world (ledger.world.sample_world) is untouched; sweep worlds are built in memory.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from ledger.chain import IST
from ledger.world import LOCALITIES

RATIOS = (1.2, 1.5, 3.0, 38.0)
HONEST = tuple(f"rc-h{i}" for i in range(1, 7))
PLASTICS = {"PET": 18.0, "HDPE": 22.0, "LDPE_film": 8.0, "mixed_plastic": 6.0}
OTHER = {"cardboard": 9.0, "paper": 11.0, "metal": 28.0}
MONTHS = (datetime(2026, 7, 1, tzinfo=IST), datetime(2026, 8, 1, tzinfo=IST), datetime(2026, 9, 1, tzinfo=IST))
YIELD = 0.85
KABADIWALAS = 15
RING_SIZE, RING_PHOTOS = 10, 3


def fraud_id(ratio: float) -> str:
    return f"rc-f{int(round(ratio * 100))}"


def sweep_world(seed: int, noise: float = 0.15, ratios: tuple[float, ...] = RATIOS) -> dict:
    rng = random.Random(seed)
    fraud = {fraud_id(r): r for r in ratios}
    recyclers = list(HONEST) + list(fraud)

    actors = [{"actor_id": rc, "role": "recycler", "name": rc, "locality": "Bawana"} for rc in recyclers]
    actors += [{"actor_id": "br-1", "role": "brand", "name": "Brand One"},
               {"actor_id": "br-2", "role": "brand", "name": "Brand Two"},
               {"actor_id": "au-1", "role": "auditor", "name": "Auditor"}]
    collectors = []
    for i in range(KABADIWALAS):
        cid, locality = f"kw-{i:02d}", LOCALITIES[i % len(LOCALITIES)]
        actors.append({"actor_id": cid, "role": "kabadiwala", "name": f"Kabadiwala {i:02d}", "locality": locality})
        collectors.append((cid, locality))

    receipts = []
    for cid, locality in collectors:
        for start in MONTHS:
            days = ((start.replace(day=28) + timedelta(days=4)).replace(day=1) - start).days
            for day in range(days):
                for _ in range(rng.randint(1, 3)):
                    ts = start + timedelta(days=day, hours=rng.randint(8, 19), minutes=rng.randint(0, 59))
                    if rng.random() < 0.8:
                        material = rng.choice(list(PLASTICS))
                        price, recycler = PLASTICS[material], rng.choice(recyclers)
                    else:
                        material = rng.choice(list(OTHER))
                        price, recycler = OTHER[material], None
                    receipts.append({
                        "collector_id": cid, "material": material,
                        "weight_kg": round(rng.uniform(4, 40), 1), "price_inr_per_kg": price,
                        "locality": locality, "ts": ts.isoformat(),
                        "photo_sha256": f"{rng.getrandbits(256):064x}",
                        "phash": f"{rng.getrandbits(64):016x}",
                        "evidence": {"source": "synthetic sweep"}, "recycler_id": recycler,
                    })

    # R2: a ring of receipts reusing a few photos with 0-3 bits changed
    bases = [rng.getrandbits(64) for _ in range(RING_PHOTOS)]
    ring = rng.sample(receipts, RING_SIZE)
    for k, r in enumerate(ring):
        flipped = bases[k % RING_PHOTOS]
        for _ in range(rng.randint(0, 3)):
            flipped ^= 1 << rng.randrange(64)
        r["phash"] = f"{flipped:016x}"

    certificates = _certificates(receipts, recyclers, fraud, noise, rng)

    # R3: one receipt edited near the end of one chain (late, so it hides little inflow from R1)
    tampered = rng.choice(collectors)[0]
    chain_len = sum(1 for r in receipts if r["collector_id"] == tampered)
    seq = chain_len - rng.randint(1, 5)

    return {
        "actors": actors,
        "certificates": certificates,
        "receipts": receipts,
        "tamper": [{"collector_id": tampered, "seq": seq, "set": {"weight_kg": 95.0}}],
        "ground_truth": {
            "seed": seed, "noise": noise,
            "fraud_ratio": fraud, "honest": list(HONEST),
            "ring_photo_sha256": sorted(r["photo_sha256"] for r in ring),
            "tampered_collector": tampered,
        },
    }


def _certificates(receipts, recyclers, fraud, noise, rng) -> list[dict]:
    certs = []
    for start in MONTHS:
        month = start.strftime("%Y-%m")
        for recycler in recyclers:
            for material in PLASTICS:
                inflow_t = sum(
                    r["weight_kg"] for r in receipts
                    if r["recycler_id"] == recycler and r["material"] == material and r["ts"].startswith(month)
                ) / 1000
                if inflow_t == 0:
                    continue
                factor = fraud.get(recycler, 1.0) * (1 + rng.uniform(-noise, noise))
                total_t = inflow_t * YIELD * factor
                share = rng.uniform(0.4, 0.6)
                for n, (brand, part) in enumerate((("br-1", share), ("br-2", 1 - share))):
                    certs.append({
                        "certificate_id": f"CERT-{recycler}-{material}-{month}-{n + 1}",
                        "recycler_id": recycler, "brand_id": brand, "month": month,
                        "material": material, "tonnes": round(total_t * part, 4),
                    })
    return certs
