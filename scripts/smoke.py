"""`make smoke`: check every endpoint and the four spine beats against a running, seeded stack.

    make demo     # in one terminal
    make smoke    # in another; exits 1 if anything fails

Writes only to a throwaway Kabadiwala (kw-smoke), so Raju's demo chain stays clean.
"""

import base64
import os
import sys
import uuid

import httpx

API = os.getenv("KK_API_URL", "http://localhost:3000").rstrip("/")
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))


def call(method: str, path: str, who: str, **kw) -> httpx.Response:
    return httpx.request(method, f"{API}{path}", headers={"X-Principal": who}, timeout=60, **kw)


def photo(tag: str) -> str:
    return base64.b64encode(f"fixture:12:PET:0.92:{tag}".encode()).decode()


def main() -> int:
    try:
        health = httpx.get(f"{API}/health", timeout=5).json()
    except httpx.HTTPError as exc:
        print(f"API not reachable at {API} ({exc}). Start it with `make demo`.")
        return 1
    check("API up", health.get("ok") is True)

    # Beat 1: receipt with a refusal
    me = f"kw-smoke-{uuid.uuid4().hex[:6]}"
    r = call("PUT", f"/actors/{me}", me, json={"name": "Smoke", "locality": "Okhla"})
    check("bot /start registers a new kabadiwala", r.status_code == 200, str(r.status_code))
    body = {"collector_id": me, "locality": "Okhla", "taps": {"material": "PET", "kg": 12}}
    r = call("POST", "/collections", me, json=body | {"photo_b64": photo(me)}).json()
    check("beat 1: matching photo -> receipt", r.get("status") == "receipt", r.get("receipt", {}).get("receipt_id", ""))
    r = call("POST", "/collections", me, json=body | {"photo_b64": photo(me + "b"), "taps": {"material": "PET", "kg": 20}}).json()
    check("beat 1: mismatch -> Hindi question, nothing written",
          r.get("status") == "question" and len(call("GET", "/receipts", me, params={"collector_id": me}).json()["receipts"]) == 1,
          (r.get("question_hi") or "")[:40])
    r = call("GET", "/receipts", me, params={"collector_id": me}).json()
    check("income history with chain status", r["chain"]["ok"] and r["monthly"][0]["count"] == 1)

    # Beat 2: fraud caught, auditor decides
    flags = call("POST", "/radar/run", "au-1").json()
    r1 = [f for f in flags if f["rule"] == "R1_mass_balance"]
    check("beat 2: radar flags an over-claiming recycler", bool(r1), r1[0]["subject_id"] if r1 else "no R1 flag")
    if r1:
        d = call("POST", f"/flags/{r1[0]['flag_id']}/decision", "au-1", json={"decision": "inspect"})
        check("beat 2: auditor requests inspection", d.status_code == 200 and d.json()["status"] == "inspection_requested")
    check("brand cannot run the radar", call("POST", "/radar/run", "br-1").status_code == 403)

    # Beat 3: tamper breaks the chain (the seeded tamper; smoke never edits data itself)
    r3 = [f for f in flags if f["rule"] == "R3_broken_chain"]
    if r3:
        v = call("GET", f"/verify/{r3[0]['subject_id']}", "au-1").json()
        check("beat 3: tampered chain reports its broken seq", v["ok"] is False and v["broken_at_seq"] is not None,
              f"{r3[0]['subject_id']} #{v['broken_at_seq']}")
    else:
        check("beat 3: tampered chain reports its broken seq", False, "no R3 flag in the seeded world")

    # Beat 4: Cedar denial, provenance only in aggregate
    denied = call("GET", "/receipts", "br-1", params={"collector_id": "kw-raju"})
    check("beat 4: brand denied a kabadiwala's receipts", denied.status_code == 403 and denied.json().get("denied_by") == "cedar")
    certs = call("GET", "/certificates", "br-1", params={"brand_id": "br-1"}).json()
    check("brand sees verified-backed % per certificate", bool(certs) and all("verified_backed_pct" in c for c in certs))
    if certs:
        p = call("GET", f"/provenance/{certs[0]['certificate_id']}", "br-1")
        check("brand provenance is aggregate", p.status_code == 200 and "kw-" not in p.text)
    other = call("GET", "/certificates", "br-1", params={"brand_id": "br-2"})
    check("brand cannot see another brand's certificates", other.status_code == 403, str(other.status_code))

    # Search copy (optional)
    s = call("GET", "/search/receipts", "au-1", params={"q": me})
    if s.status_code == 503:
        check("search copy (OpenSearch)", True, "off or down: skipped")
    else:
        check("search copy finds the new receipt", s.status_code == 200 and s.json()["total"] >= 1, str(s.status_code))

    width = max(len(n) for n, _, _ in results)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {detail}")
    failed = sum(not ok for _, ok, _ in results)
    print(f"\n{len(results) - failed}/{len(results)} passed against {API}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
