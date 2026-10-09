import sys
from pathlib import Path

import pytest

from radar import rules
from synth.sweep_world import HONEST, RATIOS, fraud_id, sweep_world

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
from radar_eval import evaluate_world  # noqa: E402


@pytest.fixture(autouse=True)
def default_thresholds(monkeypatch):
    monkeypatch.delenv("KK_R1_THRESHOLD", raising=False)
    monkeypatch.delenv("KK_R2_MAX_DISTANCE", raising=False)


def test_same_seed_same_world():
    assert sweep_world(3) == sweep_world(3)
    assert sweep_world(3) != sweep_world(4)


def test_everything_is_labelled_synthetic_and_truth_is_complete():
    w = sweep_world(0)
    truth = w["ground_truth"]
    assert all(r["evidence"]["source"] == "synthetic sweep" for r in w["receipts"])
    assert set(truth["fraud_ratio"]) == {fraud_id(r) for r in RATIOS}
    assert truth["honest"] == list(HONEST)
    assert len(truth["ring_photo_sha256"]) == 10
    assert w["tamper"][0]["collector_id"] == truth["tampered_collector"]


def test_honest_certificates_stay_within_noise():
    w = sweep_world(1, noise=0.15)
    res = evaluate_world({**w, "tamper": []})
    honest = [c["ratio"] for c in res["cells"] if c["planted"] is None]
    assert honest and all(0.85 - 1e-6 <= r <= 1.15 + 1e-6 for r in honest)


def test_rules_find_the_planted_fraud():
    res = evaluate_world(sweep_world(2))
    big = [c for c in res["cells"] if c["planted"] == 38.0]
    assert big and all(c["ratio"] > rules.r1_threshold() for c in big)
    assert res["r2"] == res["ring"]
    assert res["r3"] == res["tampered"]
