"""`make tamper`: edit one stored Receipt behind the ledger's back, for the video's tamper demo.

    make tamper COLLECTOR=kw-raju SEQ=0 KG=40
"""

import os
import sys

from ledger import chain
from ledger.store import Store
from ledger.world import tamper


def main(collector_id: str, seq: str, kg: str) -> int:
    store = Store(os.getenv("KK_DB_PATH", "data/kk.db"))
    before = next((r for r in store.receipts_for(collector_id) if r.seq == int(seq)), None)
    if before is None:
        print(f"no receipt {collector_id}#{seq}")
        return 1
    tamper(store, collector_id, int(seq), {"weight_kg": float(kg)})
    print(f"{before.receipt_id}: weight_kg {before.weight_kg} -> {kg}")
    print(chain.verify(store.receipts_for(collector_id)).model_dump())
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:]))
