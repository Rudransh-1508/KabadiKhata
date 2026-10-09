# Look-alike photo check

DINOv2-small image embeddings (ONNX), cosine similarity. Photos: the team's AI-generated kabadi set (synthetic). A pair is flagged when its similarity is at or above the threshold.

## Load region only (the default)

| pair group | should be flagged | similarity |
|---|---|---|
| different load, same shop | no | n=45, min 0.434, median 0.631, max 0.916 |
| different shops | no | n=190, min 0.205, median 0.515, max 0.817 |
| same photo, simulated new angle (stand-in) | yes | n=30, min 0.767, median 0.901, max 0.929 |

| threshold | different load, same shop | different shops | same photo, simulated new angle (stand-in) |
|---|---|---|---|
| 0.80 | 24% flagged | 1% flagged | 97% flagged |
| 0.85 | 11% flagged | 0% flagged | 87% flagged |
| 0.88 | 9% flagged | 0% flagged | 67% flagged |
| 0.90 | 7% flagged | 0% flagged | 50% flagged |
| 0.92 | 0% flagged | 0% flagged | 10% flagged |
| 0.94 | 0% flagged | 0% flagged | 0% flagged |
| 0.96 | 0% flagged | 0% flagged | 0% flagged |

## Whole photo

| pair group | should be flagged | similarity |
|---|---|---|
| different load, same shop | no | n=45, min 0.689, median 0.800, max 0.914 |
| different shops | no | n=190, min 0.351, median 0.567, max 0.816 |
| same photo, simulated new angle (stand-in) | yes | n=30, min 0.816, median 0.875, max 0.933 |

| threshold | different load, same shop | different shops | same photo, simulated new angle (stand-in) |
|---|---|---|---|
| 0.80 | 49% flagged | 1% flagged | 100% flagged |
| 0.85 | 20% flagged | 0% flagged | 73% flagged |
| 0.88 | 9% flagged | 0% flagged | 43% flagged |
| 0.90 | 4% flagged | 0% flagged | 23% flagged |
| 0.92 | 0% flagged | 0% flagged | 3% flagged |
| 0.94 | 0% flagged | 0% flagged | 0% flagged |
| 0.96 | 0% flagged | 0% flagged | 0% flagged |

Read it as: a usable threshold flags nearly all same-load pairs and almost no different-load pairs from the same shop. Until real same-load pairs are listed in data/eval_lookalike/pairs.csv, the stand-in row is the only positive evidence.
