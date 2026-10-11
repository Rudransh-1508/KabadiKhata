"""How well does the look-alike check separate "same load" from "same shop, different load"?

    uv sync --extra dev --extra product --extra dedupe && uv run --extra dedupe python eval/lookalike_eval.py

Groups of photo pairs, scored by cosine similarity (perception/lookalike.py):
  - different load, same shop: every pair of cg_01..cg_10 (one shop, ten loads). Must stay BELOW the line.
  - different shops: every pair of the kw_ photos.
  - same photo, simulated new angle (stand-in only): each photo against a copy warped in perspective,
    cropped, turned and re-lit. This is NOT a real re-shoot; it only bounds what to expect.
  - pairs listed in data/eval_lookalike/pairs.csv (file_a, file_b, same_load yes|no, source), e.g. the
    same sack from two angles via Nano Banana or a phone. These are the real test; images go in
    data/eval_lookalike/ (gitignored).
Writes eval/RESULTS_lookalike.md with each group's spread and a threshold table.
"""
import csv
import io
import itertools
import random
import sys
from pathlib import Path

from PIL import Image, ImageEnhance

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from perception import lookalike  # noqa: E402
from photo_eval import as_bot_sends  # noqa: E402  (<=1024 px JPEG, what the bot sends)

PHOTOS = Path("data/eval_photos/kabadiwala")
PAIRS = Path("data/eval_lookalike/pairs.csv")
PAIR_DIR = Path("data/eval_lookalike")
THRESHOLDS = (0.80, 0.85, 0.88, 0.90, 0.92, 0.94, 0.96)


def new_angle(raw: bytes, seed: int) -> bytes:
    """A rough stand-in for re-shooting: perspective warp, off-centre crop, small turn, new light."""
    rng = random.Random(seed)
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = im.size
    d = lambda: rng.uniform(0.04, 0.12)  # noqa: E731
    quad = (w * d(), h * d(), w * d(), h * (1 - d()), w * (1 - d()), h * (1 - d()), w * (1 - d()), h * d())
    im = im.transform((w, h), Image.QUAD, quad, Image.BICUBIC)
    im = im.rotate(rng.uniform(-8, 8), resample=Image.BICUBIC, expand=False)
    cw, ch = int(w * rng.uniform(0.8, 0.92)), int(h * rng.uniform(0.8, 0.92))
    x, y = rng.randint(0, w - cw), rng.randint(0, h - ch)
    im = ImageEnhance.Brightness(im.crop((x, y, x + cw, y + ch))).enhance(rng.uniform(0.75, 1.25))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def spread(xs: list[float]) -> str:
    if not xs:
        return "n=0"
    s = sorted(xs)
    return f"n={len(s)}, min {s[0]:.3f}, median {s[len(s) // 2]:.3f}, max {s[-1]:.3f}"


def main() -> int:
    if not lookalike.available():
        print("Install the optional extra first: uv sync --extra dev --extra product --extra dedupe")
        return 1
    files = sorted(PHOTOS.glob("*.png"))
    if not files:
        print("No photos: run eval/fetch_photos.py first.")
        return 1
    report = ["# Look-alike photo check", "",
              "DINOv2-small image embeddings (ONNX), cosine similarity. Photos: the team's AI-generated "
              "kabadi set (synthetic), resized to the <=1024 px JPEG the bot sends. A pair is flagged when its "
              "similarity is at or above the threshold.", "",
              "**Not yet evidence of catching re-shoots:** the only positive group is the same image warped "
              "(augmentation robustness). No threshold is validated until real same-load pairs are listed in "
              "data/eval_lookalike/pairs.csv.", ""]
    for title, region in (("Load region only (the default)", lookalike.LOAD_REGION), ("Whole photo", None)):
        report += [f"## {title}", ""] + _section(files, region) + [""]
    report += ["Read it as: a usable threshold flags nearly all same-load pairs and almost no "
               "different-load pairs from the same shop. Until real same-load pairs are listed in "
               "data/eval_lookalike/pairs.csv, the stand-in row is the only positive evidence."]
    out = Path("eval/RESULTS_lookalike.md")
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report[4:]))
    return 0


def _section(files: list[Path], region) -> list[str]:
    sent = {f.stem: as_bot_sends(f) for f in files}
    emb = {k: lookalike.embed(raw, region) for k, raw in sent.items()}
    sim = lookalike.similarity
    cg = [k for k in emb if k.startswith("cg_")]
    kw = [k for k in emb if k.startswith("kw_")]

    groups = {
        "different load, same shop": ([sim(emb[a], emb[b]) for a, b in itertools.combinations(cg, 2)], False),
        "different shops": ([sim(emb[a], emb[b]) for a, b in itertools.combinations(kw, 2)], False),
        "same photo, simulated new angle (stand-in)": (
            [sim(emb[f.stem], lookalike.embed(new_angle(sent[f.stem], i), region)) for i, f in enumerate(files)],
            True),
    }
    if PAIRS.exists():
        listed = {True: [], False: []}
        for r in csv.DictReader(PAIRS.open(encoding="utf-8")):
            a, b = (lookalike.embed(as_bot_sends(PAIR_DIR / r[k]), region) for k in ("file_a", "file_b"))
            listed[r["same_load"].strip().lower() == "yes"].append(sim(a, b))
        groups["listed pairs: same load"] = (listed[True], True)
        groups["listed pairs: different load"] = (listed[False], False)

    report = ["| pair group | should be flagged | similarity |", "|---|---|---|"]
    report += [f"| {name} | {'yes' if pos else 'no'} | {spread(xs)} |" for name, (xs, pos) in groups.items()]
    report += ["", "| threshold | " + " | ".join(groups) + " |", "|---|" + "---|" * len(groups)]
    for t in THRESHOLDS:
        cells = [f"{sum(x >= t for x in xs) / len(xs):.0%} flagged" if xs else "-" for xs, _ in groups.values()]
        report.append(f"| {t:.2f} | " + " | ".join(cells) + " |")
    return report


if __name__ == "__main__":
    sys.exit(main())
