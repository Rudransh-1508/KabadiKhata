# Agent (P2): stub, ready to integrate

```bash
pip install -e ".[dev]"
MOCK_LLM=1 python -m pytest              # 13 tests, no API key needed
cd src && MOCK_LLM=1 python -m agent.demo # prints the tool-call trace for a pass and a mismatch
```

## For P3 (API)
```python
from agent.agent import handle_collection
from common.models import CollectionRequest
result = handle_collection(CollectionRequest(**body), store)   # -> CollectionResult
return result.model_dump(mode="json")                           # {"status": "receipt"|"question", ...}
```
- `store` must satisfy `common.ports.ReceiptStore`: `append_receipt`, `receipts_for`, `find_receipt_by_phash`. `agent.fakes.InMemoryReceiptStore` is the reference until `ledger/store.py` lands.
- **Hashing:** hash the **full normalized Receipt** (`Receipt(**fields, hash="").model_dump()`, defaults included), not the raw input dict. Otherwise `verify()` recomputes a different hash. See `agent/fakes.py` (the test `test_receipts_chain_per_collector` catches this). Timestamps must round-trip as UTC with microseconds.

## For P1 (perception)
Pass your real functions in; the signatures follow SCOPED_DOWN §3.3:
```python
from agent.tools import Perception
handle_collection(req, store, perception=Perception(read_photo=my_read_photo, transcribe=my_transcribe,
                                                    phash_check=my_phash_check))
```
`read_photo(photo_b64) -> PhotoRead`, `transcribe(wav_b64) -> Transcript`, `phash_check(photo_b64, store) -> PhashResult`.

## For P4 (bot and console)
- Send `taps={"material": ..., "kg": ...}` (and/or `audio_b64` as WAV, `text`). On `"question"`, show `question_hi` and resend with corrected taps.
- Stub fixtures for testing without real photos: `photo_b64 = b64("fixture:<kg>:<material>:<confidence>")`. Any real photo gets the default reading (12 kg PET).
- `trace` in the result is the tool-call table (or `format_trace()` for terminal output).

## How it decides
- The model picks tools; **code decides**. Tools take no arguments from the model, so it can't supply a weight or price.
- `create_receipt` is the only write. It re-runs `check_consistency` and asks `policy.authz.is_allowed(Agent::"kabadi-agent", "create_receipt", ..., {"consistency_ok": ...})` before writing.
- If the LLM errors or is rate-limited, the run finishes in code, and the trace says so (`llm_error`).
- `MOCK_LLM=1` drives the real Strands loop with `ScriptedModel`, so there are no API calls.
- `policy/authz.py` is a stub with the final signature. Cedar replaces its internals on Saturday.
