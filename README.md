# Kabadi Khata

Verified scrap receipts for kabadiwalas, and a fraud check on plastic recycling certificates. Our entry for WeMakeDevs **Environmental Hacks** (Bharat Builds Tour, AWS), Waste and Energy track. Rules for contributors: [`CLAUDE.md`](CLAUDE.md). Vocabulary: [`CONTEXT.md`](CONTEXT.md).

> Draft sections from P3 (run and architecture). P4 owns the final README.

## Run it

Needs [uv](https://docs.astral.sh/uv/) and Python 3.12. Docker for OpenSearch and the SAM step; without it everything else still runs.

```bash
make demo        # creates .env (MOCK_LLM=1, no API key needed), installs, seeds, starts everything
```

`make demo` seeds a synthetic month (labelled synthetic everywhere) and starts the API on http://localhost:3000. Other targets: `make test`, `make seed`, `make api`, `make tamper`, `make sam-invoke`. Endpoint reference: [`src/api/README.md`](src/api/README.md).

## Architecture

```
 Kabadiwala (Telegram)            Auditor / Brand (Streamlit console)
        │ photo + taps or voice              │
        ▼                                    ▼
 ┌────────────────────── FastAPI (port 3000) ───────────────────────┐
 │ every request → policy.authz.is_allowed()  (Cedar)               │
 │                                                                  │
 │ POST /collections → Strands agent ── read_photo, transcribe,     │
 │                     (src/agent)       phash_check, consistency   │
 │                          │ create_receipt: only if consistent    │
 │                          ▼            and Cedar allows           │
 │                  ledger: hash-chained Receipts per Kabadiwala    │
 │                          │                                       │
 │ /radar/run ──────► radar: R1 mass balance · R2 duplicate photo   │
 │                          · R3 broken chain → Flags → auditor     │
 │ /certificates, /provenance → verified-backed % for brands        │
 └──────────────────────────┬───────────────────────────────────────┘
                            ▼
        SQLite ledger (data/kk.db) + data/photos/ ──copy──► OpenSearch
                                                        (search + tonnage chart)
```

- **AWS open-source tools:** Strands Agents (the agent), Cedar (every access decision), SAM CLI (`template.yaml` runs the same app as an arm64 Lambda; `make sam-invoke`), OpenSearch (read-only search copy for the auditor; [ADR 0002](docs/adr/0002-opensearch-as-read-only-search-copy.md)).
- **Why FastAPI + SQLite, not SAM + OpenSearch:** [`docs/adr/0001-fastapi-sqlite-demo-stack.md`](docs/adr/0001-fastapi-sqlite-demo-stack.md).
- **Tamper evidence:** each Receipt's hash covers every field and the previous Receipt's hash; its ID comes from its hash. Editing any stored Receipt makes `/verify` report the exact position. Corrections are new entries, never edits.

---

## Research


Research for WeMakeDevs **Environmental Hacks** (Bharat Builds Tour, AWS), 8–11 Oct 2026.

**Start here:** [`research/00_SHORTLIST.md`](research/00_SHORTLIST.md). It has the 4 candidate ideas, scores against the judging criteria, and a 2-day plan.

| File | What's inside |
|---|---|
| `research/01_problem_statements.md` | Official SIH and government problem statements (2024–2026) mapped to the 3 tracks |
| `research/02_winning_projects.md` | Winners from past environment hackathons, plus First Commit (event 1 of this tour) |
| `research/03_delhi_pain_points.md` | Current Delhi problems from news and X, ranked top 10 |
| `research/04_data_and_stack.md` | Delhi data APIs (tested) and a reality check on the AWS Build It tools |
| `research/raw/` | Raw scraped data (SIH PS dumps, X search results, API samples) |
