"""Score P3's radar rules on sweep worlds with known fraud (CLAUDE.md #5).

    uv run python eval/radar_eval.py              # 20 random worlds, ±15% honest noise
    uv run python eval/radar_eval.py --seeds 5 --noise 0.10

Each sweep world (src/synth/sweep_world.py) is loaded into a throwaway SQLite store through the
same ledger code as the demo, so hashes, chains and Verified inflow behave exactly as live.
The rules are P3's own functions; nothing here re-implements a verdict.

Reports, at the configured R1 threshold:
  - catch rate per planted over-claim ratio, and false flags on honest Recyclers
  - the smallest ratio caught every time with zero false flags
  - precision and recall per rule (R1 per recycler-material-month; R2 per receipt; R3 per chain)
plus a threshold table so P3 can see the trade-off. Writes eval/RESULTS_radar.md.
"""
import argparse
import os
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ledger.store import Store  # noqa: E402
from ledger.world import load_world  # noqa: E402
from radar import rules  # noqa: E402
from synth.sweep_world import RATIOS, sweep_world  # noqa: E402

THRESHOLDS = (1.10, 1.15, 1.17, 1.20, 1.30, 1.50)


def evaluate_world(world: dict) -> dict:
    """Run the rules on one world. Returns R1 ratios per cell with their truth, and R2/R3 hits."""
    truth = world["ground_truth"]
    with tempfile.TemporaryDirectory() as d:
        store = Store(os.path.join(d, "sweep.db"))
        load_world(store, world)
        status = rules.chain_status(store)
        verified = rules.verified_receipts(store, status)

        inflow = rules.verified_inflow_t(verified)
        all_inflow = rules.verified_inflow_t(store.all_receipts())  # as if every chain verified
        cells = []
        for key, cert_t in rules.certified_t(store.list_certificates()).items():
            recycler = key[0]
            cells.append({"key": key, "recycler": recycler, "planted": truth["fraud_ratio"].get(recycler),
                          "ratio": rules.over_claim_ratio(cert_t, inflow.get(key, 0.0)),
                          # receipts after a chain break stopped counting towards this cell's inflow
                          "cut_by_break": inflow.get(key, 0.0) < all_inflow.get(key, 0.0) - 1e-9})

        # Sanity: our ratio > threshold must flag exactly the recycler-material-month cells R1 flags
        r1_flagged = {f.flag_id for f in rules.r1_mass_balance(store, verified)}
        ours = {"R1:{}:{}:{}".format(*c["key"]) for c in cells if c["ratio"] > rules.r1_threshold()}
        if r1_flagged != ours:
            raise RuntimeError(f"eval disagrees with R1: only R1 {sorted(r1_flagged - ours)}, "
                               f"only eval {sorted(ours - r1_flagged)}")

        # R2 runs on verified receipts only, so ring receipts hidden by the planted tamper break
        # are out of its reach by design and are not counted as R2 misses
        ring_photos = set(truth["ring_photo_sha256"])
        ring_ids = {r.receipt_id for r in verified if r.photo_sha256 in ring_photos}
        r2_ids = {rid for f in rules.r2_duplicate_photos(verified) for rid in f.evidence_ids}
        r3_cids = {f.subject_id for f in rules.r3_broken_chains(store, status)}

    return {"cells": cells, "ring": ring_ids, "r2": r2_ids,
            "tampered": {truth["tampered_collector"]}, "r3": r3_cids}


def pr(tp: int, fp: int, fn: int) -> tuple[str, str]:
    p = f"{100 * tp / (tp + fp):.0f}%" if tp + fp else "n/a"
    r = f"{100 * tp / (tp + fn):.0f}%" if tp + fn else "n/a"
    return p, r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--noise", type=float, default=0.15, help="honest month-to-month noise, e.g. 0.15 = ±15%%")
    args = ap.parse_args()
    threshold = rules.r1_threshold()

    cells, r2 = [], [0, 0, 0]
    r3 = [0, 0, 0]
    for seed in range(args.seeds):
        res = evaluate_world(sweep_world(seed, noise=args.noise))
        cells += res["cells"]
        r2[0] += len(res["r2"] & res["ring"])
        r2[1] += len(res["r2"] - res["ring"])
        r2[2] += len(res["ring"] - res["r2"])
        r3[0] += len(res["r3"] & res["tampered"])
        r3[1] += len(res["r3"] - res["tampered"])
        r3[2] += len(res["tampered"] - res["r3"])
        print(f"seed {seed}: {len(res['cells'])} certificate cells scored", file=sys.stderr)

    def rates(t: float) -> tuple[float, dict[float, float], int]:
        honest = [c for c in cells if c["planted"] is None]
        fp = sum(c["ratio"] > t and not c["cut_by_break"] for c in honest)
        catch = {}
        for ratio in RATIOS:
            planted = [c for c in cells if c["planted"] == ratio]
            catch[ratio] = sum(c["ratio"] > t for c in planted) / len(planted) if planted else float("nan")
        return fp / len(honest), catch, fp

    fp_rate, catch, fp = rates(threshold)
    honest_cut = [c for c in cells if c["planted"] is None and c["cut_by_break"]]
    cut_flagged = sum(c["ratio"] > threshold for c in honest_cut)
    clean = [r for r in RATIOS if catch[r] == 1.0]
    if fp == 0 and clean:
        headline = f"Smallest over-claim caught in every case with zero false flags on honest recyclers: **{min(clean):g}x**"
    elif fp == 0:
        headline = "Zero false flags on honest recyclers, but no planted ratio was caught in every case"
    else:
        headline = f"{fp} false flag(s) on honest recyclers at this threshold; see the table"

    r1_tp = sum(c["ratio"] > threshold for c in cells if c["planted"])
    r1_fn = sum(c["ratio"] <= threshold for c in cells if c["planted"])
    rows = [("R1 mass balance", "recycler-material-month", *pr(r1_tp, fp + cut_flagged, r1_fn)),
            ("R2 duplicate photo", "receipt", *pr(*r2)),
            ("R3 broken chain", "chain", *pr(*r3))]

    n_honest = sum(c["planted"] is None for c in cells)
    n_planted = {r: sum(c["planted"] == r for c in cells) for r in RATIOS}
    report = [
        "# Radar sensitivity eval",
        "",
        f"Synthetic sweep worlds: {args.seeds} random seeds × 3 months, 6 honest recyclers with "
        f"±{args.noise:.0%} month-to-month noise, one fraudulent recycler per ratio "
        f"({', '.join(f'{r:g}x' for r in RATIOS)}), a 10-receipt duplicate-photo ring and one tampered receipt "
        f"per world. Rules are P3's (`src/radar/rules.py`), R1 threshold {threshold:g}.",
        "",
        f"- {headline}",
        f"- Honest recycler-material-months falsely flagged from noise: {fp}/{n_honest} ({fp_rate:.1%})",
        f"- Honest recycler-material-months flagged because a broken chain cut their Verified inflow: "
        f"{cut_flagged}/{len(honest_cut)}. This is R1 working as designed (a tampered chain's later "
        f"receipts no longer count), so these are reported apart from noise false flags.",
        *[f"- Planted {r:g}x caught: {catch[r]:.0%} of {n_planted[r]} recycler-material-months" for r in RATIOS],
        "",
        "## Precision and recall per rule",
        "",
        "| rule | scored per | precision | recall |",
        "|---|---|---|---|",
        *[f"| {name} | {unit} | {p} | {r} |" for name, unit, p, r in rows],
        "",
        "## R1 threshold trade-off (for P3; the threshold is not changed here)",
        "",
        "| threshold | false flags from noise (honest) | " + " | ".join(f"{r:g}x caught" for r in RATIOS) + " |",
        "|---|---|" + "---|" * len(RATIOS),
    ]
    for t in sorted(set(THRESHOLDS) | {threshold}):
        f_rate, c, _ = rates(t)
        mark = " (current)" if t == threshold else ""
        report.append(f"| {t:g}{mark} | {f_rate:.1%} | " + " | ".join(f"{c[r]:.0%}" for r in RATIOS) + " |")
    report += [
        "",
        "Limits: honest recyclers here buy only through the system. A real recycler also buys scrap "
        "outside it, which raises its ratio; the Verified-backed percentage shown to Brands is the "
        "answer to that, not a lower threshold. R2 photo hashes are random apart from the planted ring, "
        "so R2's precision here says nothing about look-alike real photos.",
    ]

    out = Path("eval/RESULTS_radar.md")
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(line for line in report if line.startswith(("- ", "|"))))
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
