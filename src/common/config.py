"""Runtime settings, read from the environment at call time so tests can flip them."""
from __future__ import annotations

import os


def mock_llm() -> bool:
    return os.getenv("MOCK_LLM", "0").strip().lower() in {"1", "true", "yes"}


def llm_provider() -> str:
    return os.getenv("LLM_PROVIDER", "gemini").strip().lower()


def gemini_model_id() -> str:
    return os.getenv("GEMINI_MODEL_ID", "gemini-2.5-flash")


def openai_model_id() -> str:
    return os.getenv("OPENAI_MODEL_ID", "gpt-4o-mini")


def cache_dir() -> str:
    return os.getenv("KK_CACHE_DIR", ".cache")


def explain_timeout_s() -> float:
    try:
        v = float(os.getenv("LLM_EXPLAIN_TIMEOUT_S", "20"))
    except ValueError:
        return 20.0
    return v if 0 < v < float("inf") else 20.0


def voice_provider() -> str:
    """Who transcribes voice notes: "sarvam" (Saaras speech-to-text) or "gemini".
    Unset: Sarvam when a real SARVAM_API_KEY is configured, else Gemini."""
    chosen = os.getenv("VOICE_PROVIDER", "").strip().lower()
    if chosen:
        return chosen
    key = os.getenv("SARVAM_API_KEY", "").strip()
    return "sarvam" if key and not key.startswith("your-") else "gemini"


def sarvam_stt_model_id() -> str:
    return os.getenv("SARVAM_STT_MODEL_ID", "saaras:v4")
