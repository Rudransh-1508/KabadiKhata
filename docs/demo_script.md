# 3-minute demo video script

Target ≤ 2:55. Recorded, no live demo. Each beat maps to a judging criterion. Pitch-line and honesty discipline per [`../CLAUDE.md`](../CLAUDE.md) #8.

**Golden rules while filming:** everything on screen is labelled synthetic where it is; the **38× is our simulation**, never a CPCB finding; the phone channel is "WhatsApp in production, Telegram for the prototype."

| Time | On screen | Voiceover (tight) | Criterion |
|---|---|---|---|
| 0:00–0:18 | News headline / stat card: "6 lakh fake EPR certificates." | "In 2024, CPCB audits of four plastic recyclers turned up 6 lakh fake recycling certificates. Every one claims plastic that a collector like Raju picked up — and nobody can prove who actually collected it." | Idea & Impact |
| 0:18–0:30 | Photo of a real kabadiwala's scale + pile (if filmed), else the Raju persona card. | "Raju collects ~150 kg a day in Delhi and sells for cash. Nothing's on record — so the 2026 rules push him out, and brands can't trust their certificates." | Idea & Impact |
| 0:30–1:15 | **Phone (Telegram, Hinglish):** send photo of scale → tap material → tap kg → **receipt card** appears (QR, ₹, SYNTHETIC watermark). Then `/demo` and repeat with a wrong weight → the agent replies **one Hinglish question and sends NO receipt**. Cut to the Strands agent trace for ~3s. | "He sends a photo, taps the material and weight. A Strands agent checks they agree and writes one tamper-evident receipt. When the weight doesn't match the photo, it refuses — it asks one question and writes nothing. Code decides, the agent explains." | Usability, Execution, AWS |
| 1:15–1:28 | `/hisaab` → his month's totals (fold the income-statement image in here if ready). | "And Raju gets something he never had: a verified income history — proof for a micro-loan." | Idea & Impact |
| 1:28–2:05 | **Auditor console:** Run radar → **Recycler C flagged, claims 38× its verified inflow** (bar: claimed vs verified) → evidence + note → click **Request inspection**. | "On the other side, an auditor runs the fraud radar. Deterministic rules — not the LLM — catch Recycler C claiming thirty-eight times the plastic that was ever verified into it. The auditor approves an inspection." | Impact, Execution |
| 2:05–2:20 | **Tamper demo:** edit one receipt in the store → `GET /verify` shows the chain **broken at seq N**. | "Try to doctor a receipt, and the hash chain breaks — exactly where." | Execution, AWS |
| 2:20–2:32 | Switch to **Brand** → certificate shows **verified-backed %**; click identity → red **"Denied by Cedar policy."** | "A brand sees how much of a certificate is really backed by verified collection — and Cedar won't let it unmask the collectors. Provenance in aggregate only." | AWS, Usability |
| 2:32–2:45 | ~10s architecture overlay: **Strands · Cedar · SAM CLI · OpenSearch** + eval numbers (scale/material accuracy; smallest fraud ratio caught with 0 false flags). | "Built locally on open-source AWS tools: Strands, Cedar, SAM, OpenSearch. Here are the numbers." | AWS, Execution |
| 2:45–3:00 | "What changes" card. | "Raju gets a record and a fair price. Brands get certificates they can defend. The seeded data is synthetic — the radar only sees supply that flows through the system — but the mechanism is real." | Impact, honesty |

## Recording notes
- Pre-warm the demo inputs (disk cache / MOCK_LLM) so every take is identical.
- Show the phone flow as a screen recording + a hand holding the phone.
- Keep the Strands trace and SAM terminal on screen only long enough to read one line.
- Open the final upload **signed out** to confirm it plays. Length ≤ 3:00 hard.
