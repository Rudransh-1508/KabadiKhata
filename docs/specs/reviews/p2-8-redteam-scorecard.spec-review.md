# Spec review: p2-8-redteam-scorecard

Checked against CLAUDE.md, CONTEXT.md, `src/api/app.py`, `src/agent/agent.py`, `src/agent/tools.py`, `src/ledger/store.py`, `src/ledger/chain.py`, `src/ledger/world.py`, `src/radar/rules.py`, `src/policy/authz.py`, `tests/conftest.py`, `tests/test_docs.py`, and the installed strands tool registry (an unknown tool name returns an error result; extra arguments to a no-argument tool are dropped). No contract in `src/common/models.py` changes.

## Findings, ranked

1. **High: the generated Markdown would not be stable.** Receipt IDs come from the hash, which includes `ts = datetime.now()`. Any row that prints a Receipt ID changes on every run, so the "committed scorecard matches the run" test would fail at random.
   Decision: **applied.** Evidence strings carry reason codes, HTTP statuses, counts, weights, `broken_at_seq` and Flag rules, never Receipt IDs, hashes or times.

2. **High: "brand decides a Flag" can pass for the wrong reason.** `POST /flags/{id}/decision` returns 404 for an unknown Flag *before* asking Cedar. An attack on a made-up Flag ID would "lose" without Cedar ever running.
   Decision: **applied.** The auditor runs the radar first, and the brand attacks a real Flag ID. The row only counts as blocked on a 403 whose body has `denied_by: "cedar"`. The same rule applies to every access row: only a Cedar 403 counts, never a 404 or 422.

3. **Medium: the search-copy row must not depend on OpenSearch.** With `KK_OPENSEARCH_URL=""` the handler would answer 503. Checked: `require()` runs before `get_mirror()`, so the brand gets the Cedar 403 first.
   Decision: **applied** (finding 2's rule covers it; the row expects 403).

4. **Medium: role takeover has two shapes.** A kabadiwala doing `PUT /actors/au-1` is stopped by Cedar (`register` needs principal == resource). The auditor's own ID re-registering as a kabadiwala is stopped by P3's 409, not Cedar.
   Decision: **applied.** The row uses the first shape and expects Cedar. The second is P3's check; not counted here.

5. **Medium: "compromised model" must reach the real code path.** `handle_collection` calls the module-level `build_model`, so swapping `agent.agent.build_model` reaches it. The swap must be restored even if the attack raises.
   Decision: **applied.** A context manager with `try/finally`, and a test that it is restored.

6. **Low: injection rows with the scripted model are weak evidence.** The scripted model ignores the note, so those rows mostly prove the code path. The compromised-model rows are the real proof, and `--real` covers the real model.
   Decision: **applied.** The scorecard text says this plainly under the injection category.

7. **Low: Makefile is shared.** Editing the existing `.PHONY` line touches a teammate's line.
   Decision: **applied.** The target gets its own `.PHONY: redteam` line; no existing line changes.

8. **Low: `--real` could make radar rows call the LLM explainer.** Only categories 1 and 2 drop `MOCK_LLM`; every other Arena forces `MOCK_LLM=1`.
   Decision: **applied** (already in the spec; made explicit in the implementation).

## Checked, no change needed
- Vocabulary: Certificate, Receipt, Chain, Kabadiwala, Flag; no "Claim" (also enforced by `tests/test_docs.py` on the docs).
- Design rule 1 and 2: the harness changes nothing in the system under attack.
- CLAUDE.md "only build what appears in the video": the scorecard is a planned video shot (added to section 6 of `docs/agent_and_policy.md`).
- Offline: `fixture:` payloads always use the stub; no network in tests.
