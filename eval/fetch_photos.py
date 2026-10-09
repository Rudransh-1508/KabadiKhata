"""Download the Kabadiwala eval photos from Kaggle into data/eval_photos/kabadiwala/ (gitignored).

Source: https://www.kaggle.com/datasets/oneshikaaa/kabadiwala (Apache-2.0, by the team's P1).
The images are AI-generated (synthetic); see data/eval_photos/labels.csv.
Files are renamed to short, space-free names: "N.png" -> "kw_N.png",
"ChatGPT Image ... PM-K.png" -> "cg_KK.png".
"""
import io
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

URL = "https://www.kaggle.com/api/v1/datasets/download/oneshikaaa/kabadiwala"
OUT = Path("data/eval_photos/kabadiwala")


def short_name(name: str) -> str:
    m = re.search(r"PM-(\d+)\.png$", name)
    return f"cg_{int(m.group(1)):02d}.png" if m else f"kw_{name}"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(URL, timeout=120) as resp:
        data = resp.read()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".png")]
        for n in names:
            (OUT / short_name(Path(n).name)).write_bytes(zf.read(n))
    print(f"Saved {len(names)} photos to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
