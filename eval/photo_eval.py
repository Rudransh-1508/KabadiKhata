"""Score read_photo against data/eval_photos/labels.csv (CLAUDE.md #6).

    uv run python eval/photo_eval.py                 # held-out rows: the number for README and video
    uv run python eval/photo_eval.py --split tune    # while tuning the prompt

Photos are resized to <=1024 px on the long side first, as the bot does (CLAUDE.md #3), so the
model sees what it sees in production. Answers are cached (.cache/photo), so re-runs are free.
Writes eval/RESULTS_photo_<split>.md.
"""
import argparse
import base64
import csv
import io
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from _env import load_env  # noqa: E402

load_env()
from perception.photo import read_photo  # noqa: E402

LABELS = Path("data/eval_photos/labels.csv")
SET_DIRS = {"kaggle_ai": Path("data/eval_photos/kabadiwala"), "real": Path("data/eval_photos/real")}
SET_NAMES = {"kaggle_ai": "AI-generated kabadi scale photos (synthetic; kaggle.com/datasets/oneshikaaa/kabadiwala, Apache-2.0)",
             "real": "Real phone photos taken by the team"}
KG_TOLERANCE = 0.05


def as_bot_sends(path: Path) -> str:
    im = Image.open(path).convert("RGB")
    im.thumbnail((1024, 1024))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="heldout", choices=["heldout", "tune", "all"])
    split = ap.parse_args().split

    rows = [r for r in csv.DictReader(LABELS.open(encoding="utf-8")) if split in ("all", r["split"])]
    unlabelled = [r["file"] for r in rows if r["readable"] not in ("yes", "no")
                  or (r["readable"] == "yes" and not r["true_kg"])]
    if unlabelled:
        print(f"Label these first (true_kg + readable in {LABELS}): {', '.join(unlabelled)}")
        return 1

    report = [f"# read_photo eval: {split} split", ""]
    for set_id, set_rows in _by_set(rows).items():
        report += _score(set_id, set_rows)
    out = Path(f"eval/RESULTS_photo_{split}.md")
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(line for line in report if line.startswith(("##", "- "))))
    print(f"Wrote {out}")
    return 0


def _by_set(rows: list[dict]) -> dict[str, list[dict]]:
    sets: dict[str, list[dict]] = {}
    for r in rows:
        sets.setdefault(r["set"], []).append(r)
    return sets


def _score(set_id: str, rows: list[dict]) -> list[str]:
    lines, kg_ok, kg_n, refuse_ok, refuse_n, mat_ok = [], 0, 0, 0, 0, 0
    for r in rows:
        got = read_photo(as_bot_sends(SET_DIRS[set_id] / r["file"]))
        mat_hit = got.material == r["true_material"]
        mat_ok += mat_hit
        if r["readable"] == "yes":
            true = float(r["true_kg"])
            hit = got.kg is not None and abs(got.kg - true) <= KG_TOLERANCE * true
            kg_n += 1
            kg_ok += hit
            verdict = "ok" if hit else "MISS"
        else:
            true = None
            hit = got.kg is None
            refuse_n += 1
            refuse_ok += hit
            verdict = "refused ok" if hit else "MISS (should refuse)"
        lines.append(f"| {r['file']} | {true if true is not None else '-'} | {got.kg if got.kg is not None else '-'} "
                     f"| {got.confidence:.2f} | {r['true_material']} | {got.material}{'' if mat_hit else ' ✗'} | {verdict} |")

    def pct(a, b):
        return f"{a}/{b} ({100 * a / b:.0f}%)" if b else "n/a"

    return [
        f"## {set_id}",
        "",
        f"Data: {SET_NAMES.get(set_id, set_id)}, labelled by a person.",
        "",
        f"- **kg within ±5%:** {pct(kg_ok, kg_n)} readable photos",
        f"- **Refused unreadable photos:** {pct(refuse_ok, refuse_n)}",
        f"- **Material correct:** {pct(mat_ok, len(rows))}",
        f"- n = {len(rows)} photos",
        "",
        "| file | true kg | read kg | confidence | true material | read material | result |",
        "|---|---|---|---|---|---|---|",
        *lines,
        "",
    ]


if __name__ == "__main__":
    sys.exit(main())
