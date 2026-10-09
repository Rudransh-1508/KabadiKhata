import pytest


@pytest.fixture(autouse=True)
def no_search_copy_by_default(monkeypatch):
    """`make test` exports .env; keep tests from writing into the demo's OpenSearch index."""
    monkeypatch.setenv("KK_OPENSEARCH_URL", "")
