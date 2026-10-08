# OpenSearch returns as a read-only search copy, not the ledger

ADR 0001 dropped OpenSearch on memory grounds, but most of that risk came from running `sam local start-api` with warm containers, which the demo no longer does. Measured on the 8 GB demo Mac: OpenSearch with a 512 MB heap uses ~0.94 GB and ~3% CPU, and free memory stayed at 29% (the Mac was already swapping heavily because of browser tabs). So we brought it back for the auditor's receipt search and tonnage chart, and to show a fourth AWS open-source tool, but only as a best-effort copy: SQLite stays the ledger that the chain, tamper check and fraud rules read, a write never fails because OpenSearch is down, and `make reindex` rebuilds the copy from SQLite.

## Considered Options
- **OpenSearch as the primary store:** rejected. The spine would then depend on a JVM service on a memory-tight laptop, and we'd maintain two store implementations before Saturday's checkpoint.

## Consequences
- Close the browser before recording the video; the Mac has little memory to spare.
- Tampering edits SQLite only, so the copy can show the original value until the next `make reindex`. The tamper demo must use `/verify`, never the search copy.
