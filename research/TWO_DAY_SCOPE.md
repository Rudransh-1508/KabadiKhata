# Kabadi Khata — 2-day scope & priorities (read this first)

**One job of this page:** so every teammate and every agent builds the same 4 things first and nothing else until those 4 work.

- **Track:** Waste & Energy · **Mode:** Build It only · **Idea is settled — do not re-litigate it.**
- **Clock:** Fri Oct 9 (today, partial) + Sat Oct 10 = **2 build days**. Sun Oct 11 = freeze, film, ship. **Submit by 18:00 IST** (hard deadline 20:00).
- Rules of record: [`CLAUDE.md`](../CLAUDE.md) (wins on conflicts) and [`KABADI_KHATA_SCOPED_DOWN.md`](KABADI_KHATA_SCOPED_DOWN.md) (owners, hour-by-hour). This page sets **priority order** when time is short.

---

## The spine — P0. These 4 beats must work. Protect them above everything.
If the clock runs out, a demo with only these still wins the track. Each is one video moment.

1. **Receipt with a refusal.** Telegram: photo + Hindi voice (or tap buttons) → Strands agent checks they agree → **on a mismatch it asks ONE Hindi question and writes nothing**; on a pass it writes **one** hash-chained receipt and sends the card.
2. **Fraud caught.** Auditor runs the radar → **Recycler C flagged** by R1 mass balance → auditor clicks *Request inspection*.
3. **Tamper breaks the chain.** Edit one receipt in the store → `GET /verify` shows the chain broken at seq N.
4. **Cedar denial.** Brand tries to see a kabadiwala's identity → red **"Denied by Cedar policy"**; provenance shown only in aggregate.

**Do not start anything below until all 4 beats run end-to-end on the real stack.**

---

## Priority order

| Prio | Build | When |
|---|---|---|
| **P0 — spine** | The 4 beats above | Day 1 → M1, Day 2 → M2 |
| **P1 — raises score** (after spine is green) | Verified-backed % on certificates (CLAUDE.md #4) · "मेरा हिसाब" income-statement image (#7) · radar sensitivity sweep 1.2×/1.5×/3×/38× + held-out photo eval numbers (#5, #6) · R2 duplicate-photo rule · Hindi voice (taps already cover the spine) | Day 2 |
| **P2 — nice to have / cut first** | OpenSearch Dashboards · QR-scan handoff UI · Builder Center blog | Day 2 spare / after submission |

---

## Hard infra cutoff (decide today, don't bleed Day 1)
The two risky pieces on Windows are **`sam build --use-container`** and **OpenSearch on WSL**. Apply the CLAUDE.md fixes (SAM↔OpenSearch network, 60s Lambda timeout, OGG→WAV in the bot).

> **Cutoff — Fri 18:00:** if SAM + OpenSearch are not both green by 6pm today, **fall back to plain FastAPI + SQLite** for the API and store, and keep a `sam local invoke` clip + `template.yaml` in the repo for the "Built on AWS" visual. Strands + Cedar already satisfy the AWS requirement. **Do not lose a day to infra.**

---

## Milestones
- **M1 — Fri ~22:00:** Telegram photo → agent → hash-chained receipt → card on a phone (spine beat 1). If not green, *everyone* stays on M1; nothing new starts.
- **M2 — Sat ~20:00:** feature-complete — all 4 beats + whatever P1 is done. Then a full timed run of the video script on the real system.
- **Sun 11:00 — feature freeze.** Only demo-blocking fixes after this. Film, edit, submit by 18:00.

## Cut lines, in order (drop from the top when behind)
Blog → Dashboards → QR UI → R2 duplicate rule → radar explainer LLM (use template text) → voice (taps only) → OpenSearch (SQLite). **Never cut any of the 4 spine beats, Cedar, or R1 mass balance.**

## Also, today (cheap, high-leverage)
- Someone films **10 seconds of a real kabadiwala's scale + pile** (with consent) for the hook — wins Idea & Impact. Nothing depends on it, but get it if you can.
- All 4: Builder Center **student verification submitted** (required to compete) + first commit from each person (history must match the event).

## Non-negotiable rules (full list in CLAUDE.md)
Code decides · human approves · LLM only explains. One write tool (`create_receipt`), guarded in code **and** Cedar. Label everything synthetic. Pitch line exactly as CLAUDE.md #8 — **38× is our simulation, not a CPCB finding.** Only build what appears in the 3-minute video.
