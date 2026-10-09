# Kabadi Khata

**Proof-of-collection for India's informal recyclers — and a fraud radar for EPR certificates.**
Our entry for **Environmental Hacks** (WeMakeDevs × AWS Bharat Builds Tour) · **Waste & Energy** track · **Build It** (local, open-source AWS tools, no AWS account).
Contributor rules: [`CLAUDE.md`](CLAUDE.md). Vocabulary (use these terms in code, UI and the video): [`CONTEXT.md`](CONTEXT.md).

> In 2024, the NGT took up CPCB's finding of **6 lakh fake recycling (EPR) certificates** from four plastic recyclers. Every one claims plastic that a collector like Raju picked up — and nobody can prove who actually collected it. Kabadi Khata lets a kabadiwala prove a collection with one photo and a voice note, and catches the recyclers who certify more than they ever received.
>
> Source: [NGT notice, CPCB/MoEFCC, July 2024](https://www.scconline.com/blog/post/2024/07/31/ngt-issues-notice-cpcb-moefcc-recovery-of-6-lakh-fake-epr-certificates-from-plastic-recycling-companies/). The **38×** fraud case in this project is **our simulation**, not a CPCB finding.

## What it does
A kabadiwala sends a photo of the scale + pile to a chat bot and taps the material and weight (voice later). A **Strands agent** checks the photo and the input agree; if they do, it writes **one hash-chained Receipt** and returns a receipt card; if not, it asks **one question and writes nothing**. An **auditor** runs a deterministic **fraud radar** over recycler data; a **brand** sees each Certificate's **verified-backed %** but, under **Cedar** policy, never the collectors' identities.

> Channel: **WhatsApp in production; Telegram for the prototype** (Telegram needs no business approval and runs fully locally for Build It).

## Who it's for
See [`docs/personas.md`](docs/personas.md): **Raju** the kabadiwala, **Priya** the brand EPR officer, and the auditor.

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

- **Tamper evidence:** each Receipt's hash covers every field and the previous Receipt's hash; its ID comes from its hash. Editing any stored Receipt makes `/verify` report the exact broken position. Corrections are new entries, never edits.

## Built on AWS (all open-source, local)
| Tool | Role here |
|---|---|
| **Strands Agents** | The agent + its tools; one guarded write tool (`create_receipt`). |
| **Cedar** | Authorises every API call and the agent's write; denies the brand collector identities. |
| **SAM CLI** (`sam local invoke`) | `template.yaml` runs the same app as an arm64 Lambda; a `sam local invoke` clip is the "Built on AWS" visual. |
| **OpenSearch** | Read-only search copy of the ledger for the auditor ([ADR 0002](docs/adr/0002-opensearch-as-read-only-search-copy.md)); SQLite stays the system of record. |

_Stack decision (not a fallback): the demo runs on **FastAPI + SQLite** per [ADR 0001](docs/adr/0001-fastapi-sqlite-demo-stack.md). Strands + Cedar satisfy the AWS requirement; nothing in the demo spine depends on OpenSearch._

## Run (local)
Needs [uv](https://docs.astral.sh/uv/), Python 3.12 and `make` (on Windows: Git Bash or WSL). Docker is only for OpenSearch and the SAM step; everything else runs without it.
```bash
make demo        # creates .env (MOCK_LLM=1, no API key needed), installs, starts OpenSearch if Docker is up,
                 # seeds a synthetic month, then runs the API (:3000), the console (:8501) and the bot
make smoke       # in a second terminal: checks every endpoint and the 4 spine beats (14 checks), then re-seeds
```
- **Bot:** put `TELEGRAM_BOT_TOKEN` in `.env` (gitignored). Without it `make demo` runs everything except the bot. Flow: `/start` → photo → material → kg → receipt card; `/demo` toggles a simulated mismatch; `/hisaab` returns the income-statement image.
- **Console:** http://localhost:8501, switch Auditor / Brand in the sidebar.
- **Real LLM:** set `MOCK_LLM=0` and `GEMINI_API_KEY` in `.env`.
- **One at a time:** `make api`, `make bot`, `make console`, `make up` / `make down` (OpenSearch), `make seed`, `make reindex`.
- **Video helpers:** `make tamper COLLECTOR=kw-raju SEQ=0 KG=40` (backup for the live `sqlite3` edit), `make sam-invoke` (the app as an arm64 Lambda: one receipt written, one Cedar denial).

Endpoint and Cedar action reference: [`src/api/README.md`](src/api/README.md).

## Repo layout
```
bot/        telegram_bot.py · cards.py · strings_hi.py · mock_api.py   (Telegram bot, Hinglish, receipt + income cards)
console/    app.py · logic.py                                          (Auditor + Brand Streamlit console)
data/       localities.json · ratecard.json · mock/                    (synthetic/indicative data + fixtures)
docs/       personas.md · demo_script.md · adr/                        (personas, 3-min video script, decisions)
src/        agent · policy · ledger · radar · api                      (P1/P2/P3: agent, Cedar, hash chain, fraud rules, FastAPI)
eval/       accuracy + radar precision/recall                          [P1]
tests/      test_cards.py · test_telegram_bot.py · test_console.py · ...
```

## Evaluation
_[TODO: P1 — scale/material accuracy on the held-out photos (state n); radar precision/recall + the smallest fraud ratio caught with zero false flags on honest recyclers.]_

## Honesty & limitations
- All seeded data is labelled **synthetic**; prices in `data/ratecard.json` are **indicative** (not the pitch).
- The radar only sees supply that flows **through the system** — surfaced as the **verified-backed %**, not hidden.
- A photo can be staged; mitigations are perceptual-hash dedupe, mass balance, and auditor-approved physical inspection.
- The **38×** case is our simulation. The 6-lakh figure is the 2024 NGT/CPCB notice only.

## AI tools used
- **Claude Code** (Anthropic) — research synthesis, planning, and to write/review parts of the code (bot, console, data, docs, and the backend/agent/policy). _[TODO: team — add any other AI coding tools used.]_

## Credits & licences
- Fonts: system fonts (Segoe UI/Arial) at runtime; _[TODO: if an OFL font (Noto/DejaVu) is bundled, credit it here]._
- Libraries: python-telegram-bot, Pillow, qrcode, pydub, Streamlit, pandas, FastAPI, Uvicorn, Mangum, opensearch-py, httpx, honcho, Strands Agents, cedarpy (see each project's licence). OpenSearch runs from the `opensearchproject/opensearch` image (Apache-2.0).
- _[TODO: P1 — credit any image dataset used, with its licence.]_

## Team
P1 ML/Perception · P2 Agent & Policy · P3 Backend & Data · P4 Product/UX & Story. _[TODO: names.]_

## Background research
See [`research/00_SHORTLIST.md`](research/00_SHORTLIST.md) for the candidate ideas scored against the judging criteria, and `research/01`–`04` for problem statements, past winners, Delhi pain points, and the data/stack reality check.

---
🤖 Built with assistance from [Claude Code](https://claude.com/claude-code).
