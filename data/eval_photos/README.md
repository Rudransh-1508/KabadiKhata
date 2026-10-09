# Photo eval set (P1)

30 **AI-generated** photos of kabadi-shop hanging scales, made by the team and published at
[kaggle.com/datasets/oneshikaaa/kabadiwala](https://www.kaggle.com/datasets/oneshikaaa/kabadiwala) (Apache-2.0).
They are synthetic (CLAUDE.md rule 3): report results as "AI-generated scale photos, n=…", never as real photos.

- Get the images: `uv run python eval/fetch_photos.py` (they land in `kabadiwala/`, which is gitignored).
- `labels.csv` is the ground truth. `split` is `tune` (20) or `heldout` (10). Tune the `read_photo`
  prompt on `tune` rows only; `heldout` is for the final number (CLAUDE.md #6).

## Labelling `true_kg` (by a person, never by the model)
Open each image at full size and read where the needle or red marker points.
- `true_kg`: the reading in kg, to the nearest small tick.
- `readable`: `yes`, or `no` if the dial is blurred, cut off, or its numbers contradict each other
  (image generators sometimes print a scale that isn't in order). For `no` rows leave `true_kg` empty:
  `read_photo` should then return no reading.
- `notes`: anything odd.

Run the eval: `uv run python eval/photo_eval.py` (held-out rows), or `--split tune` while tuning.
