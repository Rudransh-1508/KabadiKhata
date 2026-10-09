"""Regression: quote_price must read P4's cited ratecard shape
({"inr_per_kg": N, ...}), not a flat number. A merge once left quote_price
doing float({...}) -> TypeError, which broke every receipt write (the spine's
first beat). See data/ratecard.json and CLAUDE.md #7."""
import json
from pathlib import Path

from agent.stub_tools import _rate_of, quote_price

_RATECARD = Path(__file__).resolve().parents[1] / "data" / "ratecard.json"


def test_rate_of_accepts_both_shapes():
    assert _rate_of(18.0) == 18.0                       # placeholder flat number
    assert _rate_of({"inr_per_kg": 18, "label": "x"}) == 18.0   # ratecard entry
    assert _rate_of({"range": [1, 2]}) == 0.0           # missing price -> 0, no crash


def test_quote_price_uses_ratecard_value():
    rates = json.loads(_RATECARD.read_text(encoding="utf-8"))["rates"]
    expected = float(rates["PET"]["inr_per_kg"])
    q = quote_price("PET", 10.0)
    assert q.inr_per_kg == expected
    assert q.total_inr == round(expected * 10.0, 2)
    assert "ratecard" in q.source


def test_quote_price_unknown_material_is_zero_not_crash():
    q = quote_price("not_a_material", 5.0)
    assert q.inr_per_kg == 0.0
    assert q.total_inr == 0.0
