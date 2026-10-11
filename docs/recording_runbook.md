# Recorder's runbook — demo video

One page. Any team member can record the demo; nothing here needs a specific person. Follow it top to bottom.
Shot order and voiceover live in [`demo_script.md`](demo_script.md); this is the operational checklist that makes those shots run.

## Before you start (one-time)

1. Clone the repo. Needs [uv](https://docs.astral.sh/uv/), Python 3.12 and `make` (on Windows use Git Bash or WSL).
2. Create `.env` (gitignored — never commit it). You need:
   - `TELEGRAM_BOT_TOKEN=…` — required for every phone shot.
   - `GEMINI_API_KEY=…` with `MOCK_LLM=0` for the real agent, **or** `MOCK_LLM=1` for canned replay (no key, identical every take).
   - `SARVAM_API_KEY=…` only if you record a real voice note; otherwise skip it.
   - Get these from Sparsh if you don't have your own.
3. Install Telegram (phone or desktop) and a screen recorder.

> **Only one person runs the bot at a time.** Two `make bot` processes on the same token fight over Telegram updates and neither works. Agree who drives the bot during the shoot.

## Start the stack (three terminals, keep each open)

Run each in its own terminal window — don't background them; a memory reaper can kill backgrounded shells mid-take.

```bash
make seed      # once, first: loads the synthetic month into data/kk.db
```

| Terminal | Command | What it is |
|---|---|---|
| 1 | `make api`     | FastAPI on :3000 — agent, ledger, radar, Cedar |
| 2 | `make console` | Streamlit console on :8501 — Auditor / Brand (switch in sidebar) |
| 3 | `make bot`     | the Telegram bot |

`make demo` runs seed + api + console + bot together under one process if you'd rather not manage three terminals (OpenSearch is skipped if Docker is down — that's fine).

Pre-warm every input once before recording (send the photo, run the radar, etc.) so the disk cache / `MOCK_LLM` makes each take identical.

## The takes (≤ 2:55 total; full voiceover in `demo_script.md`)

Bot commands: `/start` · `/language` · `/demo` · `/hisaab` · `/help` · `/cancel`.

1. **Phone — receipt + refusal (0:30–1:15).** In Telegram: `/start` → pick language → send a photo of the scale → tap material + kg (or a voice note) → **receipt card** appears (QR, ₹, SYNTHETIC watermark). Then `/demo` (turns on the simulated 12 kg mismatch) and repeat with a **wrong** weight (e.g. 20) → the agent asks **one Hindi question and sends no receipt**. Grab ~3s of the Strands trace in terminal 1.
2. **Phone — income (1:15–1:28).** `/hisaab` → the month totals / income-statement image.
3. **Console — auditor (1:28–2:05).** Console sidebar → **Auditor** → run the radar → **Recycler C flagged (claims 38× its verified inflow)** → open evidence → **Request inspection**.
4. **Tamper (2:05–2:20).** Backup command (do this if you don't edit the DB live on screen):
   ```bash
   make tamper COLLECTOR=kw-raju SEQ=0 KG=40
   curl -s localhost:3000/verify/kw-raju -H 'X-Principal: kw-raju'
   ```
   Show the response: the chain is **broken at seq N**. (Re-seed afterwards: `make seed`.)
5. **Console — brand (2:20–2:32).** Sidebar → **Brand** → a certificate shows **verified-backed %** → click a collector identity → red **"Denied by Cedar policy."**
6. **Architecture overlay (2:32–2:45).** ~10s card: Strands · Cedar · SAM CLI · OpenSearch + the eval numbers from the README.
7. **Closing card (2:45–3:00).** The "what changes" card.

## Golden rules while filming

- Everything on screen that is synthetic is **labelled synthetic**.
- The **38× is our simulation**, never a CPCB finding. Don't call it a 2026 scandal.
- Channel line: **"WhatsApp in production, Telegram for the prototype."**
- Pitch stat, said exactly: *"In 2024, the NGT took up CPCB's finding of 6 lakh fake recycling (EPR) certificates from four plastic recyclers."*

## After the take

- Open the final upload **signed out** to confirm it plays.
- Length ≤ **3:00** hard.
- Re-seed (`make seed`) if you ran the tamper step, so the stack is clean for the next take.
