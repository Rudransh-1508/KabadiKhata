# Spec review: p2-7-agent-timeout-and-docs

Checked against CLAUDE.md, CONTEXT.md, `src/agent/agent.py`, `src/agent/tools.py`, `src/perception/photo.py` and `voice.py`, `src/common/config.py`, the installed strands source (`event_loop/_retry.py`, `event_loop/event_loop.py`, `agent/agent.py`, `models/gemini.py`), and how `src/api/app.py` calls `handle_collection`. No contract in `src/common/models.py` changes; the API call site is unaffected.

## Findings, ranked

1. **High: docs would misstate voice and photo providers.** The spec said `transcribe` is "Gemini". It is Sarvam Saaras or Gemini, chosen by `VOICE_PROVIDER` (`config.voice_provider`). Photo reading always uses Gemini and needs `GEMINI_API_KEY` regardless of `LLM_PROVIDER`. Writing "Gemini" for both would put a wrong claim in the files judges read.
   Decision: **applied.** Docs wording corrected; `VOICE_PROVIDER` and `PERCEPTION_TIMEOUT_S` env rows added (both were missing from the table).

2. **High: the 25 s reasoning overclaimed.** "A hang costs at most 6 s" ignores that code then runs any unrun perception, and that several slow turns add up. Verified that `Session` caches results and a failed perception returns the fail-closed reading (no repeat call), so the real worst case for one hung call is 6 + 2x10 = 26 s.
   Decision: **applied.** Rule 1 rewritten as a compromise, not a guarantee; the Gemini "request timeout" semantics are flagged as unverified so the docs do not promise a hard wall-clock limit.

3. **Medium: retry strategy was conditional on an unchecked signature.** Verified: `ModelRetryStrategy(*, max_attempts, initial_delay, max_delay)` takes ints and retries only throttling; `Agent` accepts `retry_strategy`. The import is from a private module.
   Decision: **applied.** Made it a firm decision (2 attempts, 1 s, max 2 s), with a guarded import so a strands upgrade cannot break the demo; a test added.

4. **Medium: turn cap was conditional too.** Verified: `limits={"turns": n}` is accepted by `Agent.__call__`; a turn is one cycle (one model call), checked as `cycles >= n` per invocation; it returns `limit_turns` and raises nothing.
   Decision: **applied.** Firm decision with `MAX_AGENT_TURNS = 10`, a `log.warning` on a cap stop, and a test that the scripted happy path fits under the cap. A new trace entry for a cap stop was **rejected**: it adds a trace shape the console and API consumers do not know, and the video does not need it.

5. **Medium: `_is_timeout` fragility.** `asyncio.TimeoutError` is a different class from `TimeoutError` on Python 3.10; exception chains can be cyclic; importing `openai` just to classify adds a hidden dependency.
   Decision: **applied.** Dropped the `openai` import (the class-name check covers it), added a visited set and depth cap, and a test.

6. **Medium: trace could leak provider error text.** Provider errors can echo URLs or key fragments, and the trace is returned by the API.
   Decision: **applied.** Spec states the note and trace carry the class name only, never the message; a test checks it.

7. **Low: test seam for the hung model was underspecified.** A fake model's `stream` error may be wrapped by strands.
   Decision: **applied.** Spec requires a `strands.models.Model` subclass and a fallback stand-in for `Agent` that still exercises the real `except` path.

8. **Low: docs line about the seed world.** Verified `data/synth/` does not exist and `src/ledger/seed.py` falls back to `sample_world()`, so docs must say the sample world is what loads today.
   Decision: **applied.** Spec made explicit. Editing the Makefile comment or `seed.py` wording (which names P1) is **rejected**: teammates' files, out of the P2 boundary.

9. **Low: `phash_check` / `quote_price` sentence was conditional.** Verified `Perception` defaults both to `stub_tools`.
   Decision: **applied.** Made firm; "until P3/P4 land" removed so docs name no teammates.

10. **Low: provider-parameter regression.** Nothing guarded temperature 0 and explicit model ids after the `client_args` change.
    Decision: **applied.** Added a test.

## Checked, no change needed
- Vocabulary: spec uses Collection, Receipt, Question, Kabadiwala; no "Claim".
- Design rule 2 (one write tool, Cedar) untouched; the timeout path still ends in `guarded_create_receipt` only after a passing check.
- Scope: stays inside the P2 boundary; no new package; `MOCK_LLM=1` path unaffected.
- A hard whole-request deadline: **rejected** as out of scope (needs an API-layer change by another owner); the spec already states it as a known limitation.
- Gemini `client_args["http_options"]` as a dict: matches how `perception/_shared.py` builds `HttpOptions(timeout=ms)` and strands' `genai.Client(**client_args)`.
