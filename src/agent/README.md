# Agent (P2): Collection to Receipt or Question

Overview for judges and the video run sheet: [`docs/agent_and_policy.md`](../../docs/agent_and_policy.md). This file is the integration note for the other modules.

```bash
pip install -e ".[dev]"
MOCK_LLM=1 python -m pytest -q           # offline, no API key needed (or: make test)
cd src && MOCK_LLM=1 python -m agent.demo # prints the tool-call trace for a pass and a mismatch
```

## For P3 (API)
```python
from agent.agent import handle_collection
from common.models import CollectionRequest
result = handle_collection(CollectionRequest(**body), store)   # -> CollectionResult
return result.model_dump(mode="json")                           # {"status": "receipt"|"question", ...}
```
- `store` must satisfy `common.ports.ReceiptStore`: `append_receipt`, `receipts_for`, `find_receipt_by_phash`. `ledger.store.Store` (SQLite, `data/kk.db`, path from `KK_DB_PATH`) satisfies it and is what `src/api/app.py` passes. `agent.fakes.InMemoryReceiptStore` remains the offline test double for agent-only tests and the demo.
- **Hashing:** hash the **full normalized Receipt** (`Receipt(**fields, hash="").model_dump()`, defaults included), not the raw input dict. Otherwise `verify()` recomputes a different hash. See `agent/fakes.py` (the test `test_receipts_chain_per_collector` catches this). Timestamps must round-trip as UTC with microseconds.

## Perception (real, cached, fail closed)
`Perception` defaults to `perception.photo.read_photo` and `perception.voice.transcribe`. Both cache on disk and fail closed: an unreadable photo or an empty transcript becomes a Question, not a guess. Photo reading always uses Gemini and needs `GEMINI_API_KEY`, whatever `LLM_PROVIDER` is; voice uses Sarvam Saaras or Gemini per `VOICE_PROVIDER` (`voice_provider` in `src/common/config.py`). With `MOCK_LLM=1` a cached answer replays and, if nothing is cached, the deterministic stub in `agent/stub_tools.py` answers. Payloads that start with `fixture:` always use the stub (the bot's `/demo` relies on this). Each call is capped by `PERCEPTION_TIMEOUT_S` (default 10 s). `phash_check` and `quote_price` are still the stubs in `agent/stub_tools.py`: `Perception` defaults both to `stub_tools`.

To override any of them (this is also the test seam), pass your own functions; the signatures follow SCOPED_DOWN §3.3:
```python
from agent.tools import Perception
handle_collection(req, store, perception=Perception(read_photo=my_read_photo, transcribe=my_transcribe,
                                                    phash_check=my_phash_check))
```
`read_photo(photo_b64) -> PhotoRead`, `transcribe(wav_b64) -> Transcript`, `phash_check(photo_b64, store) -> PhashResult`. `Perception` also carries `quote_price(material, kg) -> PriceQuote`, a placeholder rate card until the real one lands.

## For P4 (bot and console)
- Send `taps={"material": ..., "kg": ...}` (and/or `audio_b64` as WAV, `text`). On `"question"`, show `question_hi` and resend with corrected taps.
- Stub fixtures for testing without real photos: `photo_b64 = b64("fixture:<kg>:<material>:<confidence>")`. Only with `MOCK_LLM=1` and nothing cached does a real photo get the default stub reading (12 kg PET).
- `trace` in the result is the tool-call table (or `format_trace()` for terminal output).
- A policy denial from the API is HTTP 403 `{"denied_by": "cedar", "action": ..., "reason": ...}`; render it as the red "Denied by Cedar policy" banner.

## How it decides
- The model picks tools; **code decides**. Tools take no arguments from the model, so it can't supply a weight or price.
- `create_receipt` is the only write. It re-runs `check_consistency` and asks `policy.authz.is_allowed(Agent::"kabadi-agent", "create_receipt", ..., {"consistency_ok": ...})` before writing. `policy/authz.py` evaluates the real Cedar policies in `src/policy/policies.cedar`; Cedar is the policy layer that holds even if the agent code changes.
- If the LLM errors or is rate-limited, the run finishes in code, and the trace says so (`llm_error`).
- Each agent model call has a request timeout, `AGENT_TIMEOUT_S` (default 6 s; `src/common/config.py`), passed to the Gemini and OpenAI clients. A timeout raises, so the run finishes in code and the `llm_error` note says it timed out. A turn cap (`MAX_AGENT_TURNS`, 10) stops a runaway loop; hitting it is logged and code completes the outcome. The 429 retry is capped at 2 attempts.
- **Known limitation:** the timeout is per model call, not per request. Several slow turns that each stay under the limit can still add up past the ~25 s budget; a hard request deadline would need an API-layer change.
- `MOCK_LLM=1` drives the real Strands loop with `ScriptedModel`, so there are no API calls.

## Consistency rules
- Claimed kg within ±10% of the scale reading passes; the edge is **inclusive** (12 kg vs 10.8 or 13.2 passes; 10.79 or 13.21 asks a Question).
- Reason codes: `scale_unreadable`, `low_confidence` (also NaN confidence), `weight_out_of_range`, `duplicate_photo`, `no_claim`, `claim_invalid` (claimed kg is 0, negative or not finite), `kg_mismatch`, `material_mismatch`, `material_unknown` (photo cannot tell the material and the Kabadiwala said none). Bots should show `question_hi` and not switch on reason strings.
- `claim_from_text` takes the first number followed by kg/kilo/किलो; a typed note is data. The Receipt weight is always the scale reading.

## Real-LLM smoke run
`python scripts/smoke_real_llm.py` runs the `pass`, `mismatch` and `injection` cases with `MOCK_LLM=1` and against the real provider, prints both traces and exits non-zero if the outcomes differ or the real trace has `llm_error`. Without a key it prints SKIP and exits 0. It reads `os.environ` only and does not load `.env`: export the key first (`set -a; . ./.env; set +a`). Run it once with a key before demo day; `make test` never runs it.
