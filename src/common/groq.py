"""Groq (OpenAI-compatible API) as the Strands model for the agent and the radar explainer.

    GroqModel(model_id=..., timeout_s=...)        # LLM_PROVIDER=groq

Each Groq key has its own small per-minute token limit, and one Collection takes several agent
turns, so a single key can run out mid-Collection. The HTTP transport below sends each request
with the current key (from GROQ_API_KEYS, then GROQ_API_KEY) and, on 429 (rate limit) or a 5xx,
resends the same request with the next key. The working key stays current, so load moves through
the keys in order. A refusal or a bad answer is never retried: only 429 and 5xx are.
Photo reading has its own Groq key rotation in `perception.photo`.
"""
from __future__ import annotations

import functools
import logging
import threading
from typing import Any

import httpx

from common import config

log = logging.getLogger(__name__)

BASE_URL = "https://api.groq.com/openai/v1"
RETRY_STATUS = {429, 500, 502, 503, 504}
# Groq's Qwen thinks by default. Off: the answers we need are a tool choice or a short text, and
# hidden reasoning would cost tokens from the small per-minute budget and time from the ~25 s one.
NO_REASONING = {"reasoning_effort": "none"}


class KeyRing:
    """The configured keys and which one is current, shared by every model in the process."""

    def __init__(self, keys: tuple[str, ...]):
        if not keys:
            raise KeyError("GROQ_API_KEYS")  # same failure as a missing env var
        self.keys = keys
        self._i = 0
        self._lock = threading.Lock()

    def current(self) -> str:
        with self._lock:
            return self.keys[self._i]

    def failed(self, key: str, status: int) -> None:
        """Move past `key`, unless another request already did. Logs key numbers, never keys."""
        with self._lock:
            if self.keys[self._i] == key:
                self._i = (self._i + 1) % len(self.keys)
                log.warning("Groq key #%d returned %d; switching to key #%d",
                            self.keys.index(key) + 1, status, self._i + 1)


@functools.lru_cache(maxsize=4)
def _ring(keys: tuple[str, ...]) -> KeyRing:
    return KeyRing(keys)


def key_ring() -> KeyRing:
    return _ring(tuple(config.groq_api_keys()))


class FallbackTransport(httpx.AsyncBaseTransport):
    def __init__(self, ring: KeyRing, inner: httpx.AsyncBaseTransport | None = None):
        self.ring = ring
        self.inner = inner or httpx.AsyncHTTPTransport()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        await request.aread()  # the body is sent again on a retry
        for attempt in range(len(self.ring.keys)):
            key = self.ring.current()
            request.headers["Authorization"] = f"Bearer {key}"
            response = await self.inner.handle_async_request(request)
            if response.status_code not in RETRY_STATUS or attempt == len(self.ring.keys) - 1:
                return response
            await response.aclose()
            self.ring.failed(key, response.status_code)
        raise AssertionError("unreachable")

    async def aclose(self) -> None:
        await self.inner.aclose()


@functools.lru_cache(maxsize=1)
def _model_class():
    from strands.models.openai import OpenAIModel

    class GroqModel(OpenAIModel):
        """Strands' OpenAI model pointed at Groq, with a fresh key-fallback HTTP client per request
        (Strands opens and closes an OpenAI client per request, and that closes the HTTP client too)."""

        def __init__(self, *, timeout_s: float, **model_config: Any):
            self._ring = key_ring()
            self._timeout_s = timeout_s
            # api_key is a placeholder: the transport sets the real key on every request
            super().__init__(client_args={"base_url": BASE_URL, "api_key": "from-key-ring",
                                          "timeout": timeout_s, "max_retries": 0}, **model_config)

        def _resolve_client_args(self) -> dict[str, Any]:
            http = httpx.AsyncClient(transport=FallbackTransport(self._ring), timeout=self._timeout_s)
            return {**self.client_args, "http_client": http}

    return GroqModel


def GroqModel(*, model_id: str, timeout_s: float, params: dict | None = None):
    """A Strands model for Groq: temperature 0 and no reasoning unless `params` says otherwise."""
    return _model_class()(timeout_s=timeout_s, model_id=model_id,
                          params={"temperature": 0, **NO_REASONING, **(params or {})})
