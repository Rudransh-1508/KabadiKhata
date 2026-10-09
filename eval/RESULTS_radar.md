# Radar sensitivity eval

Synthetic sweep worlds: 20 random seeds × 3 months, 6 honest recyclers with ±15% month-to-month noise, one fraudulent recycler per ratio (1.2x, 1.5x, 3x, 38x), a 10-receipt duplicate-photo ring and one tampered receipt per world. Rules are P3's (`src/radar/rules.py`), R1 threshold 1.17.

- Smallest over-claim caught in every case with zero false flags on honest recyclers: **1.5x**
- Honest recycler-material-months falsely flagged from noise: 0/1440 (0.0%)
- Honest recycler-material-months flagged because a broken chain cut their Verified inflow: 5/30. This is R1 working as designed (a tampered chain's later receipts no longer count), so these are reported apart from noise false flags.
- Planted 1.2x caught: 62% of 240 recycler-material-months
- Planted 1.5x caught: 100% of 240 recycler-material-months
- Planted 3x caught: 100% of 240 recycler-material-months
- Planted 38x caught: 100% of 240 recycler-material-months

## Precision and recall per rule

| rule | scored per | precision | recall |
|---|---|---|---|
| R1 mass balance | recycler-material-month | 99% | 91% |
| R2 duplicate photo | receipt | 100% | 100% |
| R3 broken chain | chain | 100% | 100% |

## R1 threshold trade-off (for P3; the threshold is not changed here)

| threshold | false flags from noise (honest) | 1.2x caught | 1.5x caught | 3x caught | 38x caught |
|---|---|---|---|---|---|
| 1.1 | 17.7% | 78% | 100% | 100% | 100% |
| 1.15 | 0.0% | 67% | 100% | 100% | 100% |
| 1.17 (current) | 0.0% | 62% | 100% | 100% | 100% |
| 1.2 | 0.0% | 54% | 100% | 100% | 100% |
| 1.3 | 0.0% | 25% | 94% | 100% | 100% |
| 1.5 | 0.0% | 0% | 49% | 100% | 100% |

Limits: honest recyclers here buy only through the system. A real recycler also buys scrap outside it, which raises its ratio; the Verified-backed percentage shown to Brands is the answer to that, not a lower threshold. R2 photo hashes are random apart from the planted ring, so R2's precision here says nothing about look-alike real photos.
