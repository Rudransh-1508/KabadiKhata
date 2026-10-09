# Spec review: p2-5-docs

Reviewed against CLAUDE.md, CONTEXT.md, `src/api/app.py`, `src/policy/*`, `src/radar/rules.py`, `src/radar/explain.py`, `src/agent/README.md`, `Makefile`, `tests/test_api.py`, `tests/conftest.py`. Read-only review (no shell available); claims below are from reading the code.

## Findings, most severe first

### 1. HIGH: three API actions do not exist in the Cedar schema, so the spec's action-table test cannot pass and those routes are denied
`src/api/app.py` calls `require(..., "register" | "list_actors" | "read_flags", ...)`. None of the three is declared in `src/policy/schema.cedarschema`, and `authz._evaluate` returns "unknown action" for any undeclared action. Resource types `Directory` and `Actor` are also not in `authz._RESOURCE_TYPES`. Result today: `GET /flags` (the Auditor's Flag list, beat 2), `GET /actors` and `PUT /actors/{id}` (the bot's /start) are denied for every principal. The spec said every listed action must be in the schema and listed all ten, so its own test would fail, or the doc would lie.
**Decision: applied.** New Behaviour 7: run `tests/test_api.py` first. If the three routes are denied, apply the minimal P2-side fix in `src/policy` only (declare the actions and resource types, add permits: `read_flags` and `list_actors` for Auditor, `register` for a Kabadiwala on their own `Actor` id; `src/api/app.py` is not touched), add tests to `tests/test_policy.py`, extend the policy table, and call it out. The route table in the doc is generated from what is true after that check; if a fix is impossible, the doc says "denied by default, see limitations" and the test skips only those names.

### 2. HIGH: `rules._explain` integration bug is real, not conditional
`rules.run` calls `radar.explain.explain(flag, store)` (a one-argument function returning an `(en, hi)` tuple) and reads `.explanation_en`. Importing succeeds, so the `except ImportError` does not protect it: `POST /radar/run` raises `TypeError` whenever a Flag exists (beat 2). Behaviour 6 treated this as "maybe".
**Decision: applied.** Behaviour 6 now states the defect as confirmed by reading, makes the fix mandatory (call `with_llm_explanation(flag)`), and requires a regression test. The run-first check stays only to confirm the fix works.

### 3. MEDIUM: beat 4 hits an actor-directory dependency
`authz` resolves roles from `policy.directory`, filled by `load_from_store`. A bare `make api` on a seeded DB works only if the API loads the directory (it does via `refresh()` on unknown principal). The spec did not say how the recorder gets real ids, and `data/` does not exist in this worktree.
**Decision: applied.** Beat-4 section must show `curl ... /actors` with an Auditor id first to list ids, use only ids that appear in `src/ledger/world.py` (built-in demo world: `kw-raju`, etc.) or placeholders, and carry the pytest fallback. It must also tell the recorder that principal ids are plain ids (`X-Principal: kw-raju`), matching `src/api/README.md`.

### 4. MEDIUM: beat-4 command targets the wrong route for the denial
`GET /receipts?collector_id=` as a Brand returns 403 with `action: read_receipt`. That is correct, but the spec also says "Brand principal on /provenance allowed". `read_provenance` is allowed only when the Certificate's `buyer` is that Brand. The doc must say "own Certificate", else the recorder may use another Brand's Certificate and get a denial on the "allowed" shot.
**Decision: applied.** Doc text and run sheet specify the Brand's own Certificate id (from `GET /certificates?brand_id=`).

### 5. MEDIUM: spec cites the `make demo`/bot/console chain that does not all exist
CLAUDE.md lists `make bot`, `make console`, `make sam-invoke`; the Makefile has only `install test api seed demo tamper`. The spec's test already restricts to targets in the Makefile, but the prose must not name missing ones.
**Decision: applied.** Run section lists only `install`, `test`, `api`, `seed`, `demo`, `tamper`; says bot/console targets belong to P4.

### 6. LOW: "Receipt weight always the scale reading" and injection snippet
The injection snippet uses `InMemoryReceiptStore`, which is fine for the clip, but the video flow shows the real stack. Acceptable; it is optional.
**Decision: rejected (no change).** Marked optional already.

### 7. LOW: forbidden-text test too strict / too loose
The `Claim ` check is case-sensitive and would also flag sentence starts such as "Claim precedence". Spec already allows "claim precedence" lower-case; the doc must write it lower-case.
**Decision: applied** (one sentence in the test plan).

### 8. LOW: line budget
~250 lines with a 5-row policy table, a route table, an env table and two run sheets is tight but achievable. **Decision: rejected**; a soft target, not tested.

### 9. LOW: scope creep
The spec adds `radar/rules.py` and policy changes. Both are forced by findings 1 and 2 and are P2-owned or a minimal compatibility fix; they must be called out. **Decision: applied** (acceptance criteria updated). `Taps`-style new features are not added.

### 10. Vocabulary
Terms conform (Collection, Receipt, Question, Chain, Certificate, Flag). `Lambda`/`SAM` not mentioned, fine. No violations found.
