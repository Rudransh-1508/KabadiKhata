# Spec review: p2-6-radar-explanations-live

Findings ranked by severity. Each has a decision.

## 1. HIGH: the spec contradicts an existing test
`tests/test_radar_explain.py::test_radar_run_explains_flags` asserts that `rules.run()` Flags have the same `facts` as the raw rule Flags (`{}`). Attaching derived facts breaks it, yet the spec claimed "no existing test modified".
**Decision: applied.** New section "Conflict with an existing test": that file is P2's own (PR #8). Only the final assertion changes, to compare the verdict fields instead of `facts`. It is called out in the scope, acceptance criteria 1 and 8, and the hand-off. Rejected alternative: leaving facts off the Flag, which breaks brief item 3.

## 2. HIGH: the LLM path could never accept the broken-Chain note
The note says "R3". The number validator scans digits and would reject the `3` as "number not in facts", so the "llm" source would never apply in the broken-Chain case.
**Decision: applied.** The validator strips the literal token `R3` when `excluded_tonnes > 0`. Two tests added.

## 3. MEDIUM: derived facts could describe a different verdict than the rule gave
`derive_facts` recomputes from the live store after the rule ran. A concurrent write would give a ratio that no longer matches the Flag.
**Decision: applied.** R1 consistency guard (score vs. recomputed ratio, 999 for None), plus a requirement that all evidence ids resolve and `subject_id` matches; the R2 `subject_id` check too. On mismatch facts are `{}` and the rule text stays. Test added.

## 4. MEDIUM: excluded tonnes depend on tamperable fields
`ledger.world.TAMPERABLE` includes `weight_kg`, `material` and `recycler_id`, so excluded tonnes are the stored values, not necessarily the originally sold ones.
**Decision: applied.** The spec states "as currently stored", the note says "recorded", and a test documents the limitation. Not fixed in code: the original values are not recoverable, and the R3 pointer covers it.

## 5. MEDIUM: privacy and policy were not addressed
Explanations now name Kabadiwala ids, and facts go to an external LLM and the disk cache.
**Decision: applied.** New "Privacy and policy" section: Flags stay Auditor-only (Cedar `read_flags`); the `_FACT_KEYS` allowlist; no Receipt PII in facts; ids are pseudonymous and synthetic in the demo.

## 6. LOW: ambiguous `synthetic` derivation and inconsistent rule 3
"That Recycler's Receipts" was ambiguous. Rule 3 said empty facts mean source "rule" but the ladder can give "template" when the rule text is empty.
**Decision: applied.** `synthetic` is scoped to the Receipts behind the key. Rule 3 is aligned with the ladder.

## 7. LOW: the "R1 score unchanged vs. pre-feature numbers" test was untestable
**Decision: applied.** Replaced by a comparison against the raw rule output, with no explainer.

## 8. LOW: hidden coupling and housekeeping
`explain.py` would take a ledger type; the module docstring is stale; "sample world" was vague.
**Decision: applied.** `store` is typed `Any` / `TYPE_CHECKING` with a lazy import; the docstring is updated; the seeded world is named.

## Considered and rejected
- Capping total LLM time per `POST /radar/run`: needs changes in `rules.run` or the API, which are out of bounds. The spec already documents the latency and the cache warm-up.
- Memoising `chain_status` across Flags: it could go stale after a tamper. The cost is fine at ~1,000 Receipts.
- Adding a counterfactual "ratio if the excluded Receipts counted": scope creep. The video needs only the note and the R3 pointer.
- Persisting `facts` / `explanation_source`: would touch the store schema (P3). Already out of scope and documented.
- Preferring freshly derived facts over `flag.facts` supplied by a caller: rules never set facts, so the legacy contract (caller facts win) stays.
