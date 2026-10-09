"""Real backend HTTP client for the console — the Phase 2 swap for console.mock_api.

Exposes the SAME surface as console.mock_api (``run_radar``, ``list_flags``,
``decide_flag``, ``list_certificates``, ``provenance``, ``list_actors``) with the
SAME return shapes, so console.app selects a backend by importing one or the
other (KK_USE_MOCK), exactly as the bot does.

Endpoint: ``KK_API_URL`` (default http://localhost:3000). Every call names the
acting actor in the ``X-Principal`` header (the API's stand-in for auth) — the
console's sidebar "Acting as" selector supplies a real seeded id (au-1 / br-1 /
br-2). Cedar is default-deny, so a disallowed call comes back as HTTP 403
``{"denied_by": "cedar", "action": ..., "reason": ...}``; we surface that as a
``CedarDenied`` the Brand view renders as the red banner (beat #4), rather than
hardcoding the denial text.
"""
from __future__ import annotations

import os

import httpx

BASE_URL = os.environ.get("KK_API_URL", "http://localhost:3000").rstrip("/")
TIMEOUT = float(os.environ.get("KK_API_TIMEOUT", "60"))  # CLAUDE.md #2: vision/audio need > 3s


class CedarDenied(Exception):
    """Raised on an HTTP 403 whose body is a Cedar denial. Carries the raw body."""

    def __init__(self, body: dict):
        self.body = body or {}
        self.action = self.body.get("action")
        self.reason = self.body.get("reason")
        super().__init__(f"denied by cedar: {self.action}")


def _headers(principal: str) -> dict:
    return {"X-Principal": principal}


def _get(path: str, principal: str, params: dict | None = None):
    with httpx.Client(timeout=TIMEOUT) as c:
        resp = c.get(f"{BASE_URL}{path}", headers=_headers(principal), params=params)
        return _handle(resp)


def _post(path: str, principal: str, json: dict | None = None):
    with httpx.Client(timeout=TIMEOUT) as c:
        resp = c.post(f"{BASE_URL}{path}", headers=_headers(principal), json=json)
        return _handle(resp)


def _handle(resp: httpx.Response):
    if resp.status_code == 403:
        body = {}
        try:
            body = resp.json()
        except Exception:  # pragma: no cover - a non-JSON 403 is still a denial
            pass
        if body.get("denied_by") == "cedar":
            raise CedarDenied(body)
    resp.raise_for_status()
    return resp.json()


# ---------- auditor ----------

def run_radar(principal: str) -> list[dict]:
    """POST /radar/run -> list[Flag]. Re-runs the deterministic rules, then returns them."""
    return _post("/radar/run", principal, json={})


def list_flags(principal: str) -> list[dict]:
    return _get("/flags", principal)


def decide_flag(flag_id: str, decision: str, principal: str) -> dict:
    """POST /flags/{id}/decision ('inspect'|'dismiss') -> the updated Flag."""
    return _post(f"/flags/{flag_id}/decision", principal, json={"decision": decision})


# ---------- brand ----------

def list_certificates(brand_id: str, principal: str) -> list[dict]:
    """GET /certificates?brand_id= -> [{certificate_id, recycler_id, brand_id, month,
    material, tonnes, verified_backed_pct}]."""
    return _get("/certificates", principal, params={"brand_id": brand_id})


def provenance(certificate_id: str, principal: str) -> dict:
    """GET /provenance/{id} -> {certificate, verified_inflow_t, recycler_certified_t,
    verified_backed_pct, by_locality:[{locality, receipts, tonnes}]} (never identities)."""
    return _get(f"/provenance/{certificate_id}", principal)


# ---------- identity access (Cedar demo, beat #4) ----------

def list_actors(principal: str, role: str | None = None) -> list[dict]:
    """GET /actors?role= -> list[Actor]. A Brand principal is DENIED (403) — the point
    of beat #4: provenance is aggregate only, identities are never exposed to a Brand."""
    return _get("/actors", principal, params={"role": role} if role else None)
