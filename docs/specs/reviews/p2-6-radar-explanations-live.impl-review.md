# Implementation review: p2-6-radar-explanations-live

Scope reviewed: uncommitted diff (explain.py, facts.py, models.py, one line in rules.py, docs, two new test files, one assertion in tests/test_radar_explain.py) against the spec, CLAUDE.md and CONTEXT.md. Full suite before review: 307 passed, 4 skipped.

## Findings (most severe first)

1. **Medium: `_excluded` (validator and text choice) was looser than the template's own check.** The template note requires every `excluded_collector_ids` entry to be a string, while `_excluded` only required a non-empty list. With a malformed list the validator could demand a note the template would never write. **Fixed:** `_excluded` now also requires all ids to be strings, so both use the same condition.
2. **Low: one existing test was edited** (`tests/test_radar_explain.py::test_radar_run_explains_flags`). Unavoidable: it asserted that `rules.run()` Flags have empty `facts`, which contradicts the feature. It is P2's own test, the change is called out in the spec, and it now compares the verdict tuple (rule, subject, score, evidence ids, status), which is what it protected. **Not fixed (intended).**
3. **Low: `facts` and `explanation_source` are not persisted** by `Store.replace_flags`, so a Flag read back via the API shows the text only. Out of P2's boundary (ledger/api); documented in the doc and spec. **Not fixed (out of scope).**
4. **Info: excluded tonnes use stored values**, so a tampered Receipt can be attributed to another Recycler. Documented, covered by a test, and the note points the Auditor to R3. **Not fixed (by design).**
5. **Info: the rule's docstring line is long.** One-line body change only, as allowed. **Not fixed.**

## Checks with no issue
- Verdict fields (rule, subject_id, score, evidence_ids, status) are never updated; tests compare them against the raw rule output, with an accepted LLM text and end to end.
- Fail closed: any derivation error or ratio/score mismatch gives empty facts and the rule's text; the radar never raises. Nothing is written to the store.
- LLM text is used only after the existing validator (plus the broken-Chain note check); MOCK_LLM=1 makes no network call (tested by patching `socket.socket.connect`).
- Only `rules.py::_explain` changed in rules.py; no changes to ledger, api, bot, console, perception, synth, eval or other existing tests. `src/api/app.py` does not call the explainer directly.
- Vocabulary follows CONTEXT.md (Certificate, Verified inflow, Kabadiwala, Recycler, Receipt, Chain). No secrets, absolute paths or attribution text added.
- Tests would catch regressions: ratio equals score, excluded tonnes after a real tamper, rejected LLM paths, decide_flag keeps facts, legacy no-store behaviour.

## Result
The full suite passed (307 passed, 4 skipped) before fix 1. Fix 1 is a one-line tightening of a helper and was not re-run: the shell was denied after the edit.
