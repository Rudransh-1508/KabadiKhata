"""Runtime settings, read from the environment at call time so tests can flip them."""
from __future__ import annotations

import os


def mock_llm() -> bool:
    return os.getenv("MOCK_LLM", "0").strip().lower() in {"1", "true", "yes"}


def llm_provider() -> str:
    return os.getenv("LLM_PROVIDER", "gemini").strip().lower()


def gemini_model_id() -> str:
    return os.getenv("GEMINI_MODEL_ID", "gemini-flash-latest")


def openai_model_id() -> str:
    return os.getenv("OPENAI_MODEL_ID", "gpt-4o-mini")


def cache_dir() -> str:
    return os.getenv("KK_CACHE_DIR", ".cache")


def perception_timeout_s() -> float:
    """Per-call limit for read_photo / transcribe. A collection may run both, then the agent's own
    model turns, so each gets 10 s to keep the whole request under ~25 s (CLAUDE.md #2)."""
    try:
        v = float(os.getenv("PERCEPTION_TIMEOUT_S", "10"))
    except ValueError:
        return 10.0
    return v if 0 < v < float("inf") else 10.0


def agent_timeout_s() -> float:
    """Per-call limit for the agent's own model calls (tool-selection turns, about 1 to 2 s when healthy).
    6 s leaves room for two perception calls of PERCEPTION_TIMEOUT_S around one hung turn (CLAUDE.md #2)."""
    try:
        v = float(os.getenv("AGENT_TIMEOUT_S", "6"))
    except ValueError:
        return 6.0
    return v if 0 < v < float("inf") else 6.0


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


def _real_key(name: str) -> bool:
    key = os.getenv(name, "").strip()
    return bool(key) and not key.startswith("your-")


VISION_KEYS = {"gemini": "GEMINI_API_KEY", "openai": "OPENAI_API_KEY", "groq": "GROQ_API_KEY",
               "xai": "XAI_API_KEY"}


def groq_api_keys() -> list[str]:
    """All Groq keys to rotate through: GROQ_API_KEYS (comma-separated) then GROQ_API_KEY,
    placeholders and duplicates dropped, order kept."""
    raw = os.getenv("GROQ_API_KEYS", "").split(",") + [os.getenv("GROQ_API_KEY", "")]
    keys: list[str] = []
    for k in (k.strip() for k in raw):
        if k and not k.startswith("your-") and k not in keys:
            keys.append(k)
    return keys


def _has_key(provider: str) -> bool:
    return bool(groq_api_keys()) if provider == "groq" else _real_key(VISION_KEYS[provider])


def vision_providers() -> list[str]:
    """Who reads scale photos, in the order to try: the first that answers wins. VISION_PROVIDER
    (gemini | openai | groq | xai) picks the first; the others follow as fallbacks when their keys
    are set. Unset: Gemini, OpenAI, Groq, then xAI (Grok), whichever have real keys."""
    first = os.getenv("VISION_PROVIDER", "").strip().lower()
    order = [first] + [p for p in VISION_KEYS if p != first] if first in VISION_KEYS else list(VISION_KEYS)
    return [p for i, p in enumerate(order) if (i == 0 and first in VISION_KEYS) or _has_key(p)]


def openai_vision_model_id() -> str:
    return os.getenv("OPENAI_VISION_MODEL_ID", os.getenv("OPENAI_MODEL_ID", "gpt-4o-mini")).strip()


def xai_vision_model_id() -> str:
    return os.getenv("XAI_VISION_MODEL_ID", "grok-4.7").strip()


def groq_vision_model_id() -> str:
    return os.getenv("GROQ_VISION_MODEL_ID", "qwen/qwen3.8-27b").strip()
