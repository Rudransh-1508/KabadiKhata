"""Web front end: the forwarder passes the API's answers through unchanged, pages carry the synthetic badge."""
import re
from pathlib import Path

import httpx
import pytest
from starlette.testclient import TestClient

from api.app import app as api_app
from web import server

WEB = Path(server.__file__).resolve().parent


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "1")
    monkeypatch.setenv("KK_DB_PATH", str(tmp_path / "kk.db"))
    real = httpx.AsyncClient
    # the forwarder talks to the real API app in-process
    monkeypatch.setattr(server.httpx, "AsyncClient", lambda **kw: real(transport=httpx.ASGITransport(app=api_app), **kw))
    return TestClient(server.app)


def test_cedar_denial_passes_through_as_403(client):
    r = client.get("/api/actors", params={"role": "kabadiwala"}, headers={"X-Principal": "brand-1"})
    assert r.status_code == 403
    assert r.json()["denied_by"] == "cedar" and r.json()["action"] == "list_actors"


def test_principal_header_is_forwarded(client):
    assert client.get("/api/actors", headers={"X-Principal": "auditor-1"}).status_code == 200
    assert client.get("/api/actors").status_code == 401          # no header, no identity


def test_post_body_is_forwarded(client):
    r = client.post("/api/radar/run", json={}, headers={"X-Principal": "auditor-1"})
    assert r.status_code == 200 and isinstance(r.json(), list)


def test_unreachable_api_is_502_with_a_hint(monkeypatch):
    monkeypatch.setenv("KK_API_URL", "http://127.0.0.1:9")
    r = TestClient(server.app).get("/api/health", headers={"X-Principal": "auditor-1"})
    assert r.status_code == 502 and "make api" in r.json()["detail"]


@pytest.mark.parametrize("page", ["index.html", "console.html"])
def test_pages_are_served_with_the_synthetic_badge(page):
    r = TestClient(server.app).get(f"/{page}")
    assert r.status_code == 200 and "Synthetic demo data" in r.text


def test_web_text_uses_the_glossary():
    banned = re.compile(r"\bClaim\b|\b[Cc]ollector\b(?!_)|\braddiwala\b|\bblockchain\b")
    for f in WEB.glob("*.*"):
        if f.suffix in {".html", ".js"}:
            assert not banned.search(f.read_text(encoding="utf-8")), f.name
