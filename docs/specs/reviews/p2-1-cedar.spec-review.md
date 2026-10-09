# Spec review: p2-1-cedar

Reviewed `docs/specs/p2-1-cedar.md` against CLAUDE.md, CONTEXT.md, `src/common/models.py`, `src/api/app.py`, `src/agent/tools.py`, `tests/test_agent_stub.py`, `tests/test_api.py`, SCOPED_DOWN §3.4/§6. cedarpy behaviour was checked against its public API surface only (the installed module exposes `is_authorized`, `validate_policies`, `Decision`, `Diagnostics`); no code was run, so the spec tells the implementer to confirm schema syntax with the first test.

## High

1. **Required schema attributes break the existing agent test.** `Receipt {collector: Actor}` is required, but `tests/test_agent_stub.py` calls `is_allowed(AGENT, "create_receipt", {}, {"consistency_ok": True})` with no collector and expects allow. Policies reading `resource.collector` without `has` would also error. **Applied:** `collector` and `buyer` are optional in the schema (`collector?: Actor`); every policy reading them is guarded by `has`; the schema is used to validate policies, not to reject request entities.
2. **Error handling was ambiguous and could allow despite a swallowed policy error.** Cedar returns a decision plus `diagnostics.errors` rather than raising; an Allow can coexist with an erroring policy. **Applied:** allow only when Cedar says Allow AND diagnostics errors are empty; any error is a deny with `"policy error: ..."`. Cedar's `Decision` enum is imported under an alias to avoid clashing with ours.
3. **Lazy refresh was underspecified (hidden global state).** "Loaded store(s)" had no mechanism, and `load_from_store` might wipe test registrations. **Applied:** `load_from_store` is additive, remembers the store in a source list, and `is_allowed` refreshes from those sources once on an unknown principal; `clear()` also drops sources.
4. **Existing API tests rely on actors nothing seeds.** `tests/test_api.py` uses `kw-raju` and `brand-1` on a fresh temp DB; with fail-closed they would 403. **Applied:** the spec states that the `tests/conftest.py` autouse registration is what keeps them passing, and that `tests/test_api.py` is not edited.

## Medium

5. **Entity-reference attributes were not type-checked.** `collector`/`buyer` could be `Agent::"x"` or arbitrary UIDs. **Applied:** both must match the Actor UID regex, else deny as malformed. `register()` validates actor ids against the same regex so a seeded actor can never be unreachable.
6. **Test 20 hedged on the API.** The installed cedarpy has `validate_policies`. **Applied:** use it and assert it passes; the fallback is removed.
7. **Untestable acceptance line.** "No `return Decision(True, ...)` path that is not a Cedar permit" is a grep, not a test. **Applied:** added `test_allow_requires_cedar_allow` (monkeypatched Cedar returning Deny, or Allow with errors, makes `is_allowed` deny); grep kept as a secondary check.
8. **Forbid-wins not proven.** **Applied:** test 11 asserts the reason mentions the forbid for the agent's non-write actions even with `consistency_ok: True`.
9. **Test count wording.** Acceptance said "at least 20" against a plan of 23 functions; now "at least 20 new test functions" and the plan list is renumbered with the new test.

## Low

10. **Role-leaking reasons.** Fine for the demo, the banner is meant to explain. **Rejected**; reasons never include policy text or stack traces.
11. **Scope creep (`Radar`, `issue_certificate`, `Flag`).** The brief itself lists `run_radar` and `issue_certificate`; cost is a few schema lines. **Rejected**; kept as recorded open decisions.
12. **Spoofable `X-Principal`.** Authentication is out of scope for the demo stack (ADR 0001). **Rejected**; already under Out of scope.
13. **Vocabulary.** Certificate, Kabadiwala, Receipt, Chain, Collection are used per CONTEXT.md; `create_collection` is an action name from §3.4, not UI text. No change.
