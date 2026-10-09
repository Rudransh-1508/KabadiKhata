# Spec review: p2-4-agent-hardening

Checked against CLAUDE.md, CONTEXT.md, `src/common/models.py`, `src/agent/*`, `src/api/app.py`, the installed Strands Gemini/OpenAI formatters and the brief. Bash was unavailable, so formatter behaviour was read from the installed source, not executed.

## Findings (most severe first)

1. **Gemini formatting assertion would fail as written (medium).** `_format_request` returns `config` as `to_json_dict()` output, so keys are camelCase (`functionDeclarations`, `parametersJsonSchema`, `systemInstruction`), not `function_declarations`. It is also a private method.
   Decision: **applied.** Assertions use camelCase (snake_case accepted), the test skips with a reason if the private method or its signature is missing, and it also checks `model` and the system instruction.

2. **Goal overclaimed (medium).** "Rules out a schema surprise on demo day" is false: offline formatting cannot prove the provider server accepts the request.
   Decision: **applied.** Goal reworded; the human smoke run before demo day is stated as required.

3. **`photo.confidence` NaN passes the confidence check (medium, policy hole).** `nan < 0.60` is False, so a NaN reading skips `low_confidence` and can write a Receipt, the same class of hole as the NaN claim the spec already fixes.
   Decision: **applied.** `low_confidence` now triggers on `not confidence >= MIN_CONFIDENCE`; test and acceptance line added.

4. **Smoke script gaps (medium).** Unsupported `LLM_PROVIDER` would traceback; `.env` is not loaded, so a human with a key only in `.env` would see a silent SKIP; exception text could echo the key; exit-code precedence (1 vs 2) ambiguous; imports of `agent` at module level would break the "SKIP imports nothing from strands" claim and the importlib tests; `main` must call `run_case` through the module global for the monkeypatch test.
   Decision: **applied** for each (SKIP on unsupported provider, document env-only, print exception type not message, exit 2 wins, lazy imports, global lookup, `finally` restore, extra test).

5. **No real-LLM check of the injection beat (low-medium).** The video clip is the injection refusal, but the smoke only had pass and mismatch.
   Decision: **applied.** Third `injection` case. Cost is one request; code still decides the outcome.

6. **Vocabulary test mechanism untestable/too noisy (medium).** "Greps string literals" would flag the Cedar key `"collector"` in `tools.py`, the `ledger/chain.py` path in `fakes.py`, and `claim()`.
   Decision: **applied.** AST-based, prose-only (docstrings and strings with a space), explicit regex, explicit allowances. Lowercase "collection" is left to manual replacement.

7. **Untrusted text persisted verbatim (low, not ours to fix).** A passing Collection with an injection transcript stores it in `Receipt.voice_text`/`evidence`; the console must escape it.
   Decision: **applied as a flagged dependency note only**; no code change (console is not ours).

8. **Edge-case wording and gaps (low).** "taps also 12" ambiguous; taps with material only hide a voice kg (existing precedence, ends in `no_claim`) was undocumented; fixture text with a colon is truncated by the stub; claim that no existing test relies on `unknown` passing was unverified.
   Decision: **applied.** Rows, a test and a note added. Grep confirmed no test or seed path depends on `unknown` passing.

9. **`material_unknown` follow-up depends on the bot offering the material grid (low).**
   Decision: **applied** as a non-blocking P4 note. Behaviour change itself kept: writing Receipts with material `unknown` at ₹0/kg would corrupt Verified inflow.

10. **Suggested `make smoke` target (low).**
    Decision: **rejected.** Makefile is outside the spec's file scope and the smoke script is not in the video.

## Checked and fine
- Contracts unchanged (`ConsistencyResult`, `CollectionResult`, `Receipt`, tool names); `src/api/app.py` only calls `handle_collection` and passes `reasons` through.
- Tolerance fix arithmetic: 12 vs 10.8 and 13.2 pass with `1e-9` epsilon; 10.79 and 13.21 fail.
- `build_model` is inside the agent's try, so provider errors become `llm_error` and the smoke check for it is sound.
- Python 3.10 compatible, offline, no new packages, no absolute paths or names.
