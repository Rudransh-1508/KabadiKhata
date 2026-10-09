"""`make reindex`: rebuild the OpenSearch copy from the SQLite ledger."""

import os
import sys

from ledger.store import Store
from search.mirror import SearchUnavailable, mirror_from_env


def reindex(store: Store) -> str:
    mirror = mirror_from_env()
    if mirror is None:
        return "search copy off (KK_OPENSEARCH_URL not set)"
    try:
        return f"indexed {mirror.reindex(store.all_receipts())} receipts into {mirror.url}"
    except SearchUnavailable as exc:
        return f"search copy skipped, OpenSearch unavailable at {mirror.url} ({exc}); run `make up` then `make reindex`"


if __name__ == "__main__":
    print(reindex(Store(os.getenv("KK_DB_PATH", "data/kk.db"))))
    sys.exit(0)
