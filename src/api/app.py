"""HTTP API (FastAPI on SQLite, see docs/adr/0001). Port 3000.

Every handler asks policy.authz.is_allowed() before touching data. The caller
names itself in the X-Principal header (a stand-in for real auth); a denial is
HTTP 403 with {"denied_by": "cedar", ...}, which the console shows as a banner.
"""

import binascii
import base64
import hashlib
import logging
import os
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from agent.agent import handle_collection
from common.models import CollectionRequest
from ledger import chain
from ledger.store import Store
from policy.authz import Decision, is_allowed

log = logging.getLogger("kk.api")

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
def create_collection(req: CollectionRequest, who: str = Depends(principal), store: Store = Depends(get_store)):
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
def list_receipts(collector_id: str, who: str = Depends(principal), store: Store = Depends(get_store)):
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
    }


@app.get("/verify/{collector_id}")
def verify_chain(collector_id: str, who: str = Depends(principal), store: Store = Depends(get_store)):
    require(who, "verify_chain", chain_resource(collector_id))
    return chain.verify(store.receipts_for(collector_id)).model_dump()
