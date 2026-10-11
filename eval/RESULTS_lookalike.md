# Look-alike photo check

DINOv2-small image embeddings (ONNX), cosine similarity. Photos: the team's AI-generated kabadi set (synthetic), resized to the <=1024 px JPEG the bot sends. A pair is flagged when its similarity is at or above the threshold.

**Not yet evidence of catching re-shoots:** the only positive group is the same image warped (augmentation robustness). No threshold is validated until real same-load pairs are listed in data/eval_lookalike/pairs.csv.

## Load region only (the default)

| pair group | should be flagged | similarity |
|---|---|---|
| different load, same shop | no | n=45, min 0.431, median 0.620, max 0.913 |
| different shops | no | n=190, min 0.189, median 0.521, max 0.797 |
| same photo, simulated new angle (stand-in) | yes | n=30, min 0.792, median 0.890, max 0.931 |
| listed pairs: same load | yes | n=0 |
| listed pairs: different load | no | n=0 |

| threshold | different load, same shop | different shops | same photo, simulated new angle (stand-in) | listed pairs: same load | listed pairs: different load |
|---|---|---|---|---|---|
| 0.80 | 24% flagged | 0% flagged | 97% flagged | - | - |
| 0.85 | 13% flagged | 0% flagged | 83% flagged | - | - |
| 0.88 | 9% flagged | 0% flagged | 60% flagged | - | - |
| 0.90 | 7% flagged | 0% flagged | 27% flagged | - | - |
| 0.92 | 0% flagged | 0% flagged | 7% flagged | - | - |
| 0.94 | 0% flagged | 0% flagged | 0% flagged | - | - |
| 0.96 | 0% flagged | 0% flagged | 0% flagged | - | - |

## Whole photo

| pair group | should be flagged | similarity |
|---|---|---|
| different load, same shop | no | n=45, min 0.681, median 0.798, max 0.912 |
| different shops | no | n=190, min 0.355, median 0.569, max 0.813 |
| same photo, simulated new angle (stand-in) | yes | n=30, min 0.818, median 0.877, max 0.929 |
| listed pairs: same load | yes | n=0 |
| listed pairs: different load | no | n=0 |

| threshold | different load, same shop | different shops | same photo, simulated new angle (stand-in) | listed pairs: same load | listed pairs: different load |
|---|---|---|---|---|---|
| 0.80 | 49% flagged | 1% flagged | 100% flagged | - | - |
| 0.85 | 20% flagged | 0% flagged | 80% flagged | - | - |
| 0.88 | 9% flagged | 0% flagged | 43% flagged | - | - |
| 0.90 | 4% flagged | 0% flagged | 23% flagged | - | - |
| 0.92 | 0% flagged | 0% flagged | 10% flagged | - | - |
| 0.94 | 0% flagged | 0% flagged | 0% flagged | - | - |
| 0.96 | 0% flagged | 0% flagged | 0% flagged | - | - |

Read it as: a usable threshold flags nearly all same-load pairs and almost no different-load pairs from the same shop. Until real same-load pairs are listed in data/eval_lookalike/pairs.csv, the stand-in row is the only positive evidence.
