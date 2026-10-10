# Spec p2-7-agent-timeout-and-docs: agent model timeout, and docs for real perception

## Goal
- **CLAUDE.md fix #2** (one collection request under ~25 s end to end) and **video beat 1, Receipt with a refusal**. P1's perception calls are now capped at `PERCEPTION_TIMEOUT_S` (10 s). The agent's own model calls are not, so a hung call can hold a Collection open indefinitely. `handle_collection` only finishes in code when the model call raises. This spec makes a hang raise.
- **Docs truth:** `src/agent/README.md` and `docs/agent_and_policy.md` still say perception is a stub. Judges and P4 read these files; they must describe the real behaviour.

## Scope
- `src/common/config.py`: add `agent_timeout_s()` (additive; no existing function changes).
- `src/agent/agent.py`: `build_model()` passes the timeout to the provider clients. `handle_collection` gets a turn cap and a clearer trace note (see Behaviour).
- `.env.example`: one documented line.
- `src/agent/README.md`, `docs/agent_and_policy.md`: perception wording, env var table row.
- `tests/test_agent_timeout.py` (new).

## Out of scope
- `src/perception/*`, `src/radar/*`, `src/api/*`, `src/ledger/*`, `bot/*`, `console/*`, `eval/*`, and every existing test file. Nothing else under `src/agent/` changes.
- A hard wall-clock deadline for the whole request (see Edge cases, "Not bounded").
- Running against a real provider (a human does that with `scripts/smoke_real_llm.py`).
- Any new package.

## Dependencies on teammates
None blocking.
- The settings are read from `os.environ` at call time, like the other `config` functions. No P1, P3 or P4 code is imported or changed.
- Tests build models with a dummy key via `monkeypatch.setenv` and never make a request. `GeminiModel(...)` and `OpenAIModel(...)` only store `client_args` in `__init__` (checked in the installed strands: `self.client_args = client_args or {}`); the client is created per request. So no network is touched.
- Perception and the API call `handle_collection` unchanged; its signature and return shape do not change.

## Interfaces

### `src/common/config.py`
```python
def agent_timeout_s() -> float:
    """Per-call limit for the agent's own model calls. Same parsing as perception_timeout_s()."""
```
Reads `AGENT_TIMEOUT_S`; default **6.0**. A missing, non-numeric, zero, negative, NaN or infinite value gives 6.0 (copy the guard `0 < v < float("inf")`; NaN fails it).

### `src/agent/agent.py`
`build_model(session)` signature unchanged. Verified against the installed libraries (read the source, not guessed):
- **Gemini.** `strands.models.gemini.GeminiModel.__init__` stores `client_args` and later calls `genai.Client(**client_args)`. `google.genai.types.HttpOptions.timeout` is `Optional[int]`, **milliseconds**. Pass
  `client_args={"api_key": ..., "http_options": {"timeout": int(config.agent_timeout_s() * 1000)}}`. Use `max(1, ...)` so a tiny value never becomes 0 (0 would read as "no timeout" or be rejected).
- **OpenAI.** `OpenAIModel` stores `client_args` and builds `openai.AsyncOpenAI(**client_args)`. Pass `client_args={"api_key": ..., "timeout": config.agent_timeout_s(), "max_retries": 0}` (timeout in seconds; the SDK's own retry default would triple the wait). At implementation time, confirm both keys against the installed `openai` package; if it is not installed the test skips.
- **Gemini retries.** google-genai retries only when `http_options.retry_options` is set; we do not set it.
- **Strands retries (decided, verified in the installed strands).** `strands.event_loop._retry.ModelRetryStrategy.__init__(*, max_attempts=6, initial_delay=4, max_delay=240)` (all ints) retries only `ModelThrottledException` (e.g. HTTP 429), so a timeout raises at once but a 429 would back off for minutes by default. `Agent.__init__` accepts `retry_strategy` (must be a `ModelRetryStrategy` instance). Pass `retry_strategy=ModelRetryStrategy(max_attempts=2, initial_delay=1, max_delay=2)`. The import is of a private module, so wrap it: `try: from strands.event_loop._retry import ModelRetryStrategy` / `except ImportError: ModelRetryStrategy = None`, and omit the kwarg when it is `None` (a strands upgrade must not break the demo). Mention in the README limitations that the 429 retry is capped.
- **Turn cap (decided, verified in the installed strands).** `Agent.__call__` accepts `limits` (`strands.types.agent.Limits`, key `turns`, positive int; a bad key or value raises `TypeError`). `_check_limits` stops at the top of a cycle when `len(invocation.cycles) >= turns`, i.e. a turn is one event-loop cycle (one model call), counted per invocation. The stop yields `stop_reason="limit_turns"` and raises nothing. Pass `limits={"turns": MAX_AGENT_TURNS}` with module constant `MAX_AGENT_TURNS = 10`. The happy path is at most 7 model calls (one per tool step plus the final sentence; parallel tool calls make it fewer). When the result's `stop_reason` is `"limit_turns"`, `handle_collection` writes `log.warning(...)` only; it adds no trace entry and does not mark `llm_error`.

`handle_collection(req, store, perception=None, print_trace=False)` is unchanged. The `llm_error` trace entry keeps its shape `{"step", "tool": "llm_error", "ms", "result": {"error": <ExceptionName>, "note": "finished by code"}}`. Additive: when the exception is a timeout (see below) the note is `f"model call timed out (limit {config.agent_timeout_s():g}s); finished by code"`. The note and trace never contain the exception message (provider errors can echo URLs or key fragments); the class name only, as today. `CollectionResult.trace` is returned by the API, so this keeps it clean.

Timeout classification: a small private helper `_is_timeout(exc) -> bool`, true for `TimeoutError`, `asyncio.TimeoutError` (a distinct class on Python 3.10, which is our target), `httpx.TimeoutException`, or any exception in its `__cause__`/`__context__` chain with a class name containing `Timeout` (covers `openai.APITimeoutError` and google-genai wrappers without importing them). Walk the chain with a visited set and a depth cap of 8 (chains can be cyclic). It only changes the note text; the outcome path is identical for every exception.

### `.env.example` (one line, in the existing LLM block)
```
# AGENT_TIMEOUT_S=6           # per agent model call, seconds (read_photo/transcribe use PERCEPTION_TIMEOUT_S)
```
Comment only, no value that is a secret.

## Behaviour and rules
1. **Why 6 s.** Budget ~25 s. Perception may use two calls of up to 10 s in the worst case, but typical cached or fast reads take 2 to 4 s each. Agent turns are short tool-selection calls (about 1 to 2 s). 6 s is well above a healthy turn, so it does not cause false timeouts, and the first hung model call costs at most 6 s. After it, code finishes the Collection: perception that did not run yet runs once in code (`Session` caches each result, and a failed perception returns the fail-closed reading rather than raising, so nothing is retried). Worst case with one hung call: 6 s + 2 x 10 s perception = 26 s, roughly the budget. The default is a compromise, not a guarantee: it does not bound several slow turns (see Edge cases, "Not bounded"). A user who runs slow perception can lower this value.
2. A timed-out or failed model call raises out of `Agent(...)(...)`. The existing `except Exception` records `llm_error` and then code decides: `do_check_consistency`, and `guarded_create_receipt` only if the check passed and Cedar allows. Outcome is a Receipt (pass) or a Question (fail), never a hang and never a Receipt for a failing check.
3. Rule 2 of CLAUDE.md is untouched: the model still has exactly one write tool; code and Cedar still guard it.
4. `MOCK_LLM=1` ignores the timeout (the `ScriptedModel` branch returns before any client args are built).
5. A turn-cap stop is not an error: the run is not marked `llm_error`; code completes the outcome exactly as when the model skips a step (existing `completed by code` note).

## Edge cases
- `AGENT_TIMEOUT_S` unset, `abc`, `0`, `-3`, `nan`, `inf`: default 6.0.
- `AGENT_TIMEOUT_S=0.4` gives Gemini `timeout` 400 ms; `0.0004` gives `max(1, 0)` = 1 ms (never 0).
- Unknown `LLM_PROVIDER` still raises `ValueError` from `build_model`; that happens inside the `try` in `handle_collection`, so it is also finished in code (existing behaviour, test must keep passing).
- Missing `GEMINI_API_KEY` still raises `KeyError` inside the `try`: finished in code, `llm_error` trace.
- **Not bounded:** the timeout is per model call, not per request. Several slow-but-not-timed-out turns can still add up (for example 7 turns of 5 s). The turn cap and the per-call limit bound the typical case; a true request deadline would need an API-layer change (P3) and is out of scope. State this under README known limitations.
- Throttling (429) with the capped retry strategy adds at most about 1 s per call (one retry, 1 s delay); if the private import fails and the kwarg is omitted, strands' default backoff applies and can add minutes. See Interfaces.
- Gemini's `http_options.timeout` bounds the HTTP request; whether it bounds the whole of a streamed response or each read is a google-genai detail we did not verify. Do not claim a hard per-call wall-clock limit in the docs; say "request timeout".

## Test plan (`tests/test_agent_timeout.py`, all offline, no network)
Fixtures: autouse `monkeypatch.setenv("GEMINI_API_KEY", "test-key")` and `OPENAI_API_KEY`; tests that build a real provider model first `monkeypatch.setenv("MOCK_LLM", "0")`.
- `test_agent_timeout_default_and_override`: unset gives 6.0; `AGENT_TIMEOUT_S=3.5` gives 3.5.
- `test_agent_timeout_rejects_bad_values` (parametrized `abc`, `0`, `-1`, `nan`, `inf`, empty): all give 6.0.
- `test_build_model_gemini_passes_timeout_ms`: `LLM_PROVIDER=gemini`, `AGENT_TIMEOUT_S=4`; `model.client_args["http_options"]["timeout"] == 4000`, api key present, `params` temperature still 0, `model_id` explicit.
- `test_build_model_gemini_timeout_never_zero`: `AGENT_TIMEOUT_S=0.0004` gives timeout >= 1.
- `test_build_model_gemini_client_accepts_options`: `google.genai.types.HttpOptions(**model.client_args["http_options"])` validates (guards the parameter name against the installed library). `pytest.importorskip("google.genai")`.
- `test_build_model_openai_passes_timeout_s`: `LLM_PROVIDER=openai`; `client_args["timeout"] == 4.0`, `client_args["max_retries"] == 0`. `importorskip("openai")`.
- `test_build_model_mock_ignores_timeout`: `MOCK_LLM=1` returns a `ScriptedModel`.
- `test_unknown_provider_still_raises_value_error`.
- `test_build_model_gemini_and_openai_unchanged_otherwise`: keys and `model_id` explicit, `params == {"temperature": 0}` for both providers (design rule 4, "always pass the model explicitly").
- `test_retry_strategy_is_capped`: monkeypatch `agent.agent.Agent` with a recorder; assert the `retry_strategy` kwarg is a `ModelRetryStrategy` with `_max_attempts == 2` (skip if the import is unavailable).
- `test_is_timeout_handles_cyclic_chain`: two exceptions whose `__cause__` point at each other do not loop; a `RuntimeError` caused by `TimeoutError` is classified as a timeout.
- `test_timeout_note_has_no_exception_message`: raise `TimeoutError("secret-token-123")`; the serialised trace does not contain `secret-token-123`.
- `test_timeout_exception_finishes_in_code_receipt`: monkeypatch `agent.agent.build_model` to return a `strands.models.Model` subclass whose `stream` raises `TimeoutError("hung")` (if strands wraps the error so it does not propagate, patch `agent.agent.Agent` with a stand-in whose call raises instead; the test must exercise the real `except` in `handle_collection`); passing Collection (`fixture:12:PET:0.92`, taps 12 PET) gives `status == "receipt"`, one Receipt in the `InMemoryReceiptStore`, trace has an `llm_error` entry with `result["error"] == "TimeoutError"` and a note containing `timed out`, plus the `create_receipt` entry noting completion by code.
- `test_timeout_exception_finishes_in_code_question`: same hang, mismatching claim (kg 20 vs scale 12): `status == "question"`, `reasons == ["kg_mismatch"]`, store empty, `llm_error` in trace, no `create_receipt` in trace.
- `test_httpx_timeout_is_classified_as_timeout`: model raises `httpx.ReadTimeout("x")`; note contains `timed out`.
- `test_non_timeout_error_keeps_generic_note`: model raises `RuntimeError`; note is `finished by code`, outcome still correct.
- `test_turn_cap_is_passed_to_agent`: monkeypatch `agent.agent.Agent` with a recorder; assert `limits == {"turns": MAX_AGENT_TURNS}` reaches the call and the outcome is still decided by code.
- `test_scripted_happy_path_fits_turn_cap`: with `MOCK_LLM=1` the normal passing Collection reaches a Receipt with no `llm_error` and a `ScriptedModel` call count `<= MAX_AGENT_TURNS`, so the cap cannot truncate the demo.
- Existing suite unchanged and green: `MOCK_LLM=1 python -m pytest -q` (or `make test`), including `tests/test_docs.py`, `tests/test_agent_hardening.py`, `tests/test_agent_stub.py`.

## Docs changes (exact)
`src/agent/README.md`:
- Retitle "For P1 (perception)" to describe real behaviour: `Perception` defaults to `perception.photo.read_photo` and `perception.voice.transcribe` (cached on disk, fail closed: an unreadable photo or empty transcript becomes a Question, not a guess). Photo reading always uses Gemini and needs `GEMINI_API_KEY`, whatever `LLM_PROVIDER` is; voice uses Sarvam Saaras or Gemini per `VOICE_PROVIDER` (see `src/common/config.py` `voice_provider`; do not write "Gemini" alone for voice). With `MOCK_LLM=1` a cached answer replays and, if nothing is cached, the deterministic stub in `agent/stub_tools.py` answers. Payloads that start with `fixture:` always use the stub (the bot's `/demo` relies on this). Each call is capped by `PERCEPTION_TIMEOUT_S` (default 10 s). `phash_check` and `quote_price` are still the stubs in `agent/stub_tools.py`: `Perception` in `src/agent/tools.py` defaults both to `stub_tools` today (verified), so keep that sentence and drop the "until P3/P4" wording (no teammate names in the docs).
- The `Perception(...)` override example stays (it is still the test seam), reworded as "to override".
- "How it decides": add a line on `AGENT_TIMEOUT_S` and the turn cap, and the known limitation (per-call, not per-request).
- Keep "Stub fixtures" bullet; reword "Any real photo gets the default reading" to say this applies only to `MOCK_LLM=1` with nothing cached.

`docs/agent_and_policy.md`:
- Line 11: replace "Perception ... is still a stub; see section 7" with the real-perception sentence above (Gemini, cached, fail closed; `fixture:` payloads use the stub).
- Section 7 (a): replace "Perception is a stub" with "Perception is real but needs a key": real reads need a provider key; without one (or with `MOCK_LLM=1` and nothing cached) the stub answers; `phash_check` and `quote_price` as accurate. Keep the `Perception` seam sentence.
- Lines ~105 and ~159: remove "until P1's `data/synth/world.json` lands" phrasing. Verified: `src/ledger/seed.py` loads `data/synth/world.json` if it exists, else `sample_world()`; `data/synth/` does not exist in this tree, so today `make seed` loads the built-in sample world. Say exactly that ("loads `data/synth/world.json` when present, otherwise the built-in sample world; the ids below are the sample world's"), keep the `curl .../actors` hint, and do not name `data/synth/world.json` in backticks as an existing file (`test_documented_paths_exist` only checks `src/ tests/ scripts/ docs/ research/` prefixes, but stay truthful anyway). Do not edit the Makefile comment or `seed.py` (not ours).
- Env var table (near line 116): add row `| `AGENT_TIMEOUT_S` | per-call limit for the agent's own model calls (default 6; perception uses `PERCEPTION_TIMEOUT_S`, default 10) |`. Verified missing today, so also add `PERCEPTION_TIMEOUT_S` and `VOICE_PROVIDER` (`sarvam` or `gemini`; default Sarvam when a real `SARVAM_API_KEY` is set, else Gemini) rows; all three names appear in `src/` code. `tests/test_docs.py` requires every listed name to appear in `src/` or `scripts/` code: `AGENT_TIMEOUT_S` will, via `config.py`.
- No absolute paths, no `.venv`, no "Claim " in either file (checked by `test_docs_have_no_forbidden_text`). Every backticked `src/`, `tests/`, `docs/` path must exist.

## Acceptance criteria
1. `AGENT_TIMEOUT_S` exists in `config.py`, `.env.example` (commented) and the env var table.
2. `build_model` for Gemini sets `http_options.timeout` in milliseconds; for OpenAI sets `timeout` in seconds and `max_retries=0`; both verified by named tests above.
3. A model that raises a timeout makes `handle_collection` return the right outcome with an `llm_error` trace entry that says it timed out; never a Receipt for a failing check.
4. No other source file changed; no existing test edited; `MOCK_LLM=1 python -m pytest -q` is fully green, including `tests/test_docs.py`.
5. Neither doc says perception is a stub or mentions waiting for P1; both describe real, cached, fail-closed perception, the `fixture:` rule and the `MOCK_LLM=1` replay rule.
6. The README states the per-call (not per-request) limitation.
7. No secrets, absolute paths or usernames in any changed file.

## Deviations
- The two OpenAI tests skip here because `openai` is not installed in the test environment (the spec allows this); the OpenAI `timeout` and `max_retries` keys come from the spec and were not re-checked against an installed `openai`.
- The Receipt and Question hang tests use a stand-in `Agent` that raises (the spec's fallback), so they exercise the real `except` in `handle_collection`. One extra test, `test_real_model_timeout_propagates_through_strands`, confirms a real `strands.models.Model` whose `stream` raises `TimeoutError` also reaches that `except`.
- `docs/agent_and_policy.md` section 7 gains a limitation (a2) for the per-call timeout, in addition to the README note.
- The `log.warning` on a failed run now logs the exception class name only, not its message, in line with the no-message rule for the trace.
