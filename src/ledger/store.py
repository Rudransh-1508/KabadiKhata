"""SQLite storage for Actors, Receipts, Certificates and Flags.

Receipts are append-only: `append_receipt` is the only way in, and it assigns
seq, prev_hash, hash and receipt_id itself. Satisfies `common.ports.ReceiptStore`.
"""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from common.models import Actor, Certificate, Flag, Receipt
from ledger import chain
from ledger.chain import format_ts

SCHEMA = """
CREATE TABLE IF NOT EXISTS actors (
    actor_id TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    name TEXT NOT NULL,
    locality TEXT
);
CREATE TABLE IF NOT EXISTS receipts (
    receipt_id TEXT NOT NULL UNIQUE,
    collector_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    material TEXT NOT NULL,
    weight_kg REAL NOT NULL,
    price_inr_per_kg REAL NOT NULL,
    locality TEXT NOT NULL,
    ts TEXT NOT NULL,
    photo_sha256 TEXT NOT NULL,
    phash TEXT NOT NULL,
    voice_text TEXT,
    evidence TEXT NOT NULL,
    recycler_id TEXT,
    synthetic INTEGER NOT NULL,
    prev_hash TEXT NOT NULL,
    hash TEXT NOT NULL,
    PRIMARY KEY (collector_id, seq)
);
CREATE INDEX IF NOT EXISTS receipts_by_recycler ON receipts (recycler_id, material);
CREATE TABLE IF NOT EXISTS certificates (
    certificate_id TEXT PRIMARY KEY,
    recycler_id TEXT NOT NULL,
    brand_id TEXT NOT NULL,
    month TEXT NOT NULL,
    material TEXT NOT NULL,
    tonnes REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS flags (
    flag_id TEXT PRIMARY KEY,
    rule TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    score REAL NOT NULL,
    evidence_ids TEXT NOT NULL,
    explanation_en TEXT,
    explanation_hi TEXT,
    status TEXT NOT NULL,
    decided_by TEXT,
    decided_ts TEXT
);
"""


class Store:
    def __init__(self, path: str | Path, mirror=None):
        """`mirror` (search.mirror.Mirror) gets a best-effort copy of each new Receipt."""
        self.path = Path(path)
        self.mirror = mirror
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.executescript(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path, isolation_level=None, timeout=10)
        con.row_factory = sqlite3.Row
        return con

    @contextmanager
    def _write(self) -> Iterator[sqlite3.Connection]:
        con = self._connect()
        try:
            # IMMEDIATE takes the write lock up front, so two appends to the
            # same Chain can't both read the same last seq
            con.execute("BEGIN IMMEDIATE")
            yield con
            con.execute("COMMIT")
        except BaseException:
            con.execute("ROLLBACK")
            raise
        finally:
            con.close()

    def _read(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        con = self._connect()
        try:
            return con.execute(sql, params).fetchall()
        finally:
            con.close()

    # Actors

    def put_actor(self, actor: Actor) -> None:
        with self._write() as con:
            con.execute(
                "INSERT OR REPLACE INTO actors VALUES (?, ?, ?, ?)",
                (actor.actor_id, actor.role, actor.name, actor.locality),
            )

    def get_actor(self, actor_id: str) -> Actor | None:
        rows = self._read("SELECT * FROM actors WHERE actor_id = ?", (actor_id,))
        return Actor(**dict(rows[0])) if rows else None

    def list_actors(self, role: str | None = None) -> list[Actor]:
        if role:
            rows = self._read("SELECT * FROM actors WHERE role = ? ORDER BY actor_id", (role,))
        else:
            rows = self._read("SELECT * FROM actors ORDER BY actor_id")
        return [Actor(**dict(r)) for r in rows]

    # Receipts

    def append_receipt(self, fields: dict) -> Receipt:
        """Add a Receipt to the end of `fields["collector_id"]`'s Chain."""
        with self._write() as con:
            last = con.execute(
                "SELECT seq, hash FROM receipts WHERE collector_id = ? ORDER BY seq DESC LIMIT 1",
                (fields["collector_id"],),
            ).fetchone()
            seq, prev_hash = (last["seq"] + 1, last["hash"]) if last else (0, chain.GENESIS)
            receipt = chain.seal(fields, seq, prev_hash)
            con.execute(
                "INSERT INTO receipts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    receipt.receipt_id, receipt.collector_id, receipt.seq, receipt.material,
                    receipt.weight_kg, receipt.price_inr_per_kg, receipt.locality, format_ts(receipt.ts),
                    receipt.photo_sha256, receipt.phash, receipt.voice_text,
                    json.dumps(receipt.evidence, ensure_ascii=False), receipt.recycler_id,
                    int(receipt.synthetic), receipt.prev_hash, receipt.hash,
                ),
            )
        if self.mirror is not None:
            self.mirror.index_receipt(receipt)
        return receipt

    def all_receipts(self) -> list[Receipt]:
        rows = self._read("SELECT * FROM receipts ORDER BY collector_id, seq")
        return [_receipt(r) for r in rows]

    def get_receipt(self, receipt_id: str) -> Receipt | None:
        rows = self._read("SELECT * FROM receipts WHERE receipt_id = ?", (receipt_id,))
        return _receipt(rows[0]) if rows else None

    def receipts_for(self, collector_id: str) -> list[Receipt]:
        rows = self._read("SELECT * FROM receipts WHERE collector_id = ? ORDER BY seq", (collector_id,))
        return [_receipt(r) for r in rows]

    def find_receipt_by_phash(self, phash: str) -> str | None:
        if not phash:
            return None
        rows = self._read("SELECT receipt_id FROM receipts WHERE phash = ? LIMIT 1", (phash,))
        return rows[0]["receipt_id"] if rows else None

    def collector_ids(self) -> list[str]:
        return [r["collector_id"] for r in self._read("SELECT DISTINCT collector_id FROM receipts ORDER BY 1")]

    def receipts_sold_to(self, recycler_id: str) -> list[Receipt]:
        rows = self._read("SELECT * FROM receipts WHERE recycler_id = ? ORDER BY ts", (recycler_id,))
        return [_receipt(r) for r in rows]

    # Certificates

    def put_certificate(self, cert: Certificate) -> None:
        with self._write() as con:
            con.execute(
                "INSERT OR REPLACE INTO certificates VALUES (?, ?, ?, ?, ?, ?)",
                (cert.certificate_id, cert.recycler_id, cert.brand_id, cert.month, cert.material, cert.tonnes),
            )

    def get_certificate(self, certificate_id: str) -> Certificate | None:
        rows = self._read("SELECT * FROM certificates WHERE certificate_id = ?", (certificate_id,))
        return Certificate(**dict(rows[0])) if rows else None

    def list_certificates(self, *, recycler_id: str | None = None, brand_id: str | None = None) -> list[Certificate]:
        sql, params = "SELECT * FROM certificates WHERE 1=1", []
        if recycler_id:
            sql += " AND recycler_id = ?"
            params.append(recycler_id)
        if brand_id:
            sql += " AND brand_id = ?"
            params.append(brand_id)
        return [Certificate(**dict(r)) for r in self._read(sql + " ORDER BY certificate_id", tuple(params))]

    # Flags

    def replace_flags(self, flags: list[Flag]) -> None:
        """Store the result of a radar run, keeping decisions already made on the same flag_id."""
        with self._write() as con:
            decided = {
                r["flag_id"]: r
                for r in con.execute("SELECT flag_id, status, decided_by, decided_ts FROM flags WHERE status != 'open'")
            }
            con.execute("DELETE FROM flags")
            for f in flags:
                if prior := decided.get(f.flag_id):
                    f = f.model_copy(update={
                        "status": prior["status"],
                        "decided_by": prior["decided_by"],
                        "decided_ts": prior["decided_ts"],
                    })
                con.execute(
                    "INSERT INTO flags VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (f.flag_id, f.rule, f.subject_id, f.score, json.dumps(f.evidence_ids),
                     f.explanation_en, f.explanation_hi, f.status, f.decided_by,
                     format_ts(f.decided_ts) if isinstance(f.decided_ts, datetime) else f.decided_ts),
                )

    def list_flags(self) -> list[Flag]:
        return [_flag(r) for r in self._read("SELECT * FROM flags ORDER BY score DESC, flag_id")]

    def get_flag(self, flag_id: str) -> Flag | None:
        rows = self._read("SELECT * FROM flags WHERE flag_id = ?", (flag_id,))
        return _flag(rows[0]) if rows else None

    def decide_flag(self, flag_id: str, status: str, decided_by: str) -> Flag | None:
        now = format_ts(datetime.now(timezone.utc))
        with self._write() as con:
            cur = con.execute(
                "UPDATE flags SET status = ?, decided_by = ?, decided_ts = ? WHERE flag_id = ?",
                (status, decided_by, now, flag_id),
            )
            if cur.rowcount == 0:
                return None
        return self.get_flag(flag_id)


def _receipt(row: sqlite3.Row) -> Receipt:
    d = dict(row)
    d["evidence"] = json.loads(d["evidence"])
    d["synthetic"] = bool(d["synthetic"])
    return Receipt(**d)


def _flag(row: sqlite3.Row) -> Flag:
    d = dict(row)
    d["evidence_ids"] = json.loads(d["evidence_ids"])
    return Flag(**d)
