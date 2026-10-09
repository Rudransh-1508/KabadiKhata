# Implementation review: p2-1-cedar

Scope: uncommitted changes (`src/policy/authz.py`, `directory.py`, `policies.cedar`, `schema.cedarschema`, `src/api/app.py` hook, `pyproject.toml`, `tests/conftest.py`, `tests/test_policy.py`) against `docs/specs/p2-1-cedar.md`, CLAUDE.md and CONTEXT.md.

**Limitation:** the review environment refused every command that executes Python (pytest and a one-line cedarpy check), so this is a static read only. The suite was NOT run by the reviewer. Run `MOCK_LLM=1 python -m pytest -q` (or `make test`) before merging.

## Verified by reading

- Public surface matches the spec: `AGENT`, `Decision`, `Decision.to_denial`, `is_allowed(principal, action, resource, context)`. `app.py` calls (`principal()` -> `Actor::"<id>"`, `chain_resource()` -> `{"type": "Chain", "collector": ...}`) map onto the resource and principal handling.
- Fail closed: every early exit returns a deny. Covered cases: policy files missing, unknown action, unknown or malformed principal, malformed resource, bad `collector`/`buyer`, Cedar exception, non-empty `diagnostics.errors` (even with an Allow decision), and a catch-all in `is_allowed`. There is no `Decision(True, ...)` path except after Cedar returns Allow with no errors.
- Cedar only permits the agent's `create_receipt` when `context.consistency_ok == true`. The agent forbid list covers every other action and wins over permits. Brand gets `read_provenance` only when `resource.buyer == principal` and has no permit for `read_receipt` or `read_receipt_pii` (video beat 4).
- `Receipt.collector` and `Certificate.buyer` are entity references. The principal entity is written after the referenced entity, so a collector equal to the principal keeps its role parent.
- Vocabulary follows CONTEXT.md (Certificate, Kabadiwala, Receipt, Chain). No attribution, absolute paths or secrets in the changed files (grepped). The only "stub" in `authz.py` is gone.
- The `app.py` change is the single one-line directory hook, as the spec allows. `cedarpy` was added to `pyproject.toml`.
- Test quality: the tests assert real Cedar outcomes (not mocks) for the allow/deny matrix, with mocks only for the "Cedar raises" and "Allow with errors" paths. The forbid test asserts `"forbidden"` in the reason, which would fail if forbid stopped winning. The API test goes through `TestClient` end to end.

## Findings, ranked

### Medium

1. **Stale roles are never revoked or downgraded.** `directory` is additive and `refresh()` only runs when a principal is unknown, so an actor whose role changes in the store keeps its old role until restart. *Not fixed:* the spec records additive loading as a decision, there is no role-change flow in the demo, and a fix would add a per-request DB read. Noted for P3 if actors become mutable.
2. **Unauthenticated requests trigger a store read.** Each request with an unknown `X-Principal` calls `directory.refresh()`. *Not fixed:* the spec requires the refresh (seed-after-start), the DB is local SQLite, and `X-Principal` is already a documented stand-in for auth.

### Low

3. **Malformed ids from query parameters return 403, not 422.** A `collector_id` containing a quote or space is denied as "malformed collector". *Not fixed:* denying is the fail-closed outcome the spec asks for.
4. **Reason text names the role** ("no policy permits brand to read_receipt"). *Not fixed:* intentional, the Cedar banner is meant to explain the denial (see the spec review, item 10).
5. **Cedar syntax and schema validity are unverified by this reviewer** because nothing could be executed. `test_policies_validate_against_schema` is the guard; if it fails, fix the policy syntax (e.g. `principal is Actor in Role::"..."` needs a recent cedarpy) rather than weakening the test.

### None found

- No correctness, security or compatibility defect in the policy code that requires a change. No code was modified by this review.

## Decisions

| # | Decision |
|---|----------|
| 1 | Not fixed (documented limitation) |
| 2 | Not fixed (spec-mandated) |
| 3 | Not fixed (fail closed is intended) |
| 4 | Not fixed (intentional) |
| 5 | Not verifiable here; left to the first real test run |
