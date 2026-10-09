"""Score transcribe against data/eval_voice/labels.csv.

    uv run python eval/voice_eval.py

Each set (`tts` = Gemini TTS, `say` = macOS Hindi voice, `real` = recordings by the team) is scored
apart, over the clips that exist (n is stated per set):
Stated weight exactly right (the plan's bar: 8 of 10 clips), and material right. Rows with no
weight or material said expect None. Answers are cached (.cache/voice). Writes eval/RESULTS_voice.md.
"""
import base64
import csv
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from perception import voice  # noqa: E402
from perception.voice import transcribe  # noqa: E402

PAUSE_S = float(os.getenv("EVAL_PAUSE_S", "6"))  # free tier: about 10 model calls a minute

LABELS = Path("data/eval_voice/labels.csv")
SET_DIRS = {"tts": Path("data/eval_voice/tts"), "say": Path("data/eval_voice/say"),
            "sarvam": Path("data/eval_voice/sarvam"), "real": Path("data/eval_voice/real")}
SET_NAMES = {"tts": "Synthetic clips (Gemini text-to-speech, 6 voices)",
             "say": "Synthetic clips (macOS Hindi voice \"Lekha\")",
             "sarvam": "Synthetic clips (Sarvam Bulbul text-to-speech, 6 voices)",
             "real": "Real voice notes recorded by the team"}


def _num(s: str):
    return float(s) if s.strip() else None


def main() -> int:
    rows = [r for r in csv.DictReader(LABELS.open(encoding="utf-8")) if (SET_DIRS[r["set"]] / r["file"]).exists()]
    if not rows:
        print("No clips yet: run eval/gen_voice_clips.py (--engine say works offline) or record some.")
        return 1

    report = ["# transcribe eval", "", f"Transcribed with: {voice._model_tag()}", ""]
    for set_id in SET_DIRS:
        set_rows = [r for r in rows if r["set"] == set_id]
        if not set_rows:
            continue
        lines, kg_ok, mat_ok, errors = [], 0, 0, 0
        for r in set_rows:
            raw = (SET_DIRS[set_id] / r["file"]).read_bytes()
            cached = os.path.exists(voice._cache_path(voice._cache_key(raw)))
            got = transcribe(base64.b64encode(raw).decode())
            if not cached:
                time.sleep(PAUSE_S)
            if got == voice.FAILED:  # no answer from the model (quota, network): not a wrong answer
                errors += 1
                lines.append(f"| {r['file']} | {r['text']} | (model error) | | | | |")
                continue
            true_kg, true_mat = _num(r["true_kg"]), r["true_material"] or None
            kg_hit = got.claimed_kg == true_kg
            mat_hit = got.claimed_material == true_mat
            kg_ok += kg_hit
            mat_ok += mat_hit
            lines.append(f"| {r['file']} | {r['text']} | {got.text_hi} | {true_kg} | {got.claimed_kg}{'' if kg_hit else ' ✗'} "
                         f"| {true_mat} | {got.claimed_material}{'' if mat_hit else ' ✗'} |")
        n = len(set_rows) - errors
        if n == 0:
            report += [f"## {set_id}", "", f"All {errors} clips got a model error; run again later.", ""]
            continue
        report += [
            f"## {set_id}", "", f"Data: {SET_NAMES[set_id]}.", "",
            *([f"- Model errors (not scored; run again to retry): {errors}"] if errors else []),
            f"- **Stated weight exactly right:** {kg_ok}/{n} ({100 * kg_ok / n:.0f}%)",
            f"- **Material right:** {mat_ok}/{n} ({100 * mat_ok / n:.0f}%)",
            "",
            "| file | script | transcript | true kg | heard kg | true material | heard material |",
            "|---|---|---|---|---|---|---|",
            *lines, "",
        ]
    out = Path("eval/RESULTS_voice.md")
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(line for line in report if line.startswith(("##", "- "))))
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
