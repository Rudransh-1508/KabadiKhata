# Kabadi Khata

**Proof-of-collection for India's informal recyclers — and a fraud radar for EPR certificates.**
Environmental Hacks (WeMakeDevs × AWS Bharat Builds Tour) · **Waste & Energy** track · **Build It** (local, open-source AWS tools, no AWS account).

> In 2024, CPCB audits of four plastic recyclers turned up **6 lakh fake recycling (EPR) certificates**. Every one claims plastic that a collector like Raju picked up — and nobody can prove who actually collected it. Kabadi Khata lets a kabadiwala prove a collection with one photo and a voice note, and catches the recyclers who certify more than they ever received.
>
> Source: [NGT notice, CPCB/MoEFCC, July 2024](https://www.scconline.com/blog/post/2024/07/31/ngt-issues-notice-cpcb-moefcc-recovery-of-6-lakh-fake-epr-certificates-from-plastic-recycling-companies/). The **38×** fraud case in this project is **our simulation**, not a CPCB finding.

## What it does
A kabadiwala sends a photo of the scale + pile to a chat bot and taps the material and weight (voice later). A **Strands agent** checks the photo and the input agree; if they do, it writes **one hash-chained receipt** and returns a receipt card; if not, it asks **one question and writes nothing**. An **auditor** runs a deterministic **fraud radar** over recycler data; a **brand** sees each certificate's **verified-backed %** but, under **Cedar** policy, never the collectors' identities.

> Channel: **WhatsApp in production; Telegram for the prototype** (Telegram needs no business approval and runs fully locally for Build It).

## Who it's for
See [`docs/personas.md`](docs/personas.md): **Raju** the kabadiwala, **Priya** the brand EPR officer, and the auditor.

## Built on AWS (all open-source, local)
| Tool | Role here |
|---|---|
| **Strands Agents** | The agent + its tools; one guarded write tool (`create_receipt`). |
| **Cedar** | Authorises every API call and the agent's write; denies the brand collector identities. |
| **SAM CLI** (`sam local`) | Runs the APIs as Lambda functions locally. |
| **OpenSearch** | Single data store (receipts, flags, certificates). |

_Infra fallback (per CLAUDE.md): if SAM + OpenSearch aren't green, the API/store run as FastAPI + SQLite, with a `sam local invoke` clip kept for the "Built on AWS" visual. Strands + Cedar satisfy the requirement either way._

## Architecture
_[TODO: P3 — diagram + text. Phone → SAM local API → Strands agent (+Cedar) → OpenSearch; auditor/brand console; nightly-style radar.]_

## Repo layout (P4 parts shown)
```
bot/        telegram_bot.py · cards.py · strings_hi.py · mock_api.py   (Telegram bot, Hinglish, receipt card)
console/    app.py · logic.py                                          (Auditor + Brand Streamlit console)
data/       localities.json · ratecard.json · mock/                    (synthetic/indicative data + fixtures)
docs/       personas.md · demo_script.md
src/        (agent, policy, ledger, radar, api)                        [P1/P2/P3]
eval/       (accuracy + radar precision/recall)                        [P1]
tests/      test_cards.py · test_telegram_bot.py · test_console.py · ...
```

## Run (local)
Prereqs: Python 3.12, Docker (for OpenSearch/SAM). Create a venv and install:
```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r bot/requirements.txt -r console/requirements.txt
```
- **Bot:** put `TELEGRAM_BOT_TOKEN` in `.env` (gitignored), then `python -m bot.telegram_bot`. Flow: `/start` → photo → material → kg → receipt; `/demo` toggles a simulated mismatch; `/hisaab` shows totals.
- **Console:** `streamlit run console/app.py` → switch Auditor / Brand in the sidebar.
- **Full stack / `make demo`:** _[TODO: P3]_

_The bot and console currently run against `bot/mock_api.py` and `data/mock/`; the mock is a one-import swap for P3's real API._

## Evaluation
_[TODO: P1 — scale/material accuracy on held-out photos (state n); radar precision/recall + the smallest fraud ratio caught with zero false flags on honest recyclers.]_

## Honesty & limitations
- All seeded data is labelled **synthetic**; prices in `data/ratecard.json` are **indicative** (not the pitch).
- The radar only sees supply that flows **through the system** — surfaced as the **verified-backed %**, not hidden.
- A photo can be staged; mitigations are perceptual-hash dedupe, mass balance, and auditor-approved physical inspection.
- The **38×** case is our simulation. The 6-lakh figure is the 2024 NGT/CPCB notice only.

## AI tools used
- **Claude Code** (Anthropic) — used for research synthesis, planning, and to write/review parts of the code (bot, console, data, docs). _[TODO: team — add any other AI coding tools used.]_

## Credits & licences
- Fonts: system fonts (Segoe UI/Arial) at runtime; _[TODO: if an OFL font (Noto/DejaVu) is bundled, credit it here]._
- Libraries: python-telegram-bot, Pillow, qrcode, pydub, Streamlit, pandas (see each project's licence).
- _[TODO: P1 — credit any image dataset used, with its licence.]_

## Team
P1 ML/Perception · P2 Agent & Policy · P3 Backend & Data · P4 Product/UX & Story. _[TODO: names.]_

---
🤖 Built with assistance from [Claude Code](https://claude.com/claude-code).
