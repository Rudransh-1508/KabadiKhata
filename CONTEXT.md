# Kabadi Khata

A record of scrap sales by informal collectors, used to check whether recyclers' recycling certificates are backed by plastic they actually received.

## Language

### People

**Kabadiwala**:
An informal scrap collector who buys scrap door to door and sells it on. The persona in the demo is Raju.
_Avoid_: Collector (in UI text), waste picker, raddiwala

**Recycler**:
A registered business that buys scrap and issues Certificates for the tonnes it recycles.
_Avoid_: Aggregator (a separate middle role, out of scope), PRO

**Brand**:
A producer that must meet an EPR target and buys Certificates to do so.
_Avoid_: PIBO, producer, company

**Auditor**:
The person who reviews Flags and decides whether to request an inspection.
_Avoid_: Admin, reviewer

### Records

**Receipt**:
One sale of one material by a Kabadiwala, with weight, price and photo evidence. Receipts are never edited; corrections are out of scope.
_Avoid_: Collection (that is the request that may produce a Receipt), transaction, entry

**Collection**:
A Kabadiwala's submission of a photo plus voice or taps. It ends in either one Receipt or one Question, never both.
_Avoid_: Upload, submission

**Question**:
The single Hindi follow-up the agent asks when a Collection fails the consistency check. No Receipt is written.
_Avoid_: Error, rejection

**Chain**:
The ordered Receipts of one Kabadiwala, each linked to the previous by hash, so any edit shows up as a break at a specific position.
_Avoid_: Ledger (when meaning one Kabadiwala's records), blockchain

**Certificate**:
A Recycler's statement to one Brand that it recycled a stated tonnage of one material in one month.
_Avoid_: Claim, EPR credit

### Fraud check

**Verified inflow**:
The tonnes of one material sold to a Recycler in one month, counting only Receipts whose Chain verifies. Receipts without a known buyer are excluded.
_Avoid_: Supply, input

**Over-claim ratio**:
Certificate tonnes for a Recycler, material and month, divided by Verified inflow times the 0.85 recycling yield.
_Avoid_: Fraud score, multiplier

**Verified-backed percentage**:
The share of a Certificate's tonnes covered by Verified inflow, shown to the Brand.
_Avoid_: Coverage, confidence

**Flag**:
A finding from a deterministic rule about a Recycler or a Chain, with its evidence. Only an Auditor decides what happens to it.
_Avoid_: Alert, violation

**Synthetic**:
Seeded demo data, always labelled as such, as opposed to Receipts produced live through the bot.
_Avoid_: Fake, mock (in UI text)

## Relationships

- A **Kabadiwala** has exactly one **Chain**; a **Chain** holds many **Receipts**.
- A **Collection** produces one **Receipt** or one **Question**.
- A **Receipt** is sold to at most one **Recycler**; live Receipts from the bot have none.
- A **Recycler** issues **Certificates**; each **Certificate** goes to one **Brand**.
- The **Over-claim ratio** compares a Recycler's **Certificates** with its **Verified inflow**; a high ratio raises a **Flag**.

## Flagged ambiguities

- "Claim" and "Certificate" were used for the same thing. Resolved: **Certificate** only.
- "Verified" meant both "came through the system" and "chain intact". Resolved: **Verified inflow** requires both.
