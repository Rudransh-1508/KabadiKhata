# Kabadi Khata

**Proof-of-collection for India's informal recyclers — and a fraud radar for EPR certificates.**
Our entry for **Environmental Hacks** (WeMakeDevs × AWS Bharat Builds Tour) · **Waste & Energy** track · **Build It** (local, open-source AWS tools, no AWS account).
Contributor rules: [`CLAUDE.md`](CLAUDE.md). Vocabulary (use these terms in code, UI and the video): [`CONTEXT.md`](CONTEXT.md).

> In 2024, the NGT took up CPCB's finding of **6 lakh fake recycling (EPR) certificates** from four plastic recyclers. Every one claims plastic that a collector like Raju picked up — and nobody can prove who actually collected it. Kabadi Khata lets a kabadiwala prove a collection with one photo and a voice note, and catches the recyclers who certify more than they ever received.
>
> Source: [NGT notice, CPCB/MoEFCC, July 2024](https://www.scconline.com/blog/post/2024/07/31/ngt-issues-notice-cpcb-moefcc-recovery-of-6-lakh-fake-epr-certificates-from-plastic-recycling-companies/). The **38×** fraud case in this project is **our simulation**, not a CPCB finding.

## What it does
A kabadiwala sends a photo of the scale + pile to a Telegram bot and either taps the material and weight or sends a Hindi voice note. A **Strands agent** checks the photo and the input agree; if they do, it writes **one hash-chained Receipt** and returns a receipt card; if not, it asks **one question and writes nothing**. An **auditor** runs a deterministic **fraud radar** over recycler data; a **brand** sees each Certificate's **verified-backed %** but, under **Cedar** policy, never the collectors' identities.

> Channel: **Telegram only** for this prototype and the demo. *WhatsApp in production; Telegram for the prototype* — Telegram needs no business approval and runs fully locally for Build It. WhatsApp is the production direction, not part of this build.

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
- **Bot:** put `TELEGRAM_BOT_TOKEN` in `.env` (gitignored). Without it `make demo` runs everything except the bot. Flow: `/start` → photo → tap material + kg **or send a Hindi voice note** → receipt card; `/demo` toggles a simulated mismatch; `/hisaab` returns the income-statement image.
- **Console:** http://localhost:8501, switch Auditor / Brand in the sidebar.
- **Real LLM:** set `MOCK_LLM=0` and `GEMINI_API_KEY` in `.env`. Or run the agent and the radar explainer on Groq too: `LLM_PROVIDER=groq` with `GROQ_API_KEYS=key1,key2,...` (a rate-limited key hands the request to the next one).
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
Everything below is measured on **synthetic** data and says so. Scripts and full tables are in `eval/`.

**Fraud radar** (`eval/radar_eval.py`, [`RESULTS_radar.md`](eval/RESULTS_radar.md)). 20 random 3-month worlds: 6 honest
recyclers whose certificates vary ±15% month to month, and one fraudulent recycler each at 1.2×, 1.5×, 3× and 38×.
The rules are the real ones in `src/radar/rules.py` (R1 threshold 1.17).
- **Smallest over-claim caught every time with zero false flags on honest recyclers: 1.5×** (0 of 1,440 honest recycler-months flagged).
- 1.2× is caught 62% of the time; 3× and 38× every time. R1 precision 99%, recall 91%. R2 (duplicate photos) and R3 (broken chain) find every planted case.
- When a chain is tampered, its later receipts stop counting as verified inflow, so an honest recycler that bought from that kabadiwala can be flagged that month. That is the rule working as designed and is reported separately.

**Voice → Stated weight** (`eval/voice_eval.py`, [`RESULTS_voice_sarvam.md`](eval/RESULTS_voice_sarvam.md)). Sarvam Saaras
speech-to-text writes the transcript; code (`src/perception/hinglish.py`) reads the weight and material from it.
30 scripted Hindi/Hinglish lines (fractions like *dedh*, *saadhe teen*, every material, one prompt-injection line):
- **Weight right on 64 of 64 synthetic clips.**
- Material right on 30/30 clips in Sarvam Bulbul voices, 28/30 in the macOS Hindi voice, 3/4 in Gemini voices.
- **Real voice notes from a team member (WhatsApp): weight and material right on 3 of 3.** n is small, so it is reported as 3/3, not a percentage.
- The other 5 script lines, spoken in that team member's cloned voice (Sarvam voice cloning; synthetic, and from the same
  vendor as the transcriber, so an easier test than real phone audio; never counted as real): 5 of 5, including the
  prompt-injection line, which stays a Stated weight to check, not an instruction.

**Photo → Scale reading** (`eval/photo_eval.py`, scored once on the held-out split). Photos are the team's 30
AI-generated kabadi scale images ([Kaggle](https://www.kaggle.com/datasets/oneshikaaa/kabadiwala)), split 20 for tuning and
10 held out, labelled by a person. Read by Groq `qwen/qwen3.8-27b` (prompt v4); n = 10, 6 with a readable dial:
- **kg within ±5%: 2 of 6.** Within ±5% or ±1 kg (about one dial tick): 4 of 6. One large miss (25 kg read as 1.5).
- **Material right: 9 of 10.**
- 4 of the held-out dials were garbled by the image generator; the model refused only 1 of them. Shown a broken dial, it
  "corrects" the printed numbers and reads it anyway.

What this means for the design: the photo reading is never trusted alone. The agent writes a Receipt only when the Scale
reading and the kabadiwala's Stated weight (taps or voice) agree within 10%; otherwise it asks one question in Hindi and
writes nothing. A misread photo costs a question, not a false Receipt.

## Honesty & limitations
- All seeded data is labelled **synthetic**; prices in `data/ratecard.json` are **indicative** (not the pitch).
- The radar only sees supply that flows **through the system** — surfaced as the **verified-backed %**, not hidden.
- A photo can be staged; mitigations are perceptual-hash dedupe, mass balance, and auditor-approved physical inspection.
- The **38×** case is our simulation. The 6-lakh figure is the 2024 NGT/CPCB notice only.

## AI tools used
- **Claude Code** (Anthropic) — the only AI coding tool used: research synthesis, planning, and writing/reviewing the code (bot, console, data, docs, and the backend/agent/policy).

## Credits & licences
- Fonts: no third-party fonts are bundled — cards render with the OS system font at runtime (Segoe UI/Arial on Windows, DejaVu on Linux, Pillow's built-in default if none is found).
- Libraries: python-telegram-bot, Pillow, qrcode, pydub, Streamlit, pandas, FastAPI, Uvicorn, Mangum, opensearch-py, httpx, honcho, Strands Agents, OpenAI Python SDK (the client for Groq's OpenAI-compatible API), cedarpy (see each project's licence). OpenSearch runs from the `opensearchproject/opensearch` image (Apache-2.0).
- **Eval photos:** "kabadiwala" dataset by the team (Apache-2.0), [kaggle.com/datasets/oneshikaaa/kabadiwala](https://www.kaggle.com/datasets/oneshikaaa/kabadiwala). AI-generated images (made with Google's Nano Banana image model), labelled synthetic.
- **Speech:** [Sarvam AI](https://www.sarvam.ai) Saaras (speech-to-text, used by `transcribe`) and Bulbul (text-to-speech, synthetic eval clips) and voice cloning (synthetic clips in a team member's voice, with their recordings) via their API; the macOS "Lekha" Hindi voice for more synthetic clips.
- **Vision:** [Groq](https://groq.com) serving `qwen/qwen3.8-27b` reads the scale photo, with Google Gemini (`gemini-flash-latest`, via the `google-genai` SDK) as the fallback; OpenAI and xAI Grok are optional further fallbacks. Gemini is also the fallback transcriber.

## Team
**Vanshika** — P1 ML/Perception · **Aarushi** — P2 Agent & Policy · **Rudransh** — P3 Backend & Data · **Sparsh** — P4 Product/UX & Story.

## Background research
See [`research/00_SHORTLIST.md`](research/00_SHORTLIST.md) for the candidate ideas scored against the judging criteria, and `research/01`–`04` for problem statements, past winners, Delhi pain points, and the data/stack reality check.

---
🤖 Built with assistance from [Claude Code](https://claude.com/claude-code).
