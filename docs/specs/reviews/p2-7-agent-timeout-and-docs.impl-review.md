# Implementation review: p2-7-agent-timeout-and-docs

Reviewed the uncommitted diff (`src/agent/agent.py`, `src/common/config.py`, `.env.example`, `docs/agent_and_policy.md`, `src/agent/README.md`) and the new `tests/test_agent_timeout.py` against the spec, CLAUDE.md and CONTEXT.md. Checked the installed strands (`Agent.__call__(limits=...)`, `limit_turns` stop reason, no exception) and google-genai (`HttpOptions.timeout` is in milliseconds) sources.

## Findings, ranked

1. **Low: `_is_timeout` matches any class name containing "Timeout".** Broad, but it only changes the trace note text; the outcome is decided by code either way, so no security or correctness effect.
   Decision: **not fixed.** Deliberate, avoids importing provider SDKs.

2. **Low: the turn cap leaves no trace entry.** Only a `log.warning`. The spec rejected a new trace shape because console and API consumers do not know it.
   Decision: **not fixed**, per spec.

3. **Info: the timeout is per model call, not per request.** Documented as a known limitation in both docs; the worst case is stated honestly rather than promised.
   Decision: **no change needed.**

## Checks that passed

- Fail closed: a timeout or any model error still goes through the code path (`do_check_consistency`, then the guarded `create_receipt`, which Cedar still gates). The model never decides the outcome.
- The trace carries the exception class name only, never the message (a test covers this).
- Callers: `handle_collection` keeps its signature, so `src/api/app.py` is unaffected. `build_model` is unchanged under `MOCK_LLM=1`.
- Tests are offline and would catch regressions: they check the client args for both providers, the retry cap, the turn cap, and the Receipt and Question outcomes on a timeout.
- Vocabulary is correct (Receipt, Question, Collection, Certificate). `.env.example` holds a commented placeholder only. No attribution, absolute paths or secrets found in the changed files.
- Edits stay inside the P2 boundary. No teammate modules were touched.

No necessary fixes were found, so no code changes were made in this review.
