# API (P3): FastAPI on SQLite, port 3000

```bash
make install        # creates .env from .env.example (MOCK_LLM=1), then uv sync
make seed           # data/kk.db from data/synth/world.json, or the built-in sample world
make api            # http://localhost:3000/docs for the interactive schema
make test
```

Every request needs `X-Principal: <actor_id>` (e.g. `kw-raju`, `au-1`, `br-1`). A policy denial is HTTP 403 with
`{"denied_by": "cedar", "action": ..., "reason": ...}`: show it as the red "Denied by Cedar policy" banner.

## Endpoints

| Method / path | For | Returns |
|---|---|---|
| `POST /collections` | bot | Body is `common.models.CollectionRequest`. Returns P2's `CollectionResult`: `{"status": "receipt", "receipt": {...}}` or `{"status": "question", "question_hi": ...}`, plus `trace`. The photo is saved as `data/photos/<receipt.photo_sha256>.jpg`. |
| `GET /receipts?collector_id=` | bot, income statement | `{"receipts": [...], "monthly": [{"month", "count", "weight_kg", "total_inr"}], "chain": {"ok", ...}}`. Months are India time. Show "chain verified" only when `chain.ok`. |
| `GET /verify/{collector_id}` | tamper demo | `{"ok", "length", "broken_at_seq", "reason"}` |
| `PUT /actors/{actor_id}` | bot `/start` | Body `{"name", "locality"}`. Registers a Kabadiwala; 409 if the ID belongs to another role. |
| `GET /actors?role=` | console | Actors, e.g. recyclers and brands for the role switcher |
| `POST /radar/run` | auditor | Optional body `{"month": "2026-09"}`. Runs R1-R3 and returns all flags, highest score first. Earlier decisions are kept. |
| `GET /flags` | auditor | Same list without re-running |
| `POST /flags/{flag_id}/decision` | auditor | Body `{"decision": "inspect" \| "dismiss"}`. Records who and when. |
| `GET /certificates?brand_id=` | brand | The brand's Certificates, each with `verified_backed_pct` |
| `GET /provenance/{certificate_id}` | brand | `verified_inflow_t`, `recycler_certified_t`, `verified_backed_pct`, `by_locality` (no Kabadiwala identities) |
| `GET /photos/{photo_sha256}.jpg` | auditor | The scale photo of a live Receipt (seeded Receipts have none) |

## Actions passed to `policy.authz.is_allowed` (for P2's Cedar policies)

Principals are `Actor::"<X-Principal>"`. Resources are dicts; entity references are written as `Actor::"<id>"`.

| Action | Resource | Who should be allowed |
|---|---|---|
| `create_collection` | `{"type": "Chain", "collector": Actor}` | the Kabadiwala whose Chain it is |
| `read_receipt` | `{"type": "Chain", "collector": Actor}` | that Kabadiwala; the auditor. **Brand denied: spine beat 4.** |
| `verify_chain` | `{"type": "Chain", "collector": Actor}` | that Kabadiwala; the auditor |
| `read_receipt_pii` | `{"type": "Photo", "id": sha256}` | the auditor |
| `register` | `{"type": "Actor", "id": Actor}` | the principal registering itself |
| `list_actors` | `{"type": "Directory", "role": str \| None}` | anyone signed in |
| `run_radar`, `read_flags` | `{"type": "Radar"}` | the auditor |
| `approve_flag` | `{"type": "Flag", "id": str, "rule": str}` | the auditor (the agent is already forbidden) |
| `read_provenance` | `{"type": "Certificate", "id": str, "buyer": Actor}` | the brand that bought it; the auditor |

## Fraud rules (`src/radar/rules.py`)

| Rule | Flags when | Tuning |
|---|---|---|
| R1 mass balance | certified tonnes ÷ (Verified inflow × 0.85) > 1.17 for a recycler, material and month | `KK_R1_THRESHOLD` |
| R2 duplicate photo | two or more Receipts' phashes are within 6 bits | `KK_R2_MAX_DISTANCE` |
| R3 broken chain | a Kabadiwala's Chain fails `verify` | none |

Receipts at or after a break in their Chain don't count as Verified inflow.

## Demo commands

```bash
# Tamper: live on screen, then verify
sqlite3 data/kk.db "UPDATE receipts SET weight_kg = 40 WHERE collector_id = 'kw-raju' AND seq = 0"
curl -s localhost:3000/verify/kw-raju -H 'X-Principal: kw-raju'
make tamper COLLECTOR=kw-raju SEQ=0 KG=40     # backup if typing live goes wrong

# Built on AWS: the same app as an arm64 Lambda (Docker must be running)
make sam-invoke
```
