# read_photo eval: heldout split

Model: groq:qwen/qwen3.8-27b (prompt photo-v4)

## kaggle_ai

Data: AI-generated kabadi scale photos (synthetic; kaggle.com/datasets/oneshikaaa/kabadiwala, Apache-2.0), labelled by a person.

- **kg within ±5%:** 2/6 (33%) readable photos
- kg within ±5% or ±1 kg (about one tick), whichever is wider: 4/6 (67%)
- **Refused unreadable photos:** 1/4 (25%)
- **Material correct:** 9/10 (90%)
- n = 10 photos scored

| file | true kg | read kg | confidence | true material | read material | result |
|---|---|---|---|---|---|---|
| cg_03.png | - | 10.0 | 0.90 | PET | PET | MISS (should refuse) |
| cg_08.png | 6.0 | 5.0 | 0.90 | cardboard | cardboard | MISS |
| cg_10.png | 9.5 | 10.0 | 0.90 | metal | metal | MISS |
| kw_1.png | 25.0 | 1.5 | 0.60 | PET | PET | MISS |
| kw_2.png | - | - | 0.00 | paper | paper | refused ok |
| kw_22.png | - | 10.0 | 0.90 | metal | metal | MISS (should refuse) |
| kw_77.png | 18.0 | 18.0 | 0.90 | HDPE | mixed_plastic ✗ | ok |
| kw_88.png | 325.0 | 360.0 | 0.90 | metal | metal | MISS |
| kw_9.png | - | 1.5 | 0.60 | mixed_plastic | mixed_plastic | MISS (should refuse) |
| kw_99.png | 10.0 | 10.0 | 0.95 | metal | metal | ok |

