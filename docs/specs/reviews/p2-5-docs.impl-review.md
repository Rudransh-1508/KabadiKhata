# Implementation review: p2-5-docs

Scope: `docs/agent_and_policy.md`, `src/agent/README.md`, `tests/test_docs.py`, `tests/test_radar_explain.py`.
Checked against the spec, CLAUDE.md and CONTEXT.md. Every command, path, action, policy `@id`, env var
default and reason code in the docs was compared with the code (policies, `src/api/app.py`, `Makefile`,
`src/common/config.py`, `scripts/smoke_real_llm.py`, `src/ledger/seed.py`). No source under `src/` changed.

## Findings (most severe first)

1. **Low: `test_radar_run_explains_flags` relied on the shell having `MOCK_LLM=1`.** Without it, `rules.run`
   would call the real explainer and the network. Decision: **fixed** (the test now sets `MOCK_LLM=1` itself).
2. **Info: policy table, route table, reason codes, env defaults (`LLM_EXPLAIN_TIMEOUT_S` 20, `KK_CACHE_DIR`
   `.cache`, `KK_R2_MAX_DISTANCE`), smoke exit codes and the `make seed` fallback all match the code.**
   Decision: not fixed, nothing to fix.
3. **Info: fail-closed policy code is untouched. The doc presents Cedar as the policy layer that holds even
   if the agent code changes, not an independent check, and the LLM only explains.** Decision: not fixed, nothing to fix.
4. **Info: vocabulary and hygiene.** No "Claim" for Certificate, no absolute paths, venv paths, secrets or
   attribution; drift tests enforce this. Decision: not fixed, nothing to fix.
5. **Low: the beat-4 curl calls and `make api` were verified with `fastapi.testclient` in
   `tests/test_docs.py`, not against a live server** (recorded in the spec's Deviations).
   Decision: not fixed; acceptable for an offline run, and a human should run them once before recording.
