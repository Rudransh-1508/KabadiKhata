"""Pure helpers for the Kabadi Khata console (no Streamlit, no HTTP — so they are
unit-testable and shared by both backends).

Data loading lives in the two backends (``console.api_client`` for the real API,
``console.mock_api`` for offline/AppTest, both with the same surface). These
functions only compute the small derived values the UI shows, from shapes the
real API actually returns (see docs/SESSION_HANDOFF.md §6).
"""
from __future__ import annotations

# Rule literals as the real radar emits them (src/common/models.py Flag.rule).
RULE_LABELS = {
    "R1_mass_balance": "R1 · Mass balance",
    "R2_duplicate_photo": "R2 · Duplicate photo",
    "R3_broken_chain": "R3 · Broken chain",
}


def rule_label(rule: str) -> str:
    return RULE_LABELS.get(rule, rule)


def bar_from_provenance(prov: dict) -> dict:
    """Claimed vs verified-inflow tonnes for the R1 bar, from a /provenance payload.

    The Flag itself only carries ``score`` (the over-claim ratio); the actual
    tonnes come from GET /provenance/{cert_id} (cert_id = flag.evidence_ids[0]).
    """
    claimed = float(prov.get("recycler_certified_t", 0.0))
    verified = float(prov.get("verified_inflow_t", 0.0))
    ratio = (claimed / verified) if verified > 0 else float("inf")
    return {"claimed": claimed, "verified": verified, "ratio": ratio}


def backed_badge(pct: float, threshold: int) -> str:
    """'ok' if a certificate meets the verified-backed threshold, else 'low'."""
    return "ok" if pct >= threshold else "low"


def apply_decision(flag: dict, decision: str, by: str, ts: str) -> dict:
    """A copy of the flag with an auditor decision recorded, for optimistic UI.

    decision: 'inspect' -> status 'inspection_requested'; 'dismiss' -> 'dismissed'.
    Mirrors the backend's POST /flags/{id}/decision so the view can update without
    a reload; the authoritative status is whatever the API returns.
    """
    status = {"inspect": "inspection_requested", "dismiss": "dismissed"}.get(decision, flag.get("status"))
    out = dict(flag)
    out["status"] = status
    out["decided_by"] = by
    out["decided_ts"] = ts
    return out
