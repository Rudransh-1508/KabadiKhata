"""MOCK_LLM=1 model: drives the real Strands agent loop with a fixed, sensible plan, no API calls.

Used by tests, by teammates without a key, and as a rate-limit fallback. It follows the same rules the
system prompt gives the real model: perceive, check, and only price/write when the check passed.
"""
from __future__ import annotations

import json
import uuid
from typing import Any, AsyncGenerator, Optional

from strands.models.model import Model

from agent.tools import Session


def next_step(s: Session) -> Optional[str]:
    called = s.called()
    plan = ["read_photo"] + (["transcribe"] if s.request.audio_b64 else []) + ["phash_check", "check_consistency"]
    for step in plan:
        if step not in called:
            return step
    if s.consistency and s.consistency.ok:
        for step in ("quote_price", "create_receipt"):
            if step not in called:
                return step
    return None


def final_text(s: Session) -> str:
    if s.receipt:
        return f"रसीद बन गई: {s.receipt.receipt_id}"
    return (s.consistency.question_hi if s.consistency else None) or "कृपया फ़ोटो फिर से भेजिए।"


_USAGE = {"metadata": {"usage": {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0},
                       "metrics": {"latencyMs": 0}}}


class ScriptedModel(Model):
    def __init__(self, session: Session) -> None:
        self.session = session
        self.config: dict[str, Any] = {"model_id": "scripted-mock"}

    def update_config(self, **model_config: Any) -> None:
        self.config.update(model_config)

    def get_config(self) -> dict[str, Any]:
        return self.config

    async def structured_output(self, output_model, prompt, system_prompt=None, **kwargs):  # pragma: no cover
        raise NotImplementedError("ScriptedModel does not do structured output")
        yield  # makes this an async generator

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs) -> AsyncGenerator[dict, None]:
        step = next_step(self.session)
        yield {"messageStart": {"role": "assistant"}}
        if step:
            yield {"contentBlockStart": {"start": {"toolUse": {"name": step,
                                                               "toolUseId": f"tooluse_{uuid.uuid4().hex[:24]}"}}}}
            yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps({})}}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "tool_use"}}
        else:
            yield {"contentBlockStart": {"start": {}}}
            yield {"contentBlockDelta": {"delta": {"text": final_text(self.session)}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "end_turn"}}
        yield _USAGE
