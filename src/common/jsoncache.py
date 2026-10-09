"""Small JSON-file cache shared by the LLM callers (radar explainer, read_photo, transcribe).

Writes are atomic (temp file + os.replace), so a crash never leaves a half-written entry, and
the temp file is removed if writing fails. Every error is logged and swallowed: a cache that
can't be read or written just means the model is asked again.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
from typing import Optional

log = logging.getLogger(__name__)


def read_json(path: str) -> Optional[dict]:
    try:
        with open(path, encoding="utf-8") as fh:
            obj = json.load(fh)
    except (OSError, ValueError):
        return None
    return obj if isinstance(obj, dict) else None


def write_json(path: str, obj: dict) -> None:
    tmp = None
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False)
        os.replace(tmp, path)
        tmp = None
    except (OSError, TypeError, ValueError) as exc:
        log.warning("cache write failed for %s: %s", os.path.basename(path), type(exc).__name__)
    finally:
        if tmp is not None:
            try:
                os.remove(tmp)
            except OSError:
                pass


def drop(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass
