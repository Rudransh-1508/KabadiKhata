# Kabadi Khata blog — asset → post map (for publishing)

The blog is split into **four standalone posts**, one per teammate, all published on
**AWS Builder Center** (that's where the Environmental Hacks blog prize is judged —
top 5 blogs each win AirPods). Each post already has its images embedded inline with
`![](blog_assets/…)`; when you publish, **upload the images listed for your part** and
let the editor replace the local paths with its own URLs. The alt text is already
written, so keep it.

All images live in `docs/blog_assets/`. All of them are **synthetic demo data** and
are watermarked/labelled as such.

## Who publishes what

| Post file | Topic | Suggested owner* | Images to upload (in order) |
|---|---|---|---|
| `BLOG_PART1_product.md` | The problem & the product | P4 · Sparsh | `01_landing_hero.jpg`, `hisaab_card.png`, `02_console_home.jpg` |
| `BLOG_PART2_perception.md` | Reading a photo + Hindi voice, failing closed | P1 · Vanshika | `architecture.png`, `receipt_card.png` |
| `BLOG_PART3_agent_policy.md` | One write tool + the Cedar policy layer | P2 · Aarushi | `architecture.png`, `07_cedar_denied.jpg`, `04_radar_flag_detail.jpg` |
| `BLOG_PART4_ledger_radar.md` | Hash chain + the fraud radar | P3 · Rudransh | `05_chain_broken.jpg`, `03_fraud_radar_list.jpg`, `04_radar_flag_detail.jpg`, `06_brand_verified_backed.jpg` |

\* Owner mapping is a suggestion based on who built each area — swap if needed.

Note: `architecture.png` is used in **both** Part 2 and Part 3, and
`04_radar_flag_detail.jpg` is used in **both** Part 3 and Part 4. That's intentional —
each post stands alone, so a shared diagram/screenshot appears in more than one.

## Asset inventory (`docs/blog_assets/`)

| File | What it shows | Used in |
|---|---|---|
| `01_landing_hero.jpg` | Landing hero — mosaic, live stats, synthetic badge | Part 1 |
| `02_console_home.jpg` | Web console home — three desks | Part 1 |
| `03_fraud_radar_list.jpg` | Fraud radar flag list (Recycler C 41.3×, tamper, reused photo) | Part 4 |
| `04_radar_flag_detail.jpg` | Flag detail — certified vs collected, 41.3× math, EN/हिंदी | Parts 3, 4 |
| `05_chain_broken.jpg` | Receipt chain "BROKEN AT NO. 27" | Part 4 |
| `06_brand_verified_backed.jpg` | Brand view — "11 of 12 hold up", verified-backed % | Part 4 |
| `07_cedar_denied.jpg` | Brand denied kabadiwala identities (Cedar 403) | Part 3 |
| `receipt_card.png` | Receipt card (PET 24.9 kg → ₹448, chain verified, QR) | Part 2 |
| `hisaab_card.png` | मेरा हिसाब income card | Part 1 |
| `architecture.png` | Architecture diagram (write path + read/audit path) | Parts 2, 3 |
| `architecture.html` | Editable source for the diagram (re-render with headless Chrome) | — |

## Before you hit publish

- Fill the `*By [your name]*` line at the top of your post.
- Fill the three `[link]` placeholders in the "series (4 parts)" list once the sibling
  posts are live (so all four cross-link).
- Keep the exact NGT line, the "38× is our own simulation" framing, the
  "WhatsApp in production, Telegram for the prototype" line, and the synthetic-data
  labels — these are non-negotiable per the project's honesty rules.
- Add your published URL to the project's final submission.
