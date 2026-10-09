# Spec review: p2-3-llm-explainer

Reviewed `docs/specs/p2-3-llm-explainer.md` against CLAUDE.md, CONTEXT.md, `src/common/models.py`, `src/radar/explain.py`, `src/common/config.py`, `src/agent/agent.py` (`build_model`), `src/api/app.py` and the brief. No code was run.

## High

1. **Timeout test could not pass as written.** The timeout was specified only for the default completer, but the test injects a sleeping one; a `ThreadPoolExecutor` context would also block on exit. **Applied:** timeout applies to any completer, via a daemon thread; test sleeps 0.5 s and asserts a fast return.
2. **LLM was fed invalid facts.** When `explain` produced its generic fallback (bad or missing facts) step 3 only checked "facts empty", so the model would rephrase garbage. **Applied:** `_explain_ex` returns `from_facts`; invalid facts skip the LLM (`LLM skipped: no facts`); test added.
3. **Accusation language not blocked.** The brief and p2-2 review forbid accusing anyone and ban "fake"/"mock", but the validator only checked "claim". **Applied:** forbidden-word lists (English and Hindi) in the validator, plus test.

## Medium

4. **Number check would reject ids with digits.** Only evidence ids and "string facts" were stripped; list items (`receipt_ids`, `collector_ids`), `subject_id` were ambiguous. **Applied:** strip every string anywhere in facts, evidence ids and subject id; allow `len(evidence_ids)` (the template says "and N more").
5. **Rounding rule was imprecise** (float rounding, integer tokens). **Applied:** `Decimal(str(a))` with ROUND_HALF_UP; the integer-token tolerance is documented as accepted.
6. **Stale cache after template edits.** The template text is part of the prompt but not of the key. **Applied:** template hash in the key.
7. **Unfiltered facts reach an external model.** Unknown keys and long strings (hostile names) rode along. **Applied:** per-rule key allowlist, truncation; filtered dict used for prompt, key and validator; test added. Privacy note for P3 (ids and Recycler name leave the machine; demo data is synthetic).
8. **`_model_label` could raise before the call** (unknown provider) and break the "never raises" promise at the cache step. **Applied:** it never raises; the unknown provider surfaces as `LLM unavailable: ValueError`.
9. **`with_llm_explanation` spent a model call even when both texts were set.** **Applied:** skip when both exist.
10. **Hidden latency on a request path.** 20 s per uncached Flag conflicts with the 25 s request budget in CLAUDE.md fix #2. **Applied:** P3 note (few Flags, warm cache, off the request path); also no caller exists in `src/api/app.py` yet, stated explicitly.
11. **Missing tests for criteria.** Acceptance claimed the temperature-0 / explicit-model assertion with no test; no test for cache-hit-without-key (the demo scenario), bad timeout env, digits in ids, forbidden words. **Applied:** five tests added; `LLM_EXPLAIN_TIMEOUT_S` parsing made safe.

## Low

12. `.env.example` exists; "if present" removed. **Applied.**
13. Mock-test isolation: the test now sets `KK_CACHE_DIR` to `tmp_path` so "no files written" is checkable. **Applied.**
14. Sentence count "2..4" vs prompt "exactly 3" looked inconsistent. **Applied:** stated as deliberately looser.

## Rejected

- **Make `MOCK_LLM=1` replay cached LLM text** (CLAUDE.md rule 4 calls it a replay mode). The brief says MOCK_LLM returns the template and makes no cache access; replaying would make tests depend on disk state. Kept as specified. Demo determinism comes from running with `MOCK_LLM=0` and a warm cache.
- **Reuse `agent.agent.build_model`.** It returns `ScriptedModel` under `MOCK_LLM`, and importing `agent.agent` pulls in tools. The spec's own builder with the same provider settings stays; the test pins temperature 0 and the explicit model.
- **Circuit breaker after repeated LLM failures.** Scope creep for the video; the per-call timeout is enough.
- **Persist `source`/`note`.** Would need a store schema change in P3's module; the Auditor console needs only the two strings.
