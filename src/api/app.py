"""HTTP API (FastAPI on SQLite, see docs/adr/0001). Port 3000.

Every handler asks policy.authz.is_allowed() before touching data. The caller
names itself in the X-Principal header (a stand-in for real auth); a denial is
HTTP 403 with {"denied_by": "cedar", ...}, which the console shows as a banner.
"""

import base64
import binascii
import hashlib
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from agent.agent import handle_collection
from common.models import Actor, CollectionRequest
from ledger import chain
from ledger.store import Store
from policy.authz import Decision, is_allowed
from radar import rules

log = logging.getLogger("kk.api")

Role = Literal["kabadiwala", "recycler", "brand", "auditor"]

MAX_PHOTO_BYTES = 5 * 1024 * 1024

app = FastAPI(title="Kabadi Khata API")


@lru_cache
def _store_at(path: str) -> Store:
    return Store(path)


def get_store() -> Store:
    return _store_at(os.getenv("KK_DB_PATH", "data/kk.db"))


def photo_dir() -> Path:
    return Path(os.getenv("KK_PHOTO_DIR", "data/photos"))


def principal(x_principal: str | None = Header(default=None)) -> str:
    if not x_principal:
        raise HTTPException(401, "X-Principal header is required")
    return f'Actor::"{x_principal}"'


Who = Annotated[str, Depends(principal)]
Db = Annotated[Store, Depends(get_store)]


def actor_ref(actor_id: str) -> str:
    return f'Actor::"{actor_id}"'


class Denied(Exception):
    def __init__(self, decision: Decision, action: str):
        self.decision, self.action = decision, action


@app.exception_handler(Denied)
def _denied(_: Request, exc: Denied) -> JSONResponse:
    return JSONResponse(status_code=403, content=exc.decision.to_denial(exc.action))


def require(who: str, action: str, resource: dict, context: dict | None = None) -> None:
    decision = is_allowed(who, action, resource, context)
    log.info("authz %s %s %s -> %s (%s)", who, action, resource, decision.allowed, decision.reason)
    if not decision.allowed:
        raise Denied(decision, action)


def chain_resource(collector_id: str) -> dict:
    return {"type": "Chain", "collector": actor_ref(collector_id)}


@app.get("/health")
def health() -> dict:
    return {"ok": True}


# Handlers are plain `def` so FastAPI runs them in a thread pool: the agent call blocks on the LLM.
@app.post("/collections")
def create_collection(req: CollectionRequest, who: Who, store: Db):
    require(who, "create_collection", chain_resource(req.collector_id))
    try:
        photo = base64.b64decode(req.photo_b64, validate=True)
    except binascii.Error:
        raise HTTPException(422, "photo_b64 is not valid base64")
    if len(photo) > MAX_PHOTO_BYTES:
        raise HTTPException(413, "photo is larger than 5 MB; resize to 1024 px first")
    # Same key the agent records as photo_sha256, so the console can find the file from a Receipt
    sha = hashlib.sha256(req.photo_b64.encode()).hexdigest()
    photo_dir().mkdir(parents=True, exist_ok=True)
    (photo_dir() / f"{sha}.jpg").write_bytes(photo)
    return handle_collection(req, store).model_dump(mode="json")


@app.get("/receipts")
def list_receipts(collector_id: str, who: Who, store: Db):
    """A Kabadiwala's Receipts plus monthly totals (India time): Raju's income history."""
    require(who, "read_receipt", chain_resource(collector_id))
    receipts = store.receipts_for(collector_id)
    months: dict[str, dict] = {}
    for r in receipts:
        m = months.setdefault(chain.month_ist(r.ts), {"count": 0, "weight_kg": 0.0, "total_inr": 0.0})
        m["count"] += 1
        m["weight_kg"] += r.weight_kg
        m["total_inr"] += r.weight_kg * r.price_inr_per_kg
    monthly = [
        {"month": k, "count": v["count"], "weight_kg": round(v["weight_kg"], 3), "total_inr": round(v["total_inr"], 2)}
        for k, v in sorted(months.items())
    ]
    return {
        "collector_id": collector_id,
        "receipts": [r.model_dump(mode="json") for r in receipts],
        "monthly": monthly,
        # The income statement shows "chain verified" only when this is ok
        "chain": chain.verify(receipts).model_dump(),
    }


@app.get("/verify/{collector_id}")
def verify_chain(collector_id: str, who: Who, store: Db):
    require(who, "verify_chain", chain_resource(collector_id))
    return chain.verify(store.receipts_for(collector_id)).model_dump()


@app.get("/photos/{photo_sha256}.jpg")
def get_photo(photo_sha256: str, who: Who):
    require(who, "read_receipt_pii", {"type": "Photo", "id": photo_sha256})
    if len(photo_sha256) != 64 or not all(c in "0123456789abcdef" for c in photo_sha256):
        raise HTTPException(404, "no such photo")
    path = photo_dir() / f"{photo_sha256}.jpg"
    if not path.exists():
        raise HTTPException(404, "no such photo (seeded receipts have no photo files)")
    return FileResponse(path, media_type="image/jpeg")


# ---------- actors ----------

class Registration(BaseModel):
    name: str
    locality: str | None = None


@app.put("/actors/{actor_id}")
def register_kabadiwala(actor_id: str, body: Registration, who: Who,
                        store: Db):
    """The bot's /start: a Kabadiwala registers (or renames) themselves. Other roles come from the seed."""
    require(who, "register", {"type": "Actor", "id": actor_ref(actor_id)})
    existing = store.get_actor(actor_id)
    if existing and existing.role != "kabadiwala":
        raise HTTPException(409, f"{actor_id} is a {existing.role}")
    actor = Actor(actor_id=actor_id, role="kabadiwala", name=body.name, locality=body.locality)
    store.put_actor(actor)
    return actor.model_dump()


@app.get("/actors")
def list_actors(who: Who, store: Db, role: Role | None = None):
    require(who, "list_actors", {"type": "Directory", "role": role})
    return [a.model_dump() for a in store.list_actors(role)]


# ---------- fraud radar (auditor) ----------

class RadarRun(BaseModel):
    month: str | None = None


@app.post("/radar/run")
def run_radar(who: Who, store: Db, body: RadarRun | None = None):
    require(who, "run_radar", {"type": "Radar"})
    store.replace_flags(rules.run(store, body.month if body else None))
    return [f.model_dump(mode="json") for f in store.list_flags()]


@app.get("/flags")
def list_flags(who: Who, store: Db):
    require(who, "read_flags", {"type": "Radar"})
    return [f.model_dump(mode="json") for f in store.list_flags()]


class FlagDecision(BaseModel):
    decision: Literal["inspect", "dismiss"]


@app.post("/flags/{flag_id}/decision")
def decide_flag(flag_id: str, body: FlagDecision, who: Who, store: Db):
    """Only a person decides what happens to a Flag; the rule and the explanation never do."""
    flag = store.get_flag(flag_id)
    if flag is None:
        raise HTTPException(404, "no such flag")
    require(who, "approve_flag", {"type": "Flag", "id": flag_id, "rule": flag.rule})
    status = "inspection_requested" if body.decision == "inspect" else "dismissed"
    decided_by = who.removeprefix('Actor::"').removesuffix('"')
    return store.decide_flag(flag_id, status, decided_by).model_dump(mode="json")


# ---------- certificates (brand) ----------

def certificate_resource(cert) -> dict:
    return {"type": "Certificate", "id": cert.certificate_id, "buyer": actor_ref(cert.brand_id)}


@app.get("/certificates")
def list_certificates(brand_id: str, who: Who, store: Db):
    """A Brand's Certificates, each with its verified-backed percentage."""
    out = []
    for cert in store.list_certificates(brand_id=brand_id):
        require(who, "read_provenance", certificate_resource(cert))
        p = rules.provenance(store, cert)
        out.append({**p["certificate"], "verified_backed_pct": p["verified_backed_pct"]})
    return out


@app.get("/provenance/{certificate_id}")
def get_provenance(certificate_id: str, who: Who, store: Db):
    cert = store.get_certificate(certificate_id)
    if cert is None:
        raise HTTPException(404, "no such certificate")
    require(who, "read_provenance", certificate_resource(cert))
    return rules.provenance(store, cert)
