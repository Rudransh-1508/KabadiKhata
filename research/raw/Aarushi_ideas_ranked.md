# Ideas, ranked

Each idea is scored against what judges and past winners reward (see `02_what_won_before.md`):
**one named person + one decision + an agent that does something safely + nobody else building it + a clear 3-minute video + AWS visibly in the loop.**

| # | Idea | Track | Novelty vs field | Why now | Feasible in 4 days | Demo punch | Score |
|---|---|---|---|---|---|---|---|
| **1** | **Kabadi Khata**: tamper-evident proof-of-collection for informal recyclers, plus EPR fraud radar | Waste and Energy | ★★★★★ (0 at Event 01; organisers listed "informal recyclers" but gave no starter idea) | 6 to 7 lakh fake EPR certificates; 2026 PWM rules push traceability; 2026 SWM rules bar unregistered collectors | ★★★★ | ★★★★★ | **Top pick** |
| **2** | **Parali Dispatch**: predict which villages burn in the next 72 hours and send idle Super Seeders there first | Air | ★★★★ (stubble will appear as maps; dispatch won't) | Stubble season starts Oct 8, the hackathon's first day; ~77k CRM machines sit mostly idle with no booking layer | ★★★ (satellite step is the risk) | ★★★★★ (in Delhi, that week) | Strong #2 |
| **3** | **Garmi Ka Hisaab**: same-day verified heat-day record that triggers parametric payouts for worker cooperatives | Heat and Water | ★★★★★ | Payouts lag 14 to 20 days; NDMA's 11-to-4 pause is unenforced | ★★★★ | ★★★ (October, so you replay May data) | #3 |
| 4 | **CoolRoof Queue**: a ward budget in, a ranked list of which slum roofs to cool-paint first (Landsat surface temperature from AWS Open Data plus roof footprints) | Heat and Water | ★★★★ | NDMA push for local heat action plans; Mahila Housing Trust runs cool-roof programmes | ★★★ | ★★★ | Backup |
| 5 | **Landfill Watch**: FIRMS thermal anomalies plus wind, giving early warning to wards downwind of Ghazipur/Bhalswa and a ranked list of which cell to cap or soak first | Waste / Air | ★★★★ | NGT methane-hotspot committees | ★★★ | ★★★ | Backup |
| 6 | CCTS MRV copilot for small factories | Energy | ★★★ | Carbon market goes live Oct 2026 | ★★★ | ★★ (dry for judges) | Skip |

## Avoid (crowded or copied from the blog)
AQI dashboards, maps and chatbots · school "move PE indoors" alerts · delivery-rider clean-air route planner · tanker predictor · flood route app · photo-of-bin segregation scorer · rooftop solar payback calculator · carbon footprint tracker · generic disaster-response coordination (32 such projects at Event 01) · food-waste apps.

---

## #1 Kabadi Khata (recommended). Full plan in `05_winning_plan.md`
**The person:** Raju, a kabadiwala in Delhi, who collects ~150 kg of plastic a day and sells to an aggregator for cash, with no record.
**The decision that changes:** a **brand's EPR officer** deciding whether a recycler's certificate is real. Today they can't tell; 6 lakh were fake.
**The loop:** Raju sends a photo of the scale plus a Hindi voice note. A Strands agent on Bedrock reads the scale, classifies the material, and checks it against the voice note. It writes a hash-chained receipt with a QR code. The aggregator and recycler scan the QR to continue the chain of custody. A **fraud radar** runs a mass-balance check, so a recycler can't certify more than its verified inflows. Cedar decides who sees what.
**What changes for Raju:** a verifiable income history (useful for loans like PM SVANidhi), a premium for EPR-grade traceable material, and a place in the formal chain the 2026 rules would otherwise cut him out of.
**Why it should win:** It is the only project in the field built on a real 2026 scandal. It has two different people on either side, the same structure as Suraksha. The agent is bounded and verifiable, the same structure as Beacon. It uses Strands, Bedrock, Cedar, DynamoDB, S3, and Lambda in ways that are easy to show on video.

## #2 Parali Dispatch (pick this if your team is in Delhi or wants the Air track)
**The person:** the operator of a custom hiring centre (CHC) in Sangrur with 3 Super Seeders, deciding **which villages to send them to tomorrow**.
**The loop:** Sentinel-2 imagery from AWS Open Data gives an NDVI drop, which means paddy was just harvested, so a burn is likely in 2 to 5 days. Combined with NASA FIRMS fires already burning nearby, that gives a village risk ranking for the next 72 hours. An agent builds the CHC's dispatch plan for tomorrow (machines × acres × travel). It then sends farmers a Hindi voice or SMS offer with a slot ("Super Seeder free on Thursday, ₹2,000/acre, reply 1 to book"; Amazon Polly does Hindi, but not Punjabi). The farmer replies and the CHC operator approves.
**Why it wins:** It is the exact week stubble burning starts, judged in Delhi. It goes past a fire map to the next action, which is what the organisers asked for. Punjab bought the machines; the missing piece is logistics.
**Risk:** detecting harvest from NDVI in 4 days. Fallback: use FIRMS clusters plus district harvest calendars as the risk signal, and say plainly where the data comes from.

## #3 Garmi Ka Hisaab
**The person:** a cooperative (like SEWA or Mahila Housing Trust) admin who has to pay ₹750 heat-day payouts. Today it takes 14 to 20 days to verify who worked in the heat.
**The loop:** The worker taps "I'm out working" or sends a voice note. The agent combines that with IMD alerts and a heat index for their ward (NASA POWER or ERA5 from AWS Open Data). It produces a signed heat-day record the same evening, and the admin approves the batch payout the next morning. Cedar controls privacy (a worker's location history is visible only to them and the payer).
**Weakness:** it is October, so the demo replays May 2026. Still the most "a YC company could do this" idea in the list.
