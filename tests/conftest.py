import pytest

from policy import directory


@pytest.fixture(autouse=True)
def no_search_copy_by_default(monkeypatch):
    """`make test` exports .env; keep tests from writing into the demo's OpenSearch index."""
    monkeypatch.setenv("KK_OPENSEARCH_URL", "")


@pytest.fixture(autouse=True)
def actor_directory():
    """Fail-closed authz needs roles; register the actors the tests use."""
    directory.clear()
    for actor_id, role in [
        ("kw-raju", "kabadiwala"), ("kw-sita", "kabadiwala"),
        ("brand-1", "brand"), ("brand-2", "brand"),
        ("auditor-1", "auditor"), ("rec-a", "recycler"),
    ]:
        directory.register(actor_id, role)
    yield
    directory.clear()
