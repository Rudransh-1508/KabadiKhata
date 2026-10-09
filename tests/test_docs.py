"""The docs stay true to the code: every path, action, policy id, reason code, env var and make target
they name exists, and the run-sheet commands work offline."""
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.app import app
from ledger.store import Store
from ledger.world import load_world, sample_world

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "agent_and_policy.md"
AGENT_README = ROOT / "src" / "agent" / "README.md"
DOCS = [DOC, AGENT_README]
POLICIES = (ROOT / "src/policy/policies.cedar").read_text(encoding="utf-8")
SCHEMA = (ROOT / "src/policy/schema.cedarschema").read_text(encoding="utf-8")


def text(p: Path = DOC) -> str:
    return p.read_text(encoding="utf-8")


def ticks(s: str) -> list:
    return re.findall(r"`([^`\n]+)`", s)


def table_rows(s: str):
    return [[c.strip() for c in line.strip().strip("|").split("|")] for line in s.splitlines()
            if line.startswith("|") and not set(line) <= set("|- ")]


def test_doc_files_exist():
    for p in DOCS:
        assert p.is_file() and p.stat().st_size > 0


def test_documented_policy_ids_match_cedar_file():
    in_file = set(re.findall(r'@id\("([^"]+)"\)', POLICIES))
    rows = [r for r in table_rows(text()) if len(r) == 4 and r[3].startswith("`")]
    in_doc = {r[3].strip("`") for r in rows}
    assert in_file and in_doc == in_file


def test_documented_actions_exist_in_schema():
    declared = set(re.findall(r"^action (\w+)", SCHEMA, re.M))
    rows = [r for r in table_rows(text()) if len(r) == 2 and re.match(r"`(GET|POST|PUT) ", r[0])]
    documented = {a for r in rows for a in re.findall(r"`(\w+)`", r[1])}
    assert documented and documented <= declared
    required = set(re.findall(r'require\(who, "(\w+)"', (ROOT / "src/api/app.py").read_text(encoding="utf-8")))
    assert required and required <= documented


def test_documented_reason_codes_exist():
    src = (ROOT / "src/agent/consistency.py").read_text(encoding="utf-8")
    in_code = set(re.findall(r'fail\(\s*"(\w+)"', src))
    line = next(l for l in text().splitlines() if l.startswith("**Reason codes**"))
    in_doc = set(re.findall(r"`(\w+)`", line))
    assert in_code <= in_doc
    assert all(f'"{c}"' in src for c in in_doc)
    readme_line = next(l for l in text(AGENT_README).splitlines() if l.startswith("- Reason codes:"))
    assert in_code <= set(re.findall(r"`(\w+)`", readme_line))


@pytest.mark.parametrize("doc", DOCS)
def test_documented_paths_exist(doc):
    for tok in ticks(text(doc)):
        tok = tok.split(" ")[0].rstrip(".,;:)")
        tok = re.sub(r":\d+$", "", tok)
        if not tok.startswith(("src/", "tests/", "scripts/", "docs/", "research/")):
            continue
        if "<" in tok or "*" in tok:
            continue
        assert (ROOT / tok).exists(), tok
    for rel in re.findall(r"\]\(([^)#]+)\)", text(doc)):
        if not rel.startswith("http"):
            assert (doc.parent / rel).exists(), rel


@pytest.mark.parametrize("doc", DOCS)
def test_documented_make_targets_exist(doc):
    targets = set(re.findall(r"^([\w-]+):", (ROOT / "Makefile").read_text(encoding="utf-8"), re.M))
    used = re.findall(r"(?:^|`|&& )make ([\w-]+)", text(doc), re.M)
    assert set(used) <= targets, set(used) - targets
    if doc == DOC:
        assert used


def test_documented_env_vars_are_read_by_code():
    code = "".join(p.read_text(encoding="utf-8") for d in ("src", "scripts")
                   for p in (ROOT / d).rglob("*.py"))
    names = [c for r in table_rows(text()) for c in re.findall(r"`([A-Z][A-Z0-9_]+)`", r[0])]
    assert {"MOCK_LLM", "KK_DB_PATH", "KK_R1_THRESHOLD"} <= set(names)
    for n in names:
        assert n in code, n


@pytest.mark.parametrize("doc", DOCS)
def test_docs_have_no_forbidden_text(doc):
    s = text(doc)
    for bad in ("/home/", "/Users/", ".venv", "Claim ", "Co-Authored", "Claude"):
        assert bad not in s, bad


def test_video_sections_present():
    heads = [l.lower() for l in text().splitlines() if l.startswith("#")]
    assert any("beat 1" in h for h in heads) and any("beat 4" in h for h in heads)
    assert "python -m agent.demo" in text()


def test_injection_snippet_runs_and_writes_nothing(monkeypatch, capsys):
    monkeypatch.setenv("MOCK_LLM", "1")
    m = re.search(r"python - <<'EOF'\n(.*?)\nEOF", text(), re.S)
    exec(compile(m.group(1), "doc-snippet", "exec"), {})
    last = capsys.readouterr().out.strip().splitlines()[-1]
    assert last.startswith("question ") and last.endswith(" 0")


def test_beat_4_commands_match_the_sample_world(tmp_path, monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "1")
    monkeypatch.setenv("KK_DB_PATH", str(tmp_path / "kk.db"))
    load_world(Store(tmp_path / "kk.db"), sample_world())
    s = text()
    assert "X-Principal: br-1' localhost:3000/provenance/CERT-A-PET-1" in s
    assert "collector_id=kw-raju" in s
    c = TestClient(app)
    ok = c.get("/provenance/CERT-A-PET-1", headers={"X-Principal": "br-1"})
    assert ok.status_code == 200 and "kw-raju" not in ok.text
    mine = c.get("/certificates", params={"brand_id": "br-1"}, headers={"X-Principal": "br-1"})
    assert mine.status_code == 200 and "CERT-A-PET-1" in mine.text
    denied = c.get("/receipts", params={"collector_id": "kw-raju"}, headers={"X-Principal": "br-1"})
    assert denied.status_code == 403
    assert denied.json()["denied_by"] == "cedar" and denied.json()["action"] == "read_receipt"
