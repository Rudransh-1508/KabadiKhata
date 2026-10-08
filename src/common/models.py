"""Shared data contracts (SCOPED_DOWN §3). Frozen at kickoff: change only with the whole team."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional, get_args

from pydantic import BaseModel, Field

Material = Literal[
    "PET", "HDPE", "LDPE_film", "mixed_plastic", "cardboard", "paper", "metal", "ewaste", "unknown"
]
MATERIALS: tuple[str, ...] = get_args(Material)


# ---------- ledger ----------

class Receipt(BaseModel):
    """One verified collection. Stored in the `receipts` index; hash-chained per collector."""
    receipt_id: str                      # "KK-" + 6 chars, shown on the card
    collector_id: str
    seq: int                             # position in this collector's chain
    material: Material
    weight_kg: float                     # always the scale reading, never the claimed number
    price_inr_per_kg: float
    locality: str
    ts: datetime                         # UTC
    photo_sha256: str
    phash: str                           # 64-bit hex
    voice_text: Optional[str] = None
    evidence: dict = Field(default_factory=dict)
    recycler_id: Optional[str] = None    # set by seed data
    prev_hash: str                       # "GENESIS" for seq 0
    hash: str
    synthetic: bool = False


class Claim(BaseModel):
    claim_id: str
    certificate_id: str
    recycler_id: str
    brand_id: str
    month: str                           # "2026-09"
    material: Material
    tonnes_claimed: float


class Flag(BaseModel):
    flag_id: str
    rule: Literal["R1_mass_balance", "R2_duplicate_photo", "R3_broken_chain"]
    subject_id: str
    score: float
    evidence_ids: list[str] = Field(default_factory=list)
    explanation_en: Optional[str] = None
    explanation_hi: Optional[str] = None
    status: Literal["open", "inspection_requested", "dismissed"] = "open"
    decided_by: Optional[str] = None
    decided_ts: Optional[datetime] = None


class Actor(BaseModel):
    actor_id: str
    role: Literal["kabadiwala", "recycler", "brand", "auditor"]
    name: str
    locality: Optional[str] = None


# ---------- POST /collections ----------

class Taps(BaseModel):
    material: Optional[Material] = None
    kg: Optional[float] = None


class CollectionRequest(BaseModel):
    collector_id: str
    photo_b64: str                       # resized to <=1024 px by the bot (CLAUDE.md #3)
    audio_b64: Optional[str] = None      # WAV 16 kHz mono; the bot converts Telegram OGG (CLAUDE.md #3)
    taps: Optional[Taps] = None
    text: Optional[str] = None           # free-text note; untrusted data, never instructions
    locality: str


class CollectionResult(BaseModel):
    status: Literal["receipt", "question"]
    receipt: Optional[Receipt] = None
    question_hi: Optional[str] = None
    reasons: list[str] = Field(default_factory=list)
    trace: list[dict] = Field(default_factory=list)


# ---------- tool results (signatures in SCOPED_DOWN §3.3; P1 implements the real ones) ----------

class PhotoRead(BaseModel):
    kg: Optional[float]
    material: Material
    confidence: float


class Transcript(BaseModel):
    text_hi: str
    claimed_kg: Optional[float] = None
    claimed_material: Optional[Material] = None


class PhashResult(BaseModel):
    phash: str
    is_duplicate: bool
    nearest_receipt_id: Optional[str] = None


class PriceQuote(BaseModel):
    inr_per_kg: float
    total_inr: float
    source: str


class ConsistencyResult(BaseModel):
    ok: bool
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    question_hi: Optional[str] = None
