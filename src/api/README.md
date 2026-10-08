# API (P3): FastAPI on SQLite, port 3000

```bash
make install        # uv sync --extra dev
MOCK_LLM=1 make api # http://localhost:3000/docs for the interactive schema
make test
```

Every request needs `X-Principal: <actor_id>` (e.g. `kw-raju`). A policy denial is HTTP 403 with
`{"denied_by": "cedar", "action": ..., "reason": ...}`: show it as the red "Denied by Cedar policy" banner.

| Method / path | Returns |
|---|---|
| `POST /collections` | Body is `common.models.CollectionRequest`. Returns P2's `CollectionResult`: `{"status": "receipt", "receipt": {...}}` or `{"status": "question", "question_hi": ...}`, plus `trace`. The photo is saved as `data/photos/<receipt.photo_sha256>.jpg`. |
| `GET /receipts?collector_id=` | `{"receipts": [...], "monthly": [{"month", "count", "weight_kg", "total_inr"}]}`. Months are India time. |
| `GET /verify/{collector_id}` | `{"ok", "length", "broken_at_seq", "reason"}` |

Tamper demo for the video:
```bash
sqlite3 data/kk.db "UPDATE receipts SET weight_kg = 40 WHERE collector_id = 'kw-raju' AND seq = 0"
curl -s localhost:3000/verify/kw-raju -H 'X-Principal: kw-raju'
```
