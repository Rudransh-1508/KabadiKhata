# Implementation review: p2-2-flag-decisions

Scope: `src/radar/decisions.py`, `src/radar/explain.py`, `Flag` additions in `src/common/models.py`, `tests/test_flag_decisions.py`, `tests/test_radar_explain.py`, checked against the spec, CLAUDE.md and CONTEXT.md. Full suite run with `MOCK_LLM=1 python -m pytest -q`: 132 passed before the fixes.

## Findings (most severe first)

1. **Medium, vocabulary and correctness: R3 text contradicted the glossary.** The text said Receipts "from there on" are not counted in Verified inflow. CONTEXT.md defines Verified inflow as counting only Receipts whose whole Chain verifies, so a break excludes all of that Kabadiwala's Receipts, not just later ones. The explanation therefore stated something untrue to the Auditor.
   - **Decision: fixed.** English and Hindi now say none of this Kabadiwala's Receipts count towards Verified inflow. The spec text was updated to match.
2. **Low, fail-closed robustness: `decide_flag` could raise `AttributeError`.** After Cedar allowed the call it did `ACTOR_UID_RE.match(principal).group(1)`. If a future policy change allowed a non-Actor principal (for example the Agent), this would crash with a 500 instead of a typed refusal.
   - **Decision: fixed.** A non-matching principal now raises `FlagDenied` with a Cedar-style reason. Not unit-tested, because the current policies cannot reach it.
3. **Info, order of checks.** Validation, then Cedar, then status matches the spec. A non-Auditor learns nothing about a Flag's state.
   - **Decision: no change needed.**
4. **Info, compatibility.** `Flag.facts` and `Flag.decision_note` are optional and default empty, so the store's `Flag(**row)` construction and `src/api/app.py` are unaffected. Nothing under `src/api`, `src/ledger`, `bot/`, `console/` or perception was changed.
   - **Decision: no change needed.**
5. **Info, code decides and the LLM explains.** `explain.py` is pure and offline, imports no network or LLM modules (asserted via `ast` in tests), never recomputes the ratio, and falls back to a generic figure-free text on invalid facts.
   - **Decision: no change needed.**
6. **Info, test quality.** Tests cover every transition, the error order, the Cedar 403 body, immutability, facts validation and the number-provenance check. Wording tests would also catch the R3 term regression only by vocabulary, which is acceptable.
   - **Decision: no change needed.**
7. **Info, no secrets, attribution or absolute paths found** in the new files.
   - **Decision: no change needed.**

## Results

The suite is re-run after the fixes; see the final line of the reply.
