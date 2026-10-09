# Implementation review: p2-4-agent-hardening

Reviewed the uncommitted diff (`src/agent/*`, `scripts/smoke_real_llm.py`, `tests/test_agent_hardening.py`, README, spec) against the spec, CLAUDE.md and CONTEXT.md. Baseline: `MOCK_LLM=1 python -m pytest -q` passed (190 passed, 1 skipped: the OpenAI formatter test, `openai` not installed).

## Findings (most severe first)

1. **Smoke script could print provider exception text (medium).** The spec says the script never prints exception text because it could echo request details or a key. `handle_collection` logs `str(exc)` with `log.warning`, and Python's last-resort handler writes WARNING records to stderr, so a failing real run would have printed it anyway.
   Decision: **fixed.** `main` calls `logging.disable(logging.CRITICAL)` after the SKIP checks, so only the trace (exception type name) is shown. The agent's own logging is not changed, so other callers keep the diagnostic. Test `test_smoke_exit_codes_ok_and_raised` asserts the raised message is absent from output.

2. **Exit codes 0 and 2 were untested, and a raising mock run gave a traceback (low-medium).** Only exit 1 and the SKIP paths were covered. A bug in the MOCK_LLM run would crash with a stack trace instead of the documented exit 2.
   Decision: **fixed.** The mock run is wrapped like the real run (prints the type, exit 2). New test covers `SMOKE OK` (0) and a raised real run (2). The test restores `logging.disable` in a `finally` so it cannot silence other tests.

3. **Policy code is fail-closed (no issue).** NaN confidence, NaN/inf/zero/negative claimed kg and unknown photo material with nothing stated all refuse. `guarded_create_receipt` recomputes consistency from evidence and still asks Cedar, so a model that calls the write tool after a Question is refused (existing `test_guard_refuses_direct_write_on_failed_check`). The LLM never supplies a weight, material or price; the Receipt weight is the scale reading.
   Decision: not applicable.

4. **Injection tests run against the scripted model (low, accepted).** With `MOCK_LLM=1` the model is deterministic, so these tests prove the code path decides the outcome (the claim only reaches `check_consistency`), not that a real model resists. That is the intended split (code decides); the real-model behaviour is what the `injection` smoke case is for.
   Decision: **not fixed.** Documented limit; the smoke run before demo day covers it.

5. **Other callers (no issue).** `reasons` pass through `src/api/app.py` unchanged; the new codes are additive. No contract field, tool name or file outside `src/agent`, `tests`, `scripts`, `docs` changed. `grep` for `bot`/`console` finds no directory in this worktree, so the "bot must not switch on reason strings" note stays a P4 hand-off.
   Decision: not applicable.

6. **Vocabulary, secrets, attribution (no issue).** Prose uses Kabadiwala, Collection, Question, Receipt; the AST-based vocabulary test passes. No absolute paths, key values or attribution lines in new or changed files (only the spec review quotes the file name `CLAUDE.md`, which is a repo document).
   Decision: not applicable.

7. **Minor, not fixed.** `test_tool_names_are_the_six_expected_and_one_write` calls the tools on a failing Collection, so it proves the non-write tools do not write but not that `create_receipt` is the only writer on a passing one; the pass case is covered by `test_pass_writes_one_receipt` in the existing suite.
   Decision: **not fixed**, redundant.

## Result
Full suite rerun after the fixes: see the final line of the reply.
