"""P2's agent writing through P3's SQLite store: the receipts it creates must verify."""
import base64

import pytest

from agent.agent import handle_collection
from common.models import CollectionRequest, Taps
from ledger import chain
from ledger.store import Store


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "1")


def req(kg=12.0, photo="fixture:12:PET:0.92"):
    return CollectionRequest(
        collector_id="kw-raju",
        photo_b64=base64.b64encode(photo.encode()).decode(),
        taps=Taps(material="PET", kg=kg),
        locality="Seelampur",
    )


def test_agent_receipts_verify_on_sqlite(tmp_path):
    store = Store(tmp_path / "kk.db")
    for i in range(3):
        assert handle_collection(req(photo=f"fixture:12:PET:0.92:photo{i}"), store).status == "receipt"
    result = chain.verify(store.receipts_for("kw-raju"))
    assert result.ok and result.length == 3


def test_mismatch_writes_nothing(tmp_path):
    store = Store(tmp_path / "kk.db")
    assert handle_collection(req(kg=20.0), store).status == "question"
    assert store.receipts_for("kw-raju") == []


def test_reused_photo_is_caught_through_the_store(tmp_path):
    store = Store(tmp_path / "kk.db")
    assert handle_collection(req(), store).status == "receipt"
    assert handle_collection(req(), store).status == "question"
    assert len(store.receipts_for("kw-raju")) == 1
