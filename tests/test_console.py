"""Tests for the console: pure logic + real-shaped mock backend + a Streamlit
AppTest smoke run (headless, offline via the mock backend)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from console import logic, mock_api  # noqa: E402
from console.api_client import CedarDenied  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = str(ROOT / "console" / "app.py")


# ---- pure logic ----
def test_rule_label_real_literals():
    assert "Mass balance" in logic.rule_label("R1_mass_balance")
    assert "Duplicate photo" in logic.rule_label("R2_duplicate_photo")
    assert "Broken chain" in logic.rule_label("R3_broken_chain")
    assert logic.rule_label("unknown_rule") == "unknown_rule"


def test_bar_from_provenance():
    prov = {"recycler_certified_t": 190.0, "verified_inflow_t": 5.0}
    bar = logic.bar_from_provenance(prov)
    assert bar["claimed"] == 190.0 and bar["verified"] == 5.0 and bar["ratio"] == 38.0


def test_bar_from_provenance_no_inflow():
    bar = logic.bar_from_provenance({"recycler_certified_t": 10.0, "verified_inflow_t": 0.0})
    assert bar["ratio"] == float("inf")


def test_backed_badge():
    assert logic.backed_badge(94, 80) == "ok"
    assert logic.backed_badge(80, 80) == "ok"
    assert logic.backed_badge(3, 80) == "low"


def test_apply_decision():
    f = {"flag_id": "x", "status": "open"}
    out = logic.apply_decision(f, "inspect", "au-1", "2026-10-09T10:00:00+00:00")
    assert out["status"] == "inspection_requested" and out["decided_by"] == "au-1"
    assert logic.apply_decision(f, "dismiss", "au-1", "t")["status"] == "dismissed"
    assert f["status"] == "open"  # original not mutated


# ---- mock backend: real shapes (mirrors console.api_client) ----
def test_mock_run_radar_real_rule_literals():
    flags = mock_api.run_radar("au-1")
    assert len(flags) == 3
    assert {f["rule"] for f in flags} == {"R1_mass_balance", "R2_duplicate_photo", "R3_broken_chain"}
    for f in flags:  # every synthetic record is labelled
        assert f["synthetic"] is True


def test_mock_r1_evidence_is_certificate_and_bar():
    r1 = next(f for f in mock_api.run_radar("au-1") if f["rule"] == "R1_mass_balance")
    cert_id = r1["evidence_ids"][0]
    prov = mock_api.provenance(cert_id, "au-1")
    bar = logic.bar_from_provenance(prov)
    assert bar["claimed"] == 190.0 and bar["verified"] == 5.0 and bar["ratio"] == 38.0


def test_mock_decide_flag_updates_status():
    r1 = next(f for f in mock_api.run_radar("au-1") if f["rule"] == "R1_mass_balance")
    updated = mock_api.decide_flag(r1["flag_id"], "inspect", "au-1")
    assert updated["status"] == "inspection_requested" and updated["decided_by"] == "au-1"
    # the change is visible on a fresh fetch
    again = next(f for f in mock_api.list_flags("au-1") if f["flag_id"] == r1["flag_id"])
    assert again["status"] == "inspection_requested"
    mock_api.decide_flag(r1["flag_id"], "dismiss", "au-1")  # reset-ish for isolation


def test_mock_certificates_shape():
    certs = mock_api.list_certificates("br-1", "br-1")
    assert certs and all(c["brand_id"] == "br-1" for c in certs)
    c = certs[0]
    assert "tonnes" in c and "verified_backed_pct" in c and "recycler_id" in c
    assert "recycler_name" not in c and "tonnes_claimed" not in c


def test_mock_brand_denied_actors_but_auditor_allowed():
    with pytest.raises(CedarDenied) as ei:
        mock_api.list_actors("br-1", role="kabadiwala")
    assert ei.value.action == "list_actors"
    # auditor is allowed
    actors = mock_api.list_actors("au-1", role="kabadiwala")
    assert actors and actors[0]["role"] == "kabadiwala"


# ---- Streamlit AppTest smoke (headless, offline via the mock backend) ----
def test_app_runs_both_roles_without_exception():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception
    at.sidebar.radio[0].set_value("Brand").run()
    assert not at.exception


def test_app_run_radar_shows_flags():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    at.button[0].click().run()  # "Run radar"
    assert not at.exception
    assert len(at.session_state["flags"]) == 3
