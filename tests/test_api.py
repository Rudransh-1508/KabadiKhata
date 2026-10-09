import base64
import sqlite3

import pytest
from fastapi.testclient import TestClient

from api.app import app
from policy.authz import Decision

RAJU = {"X-Principal": "kw-raju"}


def b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "1")
    monkeypatch.setenv("KK_DB_PATH", str(tmp_path / "kk.db"))
    monkeypatch.setenv("KK_PHOTO_DIR", str(tmp_path / "photos"))
    return TestClient(app)


def collect(client, kg=12.0, photo="fixture:12:PET:0.92:a", headers=RAJU):
    return client.post(
        "/collections",
        headers=headers,
        json={
            "collector_id": "kw-raju",
            "photo_b64": b64(photo),
            "taps": {"material": "PET", "kg": kg},
            "locality": "Seelampur",
        },
    )


def test_matching_collection_returns_a_receipt_and_saves_the_photo(client, tmp_path):
    body = collect(client).json()
    assert body["status"] == "receipt"
    assert body["receipt"]["receipt_id"].startswith("KK-")
    assert (tmp_path / "photos" / f"{body['receipt']['photo_sha256']}.jpg").exists()


def test_mismatch_returns_a_hindi_question_and_writes_nothing(client):
    body = collect(client, kg=20.0).json()
    assert body["status"] == "question" and body["question_hi"]
    assert client.get("/receipts", params={"collector_id": "kw-raju"}, headers=RAJU).json()["receipts"] == []


def test_receipts_include_monthly_totals(client):
    collect(client, photo="fixture:12:PET:0.92:a")
    collect(client, photo="fixture:12:PET:0.92:b")
    body = client.get("/receipts", params={"collector_id": "kw-raju"}, headers=RAJU).json()
    assert len(body["receipts"]) == 2
    (month,) = body["monthly"]
    assert month["count"] == 2 and month["weight_kg"] == 24.0


def test_verify_reports_tampering(client, tmp_path):
    for i in range(3):
        collect(client, photo=f"fixture:12:PET:0.92:{i}")
    assert client.get("/verify/kw-raju", headers=RAJU).json() == {
        "ok": True, "length": 3, "broken_at_seq": None, "reason": None,
    }
    con = sqlite3.connect(tmp_path / "kk.db")
    con.execute("UPDATE receipts SET weight_kg = 50 WHERE seq = 1")
    con.commit()
    body = client.get("/verify/kw-raju", headers=RAJU).json()
    assert body["ok"] is False and body["broken_at_seq"] == 1


def test_missing_principal_is_401(client):
    assert collect(client, headers={}).status_code == 401


def test_bad_base64_is_422(client):
    r = client.post("/collections", headers=RAJU,
                    json={"collector_id": "kw-raju", "photo_b64": "not base64!!", "locality": "x"})
    assert r.status_code == 422


def test_denial_is_403_with_cedar_body(client, monkeypatch):
    monkeypatch.setattr("api.app.is_allowed", lambda *a, **k: Decision(False, "brand cannot read identities"))
    r = client.get("/receipts", params={"collector_id": "kw-raju"}, headers={"X-Principal": "brand-1"})
    assert r.status_code == 403
    assert r.json() == {"denied_by": "cedar", "action": "read_receipt", "reason": "brand cannot read identities"}


# ---------- radar, flags, certificates (seeded sample world) ----------

AUDITOR = {"X-Principal": "au-1"}
BRAND = {"X-Principal": "br-1"}


@pytest.fixture
def seeded(client, tmp_path):
    from ledger.store import Store
    from ledger.world import load_world, sample_world

    load_world(Store(tmp_path / "kk.db"), sample_world())
    return client


def test_radar_flags_recycler_c_and_the_tampered_chain(seeded):
    flags = seeded.post("/radar/run", headers=AUDITOR).json()
    r1 = [f for f in flags if f["rule"] == "R1_mass_balance"]
    assert [f["subject_id"] for f in r1] == ["rc-c"]
    assert flags[0]["flag_id"] == r1[0]["flag_id"]  # highest score first
    assert any(f["rule"] == "R3_broken_chain" and f["subject_id"] == "kw-sunita" for f in flags)


def test_auditor_decision_is_recorded_and_survives_a_rerun(seeded):
    flag_id = seeded.post("/radar/run", headers=AUDITOR).json()[0]["flag_id"]
    decided = seeded.post(f"/flags/{flag_id}/decision", headers=AUDITOR, json={"decision": "inspect"}).json()
    assert decided["status"] == "inspection_requested" and decided["decided_by"] == "au-1"
    seeded.post("/radar/run", headers=AUDITOR)
    again = {f["flag_id"]: f for f in seeded.get("/flags", headers=AUDITOR).json()}[flag_id]
    assert again["status"] == "inspection_requested" and again["decided_ts"]


def test_unknown_flag_is_404(seeded):
    assert seeded.post("/flags/nope/decision", headers=AUDITOR, json={"decision": "dismiss"}).status_code == 404


def test_brand_sees_backed_percentage_per_certificate(seeded):
    certs = {c["certificate_id"]: c for c in seeded.get("/certificates", params={"brand_id": "br-1"}, headers=BRAND).json()}
    assert certs["CERT-C-PET-1"]["verified_backed_pct"] < 5
    assert certs["CERT-A-PET-1"]["verified_backed_pct"] > 85
    assert all(c["brand_id"] == "br-1" for c in certs.values())


def test_provenance_is_aggregate(seeded):
    p = seeded.get("/provenance/CERT-A-PET-1", headers=BRAND).json()
    assert p["by_locality"] and p["verified_inflow_t"] > 0
    assert "kw-" not in str(p)


def test_kabadiwala_registers_from_the_bot(client):
    r = client.put("/actors/kw-new", headers={"X-Principal": "kw-new"}, json={"name": "Naya", "locality": "Okhla"})
    assert r.json() == {"actor_id": "kw-new", "role": "kabadiwala", "name": "Naya", "locality": "Okhla"}
    assert [a["actor_id"] for a in client.get("/actors", params={"role": "kabadiwala"}, headers=RAJU).json()] == ["kw-new"]


def test_registration_cannot_take_over_another_role(seeded):
    r = seeded.put("/actors/au-1", headers={"X-Principal": "au-1"}, json={"name": "x"})
    assert r.status_code == 409


def test_receipts_report_chain_status(seeded):
    body = seeded.get("/receipts", params={"collector_id": "kw-sunita"}, headers=AUDITOR).json()
    assert body["chain"]["ok"] is False and body["chain"]["broken_at_seq"] is not None


def test_photo_served_after_collection(client):
    sha = collect(client).json()["receipt"]["photo_sha256"]
    r = client.get(f"/photos/{sha}.jpg", headers=RAJU)
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
    assert client.get(f"/photos/{'0' * 64}.jpg", headers=RAJU).status_code == 404
