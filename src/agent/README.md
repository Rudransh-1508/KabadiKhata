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

## For P1 (perception)
Perception is still a stub (`agent/stub_tools.py`) until P1's perception module lands. Pass your real functions in; the signatures follow SCOPED_DOWN §3.3:
```python
from agent.tools import Perception
handle_collection(req, store, perception=Perception(read_photo=my_read_photo, transcribe=my_transcribe,
                                                    phash_check=my_phash_check))
```
`read_photo(photo_b64) -> PhotoRead`, `transcribe(wav_b64) -> Transcript`, `phash_check(photo_b64, store) -> PhashResult`. `Perception` also carries `quote_price(material, kg) -> PriceQuote`, a placeholder rate card until the real one lands.

## For P4 (bot and console)
- Send `taps={"material": ..., "kg": ...}` (and/or `audio_b64` as WAV, `text`). On `"question"`, show `question_hi` and resend with corrected taps.
- Stub fixtures for testing without real photos: `photo_b64 = b64("fixture:<kg>:<material>:<confidence>")`. Any real photo gets the default reading (12 kg PET).
- `trace` in the result is the tool-call table (or `format_trace()` for terminal output).
- A policy denial from the API is HTTP 403 `{"denied_by": "cedar", "action": ..., "reason": ...}`; render it as the red "Denied by Cedar policy" banner.

## How it decides
- The model picks tools; **code decides**. Tools take no arguments from the model, so it can't supply a weight or price.
- `create_receipt` is the only write. It re-runs `check_consistency` and asks `policy.authz.is_allowed(Agent::"kabadi-agent", "create_receipt", ..., {"consistency_ok": ...})` before writing. `policy/authz.py` evaluates the real Cedar policies in `src/policy/policies.cedar`; Cedar is the policy layer that holds even if the agent code changes.
- If the LLM errors or is rate-limited, the run finishes in code, and the trace says so (`llm_error`).
- `MOCK_LLM=1` drives the real Strands loop with `ScriptedModel`, so there are no API calls.

## Consistency rules
- Claimed kg within ±10% of the scale reading passes; the edge is **inclusive** (12 kg vs 10.8 or 13.2 passes; 10.79 or 13.21 asks a Question).
- Reason codes: `scale_unreadable`, `low_confidence` (also NaN confidence), `weight_out_of_range`, `duplicate_photo`, `no_claim`, `claim_invalid` (claimed kg is 0, negative or not finite), `kg_mismatch`, `material_mismatch`, `material_unknown` (photo cannot tell the material and the Kabadiwala said none). Bots should show `question_hi` and not switch on reason strings.
- `claim_from_text` takes the first number followed by kg/kilo/किलो; a typed note is data. The Receipt weight is always the scale reading.

## Real-LLM smoke run
`python scripts/smoke_real_llm.py` runs the `pass`, `mismatch` and `injection` cases with `MOCK_LLM=1` and against the real provider, prints both traces and exits non-zero if the outcomes differ or the real trace has `llm_error`. Without a key it prints SKIP and exits 0. It reads `os.environ` only and does not load `.env`: export the key first (`set -a; . ./.env; set +a`). Run it once with a key before demo day; `make test` never runs it.
