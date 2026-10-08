"""`make seed`: rebuild the database from data/synth/world.json, or the built-in sample world."""

import json
import os
import sys
import time
from pathlib import Path

from ledger.store import Store
from ledger.world import load_world, sample_world
from search.reindex import reindex

WORLD = Path("data/synth/world.json")


def main() -> int:
    db = Path(os.getenv("KK_DB_PATH", "data/kk.db"))
    for p in (db, db.with_name(db.name + "-wal"), db.with_name(db.name + "-shm")):
        p.unlink(missing_ok=True)
    if WORLD.exists():
        world, source = json.loads(WORLD.read_text()), str(WORLD)
    else:
        world, source = sample_world(), "built-in sample world (P1's data/synth/world.json not found)"
    started = time.monotonic()
    store = Store(db)
    counts = load_world(store, world)
    print(f"Seeded {db} from {source} in {time.monotonic() - started:.1f}s: {counts}")
    # One bulk copy at the end; tampering above edits SQLite only, as an attacker would
    print(reindex(store))
    return 0


if __name__ == "__main__":
    sys.exit(main())
