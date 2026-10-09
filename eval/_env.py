"""Load the repo's .env for the eval scripts (make does this for the app; plain `uv run python` doesn't).

Values already in the environment win, so `MOCK_LLM=1 uv run python eval/...` still works.
"""
import os
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / ".env"


def load_env() -> None:
    if not ENV.exists():
        return
    for line in ENV.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        key = key.strip()
        if sep and key and not key.startswith("#"):
            os.environ.setdefault(key, value.split("#", 1)[0].strip())
