from pathlib import Path

import cedarpy
import pytest
from fastapi.testclient import TestClient

from api.app import app
from common.models import Actor
from ledger.store import Store
from policy import authz, directory
from policy.authz import AGENT, Decision, is_allowed

RAJU = 'Actor::"kw-raju"'
SITA = 'Actor::"kw-sita"'
BRAND1 = 'Actor::"brand-1"'
BRAND2 = 'Actor::"brand-2"'
AUDITOR = 'Actor::"auditor-1"'
RECYCLER = 'Actor::"rec-a"'


def chain(collector):
    return {"type": "Chain", "collector": collector}


def cert(buyer):
    return {"type": "Certificate", "id": "c1", "buyer": buyer}


def test_kabadiwala_creates_collection_on_own_chain():
    assert is_allowed(RAJU, "create_collection", chain(RAJU)).allowed


def test_kabadiwala_cannot_use_another_chain():
    d = is_allowed(RAJU, "create_collection", chain(SITA))
    assert not d.allowed and d.reason
    assert not is_allowed(RAJU, "read_receipt", chain(SITA)).allowed
    assert not is_allowed(RAJU, "create_collection", {"type": "Chain"}).allowed


def test_kabadiwala_reads_and_verifies_own_chain():
    assert is_allowed(RAJU, "read_receipt", chain(RAJU)).allowed
    assert is_allowed(RAJU, "verify_chain", chain(RAJU)).allowed
    assert not is_allowed(RAJU, "verify_chain", chain(SITA)).allowed


def test_kabadiwala_denied_read_receipt_pii():
    assert not is_allowed(RAJU, "read_receipt_pii", chain(RAJU)).allowed
    assert not is_allowed(RAJU, "run_radar", {"type": "Radar"}).allowed


def test_brand_reads_provenance_of_own_certificate():
    assert is_allowed(BRAND1, "read_provenance", cert(BRAND1)).allowed


def test_brand_denied_other_brands_certificate():
    assert not is_allowed(BRAND1, "read_provenance", cert(BRAND2)).allowed
    assert not is_allowed(BRAND1, "read_provenance", {"type": "Certificate"}).allowed


def test_brand_denied_receipt_pii_and_receipts():
    for action in ("read_receipt_pii", "read_receipt"):
        d = is_allowed(BRAND1, action, chain(RAJU))
        assert not d.allowed
        body = d.to_denial(action)
        assert body["denied_by"] == "cedar" and body["action"] == action and body["reason"]


def test_auditor_can_read_verify_run_radar_approve_flag():
    assert is_allowed(AUDITOR, "read_receipt", chain(RAJU)).allowed
    assert is_allowed(AUDITOR, "read_receipt_pii", chain(RAJU)).allowed
    assert is_allowed(AUDITOR, "verify_chain", chain(RAJU)).allowed
    assert is_allowed(AUDITOR, "run_radar", {"type": "Radar"}).allowed
    assert is_allowed(AUDITOR, "approve_flag", {"type": "Flag", "id": "f1"}).allowed
    assert is_allowed(AUDITOR, "read_provenance", cert(BRAND1)).allowed


def test_auditor_cannot_create_collection():
    assert not is_allowed(AUDITOR, "create_collection", chain(AUDITOR)).allowed


def test_agent_creates_receipt_only_when_consistency_ok():
    res = {"type": "Receipt", "collector": RAJU}
    assert is_allowed(AGENT, "create_receipt", res, {"consistency_ok": True}).allowed
    assert not is_allowed(AGENT, "create_receipt", res, {"consistency_ok": False}).allowed
    assert not is_allowed(AGENT, "create_receipt", res, {}).allowed
    assert not is_allowed(AGENT, "create_receipt", res).allowed
    # existing agent tests pass no resource type
    assert is_allowed(AGENT, "create_receipt", {}, {"consistency_ok": True}).allowed


@pytest.mark.parametrize("action,resource", [
    ("approve_flag", {"type": "Flag"}),
    ("issue_certificate", {"type": "Certificate"}),
    ("read_receipt_pii", {"type": "Receipt"}),
    ("read_receipt", {"type": "Receipt"}),
    ("read_provenance", {"type": "Certificate"}),
    ("run_radar", {"type": "Radar"}),
    ("verify_chain", {"type": "Chain"}),
    ("create_collection", {"type": "Chain"}),
])
def test_agent_forbidden_everything_else(action, resource):
    d = is_allowed(AGENT, action, resource, {"consistency_ok": True})
    assert not d.allowed
    assert "forbidden" in d.reason


def test_recycler_default_denied():
    for action, res in [("read_receipt", chain(RECYCLER)), ("read_provenance", cert(RECYCLER)),
                        ("run_radar", {"type": "Radar"}), ("approve_flag", {"type": "Flag"})]:
        assert not is_allowed(RECYCLER, action, res).allowed


def test_issue_certificate_denied_for_all():
    for who in (RAJU, BRAND1, AUDITOR, RECYCLER, AGENT):
        assert not is_allowed(who, "issue_certificate", cert(BRAND1)).allowed


def test_unknown_principal_denied_with_reason():
    d = is_allowed('Actor::"ghost"', "read_receipt", chain('Actor::"ghost"'))
    assert not d.allowed and "unknown principal" in d.reason
    assert not is_allowed('Agent::"other"', "create_receipt", {}, {"consistency_ok": True}).allowed


def test_malformed_principal_or_resource_denied():
    assert not is_allowed('Actor::"a\\"b"', "read_receipt", chain(RAJU)).allowed
    assert not is_allowed("kw-raju", "read_receipt", chain(RAJU)).allowed
    assert not is_allowed(RAJU, "read_receipt", {}).allowed
    assert not is_allowed(RAJU, "read_receipt", {"type": "Nope"}).allowed
    assert not is_allowed(RAJU, "read_receipt", chain('Agent::"kabadi-agent"')).allowed
    assert not is_allowed(RAJU, "read_receipt", "not a dict").allowed
    assert not is_allowed(None, "read_receipt", chain(RAJU)).allowed


def test_unknown_action_denied():
    d = is_allowed(AUDITOR, "delete_everything", {"type": "Chain"})
    assert not d.allowed and "unknown action" in d.reason


def test_cedar_exception_denies(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("cedar exploded")
    monkeypatch.setattr(authz.cedarpy, "is_authorized", boom)
    d = is_allowed(AUDITOR, "run_radar", {"type": "Radar"})
    assert not d.allowed and d.reason.startswith("policy error")


def test_consistency_ok_wrong_type_denied():
    res = {"type": "Receipt"}
    assert not is_allowed(AGENT, "create_receipt", res, {"consistency_ok": "true"}).allowed
    assert not is_allowed(AGENT, "create_receipt", res, {"consistency_ok": 1}).allowed
    assert not is_allowed(AGENT, "create_receipt", res, {"consistency_ok": None}).allowed


def test_missing_policy_file_denies(monkeypatch, tmp_path):
    monkeypatch.setattr(authz, "_POLICY_DIR", tmp_path)
    authz._load.cache_clear()
    try:
        d = is_allowed(AUDITOR, "run_radar", {"type": "Radar"})
        assert not d.allowed and d.reason == "policy unavailable"
    finally:
        monkeypatch.undo()
        authz._load.cache_clear()
    assert is_allowed(AUDITOR, "run_radar", {"type": "Radar"}).allowed


class _Diag:
    def __init__(self, errors):
        self.errors, self.reasons = errors, []


class _Result:
    def __init__(self, decision, errors=()):
        self.decision, self.diagnostics = decision, _Diag(list(errors))


def test_allow_requires_cedar_allow(monkeypatch):
    monkeypatch.setattr(authz.cedarpy, "is_authorized",
                        lambda *a, **k: _Result(cedarpy.Decision.Deny))
    assert not is_allowed(AUDITOR, "run_radar", {"type": "Radar"}).allowed
    monkeypatch.setattr(authz.cedarpy, "is_authorized",
                        lambda *a, **k: _Result(cedarpy.Decision.Allow, ["type error"]))
    d = is_allowed(AUDITOR, "run_radar", {"type": "Radar"})
    assert not d.allowed and d.reason.startswith("policy error")


def test_seed_after_start_refreshes_directory(tmp_path):
    store = Store(str(tmp_path / "kk.db"))
    directory.load_from_store(store)
    who = 'Actor::"kw-late"'
    assert not is_allowed(who, "read_receipt", chain(who)).allowed
    store.put_actor(Actor(actor_id="kw-late", role="kabadiwala", name="Late"))
    assert is_allowed(who, "read_receipt", chain(who)).allowed


def test_policies_validate_against_schema():
    base = Path(authz.__file__).parent
    result = cedarpy.validate_policies(
        (base / "policies.cedar").read_text(), (base / "schema.cedarschema").read_text())
    assert result.validation_passed, [str(e) for e in result.errors]


def test_directory_register_rejects_bad_role():
    with pytest.raises(ValueError):
        directory.register("x", "wizard")
    with pytest.raises(ValueError):
        directory.register('a"b', "brand")


def test_load_from_store_registers_actors(tmp_path):
    store = Store(str(tmp_path / "kk.db"))
    store.put_actor(Actor(actor_id="kw-new", role="kabadiwala", name="New"))
    store.put_actor(Actor(actor_id="brand-9", role="brand", name="Nine"))
    assert directory.load_from_store(store) == 2
    assert directory.role_of("kw-new") == "kabadiwala"
    assert directory.role_of("kw-raju") == "kabadiwala"  # additive


def test_decision_to_denial_shape():
    assert Decision(False, "why").to_denial("read_receipt") == {
        "denied_by": "cedar", "action": "read_receipt", "reason": "why"}


def test_api_denies_kabadiwala_reading_another_chain(tmp_path, monkeypatch):
    monkeypatch.setenv("KK_DB_PATH", str(tmp_path / "kk.db"))
    monkeypatch.setenv("KK_PHOTO_DIR", str(tmp_path / "photos"))
    client = TestClient(app)
    r = client.get("/receipts", params={"collector_id": "kw-sita"}, headers={"X-Principal": "kw-raju"})
    assert r.status_code == 403
    assert r.json()["denied_by"] == "cedar" and r.json()["reason"]
    r = client.get("/receipts", params={"collector_id": "kw-raju"}, headers={"X-Principal": "brand-1"})
    assert r.status_code == 403


@pytest.mark.parametrize("action", ["search_receipts", "read_analytics"])
def test_search_copy_is_auditor_only(action):
    index = {"type": "SearchIndex"}
    assert is_allowed('Actor::"auditor-1"', action, index).allowed
    for who in ('Actor::"brand-1"', 'Actor::"kw-raju"', 'Actor::"rec-a"', AGENT):
        assert not is_allowed(who, action, index).allowed
