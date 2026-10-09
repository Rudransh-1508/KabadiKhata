"""Kabadi Khata console (Streamlit) — Auditor and Brand views, wired to the real API.

Run:  streamlit run console/app.py       (use the venv; seed + uvicorn first)

Backend: real API by default when KK_USE_MOCK=0, else an offline synthetic mock
(console.mock_api), selected below exactly as the bot selects its backend.

Two roles (sidebar), each acting as a real seeded actor via the X-Principal header:
- Auditor (au-1): run the fraud radar, see Flags with evidence, Request inspection /
  Dismiss. For an R1 Flag, the claimed-vs-verified bar is read from /provenance.
- Brand   (br-1/br-2): its Certificates with a verified-backed % + badge, provenance
  in aggregate, and the REAL red "Denied by Cedar policy" banner when it tries to
  read kabadiwala identities (GET /actors -> 403).
"""
from __future__ import annotations

import datetime
import os

import pandas as pd
import streamlit as st

try:  # `streamlit run console/app.py` puts console/ on the path; tests import as a package
    from console.logic import apply_decision, backed_badge, bar_from_provenance, rule_label
    from console.api_client import CedarDenied
    if os.environ.get("KK_USE_MOCK", "1") == "0":
        from console import api_client as api
    else:
        from console import mock_api as api
except ImportError:  # pragma: no cover
    from logic import apply_decision, backed_badge, bar_from_provenance, rule_label
    from api_client import CedarDenied
    if os.environ.get("KK_USE_MOCK", "1") == "0":
        import api_client as api
    else:
        import mock_api as api

st.set_page_config(page_title="Kabadi Khata console", page_icon="♻️", layout="wide")

# "Acting as" -> a real seeded actor id, so X-Principal is authentic (handoff §6).
AUDITOR = "au-1"
BRANDS = ["br-1", "br-2"]


def _principal(actor_id: str) -> str:
    """The API expects the bare id in X-Principal; it wraps it as Actor::\"id\" itself."""
    return actor_id


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _is_mock() -> bool:
    return getattr(api, "__name__", "").endswith("mock_api")


def auditor_view() -> None:
    st.header("Auditor — fraud radar")
    st.caption("Code decides the flag · the LLM only explains · the auditor approves.")
    principal = _principal(AUDITOR)

    if st.button("▶ Run radar", type="primary"):
        st.session_state["flags"] = api.run_radar(principal)
    if "flags" not in st.session_state:
        st.info("Click **Run radar** to scan the seeded recycler data.")
        return

    flags = st.session_state["flags"]

    rows = [{
        "Flag": f["flag_id"],
        "Rule": rule_label(f["rule"]),
        "Subject": f["subject_id"],
        "Score": f["score"],
        "Status": f["status"],
    } for f in flags]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    for f in flags:
        with st.expander(f"{f['flag_id']} — {rule_label(f['rule'])} — {f['subject_id']}  ·  {f['status']}"):
            if f.get("explanation_en"):
                st.write(f["explanation_en"])
            if f.get("explanation_hi"):
                st.caption(f["explanation_hi"])

            if f["rule"] == "R1_mass_balance" and f.get("evidence_ids"):
                cert_id = f["evidence_ids"][0]  # R1 evidence_ids are certificate ids
                try:
                    prov = api.provenance(cert_id, principal)
                    bar = bar_from_provenance(prov)
                    gap = "∞" if bar["ratio"] == float("inf") else f"{bar['ratio']:.0f}×"
                    st.subheader(f"Claimed vs verified inflow  ·  {gap} gap")
                    st.bar_chart(
                        pd.DataFrame({"tonnes": [bar["claimed"], bar["verified"]]},
                                     index=["Claimed", "Verified inflow"]),
                        color="#1d7a48",
                    )
                except Exception as exc:  # provenance is best-effort; the flag still stands
                    st.caption(f"(Provenance for {cert_id} unavailable: {exc})")
            elif f["rule"] == "R2_duplicate_photo":
                st.metric("Receipts in near-identical cluster", int(f["score"]))
                st.caption("(Side-by-side duplicate photos render here once photo files are wired.)")
            elif f["rule"] == "R3_broken_chain":
                st.metric("Chain broken at seq", f.get("facts", {}).get("broken_at_seq", "—"))

            st.write(f"**Evidence:** {', '.join(f.get('evidence_ids', [])) or '—'}")

            if f["status"] == "open":
                c1, c2, _ = st.columns([1, 1, 3])
                if c1.button("Request inspection", key="insp_" + f["flag_id"]):
                    _decide(f["flag_id"], "inspect", principal)
                if c2.button("Dismiss", key="dis_" + f["flag_id"]):
                    _decide(f["flag_id"], "dismiss", principal)
            else:
                st.success(f"{f['status']}"
                           + (f" by {f['decided_by']}" if f.get("decided_by") else "")
                           + (f" at {f['decided_ts']}" if f.get("decided_ts") else ""))


def _decide(flag_id: str, decision: str, principal: str) -> None:
    updated = api.decide_flag(flag_id, decision, principal)
    st.session_state["flags"] = [updated if g["flag_id"] == flag_id else g
                                 for g in st.session_state["flags"]]
    st.rerun()


def brand_view() -> None:
    st.header("Brand — my EPR certificates")
    brand_id = st.session_state.get("brand_id", BRANDS[0])
    principal = _principal(brand_id)
    threshold = 80
    st.caption(f"A certificate is trustworthy at ≥ {threshold}% verified-backed.")

    certs = api.list_certificates(brand_id, principal)
    if not certs:
        st.info(f"No certificates for {brand_id}.")
        return

    rows = [{
        "Certificate": c["certificate_id"],
        "Recycler": c["recycler_id"],  # identity stays aggregate; only the id is shown
        "Material": c["material"],
        "Tonnes": c["tonnes"],
        "Verified-backed %": c["verified_backed_pct"],
        "": "🟢 OK" if backed_badge(c["verified_backed_pct"], threshold) == "ok" else "🔴 LOW",
    } for c in certs]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    labels = [f"{c['certificate_id']} ({c['recycler_id']})" for c in certs]
    pick = st.selectbox("Inspect a certificate's provenance", labels)
    cert = certs[labels.index(pick)]

    if backed_badge(cert["verified_backed_pct"], threshold) == "low":
        st.error(f"⚠ {cert['certificate_id']} is only {cert['verified_backed_pct']}% verified-backed "
                 f"(threshold {threshold}%). Do not buy.")
    else:
        st.success(f"{cert['certificate_id']} is {cert['verified_backed_pct']}% verified-backed.")

    st.subheader("Provenance (aggregate)")
    prov = api.provenance(cert["certificate_id"], principal)
    by_locality = prov.get("by_locality", [])
    st.dataframe(
        pd.DataFrame([{"Locality": p["locality"].replace("_", " ").title(),
                       "Receipts": p["receipts"], "Tonnes": p["tonnes"]} for p in by_locality]),
        hide_index=True, width="stretch",
    )

    if st.button("Show collector identities"):
        try:
            api.list_actors(principal, role="kabadiwala")
            st.warning("Identities returned — Cedar did not deny this (unexpected).")
        except CedarDenied as denied:
            st.error(f"🔒 Denied by Cedar policy (action: {denied.action}). "
                     f"{denied.reason or 'A brand cannot read kabadiwala identities.'} "
                     "Provenance is shown in aggregate only.")


def main() -> None:
    st.sidebar.title("♻️ Kabadi Khata")
    role = st.sidebar.radio("Role", ["Auditor", "Brand"])
    if role == "Brand":
        st.session_state["brand_id"] = st.sidebar.selectbox("Acting as", BRANDS)
    else:
        st.sidebar.caption(f"Acting as auditor `{AUDITOR}`")
    if _is_mock():
        st.sidebar.warning("SYNTHETIC data (offline mock). Set KK_USE_MOCK=0 for the live API.")
    else:
        st.sidebar.caption(f"Live API · {api.BASE_URL}")

    if role == "Auditor":
        auditor_view()
    else:
        brand_view()


main()
