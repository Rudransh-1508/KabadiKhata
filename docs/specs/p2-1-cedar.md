# Spec p2-1-cedar: Cedar policies behind `is_allowed()`

## Goal
Replace the stub in `src/policy/authz.py` with real Cedar evaluation (`cedarpy`), default deny.
- **Video beat 4, Cedar denial:** a Brand asking for a Kabadiwala's identity or Receipts gets HTTP 403 `{"denied_by": "cedar", ...}`, shown as the red "Denied by Cedar policy" banner. Provenance stays aggregate-only.
- **Design rule 2:** the agent's one write, `create_receipt`, needs `context.consistency_ok == true` *and* a Cedar permit. Cedar is "the policy layer that holds even if the agent code changes".
- **CLAUDE.md smaller notes:** `Receipt.collector` and `Certificate.buyer` are entity references (`Actor::"<id>"`); every handler asks `is_allowed` first.
- Spine beats served: 1 (guarded write) and 4. Beats 2 and 3 use `run_radar` / `verify_chain` permits.

## Scope
- `src/policy/schema.cedarschema`, `src/policy/policies.cedar` (new).
- `src/policy/directory.py` (new): actor directory, principal -> role.
- `src/policy/authz.py`: Cedar internals; same public names (`AGENT`, `Decision`, `is_allowed`).
- `pyproject.toml`: add `"cedarpy"` to `dependencies`.
- `tests/test_policy.py`, `tests/conftest.py` (new).
- One minimal compatibility change outside P2, called out below: `src/api/app.py` loads the directory from the store.

## Out of scope
- Real authentication (X-Principal stays a stand-in), Cedar in Lambda/`template.yaml`, policy hot reload, Recycler permissions (none in §6, so Recyclers are default-deny everywhere), Certificate or Flag handlers (P3 adds them; the policies already cover them).
- No change to `src/ledger`, `bot/`, `console/`, perception, or the agent's code (it already calls `is_allowed(AGENT, "create_receipt", {"type": "Receipt", "collector": ...}, {"consistency_ok": ...})`).

## Dependencies on teammates
None blocking.
- Roles come from our own `directory` (in-memory dict), filled by `register()` in tests or `load_from_store(store)` at runtime. It reads `store.list_actors()` (already exists in `ledger/store.py`, returns `Actor` with `actor_id`, `role`). It never imports P1's seed file; whatever seeds the store feeds it.
- `Agent::"kabadi-agent"` is built in, not in the directory.
- Cedar evaluation needs no store, network or LLM. The only P3 touch is the one-line `app.py` hook below.

## Interfaces
`policy/authz.py` (unchanged public surface):
```python
AGENT = 'Agent::"kabadi-agent"'
@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    def to_denial(self, action: str) -> dict   # {"denied_by": "cedar", "action": action, "reason": reason}
def is_allowed(principal: str, action: str, resource: dict, context: dict | None = None) -> Decision
```
- `principal`: a Cedar UID string `Actor::"<id>"` or `Agent::"kabadi-agent"` (exactly what `app.principal()` and `tools.py` pass).
- `action`: bare name (`"create_receipt"`); mapped to `Action::"<name>"`.
- `resource`: dict, `type` required (`Receipt|Chain|Certificate|Flag|Radar`). Optional `id` (default `"-"`). Entity-reference attributes are UID strings, converted to `{"__entity": {"type", "id"}}`: `collector` (Receipt, Chain), `buyer` (Certificate). Any other keys are ignored.
- `context`: dict, passed to Cedar. Only `consistency_ok: bool` is declared in the schema; absent -> `{}`.

`policy/directory.py`:
```python
def register(actor_id: str, role: str) -> None        # role in kabadiwala|recycler|brand|auditor, else ValueError
def role_of(actor_id: str) -> str | None
def load_from_store(store) -> int                     # additive: registers store.list_actors(), never removes; returns count
def refresh() -> int                                  # re-runs load_from_store on every store seen so far
def clear() -> None                                   # tests only: drops actors AND remembered stores
```
- `register` also validates `actor_id` against the Actor id regex (see Edge cases); a bad id raises `ValueError`.
- `load_from_store` remembers the store in a source list so `refresh()` can re-read it.
- Thread-safe (one lock; FastAPI runs handlers in a thread pool).

Cedar entities built per call: principal (`Actor` with parent `Role::"<role>"`, or `Agent`), the resource with its attrs, and the referenced `Actor` entities with no attrs. Role entities have no parents.

`app.py` compatibility fix (one line, the only edit outside P2): in `_store_at(path)`, after `Store(path)`, call `policy.directory.load_from_store(store)`. Reason: unknown principals fail closed, so the real API needs roles registered. Seeding after the API starts is also covered by lazy refresh (see Behaviour).

## Cedar model
Schema (`schema.cedarschema`):
- Entity types: `Role`; `Actor in [Role]`; `Agent`; `Receipt {collector?: Actor}`; `Chain {collector?: Actor}`; `Certificate {buyer?: Actor}`; `Flag`; `Radar`.
- Entity-reference attributes are **optional** in the schema and every policy that reads them is guarded with `resource has collector` / `resource has buyer`. Reason: the agent's existing call and `tests/test_agent_stub.py` pass a Receipt resource without a collector, and an unguarded access would be a Cedar error. The schema validates the policies; request entities are not rejected by it.
- Actions (principal types `[Actor, Agent]`): `create_collection` -> Chain; `read_receipt` -> Chain, Receipt; `read_receipt_pii` -> Receipt, Chain; `verify_chain` -> Chain; `create_receipt` -> Receipt with context `{consistency_ok: Bool}`; `read_provenance` -> Certificate; `run_radar` -> Radar; `approve_flag` -> Flag; `issue_certificate` -> Certificate. The `Action` entity types are what `cedar validate` checks the policies against.

Policies (`policies.cedar`, default deny):
1. Kabadiwala, own data: `create_collection`, `read_receipt`, `verify_chain` when `resource.collector == principal`. (Decision: `verify_chain` on own chain is allowed, beyond §6, because the "मेरा हिसाब" QR links to it.) No `read_receipt_pii` for anyone but the auditor.
2. Brand: `read_provenance` when `resource.buyer == principal`.
3. Auditor: `read_receipt`, `read_receipt_pii`, `verify_chain`, `run_radar`, `approve_flag`, `read_provenance` on any resource.
4. Agent permit: `create_receipt` when `context.consistency_ok == true`.
5. Agent forbid: `approve_flag`, `issue_certificate`, `read_receipt_pii`, `read_receipt`, `read_provenance`, `run_radar`, `verify_chain`, `create_collection`. (`forbid` beats `permit`; default deny already covers it, the explicit list is the documented guarantee.)
- Nobody but the auditor gets `approve_flag`. Nobody at all gets `issue_certificate` (reserved action, recycler-side, out of scope), so it denies for every principal.

## Behaviour and rules
- Fail closed. Deny with a clear `reason` when: principal is not `Actor::"<id>"`/`Agent::"kabadi-agent"` shaped; the actor is not in the directory (`"unknown principal"`); `resource` lacks `type` or a UID string is malformed (including a `collector`/`buyer` that is not an `Actor::"<id>"` UID); `action` is not in the schema; cedarpy raises (`"policy error: ..."`). `is_allowed` never raises.
- Allow only when cedarpy's decision is Allow **and** `diagnostics.errors` is empty. Allow with any error is a deny (`"policy error: ..."`). Import cedarpy's `Decision` under an alias (it clashes with ours).
- Unknown actor: call `directory.refresh()` once before denying (cheap; keeps seed-after-start working). If still unknown, deny.
- Reasons: allow -> `"allowed by policy"`; Cedar deny -> `"no policy permits <role> to <action>"` (or `"forbidden by policy"` when a forbid matched, using diagnostics reasons). Must be non-empty and contain no stack traces.
- Policy and schema text are read once at import (`lru_cache`), from files next to `authz.py`. A missing or invalid file makes every call deny with `"policy unavailable"`, never allow.
- Every decision is logged at INFO by the caller already (`app.require`); `authz` logs only errors.
- Existing agent tests: `tests/test_agent_stub.py` expects the agent's behaviour with `resource={}` (no `type`). That would deny for the wrong reason but still deny; the allow case `is_allowed(AGENT, "create_receipt", {}, {"consistency_ok": True})` must still allow. Rule: for the Agent principal, a missing `type` on a `create_receipt` request defaults to `Receipt`. Other principals still deny on missing `type`.

## Edge cases
- `consistency_ok` missing, `False`, the string `"true"`, or `1` -> deny (Cedar type error is caught -> deny).
- Kabadiwala reading another's chain -> deny; resource without `collector` -> deny.
- Brand vs another brand's Certificate -> deny; brand `read_receipt_pii` -> deny; brand `read_receipt` -> deny.
- Principal id with quotes or backslashes (`Actor::"a\"b"`): parse strictly with a regex, deny if not matching `^Actor::"([A-Za-z0-9_.:@-]+)"$`. The same regex gates `collector` and `buyer` values (an `Agent::"x"` there is malformed -> deny) and `directory.register`.
- A `collector` that is well-formed but not in the directory is fine (the principal-equals-collector check only compares UIDs).
- Directory re-registration with a different role: last write wins; role `recycler` is valid but has no permits.
- Concurrent calls: no shared mutable state except the lock-guarded directory.
- Principal says `Agent::"other"` -> unknown, deny.

## Test plan (`tests/test_policy.py`; offline, no network)
`conftest.py` autouse fixture: `directory.clear()`, then register `kw-raju` kabadiwala, `kw-sita` kabadiwala, `brand-1`, `brand-2` brand, `auditor-1` auditor, `rec-a` recycler (matches ids used in `tests/test_api.py`). Teardown clears. This fixture is what keeps `tests/test_api.py` passing under fail-closed (its temp DB has no actors); `tests/test_api.py` itself is not edited. Because `load_from_store` is additive, the API's empty temp store never removes these registrations.
Allow/deny:
1. `test_kabadiwala_creates_collection_on_own_chain`
2. `test_kabadiwala_cannot_use_another_chain`
3. `test_kabadiwala_reads_and_verifies_own_chain`
4. `test_kabadiwala_denied_read_receipt_pii`
5. `test_brand_reads_provenance_of_own_certificate`
6. `test_brand_denied_other_brands_certificate`
7. `test_brand_denied_receipt_pii_and_receipts` (video beat 4; also asserts `to_denial` body shape)
8. `test_auditor_can_read_verify_run_radar_approve_flag`
9. `test_auditor_cannot_create_collection`
10. `test_agent_creates_receipt_only_when_consistency_ok`
11. `test_agent_forbidden_everything_else` (parametrised over all non-`create_receipt` actions, with `consistency_ok: True`; asserts deny and that the reason says forbidden, proving forbid wins)
12. `test_recycler_default_denied`
13. `test_issue_certificate_denied_for_all`
Fail-closed:
14. `test_unknown_principal_denied_with_reason`
15. `test_malformed_principal_or_resource_denied`
16. `test_unknown_action_denied`
17. `test_cedar_exception_denies` (monkeypatch cedarpy call to raise)
18. `test_consistency_ok_wrong_type_denied`
19. `test_missing_policy_file_denies` (monkeypatch path)
19b. `test_allow_requires_cedar_allow` (monkeypatch the cedarpy call to return Deny, and separately Allow with non-empty diagnostics errors; `is_allowed` must deny both)
19c. `test_seed_after_start_refreshes_directory` (unknown principal, then `put_actor` into a store already passed to `load_from_store`, then `is_allowed` allows)
Structure:
20. `test_policies_validate_against_schema` (`cedarpy.validate_policies(policies, schema)`, assert validation passed; this function exists in the installed cedarpy, no fallback)
21. `test_directory_register_rejects_bad_role`, `test_load_from_store_registers_actors` (temp SQLite `Store`, `put_actor`)
22. `test_decision_to_denial_shape`
Regression: `tests/test_api.py`, `tests/test_agent_stub.py`, `tests/test_agent_on_store.py`, `tests/test_chain.py` all pass unchanged. A new API-level test (in `test_policy.py`, using `TestClient`): Raju reading Sita's `/receipts` -> 403 `denied_by == "cedar"`.

## Acceptance criteria
- `MOCK_LLM=1 python -m pytest -q` passes, with >= 20 new test functions and no network (`MOCK_LLM=1`).
- `test_allow_requires_cedar_allow` passes; `grep -rn "stub" src/policy/authz.py` returns nothing (secondary check).
- `policies.cedar` validates against `schema.cedarschema` (test 20).
- `cedarpy` is in `pyproject.toml` dependencies; no other new packages.
- `is_allowed`, `AGENT`, `Decision.to_denial` signatures match section Interfaces; `src/api/app.py` diff is at most the one-line directory hook, noted in the commit message.
- A Brand principal requesting `read_receipt` / `read_receipt_pii` for any Kabadiwala gets a 403 body with `denied_by: "cedar"` and a non-empty `reason`.
- No file mentions an author or tool; vocabulary follows CONTEXT.md (Certificate, Kabadiwala, Receipt, Chain).
- Open decisions recorded here: own-chain `verify_chain` for Kabadiwala (beyond §6); `Radar` and `issue_certificate` added to the entity model beyond §3.4; Agent forbids list is broader than §6.
