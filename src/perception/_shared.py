"""Helpers shared by read_photo and transcribe: payload decoding, model-answer cleanup, Gemini client."""
from __future__ import annotations

import base64
import binascii
import functools
from typing import Optional


def decode_b64(payload: str) -> Optional[bytes]:
    """Strict base64 decode; None for empty or invalid input, so nothing junk reaches a model."""
    try:
        raw = base64.b64decode(payload or "", validate=True)
    except (binascii.Error, ValueError, TypeError):
        return None
    return raw or None


def to_float(v) -> Optional[float]:
    """A finite float, or None (booleans, text, NaN and infinity are not numbers here)."""
    if isinstance(v, bool):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f and f not in (float("inf"), float("-inf")) else None


def strip_fences(text: str) -> str:
    """Drop a ```json ... ``` wrapper a model sometimes puts around JSON."""
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
        t = t.rsplit("```", 1)[0]
    return t.strip()


@functools.lru_cache(maxsize=4)
def gemini_client(api_key: str, timeout_ms: int):
    """One Gemini client (and HTTP connection pool) per key and timeout, reused across calls."""
    from google import genai
    from google.genai import types

    return genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=timeout_ms))
