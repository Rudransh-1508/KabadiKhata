# read_photo eval: tune split

Model: groq:qwen/qwen3.8-27b (prompt photo-v4)

## kaggle_ai

Data: AI-generated kabadi scale photos (synthetic; kaggle.com/datasets/oneshikaaa/kabadiwala, Apache-2.0), labelled by a person.

- **kg within ±5%:** 2/4 (50%) readable photos
- kg within ±5% or ±1 kg (about one tick), whichever is wider: 2/4 (50%)
- **Refused unreadable photos:** 8/16 (50%)
- **Material correct:** 19/20 (95%)
- n = 20 photos scored

| file | true kg | read kg | confidence | true material | read material | result |
|---|---|---|---|---|---|---|
| cg_01.png | - | - | 0.40 | PET | PET | refused ok |
| cg_02.png | - | - | 0.40 | PET | PET | refused ok |
| cg_04.png | - | - | 0.40 | paper | paper | refused ok |
| cg_05.png | 10.0 | 10.0 | 0.95 | paper | paper | ok |
| cg_06.png | - | 3.0 | 0.95 | paper | paper | MISS (should refuse) |
| cg_07.png | 10.0 | 10.0 | 0.95 | cardboard | cardboard | ok |
| cg_09.png | - | - | 0.40 | metal | metal | refused ok |
| kw_0.png | - | 10.0 | 0.60 | metal | metal | MISS (should refuse) |
| kw_00.png | 20.0 | 15.0 | 0.90 | paper | cardboard ✗ | MISS |
| kw_11.png | - | 5.5 | 0.90 | paper | paper | MISS (should refuse) |
| kw_3.png | - | 10.0 | 0.90 | cardboard | cardboard | MISS (should refuse) |
| kw_33.png | 10.0 | 12.0 | 0.85 | ewaste | ewaste | MISS |
| kw_4.png | - | 22.0 | 0.85 | metal | metal | MISS (should refuse) |
| kw_44.png | - | - | 0.40 | paper | paper | refused ok |
| kw_5.png | - | 20.0 | 0.95 | ewaste | ewaste | MISS (should refuse) |
| kw_55.png | - | 1.5 | 0.90 | metal | metal | MISS (should refuse) |
| kw_6.png | - | - | 0.10 | unknown | unknown | refused ok |
| kw_66.png | - | - | 0.10 | unknown | unknown | refused ok |
| kw_7.png | - | 1.5 | 0.85 | metal | metal | MISS (should refuse) |
| kw_8.png | - | - | 0.10 | paper | paper | refused ok |

