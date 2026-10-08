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
