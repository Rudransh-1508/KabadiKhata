# p2-5-docs implementation review

## Fix round

Cause: the four failing tests in `tests/test_api.py` (`GET /flags`, `PUT /actors/{id}`, `GET /photos/{sha}.jpg`, registration takeover 409) all hit the Cedar layer. The API calls the actions `read_flags`, `list_actors` and `register`, and uses a `Photo` resource for `read_receipt_pii`. None of these were in `src/policy/schema.cedarschema` or `src/policy/policies.cedar`, so `is_allowed()` denied them (`unknown action 'register'`, or a missing permit). This is a policy gap, not a docs problem and not a test problem.

Changes (policy layer only, no test edited):
- `src/policy/schema.cedarschema`: added entities `Photo` and `Directory`; added actions `read_flags` (Radar), `list_actors` (Directory) and `register` (Actor); `read_receipt_pii` now also applies to `Photo`.
- `src/policy/policies.cedar`: the auditor policy also permits `read_flags` and `list_actors`; new permits `kabadiwala-photo` (Kabadiwala reads a Photo by sha256), `kabadiwala-list-directory`, and `self-registration` (an Actor may register only itself, `resource == principal`). The agent `forbid` list now also covers `read_flags`, `list_actors` and `register`. Brands get none of the new permits.
- `src/policy/authz.py`: `_RESOURCE_TYPES` gains `Photo`, `Directory`, `Actor`; an `Actor` resource id in the reference form `Actor::"<id>"` is parsed to its bare id; `_principal(principal, action)` lets only the `register` action accept a principal not yet in the directory (treated as a new Kabadiwala), still limited to itself by the policy.

Trade-offs to note: Photo access has no owner check because the store cannot map a photo sha256 to a collector, so the unguessable hash acts as the capability. The self-registration role assumption for unknown principals is limited to `register`.

Not verified: shell access was denied in this session after the edits, so the test suite could not be rerun. Run `MOCK_LLM=1 python -m pytest -q` to confirm; `docs/agent_and_policy.md` and `tests/test_policy.py` should also be checked for any policy table that needs the new rows.
